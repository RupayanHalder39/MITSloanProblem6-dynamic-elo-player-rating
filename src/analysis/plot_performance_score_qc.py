"""
Stage 3, Task 10: performance-score quality-control figures. QC visuals, not paper figures.
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

LALIGA_C = "#2563eb"
SEGUNDA_C = "#c0392b"
NEUTRAL = "#333333"
POS_COLORS = {"GK": "#a86f1f", "DEF": "#2563eb", "MID": "#1f6f43", "ATT": "#c0392b"}

plt.rcParams.update({"figure.dpi": 150, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


def main():
    df = pd.read_parquet(PROCESSED / "player_match_performance.parquet")
    scored = df[df.score_eligible & df.final_stage3_score_candidate.notna()].copy()

    # --- Figure 1: overall score distribution ---
    fig, ax = plt.subplots(figsize=(6.5, 4))
    ax.hist(scored.final_stage3_score_candidate, bins=40, color=LALIGA_C, edgecolor="white")
    ax.axvline(50, color="#888888", linestyle="--", linewidth=1, label="50 = average match")
    ax.set_xlabel("final_stage3_score_candidate")
    ax.set_ylabel("Number of player-match observations")
    ax.set_title("Performance score distribution (all positions)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGS / "performance_score_distribution.png")
    plt.close(fig)

    # --- Figure 2: by position ---
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    groups = ["GK", "DEF", "MID", "ATT"]
    data = [scored[scored.position_group == g].final_stage3_score_candidate.dropna() for g in groups]
    bp = ax.boxplot(data, tick_labels=groups, patch_artist=True, showfliers=False)
    for patch, g in zip(bp["boxes"], groups):
        patch.set_facecolor(POS_COLORS[g])
        patch.set_alpha(0.25)
        patch.set_edgecolor(POS_COLORS[g])
    for i, g in enumerate(groups):
        d = data[i]
        jitter = np.random.default_rng(42).uniform(-0.15, 0.15, size=min(len(d), 300))
        sample = d.sample(min(len(d), 300), random_state=42)
        ax.scatter(np.full(len(sample), i + 1) + jitter, sample, s=4, alpha=0.3, color=POS_COLORS[g])
    ax.axhline(50, color="#888888", linestyle="--", linewidth=1)
    ax.set_ylabel("final_stage3_score_candidate")
    ax.set_title("Performance score by position group")
    fig.tight_layout()
    fig.savefig(FIGS / "performance_score_by_position.png")
    plt.close(fig)

    # --- Figure 3: by minutes confidence / bucket ---
    order = ["LOW", "MEDIUM", "HIGH"]
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    data = [scored[scored.minutes_confidence == m].final_stage3_score_candidate.dropna() for m in order]
    bp = ax.boxplot(data, tick_labels=order, patch_artist=True, showfliers=False)
    for patch in bp["boxes"]:
        patch.set_facecolor(SEGUNDA_C)
        patch.set_alpha(0.25)
        patch.set_edgecolor(SEGUNDA_C)
    ax.axhline(50, color="#888888", linestyle="--", linewidth=1)
    ax.set_xlabel("Minutes confidence tier (LOW=1-19min shrunk, MEDIUM=20-59min, HIGH=60+min)")
    ax.set_ylabel("final_stage3_score_candidate")
    ax.set_title("Performance score by minutes-confidence tier")
    fig.tight_layout()
    fig.savefig(FIGS / "performance_score_by_minutes.png")
    plt.close(fig)

    # --- Figure 4: feature dominance (correlation of each raw shrunk-rate feature with the score) ---
    import sys
    sys.path.insert(0, str(BASE / "src" / "features"))
    from build_player_match_performance import POSITIVE_FEATURES, NEGATIVE_FEATURES  # noqa: E402
    all_feats = sorted(set(sum(POSITIVE_FEATURES.values(), []) + sum(NEGATIVE_FEATURES.values(), [])))
    detail_path = PROCESSED / "player_match_performance_scoreable_detail.parquet"
    detail = pd.read_parquet(detail_path)
    corrs = {}
    for feat in all_feats:
        col = f"{feat}_z_expanding"
        if col in detail.columns:
            corrs[feat] = detail[col].corr(detail.candidate_score_B)
    corr_s = pd.Series(corrs).dropna().sort_values()
    fig, ax = plt.subplots(figsize=(7, 9))
    colors = [SEGUNDA_C if v < 0 else LALIGA_C for v in corr_s.values]
    ax.barh(corr_s.index, corr_s.values, color=colors)
    ax.axvline(0, color=NEUTRAL, linewidth=0.8)
    ax.set_xlabel("Correlation with candidate_score_B")
    ax.set_title("Feature dominance check: correlation of each raw feature with the final score")
    fig.tight_layout()
    fig.savefig(FIGS / "performance_score_feature_dominance.png")
    plt.close(fig)
    corr_s.to_csv(BASE / "outputs" / "tables" / "performance_score_feature_correlations.csv",
                  header=["correlation_with_score_B"])

    # --- Figure 5: season stability ---
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    seasons = sorted(scored.season_id.dropna().unique())
    data = [scored[scored.season_id == s].final_stage3_score_candidate.dropna() for s in seasons]
    bp = ax.boxplot(data, tick_labels=[str(s) for s in seasons], patch_artist=True, showfliers=False)
    for patch in bp["boxes"]:
        patch.set_facecolor(NEUTRAL)
        patch.set_alpha(0.2)
        patch.set_edgecolor(NEUTRAL)
    ax.axhline(50, color="#888888", linestyle="--", linewidth=1)
    ax.set_xlabel("season_id")
    ax.set_ylabel("final_stage3_score_candidate")
    ax.set_title("Performance score stability across seasons")
    fig.tight_layout()
    fig.savefig(FIGS / "performance_score_season_stability.png")
    plt.close(fig)

    print("Wrote 5 QC figures to", FIGS)
    print("\nScore summary by season:")
    print(scored.groupby("season_id").final_stage3_score_candidate.describe()[["count", "mean", "std"]])


if __name__ == "__main__":
    main()
