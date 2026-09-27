"""
Stage 8.5: shared visual identity for HERO figures — a new, more dashboard-like class of
figures layered on top of (not replacing) the Stage 7 visual system in stage7_style.py.
Same semantic palette as Stage 7, extended with card/flow/threshold-band primitives so a
hero figure reads as one dominant message within 5-10 seconds.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from pathlib import Path

NAVY = "#152341"
CHARCOAL = "#2b2b2b"
MUTED = "#5b5f66"
GREEN = "#1e7e42"          # supported / positive evidence
GREEN_LIGHT = "#e6f4ea"
AMBER = "#b8730f"          # caution / threshold / transition
AMBER_LIGHT = "#fdf1e0"
RED = "#c0392b"            # genuine negative finding only
RED_LIGHT = "#fbeae8"
GRAY = "#8a8f98"           # baseline / neutral
GRAY_LIGHT = "#eef0f2"
BLUE = "#2563eb"           # dynamic rating identity color (kept from Stage 7)
BG = "#ffffff"
CARD_BG = "#fbfbfc"
RULE = "#d8dbe0"

FIG_DIR = Path(__file__).resolve().parents[2] / "outputs" / "figures"

plt.rcParams.update({
    "figure.dpi": 300,
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "savefig.facecolor": BG,
    "font.family": "sans-serif",
    # DejaVu Sans first (not Helvetica/Arial): it is the one family in this environment with full
    # glyph coverage for the check/triangle/cross/arrow marks these figures use as direct icons —
    # matplotlib's per-family fallback did not reliably substitute glyphs Helvetica/Arial lacked.
    "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial"],
    "font.size": 12,
    "axes.edgecolor": "#333333",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "legend.frameon": False,
})


def blank_canvas(figsize, xlim=(0, 10), ylim=(0, 10)):
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis("off")
    return fig, ax


def card(ax, x, y, w, h, accent=BLUE, face=CARD_BG, lw=1.4, radius=0.18):
    b = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={radius}",
                        linewidth=lw, edgecolor=accent, facecolor=face, zorder=2)
    ax.add_patch(b)
    return b


def accent_bar(ax, x, y, w, h_bar=0.14, color=BLUE, radius=0.07):
    b = FancyBboxPatch((x, y), w, h_bar, boxstyle=f"round,pad=0,rounding_size={radius}",
                        linewidth=0, facecolor=color, zorder=3)
    ax.add_patch(b)


def big_number(ax, x, y, text, color=NAVY, fontsize=34, weight="bold", ha="center"):
    ax.text(x, y, text, ha=ha, va="center", fontsize=fontsize, fontweight=weight,
             color=color, zorder=4)


def label(ax, x, y, text, color=CHARCOAL, fontsize=10.5, weight="normal", ha="center",
          style="normal"):
    ax.text(x, y, text, ha=ha, va="center", fontsize=fontsize, fontweight=weight,
             color=color, style=style, zorder=4, wrap=True)


def kicker(ax, x, y, text, color=MUTED, fontsize=9.5, ha="center"):
    ax.text(x, y, text.upper(), ha=ha, va="center", fontsize=fontsize, fontweight="bold",
             color=color, zorder=4)


def connector(ax, start, end, color=RULE, lw=2.2, style="-"):
    a = FancyArrowPatch(start, end, arrowstyle="-", linewidth=lw, color=color,
                         linestyle=style, zorder=1)
    ax.add_patch(a)


def caveat_box(fig, text, y=0.015, color=MUTED):
    fig.text(0.5, y, text, ha="center", va="bottom", fontsize=8.6, color=color,
              style="italic", wrap=True)


def title_block(fig, title, subtitle=None, y_title=0.965, y_sub=0.925):
    fig.text(0.5, y_title, title, ha="center", va="top", fontsize=19, fontweight="bold",
              color=NAVY)
    if subtitle:
        fig.text(0.5, y_sub, subtitle, ha="center", va="top", fontsize=11.5, color=MUTED,
                  style="italic")


def n_badge(ax, x, y, text, color=MUTED, fontsize=8.8, ha="center"):
    ax.text(x, y, text, ha=ha, va="center", fontsize=fontsize, color=color, style="italic",
             zorder=4)


def save(fig, name, also_pdf=True):
    png_path = FIG_DIR / f"{name}.png"
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor=BG)
    if also_pdf:
        pdf_path = FIG_DIR / f"{name}.pdf"
        fig.savefig(pdf_path, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"Wrote {png_path}" + (f" and {pdf_path.name}" if also_pdf else ""))
