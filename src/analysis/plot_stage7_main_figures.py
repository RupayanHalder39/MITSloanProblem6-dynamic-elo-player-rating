"""
Stage 7, Parts E/F: the 10 main publication-quality result figures, plus supporting figures.
Every figure traces to a Stage 5/6 table (no new numbers computed here) and uses the shared
stage7_style visual identity.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import stage7_style as S

BASE = Path(__file__).resolve().parents[2]
TABLES = BASE / "outputs" / "tables"
FIGS = BASE / "outputs" / "figures"

METHOD_LABELS = {
    "variant_A": "Dynamic rating (A)", "variant_B": "+ opponent adj. (B)",
    "variant_C": "+ opponent + history (C)", "last1": "Last match",
    "last3": "Last 3 avg", "last5": "Last 5 avg", "season_to_date": "Season-to-date",
    "career_to_date": "Career-to-date", "position_prior": "Position average only",
}


def save(fig, name, caption=None):
    if caption:
        S.add_caption(fig, caption, y=-0.03)
    fig.tight_layout(rect=(0, 0.02, 1, 1) if caption else None)
    fig.savefig(FIGS / name, bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------------------
# F1: Main method comparison
# ---------------------------------------------------------------------------
def f1_method_comparison():
    df = pd.read_csv(TABLES / "stage5_primary_method_comparison.csv").set_index("method")
    order = df.sort_values("MAE", ascending=False).index.tolist()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))
    for ax, metric, better in [(axes[0], "MAE", "lower"), (axes[1], "Spearman", "higher")]:
        colors = [S.METHOD_COLORS.get(m, S.GRAY) for m in order]
        y = np.arange(len(order))
        ax.hlines(y, 0, df.loc[order, metric], color=colors, linewidth=3, alpha=0.85)
        ax.scatter(df.loc[order, metric], y, color=colors, s=90, zorder=3, edgecolor="white", linewidth=1.2)
        ax.set_yticks(y)
        ax.set_yticklabels([METHOD_LABELS.get(m, m) for m in order])
        ax.set_xlabel(f"{metric} ({'lower is better' if better=='lower' else 'higher is better'})")
        best_idx = df[metric].idxmin() if better == "lower" else df[metric].idxmax()
        best_y = order.index(best_idx)
        ax.annotate("BEST", (df.loc[best_idx, metric], best_y), xytext=(12, 0),
                    textcoords="offset points", va="center", fontsize=10, fontweight="bold",
                    color=S.GREEN)
    axes[0].set_title("Prediction error (MAE)")
    axes[1].set_title("Ranking quality (Spearman)")
    fig.suptitle("The dynamic rating beats every recent-form baseline",
                 fontsize=16, fontweight="bold", color=S.NAVY, y=1.03)
    save(fig, "stage7_f1_method_comparison.png",
         "Test season (2025/26), n=11,353 player-match observations, 734 players. "
         "“Dynamic rating (A)” = the simplest of 3 tested rating designs; it wins on both metrics.")


# ---------------------------------------------------------------------------
# F2: Future-horizon robustness
# ---------------------------------------------------------------------------
def f2_future_horizon():
    df = pd.read_csv(TABLES / "exp_future_horizons.csv")
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for m in ["variant_A", "last5", "season_to_date", "career_to_date"]:
        sub = df[df.method == m].sort_values("horizon")
        ax.plot(sub.horizon, sub.MAE, "o-", label=METHOD_LABELS.get(m, m),
                color=S.METHOD_COLORS.get(m, S.GRAY), linewidth=2.8, markersize=9)
    ax.set_xlabel("How many matches ahead are we predicting?")
    ax.set_ylabel("Prediction error (MAE, lower is better)")
    ax.set_xticks([1, 2, 3, 5, 7])
    ax.legend(loc="upper right")
    ax.set_title("The rating's advantage holds from 1 to 7 matches ahead", color=S.NAVY)
    save(fig, "stage7_f2_future_horizon_robustness.png",
         "Test season. The dynamic rating (green) has the lowest error at every future window "
         "tested — this is not a coincidence of picking exactly 3 matches ahead.")


# ---------------------------------------------------------------------------
# F3: History depth
# ---------------------------------------------------------------------------
def f3_history_depth():
    df = pd.read_csv(TABLES / "exp_history_depth.csv")
    buckets = ["0-4", "5-9", "10-14", "15-29", "30+"]
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    width = 0.25
    x = np.arange(len(buckets))
    for i, m in enumerate(["variant_A", "last5", "season_to_date"]):
        vals = [df[(df.history_bucket == b) & (df.method == m)].MAE.values[0] for b in buckets]
        ax.bar(x + i * width, vals, width, label=METHOD_LABELS.get(m, m),
               color=S.METHOD_COLORS.get(m, S.GRAY))
    ax.set_xticks(x + width)
    ax.set_xticklabels([f"{b} matches" for b in buckets])
    ax.set_ylabel("Prediction error (MAE, lower is better)")
    ax.set_xlabel("How many matches of history has the player already played?")
    ax.legend()
    ax.axvspan(x[3] - 0.5 + width, x[-1] + 1.5 + width, color=S.GREEN, alpha=0.06)
    ax.text(x[3] + width, ax.get_ylim()[1] * 0.98, "Rating pulls ahead here",
            fontsize=10, color=S.GREEN, fontweight="bold", ha="left", va="top")
    ax.set_title("The rating needs about 15 matches of history to earn its edge", color=S.NAVY)
    save(fig, "stage7_f3_history_depth.png",
         "Test season, bucketed by matches already observed for that player. Below ~15 matches, "
         "a simple last-5 average is just as good or better; above 15, the dynamic rating wins clearly.")


# ---------------------------------------------------------------------------
# F4: Position performance
# ---------------------------------------------------------------------------
def f4_position():
    df = pd.read_csv(TABLES / "exp_position.csv")
    positions = ["GK", "DEF", "MID", "ATT"]
    pos_colors = {"GK": S.GOLD, "DEF": S.BLUE, "MID": S.GREEN, "ATT": S.RED}
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    vals = [df[(df.position_group == p) & (df.method == "variant_A")].R2.values[0] for p in positions]
    colors = [pos_colors[p] for p in positions]
    bars = ax.bar(positions, vals, color=colors, width=0.55)
    ax.axhline(0, color="#333333", linewidth=1)
    for b, v in zip(bars, vals):
        ax.annotate(f"{v:+.2f}", (b.get_x() + b.get_width() / 2, v),
                    xytext=(0, 8 if v >= 0 else -16), textcoords="offset points",
                    ha="center", fontsize=11, fontweight="bold")
    ax.set_ylabel("Predictive skill (R²) — 0 = no skill, negative = worse than guessing the average")
    ax.set_title("The rating works for outfield players — not yet for goalkeepers", color=S.NAVY)
    save(fig, "stage7_f4_position_performance.png",
         "Test season, Variant A. MID and DEF show the clearest predictive skill; GK is negative "
         "(worse than always guessing the average) — diagnosed in the next figure.")


# ---------------------------------------------------------------------------
# F5: Goalkeeper diagnosis
# ---------------------------------------------------------------------------
def f5_gk_diagnosis():
    stab = pd.read_csv(TABLES / "exp_target_stability.csv")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))
    positions = stab.position_group.tolist()
    colors = {"GK": S.GOLD, "DEF": S.BLUE, "MID": S.GREEN, "ATT": S.RED}

    ratio = stab.score_variance_between_player / (stab.score_variance_between_player + stab.score_variance_within_player_mean)
    bar_colors = [colors[p] for p in positions]
    axes[0].bar(positions, ratio, color=bar_colors)
    axes[0].set_ylabel("Share of score variance that is\nbetween different players (not just noise)")
    axes[0].set_title("How much does the score tell players apart?")
    for i, (p, r) in enumerate(zip(positions, ratio)):
        axes[0].annotate(f"{r:.0%}", (i, r), xytext=(0, 6), textcoords="offset points",
                          ha="center", fontsize=10.5, fontweight="bold")

    gk = pd.read_csv(TABLES / "exp_gk_diagnosis.csv").iloc[0]
    methods = ["last1", "last3", "last5", "career_to_date", "variant_A"]
    vals = [gk[f"{m}_Spearman"] for m in methods]
    axes[1].bar([METHOD_LABELS.get(m, m) for m in methods], vals, color=S.GOLD, alpha=0.85)
    axes[1].axhline(0, color="#333333", linewidth=1)
    axes[1].set_ylabel("Spearman correlation with future GK performance")
    axes[1].set_title("Every method fails for goalkeepers\n(even a single-match guess)")
    axes[1].tick_params(axis="x", rotation=20)

    fig.suptitle("Goalkeeper diagnosis: the problem is the target, not the rating design",
                 fontsize=15, fontweight="bold", color=S.NAVY, y=1.04)
    save(fig, "stage7_f5_goalkeeper_diagnosis.png",
         "Left: goalkeepers (gold) have the lowest share of score variance that distinguishes one "
         "player from another (10%, vs. 26-31% for outfield positions). Right: even the simplest "
         "possible method (last match) shows almost no GK skill — the rating design is not the "
         "cause.")


# ---------------------------------------------------------------------------
# F6: Opponent adjustment hurts
# ---------------------------------------------------------------------------
def f6_opponent_adjustment():
    df = pd.read_csv(TABLES / "exp_opponent_scale.csv")
    val = df[df.eval_split == "validation"]
    fig, ax1 = plt.subplots(figsize=(9, 5.5))
    ax1.plot(val.opponent_scale, val.MAE, "o-", color=S.RED, linewidth=3, markersize=10)
    ax1.set_xlabel("How strongly do we adjust for the opponent's strength?\n(0 = no adjustment, the production default)")
    ax1.set_ylabel("Prediction error (MAE, lower is better)", color=S.RED)
    ax1.tick_params(axis="y", labelcolor=S.RED)
    ax1.annotate("No adjustment\nworks best", (0.0, val.MAE.iloc[0]), xytext=(20, -35),
                 textcoords="offset points", fontsize=10.5, fontweight="bold", color=S.GREEN,
                 arrowprops=dict(arrowstyle="->", color=S.GREEN))
    ax1.set_title("More opponent adjustment makes prediction worse, not better", color=S.NAVY)
    save(fig, "stage7_f6_opponent_adjustment_hurts.png",
         "Validation season only (never the final test season) — tested at 6 predefined "
         "adjustment strengths. Error rises steadily as the adjustment gets stronger.")


# ---------------------------------------------------------------------------
# F7: Score A vs Score B
# ---------------------------------------------------------------------------
def f7_score_ablation():
    df = pd.read_csv(TABLES / "exp_score_ablation.csv")
    labels = ["Score A\n(equal-weight)", "Score B\n(category-balanced,\nproduction)"]
    fig, axes = plt.subplots(1, 2, figsize=(9, 5.2))
    colors = [S.GRAY, S.GREEN]
    axes[0].bar(labels, df.MAE, color=colors)
    axes[0].set_ylabel("Prediction error (MAE)")
    axes[0].set_title("Error")
    axes[1].bar(labels, df.Spearman, color=colors)
    axes[1].set_ylabel("Ranking quality (Spearman)")
    axes[1].set_title("Ranking quality")
    fig.suptitle("Balancing football categories beats simple equal-weighting",
                 fontsize=15, fontweight="bold", color=S.NAVY, y=1.03)
    save(fig, "stage7_f7_scoreA_vs_scoreB.png",
         "Test season, n=11,353, both run through the identical rating engine — the only "
         "difference is how the underlying match-performance score combines feature categories.")


# ---------------------------------------------------------------------------
# F8: Ranking robustness
# ---------------------------------------------------------------------------
def f8_ranking():
    dec = pd.read_csv(TABLES / "stage5_ranking_deciles.csv")
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    x = dec.rating_decile + 1
    colors = plt.cm.RdYlGn(np.linspace(0.15, 0.9, len(dec)))
    ax.bar(x, dec["mean"], color=colors)
    ax.set_xlabel("Rating decile (1 = lowest-rated 10% of appearances, 10 = highest-rated 10%)")
    ax.set_ylabel("Actual average performance over the next 3 matches")
    ax.set_xticks(x)
    ax.set_title("Higher-rated players go on to perform better — consistently", color=S.NAVY)
    save(fig, "stage7_f8_ranking_robustness.png",
         "Test season, n=11,353. Players are split into 10 equal-sized groups by their rating; "
         "each group's actual future performance rises in step, decile by decile.")


# ---------------------------------------------------------------------------
# F9: Rating + recent form combination
# ---------------------------------------------------------------------------
def f9_combination():
    df = pd.read_csv(TABLES / "exp_combination.csv")
    order = ["last5_only", "variant_A_only", "variant_A_plus_last5"]
    labels = ["Last-5 average\nonly", "Dynamic rating\nonly", "Rating + last-5\ncombined"]
    colors = [S.GRAY, S.GREEN, S.BLUE]
    fig, ax = plt.subplots(figsize=(8, 5.5))
    vals = [df[df.combination == o].MAE.values[0] for o in order]
    ax.bar(labels, vals, color=colors)
    ax.set_ylabel("Prediction error (MAE, lower is better)")
    ax.set_title("Combining the rating with recent form helps a little further", color=S.NAVY)
    save(fig, "stage7_f9_rating_plus_recent_form.png",
         "Test season, simple linear combination (no black-box model). The combined signal is "
         "slightly better than either alone — a small, real, complementary effect.")


# ---------------------------------------------------------------------------
# F10: Bootstrap effects forest plot
# ---------------------------------------------------------------------------
def f10_bootstrap_forest():
    df = pd.read_csv(TABLES / "exp_bootstrap_effects.csv")
    labels = {
        "variant_A vs last5": "vs. Last-5 average", "variant_A vs season_to_date": "vs. Season-to-date",
        "variant_A vs career_to_date": "vs. Career-to-date", "variant_A vs variant_B": "vs. Opponent-adjusted (B)",
        "variant_A vs variant_C": "vs. History-aware (C)",
    }
    df["label"] = df.comparison.map(labels)
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    y = np.arange(len(df))
    ax.errorbar(df.mae_diff_mean, y,
                xerr=[df.mae_diff_mean - df.mae_diff_ci_lo, df.mae_diff_ci_hi - df.mae_diff_mean],
                fmt="o", color=S.BLUE, capsize=5, markersize=9, linewidth=2.2)
    ax.axvline(0, color="#333333", linewidth=1.3)
    ax.set_yticks(y)
    ax.set_yticklabels(df.label)
    ax.set_xlabel("Error difference (dynamic rating − comparison method)\nnegative = rating is better, with 95% confidence interval")
    ax.set_title("The dynamic rating's advantage is statistically robust in every comparison", color=S.NAVY)
    save(fig, "stage7_f10_bootstrap_effects.png",
         "Player-clustered bootstrap (2,000 resamples), test season. Every interval sits entirely "
         "left of zero — the rating's advantage is not explained by chance in any of the 5 "
         "headline comparisons.")


if __name__ == "__main__":
    f1_method_comparison()
    f2_future_horizon()
    f3_history_depth()
    f4_position()
    f5_gk_diagnosis()
    f6_opponent_adjustment()
    f7_score_ablation()
    f8_ranking()
    f9_combination()
    f10_bootstrap_forest()
