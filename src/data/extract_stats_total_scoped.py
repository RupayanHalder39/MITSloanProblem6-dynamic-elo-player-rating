"""
Stage 3 needs the FULL column set of sports.player_match_stats_total (113 columns) for feature
inventory and scoring -- unlike Stage 2, which only needed minutes_played. Pulling all 4,871,866
global rows x 113 columns would be wasteful (the research scope is one competition, 1,554 matches).

Instead this streams the table's COPY block once and keeps only rows whose match_id (column 2) is
in the canonical Stage 2 foundation's match_id set, using awk for the filter (fast: a single pass,
array lookup, no per-row Python overhead) before handing the much smaller filtered stream to pandas.

Reads: match ids from data/processed/player_match_foundation.parquet (Stage 2 output).
Writes: data/processed/raw/player_match_stats_total_championship.parquet
"""
from pathlib import Path
import subprocess
import tempfile

import pandas as pd

from extract_sql_tables import DATA_SQL, _copy_block_line_range

BASE = Path(__file__).resolve().parents[2]
OUT = BASE / "data" / "processed" / "raw" / "player_match_stats_total_championship.parquet"

COLUMNS = [
    "player_id", "match_id", "minutes_played", "minutes_tagged", "matches_in_start",
    "matches_substituted", "matches_coming_off", "goals", "assists", "shots", "shots_on_target",
    "head_shots", "shots_blocked", "yellow_cards", "red_cards", "direct_red_cards", "penalties",
    "successful_penalties", "free_kicks", "free_kicks_on_target", "direct_free_kicks",
    "direct_free_kicks_on_target", "corners", "passes", "successful_passes", "smart_passes",
    "successful_smart_passes", "passes_to_final_third", "successful_passes_to_final_third",
    "forward_passes", "successful_forward_passes", "back_passes", "successful_back_passes",
    "through_passes", "successful_through_passes", "key_passes", "successful_key_passes",
    "vertical_passes", "successful_vertical_passes", "long_passes", "successful_long_passes",
    "lateral_passes", "successful_lateral_passes", "progressive_passes",
    "successful_progressive_passes", "crosses", "successful_crosses", "duels", "duels_won",
    "defensive_duels", "defensive_duels_won", "offensive_duels", "offensive_duels_won",
    "aerial_duels", "aerial_duels_won", "field_aerial_duels", "field_aerial_duels_won",
    "loose_ball_duels", "loose_ball_duels_won", "pressing_duels", "pressing_duels_won",
    "new_duels_won", "new_defensive_duels_won", "new_offensive_duels_won", "dribbles",
    "successful_dribbles", "new_successful_dribbles", "dribbles_against", "dribbles_against_won",
    "interceptions", "defensive_actions", "successful_defensive_action", "sliding_tackles",
    "successful_sliding_tackles", "clearances", "attacking_actions", "successful_attacking_actions",
    "linkup_plays", "successful_linkup_plays", "accelerations", "fouls", "fouls_suffered",
    "missed_balls", "shot_assists", "shot_on_target_assists", "second_assists", "third_assists",
    "recoveries", "opponent_half_recoveries", "dangerous_opponent_half_recoveries",
    "counterpressing_recoveries", "losses", "own_half_losses", "dangerous_own_half_losses",
    "received_pass", "touch_in_box", "progressive_run", "offsides", "gk_clean_sheets",
    "gk_conceded_goals", "gk_shots_against", "gk_exits", "gk_successful_exits", "gk_aerial_duels",
    "gk_aerial_duels_won", "gk_saves", "goal_kicks", "goal_kicks_short", "goal_kicks_long",
    "successful_goal_kicks", "xg_shot", "xg_assist", "xg_save",
]


def main(match_ids: list[str] | None = None):
    if match_ids is None:
        foundation = pd.read_parquet(BASE / "data" / "processed" / "player_match_foundation.parquet")
        match_ids = sorted(foundation.match_id.unique())

    start, end = _copy_block_line_range("player_match_stats_total")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("\n".join(match_ids))
        id_file = f.name

    # awk: load the match_id allowlist into an array, then stream the COPY block once, keeping
    # only rows whose 2nd tab-separated field is in that array. \r is stripped in the same pass.
    awk_prog = r'''
        BEGIN { FS="\t"; OFS="\t";
                while ((getline line < idfile) > 0) { ids[line] = 1 } }
        { sub(/\r$/, "");
          if ($2 in ids) print }
    '''
    sed = subprocess.Popen(["sed", "-n", f"{start},{end - 1}p", DATA_SQL], stdout=subprocess.PIPE)
    awk = subprocess.Popen(
        ["awk", "-v", f"idfile={id_file}", awk_prog],
        stdin=sed.stdout, stdout=subprocess.PIPE,
    )
    sed.stdout.close()

    df = pd.read_csv(awk.stdout, sep="\t", header=None, names=COLUMNS, na_values=["\\N"], dtype=str)
    awk.wait()
    Path(id_file).unlink()

    df = df[df.player_id != "\\."].reset_index(drop=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT)
    print(f"wrote {OUT} ({len(df)} rows, {len(match_ids)} match_ids requested)")
    return df


if __name__ == "__main__":
    main()
