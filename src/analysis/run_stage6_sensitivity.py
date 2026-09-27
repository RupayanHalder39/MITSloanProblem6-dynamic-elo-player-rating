"""
Stage 6, Experiment Blocks 8-11: opponent-scale, history-decay, K, and minutes-weight sensitivity.
ALL fitting/selection uses TRAIN+VALIDATION only -- test-split numbers (already observed in Stage 5)
are reported afterward, clearly labeled POST-HOC ROBUSTNESS, never used to pick a "winning" setting.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"
TABLES = BASE / "outputs" / "tables"
sys.path.insert(0, str(BASE / "src" / "analysis"))
sys.path.insert(0, str(BASE / "src" / "models"))
from evaluate_dynamic_rating import metrics_for  # noqa: E402
from rating_engine_sensitivity import run_sensitivity_variant  # noqa: E402

SEASON_SPLIT = {"188987": "train", "189951": "validation", "191644": "test"}


def load_scoreable():
    scored = pd.read_parquet(PROCESSED / "player_match_performance.parquet")
    scored = scored[scored.score_eligible & scored.final_stage3_score_candidate.notna()].copy()
    scored["match_datetime_utc"] = pd.to_datetime(scored.match_datetime_utc, utc=True)
    scored["split"] = scored.season_id.astype(str).map(SEASON_SPLIT)
    scored = scored.sort_values(["match_datetime_utc", "match_id"]).reset_index(drop=True)
    return scored


def calibrate(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    xm, ym = x.mean(), y.mean()
    b = np.sum((x - xm) * (y - ym)) / np.sum((x - xm) ** 2)
    a = ym - b * xm
    return a, b


def evaluate_variant_on_targets(ratings_df, targets_df, fit_split, eval_split):
    merged = ratings_df.merge(targets_df, on=["match_id", "player_id"])
    fit_rows = merged[(merged.split == fit_split) & merged.future_3_match_performance.notna()]
    eval_rows = merged[(merged.split == eval_split) & merged.future_3_match_performance.notna()]
    a, b = calibrate(fit_rows.post_match_player_rating.to_numpy(dtype=float),
                      fit_rows.future_3_match_performance.to_numpy(dtype=float))
    pred = a + b * eval_rows.post_match_player_rating
    return metrics_for(pred.to_numpy(), eval_rows.future_3_match_performance.to_numpy()), len(eval_rows)


def main():
    scored = load_scoreable()
    targets = pd.read_parquet(PROCESSED / "future_performance_targets.parquet")

    # --- Block 8: opponent scale sensitivity (predefined grid, validation-selected) ---
    rows8 = []
    for scale in [0.00, 0.01, 0.02, 0.03, 0.04, 0.05]:
        ratings = run_sensitivity_variant(scored, use_opponent=(scale > 0 or scale == 0.00),
                                           use_history_decay=False, opponent_scale=scale)
        # scale=0.00 is mechanically identical to Variant A (no opponent term regardless of flag);
        # kept in the grid as the natural "off" endpoint for comparison.
        val_m, val_n = evaluate_variant_on_targets(ratings, targets, "train", "validation")
        test_m, test_n = evaluate_variant_on_targets(ratings, targets, "train", "test")
        rows8.append({"opponent_scale": scale, "eval_split": "validation", "n": val_n, **val_m})
        rows8.append({"opponent_scale": scale, "eval_split": "test (POST-HOC ROBUSTNESS)", "n": test_n, **test_m})
    out8 = pd.DataFrame(rows8)
    out8.to_csv(TABLES / "exp_opponent_scale.csv", index=False)
    print("Block 8 (opponent scale) done.")
    print(out8[out8.eval_split == "validation"][["opponent_scale", "MAE", "Spearman"]])

    # --- Block 9: history decay sensitivity (predefined small grid, validation-selected) ---
    rows9 = []
    for floor, m0 in [(0.4, 15), (0.3, 10), (0.5, 20), (0.4, 30), (1.0, 15)]:
        # floor=1.0 => no decay at all (K constant), included as the "off" reference point
        ratings = run_sensitivity_variant(scored, use_opponent=False, use_history_decay=True,
                                           history_floor=floor, history_m0=m0)
        val_m, val_n = evaluate_variant_on_targets(ratings, targets, "train", "validation")
        test_m, test_n = evaluate_variant_on_targets(ratings, targets, "train", "test")
        rows9.append({"history_floor": floor, "history_m0": m0, "eval_split": "validation", "n": val_n, **val_m})
        rows9.append({"history_floor": floor, "history_m0": m0, "eval_split": "test (POST-HOC ROBUSTNESS)", "n": test_n, **test_m})
    out9 = pd.DataFrame(rows9)
    out9.to_csv(TABLES / "exp_history_decay.csv", index=False)
    print("Block 9 (history decay) done.")

    # --- Block 10: K sensitivity (predefined grid, validation-selected) ---
    rows10 = []
    for k in [1, 2, 3, 4, 5]:
        ratings = run_sensitivity_variant(scored, use_opponent=False, use_history_decay=False, k_base=k)
        val_m, val_n = evaluate_variant_on_targets(ratings, targets, "train", "validation")
        test_m, test_n = evaluate_variant_on_targets(ratings, targets, "train", "test")
        upd_std = ratings[ratings.split == "validation"].rating_change.std()
        final_range = ratings.groupby("player_id").post_match_player_rating.last()
        rows10.append({"K": k, "eval_split": "validation", "n": val_n, "update_std": round(upd_std, 2),
                        "final_rating_range": round(final_range.max() - final_range.min(), 1), **val_m})
        rows10.append({"K": k, "eval_split": "test (POST-HOC ROBUSTNESS)", "n": test_n, "update_std": round(upd_std, 2),
                        "final_rating_range": round(final_range.max() - final_range.min(), 1), **test_m})
    out10 = pd.DataFrame(rows10)
    out10.to_csv(TABLES / "exp_k_sensitivity.csv", index=False)
    print("Block 10 (K sensitivity) done.")

    # --- Block 11: minutes update-weight ablation (predefined variants) ---
    weight_variants = {
        "A_current (LOW=0.4,MED=0.7,HIGH=1.0)": {"LOW": 0.4, "MEDIUM": 0.7, "HIGH": 1.0},
        "B_all_equal (1.0/1.0/1.0)": {"LOW": 1.0, "MEDIUM": 1.0, "HIGH": 1.0},
        "D_stronger_shrink (LOW=0.15,MED=0.5,HIGH=1.0)": {"LOW": 0.15, "MEDIUM": 0.5, "HIGH": 1.0},
    }
    rows11 = []
    for label, weights in weight_variants.items():
        ratings = run_sensitivity_variant(scored, use_opponent=False, use_history_decay=False,
                                           confidence_weight=weights)
        val_m, val_n = evaluate_variant_on_targets(ratings, targets, "train", "validation")
        test_m, test_n = evaluate_variant_on_targets(ratings, targets, "train", "test")
        rows11.append({"weighting": label, "eval_split": "validation", "n": val_n, **val_m})
        rows11.append({"weighting": label, "eval_split": "test (POST-HOC ROBUSTNESS)", "n": test_n, **test_m})

    # variant C (exclude LOW-confidence cameos entirely)
    scored_excl = scored[scored.minutes_confidence != "LOW"]
    ratings_excl = run_sensitivity_variant(scored_excl, use_opponent=False, use_history_decay=False)
    val_m, val_n = evaluate_variant_on_targets(ratings_excl, targets, "train", "validation")
    test_m, test_n = evaluate_variant_on_targets(ratings_excl, targets, "train", "test")
    rows11.append({"weighting": "C_exclude_LOW_confidence", "eval_split": "validation", "n": val_n, **val_m})
    rows11.append({"weighting": "C_exclude_LOW_confidence", "eval_split": "test (POST-HOC ROBUSTNESS)", "n": test_n, **test_m})

    out11 = pd.DataFrame(rows11)
    out11.to_csv(TABLES / "exp_minutes_weight.csv", index=False)
    print("Block 11 (minutes weight) done.")

    print("\nAll sensitivity blocks written to outputs/tables/")


if __name__ == "__main__":
    main()
