"""
Stage 5, Task 17: objective error/failure case selection. No cherry-picking by name.
"""
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"
REPORTS = BASE / "outputs" / "reports"

VC = "variant_C_rating_calibrated"
VA = "variant_A_rating_calibrated"
VB = "variant_B_rating_calibrated"
L5 = "baseline_last5_calibrated"


def describe(row):
    return (f"- Player ID: `{row.player_id}`, Position: {row.position_group}\n"
            f"- Match ID: `{row.match_id}`, Date: {str(row.match_datetime_utc)[:10]}\n"
            f"- Variant C prediction: {row[VC]:.1f}, Actual future-3: {row.future_3_match_performance:.1f}, "
            f"error: {row[VC]-row.future_3_match_performance:+.1f}\n"
            f"- last5 prediction: {row[L5]:.1f}\n\n")


def main():
    df = pd.read_parquet(PROCESSED / "player_rating_predictive_evaluation.parquet")
    test = df[(df.split == "test") & df.future_3_match_performance.notna()].copy()
    for col in [VC, VA, VB, L5]:
        test = test[test[col].notna()]

    test["error_C"] = test[VC] - test.future_3_match_performance
    test["error_last5"] = test[L5] - test.future_3_match_performance
    test["C_advantage_over_last5"] = test.error_last5.abs() - test.error_C.abs()
    test["opp_adj_shift"] = test[VB] - test[VA]

    cases = {
        "variant_c_strongly_overpredicts": test.error_C.idxmax(),
        "variant_c_strongly_underpredicts": test.error_C.idxmin(),
        "last5_beats_variant_c_by_a_lot": test.C_advantage_over_last5.idxmin(),
        "variant_c_beats_last5_by_a_lot": test.C_advantage_over_last5.idxmax(),
        "opponent_adjustment_helps_substantially": (test[VB] - test.future_3_match_performance).abs().sub(
            (test[VA] - test.future_3_match_performance).abs()).idxmin(),
        "opponent_adjustment_hurts_substantially": (test[VB] - test.future_3_match_performance).abs().sub(
            (test[VA] - test.future_3_match_performance).abs()).idxmax(),
    }

    lines = ["# Stage 5 Prediction Error Cases\n\n",
             "Selected by objective, reproducible criteria on the test-split common cohort "
             "(`data/processed/player_rating_predictive_evaluation.parquet`) -- no cherry-picking.\n\n"]
    for name, idx in cases.items():
        lines.append(f"## {name.replace('_', ' ').title()}\n\n")
        lines.append(describe(test.loc[idx]))

    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "Stage5PredictionErrorCases.md").write_text("".join(lines))
    print(f"Wrote {REPORTS / 'Stage5PredictionErrorCases.md'}")
    for name, idx in cases.items():
        print(name, "->", test.loc[idx, "player_id"])


if __name__ == "__main__":
    main()
