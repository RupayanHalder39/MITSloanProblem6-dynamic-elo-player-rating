"""
Stage 6, Experiment Block 2: extends Stage 5's future-3/future-5 target construction to multiple
horizons (1, 2, 3, 5, 7 matches), using the exact same leakage-safe logic (strictly AFTER match T,
full window required, NaN not zero when insufficient future history exists).
"""
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"

HORIZONS = [1, 2, 3, 5, 7]


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
            future = scores[i + 1:]
            n_future = len(future)
            row = {"match_id": sub.loc[i, "match_id"], "player_id": pid,
                   "future_matches_available": n_future}
            for h in HORIZONS:
                row[f"future_{h}_match_performance"] = future[:h].mean() if n_future >= h else None
            rows.append(row)

    targets = pd.DataFrame(rows)
    out_path = PROCESSED / "future_horizon_targets.parquet"
    targets.to_parquet(out_path)
    print(f"Wrote {out_path} ({len(targets)} rows)")
    for h in HORIZONS:
        n_ok = targets[f"future_{h}_match_performance"].notna().sum()
        print(f"future_{h}: {n_ok} evaluable rows ({n_ok/len(targets)*100:.1f}%)")


if __name__ == "__main__":
    main()
