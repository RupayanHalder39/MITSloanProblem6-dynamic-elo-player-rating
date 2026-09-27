"""
Stage 4, Task 14: dynamic-rating QC figures. QC visuals, not paper figures.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"
FIGS = BASE / "outputs" / "figures"

POS_COLORS = {"GK": "#a86f1f", "DEF": "#2563eb", "MID": "#1f6f43", "ATT": "#c0392b"}
VARIANT_COLORS = {"A": "#888888", "B": "#2563eb", "C": "#c0392b"}

plt.rcParams.update({"figure.dpi": 150, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


def main():
    df = pd.read_parquet(PROCESSED / "player_dynamic_ratings_candidates.parquet")
    final = df.sort_values("match_datetime_utc").groupby(["rating_variant", "player_id"]).tail(1)

    # --- Figure 1: final rating distribution, by variant ---
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=True)
    for ax, variant in zip(axes, ["A", "B", "C"]):
        sub = final[final.rating_variant == variant]
        ax.hist(sub.post_match_player_rating, bins=30, color=VARIANT_COLORS[variant], edgecolor="white")
        ax.axvline(1500, color="#333", linestyle="--", linewidth=1)
        ax.set_title(f"Variant {variant}")
        ax.set_xlabel("Final player rating")
    axes[0].set_ylabel("Number of players")
    fig.suptitle("Final rating distribution by variant")
    fig.tight_layout()
    fig.savefig(FIGS / "dynamic_rating_distribution.png")
    plt.close(fig)

    # --- Figure 2: by position (Variant B) ---
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    b = final[final.rating_variant == "B"]
    groups = ["GK", "DEF", "MID", "ATT"]
    data = [b[b.position_group == g].post_match_player_rating.dropna() for g in groups]
    bp = ax.boxplot(data, tick_labels=groups, patch_artist=True, showfliers=False)
    for patch, g in zip(bp["boxes"], groups):
        patch.set_facecolor(POS_COLORS[g])
        patch.set_alpha(0.25)
        patch.set_edgecolor(POS_COLORS[g])
    ax.axhline(1500, color="#888888", linestyle="--", linewidth=1)
    ax.set_ylabel("Final player rating (Variant B)")
    ax.set_title("Final rating by position group")
    fig.tight_layout()
    fig.savefig(FIGS / "dynamic_rating_by_position.png")
    plt.close(fig)

    # --- Figure 3: update-magnitude distribution ---
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for variant in ["A", "B", "C"]:
        sub = df[df.rating_variant == variant]
        ax.hist(sub.rating_change, bins=60, range=(-150, 150), histtype="step",
                 color=VARIANT_COLORS[variant], linewidth=1.5, label=f"Variant {variant}")
    ax.axvline(0, color="#333", linewidth=0.8)
    ax.set_xlabel("rating_change (single-match update)")
    ax.set_ylabel("Count")
    ax.set_title("Rating-update magnitude distribution")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGS / "dynamic_rating_update_distribution.png")
    plt.close(fig)

    # --- Figure 4: selected trajectories (Variant B; top 3 / bottom 3 by final rating among players
    # with >=20 matches, so trajectories are readable full-season arcs) ---
    counts = df[df.rating_variant == "B"].groupby("player_id").size()
    eligible_players = counts[counts >= 20].index
    finalB = final[(final.rating_variant == "B") & (final.player_id.isin(eligible_players))]
    top3 = finalB.nlargest(3, "post_match_player_rating").player_id.tolist()
    bot3 = finalB.nsmallest(3, "post_match_player_rating").player_id.tolist()

    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors = plt.cm.tab10.colors
    for i, pid in enumerate(top3 + bot3):
        traj = df[(df.rating_variant == "B") & (df.player_id == pid)].sort_values("match_datetime_utc")
        style = "-" if pid in top3 else "--"
        ax.plot(traj.match_datetime_utc, traj.post_match_player_rating, style,
                 color=colors[i % 10], linewidth=1.3, label=f"player {pid}")
    ax.axhline(1500, color="#cccccc", linewidth=1)
    ax.set_xlabel("Match date")
    ax.set_ylabel("Post-match player rating (Variant B)")
    ax.set_title("Selected player rating trajectories (top 3 solid, bottom 3 dashed, ≥20 matches)")
    ax.legend(fontsize=7)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(FIGS / "dynamic_rating_selected_trajectories.png")
    plt.close(fig)

    # --- Figure 5: performance surprise distribution, by position (Variant B) ---
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    b = df[df.rating_variant == "B"]
    data = [b[b.position_group == g].performance_surprise.dropna() for g in groups]
    bp = ax.boxplot(data, tick_labels=groups, patch_artist=True, showfliers=False)
    for patch, g in zip(bp["boxes"], groups):
        patch.set_facecolor(POS_COLORS[g])
        patch.set_alpha(0.25)
        patch.set_edgecolor(POS_COLORS[g])
    ax.axhline(0, color="#888888", linestyle="--", linewidth=1)
    ax.set_ylabel("performance_surprise (Variant B)")
    ax.set_title("Performance surprise distribution by position")
    fig.tight_layout()
    fig.savefig(FIGS / "performance_surprise_distribution.png")
    plt.close(fig)

    # --- Figure 6: opponent adjustment effect (A vs B expected performance, same rating) ---
    merged = df[df.rating_variant.isin(["A", "B"])].pivot_table(
        index=["match_id", "player_id"], columns="rating_variant", values="expected_performance"
    ).dropna()
    elo_diff = df[df.rating_variant == "B"].set_index(["match_id", "player_id"])["pre_match_team_elo"] - \
        df[df.rating_variant == "B"].set_index(["match_id", "player_id"])["pre_match_opponent_elo"]
    merged["elo_diff"] = elo_diff.reindex(merged.index)
    merged["opponent_shift"] = merged["B"] - merged["A"]
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    sample = merged.sample(min(3000, len(merged)), random_state=42)
    ax.scatter(sample.elo_diff, sample.opponent_shift, s=4, alpha=0.25, color="#2563eb")
    ax.axhline(0, color="#888", linewidth=0.8)
    ax.axvline(0, color="#888", linewidth=0.8)
    ax.set_xlabel("Pre-match team Elo − opponent Elo")
    ax.set_ylabel("Expectation shift from opponent adjustment (B − A)")
    ax.set_title("Opponent-adjustment effect on expected performance")
    fig.tight_layout()
    fig.savefig(FIGS / "opponent_adjustment_effect.png")
    plt.close(fig)

    # --- Figure 7: rating stability by experience (Variant C vs B update magnitude by matches_seen) ---
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for variant, color in [("B", VARIANT_COLORS["B"]), ("C", VARIANT_COLORS["C"])]:
        sub = df[df.rating_variant == variant].copy()
        sub["abs_change"] = sub.rating_change.abs()
        bins = [0, 5, 10, 15, 20, 30, 100]
        sub["bucket"] = pd.cut(sub.matches_seen_before, bins)
        g = sub.groupby("bucket", observed=True).abs_change.mean()
        ax.plot(range(len(g)), g.values, "o-", color=color, label=f"Variant {variant}")
    ax.set_xticks(range(len(bins) - 1))
    ax.set_xticklabels([f"{bins[i]}-{bins[i+1]}" for i in range(len(bins) - 1)], rotation=30)
    ax.set_xlabel("matches_seen_before (bucketed)")
    ax.set_ylabel("Mean |rating_change|")
    ax.set_title("Rating stability by experience (Variant C should flatten faster)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGS / "rating_stability_by_experience.png")
    plt.close(fig)

    print("Wrote 7 QC figures to", FIGS)


if __name__ == "__main__":
    main()
