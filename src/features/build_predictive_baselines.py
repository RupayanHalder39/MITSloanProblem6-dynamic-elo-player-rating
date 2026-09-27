"""
Stage 5, Task 3/timing convention: 6 simple baselines, all using the AFTER-MATCH-T convention
(docs/PredictionTimingConvention.md) -- "given everything we know after today's match, how well
will this player perform over the next few matches?" Every baseline INCLUDES match T's own score
(consistent with predicting from T's post-match state, matching how the dynamic rating's
post_match_player_rating is also used as a T-inclusive predictor).

Output: data/processed/predictive_baselines.parquet (join keys: match_id, player_id)
"""
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"


def main():
    df = pd.read_parquet(PROCESSED / "player_match_performance.parquet")
    scored = df[df.score_eligible & df.final_stage3_score_candidate.notna()].copy()
    scored["match_datetime_utc"] = pd.to_datetime(scored.match_datetime_utc, utc=True)
    scored = scored.sort_values(["player_id", "match_datetime_utc", "match_id"]).reset_index(drop=True)

    # position prior: precomputed constants, identical convention to docs/ExpectedPerformanceDesign.md
    # (Stage 3's population mean score by position) -- available before ANY match, the weakest
    # possible reference baseline.
    POSITION_PRIOR = {"GK": 51.68, "MID": 51.13, "DEF": 50.90, "ATT": 50.62, "UNKNOWN": 51.00}

    rows = []
    for pid, sub in scored.groupby("player_id", sort=False):
        sub = sub.sort_values(["match_datetime_utc", "match_id"]).reset_index(drop=True)
        scores = sub.final_stage3_score_candidate.to_numpy()
        seasons = sub.season_id.to_numpy()
        n = len(sub)
        for i in range(n):
            window_incl_T = scores[: i + 1]  # everything up to and including T -- the AFTER-T convention
            last1 = scores[i]
            last3 = window_incl_T[-3:].mean()
            last5 = window_incl_T[-5:].mean()
            career_to_date = window_incl_T.mean()
            season_mask = seasons[: i + 1] == seasons[i]
            season_to_date = window_incl_T[season_mask].mean()
            rows.append({
                "match_id": sub.loc[i, "match_id"], "player_id": pid,
                "baseline_last1": last1,
                "baseline_last3": last3,
                "baseline_last5": last5,
                "baseline_season_to_date": season_to_date,
                "baseline_career_to_date": career_to_date,
                "baseline_position_prior": POSITION_PRIOR.get(sub.loc[i, "position_group"], 51.0),
            })

    baselines = pd.DataFrame(rows)
    out_path = PROCESSED / "predictive_baselines.parquet"
    baselines.to_parquet(out_path)
    print(f"Wrote {out_path} ({len(baselines)} rows)")
    print(baselines.describe())


if __name__ == "__main__":
    main()
