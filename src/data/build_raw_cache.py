"""
Populate data/processed/raw/*.parquet from the read-only master SQL dump, using the generic
extractor in extract_sql_tables.py. Column lists below are copied verbatim from each table's
CREATE TABLE statement in the dump (verified once via `grep -A CREATE TABLE sports.<table>`).

Run once per fresh checkout; re-run only if the upstream Data/ dump is refreshed. Takes several
minutes total for the larger tables (player_match_stats spine, match_player_appearances,
player_match_stats_positions) since the 6.2GB file is streamed once per table.

This script writes ONLY inside data/processed/raw/ under this project's own root.
"""
from pathlib import Path

from extract_sql_tables import save_table

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "processed" / "raw"

TABLES = {
    "matches": [
        "match_id", "competition_id", "season_id", "round_id", "winner_team_id",
        "match_datetime_utc", "gameweek", "status", "duration_type", "venue", "label",
        "has_data_available", "possession_dead_time", "possesion_total_time", "created_at",
    ],
    "match_teams": [
        "match_team_id", "match_id", "team_id", "coach_id", "side", "score", "score_ht",
        "score_ft", "score_et", "score_p", "has_formation", "created_at", "updated_at",
    ],
    "match_player_appearances": [
        "match_id", "team_id", "player_id", "is_starting", "shirt_number", "goals",
        "assists", "own_goals", "created_at", "updated_at",
    ],
    # the player_match_stats "spine" (NOT _total) -- 1:1 with _total/_average/_percent,
    # but only 7 columns, which is all Stage 2 needs to reconcile against appearances.
    "player_match_stats": [
        "player_id", "match_id", "competition_id", "season_id", "round_id",
        "created_at", "updated_at",
    ],
    "player_match_stats_positions": [
        "player_match_stats_position_id", "player_id", "match_id", "position_code", "percent",
    ],
    "competitions": [
        "competition_id", "area_id", "name", "format", "gender", "category", "type",
        "division_level", "created_at", "updated_at",
    ],
    "seasons": [
        "season_id", "competition_id", "super_season_id", "name", "start_date", "end_date",
        "active", "created_at", "updated_at",
    ],
    "players": [
        "player_id", "short_name", "first_name", "last_name", "birth_date", "birth_area_id",
        "passport_area_id", "second_citizenship_area_id", "role_code", "role_name", "foot",
        "height_cm", "weight_kg", "status", "image_url", "created_at", "updated_at",
    ],
}


def main():
    for table, columns in TABLES.items():
        out = RAW_DIR / f"{table}.parquet"
        path = save_table(table, columns, out)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
