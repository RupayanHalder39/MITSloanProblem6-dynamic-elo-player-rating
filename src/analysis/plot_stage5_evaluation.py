"""
Stage 5, Task 19: experimental/QC figures for the predictive evaluation. Not final paper figures.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"
TABLES = BASE / "outputs" / "tables"
FIGS = BASE / "outputs" / "figures"

METHOD_COLS = {
    "last1": "baseline_last1_calibrated", "last3": "baseline_last3_calibrated",
    "last5": "baseline_last5_calibrated", "season_to_date": "baseline_season_to_date_calibrated",
    "career_to_date": "baseline_career_to_date_calibrated",
    "position_prior": "baseline_position_prior_calibrated",
    "variant_A": "variant_A_rating_calibrated", "variant_B": "variant_B_rating_calibrated",
    "variant_C": "variant_C_rating_calibrated",
}
METHOD_COLORS = {
    "last1": "#cccccc", "last3": "#aaaaaa", "last5": "#888888",
    "season_to_date": "#c0a060", "career_to_date": "#a86f1f", "position_prior": "#dddddd",
    "variant_A": "#1f6f43", "variant_B": "#2563eb", "variant_C": "#c0392b",
}

plt.rcParams.update({"figure.dpi": 150, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


def main():
    df = pd.read_parquet(PROCESSED / "player_rating_predictive_evaluation.parquet")
    primary = pd.read_csv(TABLES / "stage5_primary_method_comparison.csv").set_index("method")
    test = df[(df.split == "test") & df.future_3_match_performance.notna()].copy()
    for col in METHOD_COLS.values():
        test = test[test[col].notna()]

    order = primary.sort_values("MAE").index.tolist()

    # --- Figure 1: MAE comparison ---
    fig, ax = plt.subplots(figsize=(7, 4.5))
    colors = [METHOD_COLORS[m] for m in order]
    ax.bar(order, primary.loc[order, "MAE"], color=colors)
    ax.set_ylabel("MAE (future-3 match performance, test)")
    ax.set_title("Method comparison: MAE (lower is better)")
    ax.tick_params(axis="x", rotation=40)
    fig.tight_layout()
    fig.savefig(FIGS / "stage5_method_mae_comparison.png")
    plt.close(fig)

    # --- Figure 2: Spearman comparison ---
    fig, ax = plt.subplots(figsize=(7, 4.5))
    order_sp = primary.sort_values("Spearman", ascending=False).index.tolist()
    colors_sp = [METHOD_COLORS[m] for m in order_sp]
    ax.bar(order_sp, primary.loc[order_sp, "Spearman"], color=colors_sp)
    ax.set_ylabel("Spearman correlation (future-3, test)")
    ax.set_title("Method comparison: ranking quality (higher is better)")
    ax.tick_params(axis="x", rotation=40)
    fig.tight_layout()
    fig.savefig(FIGS / "stage5_method_spearman_comparison.png")
    plt.close(fig)

    # --- Figure 3: Variant C predicted vs actual ---
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    sample = test.sample(min(3000, len(test)), random_state=42)
    ax.scatter(sample[METHOD_COLS["variant_C"]], sample.future_3_match_performance,
               s=5, alpha=0.2, color=METHOD_COLORS["variant_C"])
    lims = [20, 100]
    ax.plot(lims, lims, "--", color="#333", linewidth=1)
    ax.set_xlim(lims); ax.set_ylim(lims)
    ax.set_xlabel("Variant C calibrated prediction")
    ax.set_ylabel("Actual future-3 match performance")
    ax.set_title(f"Variant C: predicted vs. actual (test, n={len(sample)} sampled)")
    fig.tight_layout()
    fig.savefig(FIGS / "stage5_variant_c_predicted_vs_actual.png")
    plt.close(fig)

    # --- Figure 4: performance by position ---
    pos_comp = pd.read_csv(TABLES / "stage5_position_comparison.csv")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    positions = ["GK", "DEF", "MID", "ATT"]
    methods = ["variant_C", "last5", "season_to_date"]
    x = np.arange(len(positions))
    width = 0.25
    for i, m in enumerate(methods):
        vals = [pos_comp[(pos_comp.position_group == p) & (pos_comp.method == m)].MAE.values[0] for p in positions]
        ax.bar(x + i * width, vals, width, label=m, color=[METHOD_COLORS.get(m, "#888")] * len(positions), alpha=0.7 + i * 0.1)
    ax.set_xticks(x + width)
    ax.set_xticklabels(positions)
    ax.set_ylabel("MAE (future-3, test)")
    ax.set_title("Predictive performance by position group")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGS / "stage5_performance_by_position.png")
    plt.close(fig)

    # --- Figure 5: performance by experience ---
    exp_comp = pd.read_csv(TABLES / "stage5_experience_comparison.csv")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    buckets = ["0-4", "5-14", "15-29", "30+"]
    x = np.arange(len(buckets))
    for i, m in enumerate(methods):
        vals = [exp_comp[(exp_comp.experience_bucket == b) & (exp_comp.method == m)].MAE.values[0] for b in buckets]
        ax.plot(x, vals, "o-", label=m, color=METHOD_COLORS.get(m, "#888"))
    ax.set_xticks(x)
    ax.set_xticklabels(buckets)
    ax.set_xlabel("matches_seen_before bucket")
    ax.set_ylabel("MAE (future-3, test)")
    ax.set_title("Predictive performance by experience level")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGS / "stage5_performance_by_experience.png")
    plt.close(fig)

    # --- Figure 6: dynamic vs last5, direct scatter of errors ---
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    err_dynamic = (test[METHOD_COLS["variant_C"]] - test.future_3_match_performance).abs()
    err_last5 = (test[METHOD_COLS["last5"]] - test.future_3_match_performance).abs()
    sample_idx = test.sample(min(3000, len(test)), random_state=42).index
    ax.scatter(err_last5.loc[sample_idx], err_dynamic.loc[sample_idx], s=5, alpha=0.2, color="#2563eb")
    lims = [0, max(err_dynamic.max(), err_last5.max())]
    ax.plot(lims, lims, "--", color="#333", linewidth=1)
    ax.set_xlabel("|error|, last-5 baseline")
    ax.set_ylabel("|error|, Variant C")
    ax.set_title("Dynamic rating vs. last-5 baseline: per-row absolute error")
    fig.tight_layout()
    fig.savefig(FIGS / "stage5_dynamic_vs_last5.png")
    plt.close(fig)

    # --- Figure 7: opponent-adjustment ablation ---
    opp = pd.read_csv(TABLES / "stage5_opponent_adjustment_ablation.csv")
    fig, ax = plt.subplots(1, 2, figsize=(9, 4))
    ax[0].bar(opp.variant, opp.MAE, color=["#1f6f43", "#2563eb"])
    ax[0].set_ylabel("MAE")
    ax[0].set_title("MAE")
    ax[0].tick_params(axis="x", rotation=15)
    ax[1].bar(opp.variant, opp.Spearman, color=["#1f6f43", "#2563eb"])
    ax[1].set_ylabel("Spearman")
    ax[1].set_title("Spearman")
    ax[1].tick_params(axis="x", rotation=15)
    fig.suptitle("Opponent-adjustment ablation (Variant A vs. B, test, same cohort)")
    fig.tight_layout()
    fig.savefig(FIGS / "stage5_opponent_adjustment_ablation.png")
    plt.close(fig)

    print("Wrote 7 Stage-5 figures to", FIGS)


if __name__ == "__main__":
    main()
