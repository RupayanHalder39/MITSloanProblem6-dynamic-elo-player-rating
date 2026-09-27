"""
Stage 6, Experiment Block 1: rerun the Stage-5 pipeline end-to-end from the saved intermediate
parquets (not from raw SQL -- that part of the pipeline is already validated in Stages 2-3 and
re-running the 6.2GB extraction is not what this check is for) and confirm the headline numbers
match exactly. If they differ materially, Stage 6 experiments should not proceed until investigated.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"
TABLES = BASE / "outputs" / "tables"
REPORTS = BASE / "outputs" / "reports"

sys.path.insert(0, str(BASE / "src" / "analysis"))
from evaluate_dynamic_rating import METHOD_COLS, metrics_for, common_cohort  # noqa: E402


def main():
    df = pd.read_parquet(PROCESSED / "player_rating_predictive_evaluation.parquet")
    test = df[df.split == "test"]
    cohort3 = common_cohort(test, "future_3_match_performance")

    rows = []
    for name, col in METHOD_COLS.items():
        m = metrics_for(cohort3[col].to_numpy(), cohort3.future_3_match_performance.to_numpy())
        rows.append({"method": name, **m})
    reproduced = pd.DataFrame(rows).set_index("method")

    original = pd.read_csv(TABLES / "stage5_primary_method_comparison.csv").set_index("method")

    lines = ["# Stage 5 Reproduction Check\n\n",
              "Rerun of the Stage-5 primary comparison (future-3, test split, common cohort) from "
              "the saved Stage-2/3/4 intermediate parquets, to confirm Stage 6 experiments start "
              "from a verified-stable baseline.\n\n",
              f"**Common cohort n:** reproduced={len(cohort3)}, original=11353\n\n",
              "| Method | MAE (orig) | MAE (reproduced) | Match? | Spearman (orig) | Spearman (reproduced) | Match? |\n",
              "|---|---|---|---|---|---|---|\n"]

    all_match = len(cohort3) == 11353
    for name in METHOD_COLS:
        o_mae, r_mae = original.loc[name, "MAE"], reproduced.loc[name, "MAE"]
        o_sp, r_sp = original.loc[name, "Spearman"], reproduced.loc[name, "Spearman"]
        mae_match = np.isclose(o_mae, r_mae, atol=1e-6)
        sp_match = np.isclose(o_sp, r_sp, atol=1e-6)
        all_match &= mae_match and sp_match
        lines.append(f"| {name} | {o_mae} | {r_mae} | {'YES' if mae_match else '**NO**'} | "
                      f"{o_sp} | {r_sp} | {'YES' if sp_match else '**NO**'} |\n")

    lines.append(f"\n**Overall: {'EXACT REPRODUCTION -- PROCEED WITH STAGE 6' if all_match else 'MISMATCH FOUND -- INVESTIGATE BEFORE PROCEEDING'}**\n")

    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "Stage5ReproductionCheck.md").write_text("".join(lines))
    print(f"Wrote {REPORTS / 'Stage5ReproductionCheck.md'}")
    print("EXACT REPRODUCTION" if all_match else "MISMATCH FOUND")
    print(reproduced)

    if not all_match:
        raise SystemExit("Stage 5 reproduction mismatch -- stopping before Stage 6 experiments.")


if __name__ == "__main__":
    main()
