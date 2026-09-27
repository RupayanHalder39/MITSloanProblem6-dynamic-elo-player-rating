"""
Validate Stage 6 (Robustness, Ablations & Experimental Report) against its completion criteria.
Output: printed to stdout (this is a checklist validator over already-written artifacts, not a
single new dataset -- see outputs/reports/Stage5ReproductionCheck.md and
outputs/reports/ExpandedExperimentalResultsReport.md for the substantive results this checks).
"""
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
TABLES = BASE / "outputs" / "tables"
REPORTS = BASE / "outputs" / "reports"
DOCS = BASE / "docs"


def main():
    checks = []

    def record(name, passed, detail="", blocking=True):
        checks.append({"check": name, "blocking": blocking,
                        "result": "PASS" if passed else "FAIL", "detail": detail})

    # --- Stage-5 headline reproduction exact ---
    repro = (REPORTS / "Stage5ReproductionCheck.md").read_text()
    record("Stage-5 reproduction report confirms EXACT REPRODUCTION",
           "EXACT REPRODUCTION" in repro, "checked for the literal phrase in the report")

    # --- no test-set tuning: every sensitivity table's selection-relevant rows are validation ---
    for fname, param_cols in [
        ("exp_opponent_scale.csv", ["opponent_scale"]),
        ("exp_history_decay.csv", ["history_floor", "history_m0"]),
        ("exp_k_sensitivity.csv", ["K"]),
        ("exp_minutes_weight.csv", ["weighting"]),
    ]:
        df = pd.read_csv(TABLES / fname)
        has_val = (df.eval_split == "validation").any()
        has_labeled_test = df.eval_split.astype(str).str.contains("POST-HOC ROBUSTNESS").any()
        record(f"{fname}: validation rows present AND any test rows explicitly labeled POST-HOC ROBUSTNESS",
               has_val and has_labeled_test, f"validation rows={has_val}, labeled test rows={has_labeled_test}")

    # --- chronological target construction: future_3 spot check reuses Stage 5's own validated
    # builder logic (already checked in Stage 5's validator); here just confirm no target file
    # was modified in a way that breaks the leakage-safety invariant (never NaN->populated backwards)
    targets = pd.read_parquet(BASE / "data" / "processed" / "future_horizon_targets.parquet")
    bad = ((targets.future_5_match_performance.notna()) & (targets.future_3_match_performance.isna())).sum()
    record("future_5 never populated when future_3 is missing (horizon-ordering invariant)",
           bad == 0, f"{bad} violations")
    bad2 = ((targets.future_3_match_performance.notna()) & (targets.future_2_match_performance.isna())).sum()
    record("future_3 never populated when future_2 is missing", bad2 == 0, f"{bad2} violations")

    # --- same-cohort comparisons: spot check a few exp_* tables for identical n across methods
    # within the same grouping key ---
    pos = pd.read_csv(TABLES / "exp_position.csv")
    n_by_pos_method = pos.pivot_table(index="position_group", columns="method", values="n")
    same_n = (n_by_pos_method.nunique(axis=1) == 1).all()
    record("exp_position.csv: identical n across all methods within each position (common cohort)",
           bool(same_n), "")

    horizons = pd.read_csv(TABLES / "exp_future_horizons.csv")
    n_by_horizon_method = horizons.pivot_table(index="horizon", columns="method", values="n")
    same_n2 = (n_by_horizon_method.nunique(axis=1) == 1).all()
    record("exp_future_horizons.csv: identical n across all methods within each horizon (common cohort)",
           bool(same_n2), "")

    # --- player-clustered bootstrap: seed recorded, n_boot recorded ---
    boot = pd.read_csv(TABLES / "exp_bootstrap_effects.csv")
    record("exp_bootstrap_effects.csv records seed and n_boot for every row",
           (boot.seed == 42).all() and (boot.n_boot == 2000).all(), "")

    # --- fixed random seeds used consistently ---
    record("Bootstrap seed is the fixed value 42 throughout (matches Stage 5's own seed)",
           (boot.seed == 42).all(), "")

    # --- table/figure consistency: every referenced exp_ table has a corresponding file ---
    required_tables = [
        "exp_future_horizons.csv", "exp_temporal_folds.csv", "exp_history_depth.csv",
        "exp_position.csv", "exp_gk_diagnosis.csv", "exp_att_diagnosis.csv",
        "exp_opponent_scale.csv", "exp_history_decay.csv", "exp_k_sensitivity.csv",
        "exp_minutes_weight.csv", "exp_score_ablation.csv", "exp_category_ablation.csv",
        "exp_combination.csv", "exp_ranking.csv", "exp_momentum.csv", "exp_decline.csv",
        "exp_team_context.csv", "exp_starter_sub.csv", "exp_target_stability.csv",
        "exp_bootstrap_effects.csv",
    ]
    missing_tables = [t for t in required_tables if not (TABLES / t).exists()]
    record("All 20 required exp_*.csv tables exist", len(missing_tables) == 0, f"missing: {missing_tables}")

    # --- no impossible sample sizes (n > 0, n <= total scoreable population) ---
    bad_n_files = []
    for t in required_tables:
        df = pd.read_csv(TABLES / t)
        if "n" in df.columns:
            if (df.n <= 0).any() or (df.n > 50_000).any():
                bad_n_files.append(t)
    record("No impossible sample sizes (n<=0 or n>50000) in any exp_ table", len(bad_n_files) == 0,
           f"files with issues: {bad_n_files}")

    # --- no duplicated experiment rows (spot check a few key tables for exact-duplicate rows) ---
    dup_files = []
    for t in ["exp_future_horizons.csv", "exp_position.csv", "exp_history_depth.csv"]:
        df = pd.read_csv(TABLES / t)
        if df.duplicated().any():
            dup_files.append(t)
    record("No fully-duplicated rows in spot-checked exp_ tables", len(dup_files) == 0, f"{dup_files}")

    # --- all reported claims trace back to an experiment table (spot check ClaimAudit references) ---
    claim_audit = (DOCS / "ClaimAudit.md").read_text()
    referenced_tables = [t for t in required_tables if t in claim_audit]
    record("ClaimAudit.md references at least 10 of the exp_ tables by filename",
           len(referenced_tables) >= 10, f"{len(referenced_tables)} tables referenced")

    # --- no NaN/inf in headline outputs ---
    headline = pd.read_csv(TABLES / "stage5_primary_method_comparison.csv")
    bad_headline = headline[["MAE", "RMSE", "Pearson", "Spearman"]].isna().sum().sum() + \
        np.isinf(headline[["MAE", "RMSE", "Pearson", "Spearman"]].to_numpy()).sum()
    record("No NaN/inf in the headline primary-method-comparison table", bad_headline == 0, f"{bad_headline} bad values")

    # --- required documents exist ---
    required_docs = ["ClaimAudit.md", "SimpleFootballFindings.md"]
    missing_docs = [d for d in required_docs if not (DOCS / d).exists()]
    required_reports = ["ExperimentIndex.md", "ExpandedExperimentalResultsReport.md", "Stage5ReproductionCheck.md"]
    missing_reports = [r for r in required_reports if not (REPORTS / r).exists()]
    record("Required docs (ClaimAudit.md, SimpleFootballFindings.md) exist", len(missing_docs) == 0, f"{missing_docs}")
    record("Required reports (ExperimentIndex, ExpandedExperimentalResultsReport, Stage5ReproductionCheck) exist",
           len(missing_reports) == 0, f"{missing_reports}")

    blocking = [c for c in checks if c["blocking"]]
    all_pass = all(c["result"] == "PASS" for c in blocking)

    print(f"Stage 6 validation: {'ALL BLOCKING CHECKS PASS' if all_pass else 'FAILURES FOUND'} "
          f"({sum(c['result']=='PASS' for c in blocking)}/{len(blocking)})")
    for c in checks:
        print(f"[{c['result']}] {c['check']} -- {c['detail']}")

    report_path = REPORTS / "Stage6ValidationReport.md"
    lines = ["# Stage 6 Validation Report\n\n",
             f"**Overall: {'ALL PASS' if all_pass else 'FAILURES FOUND'}** "
             f"({sum(c['result']=='PASS' for c in blocking)}/{len(blocking)})\n\n",
             "| Check | Result | Detail |\n|---|---|---|\n"]
    for c in checks:
        lines.append(f"| {c['check']} | {c['result']} | {str(c['detail']).replace('|', chr(92)+'|')[:200]} |\n")
    report_path.write_text("".join(lines))
    print(f"\nWrote {report_path}")

    if not all_pass:
        raise SystemExit("Stage 6 blocking checks failed.")


if __name__ == "__main__":
    main()
