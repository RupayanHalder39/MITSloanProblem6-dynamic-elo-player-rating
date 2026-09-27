"""
Stage 4, Task 13: objective player-trajectory case studies. No cherry-picking by name -- every
case selected by an explicit, reproducible criterion, primarily on Variant B (the main research
candidate per the brief's framing) unless the criterion specifically concerns opponent adjustment
(A vs B) or history-awareness (B vs C).
"""
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"
REPORTS = BASE / "outputs" / "reports"


def describe(df, pid, variant):
    sub = df[(df.player_id == pid) & (df.rating_variant == variant)].sort_values("match_datetime_utc")
    first, last = sub.iloc[0], sub.iloc[-1]
    return {
        "player_id": pid, "variant": variant, "position_group": last.position_group,
        "n_matches": len(sub),
        "first_date": str(first.match_datetime_utc)[:10],
        "last_date": str(last.match_datetime_utc)[:10],
        "initial_rating": round(first.pre_match_player_rating, 1),
        "final_rating": round(last.post_match_player_rating, 1),
        "net_change": round(last.post_match_player_rating - first.pre_match_player_rating, 1),
    }


def main():
    df = pd.read_parquet(PROCESSED / "player_dynamic_ratings_candidates.parquet")
    b = df[df.rating_variant == "B"]
    counts = b.groupby("player_id").size()
    sufficiently_observed = counts[counts >= 15].index  # objective "enough history" threshold

    per_player = b.sort_values("match_datetime_utc").groupby("player_id").agg(
        first_rating=("pre_match_player_rating", "first"),
        last_rating=("post_match_player_rating", "last"),
        n=("match_id", "size"),
        std_rating=("post_match_player_rating", "std"),
    )
    per_player["net_change"] = per_player.last_rating - per_player.first_rating

    cases = {}
    cases["largest_rating_riser"] = per_player.net_change.idxmax()
    cases["largest_rating_faller"] = per_player.net_change.idxmin()

    stable = per_player[per_player.n >= 20].sort_values("std_rating").index
    cases["most_stable_high_appearance_player"] = stable[0] if len(stable) else None

    cases["highest_final_rating"] = per_player.last_rating.idxmax()
    sufficient = per_player[per_player.n >= 15]
    cases["lowest_final_rating_sufficiently_observed"] = sufficient.last_rating.idxmin()

    idx_max_pos = b.rating_change.idxmax()
    idx_max_neg = b.rating_change.idxmin()
    cases["biggest_one_match_positive_update"] = ("__match__", b.loc[idx_max_pos])
    cases["biggest_one_match_negative_update"] = ("__match__", b.loc[idx_max_neg])

    # strongest opponent-adjustment effect: largest |expected_B - expected_A| for the same appearance
    a = df[df.rating_variant == "A"].set_index(["match_id", "player_id"])["expected_performance"]
    b_idx = b.set_index(["match_id", "player_id"], drop=False)
    diff = (b_idx["expected_performance"] - a.reindex(b_idx.index)).abs()
    strongest_opp_key = diff.idxmax()
    cases["strongest_opponent_adjustment_effect"] = ("__row__", b_idx.loc[strongest_opp_key])

    for pos in ["GK", "DEF", "MID", "ATT"]:
        pos_players = per_player.loc[per_player.index.isin(b[b.position_group == pos].player_id.unique())]
        pos_players = pos_players[pos_players.n >= 15]
        if len(pos_players):
            cases[f"{pos.lower()}_example"] = pos_players.net_change.abs().idxmax()

    lines = ["# Dynamic Rating Case Studies\n\n",
             "Selected by objective, reproducible criteria applied to "
             "`data/processed/player_dynamic_ratings_candidates.parquet` -- no names chosen manually. "
             "Trajectory cases use Variant B (main research candidate); opponent-adjustment and "
             "single-match-update cases reference the specific rows that trigger the criterion.\n\n"]

    for name, val in cases.items():
        lines.append(f"## {name.replace('_', ' ').title()}\n\n")
        if val is None:
            lines.append("No qualifying player found for this criterion.\n\n")
            continue
        if isinstance(val, tuple):
            row = val[1]
            lines.append(f"- Player ID: `{row.player_id}`, Position: {row.position_group}\n")
            lines.append(f"- Match ID: `{row.match_id}`, Date: {str(row.match_datetime_utc)[:10]}\n")
            lines.append(f"- pre_match_player_rating: {row.pre_match_player_rating:.1f}\n")
            lines.append(f"- expected_performance: {row.expected_performance:.1f}\n")
            lines.append(f"- actual_performance_score: {row.actual_performance_score:.1f}\n")
            lines.append(f"- performance_surprise: {row.performance_surprise:.1f}\n")
            lines.append(f"- rating_change: {row.rating_change:.1f}\n")
            lines.append(f"- confidence_tier: {row.confidence_tier}\n\n")
        else:
            pid = val
            d = describe(df, pid, "B")
            lines.append(f"- Player ID: `{pid}`, Position: {d['position_group']}\n")
            lines.append(f"- Matches: {d['n_matches']} ({d['first_date']} → {d['last_date']})\n")
            lines.append(f"- Rating: {d['initial_rating']} → {d['final_rating']} "
                          f"(net change {d['net_change']:+.1f})\n\n")

    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "DynamicRatingCaseStudies.md").write_text("".join(lines))
    print(f"Wrote {REPORTS / 'DynamicRatingCaseStudies.md'}")
    for name, val in cases.items():
        print(name, "->", val if not isinstance(val, tuple) else val[1].player_id)


if __name__ == "__main__":
    main()
