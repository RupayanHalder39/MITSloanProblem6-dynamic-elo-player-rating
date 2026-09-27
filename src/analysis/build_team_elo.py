"""
Build a chronological, leakage-safe team-level Elo rating from match results, scoped to one
competition at a time (Stage 2 default: English Championship, competition_id=346 -- see
docs/ResearchScopeSelection.md for why).

Leakage rule (load-bearing): for a match at time T, the Elo value RECORDED as that match's
"pre-match" rating for each team is the team's rating immediately BEFORE T. Only after the
pre-match values are recorded does the match's own result get folded into an update. No match's
result ever informs its own pre-match rating.

This is deliberately simple per the Stage 2 brief ("keep it simple... this team Elo is NOT the
player rating, it is only an opponent-strength input"): standard Elo update, K constant, optional
home-advantage offset, draw = 0.5 score. Two variants are run and compared (with/without home
advantage); the with-home-advantage variant is used as the default going forward (see
docs/TeamOpponentStrengthMethod.md for the comparison and justification).

Inputs: data/processed/raw/matches.parquet, data/processed/raw/match_teams.parquet
Outputs: data/processed/team_elo_history.parquet (one row per team-match, pre- and post-match Elo)
         outputs/tables/team_elo_validation.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
RAW = BASE / "data" / "processed" / "raw"
PROCESSED = BASE / "data" / "processed"
TABLES = BASE / "outputs" / "tables"

INITIAL_ELO = 1500.0
K = 20.0
HOME_ADVANTAGE = 60.0  # Elo points added to the home team's rating when computing expectation only


def _result_score(row_score: float, opp_score: float) -> float:
    if row_score > opp_score:
        return 1.0
    if row_score < opp_score:
        return 0.0
    return 0.5


def build_elo(competition_id: str, home_advantage: float | None = HOME_ADVANTAGE) -> pd.DataFrame:
    matches = pd.read_parquet(RAW / "matches.parquet")
    match_teams = pd.read_parquet(RAW / "match_teams.parquet")

    m = matches[(matches.competition_id == competition_id) & (matches.status == "Played")].copy()
    m["dt"] = pd.to_datetime(m.match_datetime_utc, utc=True, errors="coerce")
    m = m.dropna(subset=["dt"])

    mt = match_teams[match_teams.match_id.isin(m.match_id)].copy()
    mt["score_num"] = pd.to_numeric(mt.score, errors="coerce")

    # keep only matches with exactly 2 team rows and both scores present (clean result)
    teams_per_match = mt.groupby("match_id").size()
    clean_matches = teams_per_match[teams_per_match == 2].index
    mt = mt[mt.match_id.isin(clean_matches)]
    mt = mt.dropna(subset=["score_num"])
    clean_matches = mt.groupby("match_id").size()
    clean_matches = clean_matches[clean_matches == 2].index
    mt = mt[mt.match_id.isin(clean_matches)]

    m = m[m.match_id.isin(mt.match_id)].sort_values(["dt", "match_id"])

    ratings: dict[str, float] = {}
    rows = []

    for _, match in m.iterrows():
        mid = match.match_id
        sides = mt[mt.match_id == mid]
        home = sides[sides.side == "home"]
        away = sides[sides.side == "away"]
        if len(home) != 1 or len(away) != 1:
            continue  # defensive skip; should not happen after the cleaning above
        home_team = home.iloc[0].team_id
        away_team = away.iloc[0].team_id
        if home_team == away_team:
            continue  # defensive skip against a team-vs-itself data error
        home_score = home.iloc[0].score_num
        away_score = away.iloc[0].score_num

        pre_home = ratings.get(home_team, INITIAL_ELO)
        pre_away = ratings.get(away_team, INITIAL_ELO)

        ha = home_advantage or 0.0
        expected_home = 1.0 / (1.0 + 10 ** (((pre_away) - (pre_home + ha)) / 400.0))
        expected_away = 1.0 - expected_home

        actual_home = _result_score(home_score, away_score)
        actual_away = 1.0 - actual_home

        post_home = pre_home + K * (actual_home - expected_home)
        post_away = pre_away + K * (actual_away - expected_away)

        rows.append({
            "match_id": mid, "match_datetime_utc": match["dt"], "season_id": match.season_id,
            "home_team_id": home_team, "away_team_id": away_team,
            "home_score": home_score, "away_score": away_score,
            "pre_match_home_elo": pre_home, "pre_match_away_elo": pre_away,
            "post_match_home_elo": post_home, "post_match_away_elo": post_away,
            "expected_home_score": expected_home, "actual_home_score": actual_home,
        })

        ratings[home_team] = post_home
        ratings[away_team] = post_away

    return pd.DataFrame(rows)


def main(competition_id: str = "346"):
    elo_with_ha = build_elo(competition_id, home_advantage=HOME_ADVANTAGE)
    elo_no_ha = build_elo(competition_id, home_advantage=0.0)

    PROCESSED.mkdir(parents=True, exist_ok=True)
    elo_with_ha.to_parquet(PROCESSED / "team_elo_history.parquet")

    # simple calibration check for each variant: within Elo-difference bins, does the
    # home team's actual win rate track the expected score?
    def calibration(df):
        d = df.copy()
        d["elo_diff"] = d.pre_match_home_elo - d.pre_match_away_elo
        bins = [-np.inf, -200, -100, -50, 0, 50, 100, 200, np.inf]
        d["bin"] = pd.cut(d.elo_diff, bins)
        return d.groupby("bin", observed=True).agg(
            n=("actual_home_score", "size"),
            mean_expected=("expected_home_score", "mean"),
            mean_actual=("actual_home_score", "mean"),
        )

    cal_ha = calibration(elo_with_ha)
    cal_no_ha = calibration(elo_no_ha)

    TABLES.mkdir(parents=True, exist_ok=True)
    summary_rows = []
    summary_rows.append({"check": "matches processed (with home advantage)", "value": len(elo_with_ha)})
    summary_rows.append({"check": "matches processed (no home advantage)", "value": len(elo_no_ha)})
    summary_rows.append({"check": "unique teams", "value": len(set(elo_with_ha.home_team_id) | set(elo_with_ha.away_team_id))})
    summary_rows.append({"check": "K factor", "value": K})
    summary_rows.append({"check": "home advantage (Elo points)", "value": HOME_ADVANTAGE})
    summary_rows.append({"check": "initial Elo", "value": INITIAL_ELO})

    final_ratings = {}
    for _, r in elo_with_ha.iterrows():
        final_ratings[r.home_team_id] = r.post_match_home_elo
        final_ratings[r.away_team_id] = r.post_match_away_elo
    ratings_series = pd.Series(final_ratings)
    summary_rows.append({"check": "final rating min", "value": round(ratings_series.min(), 1)})
    summary_rows.append({"check": "final rating max", "value": round(ratings_series.max(), 1)})
    summary_rows.append({"check": "final rating mean", "value": round(ratings_series.mean(), 1)})
    summary_rows.append({"check": "final rating std", "value": round(ratings_series.std(), 1)})

    pd.DataFrame(summary_rows).to_csv(TABLES / "team_elo_validation.csv", index=False)
    cal_ha.to_csv(TABLES / "team_elo_calibration_with_home_advantage.csv")
    cal_no_ha.to_csv(TABLES / "team_elo_calibration_no_home_advantage.csv")

    print("Elo history rows:", len(elo_with_ha))
    print(ratings_series.describe())
    print("\nCalibration (with home advantage):")
    print(cal_ha)


if __name__ == "__main__":
    main()
