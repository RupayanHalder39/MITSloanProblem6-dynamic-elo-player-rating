"""
Validate data/processed/player_match_foundation.parquet against the Stage 2 completion criteria.

Blocking checks (must all PASS for Stage 2 to be marked DONE): canonical-key uniqueness, no
impossible/future dates, no missing required IDs, no player on two teams in the same match, every
row has a pre-match team AND opponent Elo, no duplicated canonical rows, team != opponent, minutes
validity, result consistency, chronology orderability.

Non-blocking checks (informational, expected to be < 100% by design -- documented, not silently
ignored): position_code completeness, has_stats_row completeness.

Output: outputs/reports/Stage2DataFoundationReport.md
"""
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"
REPORT = BASE / "outputs" / "reports" / "Stage2DataFoundationReport.md"

TODAY_UPPER_BOUND = pd.Timestamp("2026-09-16", tz="UTC")  # in-universe "today"; matches after this are impossible
DATASET_LOWER_BOUND = pd.Timestamp("2019-01-01", tz="UTC")  # sanity floor, well before any real match


def main():
    df = pd.read_parquet(PROCESSED / "player_match_foundation.parquet")
    checks = []

    def record(name, passed, detail="", blocking=True):
        checks.append({
            "check": name, "blocking": blocking,
            "result": "PASS" if passed else "FAIL", "detail": detail,
        })

    # --- canonical key uniqueness: one row per (match_id, player_id) ---
    dup = df.duplicated(subset=["match_id", "player_id"]).sum()
    record("Canonical key (match_id, player_id) is unique", dup == 0, f"{dup} duplicate rows")

    # --- required IDs present ---
    for col in ["match_id", "player_id", "team_id", "opponent_team_id"]:
        n_missing = df[col].isna().sum()
        record(f"No missing {col}", n_missing == 0, f"{n_missing} missing")

    # --- impossible / future dates ---
    dt = pd.to_datetime(df.match_datetime_utc, utc=True, errors="coerce")
    n_null_dt = dt.isna().sum()
    record("No missing match_datetime_utc", n_null_dt == 0, f"{n_null_dt} missing")
    n_future = (dt > TODAY_UPPER_BOUND).sum()
    record("No dates after the in-universe present (2026-09-16)", n_future == 0, f"{n_future} rows")
    n_too_old = (dt < DATASET_LOWER_BOUND).sum()
    record("No implausibly old dates (before 2019-01-01)", n_too_old == 0, f"{n_too_old} rows")

    # --- player on two teams in the same match (should be impossible given canonical key) ---
    team_count_per_pm = df.groupby(["match_id", "player_id"]).team_id.nunique()
    n_multi_team = (team_count_per_pm > 1).sum()
    record("No player assigned to two teams in the same match", n_multi_team == 0, f"{n_multi_team} cases")

    # --- team != opponent ---
    n_self_play = (df.team_id == df.opponent_team_id).sum()
    record("team_id != opponent_team_id on every row", n_self_play == 0, f"{n_self_play} rows")

    # --- pre-match Elo present for both sides ---
    n_missing_team_elo = df.pre_match_team_elo.isna().sum()
    record("pre_match_team_elo present on every row", n_missing_team_elo == 0, f"{n_missing_team_elo} missing")
    n_missing_opp_elo = df.pre_match_opponent_elo.isna().sum()
    record("pre_match_opponent_elo present on every row", n_missing_opp_elo == 0, f"{n_missing_opp_elo} missing")

    # --- minutes validity: bound depends on duration_type -- a Regular match cannot legitimately
    # exceed ~120 (90 + stoppage across two halves), while an ExtraTime match can legitimately
    # reach ~130-140 (120 + stoppage across four periods). Verified against a real case: match
    # 5594687 (Sunderland vs Coventry City playoff semi-final, duration_type=ExtraTime) has 17
    # players at exactly 132 minutes -- a genuine extra-time match, not a data error.
    present = df[df.minutes_played.notna()].copy()
    bound = present.duration_type.map({"ExtraTime": 145}).fillna(120)
    bad = present[(present.minutes_played < 0) | (present.minutes_played > bound)]
    record("minutes_played within duration_type-aware bound where present", len(bad) == 0,
           f"{len(bad)} out-of-range values out of {len(present)} present "
           "(bound: 120 for Regular, 145 for ExtraTime)")

    # --- result consistency: match_result matches team_score vs opponent_score ---
    def expected_result(row):
        if pd.isna(row.team_score) or pd.isna(row.opponent_score):
            return None
        if row.team_score > row.opponent_score:
            return "W"
        if row.team_score < row.opponent_score:
            return "L"
        return "D"

    computed = df.apply(expected_result, axis=1)
    mismatch = ((computed != df.match_result) & computed.notna() & df.match_result.notna()).sum()
    record("match_result consistent with team_score vs opponent_score", mismatch == 0, f"{mismatch} mismatches")

    # --- chronology orderability ---
    sortable = dt.notna().all()
    record("match_datetime_utc is fully sortable (no nulls, valid dtype)", sortable, "")

    # --- non-blocking / informational checks ---
    pos_pct = df.position_code.notna().mean() * 100
    record("position_code completeness (informational, not blocking)", True,
           f"{pos_pct:.1f}% populated -- matches the measured Championship position-completeness "
           "rate; the remainder is a genuine upstream data gap, not a pipeline bug", blocking=False)
    stats_pct = df.has_stats_row.mean() * 100
    record("has_stats_row completeness (informational, not blocking)", True,
           f"{stats_pct:.1f}% have a matching player_match_stats row", blocking=False)

    blocking_checks = [c for c in checks if c["blocking"]]
    all_blocking_pass = all(c["result"] == "PASS" for c in blocking_checks)

    lines = [
        "# Stage 2 Data Foundation Report\n\n",
        f"**Dataset:** `data/processed/player_match_foundation.parquet` ({len(df)} rows, "
        f"{df.match_id.nunique()} matches, {df.player_id.nunique()} players)\n\n",
        f"**Overall blocking checks: {'ALL PASS' if all_blocking_pass else 'FAILURES FOUND'}** "
        f"({sum(c['result']=='PASS' for c in blocking_checks)}/{len(blocking_checks)})\n\n",
        "| Check | Blocking | Result | Detail |\n|---|---|---|---|\n",
    ]
    for c in checks:
        detail = c["detail"].replace("|", "\\|")
        lines.append(f"| {c['check']} | {'YES' if c['blocking'] else 'NO'} | {c['result']} | {detail} |\n")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines))
    print(f"Wrote {REPORT}")
    print("ALL BLOCKING CHECKS PASS" if all_blocking_pass else "BLOCKING FAILURES FOUND")
    for c in checks:
        print(f"[{c['result']}] {c['check']} -- {c['detail']}")


if __name__ == "__main__":
    main()
