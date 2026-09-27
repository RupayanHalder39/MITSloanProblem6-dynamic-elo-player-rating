"""
Stage 6, Experiment Blocks 12-17, 21-23 (Blocks 18-20 already in run_stage6_experiments.py).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"
TABLES = BASE / "outputs" / "tables"
REPORTS = BASE / "outputs" / "reports"
sys.path.insert(0, str(BASE / "src" / "analysis"))
sys.path.insert(0, str(BASE / "src" / "models"))
from evaluate_dynamic_rating import metrics_for, common_cohort  # noqa: E402
from bootstrap_predictive_comparisons import bootstrap_diff  # noqa: E402
from rating_engine_sensitivity import run_sensitivity_variant  # noqa: E402

SEASON_SPLIT = {"188987": "train", "189951": "validation", "191644": "test"}
SEED = 42


def calibrate(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    xm, ym = x.mean(), y.mean()
    b = np.sum((x - xm) * (y - ym)) / np.sum((x - xm) ** 2)
    a = ym - b * xm
    return a, b


def load_eval():
    return pd.read_parquet(PROCESSED / "player_rating_predictive_evaluation.parquet")


# ---------------------------------------------------------------------------
# Block 12: Score A vs Score B through the full pipeline
# ---------------------------------------------------------------------------
def block12_score_ablation():
    df = pd.read_parquet(PROCESSED / "player_match_performance.parquet")
    scored = df[df.score_eligible & df.candidate_score_A.notna()].copy()
    scored["match_datetime_utc"] = pd.to_datetime(scored.match_datetime_utc, utc=True)
    scored["split"] = scored.season_id.astype(str).map(SEASON_SPLIT)

    # scale candidate_score_A onto 0-100 using the SAME method as Stage 3's Score B scaling
    # (median-centered, 2nd/98th percentile -> 25/75), fit on candidate_score_A's OWN distribution
    ref = scored.candidate_score_A.dropna()
    p50, p_lo, p_hi = ref.quantile([0.50, 0.02, 0.98])
    scale = 25.0 / max((p_hi - p50), (p50 - p_lo), 0.1)
    scored["final_score_A_100"] = (50 + (scored.candidate_score_A - p50) * scale).clip(0, 100)

    scored_for_engine = scored.rename(
        columns={"final_stage3_score_candidate": "_orig_score", "final_score_A_100": "final_stage3_score_candidate"}
    ).sort_values(["match_datetime_utc", "match_id"]).reset_index(drop=True)

    ratings_A = run_sensitivity_variant(scored_for_engine, use_opponent=False, use_history_decay=False)

    # future target must ALSO be recomputed using Score A's own scale (leakage-safe, per-player forward)
    rows = []
    for pid, sub in scored_for_engine.groupby("player_id", sort=False):
        sub = sub.sort_values(["match_datetime_utc", "match_id"]).reset_index(drop=True)
        s = sub.final_stage3_score_candidate.to_numpy()
        for i in range(len(sub)):
            future = s[i + 1:]
            rows.append({"match_id": sub.loc[i, "match_id"], "player_id": pid,
                         "future_3_scoreA": future[:3].mean() if len(future) >= 3 else None})
    targets_A = pd.DataFrame(rows)

    merged = ratings_A.merge(targets_A, on=["match_id", "player_id"])
    fit = merged[(merged.split == "train") & merged.future_3_scoreA.notna()]
    test = merged[(merged.split == "test") & merged.future_3_scoreA.notna()]
    a, b = calibrate(fit.post_match_player_rating.to_numpy(dtype=float), fit.future_3_scoreA.to_numpy(dtype=float))
    pred_A_score = a + b * test.post_match_player_rating
    mt_scoreA = metrics_for(pred_A_score.to_numpy(), test.future_3_scoreA.to_numpy())

    # Score B (production) comparison on the SAME evaluation frame (variant A ratings, future-3, test)
    eval_df = load_eval()
    test_b = eval_df[eval_df.split == "test"]
    cohort_b = common_cohort(test_b, "future_3_match_performance", methods=["variant_A_rating_calibrated"])
    mt_scoreB = metrics_for(cohort_b.variant_A_rating_calibrated.to_numpy(), cohort_b.future_3_match_performance.to_numpy())

    out = pd.DataFrame([
        {"score_variant": "Score A (equal-weight, feature-count-biased)", "n": len(test), **mt_scoreA},
        {"score_variant": "Score B (category-balanced, production)", "n": len(cohort_b), **mt_scoreB},
    ])
    out.to_csv(TABLES / "exp_score_ablation.csv", index=False)
    print("Block 12 (Score A vs B) done.")
    print(out)


# ---------------------------------------------------------------------------
# Block 13 (scoped): leave-one-category-out correlation with future-3 target
# ---------------------------------------------------------------------------
def block13_category_ablation():
    df = pd.read_parquet(PROCESSED / "player_match_performance.parquet")
    scored = df[df.score_eligible].copy()
    targets = pd.read_parquet(PROCESSED / "future_performance_targets.parquet")
    merged = scored.merge(targets, on=["match_id", "player_id"])
    merged = merged[merged.future_3_match_performance.notna()]

    cats = ["ATTACKING", "CREATION", "POSSESSION", "DEFENDING", "GOALKEEPING"]
    rows = []
    for cat in cats:
        col = f"category_score_{cat}"
        sub = merged[merged[col].notna()]
        if len(sub) < 100:
            continue
        r_s = stats.spearmanr(sub[col], sub.future_3_match_performance)[0]
        r_p = stats.pearsonr(sub[col], sub.future_3_match_performance)[0]
        rows.append({"category": cat, "n": len(sub),
                     "spearman_with_future3": round(r_s, 3), "pearson_with_future3": round(r_p, 3)})
    # also: full Score B (all categories) as a reference point
    full = merged[merged.final_stage3_score_candidate.notna()]
    r_full = stats.spearmanr(full.final_stage3_score_candidate, full.future_3_match_performance)[0]
    rows.append({"category": "FULL_SCORE_B (reference, all categories combined)", "n": len(full),
                 "spearman_with_future3": round(r_full, 3),
                 "pearson_with_future3": round(stats.pearsonr(full.final_stage3_score_candidate, full.future_3_match_performance)[0], 3)})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "exp_category_ablation.csv", index=False)
    print("Block 13 (category ablation, scoped: single-category correlation with future target) done.")
    print(out)


# ---------------------------------------------------------------------------
# Block 14: rating + recent-form combination
# ---------------------------------------------------------------------------
def block14_combination():
    df = load_eval()
    train = df[(df.split == "train") & df.future_3_match_performance.notna()]
    test = df[(df.split == "test") & df.future_3_match_performance.notna()]

    def fit_multi(cols, train_df):
        X = train_df[cols].to_numpy(dtype=float)
        y = train_df.future_3_match_performance.to_numpy(dtype=float)
        X1 = np.column_stack([np.ones(len(X)), X])
        coef, *_ = np.linalg.lstsq(X1, y, rcond=None)
        return coef

    def predict(cols, coef, d):
        X = d[cols].to_numpy(dtype=float)
        X1 = np.column_stack([np.ones(len(X)), X])
        return X1 @ coef

    combos = {
        "variant_A_only": ["variant_A_rating"],
        "last5_only": ["baseline_last5"],
        "variant_A_plus_last5": ["variant_A_rating", "baseline_last5"],
        "variant_A_plus_season_to_date": ["variant_A_rating", "baseline_season_to_date"],
    }
    rows = []
    for name, cols in combos.items():
        sub_train = train.dropna(subset=cols)
        sub_test = test.dropna(subset=cols)
        coef = fit_multi(cols, sub_train)
        pred = predict(cols, coef, sub_test)
        mt = metrics_for(pred, sub_test.future_3_match_performance.to_numpy())
        rows.append({"combination": name, "n": len(sub_test), **mt})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "exp_combination.csv", index=False)
    print("Block 14 (combination) done.")
    print(out)


# ---------------------------------------------------------------------------
# Block 15: ranking robustness (extended)
# ---------------------------------------------------------------------------
def block15_ranking_robustness():
    df = load_eval()
    test = df[df.split == "test"]
    cohort = common_cohort(test, "future_3_match_performance", methods=["variant_A_rating_calibrated"])
    rows = []
    for frac, label in [(0.10, "top10"), (0.20, "top20"), (0.25, "top25")]:
        cut = cohort.variant_A_rating_calibrated.quantile(1 - frac)
        top = cohort[cohort.variant_A_rating_calibrated >= cut].future_3_match_performance
        rest = cohort[cohort.variant_A_rating_calibrated < cut].future_3_match_performance
        rows.append({"cutoff": label, "n_top": len(top), "n_rest": len(rest),
                     "top_mean_future3": round(top.mean(), 2), "top_std": round(top.std(), 2),
                     "rest_mean_future3": round(rest.mean(), 2), "gap": round(top.mean() - rest.mean(), 2)})
    # season consistency: repeat top20 for each split
    for split in ["train", "validation", "test"]:
        s = df[df.split == split]
        c = common_cohort(s, "future_3_match_performance", methods=["variant_A_rating_calibrated"])
        cut = c.variant_A_rating_calibrated.quantile(0.80)
        top = c[c.variant_A_rating_calibrated >= cut].future_3_match_performance
        rest = c[c.variant_A_rating_calibrated < cut].future_3_match_performance
        rows.append({"cutoff": f"top20_{split}", "n_top": len(top), "n_rest": len(rest),
                     "top_mean_future3": round(top.mean(), 2), "top_std": round(top.std(), 2),
                     "rest_mean_future3": round(rest.mean(), 2), "gap": round(top.mean() - rest.mean(), 2)})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "exp_ranking.csv", index=False)
    print("Block 15 (ranking robustness) done.")
    print(out)


# ---------------------------------------------------------------------------
# Block 16/17: momentum / decline
# ---------------------------------------------------------------------------
def block16_17_momentum_decline():
    ratings = pd.read_parquet(PROCESSED / "player_dynamic_ratings_candidates.parquet")
    a = ratings[ratings.rating_variant == "A"].copy()
    a["match_datetime_utc"] = pd.to_datetime(a.match_datetime_utc, utc=True)
    a = a.sort_values(["player_id", "match_datetime_utc"])
    N = 5
    a["rating_momentum"] = a.groupby("player_id").post_match_player_rating.diff(N)

    targets = pd.read_parquet(PROCESSED / "future_performance_targets.parquet")
    merged = a.merge(targets, on=["match_id", "player_id"])
    merged = merged[merged.future_3_match_performance.notna() & merged.rating_momentum.notna()]

    p10, p90 = merged.rating_momentum.quantile([0.10, 0.90])
    high_mom = merged[merged.rating_momentum >= p90]
    mid_mom = merged[(merged.rating_momentum > p10) & (merged.rating_momentum < p90)]
    low_mom = merged[merged.rating_momentum <= p10]

    rows = [
        {"group": "top10pct_momentum (rising)", "n": len(high_mom),
         "mean_future3": round(high_mom.future_3_match_performance.mean(), 2)},
        {"group": "middle80pct_momentum", "n": len(mid_mom),
         "mean_future3": round(mid_mom.future_3_match_performance.mean(), 2)},
        {"group": "bottom10pct_momentum (declining)", "n": len(low_mom),
         "mean_future3": round(low_mom.future_3_match_performance.mean(), 2)},
    ]
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "exp_momentum.csv", index=False)
    # decline is the mirror of the same table -- saved separately per the brief's file list
    out.to_csv(TABLES / "exp_decline.csv", index=False)
    print("Block 16/17 (momentum/decline) done.")
    print(out)


# ---------------------------------------------------------------------------
# Block 21/22: bootstrap headline comparisons + effect sizes
# ---------------------------------------------------------------------------
def block21_22_bootstrap_effects():
    df = load_eval()
    test = df[(df.split == "test") & df.future_3_match_performance.notna()].copy()
    METHOD_COLS = {
        "variant_A": "variant_A_rating_calibrated", "variant_B": "variant_B_rating_calibrated",
        "variant_C": "variant_C_rating_calibrated", "last5": "baseline_last5_calibrated",
        "season_to_date": "baseline_season_to_date_calibrated",
        "career_to_date": "baseline_career_to_date_calibrated",
    }
    for c in METHOD_COLS.values():
        test = test[test[c].notna()]

    comparisons = [("variant_A", "last5"), ("variant_A", "season_to_date"),
                   ("variant_A", "career_to_date"), ("variant_A", "variant_B"), ("variant_A", "variant_C")]
    rows = []
    for a_name, b_name in comparisons:
        mae_d, sp_d = bootstrap_diff(test, METHOD_COLS[a_name], METHOD_COLS[b_name],
                                      "future_3_match_performance", n_boot=2000, seed=SEED)
        mae_a = metrics_for(test[METHOD_COLS[a_name]].to_numpy(), test.future_3_match_performance.to_numpy())["MAE"]
        mae_b = metrics_for(test[METHOD_COLS[b_name]].to_numpy(), test.future_3_match_performance.to_numpy())["MAE"]
        rows.append({
            "comparison": f"{a_name} vs {b_name}",
            "mae_diff_mean": round(mae_d.mean(), 4),
            "mae_diff_ci_lo": round(np.percentile(mae_d, 2.5), 4),
            "mae_diff_ci_hi": round(np.percentile(mae_d, 97.5), 4),
            "robust": bool(np.percentile(mae_d, 2.5) > 0 or np.percentile(mae_d, 97.5) < 0),
            "spearman_diff_mean": round(sp_d.mean(), 4),
            "spearman_diff_ci_lo": round(np.percentile(sp_d, 2.5), 4),
            "spearman_diff_ci_hi": round(np.percentile(sp_d, 97.5), 4),
            "absolute_MAE_improvement": round(mae_b - mae_a, 4),
            "relative_MAE_improvement_pct": round((mae_b - mae_a) / mae_b * 100, 2),
            "n_boot": 2000, "seed": SEED,
        })
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "exp_bootstrap_effects.csv", index=False)
    print("Block 21/22 (bootstrap + effect sizes) done.")
    print(out[["comparison", "mae_diff_mean", "robust", "relative_MAE_improvement_pct"]])


if __name__ == "__main__":
    block12_score_ablation()
    block13_category_ablation()
    block14_combination()
    block15_ranking_robustness()
    block16_17_momentum_decline()
    block21_22_bootstrap_effects()
