"""
Stage 4: the chronological dynamic player-rating engine.

Builds 3 rating variants (A: simple, B: opponent-adjusted, C: history-aware) over the Stage-3
scoreable population, strictly chronologically, with same-match freezing (all pre-match states for
a given match_id are snapshotted before any of that match's updates are applied).

See docs/PlayerRatingStateDefinition.md, docs/DynamicRatingScale.md, docs/PlayerRatingColdStart.md,
docs/ExpectedPerformanceDesign.md, docs/PerformanceSurpriseDefinition.md,
docs/DynamicRatingUpdateRules.md, docs/MinutesRatingUpdatePolicy.md, docs/InactivityPolicy.md for
the full design reasoning behind every constant and rule used here.

NON-NEGOTIABLE LEAKAGE RULE: pre_match_player_rating for a match uses only information from
matches strictly before it. The processing order is structurally: (1) read state, (2) record
pre-match rating, (3) compute expectation, (4) look up the Stage-3 actual score, (5) compute
surprise, (6) update state, (7) advance. Never performance -> rating -> labeled "pre-match".
"""
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"

# --- docs/DynamicRatingScale.md ---
INITIAL_RATING = 1500.0
RATING_SCALE = 40.0

# --- docs/ExpectedPerformanceDesign.md ---
POSITION_BASELINE = {
    "GK": 1.68, "MID": 1.13, "DEF": 0.90, "ATT": 0.62, "UNKNOWN": 1.00,
}
OPPONENT_SCALE = 0.03

# --- docs/DynamicRatingUpdateRules.md ---
K_BASE = 3.0
HISTORY_FLOOR = 0.4
HISTORY_M0 = 15.0

# --- docs/MinutesRatingUpdatePolicy.md ---
CONFIDENCE_WEIGHT = {"LOW": 0.4, "MEDIUM": 0.7, "HIGH": 1.0}

# --- docs/InactivityPolicy.md ---
BASE_UNCERTAINTY = 100.0
GAP_FACTOR = 5.0


def expectation_a(rating: float, position_group: str) -> float:
    baseline = POSITION_BASELINE.get(position_group, POSITION_BASELINE["UNKNOWN"])
    return float(np.clip(50.0 + baseline + (rating - INITIAL_RATING) / RATING_SCALE, 0, 100))


def expectation_b(rating: float, position_group: str, elo_difference: float) -> float:
    base = expectation_a(rating, position_group)
    return float(np.clip(base + OPPONENT_SCALE * elo_difference, 0, 100))


def history_decay(matches_seen_before: int) -> float:
    return HISTORY_FLOOR + (1 - HISTORY_FLOOR) / (1 + matches_seen_before / HISTORY_M0)


def rating_uncertainty(matches_seen_before: int, days_since_last: float | None) -> float:
    val = BASE_UNCERTAINTY / np.sqrt(1 + matches_seen_before)
    if days_since_last is not None and days_since_last > 0:
        val += GAP_FACTOR * np.log1p(days_since_last / 30.0)
    return float(val)


class PlayerState:
    __slots__ = ("rating", "matches_seen", "last_match_date")

    def __init__(self):
        self.rating = INITIAL_RATING
        self.matches_seen = 0
        self.last_match_date = None


def run_variant(df: pd.DataFrame, variant: str) -> pd.DataFrame:
    """df must be the scoreable rows, sorted chronologically by (match_datetime_utc, match_id)."""
    states: dict[str, PlayerState] = {}
    rows = []

    # process one match at a time so all pre-match snapshots for that match are taken before ANY
    # update from that match is applied -- structural same-match freezing, per the brief.
    for match_id, match_rows in df.groupby("match_id", sort=False):
        match_rows = match_rows.sort_values("player_id")  # deterministic order, irrelevant to result
        pre_snapshots = []
        for _, r in match_rows.iterrows():
            pid = r.player_id
            st = states.setdefault(pid, PlayerState())
            days_since = None
            if st.last_match_date is not None:
                days_since = (r.match_datetime_utc - st.last_match_date).total_seconds() / 86400.0
            pre_snapshots.append({
                "row": r, "player_id": pid,
                "pre_match_player_rating": st.rating,
                "matches_seen_before": st.matches_seen,
                "pre_match_uncertainty": rating_uncertainty(st.matches_seen, days_since),
            })

        # now compute expectation/surprise/update using ONLY the frozen pre-match snapshots, and
        # apply updates only after every player's pre-match value has been read
        for snap in pre_snapshots:
            r = snap["row"]
            pos = r.position_group
            elo_diff = r.elo_difference
            rating = snap["pre_match_player_rating"]

            if variant == "A":
                expected = expectation_a(rating, pos)
                decay = 1.0
            elif variant == "B":
                expected = expectation_b(rating, pos, elo_diff)
                decay = 1.0
            elif variant == "C":
                expected = expectation_b(rating, pos, elo_diff)
                decay = history_decay(snap["matches_seen_before"])
            else:
                raise ValueError(variant)

            actual = r.final_stage3_score_candidate
            surprise = actual - expected
            conf_w = CONFIDENCE_WEIGHT[r.minutes_confidence]
            update_multiplier = K_BASE * decay * conf_w
            rating_change = update_multiplier * surprise
            post_rating = rating + rating_change

            rows.append({
                "match_id": r.match_id, "match_datetime_utc": r.match_datetime_utc,
                "player_id": r.player_id, "team_id": r.team_id,
                "opponent_team_id": r.opponent_team_id, "position_group": pos,
                "actual_performance_score": actual,
                "pre_match_player_rating": rating,
                "expected_performance": expected,
                "performance_surprise": surprise,
                "update_multiplier": update_multiplier,
                "rating_change": rating_change,
                "post_match_player_rating": post_rating,
                "matches_seen_before": snap["matches_seen_before"],
                "matches_seen_after": snap["matches_seen_before"] + 1,
                "pre_match_team_elo": r.pre_match_team_elo,
                "pre_match_opponent_elo": r.pre_match_opponent_elo,
                "pre_match_rating_uncertainty": snap["pre_match_uncertainty"],
                "rating_variant": variant,
                "confidence_tier": r.minutes_confidence,
            })

        # apply all of this match's updates AFTER every pre-match value was already read/used
        for snap, out_row in zip(pre_snapshots, rows[-len(pre_snapshots):]):
            st = states[snap["player_id"]]
            st.rating = out_row["post_match_player_rating"]
            st.matches_seen += 1
            st.last_match_date = out_row["match_datetime_utc"]

    return pd.DataFrame(rows)


def main():
    df = pd.read_parquet(PROCESSED / "player_match_performance.parquet")
    scoreable = df[df.score_eligible & df.final_stage3_score_candidate.notna()].copy()
    scoreable["match_datetime_utc"] = pd.to_datetime(scoreable.match_datetime_utc, utc=True)
    scoreable = scoreable.sort_values(["match_datetime_utc", "match_id"])

    variants = []
    for variant in ["A", "B", "C"]:
        out = run_variant(scoreable, variant)
        variants.append(out)
        print(f"Variant {variant}: {len(out)} rows, "
              f"final rating range [{out.post_match_player_rating.min():.1f}, "
              f"{out.post_match_player_rating.max():.1f}]")

    all_variants = pd.concat(variants, ignore_index=True)
    out_path = PROCESSED / "player_dynamic_ratings_candidates.parquet"
    all_variants.to_parquet(out_path)
    print(f"Wrote {out_path} ({len(all_variants)} total rows)")

    # Primary Stage-5 candidate written separately once selected -- see
    # docs/Stage4DynamicRatingDecision.md and build_primary_candidate() below, called by the
    # decision doc's own build step (kept separate so this script's job stays "build all variants").


def build_primary_candidate(variant: str = "B"):
    all_variants = pd.read_parquet(PROCESSED / "player_dynamic_ratings_candidates.parquet")
    primary = all_variants[all_variants.rating_variant == variant].copy()
    out_path = PROCESSED / "player_dynamic_rating_primary.parquet"
    primary.to_parquet(out_path)
    print(f"Wrote {out_path} (variant {variant}, {len(primary)} rows)")


if __name__ == "__main__":
    main()
