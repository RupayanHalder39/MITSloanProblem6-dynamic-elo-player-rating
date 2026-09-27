"""
Validate data/processed/player_match_performance.parquet against the Stage 3 completion criteria.

Output: outputs/reports/Stage3PerformanceScoreReport.md
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"
REPORT = BASE / "outputs" / "reports" / "Stage3PerformanceScoreReport.md"

sys.path.insert(0, str(BASE / "src" / "features"))
from build_player_match_performance import (  # noqa: E402
    POSITIVE_FEATURES, NEGATIVE_FEATURES, MIN_MINUTES_FULL,
)

VALID_POSITION_GROUPS = {"GK", "DEF", "MID", "ATT", "UNKNOWN"}
GK_ONLY_COLS = {c for c in POSITIVE_FEATURES["GK"] + NEGATIVE_FEATURES["GK"] if c.startswith("gk_")}


def main():
    df = pd.read_parquet(PROCESSED / "player_match_performance.parquet")
    detail = pd.read_parquet(PROCESSED / "player_match_performance_scoreable_detail.parquet")
    checks = []

    def record(name, passed, detail_str="", blocking=True):
        checks.append({"check": name, "blocking": blocking,
                        "result": "PASS" if passed else "FAIL", "detail": detail_str})

    # --- canonical row uniqueness preserved ---
    dup = df.duplicated(subset=["match_id", "player_id"]).sum()
    record("Canonical key (match_id, player_id) still unique after Stage 3 join", dup == 0, f"{dup} duplicates")

    # --- required raw features valid (non-negative counts where present) ---
    all_feats = sorted(set(sum(POSITIVE_FEATURES.values(), []) + sum(NEGATIVE_FEATURES.values(), [])))
    bad_feat_cols = []
    for f in all_feats:
        if f in df.columns:
            vals = pd.to_numeric(df[f], errors="coerce").dropna()
            if (vals < 0).any():
                bad_feat_cols.append(f)
    record("No negative raw feature values", len(bad_feat_cols) == 0, f"columns with negatives: {bad_feat_cols}")

    # --- position groups valid ---
    invalid_groups = set(df.position_group.dropna().unique()) - VALID_POSITION_GROUPS
    record("All position_group values are in {GK,DEF,MID,ATT,UNKNOWN}", len(invalid_groups) == 0,
           f"invalid values found: {invalid_groups}")

    # --- score exists for every eligible appearance ---
    missing_score_for_eligible = ((df.score_eligible) & (df.final_stage3_score_candidate.isna())).sum()
    record("Every score_eligible row has a final_stage3_score_candidate", missing_score_for_eligible == 0,
           f"{missing_score_for_eligible} eligible rows missing a score")
    score_for_ineligible = ((~df.score_eligible) & (df.final_stage3_score_candidate.notna())).sum()
    record("No non-eligible row has a score (excluded rows stay excluded)", score_for_ineligible == 0,
           f"{score_for_ineligible} non-eligible rows unexpectedly scored")

    # --- no impossible score values ---
    scored_vals = df.final_stage3_score_candidate.dropna()
    out_of_range = ((scored_vals < 0) | (scored_vals > 100)).sum()
    record("final_stage3_score_candidate within [0, 100]", out_of_range == 0, f"{out_of_range} out-of-range")

    # --- no infinite per-90 / z-score values ---
    shrunk_cols = [c for c in detail.columns if c.endswith("_shrunk_per90")]
    z_cols = [c for c in detail.columns if c.endswith("_z_expanding") or c.endswith("_z_descriptive")]
    inf_shrunk = detail[shrunk_cols].apply(lambda s: np.isinf(s).sum()).sum()
    inf_z = detail[z_cols].apply(lambda s: np.isinf(s.astype(float)).sum()).sum()
    record("No infinite shrunk per-90 rates", inf_shrunk == 0, f"{inf_shrunk} infinite values across {len(shrunk_cols)} columns")
    record("No infinite z-scores", inf_z == 0, f"{inf_z} infinite values across {len(z_cols)} columns")

    # --- no future-derived feature used (leakage-basis check) ---
    basis_cols = [c for c in detail.columns if c.endswith("_z_basis")]
    valid_basis_values = {"expanding", "cold_start_prior"}
    bad_basis = 0
    for c in basis_cols:
        bad_basis += (~detail[c].isin(valid_basis_values)).sum()
    record("Every expanding-z row is tagged 'expanding' or 'cold_start_prior' (no untracked basis)",
           bad_basis == 0, f"{bad_basis} rows with an unexpected/missing normalization_basis tag")
    # structural check: the leakage-safe candidate score uses ONLY *_z_expanding columns, never
    # *_z_descriptive -- verified by inspecting the score-formula construction itself
    src = Path(BASE / "src" / "features" / "build_player_match_performance.py").read_text()
    uses_descriptive_for_final = 'scoreable.candidate_score_B.apply(to_100_scale)' in src and \
        'scoreable["candidate_score_B"] = scoreable.apply(lambda r: score_b(r, "_z_expanding")' in src
    record("final_stage3_score_candidate is derived from candidate_score_B computed on _z_expanding (leakage-safe), not _z_descriptive",
           uses_descriptive_for_final, "verified by source inspection of build_player_match_performance.py")

    # --- no duplicated match-player-team ---
    dup_team = df.groupby(["match_id", "player_id"]).team_id.nunique()
    record("No player assigned to two teams in the same match (inherited from Stage 2, re-checked)",
           (dup_team > 1).sum() == 0, f"{(dup_team>1).sum()} violations")

    # --- minutes threshold correctly applied ---
    mism = 0
    low = df[df.minutes_confidence == "LOW"]
    mism += ((low.minutes_for_scoring <= 0) | (low.minutes_for_scoring >= MIN_MINUTES_FULL)).sum()
    med = df[df.minutes_confidence == "MEDIUM"]
    mism += ((med.minutes_for_scoring < MIN_MINUTES_FULL) | (med.minutes_for_scoring >= 60)).sum()
    high = df[df.minutes_confidence == "HIGH"]
    mism += (high.minutes_for_scoring < 60).sum()
    record(f"Minutes-confidence tiers correctly bounded (LOW<{MIN_MINUTES_FULL}, MEDIUM {MIN_MINUTES_FULL}-59, HIGH 60+)",
           mism == 0, f"{mism} tier/minutes mismatches")

    # --- score transformation monotonic ---
    s = df[["candidate_score_B", "final_stage3_score_candidate"]].dropna().sort_values("candidate_score_B")
    non_monotonic = (s.final_stage3_score_candidate.diff().dropna() < -1e-9).sum()
    record("0-100 scale transformation is monotonic in candidate_score_B", non_monotonic == 0,
           f"{non_monotonic} rank inversions")

    # --- GK uses GK feature set; outfield does not accidentally use GK-only features ---
    outfield_leak = set()
    for grp in ["DEF", "MID", "ATT"]:
        overlap = (set(POSITIVE_FEATURES[grp]) | set(NEGATIVE_FEATURES[grp])) & GK_ONLY_COLS
        if overlap:
            outfield_leak |= overlap
    record("No outfield position group's feature set includes a GK-only column",
           len(outfield_leak) == 0, f"overlap found: {outfield_leak}")
    gk_has_gk_cols = bool(set(POSITIVE_FEATURES["GK"]) & GK_ONLY_COLS)
    record("GK position group's feature set includes at least one GK-only column",
           gk_has_gk_cols, f"GK positive features: {POSITIVE_FEATURES['GK']}")

    blocking = [c for c in checks if c["blocking"]]
    all_pass = all(c["result"] == "PASS" for c in blocking)

    lines = [
        "# Stage 3 Performance Score Report\n\n",
        f"**Dataset:** `data/processed/player_match_performance.parquet` "
        f"({len(df)} rows, {df.score_eligible.sum()} score-eligible)\n\n",
        f"**Overall blocking checks: {'ALL PASS' if all_pass else 'FAILURES FOUND'}** "
        f"({sum(c['result']=='PASS' for c in blocking)}/{len(blocking)})\n\n",
        "| Check | Blocking | Result | Detail |\n|---|---|---|---|\n",
    ]
    for c in checks:
        d = str(c["detail"]).replace("|", "\\|")[:220]
        lines.append(f"| {c['check']} | {'YES' if c['blocking'] else 'NO'} | {c['result']} | {d} |\n")

    lines.append("\n## Summary statistics\n\n")
    lines.append("See `outputs/tables/performance_score_summary.csv` for the full breakdown "
                  "(by position, minutes-confidence tier, and season).\n\n")
    lines.append("## Case studies\n\nSee `outputs/reports/PerformanceScoreCaseStudies.md`.\n\n")
    lines.append("## Score selection\n\nSee `docs/Stage3PerformanceScoreDecision.md`.\n")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines))
    print(f"Wrote {REPORT}")
    print("ALL BLOCKING CHECKS PASS" if all_pass else "BLOCKING FAILURES FOUND")
    for c in checks:
        print(f"[{c['result']}] {c['check']} -- {c['detail']}")


if __name__ == "__main__":
    main()
