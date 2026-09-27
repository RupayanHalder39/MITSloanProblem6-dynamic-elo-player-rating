"""
Stage 7, Part D: core explanatory diagrams (D1-D4). Schematic, not data plots -- built with the
shared stage7_style visual identity for consistency with the data figures in
plot_stage7_main_figures.py.
"""
from pathlib import Path

import matplotlib.pyplot as plt

import stage7_style as S

BASE = Path(__file__).resolve().parents[2]
FIGS = BASE / "outputs" / "figures"


def d1_system_overview():
    fig, ax = plt.subplots(figsize=(11, 3.6))
    ax.set_xlim(0, 12.5)
    ax.set_ylim(0, 4)
    ax.axis("off")
    ax.text(6.25, 3.7, "From a match to a future-performance prediction", ha="center",
            fontsize=15, fontweight="bold", color=S.NAVY)

    stages = [
        ("Match stats", "passes, tackles,\nshots, saves...", S.GRAY),
        ("Match performance\nscore", "0–100,\nposition-aware\n(Stage 3)", S.GOLD),
        ("Dynamic player\nrating", "updates after\nevery match\n(Stage 4)", S.BLUE),
        ("Future-performance\nprediction", "next 1–7\nmatches\n(Stage 5–6)", S.GREEN),
    ]
    w, h, gap = 2.5, 1.9, 0.55
    x = 0.3
    centers = []
    for label, sub, color in stages:
        cx, cy = S.box(ax, (x, 1.0), w, h, label, sub, facecolor=color, fontsize=12)
        centers.append((x, cy, w))
        x += w + gap
    for i in range(len(centers) - 1):
        x0 = centers[i][0] + centers[i][2]
        x1 = centers[i + 1][0]
        S.arrow(ax, (x0 + 0.05, centers[i][1]), (x1 - 0.05, centers[i + 1][1]), color=S.NAVY)

    fig.tight_layout()
    fig.savefig(FIGS / "stage7_d1_system_overview.png")
    plt.close(fig)
    print("wrote stage7_d1_system_overview.png")


def d2_prediction_timing():
    fig, ax = plt.subplots(figsize=(11, 3.8))
    ax.set_xlim(0, 12.5)
    ax.set_ylim(0, 4.3)
    ax.axis("off")
    ax.text(6.25, 4.05, "Leakage-safe prediction timing", ha="center",
            fontsize=15, fontweight="bold", color=S.NAVY)

    # timeline
    ax.annotate("", xy=(12.0, 2.1), xytext=(0.3, 2.1),
                arrowprops=dict(arrowstyle="-|>", color="#999999", linewidth=1.5))
    ax.text(0.3, 2.35, "time  >", fontsize=10, color="#777777", style="italic")

    past_matches_x = [1.2, 2.1, 3.0, 3.9]
    for px in past_matches_x:
        ax.plot(px, 2.1, "o", color=S.GRAY, markersize=10, zorder=3)
    ax.text((past_matches_x[0] + past_matches_x[-1]) / 2, 1.55,
            "Past matches\n(used to build the rating)", ha="center", fontsize=10, color=S.CHARCOAL)

    t_x = 5.0
    ax.plot(t_x, 2.1, "o", color=S.GOLD, markersize=16, zorder=4)
    ax.text(t_x, 2.75, "Match T\n(post-match rating\nrecorded here)", ha="center", fontsize=10.5,
            color=S.GOLD, fontweight="bold")

    future_x = [6.6, 7.6, 8.6]
    for i, fx in enumerate(future_x):
        ax.plot(fx, 2.1, "o", color=S.GREEN, markersize=10, zorder=3)
        ax.text(fx, 1.55, f"T+{i+1}", ha="center", fontsize=9.5, color=S.GREEN)
    ax.text((future_x[0] + future_x[-1]) / 2, 3.15,
            "Future target window\n(what we predict — NEVER used as an input)",
            ha="center", fontsize=10.5, color=S.GREEN, fontweight="bold")

    ax.annotate("", xy=(future_x[0] - 0.35, 2.1), xytext=(t_x + 0.35, 2.1),
                arrowprops=dict(arrowstyle="-|>", color=S.NAVY, linewidth=2.2))
    ax.text((t_x + future_x[0]) / 2, 2.35, "predict", ha="center", fontsize=10,
            color=S.NAVY, style="italic")

    fig.tight_layout()
    fig.savefig(FIGS / "stage7_d2_prediction_timing.png")
    plt.close(fig)
    print("wrote stage7_d2_prediction_timing.png")


def d3_variant_comparison():
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.set_xlim(0, 12.5)
    ax.set_ylim(0, 4.6)
    ax.axis("off")
    ax.text(6.25, 4.35, "Three rating designs — the simplest one won", ha="center",
            fontsize=15, fontweight="bold", color=S.NAVY)

    variants = [
        ("Variant A", "Dynamic rating only", S.GREEN, "WINNER\nMAE 4.231", True),
        ("Variant B", "+ opponent-strength\nadjustment", S.BLUE, "MAE 4.286\n(worse)", False),
        ("Variant C", "+ opponent adj.\n+ history-aware update", S.RED, "MAE 4.280\n(worse)", False),
    ]
    w, h, gap = 3.3, 2.1, 0.55
    x = 0.65
    for title, desc, color, result, winner in variants:
        cx, cy = S.box(ax, (x, 1.4), w, h, title, desc, facecolor=color, fontsize=13)
        badge_color = S.GREEN if winner else "#999999"
        ax.text(cx, 0.85, result, ha="center", va="center", fontsize=10.5,
                color=badge_color, fontweight="bold" if winner else "normal")
        if winner:
            ax.text(cx, 3.75, "BEST", ha="center", fontsize=13, color=S.GOLD, fontweight="bold")
        x += w + gap

    fig.tight_layout()
    fig.savefig(FIGS / "stage7_d3_variant_comparison.png")
    plt.close(fig)
    print("wrote stage7_d3_variant_comparison.png")


def d4_why_dynamic_rating_helps():
    fig, ax = plt.subplots(figsize=(11, 4.0))
    ax.set_xlim(0, 12.5)
    ax.set_ylim(0, 4.3)
    ax.axis("off")
    ax.text(6.25, 4.05, "Short memory vs. long memory", ha="center",
            fontsize=15, fontweight="bold", color=S.NAVY)

    # left: recent form (short memory)
    ax.text(3.0, 3.35, "Recent form (last 5 matches)", ha="center", fontsize=12.5,
            fontweight="bold", color=S.GRAY)
    xs = [1.2, 1.9, 2.6, 3.3, 4.0]
    vals = [0.3, 0.6, 0.2, 0.7, 0.45]
    for i, (px, v) in enumerate(zip(xs, vals)):
        ax.bar(px, v, width=0.5, bottom=1.2, color=S.GRAY, alpha=0.75)
    ax.text(3.0, 0.75, "Only sees the last 5 games —\nforgets everything before that",
            ha="center", fontsize=9.5, color="#666666")

    # right: dynamic rating (long memory)
    ax.text(9.5, 3.35, "Dynamic rating (running form)", ha="center", fontsize=12.5,
            fontweight="bold", color=S.BLUE)
    import numpy as np
    xs2 = np.linspace(7.0, 12.0, 30)
    ys2 = 1.6 + 0.9 * np.sin(xs2 / 1.3) * np.linspace(0.3, 1, 30) + np.linspace(0, 0.6, 30)
    ax.plot(xs2, ys2, color=S.BLUE, linewidth=2.5)
    ax.fill_between(xs2, 1.2, ys2, color=S.BLUE, alpha=0.12)
    ax.text(9.5, 0.75, "Remembers a player's whole history,\nupdating a little after every match",
            ha="center", fontsize=9.5, color="#3f5a9e")

    ax.annotate("", xy=(6.6, 2.0), xytext=(5.3, 2.0),
                arrowprops=dict(arrowstyle="-|>", color=S.NAVY, linewidth=1.8))
    ax.text(5.95, 2.25, "vs.", ha="center", fontsize=11, color=S.NAVY, style="italic")

    fig.tight_layout()
    fig.savefig(FIGS / "stage7_d4_why_dynamic_rating_helps.png")
    plt.close(fig)
    print("wrote stage7_d4_why_dynamic_rating_helps.png")


if __name__ == "__main__":
    d1_system_overview()
    d2_prediction_timing()
    d3_variant_comparison()
    d4_why_dynamic_rating_helps()
