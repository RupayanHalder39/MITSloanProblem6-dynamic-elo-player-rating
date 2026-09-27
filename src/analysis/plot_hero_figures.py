"""
Stage 8.5: HERO FIGURES. A new class of figure on top of Stage 7's already-complete,
scientifically-correct set (unchanged, still the evidence-of-record). Every number below is
copied verbatim from outputs/tables/*.csv (see outputs/reports/HeroFigureIndex.md for the exact
source of each). No new experiment is run here and no number is invented; horizon-margin values
(Hero 7) are a subtraction of two already-existing MAE columns, documented in the index.
"""
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, Circle

from hero_style import (
    NAVY, CHARCOAL, MUTED, GREEN, GREEN_LIGHT, AMBER, AMBER_LIGHT, RED, RED_LIGHT,
    GRAY, GRAY_LIGHT, BLUE, CARD_BG, RULE,
    blank_canvas, card, accent_bar, big_number, label, kicker, connector, caveat_box,
    title_block, n_badge, save,
)


# ---------------------------------------------------------------------------
# HERO 1 — the entire paper in one figure
# ---------------------------------------------------------------------------
def hero_01():
    fig, ax = blank_canvas((15, 8.6))
    title_block(fig, "One Rating. Three Angles of Evidence.",
                "Why a running, match-by-match player rating matters")

    cards = [
        dict(x=0.35, kicker="Better Prediction", accent=GREEN,
             top="4.231", top_lbl="Dynamic rating", bot="4.448", bot_lbl="Last-5 average",
             badge="-4.88% error", badge_color=GREEN,
             foot="Running player strength beats simply\naveraging the last five games."),
        dict(x=3.65, kicker="Better Ranking", accent=BLUE,
             top="+8.18", top_lbl="Top-20% vs rest gap\n(test season, future-3 pts)", bot=None,
             badge="Consistent: +7.18 / +7.66 / +8.18\nacross 2023/24, 2024/25, 2025/26",
             badge_color=BLUE,
             foot="Players rated higher now really do\nperform better next."),
        dict(x=6.95, kicker="Needs History", accent=AMBER,
             top=None, bot=None, badge=None, badge_color=AMBER,
             foot="The rating needs about 15 matches\nbefore we should really trust it."),
    ]
    cw, cy, ch = 2.85, 1.15, 6.65

    # connecting sequence markers above the cards
    centers = [c["x"] + cw / 2 for c in cards]
    connector(ax, (centers[0], cy + ch + 0.55), (centers[2], cy + ch + 0.55), color=RULE, lw=2)
    for i, cx in enumerate(centers, start=1):
        ax.add_patch(Circle((cx, cy + ch + 0.55), 0.22, facecolor=NAVY, edgecolor=NAVY, zorder=5))
        ax.text(cx, cy + ch + 0.55, str(i), ha="center", va="center", fontsize=11,
                 fontweight="bold", color="white", zorder=6)

    for c in cards:
        card(ax, c["x"], cy, cw, ch, accent=c["accent"])
        accent_bar(ax, c["x"], cy + ch - 0.16, cw, color=c["accent"])
        cx = c["x"] + cw / 2
        kicker(ax, cx, cy + ch - 0.6, c["kicker"], color=c["accent"], fontsize=12.5)

        if c["top"] and c["bot"]:
            big_number(ax, cx, cy + ch - 2.05, c["top"], color=c["accent"], fontsize=40)
            label(ax, cx, cy + ch - 2.62, c["top_lbl"], color=CHARCOAL, fontsize=10, weight="bold")
            label(ax, cx, cy + ch - 3.15, "vs.", color=MUTED, fontsize=10, style="italic")
            big_number(ax, cx, cy + ch - 3.75, c["bot"], color=GRAY, fontsize=26)
            label(ax, cx, cy + ch - 4.18, c["bot_lbl"], color=MUTED, fontsize=10)
        elif c["top"]:
            big_number(ax, cx, cy + ch - 2.3, c["top"], color=c["accent"], fontsize=44)
            label(ax, cx, cy + ch - 3.05, c["top_lbl"], color=CHARCOAL, fontsize=10, weight="bold")
        else:
            # Hero 1 Card C: mini trust meter
            mx0, mx1, my = c["x"] + 0.35, c["x"] + cw - 0.35, cy + ch - 2.6
            seg_bounds = [0, 0.34, 0.62, 1.0]
            seg_colors = [GRAY, AMBER, GREEN]
            seg_labels = ["<10 matches", "10-14", "15+"]
            for k in range(3):
                x0 = mx0 + seg_bounds[k] * (mx1 - mx0)
                x1 = mx0 + seg_bounds[k + 1] * (mx1 - mx0)
                ax.add_patch(plt.Rectangle((x0, my), x1 - x0, 0.45, facecolor=seg_colors[k],
                                            edgecolor="white", linewidth=1.5, zorder=3))
                label(ax, (x0 + x1) / 2, my - 0.35, seg_labels[k], fontsize=8.6, color=MUTED)
            seg_desc = ["No clear\nadvantage", "Transition\nzone", "Clear\nadvantage"]
            for k in range(3):
                x0 = mx0 + seg_bounds[k] * (mx1 - mx0)
                x1 = mx0 + seg_bounds[k + 1] * (mx1 - mx0)
                label(ax, (x0 + x1) / 2, my + 0.85, seg_desc[k], fontsize=8.2,
                      color=CHARCOAL, weight="bold")

        if c["badge"]:
            by = cy + 1.55 if c["top"] and not c["bot"] else (cy + 1.15 if not c["top"] else cy + 0.95)
            ax.text(cx, by, c["badge"], ha="center", va="center", fontsize=9.6,
                    fontweight="bold", color="white",
                    bbox=dict(boxstyle="round,pad=0.35", facecolor=c["badge_color"], linewidth=0))
        label(ax, cx, cy + 0.35, c["foot"], color=CHARCOAL, fontsize=10.3)

    caveat_box(fig, "English Championship, 3 seasons (2023/24-2025/26). No causal claims — "
                     "correlational, predictive evidence only. See docs/AbstractClaimReadiness.md.")
    save(fig, "hero_01_paper_in_one_figure")


# ---------------------------------------------------------------------------
# HERO 2 — the rating ladder
# ---------------------------------------------------------------------------
def hero_02():
    deciles = [46.43, 47.26, 48.39, 49.19, 49.36, 50.50, 51.58, 53.06, 54.25, 60.84]
    fig, ax = plt.subplots(figsize=(10.5, 9.2))
    x = np.arange(1, 11)
    colors = plt.cm.Greens(np.linspace(0.35, 0.92, 10))
    ax.bar(x, deciles, width=0.72, color=colors, edgecolor="white", linewidth=1.2, zorder=3)
    ax.step(x, deciles, where="mid", color=NAVY, linewidth=1.6, alpha=0.55, zorder=4)

    for i, (xi, v) in enumerate(zip(x, deciles)):
        if i in (0, 9):
            ax.text(xi, v + 1.8, f"{v:.1f}", ha="center", fontsize=16, fontweight="bold",
                     color=NAVY if i == 9 else CHARCOAL, zorder=5)
        else:
            ax.text(xi, v + 1.0, f"{v:.1f}", ha="center", fontsize=8.3, color=MUTED)
    ax.text(1, 45.0, "LOWEST RATED 10%", ha="center", va="top", fontsize=9.6, color=CHARCOAL,
            fontweight="bold")
    ax.text(10, 67.8, "HIGHEST RATED 10%", ha="center", va="bottom", fontsize=9.6, color=GREEN,
            fontweight="bold")

    ax.text(0.55, -12.5, "LOWER RATING TODAY", ha="left", fontsize=10, color=MUTED,
            fontweight="bold")
    ax.annotate("", xy=(10.45, -12.5), xytext=(3.15, -12.5),
                arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=1.6))
    ax.text(10.45, -12.5, "HIGHER RATING TODAY", ha="right", fontsize=10, color=GREEN,
            fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels([f"D{i}" for i in x])
    ax.set_xlabel("Current-rating decile (D1 = lowest rated 10%  →  D10 = highest rated 10%)")
    ax.set_ylabel("Actual future-3-match performance score (0-100)")
    ax.set_ylim(-18, 78)
    ax.spines["left"].set_visible(False)
    ax.set_yticks([0, 20, 40, 60])
    ax.grid(axis="y", color=RULE, linewidth=0.6, zorder=0)

    box_txt = ("TOP 20% vs REST\n+8.18 future-performance points (test season, 2025/26)\n\n"
               "Season-by-season gap:\n"
               "2023/24: +7.18      2024/25: +7.66      2025/26: +8.18")
    ax.text(0.45, 68.5, box_txt, ha="left", va="top", fontsize=9.6, color=NAVY,
            bbox=dict(boxstyle="round,pad=0.6", facecolor=GREEN_LIGHT, edgecolor=GREEN,
                      linewidth=1.2), zorder=6)

    fig.suptitle("The Rating Ladder", fontsize=19, fontweight="bold", color=NAVY, y=0.985)
    ax.set_title("Higher rating today → better performances tomorrow", fontsize=12.5,
                 color=MUTED, style="italic", pad=10)
    caveat_box(fig, "Ranking evidence, not a precise-score predictor. No causal claim — a higher "
                     "rating is associated with, not proven to cause, better future performance.")
    fig.tight_layout(rect=[0, 0.035, 1, 0.94])
    save(fig, "hero_02_rating_ladder")


# ---------------------------------------------------------------------------
# HERO 3 — the trust meter
# ---------------------------------------------------------------------------
def hero_03():
    fig, ax = blank_canvas((13, 5.3), xlim=(0, 13), ylim=(0, 10))
    title_block(fig, "When Can We Trust the Dynamic Rating?", None, y_title=0.94)

    buckets = ["0-4", "5-9", "10-14", "15-29", "30+"]
    a_mae = [4.248, 3.812, 4.122, 3.909, 4.372]
    l5_mae = [4.201, 3.779, 4.159, 4.183, 4.663]
    colors = [GRAY, GRAY, AMBER, GREEN, GREEN]
    x0, x1, y = 0.6, 12.4, 4.6
    n = 5
    seg_w = (x1 - x0) / n
    for i in range(n):
        xs = x0 + i * seg_w
        ax.add_patch(plt.Rectangle((xs, y), seg_w, 1.1, facecolor=colors[i], edgecolor="white",
                                    linewidth=2, zorder=3))
        cx = xs + seg_w / 2
        label(ax, cx, y + 0.55, f"{buckets[i]}\nmatches", fontsize=11, weight="bold", color="white")
        win = "wins" if a_mae[i] < l5_mae[i] else "loses"
        wcol = "white"
        label(ax, cx, y - 0.55, f"Rating {a_mae[i]:.2f}", fontsize=9.4, weight="bold", color=CHARCOAL)
        label(ax, cx, y - 0.95, f"Last-5 {l5_mae[i]:.2f}  ({win})", fontsize=8.6, color=MUTED)

    zone_defs = [(0, 2, "TOO LITTLE HISTORY", GRAY, "No clear advantage"),
                 (2, 3, "SIGNAL EMERGING", AMBER, "Transition zone"),
                 (3, 5, "TRUST ZONE", GREEN, "Clear advantage")]
    for a, b, ztitle, zcol, zsub in zone_defs:
        cx = x0 + (a + b) / 2 * seg_w
        label(ax, cx, y + 2.05, ztitle, fontsize=12, weight="bold", color=zcol)
        label(ax, cx, y + 1.65, zsub, fontsize=9.3, color=MUTED, style="italic")
        ax.plot([x0 + a * seg_w + 0.05, x0 + b * seg_w - 0.05], [y + 1.35, y + 1.35],
                color=zcol, linewidth=3, solid_capstyle="round")

    ax.annotate("Clear advantage emerges\naround 15 prior matches",
                xy=(x0 + 3 * seg_w, y), xytext=(x0 + 3 * seg_w, y - 2.2),
                ha="center", fontsize=11, fontweight="bold", color=GREEN,
                arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=1.6))

    caveat_box(fig, "\"~15 matches\" describes where the tested history buckets show a clear, "
                     "consistent advantage — it is not a fitted mathematical cutoff. "
                     "outputs/tables/exp_history_depth.csv.")
    save(fig, "hero_03_when_can_we_trust_rating")


# ---------------------------------------------------------------------------
# HERO 4 — where the model works (positions)
# ---------------------------------------------------------------------------
def hero_04():
    fig, ax = blank_canvas((13, 8), xlim=(0, 13), ylim=(0, 10))
    title_block(fig, "One Rating Does Not Work Equally Well for Every Position", None, y_title=0.955)

    positions = [
        dict(name="GK", r2="−0.122", accent=RED, face=RED_LIGHT,
             desc="Current score cannot separate\nkeepers reliably", order=1),
        dict(name="DEF", r2="0.322", accent=GREEN, face=GREEN_LIGHT,
             desc="Strong predictive signal", order=2),
        dict(name="MID", r2="0.429", accent=GREEN, face=GREEN_LIGHT,
             desc="Strongest predictive signal", order=3),
        dict(name="ATT", r2="0.082", accent=AMBER, face=AMBER_LIGHT,
             desc="Weaker / more volatile signal", order=4),
    ]
    cw, gap = 2.7, 0.35
    x0 = (13 - (4 * cw + 3 * gap)) / 2
    base_y = 2.0
    heights = {"GK": 5.0, "DEF": 6.3, "MID": 6.9, "ATT": 5.5}
    for i, p in enumerate(positions):
        x = x0 + i * (cw + gap)
        h = heights[p["name"]]
        card(ax, x, base_y, cw, h, accent=p["accent"], face=p["face"])
        accent_bar(ax, x, base_y + h - 0.18, cw, color=p["accent"])
        cx = x + cw / 2
        kicker(ax, cx, base_y + h - 0.65, p["name"], color=NAVY, fontsize=15)
        big_number(ax, cx, base_y + h / 2 + 0.5, p["r2"], color=p["accent"], fontsize=32)
        label(ax, cx, base_y + h / 2 - 0.35, "R² (future-3 target)", color=MUTED, fontsize=9)
        label(ax, cx, base_y + 0.75, p["desc"], color=CHARCOAL, fontsize=10, weight="bold")

    ax.annotate("", xy=(x0 + 4 * cw + 3 * gap, 1.35), xytext=(x0, 1.35),
                arrowprops=dict(arrowstyle="-|>", color=RULE, lw=1.5))
    label(ax, 6.5, 0.85, "Typical pitch order: goalkeeper → defence → midfield → attack",
          color=MUTED, fontsize=9.5, style="italic")

    caveat_box(fig, "Championship sample, current performance-score design. GK limitation reflects "
                     "the underlying target, not the rating engine — see Hero 10.")
    save(fig, "hero_04_where_rating_works")


# ---------------------------------------------------------------------------
# HERO 5 — simplicity won
# ---------------------------------------------------------------------------
def hero_05():
    fig, ax = blank_canvas((14, 8), xlim=(0, 14), ylim=(0, 10))
    title_block(fig, "Adding Complexity Did Not Improve Prediction", None, y_title=0.955)

    lanes = [
        dict(y=7.1, name="Variant A", steps=["Match performance score"], mae="4.231",
             accent=GREEN, best=True),
        dict(y=4.55, name="Variant B", steps=["Match performance score", "+ opponent-strength adj."],
             mae="4.286", accent=GRAY, best=False),
        dict(y=2.0, name="Variant C",
             steps=["Match performance score", "+ opponent-strength adj.", "+ history-aware speed"],
             mae="4.280", accent=AMBER, best=False),
    ]
    step_x0, step_w, step_gap = 0.5, 2.9, 0.35
    for ln in lanes:
        label(ax, 0.5, ln["y"] + 1.0, ln["name"], ha="left", color=NAVY, fontsize=13, weight="bold")
        xi = step_x0
        prev_c = None
        for si, step_text in enumerate(ln["steps"]):
            box_w = step_w if si == 0 else step_w + 0.9
            card(ax, xi, ln["y"], box_w, 0.95, accent=ln["accent"], face=CARD_BG, lw=1.2)
            label(ax, xi + box_w / 2, ln["y"] + 0.48, step_text, color=CHARCOAL, fontsize=9.2)
            if prev_c is not None:
                connector(ax, (prev_c, ln["y"] + 0.48), (xi, ln["y"] + 0.48),
                          color=ln["accent"], lw=1.8)
            prev_c = xi + box_w
            xi += box_w + step_gap
        connector(ax, (prev_c, ln["y"] + 0.48), (11.0, ln["y"] + 0.48), color=ln["accent"], lw=1.8)
        card(ax, 11.0, ln["y"] - 0.05, 2.4, 1.05, accent=ln["accent"],
             face=GREEN_LIGHT if ln["best"] else "#f4f5f6")
        label(ax, 12.2, ln["y"] + 0.62, "Test MAE", color=MUTED, fontsize=8.6)
        big_number(ax, 12.2, ln["y"] + 0.25, ln["mae"], color=ln["accent"], fontsize=20)
        if ln["best"]:
            label(ax, 12.2, ln["y"] - 0.28, "BEST", color=GREEN, fontsize=9, weight="bold")

    label(ax, 7, 0.95, "Adding complexity did not improve prediction.",
          color=NAVY, fontsize=16.5, weight="bold")
    caveat_box(fig, "This compares 3 specific enhancements tested here — it is not a general claim "
                     "that simpler models always outperform complex ones. outputs/tables/"
                     "stage5_primary_method_comparison.csv.")
    save(fig, "hero_05_simpler_rating_wins")


# ---------------------------------------------------------------------------
# HERO 6 — opponent adjustment backfires
# ---------------------------------------------------------------------------
def hero_06():
    scales = [0.00, 0.01, 0.02, 0.03, 0.04, 0.05]
    mae = [4.151, 4.198, 4.256, 4.311, 4.351, 4.386]
    fig, ax = plt.subplots(figsize=(11.5, 7.2))
    ax.plot(scales, mae, color=RED, linewidth=2.6, zorder=3)
    ax.scatter(scales, mae, s=70, color=RED, zorder=4, edgecolor="white", linewidth=1.2)
    ax.fill_between(scales, mae, min(mae) - 0.05, color=RED, alpha=0.06, zorder=1)

    ax.scatter([0.00], [4.151], s=220, color=GREEN, zorder=5, edgecolor="white", linewidth=1.6)
    ax.annotate("BEST\nNo opponent correction\nMAE 4.151", xy=(0.00, 4.151), xytext=(0.006, 4.17),
                fontsize=10.3, fontweight="bold", color=GREEN, ha="left",
                arrowprops=dict(arrowstyle="-", color=GREEN, lw=1.2))
    ax.annotate("Original design\nMAE 4.311", xy=(0.03, 4.311), xytext=(0.019, 4.30),
                fontsize=9.8, color=AMBER, fontweight="bold", ha="right",
                arrowprops=dict(arrowstyle="-", color=AMBER, lw=1.1))
    ax.annotate("WORST TESTED\nMAE 4.386", xy=(0.05, 4.386), xytext=(0.044, 4.40),
                fontsize=9.8, color=RED, fontweight="bold", ha="left",
                arrowprops=dict(arrowstyle="-", color=RED, lw=1.1))

    ax.set_xlabel("Opponent-adjustment strength (validation split, predefined grid)")
    ax.set_ylabel("Prediction error, MAE (lower is better)")
    ax.set_xlim(-0.004, 0.058)
    ax.set_ylim(4.12, 4.42)
    ax.grid(axis="y", color=RULE, linewidth=0.6, zorder=0)

    fig.suptitle("Opponent Adjustment Backfires", fontsize=19, fontweight="bold", color=NAVY, y=0.99)
    ax.set_title("We expected harder opponents to need extra credit.\n"
                  "In this implementation, every amount of adjustment made prediction worse.",
                 fontsize=11.5, color=MUTED, style="italic", pad=10)
    caveat_box(fig, "This does NOT mean opponent quality is irrelevant — only that this specific "
                     "adjustment mechanism hurt prediction here. outputs/tables/exp_opponent_scale.csv.")
    fig.tight_layout(rect=[0, 0.035, 1, 0.86])
    save(fig, "hero_06_opponent_adjustment_backfires")


# ---------------------------------------------------------------------------
# HERO 7 — future-horizon dominance (win margin)
# ---------------------------------------------------------------------------
def hero_07():
    horizons = [1, 2, 3, 5, 7]
    a = {1: 6.473, 2: 4.912, 3: 4.231, 5: 3.532, 7: 3.230}
    l5 = {1: 6.584, 2: 5.083, 3: 4.448, 5: 3.827, 7: 3.553}
    ctd = {1: 6.518, 2: 4.998, 3: 4.349, 5: 3.690, 7: 3.393}
    margin_l5 = [round(l5[h] - a[h], 3) for h in horizons]
    margin_ctd = [round(ctd[h] - a[h], 3) for h in horizons]

    fig, ax = plt.subplots(figsize=(10.5, 7))
    x = np.arange(len(horizons))
    w = 0.38
    ax.bar(x - w / 2, margin_l5, width=w, color=GREEN, label="vs. Last-5 average", zorder=3)
    ax.bar(x + w / 2, margin_ctd, width=w, color=BLUE, alpha=0.75, label="vs. Career-to-date", zorder=3)
    for xi, v in zip(x - w / 2, margin_l5):
        ax.text(xi, v + 0.008, f"+{v:.3f}", ha="center", fontsize=9.3, fontweight="bold", color=GREEN)
    for xi, v in zip(x + w / 2, margin_ctd):
        ax.text(xi, v + 0.008, f"+{v:.3f}", ha="center", fontsize=8.6, color=BLUE)

    ax.axhline(0, color=CHARCOAL, linewidth=1.1)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{h} match{'es' if h != 1 else ''} ahead" for h in horizons])
    ax.set_ylabel("Error reduction vs. dynamic rating\n(MAE points, higher = bigger win)")
    ax.set_ylim(0, 0.36)
    ax.grid(axis="y", color=RULE, linewidth=0.6, zorder=0)
    ax.legend(loc="upper left", fontsize=10)

    fig.suptitle("The Advantage Survives Whether We Look 1 or 7 Matches Ahead",
                 fontsize=16.5, fontweight="bold", color=NAVY, y=0.99)
    caveat_box(fig, "Margin = comparator MAE − dynamic-rating MAE, from outputs/tables/"
                     "exp_future_horizons.csv (e.g. horizon 3: last5 4.448 − A 4.231 = 0.217). "
                     "No per-horizon bootstrap CI was computed.", y=0.005)
    fig.tight_layout(rect=[0.02, 0.11, 1, 0.92])
    save(fig, "hero_07_works_across_horizons")


# ---------------------------------------------------------------------------
# HERO 8 — evidence forest (upgraded)
# ---------------------------------------------------------------------------
def hero_08():
    rows = [
        ("Last 5 average", -0.217, -0.286, -0.149),
        ("Season-to-date", -0.164, -0.229, -0.099),
        ("Career-to-date", -0.118, -0.201, -0.038),
        ("+ Opponent adj. (B)", -0.056, -0.087, -0.024),
        ("+ Opponent + history (C)", -0.049, -0.085, -0.015),
    ]
    fig, ax = plt.subplots(figsize=(11, 6.6))
    y = np.arange(len(rows))[::-1]
    for yi, (nm, mean, lo, hi) in zip(y, rows):
        ax.plot([lo, hi], [yi, yi], color=GREEN, linewidth=3.2, zorder=3, solid_capstyle="round")
        ax.scatter([mean], [yi], s=90, color=NAVY, zorder=4, edgecolor="white", linewidth=1.3)
        ax.text(hi + 0.008, yi, f"{mean:.3f}  [{lo:.3f}, {hi:.3f}]", va="center", fontsize=9.6,
                color=CHARCOAL)
    ax.axvline(0, color=CHARCOAL, linewidth=1.3, linestyle="--")
    ax.text(0, len(rows) - 0.15, "0 = no difference", ha="center", fontsize=9, color=MUTED,
            style="italic")
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=11.5)
    ax.set_xlabel("MAE difference: Dynamic rating (A) − comparator")
    ax.set_xlim(-0.34, 0.09)
    ax.text(-0.3, -1.0, "←  DYNAMIC RATING BETTER", ha="left", fontsize=10.5, fontweight="bold",
            color=GREEN)
    ax.text(0.08, -1.0, "COMPARATOR BETTER  →", ha="right", fontsize=10.5, fontweight="bold",
            color=GRAY)
    ax.set_ylim(-1.6, len(rows) + 0.3)
    ax.grid(axis="x", color=RULE, linewidth=0.6, zorder=0)

    fig.suptitle("The Main Advantage Survives Player-Level Resampling", fontsize=17,
                 fontweight="bold", color=NAVY, y=0.99)
    ax.set_title("We resampled whole players 2,000 times (player-clustered bootstrap, seed=42). "
                 "Every 95% interval sits entirely on the dynamic-rating side.",
                 fontsize=10.3, color=MUTED, style="italic", pad=8)
    caveat_box(fig, "outputs/tables/exp_bootstrap_effects.csv. Uncertainty is descriptive "
                     "(bootstrap CIs), not classical hypothesis-test p-values.")
    fig.tight_layout(rect=[0, 0.035, 1, 0.9])
    save(fig, "hero_08_evidence_forest")


# ---------------------------------------------------------------------------
# HERO 9 — score design matters
# ---------------------------------------------------------------------------
def hero_09():
    fig, ax = blank_canvas((12.5, 9), xlim=(0, 12.5), ylim=(0, 10))
    title_block(fig, "How We Summarize a Match Matters — Before the Rating Even Starts",
                None, y_title=0.965)

    card(ax, 4.05, 8.5, 4.4, 0.85, accent=NAVY, face=GRAY_LIGHT)
    label(ax, 6.25, 8.92, "MATCH ACTIONS", color=NAVY, fontsize=12.5, weight="bold")

    connector(ax, (5.2, 8.5), (2.3, 7.5), color=GRAY, lw=1.8)
    connector(ax, (7.3, 8.5), (9.2, 7.5), color=BLUE, lw=1.8)

    card(ax, 0.5, 6.6, 3.6, 0.9, accent=GRAY, face=GRAY_LIGHT)
    label(ax, 2.3, 7.05, "Every raw metric treated\nequally (Score A)", fontsize=9.8, color=CHARCOAL)

    cats = ["Attack", "Creation", "Possession", "Defending"]
    cx0 = 6.7
    for i, cname in enumerate(cats):
        cx = cx0 + i * 1.05
        card(ax, cx, 6.6, 0.9, 0.9, accent=BLUE, face=CARD_BG, lw=1.1)
        label(ax, cx + 0.45, 7.05, cname, fontsize=7.9, color=NAVY, weight="bold")
    label(ax, 8.9, 6.0, "balanced across categories (Score B)", fontsize=9, color=MUTED,
          style="italic")

    connector(ax, (2.3, 6.6), (2.3, 5.5), color=GRAY, lw=1.8)
    connector(ax, (8.9, 6.6), (8.9, 6.3), color=BLUE, lw=1.8)
    connector(ax, (8.9, 5.75), (8.9, 5.5), color=BLUE, lw=1.8)
    card(ax, 0.7, 4.6, 3.2, 0.85, accent=GRAY, face="#f4f5f6")
    label(ax, 2.3, 5.02, "Score A", fontsize=11, weight="bold", color=CHARCOAL)
    card(ax, 7.3, 4.6, 3.2, 0.85, accent=BLUE, face="#eaf0fe")
    label(ax, 8.9, 5.02, "Score B (production)", fontsize=11, weight="bold", color=BLUE)

    connector(ax, (2.3, 4.6), (5.5, 3.7), color=GRAY, lw=1.6)
    connector(ax, (8.9, 4.6), (7.0, 3.7), color=BLUE, lw=1.6)
    card(ax, 4.6, 2.9, 3.3, 0.85, accent=NAVY, face=GRAY_LIGHT)
    label(ax, 6.25, 3.32, "Dynamic rating engine", fontsize=10.5, weight="bold", color=NAVY)

    connector(ax, (6.25, 2.9), (6.25, 2.1), color=NAVY, lw=1.6)
    ry = 0.4
    card(ax, 1.6, ry, 4.0, 1.55, accent=GRAY, face="#f4f5f6")
    label(ax, 3.6, ry + 1.2, "SCORE A RESULT", fontsize=10, weight="bold", color=CHARCOAL)
    big_number(ax, 3.6, ry + 0.72, "MAE 4.507", color=GRAY, fontsize=17)
    label(ax, 3.6, ry + 0.28, "Spearman 0.503", color=MUTED, fontsize=9.5)

    card(ax, 6.9, ry, 4.0, 1.55, accent=GREEN, face=GREEN_LIGHT)
    label(ax, 8.9, ry + 1.2, "SCORE B RESULT (WINS)", fontsize=10, weight="bold", color=GREEN)
    big_number(ax, 8.9, ry + 0.72, "MAE 4.231", color=GREEN, fontsize=17)
    label(ax, 8.9, ry + 0.28, "Spearman 0.534", color=GREEN, fontsize=9.5)

    caveat_box(fig, "Full downstream pipeline rerun for both scores, identical rating engine and "
                     "evaluation. outputs/tables/exp_score_ablation.csv.")
    save(fig, "hero_09_score_design_matters")


# ---------------------------------------------------------------------------
# HERO 10 — goalkeeper diagnosis
# ---------------------------------------------------------------------------
def hero_10():
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.6))
    fig.suptitle("Goalkeeper Failure Starts in the Performance Target, Not the Rating Engine",
                 fontsize=15.5, fontweight="bold", color=NAVY, y=1.02)

    ax = axes[0]
    ax.set_title("Can our match score tell goalkeepers apart?", fontsize=11.5, color=MUTED,
                 style="italic")
    pos = ["ATT", "DEF", "MID", "GK"]
    vals = [31, 26, 30, 10]
    colors = [GREEN, GREEN, GREEN, RED]
    bars = ax.bar(pos, vals, color=colors, width=0.6, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1, f"{v}%", ha="center", fontsize=12,
                fontweight="bold", color=CHARCOAL)
    ax.set_ylabel("Share of score variance that is\nbetween different players (signal, not noise)")
    ax.set_ylim(0, 38)
    ax.grid(axis="y", color=RULE, linewidth=0.6, zorder=0)

    ax = axes[1]
    ax.set_title("Can ANY method predict next-match\ngoalkeeper performance?", fontsize=11.5,
                 color=MUTED, style="italic")
    methods = ["Last\nmatch", "Last-5\navg", "Career-\nto-date", "Dynamic\nrating"]
    sp = [0.027, 0.116, 0.186, 0.181]
    bars = ax.bar(methods, sp, color=[GRAY, GRAY, RED, RED], width=0.6, zorder=3)
    for b, v in zip(bars, sp):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.008, f"{v:.3f}", ha="center", fontsize=10.5,
                fontweight="bold", color=CHARCOAL)
    ax.axhline(0.30, color=GREEN, linewidth=1.4, linestyle="--")
    ax.text(3.55, 0.31, "meaningful signal\n(outfield positions)", ha="right", fontsize=8.3,
            color=GREEN, style="italic")
    ax.set_ylabel("Spearman correlation with future GK performance")
    ax.set_ylim(0, 0.36)
    ax.grid(axis="y", color=RULE, linewidth=0.6, zorder=0)

    fig.text(0.5, 0.03,
              "Every method fails for goalkeepers — even a zero-modeling single-match guess.",
              ha="center", fontsize=12, fontweight="bold", color=RED)
    caveat_box(fig, "Current score design only — not evidence that goalkeeper rating is "
                     "impossible in principle. outputs/tables/exp_target_stability.csv, "
                     "exp_gk_diagnosis.csv.", y=-0.01)
    fig.tight_layout(rect=[0, 0.09, 1, 0.92])
    save(fig, "hero_10_goalkeeper_problem")


# ---------------------------------------------------------------------------
# HERO 11 — rating memory vs recent form
# ---------------------------------------------------------------------------
def hero_11():
    fig, ax = blank_canvas((12.5, 8), xlim=(0, 12.5), ylim=(0, 10))
    title_block(fig, "Long Memory vs. Recent Form", None, y_title=0.955)

    label(ax, 1.0, 8.2, "LAST-5 FORM", ha="left", fontsize=12.5, weight="bold", color=GRAY)
    label(ax, 1.0, 7.75, "only remembers the last 5 matches", ha="left", fontsize=9.5, color=MUTED)
    for i in range(5):
        x = 1.0 + i * 0.58
        card(ax, x, 6.7, 0.46, 0.7, accent=GRAY, face=GRAY_LIGHT, lw=1)
    card(ax, 4.1, 6.7, 0.46, 0.7, accent=GRAY, face="#fff", lw=1)
    ax.text(4.33, 7.05, "…", ha="center", fontsize=14, color=GRAY)
    connector(ax, (0.75, 6.35), (4.9, 6.35), color=GRAY, lw=6)
    label(ax, 2.8, 5.85, "sliding 5-match window — older matches are forgotten entirely",
          fontsize=8.8, color=MUTED, style="italic")

    label(ax, 1.0, 4.7, "DYNAMIC RATING", ha="left", fontsize=12.5, weight="bold", color=BLUE)
    label(ax, 1.0, 4.25, "carries information forward from a player's full accumulated history",
          ha="left", fontsize=9.5, color=MUTED)
    n_hist = 14
    for i in range(n_hist):
        x = 1.0 + i * 0.27
        h = 0.35 + 0.45 * (i / n_hist)
        ax.add_patch(plt.Rectangle((x, 3.15), 0.22, h, facecolor=BLUE,
                                    alpha=0.35 + 0.5 * (i / n_hist), zorder=3))
    label(ax, 6.0, 2.75, "each match updates the rating; earlier matches still echo through it",
          fontsize=8.8, color=MUTED, style="italic")

    card(ax, 8.7, 3.0, 3.3, 4.4, accent=NAVY, face=CARD_BG)
    label(ax, 10.35, 6.95, "MEASURED RESULT", fontsize=10, weight="bold", color=NAVY)
    big_number(ax, 10.35, 6.15, "4.231", color=BLUE, fontsize=26)
    label(ax, 10.35, 5.72, "Dynamic rating MAE", fontsize=9, color=MUTED)
    label(ax, 10.35, 5.35, "vs.", fontsize=9, color=MUTED, style="italic")
    big_number(ax, 10.35, 4.75, "4.448", color=GRAY, fontsize=20)
    label(ax, 10.35, 4.38, "Last-5 average MAE", fontsize=9, color=MUTED)
    label(ax, 10.35, 3.7, "Long memory wins —\nbut only past ~15 matches\n(see Hero 3)",
          fontsize=8.8, color=CHARCOAL, weight="bold")

    caveat_box(fig, "Mechanism illustration (conceptual) paired with measured results from "
                     "outputs/tables/stage5_primary_method_comparison.csv and exp_history_depth.csv.")
    save(fig, "hero_11_long_memory_vs_recent_form")


# ---------------------------------------------------------------------------
# HERO 12 — the honest scorecard
# ---------------------------------------------------------------------------
def hero_12():
    fig, ax = blank_canvas((11, 10.5), xlim=(0, 11), ylim=(0, 10.5))
    title_block(fig, "The Honest Scorecard", "What worked, what was limited, and what did not work",
                y_title=0.975, y_sub=0.945)

    sections = [
        dict(y0=6.55, h=3.35, title="WORKED", mark="✓", accent=GREEN, face=GREEN_LIGHT,
             items=["Dynamic rating vs. last-5 average", "Dynamic rating vs. season-to-date",
                    "Dynamic rating vs. career-to-date", "Ranking players by rating level",
                    "Category-balanced Score B (vs. Score A)", "Robust across 1-7 match horizons"]),
        dict(y0=3.55, h=2.65, title="LIMITED", mark="△", accent=AMBER, face=AMBER_LIGHT,
             items=["New players (<~15 matches)", "Attacking-position players",
                    "Minutes-confidence weighting"]),
        dict(y0=0.55, h=2.65, title="DID NOT WORK", mark="✕", accent=RED, face=RED_LIGHT,
             items=["Opponent-strength adjustment", "History-aware update decay",
                    "Current goalkeeper performance target"]),
    ]
    for s in sections:
        card(ax, 0.4, s["y0"], 10.2, s["h"], accent=s["accent"], face=s["face"])
        accent_bar(ax, 0.4, s["y0"] + s["h"] - 0.16, 10.2, color=s["accent"])
        label(ax, 1.0, s["y0"] + s["h"] - 0.55, s["title"], ha="left", fontsize=14, weight="bold",
              color=s["accent"])
        row_h = (s["h"] - 0.95) / max(len(s["items"]), 1)
        for i, item in enumerate(s["items"]):
            iy = s["y0"] + s["h"] - 1.0 - i * row_h - row_h / 2 + 0.05
            ax.text(1.1, iy, s["mark"], fontsize=13, color=s["accent"], fontweight="bold", va="center")
            label(ax, 1.75, iy, item, ha="left", fontsize=10.6, color=CHARCOAL)

    caveat_box(fig, "\"Limited\"/\"did not work\" are reported with the same rigor as the successes — "
                     "see docs/NegativeFindingsRegister.md for full technical detail on each.")
    save(fig, "hero_12_what_worked_what_didnt")


# ---------------------------------------------------------------------------
# HERO 13 (bonus) — sporting director dashboard concept (illustrative only)
# ---------------------------------------------------------------------------
def hero_13():
    fig, ax = blank_canvas((13, 8.6), xlim=(0, 13), ylim=(0, 10))
    banner_color = "#5b3fa0"
    ax.add_patch(plt.Rectangle((0, 9.15), 13, 0.85, facecolor=banner_color, zorder=5))
    ax.text(6.5, 9.575, "ILLUSTRATIVE PRODUCT CONCEPT  —  NOT AN EXPERIMENTAL RESULT",
            ha="center", va="center", fontsize=13, fontweight="bold", color="white", zorder=6)

    title_block(fig, "A Sporting-Director View (Concept)", None, y_title=0.895)

    cols = ["Current rating", "Recent trend", "History confidence", "Next-few-games outlook"]
    col_x = [3.3, 5.6, 7.9, 10.5]
    for cx, cname in zip(col_x, cols):
        label(ax, cx, 8.1, cname, fontsize=10, weight="bold", color=NAVY)

    players = [
        dict(name="PLAYER A", rating="1583", trend="up", conf="High", outlook="Promising",
             ocolor=GREEN),
        dict(name="PLAYER B", rating="1502", trend="flat", conf="Medium", outlook="Stable",
             ocolor=AMBER),
        dict(name="PLAYER C", rating="1447", trend="down", conf="Low", outlook="Uncertain",
             ocolor=GRAY),
    ]
    row_y = [6.6, 4.5, 2.4]
    for p, ry in zip(players, row_y):
        card(ax, 0.4, ry, 12.2, 1.7, accent=RULE, face=CARD_BG, lw=1.0)
        label(ax, 1.6, ry + 0.85, p["name"], ha="left", fontsize=11.5, weight="bold", color=NAVY)
        big_number(ax, col_x[0], ry + 0.85, p["rating"], color=BLUE, fontsize=20)
        arrow_glyph = {"up": "↑ rising", "down": "↓ falling", "flat": "→ flat"}[p["trend"]]
        acolor = {"up": GREEN, "down": RED, "flat": GRAY}[p["trend"]]
        label(ax, col_x[1], ry + 0.85, arrow_glyph, color=acolor, fontsize=12, weight="bold")
        conf_frac = {"High": 0.9, "Medium": 0.55, "Low": 0.25}[p["conf"]]
        bx0 = col_x[2] - 0.9
        ax.add_patch(plt.Rectangle((bx0, ry + 0.65), 1.8, 0.3, facecolor=GRAY_LIGHT, zorder=3))
        ax.add_patch(plt.Rectangle((bx0, ry + 0.65), 1.8 * conf_frac, 0.3, facecolor=BLUE, zorder=4))
        label(ax, col_x[2], ry + 0.35, p["conf"], fontsize=9.5, color=MUTED)
        ax.text(col_x[3], ry + 0.85, p["outlook"], ha="center", va="center", fontsize=10.5,
                fontweight="bold", color="white", zorder=4,
                bbox=dict(boxstyle="round,pad=0.35", facecolor=p["ocolor"], linewidth=0))

    ax.add_patch(plt.Rectangle((0, 0.15), 13, 0.75, facecolor=banner_color, alpha=0.12, zorder=1))
    label(ax, 6.5, 0.53, "Generic illustrative labels only — no real player names or values are used.",
          fontsize=9.5, color=banner_color, weight="bold")

    save(fig, "hero_13_sporting_director_view")


if __name__ == "__main__":
    for fn in [hero_01, hero_02, hero_03, hero_04, hero_05, hero_06, hero_07, hero_08,
               hero_09, hero_10, hero_11, hero_12, hero_13]:
        fn()
    print("All hero figures generated.")
