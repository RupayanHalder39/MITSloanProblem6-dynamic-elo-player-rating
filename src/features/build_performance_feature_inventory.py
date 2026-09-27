"""
Stage 3, Task 1: full statistical + semantic inventory of every column in
sports.player_match_stats_total (113 columns total: player_id, match_id, + 111 performance
columns), scoped to the chosen research population (Championship, Stage-2 canonical match set).

Outputs:
  outputs/tables/performance_feature_inventory.csv  (machine-readable, one row per column)
  docs/PerformanceFeatureInventory.md               (human-readable summary, grouped by category)

Every "interpretation"/"category"/"metric_type"/"position_relevance"/"redundancy" annotation below
was written from the column name + verified against measured statistics (distribution, and for
suspected duplicates, direct row-by-row equality/correlation checks -- see the "redundancy" column
and docs/PerformanceFeatureInventory.md's "Confirmed redundancies" section for the exact numbers).
Anything whose meaning could not be pinned down this way is marked SEMANTICS UNVERIFIED and is
excluded from every score candidate in this stage.
"""
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[2]
RAW = BASE / "data" / "processed" / "raw"
TABLES = BASE / "outputs" / "tables"
DOCS = BASE / "docs"

STATS_PATH = RAW / "player_match_stats_total_championship.parquet"

# category, metric_type (count/rate/percent/expected/binary), position_relevance, interpretation,
# redundant_with (or None), semantics_unverified (bool)
ANNOTATIONS = {
    "minutes_played": ("MINUTES", "count", "ALL", "Minutes on the pitch", None, False),
    "minutes_tagged": ("MINUTES", "count", "ALL", "Minutes with tracked event data (duplicate of minutes_played in this scope)", "minutes_played", False),
    "matches_in_start": ("MINUTES", "binary", "ALL", "Started the match (0/1)", None, False),
    "matches_substituted": ("MINUTES", "binary", "ALL", "Was substituted off (0/1)", None, False),
    "matches_coming_off": ("MINUTES", "binary", "ALL", "Came on as a substitute (0/1)", None, False),
    "goals": ("ATTACKING", "count", "ATT/MID", "Goals scored", None, False),
    "assists": ("CREATION", "count", "ATT/MID", "Assists", None, False),
    "shots": ("ATTACKING", "count", "ATT/MID", "Total shots", None, False),
    "shots_on_target": ("ATTACKING", "count", "ATT/MID", "Shots on target", None, False),
    "head_shots": ("ATTACKING", "count", "ATT", "Headed shots", None, False),
    "shots_blocked": ("ATTACKING", "count", "ATT", "Own shots blocked by opponent", None, False),
    "yellow_cards": ("DISCIPLINE", "count", "ALL", "Yellow cards", None, False),
    "red_cards": ("DISCIPLINE", "count", "ALL", "Red cards (incl. second yellow)", None, False),
    "direct_red_cards": ("DISCIPLINE", "count", "ALL", "Direct red cards", None, False),
    "penalties": ("ATTACKING", "count", "ATT", "Penalties taken", None, False),
    "successful_penalties": ("ATTACKING", "count", "ATT", "Penalties scored", None, False),
    "free_kicks": ("ATTACKING", "count", "ATT/MID", "Free kicks taken", None, False),
    "free_kicks_on_target": ("ATTACKING", "count", "ATT/MID", "Free kicks on target", None, False),
    "direct_free_kicks": ("ATTACKING", "count", "ATT/MID", "Direct free-kick shots", None, False),
    "direct_free_kicks_on_target": ("ATTACKING", "count", "ATT/MID", "Direct free kicks on target", None, False),
    "corners": ("CREATION", "count", "MID/ATT", "Corners taken", None, False),
    "passes": ("POSSESSION", "count", "ALL", "Total passes attempted", None, False),
    "successful_passes": ("POSSESSION", "count", "ALL", "Passes completed", None, False),
    "smart_passes": ("CREATION", "count", "MID/ATT", "Line-breaking creative passes", None, False),
    "successful_smart_passes": ("CREATION", "count", "MID/ATT", "Completed smart passes", None, False),
    "passes_to_final_third": ("POSSESSION", "count", "MID/DEF", "Passes into the attacking third", None, False),
    "successful_passes_to_final_third": ("POSSESSION", "count", "MID/DEF", "Completed passes into the attacking third", None, False),
    "forward_passes": ("POSSESSION", "count", "ALL", "Forward-direction passes", None, False),
    "successful_forward_passes": ("POSSESSION", "count", "ALL", "Completed forward passes", None, False),
    "back_passes": ("POSSESSION", "count", "ALL", "Backward-direction passes", None, False),
    "successful_back_passes": ("POSSESSION", "count", "ALL", "Completed backward passes", None, False),
    "through_passes": ("CREATION", "count", "MID/ATT", "Through balls", None, False),
    "successful_through_passes": ("CREATION", "count", "MID/ATT", "Completed through balls", None, False),
    "key_passes": ("CREATION", "count", "MID/ATT", "Passes directly leading to a shot", None, False),
    "successful_key_passes": ("CREATION", "count", "MID/ATT", "Completed key passes (near-duplicate of key_passes by definition)", "key_passes", False),
    "vertical_passes": ("POSSESSION", "count", "ALL", "Vertical-direction passes (100% identical to lateral_passes in this scope -- SEE REDUNDANCY)", "lateral_passes", False),
    "successful_vertical_passes": ("POSSESSION", "count", "ALL", "Completed vertical passes (100% identical to successful_lateral_passes)", "successful_lateral_passes", False),
    "long_passes": ("POSSESSION", "count", "ALL", "Long passes attempted", None, False),
    "successful_long_passes": ("POSSESSION", "count", "ALL", "Completed long passes", None, False),
    "lateral_passes": ("POSSESSION", "count", "ALL", "Lateral-direction passes (100% identical to vertical_passes -- SEMANTICS UNVERIFIED, likely a provider aliasing quirk for this competition)", "vertical_passes", True),
    "successful_lateral_passes": ("POSSESSION", "count", "ALL", "Completed lateral passes (100% identical to successful_vertical_passes)", "successful_vertical_passes", True),
    "progressive_passes": ("POSSESSION", "count", "MID/DEF", "Passes that significantly advance the ball", None, False),
    "successful_progressive_passes": ("POSSESSION", "count", "MID/DEF", "Completed progressive passes", None, False),
    "crosses": ("CREATION", "count", "MID/ATT", "Crosses attempted", None, False),
    "successful_crosses": ("CREATION", "count", "MID/ATT", "Completed crosses", None, False),
    "duels": ("DEFENDING", "count", "ALL", "Total duels contested", None, False),
    "duels_won": ("DEFENDING", "count", "ALL", "Duels won (legacy metric, 47.7% identical to new_duels_won -- SEE REDUNDANCY)", "new_duels_won", False),
    "defensive_duels": ("DEFENDING", "count", "DEF/MID", "Defensive duels contested", None, False),
    "defensive_duels_won": ("DEFENDING", "count", "DEF/MID", "Defensive duels won (legacy, 48.9% identical to new_defensive_duels_won)", "new_defensive_duels_won", False),
    "offensive_duels": ("ATTACKING", "count", "ATT/MID", "Offensive/dribble duels contested", None, False),
    "offensive_duels_won": ("ATTACKING", "count", "ATT/MID", "Offensive duels won (legacy, 75.1% identical to new_offensive_duels_won)", "new_offensive_duels_won", False),
    "aerial_duels": ("DEFENDING", "count", "DEF/ATT", "Aerial duels contested", None, False),
    "aerial_duels_won": ("DEFENDING", "count", "DEF/ATT", "Aerial duels won", None, False),
    "field_aerial_duels": ("DEFENDING", "count", "DEF/ATT", "Aerial duels excl. set pieces (98.3% identical to aerial_duels -- near-duplicate)", "aerial_duels", False),
    "field_aerial_duels_won": ("DEFENDING", "count", "DEF/ATT", "Won, excl. set pieces (98.4% identical to aerial_duels_won)", "aerial_duels_won", False),
    "loose_ball_duels": ("DEFENDING", "count", "ALL", "50/50 loose-ball duels contested", None, False),
    "loose_ball_duels_won": ("DEFENDING", "count", "ALL", "Loose-ball duels won", None, False),
    "pressing_duels": ("DEFENDING", "count", "DEF/MID", "Duels while pressing", None, False),
    "pressing_duels_won": ("DEFENDING", "count", "DEF/MID", "ALWAYS ZERO in this scope -- SEMANTICS UNVERIFIED / not populated for this competition", None, True),
    "new_duels_won": ("DEFENDING", "count", "ALL", "Duels won, provider's updated methodology -- preferred over legacy duels_won", None, False),
    "new_defensive_duels_won": ("DEFENDING", "count", "DEF/MID", "Defensive duels won, updated methodology -- preferred", None, False),
    "new_offensive_duels_won": ("ATTACKING", "count", "ATT/MID", "Offensive duels won, updated methodology -- preferred", None, False),
    "dribbles": ("ATTACKING", "count", "ATT/MID", "Dribble attempts", None, False),
    "successful_dribbles": ("ATTACKING", "count", "ATT/MID", "Completed dribbles (legacy, 84.4% identical to new_successful_dribbles)", "new_successful_dribbles", False),
    "new_successful_dribbles": ("ATTACKING", "count", "ATT/MID", "Completed dribbles, updated methodology -- preferred", None, False),
    "dribbles_against": ("DEFENDING", "count", "DEF", "Times dribbled past (faced)", None, False),
    "dribbles_against_won": ("DEFENDING", "count", "DEF", "Times successfully stopped a dribble against", None, False),
    "interceptions": ("DEFENDING", "count", "DEF/MID", "Interceptions", None, False),
    "defensive_actions": ("DEFENDING", "count", "DEF/MID", "Total defensive actions", None, False),
    "successful_defensive_action": ("DEFENDING", "count", "DEF/MID", "Successful defensive actions", None, False),
    "sliding_tackles": ("DEFENDING", "count", "DEF", "Sliding tackles", None, False),
    "successful_sliding_tackles": ("DEFENDING", "count", "DEF", "Completed sliding tackles", None, False),
    "clearances": ("DEFENDING", "count", "DEF", "Clearances", None, False),
    "attacking_actions": ("ATTACKING", "count", "ATT/MID", "Total attacking actions", None, False),
    "successful_attacking_actions": ("ATTACKING", "count", "ATT/MID", "Successful attacking actions", None, False),
    "linkup_plays": ("POSSESSION", "count", "MID/ATT", "Combination-play involvements", None, False),
    "successful_linkup_plays": ("POSSESSION", "count", "MID/ATT", "Successful combination plays", None, False),
    "accelerations": ("ATTACKING", "count", "ATT/MID", "Explosive sprint actions with the ball", None, False),
    "fouls": ("DISCIPLINE", "count", "ALL", "Fouls committed", None, False),
    "fouls_suffered": ("CONTEXT", "count", "ALL", "Fouls won", None, False),
    "missed_balls": ("DEFENDING", "count", "DEF", "Defensive misjudgments/errors", None, False),
    "shot_assists": ("CREATION", "count", "MID/ATT", "Passes leading to a shot (incl. indirect)", None, False),
    "shot_on_target_assists": ("CREATION", "count", "MID/ATT", "Passes leading to a shot on target", None, False),
    "second_assists": ("CREATION", "count", "MID/ATT", "Pass before the assist", None, False),
    "third_assists": ("CREATION", "count", "MID/ATT", "Pass two before the assist", None, False),
    "recoveries": ("DEFENDING", "count", "ALL", "Ball recoveries", None, False),
    "opponent_half_recoveries": ("DEFENDING", "count", "MID/ATT", "Recoveries in the opponent's half", None, False),
    "dangerous_opponent_half_recoveries": ("DEFENDING", "count", "MID/ATT", "High-value recoveries in the opponent's half", None, False),
    "counterpressing_recoveries": ("DEFENDING", "count", "MID/ATT", "Recoveries within seconds of losing the ball", None, False),
    "losses": ("DISCIPLINE", "count", "ALL", "Possession losses", None, False),
    "own_half_losses": ("DISCIPLINE", "count", "DEF/MID", "Possession losses in own half", None, False),
    "dangerous_own_half_losses": ("DISCIPLINE", "count", "DEF/MID", "High-risk losses in own half", None, False),
    "received_pass": ("POSSESSION", "count", "ALL", "Passes received", None, False),
    "touch_in_box": ("ATTACKING", "count", "ATT", "Touches inside the opponent's box", None, False),
    "progressive_run": ("ATTACKING", "count", "ATT/MID", "Ball-carrying runs that advance play significantly", None, False),
    "offsides": ("DISCIPLINE", "count", "ATT", "Offsides", None, False),
    "gk_clean_sheets": ("GOALKEEPING", "binary", "GK", "Clean sheet while on pitch (0/1)", None, False),
    "gk_conceded_goals": ("GOALKEEPING", "count", "GK", "Goals conceded", None, False),
    "gk_shots_against": ("GOALKEEPING", "count", "GK", "Shots faced", None, False),
    "gk_exits": ("GOALKEEPING", "count", "GK", "Claims/exits off the line", None, False),
    "gk_successful_exits": ("GOALKEEPING", "count", "GK", "ALWAYS ZERO in this scope -- SEMANTICS UNVERIFIED / not populated for this competition", None, True),
    "gk_aerial_duels": ("GOALKEEPING", "count", "GK", "Aerial duels contested by the GK", None, False),
    "gk_aerial_duels_won": ("GOALKEEPING", "count", "GK", "Aerial duels won by the GK", None, False),
    "gk_saves": ("GOALKEEPING", "count", "GK", "Saves made", None, False),
    "goal_kicks": ("GOALKEEPING", "count", "GK", "Goal kicks taken", None, False),
    "goal_kicks_short": ("GOALKEEPING", "count", "GK", "Short goal kicks", None, False),
    "goal_kicks_long": ("GOALKEEPING", "count", "GK", "Long goal kicks", None, False),
    "successful_goal_kicks": ("GOALKEEPING", "count", "GK", "Completed goal kicks", None, False),
    "xg_shot": ("ATTACKING", "expected", "ATT/MID", "Expected goals from this player's shots", None, False),
    "xg_assist": ("CREATION", "expected", "MID/ATT", "Expected goals from chances this player created", None, False),
    "xg_save": ("GOALKEEPING", "expected", "GK", "Expected-goals-value of shots saved (proxy for shot-stopping quality above expectation)", None, False),
}


def main():
    df = pd.read_parquet(STATS_PATH)
    rows = []
    for col, (category, mtype, posrel, interp, redundant_with, unverified) in ANNOTATIONS.items():
        s = pd.to_numeric(df[col], errors="coerce")
        rows.append({
            "column": col, "category": category, "metric_type": mtype,
            "position_relevance": posrel,
            "non_null_count": int(s.notna().sum()), "non_zero_count": int((s.fillna(0) != 0).sum()),
            "median": s.median(), "mean": round(s.mean(), 4) if s.notna().any() else None,
            "min": s.min(), "max": s.max(),
            "interpretation": interp,
            "redundant_with": redundant_with or "",
            "semantics_unverified": unverified,
        })
    inv = pd.DataFrame(rows)
    TABLES.mkdir(parents=True, exist_ok=True)
    inv.to_csv(TABLES / "performance_feature_inventory.csv", index=False)
    print(f"Wrote {TABLES / 'performance_feature_inventory.csv'} ({len(inv)} columns)")
    print("SEMANTICS UNVERIFIED columns:", inv[inv.semantics_unverified].column.tolist())
    print("Redundant columns:", inv[inv.redundant_with != ""][["column", "redundant_with"]].to_string())


if __name__ == "__main__":
    main()
