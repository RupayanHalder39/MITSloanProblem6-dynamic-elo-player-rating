"""
Stage 3, Task 11/10(15): objective case-study selection + outlier table. No cherry-picking by
name -- every case is selected by an explicit, reproducible criterion applied to the data.
"""
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"
RAW = BASE / "data" / "processed" / "raw"
REPORTS = BASE / "outputs" / "reports"
TABLES = BASE / "outputs" / "tables"


def context_row(df, idx, stats):
    r = df.loc[idx]
    s = stats[(stats.player_id == r.player_id) & (stats.match_id == r.match_id)]
    key_stats = {}
    if len(s):
        s = s.iloc[0]
        for c in ["goals", "assists", "shots_on_target", "key_passes", "successful_passes",
                  "passes", "new_duels_won", "interceptions", "recoveries", "gk_saves",
                  "gk_conceded_goals", "clearances"]:
            v = pd.to_numeric(s[c], errors="coerce")
            if pd.notna(v) and v != 0:
                key_stats[c] = v
    return {
        "player_id": r.player_id, "team_id": r.team_id, "opponent_team_id": r.opponent_team_id,
        "match_id": r.match_id, "date": str(r.match_datetime_utc)[:10],
        "position_group": r.position_group, "minutes": r.minutes_for_scoring,
        "is_starting": r.is_starting, "minutes_confidence": r.minutes_confidence,
        "match_result": r.match_result, "key_stats": key_stats,
        "candidate_score_B": round(r.candidate_score_B, 3) if pd.notna(r.candidate_score_B) else None,
        "final_stage3_score_candidate": round(r.final_stage3_score_candidate, 1) if pd.notna(r.final_stage3_score_candidate) else None,
    }


def main():
    df = pd.read_parquet(PROCESSED / "player_match_performance.parquet")
    stats = pd.read_parquet(RAW / "player_match_stats_total_championship.parquet")
    scored = df[df.score_eligible & df.final_stage3_score_candidate.notna()].copy()

    cases = {}
    cases["highest_score_overall"] = scored.final_stage3_score_candidate.idxmax()
    cases["lowest_score_overall"] = scored.final_stage3_score_candidate.idxmin()

    att = scored[scored.position_group == "ATT"]
    cases["highest_attacking_score"] = att.final_stage3_score_candidate.idxmax() if len(att) else None

    defn = scored[scored.position_group == "DEF"]
    cases["highest_defensive_score"] = defn.final_stage3_score_candidate.idxmax() if len(defn) else None

    gk = scored[scored.position_group == "GK"]
    cases["highest_goalkeeper_score"] = gk.final_stage3_score_candidate.idxmax() if len(gk) else None

    sub_cameo = scored[(scored.minutes_confidence == "LOW") & (scored.is_starting.astype(str) == "f")]
    cases["strong_substitute_cameo"] = sub_cameo.final_stage3_score_candidate.idxmax() if len(sub_cameo) else None

    # high-minute (90+) but low-event: joined to raw stats for event totals
    # `scored` already carries the raw feature columns (incl. passes, recoveries) from the
    # Stage-3 build script's own merge -- no need to re-merge with `stats` here.
    high_min = scored[scored.minutes_confidence == "HIGH"].copy()
    high_min["event_total"] = pd.to_numeric(high_min.successful_passes, errors="coerce").fillna(0) + \
        pd.to_numeric(high_min.recoveries, errors="coerce").fillna(0) + \
        pd.to_numeric(high_min.new_duels_won, errors="coerce").fillna(0)
    low_event = high_min[high_min.minutes_for_scoring >= 90].sort_values("event_total").head(1)
    cases["high_minute_low_event"] = low_event.index[0] if len(low_event) else None

    # unusual outlier: largest |z-score| gap between candidate_score_A and candidate_score_B
    scored["score_disagreement"] = (scored.candidate_score_A - scored.candidate_score_B).abs()
    cases["unusual_outlier_score_disagreement"] = scored.score_disagreement.idxmax()

    results = {}
    for name, idx in cases.items():
        if idx is None:
            results[name] = None
            continue
        row_idx = idx if not isinstance(idx, pd.Index) else idx[0]
        results[name] = context_row(scored, row_idx, stats)

    # --- outlier table (Task 10 item 15): top 20 + bottom 20 by score ---
    top20 = scored.nlargest(20, "final_stage3_score_candidate")
    bot20 = scored.nsmallest(20, "final_stage3_score_candidate")
    outliers = pd.concat([top20, bot20])[
        ["player_id", "match_id", "position_group", "minutes_for_scoring", "minutes_confidence",
         "is_starting", "candidate_score_A", "candidate_score_B", "candidate_score_C",
         "final_stage3_score_candidate"]
    ].sort_values("final_stage3_score_candidate", ascending=False)
    outliers.to_csv(TABLES / "performance_score_outliers.csv", index=False)

    # --- write markdown report ---
    lines = ["# Performance Score Case Studies\n\n",
             "Selected by objective, reproducible criteria applied to "
             "`data/processed/player_match_performance.parquet` -- no names chosen manually.\n\n"]
    for name, r in results.items():
        lines.append(f"## {name.replace('_', ' ').title()}\n\n")
        if r is None:
            lines.append("No qualifying row found for this criterion.\n\n")
            continue
        lines.append(f"- Player ID: `{r['player_id']}`, Team ID: `{r['team_id']}`, "
                      f"Opponent Team ID: `{r['opponent_team_id']}`\n")
        lines.append(f"- Match ID: `{r['match_id']}`, Date: {r['date']}, Result: {r['match_result']}\n")
        lines.append(f"- Position group: {r['position_group']}, Minutes: {r['minutes']:.0f} "
                      f"({r['minutes_confidence']} confidence), Starting: {r['is_starting']}\n")
        lines.append(f"- Key raw stats (non-zero): {r['key_stats']}\n")
        lines.append(f"- candidate_score_B (robust z, pre-scale): {r['candidate_score_B']}\n")
        lines.append(f"- **final_stage3_score_candidate: {r['final_stage3_score_candidate']}**\n\n")

    lines.append("## Outlier table (top 20 + bottom 20 by final score)\n\n")
    lines.append("Full table: `outputs/tables/performance_score_outliers.csv`\n\n")

    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "PerformanceScoreCaseStudies.md").write_text("".join(lines))
    print(f"Wrote {REPORTS / 'PerformanceScoreCaseStudies.md'}")
    for name, r in results.items():
        print(name, "->", r["final_stage3_score_candidate"] if r else None)


if __name__ == "__main__":
    main()
