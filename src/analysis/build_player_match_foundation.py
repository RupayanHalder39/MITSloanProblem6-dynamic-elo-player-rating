"""
Build the Stage 2 canonical player-match foundation dataset.

Canonical population (per docs/CanonicalPlayerMatchDefinition.md): one row per
(match_id, player_id) pair FROM sports.match_player_appearances, restricted to the chosen research
scope (English Championship, competition_id=346; see docs/ResearchScopeSelection.md), Played
matches with a valid datetime and exactly 2 clean match_teams rows (the same match set the team
Elo was built on, so every row has a defined opponent and pre-match Elo by construction).

match_player_appearances is canonical -- not player_match_stats -- because it is the ONLY source
of team_id (and therefore opponent_id) per player-match; player_match_stats has broader match
coverage but cannot be assigned a team without it (see docs/AppearanceStatsReconciliation.md).
Stats/minutes/position are LEFT-joined onto this population; a missing stats row is recorded as
missing (has_stats_row = False / minutes_played = NaN), never silently dropped.

Output: data/processed/player_match_foundation.parquet
"""
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[2]
RAW = BASE / "data" / "processed" / "raw"
PROCESSED = BASE / "data" / "processed"

COMPETITION_ID = "346"  # English Championship -- see docs/ResearchScopeSelection.md

# Explicit, documented exclusion (NOT a silent drop -- see
# docs/PlayerMatchFoundationDataDictionary.md "Known exceptions"): match 5594316
# (Millwall vs Sunderland, 2024-11-23, duration_type=Regular) has 18 players recorded with
# minutes_played in [124, 130], which is not explainable by extra time (duration_type=Regular)
# and could not be explained by any legitimate stoppage-time scenario found during Stage 2
# validation. This is a confirmed upstream data-quality anomaly in the source stats feed for this
# one match, not a pipeline bug -- excluded from the canonical foundation dataset.
KNOWN_BAD_MATCH_IDS = {"5594316"}


def main():
    matches = pd.read_parquet(RAW / "matches.parquet")
    match_teams = pd.read_parquet(RAW / "match_teams.parquet")
    appearances = pd.read_parquet(RAW / "match_player_appearances.parquet")
    stats_spine = pd.read_parquet(RAW / "player_match_stats.parquet")
    positions = pd.read_parquet(RAW / "player_match_stats_positions.parquet")
    minutes = pd.read_parquet(RAW / "player_match_stats_minutes.parquet")
    players = pd.read_parquet(RAW / "players.parquet")
    elo = pd.read_parquet(PROCESSED / "team_elo_history.parquet")

    # --- 1. define the eligible match universe: same rule used for the team Elo build ---
    m = matches[(matches.competition_id == COMPETITION_ID) & (matches.status == "Played")].copy()
    m["match_datetime_utc"] = pd.to_datetime(m.match_datetime_utc, utc=True, errors="coerce")
    m = m.dropna(subset=["match_datetime_utc"])

    mt = match_teams[match_teams.match_id.isin(m.match_id)].copy()
    mt["score_num"] = pd.to_numeric(mt.score, errors="coerce")
    teams_per_match = mt.groupby("match_id").size()
    clean = teams_per_match[teams_per_match == 2].index
    mt = mt[mt.match_id.isin(clean)].dropna(subset=["score_num"])
    clean = mt.groupby("match_id").size()
    clean = clean[clean == 2].index
    mt = mt[mt.match_id.isin(clean)]

    # matches actually present in the Elo history (i.e. also passed the home==away/self-play guard)
    eligible_match_ids = set(elo.match_id) - KNOWN_BAD_MATCH_IDS
    mt = mt[mt.match_id.isin(eligible_match_ids)]
    m = m[m.match_id.isin(eligible_match_ids)]

    # --- 2. canonical population: appearance rows within the eligible match universe ---
    a = appearances[appearances.match_id.isin(eligible_match_ids)].copy()
    n_appearance_rows = len(a)

    # --- 3. opponent + score/result, via the OTHER side's match_teams row for the same match ---
    side_lookup = mt.set_index(["match_id", "team_id"])["side"].to_dict()
    score_lookup = mt.set_index(["match_id", "team_id"])["score_num"].to_dict()
    # per match, map each team_id -> the opposing team_id and its score
    opp_map = {}
    score_map = {}
    for mid, grp in mt.groupby("match_id"):
        t1, t2 = grp.team_id.tolist()
        s1, s2 = grp.score_num.tolist()
        opp_map[(mid, t1)] = t2
        opp_map[(mid, t2)] = t1
        score_map[(mid, t1)] = (s1, s2)
        score_map[(mid, t2)] = (s2, s1)

    a["opponent_team_id"] = a.apply(lambda r: opp_map.get((r.match_id, r.team_id)), axis=1)
    a["team_score"] = a.apply(lambda r: score_map.get((r.match_id, r.team_id), (None, None))[0], axis=1)
    a["opponent_score"] = a.apply(lambda r: score_map.get((r.match_id, r.team_id), (None, None))[1], axis=1)

    def result(row):
        if pd.isna(row.team_score) or pd.isna(row.opponent_score):
            return None
        if row.team_score > row.opponent_score:
            return "W"
        if row.team_score < row.opponent_score:
            return "L"
        return "D"

    a["match_result"] = a.apply(result, axis=1)

    # --- 4. match-level context (datetime, season, competition) ---
    a = a.merge(
        m[["match_id", "match_datetime_utc", "season_id", "competition_id", "duration_type"]],
        on="match_id", how="left",
    )

    # --- 5. pre-match team/opponent Elo, from the Elo history built with the SAME match set ---
    elo_home = elo[["match_id", "home_team_id", "pre_match_home_elo"]].rename(
        columns={"home_team_id": "team_id", "pre_match_home_elo": "elo_a"})
    elo_away = elo[["match_id", "away_team_id", "pre_match_away_elo"]].rename(
        columns={"away_team_id": "team_id", "pre_match_away_elo": "elo_a"})
    elo_by_team = pd.concat([elo_home, elo_away], ignore_index=True)
    a = a.merge(elo_by_team, on=["match_id", "team_id"], how="left")
    a = a.rename(columns={"elo_a": "pre_match_team_elo"})

    elo_opp = elo_by_team.rename(columns={"team_id": "opponent_team_id", "elo_a": "pre_match_opponent_elo"})
    a = a.merge(elo_opp, on=["match_id", "opponent_team_id"], how="left")
    a["elo_difference"] = a.pre_match_team_elo - a.pre_match_opponent_elo

    # --- 6. stats-row presence + minutes (LEFT join -- missing is recorded, not dropped) ---
    stats_keys = set(zip(stats_spine.player_id, stats_spine.match_id))
    a["has_stats_row"] = a.apply(lambda r: (r.player_id, r.match_id) in stats_keys, axis=1)

    minutes_dedup = minutes.drop_duplicates(subset=["player_id", "match_id"])
    a = a.merge(
        minutes_dedup[["player_id", "match_id", "minutes_played"]],
        on=["player_id", "match_id"], how="left",
    )
    a["minutes_played"] = pd.to_numeric(a.minutes_played, errors="coerce")

    # --- 7. position: primary position_code = highest-percent row per (match_id, player_id) ---
    positions_in_scope = positions[positions.match_id.isin(a.match_id.unique())].copy()
    positions_in_scope["percent"] = pd.to_numeric(positions_in_scope.percent, errors="coerce")
    positions_in_scope = positions_in_scope.sort_values("percent", ascending=False)
    primary_position = positions_in_scope.drop_duplicates(subset=["match_id", "player_id"], keep="first")
    n_positions_per_pm = positions_in_scope.groupby(["match_id", "player_id"]).size()
    multi_position_keys = set(n_positions_per_pm[n_positions_per_pm > 1].index)

    a = a.merge(
        primary_position[["match_id", "player_id", "position_code", "percent"]].rename(
            columns={"percent": "position_confidence_pct"}),
        on=["match_id", "player_id"], how="left",
    )
    a["is_multi_position_match"] = a.apply(
        lambda r: (r.match_id, r.player_id) in multi_position_keys, axis=1)

    # --- 8. coarse role from players master table ---
    a = a.merge(players[["player_id", "role_code"]].rename(columns={"role_code": "coarse_role"}),
                on="player_id", how="left")

    # --- final column selection, per the Task 7 spec ---
    out_cols = [
        "match_id", "match_datetime_utc", "season_id", "competition_id", "duration_type",
        "team_id", "opponent_team_id", "player_id",
        "minutes_played", "is_starting", "position_code", "position_confidence_pct",
        "is_multi_position_match", "coarse_role",
        "team_score", "opponent_score", "match_result",
        "pre_match_team_elo", "pre_match_opponent_elo", "elo_difference",
        "has_stats_row", "shirt_number", "goals", "assists", "own_goals",
    ]
    foundation = a[out_cols].reset_index(drop=True)

    PROCESSED.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED / "player_match_foundation.parquet"
    foundation.to_parquet(out_path)

    print(f"Canonical population (appearance rows in scope): {n_appearance_rows}")
    print(f"Foundation dataset rows: {len(foundation)}")
    print(f"Unique matches: {foundation.match_id.nunique()}")
    print(f"Unique players: {foundation.player_id.nunique()}")
    print(f"has_stats_row True: {foundation.has_stats_row.sum()} ({foundation.has_stats_row.mean()*100:.1f}%)")
    print(f"minutes_played non-null: {foundation.minutes_played.notna().sum()} ({foundation.minutes_played.notna().mean()*100:.1f}%)")
    print(f"position_code non-null: {foundation.position_code.notna().sum()} ({foundation.position_code.notna().mean()*100:.1f}%)")
    print(f"pre_match_team_elo non-null: {foundation.pre_match_team_elo.notna().sum()} ({foundation.pre_match_team_elo.notna().mean()*100:.1f}%)")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
