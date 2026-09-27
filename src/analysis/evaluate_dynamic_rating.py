"""
Stage 5, Tasks 9-16: primary predictive comparison, secondary future-5 comparison,
position-specific, experience-specific, opponent-adjustment ablation, history-awareness ablation,
ranking-decile use case. All metrics computed on a COMMON cohort per target (Task 5) -- rows where
every compared predictor's calibrated value AND the target are non-null, so no method is compared
on a more favorable subset than another.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"
TABLES = BASE / "outputs" / "tables"

METHOD_COLS = {
    "last1": "baseline_last1_calibrated",
    "last3": "baseline_last3_calibrated",
    "last5": "baseline_last5_calibrated",
    "season_to_date": "baseline_season_to_date_calibrated",
    "career_to_date": "baseline_career_to_date_calibrated",
    "position_prior": "baseline_position_prior_calibrated",
    "variant_A": "variant_A_rating_calibrated",
    "variant_B": "variant_B_rating_calibrated",
    "variant_C": "variant_C_rating_calibrated",
}


def metrics_for(pred: np.ndarray, actual: np.ndarray) -> dict:
    err = pred - actual
    mae = np.mean(np.abs(err))
    rmse = np.sqrt(np.mean(err ** 2))
    pearson = stats.pearsonr(pred, actual)[0] if len(pred) > 2 else np.nan
    spearman = stats.spearmanr(pred, actual)[0] if len(pred) > 2 else np.nan
    ss_res = np.sum(err ** 2)
    ss_tot = np.sum((actual - actual.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
    return {"n": len(pred), "MAE": round(mae, 3), "RMSE": round(rmse, 3),
            "Pearson": round(pearson, 3), "Spearman": round(spearman, 3), "R2": round(r2, 3)}


def common_cohort(df: pd.DataFrame, target_col: str, methods=None) -> pd.DataFrame:
    methods = methods or list(METHOD_COLS.values())
    mask = df[target_col].notna()
    for m in methods:
        mask &= df[m].notna()
    return df[mask]


def main():
    df = pd.read_parquet(PROCESSED / "player_rating_predictive_evaluation.parquet")
    test = df[df.split == "test"]

    # --- Task 9: primary comparison, future-3, test split, common cohort ---
    cohort3 = common_cohort(test, "future_3_match_performance")
    rows = []
    for name, col in METHOD_COLS.items():
        m = metrics_for(cohort3[col].to_numpy(), cohort3.future_3_match_performance.to_numpy())
        rows.append({"method": name, **m})
    primary = pd.DataFrame(rows).sort_values("MAE")
    primary.to_csv(TABLES / "stage5_primary_method_comparison.csv", index=False)
    print("=== PRIMARY (future-3, test, n common cohort =", len(cohort3), ") ===")
    print(primary.to_string(index=False))

    # --- Task 10: secondary, future-5 ---
    cohort5 = common_cohort(test, "future_5_match_performance")
    if len(cohort5) >= 500:  # adequacy check, per the brief's "only if sample size is adequate"
        rows5 = []
        for name, col in METHOD_COLS.items():
            m = metrics_for(cohort5[col].to_numpy(), cohort5.future_5_match_performance.to_numpy())
            rows5.append({"method": name, **m})
        secondary = pd.DataFrame(rows5).sort_values("MAE")
        secondary.to_csv(TABLES / "stage5_future5_method_comparison.csv", index=False)
        print("\n=== SECONDARY (future-5, test, n common cohort =", len(cohort5), ") ===")
        print(secondary.to_string(index=False))
    else:
        print(f"\nFuture-5 cohort too small ({len(cohort5)}) -- skipped per adequacy check.")

    # --- Task 12: position-specific (variant_C, last5, season_to_date) ---
    pos_rows = []
    for pos, g in cohort3.groupby("position_group"):
        for name in ["variant_C", "last5", "season_to_date"]:
            col = METHOD_COLS[name]
            m = metrics_for(g[col].to_numpy(), g.future_3_match_performance.to_numpy())
            pos_rows.append({"position_group": pos, "method": name, **m})
    pos_comp = pd.DataFrame(pos_rows)
    pos_comp.to_csv(TABLES / "stage5_position_comparison.csv", index=False)
    print("\n=== POSITION-SPECIFIC ===")
    print(pos_comp.to_string(index=False))

    # --- Task 13: experience-specific ---
    exp_rows = []
    for bucket, g in cohort3.groupby("experience_bucket", observed=True):
        for name in ["variant_C", "last5", "season_to_date"]:
            col = METHOD_COLS[name]
            m = metrics_for(g[col].to_numpy(), g.future_3_match_performance.to_numpy())
            exp_rows.append({"experience_bucket": bucket, "method": name, **m})
    exp_comp = pd.DataFrame(exp_rows)
    exp_comp.to_csv(TABLES / "stage5_experience_comparison.csv", index=False)
    print("\n=== EXPERIENCE-SPECIFIC ===")
    print(exp_comp.to_string(index=False))

    # --- Task 14: opponent-adjustment ablation, A vs B, same cohort ---
    cohortAB = common_cohort(test, "future_3_match_performance",
                              methods=[METHOD_COLS["variant_A"], METHOD_COLS["variant_B"]])
    mA = metrics_for(cohortAB[METHOD_COLS["variant_A"]].to_numpy(), cohortAB.future_3_match_performance.to_numpy())
    mB = metrics_for(cohortAB[METHOD_COLS["variant_B"]].to_numpy(), cohortAB.future_3_match_performance.to_numpy())
    opp_ablation = pd.DataFrame([{"variant": "A (no opponent adj.)", **mA},
                                  {"variant": "B (opponent-adjusted)", **mB}])
    opp_ablation.to_csv(TABLES / "stage5_opponent_adjustment_ablation.csv", index=False)
    print("\n=== OPPONENT-ADJUSTMENT ABLATION (A vs B) ===")
    print(opp_ablation.to_string(index=False))

    # --- Task 15: history-awareness ablation, B vs C, same cohort ---
    cohortBC = common_cohort(test, "future_3_match_performance",
                              methods=[METHOD_COLS["variant_B"], METHOD_COLS["variant_C"]])
    mB2 = metrics_for(cohortBC[METHOD_COLS["variant_B"]].to_numpy(), cohortBC.future_3_match_performance.to_numpy())
    mC2 = metrics_for(cohortBC[METHOD_COLS["variant_C"]].to_numpy(), cohortBC.future_3_match_performance.to_numpy())
    hist_ablation = pd.DataFrame([{"variant": "B (fixed K)", **mB2},
                                   {"variant": "C (history-aware K)", **mC2}])
    hist_ablation.to_csv(TABLES / "stage5_history_awareness_ablation.csv", index=False)
    print("\n=== HISTORY-AWARENESS ABLATION (B vs C) ===")
    print(hist_ablation.to_string(index=False))

    # --- Task 16: ranking use case, predefined deciles/top-20% (Variant C, calibrated) ---
    c = cohort3.copy()
    c["rating_decile"] = pd.qcut(c[METHOD_COLS["variant_C"]], 10, labels=False, duplicates="drop")
    decile_perf = c.groupby("rating_decile").future_3_match_performance.agg(["count", "mean", "std"])
    decile_perf.to_csv(TABLES / "stage5_ranking_deciles.csv")
    top20_cut = c[METHOD_COLS["variant_C"]].quantile(0.80)
    top20 = c[c[METHOD_COLS["variant_C"]] >= top20_cut].future_3_match_performance
    rest = c[c[METHOD_COLS["variant_C"]] < top20_cut].future_3_match_performance
    print("\n=== RANKING USE CASE (Variant C, predefined top-20% vs rest) ===")
    print(f"Top 20% (n={len(top20)}): mean future-3 = {top20.mean():.2f}")
    print(f"Rest (n={len(rest)}): mean future-3 = {rest.mean():.2f}")
    print(decile_perf)

    print("\nAll Stage 5 evaluation tables written to outputs/tables/")


if __name__ == "__main__":
    main()
