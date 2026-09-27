"""
Stage 2 quality-control visuals for the team Elo built in build_team_elo.py. These are QC/sanity
plots, not paper figures -- purpose is to visually confirm the Elo system behaves sensibly before
it is trusted as an opponent-strength input in later stages.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"
FIGS = BASE / "outputs" / "figures"
RAW = BASE / "data" / "processed" / "raw"

plt.rcParams.update({"figure.dpi": 150, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


def main():
    elo = pd.read_parquet(PROCESSED / "team_elo_history.parquet")
    teams = pd.read_parquet(RAW / "match_teams.parquet")

    # try to attach readable team names if a teams table is available; otherwise use raw IDs
    try:
        teams_lookup = pd.read_parquet(RAW / "teams.parquet")[["team_id", "name"]]
        name_map = dict(zip(teams_lookup.team_id, teams_lookup.name))
    except FileNotFoundError:
        name_map = {}

    # --- Figure 1: distribution of final team ratings ---
    final_ratings = {}
    for _, r in elo.iterrows():
        final_ratings[r.home_team_id] = r.post_match_home_elo
        final_ratings[r.away_team_id] = r.post_match_away_elo
    ratings = pd.Series(final_ratings)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(ratings.values, bins=15, color="#2563eb", edgecolor="white")
    ax.axvline(1500, color="#888888", linestyle="--", linewidth=1, label="initial Elo (1500)")
    ax.set_xlabel("Final team Elo")
    ax.set_ylabel("Number of teams")
    ax.set_title("Team Elo distribution (Championship, 3 seasons)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGS / "team_elo_distribution.png")
    plt.close(fig)

    # --- Figure 2: selected team trajectories over time ---
    # build a long-form per-team-match Elo series (post-match value at each of the team's matches)
    long_rows = []
    for _, r in elo.iterrows():
        long_rows.append({"team_id": r.home_team_id, "dt": r.match_datetime_utc, "elo": r.post_match_home_elo})
        long_rows.append({"team_id": r.away_team_id, "dt": r.match_datetime_utc, "elo": r.post_match_away_elo})
    long_df = pd.DataFrame(long_rows).sort_values(["team_id", "dt"])

    # pick the 3 highest and 3 lowest final-rating teams for a readable trajectory plot
    top3 = ratings.sort_values(ascending=False).head(3).index.tolist()
    bot3 = ratings.sort_values(ascending=True).head(3).index.tolist()
    selected = top3 + bot3

    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors = plt.cm.tab10.colors
    for i, tid in enumerate(selected):
        sub = long_df[long_df.team_id == tid]
        label = name_map.get(tid, f"team {tid}")
        style = "-" if tid in top3 else "--"
        ax.plot(sub.dt, sub.elo, style, color=colors[i % 10], linewidth=1.4, label=label)
    ax.axhline(1500, color="#cccccc", linewidth=1, zorder=0)
    ax.set_xlabel("Match date")
    ax.set_ylabel("Post-match team Elo")
    ax.set_title("Selected team Elo trajectories (top 3 solid, bottom 3 dashed)")
    ax.legend(fontsize=7, loc="best")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(FIGS / "team_elo_selected_trajectories.png")
    plt.close(fig)

    # --- Figure 3: pre-match Elo difference vs actual result (calibration) ---
    d = elo.copy()
    d["elo_diff"] = d.pre_match_home_elo - d.pre_match_away_elo
    bins = list(range(-300, 301, 50))
    d["bin_mid"] = pd.cut(d.elo_diff, bins).apply(lambda x: x.mid if pd.notna(x) else None)
    cal = d.groupby("bin_mid", observed=True).agg(
        n=("actual_home_score", "size"),
        mean_expected=("expected_home_score", "mean"),
        mean_actual=("actual_home_score", "mean"),
    ).reset_index()

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.plot(cal.bin_mid, cal.mean_expected, "o-", color="#2563eb", label="Elo-expected home score")
    ax.plot(cal.bin_mid, cal.mean_actual, "s--", color="#c0392b", label="Actual mean home score")
    for _, row in cal.iterrows():
        ax.annotate(f"n={int(row.n)}", (row.bin_mid, row.mean_actual), fontsize=7,
                    textcoords="offset points", xytext=(0, -12), ha="center", color="#555555")
    ax.set_xlabel("Pre-match home Elo − away Elo")
    ax.set_ylabel("Home-team result score (1=win, 0.5=draw, 0=loss)")
    ax.set_title("Elo-difference calibration (with home advantage)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGS / "elo_difference_vs_result.png")
    plt.close(fig)

    print("Wrote 3 QC figures to", FIGS)


if __name__ == "__main__":
    main()
