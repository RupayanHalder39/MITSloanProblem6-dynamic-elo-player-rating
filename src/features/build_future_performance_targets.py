"""
Stage 5, Task 1/2: leakage-safe future-performance targets.

For each scored appearance at match T for player P, look strictly forward in P's own chronological
sequence of scored appearances and take the mean of the NEXT 3 (and next 5) actual
final_stage3_score_candidate values. Match T's own score is NEVER included in its own target.
Rows with insufficient future history get NaN targets (NOT a bad-performance value) plus an
explicit future_matches_available count so "not evaluable" is never confused with "predicted zero."

Output: data/processed/future_performance_targets.parquet (join keys: match_id, player_id)
        outputs/tables/stage5_target_coverage.csv
"""
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"
TABLES = BASE / "outputs" / "tables"


def main():
    df = pd.read_parquet(PROCESSED / "player_match_performance.parquet")
    scored = df[df.score_eligible & df.final_stage3_score_candidate.notna()].copy()
    scored["match_datetime_utc"] = pd.to_datetime(scored.match_datetime_utc, utc=True)
    scored = scored.sort_values(["player_id", "match_datetime_utc", "match_id"]).reset_index(drop=True)

    rows = []
    for pid, sub in scored.groupby("player_id", sort=False):
        sub = sub.sort_values(["match_datetime_utc", "match_id"]).reset_index(drop=True)
        scores = sub.final_stage3_score_candidate.to_numpy()
        n = len(sub)
        for i in range(n):
            future = scores[i + 1:]  # strictly AFTER row i -- never includes row i itself
            n_future = len(future)
            rows.append({
                "match_id": sub.loc[i, "match_id"], "player_id": pid,
                # only a FULL 3 (or 5) -match window counts -- a partial 1-2 match average would be
                # a weaker, differently-defined signal, not "the future-3 target"; NaN (not zero)
                # when insufficient future history exists, so "not evaluable" != "predicted poorly"
                "future_3_match_performance": future[:3].mean() if n_future >= 3 else None,
                "future_3_matches_used": min(n_future, 3),
                "future_5_match_performance": future[:5].mean() if n_future >= 5 else None,
                "future_5_matches_used": min(n_future, 5),
                "future_matches_available": n_future,
            })

    targets = pd.DataFrame(rows)
    out_path = PROCESSED / "future_performance_targets.parquet"
    targets.to_parquet(out_path)
    print(f"Wrote {out_path} ({len(targets)} rows)")

    # --- Task 2: coverage audit ---
    merged = scored.merge(targets, on=["match_id", "player_id"])
    cov_rows = []

    def add(metric, value):
        cov_rows.append({"metric": metric, "value": value})

    add("total_scored_rows", len(merged))
    add("rows_with_ge1_future_match", int((merged.future_matches_available >= 1).sum()))
    add("rows_with_ge3_future_matches", int((merged.future_matches_available >= 3).sum()))
    add("rows_with_ge5_future_matches", int((merged.future_matches_available >= 5).sum()))
    add("unique_players_ge1_future", merged[merged.future_matches_available >= 1].player_id.nunique())
    add("unique_players_ge3_future", merged[merged.future_matches_available >= 3].player_id.nunique())
    add("unique_players_ge5_future", merged[merged.future_matches_available >= 5].player_id.nunique())

    for season, g in merged.groupby("season_id"):
        add(f"season_{season}_rows_ge3_future", int((g.future_matches_available >= 3).sum()))
        add(f"season_{season}_rows_ge5_future", int((g.future_matches_available >= 5).sum()))
        add(f"season_{season}_total_rows", len(g))

    for pos, g in merged.groupby("position_group"):
        add(f"position_{pos}_rows_ge3_future", int((g.future_matches_available >= 3).sum()))
        add(f"position_{pos}_rows_ge5_future", int((g.future_matches_available >= 5).sum()))

    # Experience-bucket coverage needs matches_seen_before, which lives in the rating candidates
    # parquet, not this one -- computed in the main evaluation build script instead, where ratings
    # are joined onto these targets.

    cov = pd.DataFrame(cov_rows)
    TABLES.mkdir(parents=True, exist_ok=True)
    cov.to_csv(TABLES / "stage5_target_coverage.csv", index=False)
    print(cov.to_string())


if __name__ == "__main__":
    main()
