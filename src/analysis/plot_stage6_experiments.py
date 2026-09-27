"""
Stage 6: experiment/report figures (not final paper figures). Covers the highest-priority subset
of the requested 25 -- prioritized for information density given the scope of this stage; every
figure traces directly to a saved outputs/tables/exp_*.csv, so nothing here is illustrative-only.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
TABLES = BASE / "outputs" / "tables"
FIGS = BASE / "outputs" / "figures"

C = {"variant_A": "#1f6f43", "variant_B": "#2563eb", "variant_C": "#c0392b",
     "last1": "#dddddd", "last3": "#bbbbbb", "last5": "#888888",
     "season_to_date": "#c0a060", "career_to_date": "#a86f1f", "position_prior": "#eeeeee"}

plt.rcParams.update({"figure.dpi": 150, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


def savefig(fig, name):
    fig.tight_layout()
    fig.savefig(FIGS / name)
    plt.close(fig)
    print("wrote", name)


def fig3_future_horizons():
    df = pd.read_csv(TABLES / "exp_future_horizons.csv")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for m in ["variant_A", "variant_B", "variant_C", "last5", "career_to_date"]:
        sub = df[df.method == m].sort_values("horizon")
        ax.plot(sub.horizon, sub.MAE, "o-", label=m, color=C.get(m, "#888"))
    ax.set_xlabel("Future horizon (matches ahead)")
    ax.set_ylabel("MAE (test)")
    ax.set_title("Does the advantage survive across future horizons?")
    ax.legend(fontsize=8)
    savefig(fig, "exp_fig_future_horizons.png")


def fig4_temporal_folds():
    df = pd.read_csv(TABLES / "exp_temporal_folds.csv")
    folds = df.fold.unique()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(folds))
    methods = ["last5", "season_to_date", "variant_A", "variant_C"]
    width = 0.2
    for i, m in enumerate(methods):
        vals = [df[(df.fold == f) & (df.method == m)].MAE.values[0] if len(df[(df.fold == f) & (df.method == m)]) else np.nan for f in folds]
        ax.bar(x + i * width, vals, width, label=m, color=C.get(m, "#888"))
    ax.set_xticks(x + 1.5 * width)
    ax.set_xticklabels([f.replace(" -> ", "\n→ ") for f in folds], fontsize=7)
    ax.set_ylabel("MAE")
    ax.set_title("Rolling-origin temporal folds (train/validation only)")
    ax.legend(fontsize=8)
    savefig(fig, "exp_fig_temporal_folds.png")


def fig5_history_depth():
    df = pd.read_csv(TABLES / "exp_history_depth.csv")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    buckets = ["0-4", "5-9", "10-14", "15-29", "30+"]
    for m in ["variant_A", "last5", "season_to_date"]:
        vals = [df[(df.history_bucket == b) & (df.method == m)].MAE.values[0] for b in buckets]
        ax.plot(buckets, vals, "o-", label=m, color=C.get(m, "#888"))
    ax.set_xlabel("Matches of history seen before this match")
    ax.set_ylabel("MAE (test)")
    ax.set_title("How much history before the dynamic rating becomes useful?")
    ax.legend(fontsize=8)
    savefig(fig, "exp_fig_history_depth.png")


def fig6_position():
    df = pd.read_csv(TABLES / "exp_position.csv")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    positions = ["GK", "DEF", "MID", "ATT"]
    x = np.arange(len(positions))
    methods = ["variant_A", "last5", "season_to_date", "career_to_date"]
    width = 0.2
    for i, m in enumerate(methods):
        vals = [df[(df.position_group == p) & (df.method == m)].R2.values[0] for p in positions]
        ax.bar(x + i * width, vals, width, label=m)
    ax.axhline(0, color="#333", linewidth=0.8)
    ax.set_xticks(x + 1.5 * width)
    ax.set_xticklabels(positions)
    ax.set_ylabel("R² (test) -- negative = worse than predicting the mean")
    ax.set_title("Predictive skill (R²) by position")
    ax.legend(fontsize=8)
    savefig(fig, "exp_fig_position_r2.png")


def fig7_8_gk_att_diagnosis():
    stab = pd.read_csv(TABLES / "exp_target_stability.csv")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    positions = stab.position_group.tolist()
    axes[0].bar(positions, stab.score_variance_between_player, color="#2563eb", alpha=0.7, label="between-player")
    axes[0].bar(positions, stab.score_variance_within_player_mean, color="#c0392b", alpha=0.4, label="within-player (noise)", bottom=0)
    axes[0].set_ylabel("Variance")
    axes[0].set_title("Score variance: between- vs within-player")
    axes[0].legend(fontsize=8)
    axes[1].bar(positions, stab.lag1_autocorrelation_mean, color="#1f6f43")
    axes[1].axhline(0, color="#333", linewidth=0.8)
    axes[1].set_ylabel("Lag-1 autocorrelation")
    axes[1].set_title("Match-to-match score stability")
    fig.suptitle("GK/ATT diagnosis: is the target itself predictable?")
    savefig(fig, "exp_fig_gk_att_diagnosis.png")


def fig9_opponent_scale():
    df = pd.read_csv(TABLES / "exp_opponent_scale.csv")
    val = df[df.eval_split == "validation"]
    fig, ax1 = plt.subplots(figsize=(6.5, 4.5))
    ax1.plot(val.opponent_scale, val.MAE, "o-", color="#c0392b")
    ax1.set_xlabel("OPPONENT_SCALE")
    ax1.set_ylabel("MAE (validation)", color="#c0392b")
    ax2 = ax1.twinx()
    ax2.plot(val.opponent_scale, val.Spearman, "s--", color="#2563eb")
    ax2.set_ylabel("Spearman (validation)", color="#2563eb")
    ax1.set_title("Opponent-scale sensitivity (fit/evaluated on validation only)")
    savefig(fig, "exp_fig_opponent_scale.png")


def fig10_history_decay():
    df = pd.read_csv(TABLES / "exp_history_decay.csv")
    val = df[df.eval_split == "validation"].copy()
    val["label"] = val.apply(lambda r: f"floor={r.history_floor},M0={r.history_m0}", axis=1)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(val.label, val.MAE, color="#c0392b")
    ax.set_ylabel("MAE (validation)")
    ax.set_title("History-decay sensitivity (validation only)")
    ax.tick_params(axis="x", rotation=30)
    savefig(fig, "exp_fig_history_decay.png")


def fig11_k_sensitivity():
    df = pd.read_csv(TABLES / "exp_k_sensitivity.csv")
    val = df[df.eval_split == "validation"]
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.plot(val.K, val.MAE, "o-", color="#2563eb")
    ax.set_xlabel("K (update strength)")
    ax.set_ylabel("MAE (validation)")
    ax.set_title("K sensitivity: small K = trust history more, large K = react to 1 match more")
    savefig(fig, "exp_fig_k_sensitivity.png")


def fig12_minutes_weight():
    df = pd.read_csv(TABLES / "exp_minutes_weight.csv")
    val = df[df.eval_split == "validation"]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh(val.weighting, val.MAE, color="#1f6f43")
    ax.set_xlabel("MAE (validation)")
    ax.set_title("Minutes update-weight ablation (validation only)")
    savefig(fig, "exp_fig_minutes_weight.png")


def fig13_score_ablation():
    df = pd.read_csv(TABLES / "exp_score_ablation.csv")
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    axes[0].bar(df.score_variant.str.split("(").str[0], df.MAE, color=["#888", "#1f6f43"])
    axes[0].set_ylabel("MAE (test)")
    axes[0].tick_params(axis="x", rotation=20)
    axes[1].bar(df.score_variant.str.split("(").str[0], df.Spearman, color=["#888", "#1f6f43"])
    axes[1].set_ylabel("Spearman (test)")
    axes[1].tick_params(axis="x", rotation=20)
    fig.suptitle("Score A (equal-weight) vs Score B (category-balanced)")
    savefig(fig, "exp_fig_score_ablation.png")


def fig14_category_ablation():
    df = pd.read_csv(TABLES / "exp_category_ablation.csv")
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    colors = ["#c0392b" if v < 0 else "#2563eb" for v in df.spearman_with_future3]
    ax.barh(df.category, df.spearman_with_future3, color=colors)
    ax.axvline(0, color="#333", linewidth=0.8)
    ax.set_xlabel("Spearman correlation with future-3 performance")
    ax.set_title("Which performance categories carry forward-looking signal?")
    savefig(fig, "exp_fig_category_ablation.png")


def fig15_combination():
    df = pd.read_csv(TABLES / "exp_combination.csv")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(df.combination, df.MAE, color="#2563eb")
    ax.set_ylabel("MAE (test)")
    ax.set_title("Does combining dynamic rating + recent form help?")
    ax.tick_params(axis="x", rotation=25)
    savefig(fig, "exp_fig_combination.png")


def fig16_momentum():
    df = pd.read_csv(TABLES / "exp_momentum.csv")
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.bar(df.group, df.mean_future3, color=["#1f6f43", "#888", "#c0392b"])
    ax.set_ylabel("Mean future-3 performance")
    ax.set_title("Does rating momentum predict future performance?")
    ax.tick_params(axis="x", rotation=15)
    savefig(fig, "exp_fig_momentum.png")


def fig18_team_context():
    df = pd.read_csv(TABLES / "exp_team_context.csv")
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.bar(df.team_elo_tercile, df.MAE, color="#a86f1f")
    ax.set_ylabel("MAE (test)")
    ax.set_title("Does the rating work equally well across team strength?")
    savefig(fig, "exp_fig_team_context.png")


def fig19_starter_sub():
    df = pd.read_csv(TABLES / "exp_starter_sub.csv")
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    groups = df.group.unique()
    x = np.arange(len(groups))
    width = 0.35
    for i, m in enumerate(["variant_A", "last5"]):
        vals = [df[(df.group == g) & (df.method == m)].MAE.values[0] for g in groups]
        ax.bar(x + i * width, vals, width, label=m, color=C.get(m, "#888"))
    ax.set_xticks(x + width / 2)
    ax.set_xticklabels(groups)
    ax.set_ylabel("MAE (test)")
    ax.set_title("Starters vs. substitutes")
    ax.legend(fontsize=8)
    savefig(fig, "exp_fig_starter_sub.png")


def fig21_bootstrap_forest():
    df = pd.read_csv(TABLES / "exp_bootstrap_effects.csv")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    y = np.arange(len(df))
    ax.errorbar(df.mae_diff_mean, y, xerr=[df.mae_diff_mean - df.mae_diff_ci_lo, df.mae_diff_ci_hi - df.mae_diff_mean],
                fmt="o", color="#2563eb", capsize=4)
    ax.axvline(0, color="#333", linewidth=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(df.comparison)
    ax.set_xlabel("MAE difference (negative = first method better), 95% bootstrap CI")
    ax.set_title("Bootstrap effect sizes: Variant A vs. everything")
    savefig(fig, "exp_fig_bootstrap_forest.png")


if __name__ == "__main__":
    fig3_future_horizons()
    fig4_temporal_folds()
    fig5_history_depth()
    fig6_position()
    fig7_8_gk_att_diagnosis()
    fig9_opponent_scale()
    fig10_history_decay()
    fig11_k_sensitivity()
    fig12_minutes_weight()
    fig13_score_ablation()
    fig14_category_ablation()
    fig15_combination()
    fig16_momentum()
    fig18_team_context()
    fig19_starter_sub()
    fig21_bootstrap_forest()
    print("Done.")
