"""
Stage 6: a parametrized copy of Stage 4's rating engine (src/models/build_dynamic_player_rating.py),
used ONLY for sensitivity/ablation experiments (Experiment Blocks 8-11). Stage 4's own script is not
modified, per the brief's instruction not to alter Stages 2-4 without a genuine defect. This module
duplicates the same leakage-safe, same-match-freezing logic, but exposes OPPONENT_SCALE,
HISTORY_FLOOR, HISTORY_M0, K_BASE, and the confidence-weight map as function arguments instead of
module constants, so a small predefined grid can be swept without touching production code.
"""
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"

INITIAL_RATING = 1500.0
RATING_SCALE = 40.0
POSITION_BASELINE = {"GK": 1.68, "MID": 1.13, "DEF": 0.90, "ATT": 0.62, "UNKNOWN": 1.00}


def expectation(rating, position_group, elo_difference, opponent_scale, use_opponent):
    base = 50.0 + POSITION_BASELINE.get(position_group, POSITION_BASELINE["UNKNOWN"]) + \
        (rating - INITIAL_RATING) / RATING_SCALE
    if use_opponent:
        base += opponent_scale * elo_difference
    return float(np.clip(base, 0, 100))


def history_decay(matches_seen_before, floor, m0):
    return floor + (1 - floor) / (1 + matches_seen_before / m0)


class PlayerState:
    __slots__ = ("rating", "matches_seen")

    def __init__(self):
        self.rating = INITIAL_RATING
        self.matches_seen = 0


def run_sensitivity_variant(
    df: pd.DataFrame, *, use_opponent: bool, use_history_decay: bool,
    k_base: float = 3.0, opponent_scale: float = 0.03,
    history_floor: float = 0.4, history_m0: float = 15.0,
    confidence_weight: dict | None = None,
) -> pd.DataFrame:
    """df must be the scoreable rows, sorted chronologically by (match_datetime_utc, match_id)."""
    confidence_weight = confidence_weight or {"LOW": 0.4, "MEDIUM": 0.7, "HIGH": 1.0}
    states: dict = {}
    rows = []

    for match_id, match_rows in df.groupby("match_id", sort=False):
        match_rows = match_rows.sort_values("player_id")
        pre_snapshots = []
        for _, r in match_rows.iterrows():
            pid = r.player_id
            st = states.setdefault(pid, PlayerState())
            pre_snapshots.append({"row": r, "player_id": pid, "pre_rating": st.rating,
                                   "matches_seen_before": st.matches_seen})

        for snap in pre_snapshots:
            r = snap["row"]
            rating = snap["pre_rating"]
            expected = expectation(rating, r.position_group, r.elo_difference, opponent_scale, use_opponent)
            decay = history_decay(snap["matches_seen_before"], history_floor, history_m0) if use_history_decay else 1.0
            actual = r.final_stage3_score_candidate
            surprise = actual - expected
            conf_w = confidence_weight.get(r.minutes_confidence, 1.0)
            update_multiplier = k_base * decay * conf_w
            rating_change = update_multiplier * surprise
            post_rating = rating + rating_change
            rows.append({
                "match_id": r.match_id, "match_datetime_utc": r.match_datetime_utc,
                "player_id": r.player_id, "position_group": r.position_group,
                "pre_match_player_rating": rating, "expected_performance": expected,
                "performance_surprise": surprise, "rating_change": rating_change,
                "post_match_player_rating": post_rating,
                "matches_seen_before": snap["matches_seen_before"],
                "minutes_confidence": r.minutes_confidence, "split": r.get("split"),
            })

        for snap, out_row in zip(pre_snapshots, rows[-len(pre_snapshots):]):
            st = states[snap["player_id"]]
            st.rating = out_row["post_match_player_rating"]
            st.matches_seen += 1

    return pd.DataFrame(rows)
