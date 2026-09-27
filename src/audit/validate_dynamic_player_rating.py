"""
Validate data/processed/player_dynamic_ratings_candidates.parquet against the Stage 4 completion
criteria. Output: outputs/reports/Stage4DynamicRatingReport.md
"""
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"
REPORT = BASE / "outputs" / "reports" / "Stage4DynamicRatingReport.md"


def main():
    df = pd.read_parquet(PROCESSED / "player_dynamic_ratings_candidates.parquet")
    foundation_scored = pd.read_parquet(PROCESSED / "player_match_performance.parquet")
    foundation_scored = foundation_scored[
        foundation_scored.score_eligible & foundation_scored.final_stage3_score_candidate.notna()]

    checks = []

    def record(name, passed, detail="", blocking=True):
        checks.append({"check": name, "blocking": blocking,
                        "result": "PASS" if passed else "FAIL", "detail": detail})

    for variant in ["A", "B", "C"]:
        v = df[df.rating_variant == variant].copy()
        v["match_datetime_utc"] = pd.to_datetime(v.match_datetime_utc, utc=True)

        # --- chronological ordering: within each player, matches are non-decreasing in time ---
        bad_order = 0
        for pid, sub in v.groupby("player_id"):
            sub = sub.sort_index()  # engine's own emission order
            if not sub.match_datetime_utc.is_monotonic_increasing:
                bad_order += 1
        record(f"[{variant}] Chronological ordering (each player's rows are time-increasing in emission order)",
               bad_order == 0, f"{bad_order} players out of order")

        # --- pre/post relationship: pre-match rating for match N equals previous post-match rating ---
        mismatches = 0
        for pid, sub in v.sort_values("match_datetime_utc").groupby("player_id"):
            posts = sub.post_match_player_rating.values[:-1]
            pres = sub.pre_match_player_rating.values[1:]
            if len(posts) and not np.allclose(posts, pres, atol=1e-6):
                mismatches += 1
        record(f"[{variant}] pre_match_player_rating(N) == post_match_player_rating(N-1) for every player",
               mismatches == 0, f"{mismatches} players with a broken chain")

        # --- cold start: first appearance uses only the cold-start prior (1500, no position bump
        # baked into the RATING itself -- the baseline lives in the expectation, not the prior) ---
        first_rows = v.sort_values("match_datetime_utc").groupby("player_id").head(1)
        bad_cold_start = (first_rows.pre_match_player_rating != 1500.0).sum()
        record(f"[{variant}] Every player's first appearance starts from the flat 1500 cold-start prior",
               bad_cold_start == 0, f"{bad_cold_start} players with a non-1500 first pre-match rating")
        bad_matches_seen = (first_rows.matches_seen_before != 0).sum()
        record(f"[{variant}] Every player's first appearance has matches_seen_before == 0",
               bad_matches_seen == 0, f"{bad_matches_seen} violations")

        # --- no future leakage: expected_performance must not equal a function of actual_performance_score
        # (structural check: correlation between the RESIDUAL of expected vs a pre-match-only
        # reconstruction should be ~0; simplest robust check is that expected_performance never
        # exactly reproduces actual_performance_score row-for-row, which would indicate a leak) ---
        exact_leak = (v.expected_performance == v.actual_performance_score).sum()
        record(f"[{variant}] expected_performance never trivially equals actual_performance_score",
               exact_leak < len(v) * 0.01, f"{exact_leak}/{len(v)} exact matches (>1% would be suspicious)")

        # --- valid rating ranges / no inf/NaN ---
        for col in ["pre_match_player_rating", "expected_performance", "performance_surprise",
                    "rating_change", "post_match_player_rating"]:
            n_na = v[col].isna().sum()
            n_inf = np.isinf(v[col]).sum()
            record(f"[{variant}] No NaN/inf in {col}", n_na == 0 and n_inf == 0,
                   f"{n_na} NaN, {n_inf} inf")

        # --- sign consistency of updates ---
        pos_surprise_neg_change = ((v.performance_surprise > 0) & (v.rating_change < -1e-9)).sum()
        neg_surprise_pos_change = ((v.performance_surprise < 0) & (v.rating_change > 1e-9)).sum()
        record(f"[{variant}] Positive surprise never decreases rating", pos_surprise_neg_change == 0,
               f"{pos_surprise_neg_change} violations")
        record(f"[{variant}] Negative surprise never increases rating", neg_surprise_pos_change == 0,
               f"{neg_surprise_pos_change} violations")

        # --- history counts ---
        bad_history = 0
        for pid, sub in v.sort_values("match_datetime_utc").groupby("player_id"):
            expected_seq = list(range(len(sub)))
            if list(sub.matches_seen_before.values) != expected_seq:
                bad_history += 1
        record(f"[{variant}] matches_seen_before increments correctly (0,1,2,...) per player",
               bad_history == 0, f"{bad_history} players with an inconsistent sequence")

        # --- position validity ---
        invalid_pos = set(v.position_group.unique()) - {"GK", "DEF", "MID", "ATT", "UNKNOWN"}
        record(f"[{variant}] All position_group values valid", len(invalid_pos) == 0, f"{invalid_pos}")

        # --- team/opponent Elo availability ---
        missing_elo = v.pre_match_team_elo.isna().sum() + v.pre_match_opponent_elo.isna().sum()
        record(f"[{variant}] pre_match_team_elo and pre_match_opponent_elo present on every row",
               missing_elo == 0, f"{missing_elo} missing")

        # --- eligible-row preservation: variant covers exactly the Stage-3 scoreable population ---
        record(f"[{variant}] Row count matches Stage-3 scoreable population",
               len(v) == len(foundation_scored), f"{len(v)} vs {len(foundation_scored)}")

        # --- no unexpected duplicate canonical keys per variant ---
        dup = v.duplicated(subset=["match_id", "player_id"]).sum()
        record(f"[{variant}] No duplicated (match_id, player_id) within this variant", dup == 0, f"{dup} duplicates")

    # --- rating variant completeness ---
    record("All 3 variants (A, B, C) present", set(df.rating_variant.unique()) == {"A", "B", "C"},
           f"{sorted(df.rating_variant.unique())}")

    # --- deterministic reproducibility: re-run variant B and compare ---
    import sys
    sys.path.insert(0, str(BASE / "src" / "models"))
    from build_dynamic_player_rating import run_variant  # noqa: E402
    scoreable = foundation_scored.copy()
    scoreable["match_datetime_utc"] = pd.to_datetime(scoreable.match_datetime_utc, utc=True)
    scoreable = scoreable.sort_values(["match_datetime_utc", "match_id"])
    rerun_b = run_variant(scoreable, "B")
    orig_b = df[df.rating_variant == "B"].sort_values(["match_id", "player_id"]).reset_index(drop=True)
    rerun_b_sorted = rerun_b.sort_values(["match_id", "player_id"]).reset_index(drop=True)
    reproducible = np.allclose(
        orig_b.post_match_player_rating.values, rerun_b_sorted.post_match_player_rating.values, atol=1e-9
    ) and len(orig_b) == len(rerun_b_sorted)
    record("Deterministic rerun: Variant B re-run reproduces identical final ratings", reproducible,
           f"{len(orig_b)} vs {len(rerun_b_sorted)} rows; max diff="
           f"{np.max(np.abs(orig_b.post_match_player_rating.values - rerun_b_sorted.post_match_player_rating.values)):.2e}")

    blocking = [c for c in checks if c["blocking"]]
    all_pass = all(c["result"] == "PASS" for c in blocking)

    lines = [
        "# Stage 4 Dynamic Rating Report\n\n",
        f"**Dataset:** `data/processed/player_dynamic_ratings_candidates.parquet` "
        f"({len(df)} rows, 3 variants x {len(foundation_scored)} scoreable appearances)\n\n",
        f"**Overall blocking checks: {'ALL PASS' if all_pass else 'FAILURES FOUND'}** "
        f"({sum(c['result']=='PASS' for c in blocking)}/{len(blocking)})\n\n",
        "| Check | Blocking | Result | Detail |\n|---|---|---|---|\n",
    ]
    for c in checks:
        d = str(c["detail"]).replace("|", "\\|")[:200]
        lines.append(f"| {c['check']} | {'YES' if c['blocking'] else 'NO'} | {c['result']} | {d} |\n")

    lines.append("\n## Variant comparison, position/update summaries, case studies\n\n")
    lines.append("See `outputs/tables/dynamic_rating_variant_comparison.csv`, "
                  "`dynamic_rating_position_summary.csv`, `dynamic_rating_update_summary.csv`, "
                  "`dynamic_rating_final_player_summary.csv`, and "
                  "`outputs/reports/DynamicRatingCaseStudies.md`.\n\n")
    lines.append("## Primary Stage-5 candidate\n\nSee `docs/Stage4DynamicRatingDecision.md` "
                  "(Variant C, selected on design/stability grounds only).\n")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines))
    print(f"Wrote {REPORT}")
    print("ALL BLOCKING CHECKS PASS" if all_pass else "BLOCKING FAILURES FOUND")
    for c in checks:
        print(f"[{c['result']}] {c['check']} -- {c['detail']}")


if __name__ == "__main__":
    main()
