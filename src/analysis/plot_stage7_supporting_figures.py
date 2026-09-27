"""
Stage 7, Part F: supporting/appendix figures, restyled with the shared publication-quality
identity. Covers the Tier-2/3 claims from docs/VisualClaimSelection.md.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import stage7_style as S
from plot_stage7_main_figures import save, METHOD_LABELS  # noqa: E402

BASE = Path(__file__).resolve().parents[2]
TABLES = BASE / "outputs" / "tables"
FIGS = BASE / "outputs" / "figures"


def supp1_temporal_folds():
    df = pd.read_csv(TABLES / "exp_temporal_folds.csv")
    folds = df.fold.unique()
    fig, ax = plt.subplots(figsize=(10, 5.5))
    methods = ["last5", "season_to_date", "variant_A", "variant_C"]
    x = np.arange(len(folds))
    width = 0.2
    for i, m in enumerate(methods):
        vals = [df[(df.fold == f) & (df.method == m)].MAE.values[0] for f in folds]
        ax.bar(x + i * width, vals, width, label=METHOD_LABELS.get(m, m), color=S.METHOD_COLORS.get(m, S.GRAY))
    ax.set_xticks(x + 1.5 * width)
    ax.set_xticklabels(["Early season 1\n>> later season 1", "Season 1\n>> early season 2",
                        "Season 1 + early season 2\n>> later season 2"], fontsize=9.5)
    ax.set_ylabel("Prediction error (MAE)")
    ax.legend(fontsize=9)
    ax.set_title("The result mostly holds across time — except very early on", color=S.NAVY)
    save(fig, "stage7_supp_temporal_folds.png",
         "Rolling-origin folds within train+validation only (test season never used here). The "
         "rating only loses in the very first fold, where the least history has accumulated.")


def supp2_starter_sub():
    df = pd.read_csv(TABLES / "exp_starter_sub.csv")
    groups = ["regular_starter", "substitute"]
    labels = ["Regular starters", "Substitutes"]
    fig, ax = plt.subplots(figsize=(8, 5.5))
    x = np.arange(len(groups))
    width = 0.32
    for i, m in enumerate(["variant_A", "last5"]):
        vals = [df[(df.group == g) & (df.method == m)].MAE.values[0] for g in groups]
        ax.bar(x + i * width, vals, width, label=METHOD_LABELS.get(m, m), color=S.METHOD_COLORS.get(m, S.GRAY))
    ax.set_xticks(x + width / 2)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Prediction error (MAE)")
    ax.legend()
    ax.set_title("The rating's edge is bigger for regular starters", color=S.NAVY)
    save(fig, "stage7_supp_starter_sub.png",
         "Test season. Substitutes have lower absolute error (less variance to predict, a side "
         "effect of Stage 3's minutes-based shrinkage), but the rating's advantage over last-5 is "
         "concentrated in players with stable, high minutes.")


def supp3_momentum():
    df = pd.read_csv(TABLES / "exp_momentum.csv")
    labels = ["Falling fastest\n(bottom 10%)", "Middle 80%", "Rising fastest\n(top 10%)"]
    order = ["bottom10pct_momentum (declining)", "middle80pct_momentum", "top10pct_momentum (rising)"]
    colors = [S.RED, S.GRAY, S.GREEN]
    fig, ax = plt.subplots(figsize=(8, 5.5))
    vals = [df[df.group == o].mean_future3.values[0] for o in order]
    ax.bar(labels, vals, color=colors)
    ax.set_ylabel("Actual average performance, next 3 matches")
    ax.set_title("A rising or falling rating says something real (exploratory)", color=S.NAVY)
    save(fig, "stage7_supp_momentum.png",
         "Test season, predefined quantiles of 5-match rating change. Players whose rating rose "
         "fastest went on to outperform those whose rating fell fastest by ~5 points. Exploratory "
         "result, smaller evidence base than the main figures.")


def supp4_team_context():
    df = pd.read_csv(TABLES / "exp_team_context.csv")
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.bar(["Weaker teams", "Mid-strength teams", "Stronger teams"], df.MAE, color=S.GOLD, alpha=0.85)
    ax.set_ylabel("Prediction error (MAE)")
    ax.set_title("No clean pattern by team strength (honesty check)", color=S.NAVY)
    save(fig, "stage7_supp_team_context.png",
         "Test season, split into 3 equal groups by the player's own team's pre-match Elo rating. "
         "Error is not monotonic with team strength — shown plainly rather than a forced story.")


def supp5_history_decay_flat():
    df = pd.read_csv(TABLES / "exp_history_decay.csv")
    val = df[df.eval_split == "validation"].copy()
    val["label"] = val.apply(lambda r: f"floor={r.history_floor}\nM0={r.history_m0}", axis=1)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.bar(val.label, val.MAE, color=S.RED, alpha=0.8)
    ax.set_ylim(4.0, 4.25)
    ax.set_ylabel("Prediction error (MAE, validation)")
    ax.set_title("Making the rating update faster for new players doesn't help either", color=S.NAVY)
    save(fig, "stage7_supp_history_decay_flat.png",
         "Validation season only, 5 predefined settings including “no decay at all.” Error "
         "is essentially flat — a genuine null result, tested carefully, not just unlucky once.")


if __name__ == "__main__":
    supp1_temporal_folds()
    supp2_starter_sub()
    supp3_momentum()
    supp4_team_context()
    supp5_history_decay_flat()
