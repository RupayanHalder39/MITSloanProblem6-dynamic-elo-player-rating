"""
Stage 6 orchestrator: runs Experiment Blocks 2-11, 14-23, writing one CSV per block to
outputs/tables/. Reuses Stage 5's metrics_for/common_cohort/bootstrap_diff (imported, not
duplicated). All sensitivity sweeps (opponent scale, history decay, K) are fit/compared on
TRAIN+VALIDATION only; any test-split numbers for those are explicitly labeled POST-HOC ROBUSTNESS
in the accompanying report, never chosen by looking at test.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"
TABLES = BASE / "outputs" / "tables"
sys.path.insert(0, str(BASE / "src" / "analysis"))
sys.path.insert(0, str(BASE / "src" / "models"))
from evaluate_dynamic_rating import metrics_for, common_cohort  # noqa: E402
from bootstrap_predictive_comparisons import bootstrap_diff  # noqa: E402
from rating_engine_sensitivity import run_sensitivity_variant  # noqa: E402

SEASON_SPLIT = {"188987": "train", "189951": "validation", "191644": "test"}
SEED = 42


def load_eval():
    df = pd.read_parquet(PROCESSED / "player_rating_predictive_evaluation.parquet")
    return df


def load_scoreable_for_engine():
    scored = pd.read_parquet(PROCESSED / "player_match_performance.parquet")
    scored = scored[scored.score_eligible & scored.final_stage3_score_candidate.notna()].copy()
    scored["match_datetime_utc"] = pd.to_datetime(scored.match_datetime_utc, utc=True)
    scored["split"] = scored.season_id.astype(str).map(SEASON_SPLIT)
    scored = scored.sort_values(["match_datetime_utc", "match_id"]).reset_index(drop=True)
    return scored


def calibrate(x_train, y_train):
    m = np.isfinite(x_train) & np.isfinite(y_train)
    x, y = x_train[m], y_train[m]
    xm, ym = x.mean(), y.mean()
    b = np.sum((x - xm) * (y - ym)) / np.sum((x - xm) ** 2)
    a = ym - b * xm
    return a, b


# ---------------------------------------------------------------------------
# Block 2: multiple future horizons
# ---------------------------------------------------------------------------
def block2_future_horizons():
    df = load_eval()
    horizons_df = pd.read_parquet(PROCESSED / "future_horizon_targets.parquet")
    df = df.merge(horizons_df, on=["match_id", "player_id"], suffixes=("", "_h"))

    methods = {
        "last1": "baseline_last1", "last3": "baseline_last3", "last5": "baseline_last5",
        "season_to_date": "baseline_season_to_date", "career_to_date": "baseline_career_to_date",
        "variant_A": "variant_A_rating", "variant_B": "variant_B_rating", "variant_C": "variant_C_rating",
    }
    rows = []
    for h in [1, 2, 3, 5, 7]:
        target_col = f"future_{h}_match_performance"
        train_mask = (df.split == "train") & df[target_col].notna()
        for name, raw_col in methods.items():
            a, b = calibrate(df.loc[train_mask, raw_col].to_numpy(dtype=float),
                              df.loc[train_mask, target_col].to_numpy(dtype=float))
            df[f"_calib_{name}_{h}"] = a + b * df[raw_col]
        test = df[df.split == "test"]
        cohort = test[test[target_col].notna()]
        for m in methods:
            cohort = cohort[cohort[f"_calib_{m}_{h}"].notna()]
        for name in methods:
            mt = metrics_for(cohort[f"_calib_{name}_{h}"].to_numpy(), cohort[target_col].to_numpy())
            rows.append({"horizon": h, "method": name, **mt})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "exp_future_horizons.csv", index=False)
    print("Block 2 (future horizons) done.")
    return out


# ---------------------------------------------------------------------------
# Block 3: rolling temporal folds (train+validation only, no test)
# ---------------------------------------------------------------------------
def block3_temporal_folds():
    df = load_eval()
    df["match_datetime_utc"] = pd.to_datetime(df.match_datetime_utc, utc=True)
    pretest = df[df.split.isin(["train", "validation"])].sort_values("match_datetime_utc")

    # fold boundaries by calendar date within train+validation only
    dates = pretest.match_datetime_utc
    q33, q66 = dates.quantile([1 / 3, 2 / 3])
    folds = [
        ("early-2023/24 -> later-2023/24",
         pretest[(pretest.split == "train") & (pretest.match_datetime_utc < q33)],
         pretest[(pretest.split == "train") & (pretest.match_datetime_utc >= q33)]),
        ("2023/24 -> early-2024/25",
         pretest[pretest.split == "train"],
         pretest[(pretest.split == "validation") & (pretest.match_datetime_utc < pretest[pretest.split == "validation"].match_datetime_utc.quantile(0.5))]),
        ("2023/24+early-2024/25 -> later-2024/25",
         pretest[(pretest.split == "train") | ((pretest.split == "validation") & (pretest.match_datetime_utc < pretest[pretest.split == "validation"].match_datetime_utc.quantile(0.5)))],
         pretest[(pretest.split == "validation") & (pretest.match_datetime_utc >= pretest[pretest.split == "validation"].match_datetime_utc.quantile(0.5))]),
    ]
    methods = {"last5": "baseline_last5", "season_to_date": "baseline_season_to_date",
               "variant_A": "variant_A_rating", "variant_C": "variant_C_rating"}
    rows = []
    for fold_name, fit_rows, eval_rows in folds:
        fit_rows = fit_rows[fit_rows.future_3_match_performance.notna()]
        eval_rows2 = eval_rows[eval_rows.future_3_match_performance.notna()]
        if len(fit_rows) < 200 or len(eval_rows2) < 200:
            continue
        fold_metrics = {}
        for name, raw_col in methods.items():
            a, b = calibrate(fit_rows[raw_col].to_numpy(dtype=float),
                              fit_rows.future_3_match_performance.to_numpy(dtype=float))
            pred = a + b * eval_rows2[raw_col]
            mt = metrics_for(pred.to_numpy(), eval_rows2.future_3_match_performance.to_numpy())
            fold_metrics[name] = mt
            rows.append({"fold": fold_name, "method": name,
                         "fit_rows": len(fit_rows), "fit_players": fit_rows.player_id.nunique(),
                         "eval_rows": len(eval_rows2), "eval_players": eval_rows2.player_id.nunique(),
                         **mt})
        best_mae = min(fold_metrics, key=lambda k: fold_metrics[k]["MAE"])
        best_sp = max(fold_metrics, key=lambda k: fold_metrics[k]["Spearman"])
        for r in rows[-len(methods):]:
            r["winner_MAE"] = best_mae
            r["winner_Spearman"] = best_sp
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "exp_temporal_folds.csv", index=False)
    print("Block 3 (temporal folds) done.")
    return out


# ---------------------------------------------------------------------------
# Block 4: history depth
# ---------------------------------------------------------------------------
def block4_history_depth():
    df = load_eval()
    test = df[df.split == "test"]
    cohort = common_cohort(test, "future_3_match_performance",
                            methods=["variant_A_rating_calibrated", "baseline_last5_calibrated",
                                     "baseline_season_to_date_calibrated"])
    bins = [-1, 4, 9, 14, 29, 10_000]
    labels = ["0-4", "5-9", "10-14", "15-29", "30+"]
    cohort = cohort.copy()
    cohort["history_bucket"] = pd.cut(cohort.matches_seen_before, bins=bins, labels=labels)
    rows = []
    for bucket, g in cohort.groupby("history_bucket", observed=True):
        for name, col in [("variant_A", "variant_A_rating_calibrated"), ("last5", "baseline_last5_calibrated"),
                           ("season_to_date", "baseline_season_to_date_calibrated")]:
            mt = metrics_for(g[col].to_numpy(), g.future_3_match_performance.to_numpy())
            rows.append({"history_bucket": bucket, "method": name, **mt})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "exp_history_depth.csv", index=False)
    print("Block 4 (history depth) done.")
    return out


# ---------------------------------------------------------------------------
# Block 5: position (extended w/ bootstrap)
# ---------------------------------------------------------------------------
def block5_position():
    df = load_eval()
    test = df[df.split == "test"]
    cohort = common_cohort(test, "future_3_match_performance",
                            methods=["variant_A_rating_calibrated", "baseline_last5_calibrated",
                                     "baseline_season_to_date_calibrated", "baseline_career_to_date_calibrated"])
    rows = []
    for pos, g in cohort.groupby("position_group"):
        for name, col in [("variant_A", "variant_A_rating_calibrated"), ("last5", "baseline_last5_calibrated"),
                           ("season_to_date", "baseline_season_to_date_calibrated"),
                           ("career_to_date", "baseline_career_to_date_calibrated")]:
            mt = metrics_for(g[col].to_numpy(), g.future_3_match_performance.to_numpy())
            rows.append({"position_group": pos, "method": name, **mt})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "exp_position.csv", index=False)
    print("Block 5 (position, extended) done.")
    return out, cohort


# ---------------------------------------------------------------------------
# Block 20 (built first, feeds 6/7): target stability / autocorrelation by position
# ---------------------------------------------------------------------------
def block20_target_stability():
    scored = load_scoreable_for_engine()
    rows = []
    for pos, g in scored.groupby("position_group"):
        g = g.sort_values(["player_id", "match_datetime_utc"])
        within_var = g.groupby("player_id").final_stage3_score_candidate.var().mean()
        between_var = g.groupby("player_id").final_stage3_score_candidate.mean().var()
        lag1s, lag3s = [], []
        for pid, gp in g.groupby("player_id"):
            gp = gp.sort_values("match_datetime_utc")
            s = gp.final_stage3_score_candidate.to_numpy()
            if len(s) > 3:
                lag1s.append(np.corrcoef(s[:-1], s[1:])[0, 1])
            if len(s) > 5:
                lag3s.append(np.corrcoef(s[:-3], s[3:])[0, 1])
        rows.append({
            "position_group": pos, "n_rows": len(g), "n_players": g.player_id.nunique(),
            "score_variance_within_player_mean": round(within_var, 3),
            "score_variance_between_player": round(between_var, 3),
            "lag1_autocorrelation_mean": round(np.nanmean(lag1s), 3) if lag1s else None,
            "lag3_autocorrelation_mean": round(np.nanmean(lag3s), 3) if lag3s else None,
            "n_players_lag1": len(lag1s),
        })
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "exp_target_stability.csv", index=False)
    print("Block 20 (target stability) done.")
    return out


# ---------------------------------------------------------------------------
# Block 6/7: GK / ATT diagnosis
# ---------------------------------------------------------------------------
def block6_7_position_diagnosis(stability_table):
    df = load_eval()
    test = df[df.split == "test"]
    cohort = common_cohort(test, "future_3_match_performance",
                            methods=["variant_A_rating_calibrated", "baseline_last1_calibrated",
                                     "baseline_last3_calibrated", "baseline_last5_calibrated",
                                     "baseline_career_to_date_calibrated"])
    rows = []
    for pos in ["GK", "ATT"]:
        g = cohort[cohort.position_group == pos]
        n_matches = g.groupby("player_id").size()
        stab = stability_table[stability_table.position_group == pos].iloc[0]
        diag_row = {
            "position_group": pos, "n_test_rows": len(g), "n_players": g.player_id.nunique(),
            "median_matches_per_player_test": n_matches.median(),
            "future3_target_variance": round(g.future_3_match_performance.var(), 3),
            "score_variance_within_player": stab.score_variance_within_player_mean,
            "score_variance_between_player": stab.score_variance_between_player,
            "lag1_autocorrelation": stab.lag1_autocorrelation_mean,
        }
        for name, col in [("last1", "baseline_last1_calibrated"), ("last3", "baseline_last3_calibrated"),
                           ("last5", "baseline_last5_calibrated"), ("career_to_date", "baseline_career_to_date_calibrated"),
                           ("variant_A", "variant_A_rating_calibrated")]:
            mt = metrics_for(g[col].to_numpy(), g.future_3_match_performance.to_numpy())
            diag_row[f"{name}_MAE"] = mt["MAE"]
            diag_row[f"{name}_Spearman"] = mt["Spearman"]
            diag_row[f"{name}_R2"] = mt["R2"]
        rows.append(diag_row)
    out = pd.DataFrame(rows)
    gk_out = out[out.position_group == "GK"]
    att_out = out[out.position_group == "ATT"]
    gk_out.to_csv(TABLES / "exp_gk_diagnosis.csv", index=False)
    att_out.to_csv(TABLES / "exp_att_diagnosis.csv", index=False)
    print("Block 6/7 (GK/ATT diagnosis) done.")
    return out


# ---------------------------------------------------------------------------
# Block 18: team context (pre-match team Elo terciles)
# ---------------------------------------------------------------------------
def block18_team_context():
    df = load_eval()
    elo = pd.read_parquet(PROCESSED / "player_match_performance.parquet")[
        ["match_id", "player_id", "pre_match_team_elo"]]
    df = df.merge(elo, on=["match_id", "player_id"], how="left")
    test = df[df.split == "test"].copy()
    cohort = common_cohort(test, "future_3_match_performance",
                            methods=["variant_A_rating_calibrated"])
    cohort = cohort.copy()
    t1, t2 = cohort.pre_match_team_elo.quantile([1 / 3, 2 / 3])
    cohort["team_tercile"] = pd.cut(cohort.pre_match_team_elo, [-np.inf, t1, t2, np.inf],
                                     labels=["low", "middle", "high"])
    rows = []
    for tercile, g in cohort.groupby("team_tercile", observed=True):
        mt = metrics_for(g.variant_A_rating_calibrated.to_numpy(), g.future_3_match_performance.to_numpy())
        rows.append({"team_elo_tercile": tercile, "elo_range": f"[{g.pre_match_team_elo.min():.0f}, {g.pre_match_team_elo.max():.0f}]", **mt})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "exp_team_context.csv", index=False)
    print("Block 18 (team context) done.")
    return out


# ---------------------------------------------------------------------------
# Block 19: starters vs substitutes
# ---------------------------------------------------------------------------
def block19_starter_sub():
    df = load_eval()
    scored = pd.read_parquet(PROCESSED / "player_match_performance.parquet")
    scored = scored[["match_id", "player_id", "is_starting"]]
    test = df[df.split == "test"].merge(scored, on=["match_id", "player_id"])
    cohort = common_cohort(test, "future_3_match_performance",
                            methods=["variant_A_rating_calibrated", "baseline_last5_calibrated"])
    cohort = cohort.copy()
    cohort["group"] = np.where(cohort.is_starting.astype(str) == "t", "regular_starter", "substitute")
    rows = []
    for grp, g in cohort.groupby("group"):
        for name, col in [("variant_A", "variant_A_rating_calibrated"), ("last5", "baseline_last5_calibrated")]:
            mt = metrics_for(g[col].to_numpy(), g.future_3_match_performance.to_numpy())
            rows.append({"group": grp, "method": name, **mt})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "exp_starter_sub.csv", index=False)
    print("Block 19 (starter/sub) done.")
    return out


if __name__ == "__main__":
    block2_future_horizons()
    block3_temporal_folds()
    block4_history_depth()
    block5_position()
    stability = block20_target_stability()
    block6_7_position_diagnosis(stability)
    block18_team_context()
    block19_starter_sub()
