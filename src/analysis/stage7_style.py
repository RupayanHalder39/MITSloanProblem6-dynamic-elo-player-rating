"""
Stage 7: shared visual identity for every publication-quality figure/diagram this stage produces.
Consistent palette, typography, and helper functions so all Stage-7 assets look like one system.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

NAVY = "#152341"
CHARCOAL = "#2b2b2b"
BLUE = "#2563eb"          # dynamic rating / primary positive
RED = "#c0392b"           # negative result / warning
GREEN = "#1f6f43"         # winning method / success
GRAY = "#8a8f98"          # neutral / baseline
LIGHT_GRAY = "#c8ccd2"
GOLD = "#a86f1f"          # accent
BG = "#ffffff"

METHOD_COLORS = {
    "variant_A": GREEN, "variant_B": BLUE, "variant_C": RED,
    "last1": "#dcdfe4", "last3": "#c8ccd2", "last5": GRAY,
    "season_to_date": GOLD, "career_to_date": "#7a5015", "position_prior": "#eceef1",
}

plt.rcParams.update({
    "figure.dpi": 200,
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "savefig.facecolor": BG,
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 12,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 12,
    "axes.edgecolor": "#333333",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.labelsize": 10.5,
    "ytick.labelsize": 10.5,
    "legend.fontsize": 10,
    "legend.frameon": False,
})


def add_caption(fig, text, y=-0.02):
    fig.text(0.5, y, text, ha="center", va="top", fontsize=9, color="#555555", wrap=True)


def add_n(ax, n, loc="upper right"):
    xy = {"upper right": (0.98, 0.96), "upper left": (0.02, 0.96),
          "lower right": (0.98, 0.04), "lower left": (0.02, 0.04)}[loc]
    ha = "right" if "right" in loc else "left"
    va = "top" if "upper" in loc else "bottom"
    ax.text(xy[0], xy[1], f"n={n:,}", transform=ax.transAxes, ha=ha, va=va,
             fontsize=9, color="#666666", style="italic")


def box(ax, xy, w, h, label, value=None, facecolor=BLUE, textcolor=NAVY, alpha=0.14, fontsize=11):
    b = FancyBboxPatch(xy, w, h, boxstyle="round,pad=0.06,rounding_size=0.12",
                        linewidth=1.6, edgecolor=facecolor, facecolor=facecolor, alpha=alpha)
    ax.add_patch(b)
    cx, cy = xy[0] + w / 2, xy[1] + h / 2
    if value is not None:
        ax.text(cx, cy + h * 0.16, label, ha="center", va="center", fontsize=fontsize,
                 color=textcolor, fontweight="bold")
        ax.text(cx, cy - h * 0.22, value, ha="center", va="center", fontsize=fontsize - 1.5,
                 color=facecolor, fontweight="bold")
    else:
        ax.text(cx, cy, label, ha="center", va="center", fontsize=fontsize,
                 color=textcolor, fontweight="bold")
    return cx, cy


def arrow(ax, start, end, color=NAVY, label=None, label_fontsize=9.5):
    a = FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=20,
                         linewidth=2.0, color=color)
    ax.add_patch(a)
    if label:
        mx, my = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
        ax.text(mx, my + 0.28, label, ha="center", va="center", fontsize=label_fontsize,
                 color=color, style="italic")
