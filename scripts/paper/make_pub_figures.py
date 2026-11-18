#!/usr/bin/env python
"""Publication figures for Paper 1 ("Place or Placeholder?").

Reads ONLY the results-kit tables (docs/results/tables/*.csv) and writes

    docs/results/figures/pub/Fig1..Fig4.{png,pdf}
    docs/results/figures/pub/FigS1..FigS3.{png,pdf}
    docs/results/figures/pub/CAPTIONS.md

Rerun after the kit is regenerated (no other inputs, no compute):

    source env.sh; nice -n 19 python scripts/paper/make_pub_figures.py

Style: no in-image titles (captions carry them), sans-serif 8 pt at print size,
6.5 in wide, 300 dpi PNG + vector PDF (TrueType embedded), one colour per country
(colour-blind-safe categorical slots 1-4), hairline axes, direct labels.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle, RegularPolygon  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
TAB = ROOT / "docs/results/tables"
OUT = ROOT / "docs/results/figures/pub"

# ----------------------------------------------------------------------------- style
INK = "#0b0b0b"        # primary ink
INK2 = "#52514e"       # secondary ink
MUTED = "#898781"      # axis / muted labels
GRID = "#e1e0d9"       # hairline grid
BAND = "#ecebe6"       # equivalence band fill
LIGHT = "#d9d8d2"      # training hexes / neutral fills
BOXFILL = "#f4f3f0"
COUNTRY_ORDER = ["brazil", "colombia", "peru", "taiwan"]
# categorical slots 1-4 of the validated palette (adjacent CVD dE >= 9.1 on white)
COUNTRY_COLOR = {"brazil": "#2a78d6", "colombia": "#eb6834", "peru": "#1baf7a", "taiwan": "#eda100"}
COUNTRY_NAME = {"brazil": "Brazil", "colombia": "Colombia", "peru": "Peru", "taiwan": "Taiwan"}
CODE_COUNTRY = {"BR": "brazil", "CO": "colombia", "PE": "peru", "TW": "taiwan"}
SPLIT_ORDER = ["S1", "S2", "S3", "S4", "S5"]
SPLIT_NAME = {"S1": "New years", "S2": "Held-out states", "S3": "Held-out blocks",
              "S4": "Held-out districts", "S5": "Held-out country"}
SPLIT_LONG = {"S1": "new years", "S2": "held-out states", "S3": "held-out buffered blocks",
              "S4": "held-out random districts", "S5": "held-out country"}
SPLIT_MARKER = {"S1": "o", "S2": "s", "S3": "^", "S4": "D", "S5": "v"}
CONTROL_NAME = {"C1": "pre-2018 case average", "C2": "coordinates", "C3": "shuffled embedding",
                "C4": "random smooth fields", "C4s": "short-range random fields",
                "C5": "2023 embedding snapshot", "C6": "district ID"}
W_FULL = 6.5
MINUS = "−"


def setup_style() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
        "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
        "text.color": INK, "axes.labelcolor": INK,
        "axes.edgecolor": MUTED, "axes.linewidth": 0.6,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5,
        "xtick.major.pad": 2.0, "ytick.major.pad": 2.0,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.unicode_minus": True,
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "savefig.dpi": 300, "figure.dpi": 100,
        "hatch.linewidth": 0.5, "hatch.color": "#c9524f",
        "legend.frameon": False,
    })


# ----------------------------------------------------------------------------- helpers
def read(name: str) -> pd.DataFrame:
    return pd.read_csv(TAB / f"{name}.csv")


def fnum(v: float, signed: bool = True, dec: int | None = None) -> str:
    """2 decimals (1 when |v| >= 10). A signed estimate that rounds to zero prints as 0.00 (no sign);
    an interval bound keeps its sign (e.g. -0.00) so it shows which side of zero it lies on."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "\u2013"
    d = dec if dec is not None else (1 if abs(v) >= 10 else 2)
    if signed:
        s = f"{0:.{d}f}" if round(v, d) == 0 else f"{v:+.{d}f}"
    else:
        s = f"{v:.{d}f}"
    return s.replace("-", MINUS)


def fci(est: float, lo: float, hi: float) -> str:
    if max(abs(est), abs(lo), abs(hi)) >= 10:
        return f"{fnum(est, True, 1)} ({fnum(lo, False, 1)}, {fnum(hi, False, 1)})"
    return f"{fnum(est)} ({fnum(lo, False)}, {fnum(hi, False)})"


def fp(p: float) -> str:
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return "–"
    if p < 0.001:
        return "<0.001"
    if p < 0.1:
        return f"{p:.3f}"
    return f"{p:.2f}"


def axes_in(fig, x0, y0, w, h):
    """Axes placed in inches from the bottom-left corner."""
    W, H = fig.get_size_inches()
    return fig.add_axes([x0 / W, y0 / H, w / W, h / H])


def ftext(fig, x, y, s, **kw):
    """Figure text placed in inches."""
    W, H = fig.get_size_inches()
    kw.setdefault("color", INK)
    return fig.text(x / W, y / H, s, **kw)


def save(fig, name: str) -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext in ("png", "pdf"):
        p = OUT / f"{name}.{ext}"
        fig.savefig(p, dpi=300, facecolor="white", metadata={"Creator": "make_pub_figures.py"})
        paths.append(p)
    plt.close(fig)
    return paths


def draw_interval(ax, y, est, lo, hi, color, filled=True, xlim=None, marker="o", ms=4.6, lw=1.1,
                  label_off=True):
    """Point + 95% CI; parts outside xlim are clipped with an arrowhead at the edge.
    An off-scale point is drawn as an edge arrow with its value printed beside it."""
    x0, x1 = xlim if xlim is not None else ax.get_xlim()
    if not (np.isfinite(lo) and np.isfinite(hi)):
        lo = hi = est
    lo_c, hi_c = max(lo, x0), min(hi, x1)
    if hi_c > lo_c:
        ax.plot([lo_c, hi_c], [y, y], color=color, lw=lw, solid_capstyle="butt", zorder=3)
    if lo < x0 and hi > x0:
        ax.plot(x0, y, marker="<", ms=3.6, color=color, mew=0, zorder=4, clip_on=False)
    if hi > x1 and lo < x1:
        ax.plot(x1, y, marker=">", ms=3.6, color=color, mew=0, zorder=4, clip_on=False)
    if x0 <= est <= x1:
        ax.plot(est, y, marker=marker, ms=ms, mfc=color if filled else "white", mec=color, mew=1.0,
                zorder=5, clip_on=False)
        return
    # off-scale estimate
    edge = x0 if est < x0 else x1
    ax.plot(edge, y, marker="<" if est < x0 else ">", ms=5.5, color=color, mew=0, zorder=5, clip_on=False)
    if label_off:
        ax.annotate(fnum(est), (edge, y),
                    xytext=(6 if est < x0 else -6, 0), textcoords="offset points",
                    ha="left" if est < x0 else "right", va="center", fontsize=7, color=INK2, zorder=6,
                    bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none"))


def x_cues(ax, left="← embeddings hurt", right="embeddings help →", dy=-15, size=7.5):
    ax.annotate(left, (0, 0), xycoords="axes fraction", xytext=(0, dy), textcoords="offset points",
                ha="left", va="top", fontsize=size, color=MUTED)
    ax.annotate(right, (1, 0), xycoords="axes fraction", xytext=(0, dy), textcoords="offset points",
                ha="right", va="top", fontsize=size, color=MUTED)


def break_marks(ax, side: str):
    """A slanted stroke on the bottom spine marking an axis break (fixed size in points)."""
    x = 0 if side == "left" else 1
    ax.plot([x], [0], transform=ax.transAxes, marker=[(-0.5, -1), (0.5, 1)], ms=7, mew=0.8,
            color=MUTED, clip_on=False, zorder=6)


def sig_key(fig, x, y, filled_text, open_text, color=INK2):
    """Marker key drawn in inches (filled vs open circle)."""
    ax = axes_in(fig, x, y - 0.09, 0.12, 0.18)
    ax.set_axis_off()
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.plot(0.5, 0.5, "o", ms=4.6, mfc=color, mec=color, mew=1.0, clip_on=False)
    ftext(fig, x + 0.13, y, filled_text, va="center", fontsize=7.5, color=INK2)
    x2 = x + 0.13 + 0.058 * len(filled_text) + 0.18
    ax2 = axes_in(fig, x2, y - 0.09, 0.12, 0.18)
    ax2.set_axis_off(); ax2.set_xlim(0, 1); ax2.set_ylim(0, 1)
    ax2.plot(0.5, 0.5, "o", ms=4.6, mfc="white", mec=color, mew=1.0, clip_on=False)
    ftext(fig, x2 + 0.13, y, open_text, va="center", fontsize=7.5, color=INK2)


# ----------------------------------------------------------------------------- primary-family rows
def family_rows(t1: pd.DataFrame, gap=0.4):
    rows, y = [], 0.0
    for c in COUNTRY_ORDER:
        sub = t1[t1.country == c].copy()
        if sub.empty:
            continue
        sub["_o"] = sub.split.map(SPLIT_ORDER.index)
        sub = sub.sort_values("_o")
        rows.append(dict(kind="header", country=c, y=y)); y -= 1
        for _, r in sub.iterrows():
            rows.append(dict(kind="cell", country=c, split=r["split"], cell=r["cell"], y=y, rec=r)); y -= 1
        y -= gap
    return rows, y + gap + 1  # last used y


def is_available(r) -> bool:
    return str(r.get("status", "")) == "available" and np.isfinite(r.get("pct_of_WIS_ref", np.nan))


def draw_row_labels(ax, rows, x_country=0.02, x_cell=0.10):
    ax.set_axis_off()
    for r in rows:
        if r["kind"] == "header":
            ax.plot(x_country + 0.012, r["y"], "o", ms=5.0, color=COUNTRY_COLOR[r["country"]],
                    transform=ax.get_yaxis_transform(), clip_on=False)
            ax.text(x_country + 0.05, r["y"], COUNTRY_NAME[r["country"]], fontweight="bold",
                    va="center", ha="left", fontsize=8, transform=ax.get_yaxis_transform())
        else:
            ax.text(x_cell, r["y"], f"{r['split']}", va="center", ha="left", fontsize=8, color=INK2,
                    transform=ax.get_yaxis_transform())
            ax.text(x_cell + 0.15, r["y"], SPLIT_NAME[r["split"]], va="center", ha="left", fontsize=8,
                    transform=ax.get_yaxis_transform())


# ============================================================================= Fig 1
HEX_TRAIN, HEX_TEST = LIGHT, "#4a4946"


def hex_center(q, r, R):
    return (R * math.sqrt(3) * (q + r / 2.0), -R * 1.5 * r)


def hex_disc(n):
    return [(q, r) for q in range(-n, n + 1) for r in range(-n, n + 1) if max(abs(q), abs(r), abs(q + r)) <= n]


def hex_blob(n, drop, seed):
    cells = hex_disc(n)
    rim = [c for c in cells if max(abs(c[0]), abs(c[1]), abs(c[0] + c[1])) == n]
    rng = np.random.default_rng(seed)
    gone = set(map(tuple, rng.choice(rim, size=min(drop, len(rim)), replace=False))) if drop else set()
    return [c for c in cells if c not in gone]


def draw_hexes(ax, cells, x0, y0, R, kind_of, group_of=None, gap=0.90):
    """kind_of(cell) -> 'train'|'test'|'drop'. group_of draws thick borders between groups."""
    centers = {}
    for c in cells:
        cx, cy = hex_center(*c, R)
        cx, cy = cx + x0, cy + y0
        centers[c] = (cx, cy)
        k = kind_of(c)
        if k == "drop":
            ax.add_patch(RegularPolygon((cx, cy), 6, radius=R * gap, orientation=0, facecolor="white",
                                        edgecolor=MUTED, lw=0.6, linestyle=(0, (1.6, 1.2)), zorder=2))
        else:
            ax.add_patch(RegularPolygon((cx, cy), 6, radius=R * gap, orientation=0, lw=0,
                                        facecolor=HEX_TEST if k == "test" else HEX_TRAIN, zorder=2))
    if group_of is not None:
        dirs = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
        cellset = set(cells)
        for c in cells:
            cx, cy = centers[c]
            for dq, dr in dirs:
                nb = (c[0] + dq, c[1] + dr)
                if nb in cellset and group_of(nb) == group_of(c):
                    continue
                nx, ny = hex_center(*nb, R)
                nx, ny = nx + x0, ny + y0
                mx, my = (cx + nx) / 2, (cy + ny) / 2
                vx, vy = (nx - cx), (ny - cy)
                L = math.hypot(vx, vy)
                px, py = -vy / L * R / 2, vx / L * R / 2
                ax.plot([mx - px, mx + px], [my - py, my + py], color=INK2, lw=0.9,
                        solid_capstyle="round", zorder=3)
    return centers


def blob_extent(cells, R):
    xs = [hex_center(*c, R)[0] for c in cells]
    ys = [hex_center(*c, R)[1] for c in cells]
    return min(xs) - R, max(xs) + R, min(ys) - R, max(ys) + R


def rbox(ax, x, y, w, h, fc=BOXFILL, ec="#c3c2b7", lw=0.6, z=2):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.035", fc=fc, ec=ec, lw=lw, zorder=z)
    ax.add_patch(p)
    return p


def arrow(ax, p0, p1, lw=0.8, color=INK2, ms=7, z=4, style="-|>", shrinkA=0, shrinkB=0):
    a = FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=ms, lw=lw, color=color, zorder=z,
                        shrinkA=shrinkA, shrinkB=shrinkB, joinstyle="miter", capstyle="butt")
    ax.add_patch(a)
    return a


def fig1():
    W, H = W_FULL, 7.45
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.set_axis_off()
    T = dict(fontsize=8, color=INK, zorder=6)

    def head(x, y, letter, title):
        ax.text(x, y, letter, fontsize=9.5, fontweight="bold", va="baseline", ha="left", color=INK)
        ax.text(x + 0.2, y, title, fontsize=8.5, fontweight="bold", va="baseline", ha="left", color=INK)

    # ------------------------------------------------------------- Panel A: what is compared
    top = H - 0.22
    head(0.05, top, "A", "What is compared")
    bw, bh, gap, bx = 1.32, 0.42, 0.10, 0.06
    y_top_ladder = top - 0.30
    y_bottom = y_top_ladder - (5 * bh + 4 * gap)
    ladder = [("L0", "seasonal naive"), ("L1", "+ case history"), ("L2", "+ weekly climate"),
              ("L3", "+ remote sensing\nand population"), ("L4", "+ AlphaEarth\nembedding")]
    centers = {}
    for i, (code, desc) in enumerate(ladder):
        y = y_bottom + i * (bh + gap)
        emph = code in ("L3", "L4")
        rbox(ax, bx, y, bw, bh, fc=BOXFILL, ec=INK2 if emph else "#c3c2b7", lw=0.8 if emph else 0.6)
        ax.text(bx + 0.08, y + bh / 2, code, fontweight="bold", va="center", ha="left", **T)
        ax.text(bx + 0.33, y + bh / 2, desc, va="center", ha="left", fontsize=7.5, color=INK, zorder=6,
                linespacing=1.05)
        centers[code] = y + bh / 2
        if i < 4:
            arrow(ax, (bx + 0.17, y + bh), (bx + 0.17, y + bh + gap), lw=0.6, ms=5, color=MUTED)
    cw, ch = 0.64, 0.40
    gx0, gx1 = 2.10, 3.20
    yT = centers["L3"]
    yB = yT - ch - 0.66
    for lab, (cx, cy) in {"L3": (gx0, yT), "L3 + C*": (gx1, yT), "L4": (gx0, yB), "L4 + C*": (gx1, yB)}.items():
        rbox(ax, cx, cy - ch / 2, cw, ch, fc="white", ec=INK2, lw=0.8)
        ax.text(cx + cw / 2, cy, lab, ha="center", va="center", fontweight="bold", **T)
    ax.text(gx0 + cw / 2, yT + ch / 2 + 0.06, "no location\ncontrol", ha="center", va="bottom",
            fontsize=7.5, color=INK2, linespacing=1.05)
    ax.text(gx1 + cw / 2, yT + ch / 2 + 0.06, "with location\ncontrol C*", ha="center", va="bottom",
            fontsize=7.5, color=INK2, linespacing=1.05)
    ax.text(gx0 - 0.08, yT + 0.06, "without\nembedding", ha="right", va="bottom", fontsize=7.5, color=INK2,
            linespacing=1.05)
    ax.text(gx0 - 0.08, yB, "with\nembedding", ha="right", va="center", fontsize=7.5, color=INK2,
            linespacing=1.05)
    arrow(ax, (bx + bw + 0.03, yT), (gx0 - 0.03, yT), lw=0.8, color=MUTED, ms=6)
    # the three gains
    arrow(ax, (gx0 + cw / 2, yT - ch / 2 - 0.03), (gx0 + cw / 2, yB + ch / 2 + 0.03), lw=0.9, ms=7)
    ax.text(gx0 + cw / 2 - 0.07, (yT + yB) / 2, "embedding\ngain", ha="right", va="center", fontsize=7.5,
            color=INK, linespacing=1.05)
    arrow(ax, (gx0 + cw + 0.03, yT), (gx1 - 0.03, yT), lw=0.9, ms=7)
    ax.text((gx0 + cw + gx1) / 2, yT - 0.05, "identity\ngain", ha="center", va="top", fontsize=7.5,
            color=INK, linespacing=1.05)
    arrow(ax, (gx1 + cw / 2, yT - ch / 2 - 0.03), (gx1 + cw / 2, yB + ch / 2 + 0.03), lw=2.0, ms=10,
          color=INK)
    ax.text(gx1 + cw / 2 - 0.08, (yT + yB) / 2 - 0.05, "excess gain\n(primary)", ha="right", va="center",
            fontsize=7.5, color=INK, fontweight="bold", linespacing=1.05)
    legend = ("C* chosen at the 2019 origin from:\nC1 historical risk, C2 coordinates,\n"
              "C3 shuffled embedding, C4/C4s random\nsmooth fields, C5 2023 snapshot")
    ax.text(1.52, yB - ch / 2 - 0.14, legend, fontsize=7, color=INK2, va="top", ha="left", linespacing=1.2)

    # ------------------------------------------------------------- Panel B: where models are tested
    bx0 = 4.05
    head(bx0 - 0.05, top, "B", "Where models are tested")
    Rb = 0.030
    ly = top - 0.25
    lx = bx0
    for kind, lab in (("train", "training"), ("test", "test"), ("drop", "dropped")):
        if kind == "drop":
            ax.add_patch(RegularPolygon((lx + 0.04, ly), 6, radius=0.045, orientation=0, facecolor="white",
                                        edgecolor=INK2, lw=0.6, linestyle=(0, (1.5, 1.0))))
        else:
            ax.add_patch(RegularPolygon((lx + 0.04, ly), 6, radius=0.045, orientation=0, lw=0,
                                        facecolor=HEX_TEST if kind == "test" else HEX_TRAIN))
        t = ax.text(lx + 0.11, ly, lab, fontsize=7, color=INK2, va="center", ha="left")
        lx += 0.11 + 0.052 * len(lab) + 0.17
    sx, tx = bx0 + 0.02, bx0 + 1.06
    pitch = 0.53
    steps = [0.0, 0.50, 0.50, 0.72, 0.50]          # S3 carries a two-line note, so S4 sits lower
    rows_y = list(ly - 0.40 - np.cumsum(steps))
    blob = hex_blob(3, 7, seed=3)   # 30 hexagons

    def place(cells, x_left, y_mid):
        x_min, x_max, y_min, y_max = blob_extent(cells, Rb)
        return x_left - x_min, y_mid - (y_min + y_max) / 2, x_max - x_min

    def label(y, code, name, extra=None):
        ax.text(tx, y + 0.10, code, fontsize=8, fontweight="bold", va="top", ha="left")
        ax.text(tx + 0.22, y + 0.10, name, fontsize=7.5, va="top", ha="left", color=INK, linespacing=1.1)
        if extra:
            nl = name.count("\n") + 1
            ax.text(tx + 0.22, y + 0.10 - 0.135 * nl - 0.02, extra, fontsize=7, va="top", ha="left",
                    color=INK2, linespacing=1.1)

    # S1: same cluster, training years then test year
    y = rows_y[0]
    xo, yo, wbl = place(blob, sx, y + 0.05)
    draw_hexes(ax, blob, xo, yo, Rb, lambda c: "train")
    ax.text(sx + wbl / 2, y - 0.19, "2018 to Y−1", fontsize=6.8, color=INK2, ha="center", va="center")
    arrow(ax, (sx + wbl + 0.02, y + 0.05), (sx + wbl + 0.12, y + 0.05), lw=0.7, ms=5, color=MUTED)
    xo2, yo2, _ = place(blob, sx + wbl + 0.14, y + 0.05)
    draw_hexes(ax, blob, xo2, yo2, Rb, lambda c: "test")
    ax.text(sx + wbl + 0.14 + wbl / 2, y - 0.19, "year Y", fontsize=6.8, color=INK2, ha="center", va="center")
    label(y, "S1", "new years")

    # S2: five state groups, one whole group dark
    def state_of(c):
        if c == (0, 0):
            return 0
        cx, cy = hex_center(*c, 1.0)
        return int(((math.atan2(cy, cx) + math.pi) / (2 * math.pi)) * 5 + 0.3) % 5

    y = rows_y[1]
    xo, yo, wbl = place(blob, sx + 0.25, y)
    draw_hexes(ax, blob, xo, yo, Rb, lambda c: "test" if state_of(c) == 2 else "train", group_of=state_of)
    label(y, "S2", "held-out states")
    # S3: compact dark block, ring of dropped buffer hexagons
    y = rows_y[2]
    disc = hex_disc(3)
    ring = lambda c: max(abs(c[0]), abs(c[1]), abs(c[0] + c[1]))  # noqa: E731
    xo, yo, wbl = place(disc, sx + 0.25, y)
    draw_hexes(ax, disc, xo, yo, Rb, lambda c: "test" if ring(c) <= 1 else ("drop" if ring(c) == 2 else "train"))
    label(y + 0.06, "S3", "held-out buffered\nblocks", "buffer D (BR 225 km,\nCO 130 km)")
    # S4: about 1 in 5 districts, scattered
    y = rows_y[3]
    rng = np.random.default_rng(11)
    pick = set(map(tuple, rng.choice(blob, size=round(len(blob) / 5), replace=False)))
    xo, yo, wbl = place(blob, sx + 0.25, y)
    draw_hexes(ax, blob, xo, yo, Rb, lambda c: "test" if c in pick else "train")
    label(y, "S4", "held-out random\ndistricts")
    # S5: four country clusters, one dark
    y = rows_y[4]
    shapes = {"BR": hex_blob(2, 2, seed=5), "CO": hex_blob(1, 0, seed=1) + [(2, -1), (1, 1)],
              "PE": hex_blob(1, 1, seed=2), "TW": [(0, 0), (0, 1), (1, 0)]}
    x = sx
    for k, cells_k in shapes.items():
        xo, yo, wk = place(cells_k, x, y + 0.05)
        draw_hexes(ax, cells_k, xo, yo, Rb, lambda c, k=k: "test" if k == "PE" else "train")
        ax.text(x + wk / 2, y - 0.19, k, fontsize=6.8, color=INK2, ha="center", va="center")
        x += wk + 0.07
    label(y, "S5", "held-out country")
    ax.text(bx0 - 0.03, rows_y[4] - 0.32,
            "S2–S4 in Brazil and Colombia; S1 and S5 in\nall four countries. Held-out districts keep\n"
            "their own lagged cases.", fontsize=7, color=INK2, va="top", ha="left", linespacing=1.15)

    # ------------------------------------------------------------- Panel C: information timing
    cTop = top - 3.70
    head(0.05, cTop, "C", "Information timing for one forecast")
    w0, w1 = -12, 14
    xa, xb = 1.98, 6.40
    s = (xb - xa) / (w1 - w0)

    def X(w):                          # w = weeks relative to the epidemiological-year boundary
        return xa + (w - w0) * s

    o = 6                              # origin: end of week 6 of year Y (February)
    # top band: yearly inputs (far left) and the year inset (right)
    bt, bhgt = cTop - 0.15, 0.56
    rbox(ax, 0.06, bt - bhgt, 3.10, bhgt, fc=BOXFILL, ec="#c3c2b7")
    ax.text(0.14, bt - 0.09, "Yearly inputs from year y − 1", fontsize=7.5, fontweight="bold",
            va="top", ha="left")
    ax.text(0.14, bt - 0.26, "AlphaEarth, population, night lights, built-up share;\n"
            "y = the target's epidemiological year", fontsize=7, color=INK2, va="top", ha="left",
            linespacing=1.12)
    years = ["2018", "2019", "2020", "2021", "…", "last"]
    ix0, iw, iy = 3.50, 0.465, bt - 0.29
    for i, yr in enumerate(years):
        if yr != "…":
            fc = HEX_TRAIN if yr == "2018" else ("#b4b3ad" if yr == "2019" else "white")
            ax.add_patch(Rectangle((ix0 + i * iw, iy - 0.085), iw - 0.03, 0.17, fc=fc, ec="#c3c2b7", lw=0.6))
        ax.text(ix0 + i * iw + (iw - 0.03) / 2, iy, yr, fontsize=7, ha="center", va="center", color=INK)
    ax.plot([ix0, ix0 + 2 * iw - 0.03], [iy + 0.115, iy + 0.115], color=INK2, lw=0.6)
    ax.text(ix0, iy + 0.14, "2019: tuning and C* selection (train 2018, validate 2019)", fontsize=7,
            color=INK2, ha="left", va="bottom")
    ax.plot([ix0 + 2 * iw, ix0 + 6 * iw - 0.03], [iy - 0.115, iy - 0.115], color=INK2, lw=0.6)
    ax.text(ix0 + 6 * iw - 0.03, iy - 0.14, "2020 to last: one refit per test year", fontsize=7,
            color=INK2, ha="right", va="top")

    yTopLines = cTop - 0.86
    r1, r2, r3 = cTop - 1.24, cTop - 1.50, cTop - 1.80
    yAx = cTop - 2.34
    yT4 = yAx + 0.12
    bar_h = 0.17
    # vertical reference lines
    ax.plot([X(0), X(0)], [yAx - 0.04, yTopLines], color=MUTED, lw=0.8, zorder=1)
    ax.text(X(0) - 0.05, yTopLines, "epidemiological\nyear boundary", fontsize=7, color=INK2,
            ha="right", va="top", linespacing=1.05)
    ax.plot([X(o), X(o)], [yAx - 0.04, yTopLines], color=INK, lw=1.1, zorder=5)
    ax.text(X(o) + 0.05, yTopLines, "forecast origin\n(end of week o)", fontsize=7, color=INK,
            ha="left", va="top", linespacing=1.05)
    # inputs that end at the origin (labels inside the bars)
    for yy, lab in ((r1, "case history, weeks o−11 to o"), (r2, "climate, weeks o−11 to o")):
        ax.add_patch(Rectangle((X(o - 12), yy - bar_h / 2), X(o) - X(o - 12), bar_h, fc="#cfcec8", lw=0,
                               zorder=3))
        ax.text(X(o - 12) + 0.06, yy, lab, fontsize=7.5, ha="left", va="center", color=INK, zorder=4)
    rs0, rs1 = -8.7, 4.4               # 1 Nov to 31 Jan for an origin in February
    ax.add_patch(Rectangle((X(rs0), r3 - bar_h / 2), X(rs1) - X(rs0), bar_h, fc="#e2e1dc", lw=0, zorder=3))
    ax.text(X(rs0) - 0.06, r3, "remote sensing: last 3 complete\nmonths before the month of o",
            fontsize=7.5, ha="right", va="center", color=INK, linespacing=1.05)
    # same week +/- 1 in the previous three years (left of the axis break)
    for i, xx in enumerate((0.32, 0.82, 1.32)):
        ax.add_patch(Rectangle((xx - 0.07, r1 - bar_h / 2), 0.14, bar_h, fc="#cfcec8", lw=0, zorder=3))
        ax.text(xx, r1 - 0.13, f"{3 - i} y back", fontsize=6.8, color=INK2, ha="center", va="top")
    ax.text(0.12, r1 + 0.13, "same week ± 1, previous 3 years", fontsize=7, color=INK2, ha="left",
            va="bottom")
    # target weeks of year Y: first h weeks dropped, the rest primary
    ax.add_patch(Rectangle((X(0), yT4 - 0.085), X(4) - X(0), 0.17, fc="#f6d4d3", ec="none", hatch="/////",
                           zorder=1))
    ax.add_patch(Rectangle((X(4), yT4 - 0.085), X(w1) - X(4), 0.17, fc="#d3ead3", ec="none", zorder=1))
    ax.plot(X(o + 2.5), yT4, marker="D", ms=6.5, color=INK, mec="white", mew=0.8, zorder=6)
    yb = yT4 + 0.17
    ax.plot([X(o), X(o), X(o + 4), X(o + 4)], [yb - 0.035, yb, yb, yb - 0.035], color=INK, lw=0.7, zorder=5)
    ax.text(X(o) + 0.05, yb + 0.03, "target t = o + h\nh = 1 to 4 weeks", fontsize=7, color=INK,
            ha="left", va="bottom", linespacing=1.1)
    # time axis with a break to the earlier years
    ax.plot([X(w0), X(w1)], [yAx, yAx], color=INK2, lw=0.7, zorder=2)
    ax.plot([0.12, 1.62], [yAx, yAx], color=MUTED, lw=0.7, linestyle=(0, (1.5, 1.5)), zorder=2)
    for xx in (1.74, 1.82):
        ax.plot([xx - 0.03, xx + 0.03], [yAx - 0.05, yAx + 0.05], color=INK2, lw=0.7)
    ticks = [(wk - 52 - 0.5, wk) for wk in (41, 45, 49)] + [(wk - 0.5, wk) for wk in (1, 5, 9, 13)]
    for w, wk in ticks:
        ax.plot([X(w), X(w)], [yAx, yAx - 0.04], color=INK2, lw=0.6)
        ax.text(X(w), yAx - 0.07, str(wk), fontsize=7, color=INK2, ha="center", va="top")
    ax.text((X(w0) + X(0)) / 2, yAx - 0.22, "year Y − 1 (epidemiological weeks)", fontsize=7.5,
            ha="center", va="top")
    ax.text((X(0) + X(w1)) / 2, yAx - 0.22, "year Y", fontsize=7.5, ha="center", va="top")
    # training targets
    yTr = yAx - 0.53
    ax.add_patch(Rectangle((0.12, yTr - 0.085), X(0) - 0.12, 0.17, fc=HEX_TRAIN, lw=0, zorder=2))
    ax.text(0.20, yTr, "training targets: 2018 to the last week of Y − 1", fontsize=7.5, ha="left",
            va="center", zorder=4)
    # key for the shading
    ky = yTr - 0.28
    ax.add_patch(Rectangle((0.12, ky - 0.065), 0.26, 0.13, fc="#f6d4d3", ec="none", hatch="/////"))
    ax.text(0.45, ky, "dropped from primary scoring: origin in Y − 1 (yearly inputs or training labels "
            "after the origin)", fontsize=7, color=INK2, va="center", ha="left")
    ky2 = ky - 0.19
    ax.add_patch(Rectangle((0.12, ky2 - 0.065), 0.26, 0.13, fc="#d3ead3", ec="none"))
    ax.text(0.45, ky2, "origin-year rows (primary)", fontsize=7, color=INK2, va="center", ha="left")
    return fig


# ============================================================================= Fig 2
def fig2(t1: pd.DataFrame):
    rows, ylast = family_rows(t1)
    pitch = 0.19
    n_units = -ylast + 1.0
    top_m, bot_m = 0.40, 0.78
    H = n_units * pitch + top_m + bot_m
    fig = plt.figure(figsize=(W_FULL, H))
    yl = (ylast - 0.6, 0.6)
    ah = (yl[1] - yl[0]) * pitch
    ay = bot_m
    cells = [r for r in rows if r["kind"] == "cell"]
    avail = [r for r in cells if is_available(r["rec"])]
    margin = 1.0
    # outliers go to a broken-axis panel on the left (negative) side
    out = [r for r in avail if abs(r["rec"]["pct_of_WIS_ref"]) > 5]
    inn = [r for r in avail if abs(r["rec"]["pct_of_WIS_ref"]) <= 5]
    lo_in = min([r["rec"]["lo95_pct"] for r in inn] + [-margin])
    hi_in = max([r["rec"]["hi95_pct"] for r in inn] + [margin])
    xm = (math.floor((lo_in - 0.15) * 2) / 2, math.ceil((hi_in + 0.15) * 2) / 2)
    has_break = len(out) > 0
    x_lab, w_lab = 0.0, 1.50
    x_brk, w_brk = 1.55, 0.72
    x_main = (x_brk + w_brk + 0.12) if has_break else 1.62
    x_txt = 4.52
    w_main = x_txt - 0.16 - x_main
    axL = axes_in(fig, x_lab, ay, w_lab, ah); axL.set_ylim(*yl); axL.set_xlim(0, 1)
    draw_row_labels(axL, rows, x_country=0.03, x_cell=0.10)
    axM = axes_in(fig, x_main, ay, w_main, ah); axM.set_ylim(*yl); axM.set_xlim(*xm)
    axM.axvspan(-margin, margin, color=BAND, lw=0, zorder=0)
    axM.axvline(0, color=INK2, lw=0.7, zorder=1)
    axM.spines["left"].set_visible(False); axM.set_yticks([])
    axM.set_xticks([t for t in np.arange(math.ceil(xm[0]), math.floor(xm[1]) + 1, 1.0)
                    if not (has_break and t - xm[0] < 0.35)])
    axM.text(0, yl[1] + 0.25, f"±{margin:g}% equivalence margin", ha="center", va="bottom", fontsize=7,
             color=MUTED, transform=axM.transData, clip_on=False)
    axB = None
    if has_break:
        lo_o = min(r["rec"]["lo95_pct"] for r in out)
        hi_o = max(r["rec"]["hi95_pct"] for r in out)
        xb = (math.floor((lo_o - 1.5) / 5) * 5, math.ceil((hi_o + 1.5) / 5) * 5)
        axB = axes_in(fig, x_brk, ay, w_brk, ah); axB.set_ylim(*yl); axB.set_xlim(*xb)
        axB.spines["left"].set_visible(False); axB.set_yticks([])
        span = xb[1] - xb[0]
        step = 10 if span > 18 else 5
        tk = [t for t in np.arange(math.ceil(xb[0] / step) * step, xb[1] + 0.01, step)
              if xb[0] + 0.15 * span <= t <= xb[1] - 0.15 * span]
        axB.set_xticks(tk)
        break_marks(axB, "right"); break_marks(axM, "left")
    axT = axes_in(fig, x_txt, ay, W_FULL - x_txt - 0.04, ah); axT.set_ylim(*yl); axT.set_xlim(0, 1)
    axT.set_axis_off()
    axT.text(0.0, yl[1] + 0.25, "Change, % (95% CI)", fontsize=7.5, color=INK2, ha="left", va="bottom",
             fontweight="bold")
    axT.text(1.0, yl[1] + 0.25, "Holm p", fontsize=7.5, color=INK2, ha="right", va="bottom",
             fontweight="bold")
    for r in cells:
        rec, y, col = r["rec"], r["y"], COUNTRY_COLOR[r["country"]]
        if not is_available(rec):
            axM.text(xm[0] + 0.08, y, "results pending", fontsize=7.5, color=MUTED, style="italic",
                     va="center", ha="left")
            axT.text(0.0, y, "pending", fontsize=7.5, color=MUTED, style="italic", va="center", ha="left")
            continue
        est, lo, hi = rec["pct_of_WIS_ref"], rec["lo95_pct"], rec["hi95_pct"]
        sig = bool(rec["Holm_p"] < 0.05)
        target = axB if (has_break and r in out) else axM
        draw_interval(target, y, est, lo, hi, col, filled=sig, xlim=target.get_xlim())
        axT.text(0.0, y, fci(est, lo, hi), fontsize=7.5, color=INK, va="center", ha="left")
        axT.text(1.0, y, fp(rec["Holm_p"]), fontsize=7.5, color=INK if sig else INK2, va="center", ha="right",
                 fontweight="bold" if sig else "normal")
    if has_break:
        axB.annotate("\u2190 embeddings hurt", (0, 0), xycoords="axes fraction", xytext=(0, -13),
                     textcoords="offset points", ha="left", va="top", fontsize=7.5, color=MUTED)
        x_cues(axM, left="", dy=-13)
    else:
        x_cues(axM, dy=-13)
    xc = ((x_brk if has_break else x_main) + x_main + w_main) / 2
    ftext(fig, xc, ay - 0.42, "Reduction in forecast error from embeddings (%)", ha="center", va="top",
          fontsize=8)
    sig_key(fig, 0.06, ay - 0.62, "Holm-adjusted p < 0.05", "not significant")
    return fig, dict(n_avail=len(avail), n_cells=len(cells),
                     pending=[f"{COUNTRY_NAME[r['country']]} {r['split']}" for r in cells
                              if not is_available(r["rec"])],
                     outliers=[f"{COUNTRY_NAME[r['country']]} {r['split']}" for r in out])


# ============================================================================= Fig 3
STRATA = [("positive", "Weeks with cases"), ("recorded_zero", "Recorded zeros\n(Brazil 2020–21 only)"),
          ("zero_filled", "Zero-filled weeks")]


def fig3(t1: pd.DataFrame, t5: pd.DataFrame):
    rows, ylast = family_rows(t1)
    s = t5[t5.estimand == "G_excess"]
    pitch = 0.19
    top_m, bot_m = 0.52, 0.66
    H = (-ylast + 1.0 + 0.2) * pitch + top_m + bot_m
    fig = plt.figure(figsize=(W_FULL, H))
    yl = (ylast - 0.6, 0.6)
    ah = (yl[1] - yl[0]) * pitch
    ay = bot_m
    cells = [r for r in rows if r["kind"] == "cell"]
    vals = s[s.cell.isin([r["cell"] for r in cells]) & (s.row_share > 0)]
    inn = vals[vals.contrib_pct.abs() <= 5]
    est_max = max(inn.contrib_pct.abs().max(), 1.0)
    lo = max(inn.contrib_lo95_pct.min(), -2.5 * est_max)
    hi = min(inn.contrib_hi95_pct.max(), 2.5 * est_max)
    xl = (math.floor((lo - 0.1) * 2) / 2, math.ceil((hi + 0.1) * 2) / 2)
    x_lab, w_lab = 0.0, 1.50
    w_p, gap = 1.36, 0.13
    xs = [1.52 + i * (w_p + gap) for i in range(3)]
    axL = axes_in(fig, x_lab, ay, w_lab, ah); axL.set_ylim(*yl); axL.set_xlim(0, 1)
    draw_row_labels(axL, rows, x_country=0.03, x_cell=0.10)
    for (key, title), x0 in zip(STRATA, xs):
        ax = axes_in(fig, x0, ay, w_p, ah); ax.set_ylim(*yl); ax.set_xlim(*xl)
        ax.axvline(0, color=INK2, lw=0.7, zorder=1)
        ax.spines["left"].set_visible(False); ax.set_yticks([])
        ax.set_xticks(np.arange(math.ceil(xl[0]), math.floor(xl[1]) + 1, 1.0))
        ax.xaxis.grid(True, color=GRID, lw=0.5, zorder=0); ax.set_axisbelow(True)
        ax.text(0.5, 1.0, title, transform=ax.transAxes, ha="center", va="bottom", fontsize=8,
                fontweight="bold", linespacing=1.05)
        for r in cells:
            rec = vals[(vals.cell == r["cell"]) & (vals.stratum == key)]
            if not is_available(r["rec"]):
                if key == "positive":
                    ax.text(xl[0] + 0.08, r["y"], "results pending", fontsize=7.5, color=MUTED,
                            style="italic", va="center", ha="left")
                continue
            if rec.empty:
                continue
            q = rec.iloc[0]
            filled = bool(q.contrib_lo95_pct > 0 or q.contrib_hi95_pct < 0)
            draw_interval(ax, r["y"], q.contrib_pct, q.contrib_lo95_pct, q.contrib_hi95_pct,
                          COUNTRY_COLOR[r["country"]], filled=filled, xlim=xl)
        x_cues(ax, left="← hurt", right="help →", dy=-13, size=7)
    # total column
    xt = xs[-1] + w_p + 0.10
    axT = axes_in(fig, xt, ay, W_FULL - xt - 0.04, ah); axT.set_ylim(*yl); axT.set_xlim(0, 1)
    axT.set_axis_off()
    axT.text(1.0, yl[1] + 0.1, "Total", fontsize=8, fontweight="bold", ha="right", va="bottom")
    for r in cells:
        if not is_available(r["rec"]):
            axT.text(1.0, r["y"], "pending", fontsize=7.5, color=MUTED, style="italic", ha="right", va="center")
            continue
        tot = s[s.cell == r["cell"]].total_pct
        v = tot.iloc[0] if len(tot) else r["rec"]["pct_of_WIS_ref"]
        axT.text(1.0, r["y"], fnum(v), fontsize=7.5, ha="right", va="center")
    ftext(fig, (xs[0] + xs[-1] + w_p) / 2, ay - 0.36,
          "Contribution to the reduction in forecast error (percentage points)", ha="center", va="top")
    sig_key(fig, 0.06, ay - 0.52, "95% CI excludes 0", "includes 0")
    return fig, dict(xlim=xl)


# ============================================================================= Fig 4
def nohist_label(code: str, cstar: str) -> str:
    cn = CONTROL_NAME.get(cstar, cstar)
    return {"N3": "Base model (N3)",
            "N3+C1": "Base + pre-2018 case average (C1)",
            "N3+C*": f"Base + {cn} ({cstar})",
            "N4": "Base + embeddings (N4)",
            "N4+C*": f"Base + embeddings + {cn}"}.get(code, code)


def fig4(t6b: pd.DataFrame, t6c: pd.DataFrame, t4: pd.DataFrame):
    cells = [c for c in ("BR_S1_nohist", "BR_S2_nohist") if c in set(t6b.cell) | set(t6c.cell)]
    cstar = {}
    for c in cells:
        sel = t4[(t4.cell == c) & (t4.selected == True)]  # noqa: E712
        cstar[c] = sel.C_star.iloc[0] if len(sel) else (t4[t4.cell == c].C_star.dropna().iloc[0]
                                                          if t4[t4.cell == c].C_star.notna().any() else "C*")
    cs = cstar[cells[0]]
    color = COUNTRY_COLOR["brazil"]
    split_of = {c: c.split("_")[1] for c in cells}
    multi = len(cells) > 1
    offs = {c: (0.0 if not multi else (0.16 if i == 0 else -0.16)) for i, c in enumerate(cells)}
    ladder = ["N3", "N3+C1", "N3+C*", "N4", "N4+C*"]
    gains = [("G_id", f"{CONTROL_NAME.get(cs, cs).capitalize()} alone",
              "identity gain: N3 → N3 + C*"),
             ("G_emb", "Embeddings alone", "embedding gain: N3 → N4"),
             ("G_excess", f"Embeddings beyond {CONTROL_NAME.get(cs, cs)}",
              "excess gain: N3 + C* → N4 + C*")]
    pitch = 0.24 if not multi else 0.30
    hA = len(ladder) * pitch + 0.15
    hB = len(gains) * (pitch + 0.08) + 0.15
    bot, mid, topm = 0.62, 0.72, (0.22 if not multi else 0.40)
    H = bot + hB + mid + hA + topm
    fig = plt.figure(figsize=(W_FULL, H))
    x_lab, w_lab = 0.0, 2.25
    x_plot = 2.35
    w_plot = 2.75 if not multi else 2.45
    x_txt = x_plot + w_plot + 0.12
    # ---- A: ladder (mean WIS)
    yA = bot + hB + mid
    lab = axes_in(fig, x_lab, yA, w_lab, hA); lab.set_axis_off()
    axA = axes_in(fig, x_plot, yA, w_plot, hA)
    yl = (-len(ladder) + 0.4, 0.6)
    for a in (lab, axA):
        a.set_ylim(*yl)
    lab.set_xlim(0, 1)
    vals = []
    for i, code in enumerate(ladder):
        y = -i
        if code == "N3":
            lab.text(0.04, y + 0.13, nohist_label(code, cs), va="center", ha="left", fontsize=8)
            lab.text(0.04, y - 0.25, "climate, remote sensing, population", va="center", ha="left",
                     fontsize=7, color=INK2)
        else:
            lab.text(0.04, y, nohist_label(code, cs), va="center", ha="left", fontsize=8)
        for c in cells:
            row = t6c[(t6c.cell == c) & (t6c.label == code) & (t6c.horizon.astype(str) == "pooled")]
            if row.empty:
                continue
            v = float(row.wis_log.iloc[0]); vals.append(v)
            axA.plot(v, y + offs[c], marker=SPLIT_MARKER[split_of[c]], ms=5.5, color=color, mec="white",
                     mew=0.8, zorder=4)
            axA.annotate(f"{v:.3f}", (v, y + offs[c]), xytext=(6, 0), textcoords="offset points",
                         va="center", ha="left", fontsize=7, color=INK2)
    if vals:
        span = max(vals) - min(vals)
        axA.set_xlim(min(vals) - 0.12 * span - 0.0005, max(vals) + 0.22 * span + 0.0005)
    axA.spines["left"].set_visible(False); axA.set_yticks([])
    axA.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(4))
    axA.xaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%.3f"))
    axA.xaxis.grid(True, color=GRID, lw=0.5); axA.set_axisbelow(True)
    axA.set_xlabel("Forecast error (mean WIS on log cases; lower is better)", labelpad=3)
    ftext(fig, 0.05, yA + hA + 0.05, "A", fontsize=9.5, fontweight="bold", va="bottom")
    # ---- B: gains
    yB = bot
    labB = axes_in(fig, x_lab, yB, w_lab, hB); labB.set_axis_off(); labB.set_xlim(0, 1)
    axB = axes_in(fig, x_plot, yB, w_plot, hB)
    axT = axes_in(fig, x_txt, yB, W_FULL - x_txt - 0.04, hB); axT.set_axis_off(); axT.set_xlim(0, 1)
    gp = 1.25
    ylB = (-(len(gains) - 1) * gp - 0.6, 0.6)
    for a in (labB, axB, axT):
        a.set_ylim(*ylB)
    allv = []
    for i, (est, name, sub) in enumerate(gains):
        for c in cells:
            r = t6b[(t6b.cell == c) & (t6b.estimand == est) & (t6b.horizon.astype(str) == "pooled")]
            if len(r):
                allv += [float(r.lo95_pct.iloc[0]), float(r.hi95_pct.iloc[0])]
    lo, hi = min(allv + [-1.0]), max(allv + [1.0])
    xlB = (math.floor(lo - 0.3), math.ceil(hi + 0.3))
    axB.set_xlim(*xlB)
    axB.axvspan(-1, 1, color=BAND, lw=0, zorder=0)
    axB.axvline(0, color=INK2, lw=0.7, zorder=1)
    axB.spines["left"].set_visible(False); axB.set_yticks([])
    axB.set_xticks(np.arange(xlB[0], xlB[1] + 0.01, 1.0 if xlB[1] - xlB[0] <= 10 else 2.0))
    axB.text(0, ylB[1] + 0.1, "±1% margin", ha="center", va="bottom", fontsize=7, color=MUTED)
    axT.text(0.0, ylB[1] + 0.1, "% (95% CI)", fontsize=7.5, color=INK2, fontweight="bold", va="bottom")
    for i, (est, name, sub) in enumerate(gains):
        y = -i * gp
        labB.text(0.04, y + 0.17, name, va="center", ha="left", fontsize=8, fontweight="bold")
        labB.text(0.04, y - 0.25, sub, va="center", ha="left", fontsize=7, color=INK2)
        for c in cells:
            r = t6b[(t6b.cell == c) & (t6b.estimand == est) & (t6b.horizon.astype(str) == "pooled")]
            if r.empty:
                continue
            q = r.iloc[0]
            filled = bool(q.lo95_pct > 0 or q.hi95_pct < 0)
            draw_interval(axB, y + offs[c], q.pct_of_ref, q.lo95_pct, q.hi95_pct, color, filled=filled,
                          xlim=xlB, marker=SPLIT_MARKER[split_of[c]], ms=5.2)
            txt = fci(q.pct_of_ref, q.lo95_pct, q.hi95_pct)
            if multi:
                txt = f"{split_of[c]}  {txt}"
            axT.text(0.0, y + offs[c], txt, fontsize=7.5, va="center", ha="left")
    x_cues(axB, left="\u2190 worse", right="better \u2192", dy=-13)
    axB.set_xlabel("Reduction in forecast error (% of the base model's error)", labelpad=17)
    ftext(fig, 0.05, yB + hB + 0.05, "B", fontsize=9.5, fontweight="bold", va="bottom")
    if multi:
        fig.canvas.draw()
        rend = fig.canvas.get_renderer()
        x, yk = x_plot, H - 0.14
        for c in cells:
            k = axes_in(fig, x, yk - 0.06, 0.12, 0.12); k.set_axis_off(); k.set_xlim(0, 1); k.set_ylim(0, 1)
            k.plot(0.5, 0.5, SPLIT_MARKER[split_of[c]], ms=5, color=color, clip_on=False)
            t = ftext(fig, x + 0.14, yk, f"{split_of[c]} {SPLIT_LONG[split_of[c]]}", va="center", fontsize=7.5,
                      color=INK2)
            x += 0.14 + t.get_window_extent(rend).width / fig.dpi + 0.2
    take = ""
    head = "BR_S2_nohist" if "BR_S2_nohist" in cells else cells[0]

    def ci(est):
        r = t6b[(t6b.cell == head) & (t6b.estimand == est) & (t6b.horizon.astype(str) == "pooled")]
        return (float(r.lo95_pct.iloc[0]), float(r.hi95_pct.iloc[0])) if len(r) else (np.nan, np.nan)

    cn = CONTROL_NAME.get(cstar.get(head, cs), cs)
    (gl, gh), (el, eh) = ci("G_id"), ci("G_excess")
    where = f" (Brazil {split_of[head]})"
    if gl > 0:
        take += f" Adding {cn} alone improves forecasts{where}."
    if el <= 0 <= eh:
        take += f" The embeddings add no detectable skill once {cn} are in the model."
    elif eh < 0:
        take += f" Adding the embeddings on top of {cn} makes forecasts worse."
    elif el > 0:
        take += f" The embeddings improve forecasts beyond {cn}."
    return fig, dict(cells=cells, cstar=cstar, takeaway=take)


# ============================================================================= Fig S1
def figS1(s7: pd.DataFrame, s7b: pd.DataFrame):
    cells = [f"{k}_S5" for k in ("BR", "CO", "PE", "TW") if f"{k}_S5" in set(s7b.cell)]
    n = len(cells)
    H = 2.55
    fig = plt.figure(figsize=(W_FULL, H))
    left, right, gap = 0.70, 0.08, 0.42
    w = (W_FULL - left - right - gap * (n - 1)) / n
    for i, c in enumerate(cells):
        country = CODE_COUNTRY[c[:2]]
        col = COUNTRY_COLOR[country]
        d = s7b[s7b.cell == c].sort_values("bin")
        ax = axes_in(fig, left + i * (w + gap), 0.62, w, H - 1.22)
        x = d.cos_max_mean.values
        y = d.G_excess_pct_cell.values
        lo, hi = d.G_excess_lo95_pct_cell.values, d.G_excess_hi95_pct_cell.values
        ymin, ymax = min(lo.min(), 0), max(hi.max(), 0)
        pad = 0.12 * (ymax - ymin)
        ax.set_ylim(ymin - pad, ymax + pad)
        ax.axhline(0, color=INK2, lw=0.7, zorder=1)
        ax.yaxis.grid(True, color=GRID, lw=0.5); ax.set_axisbelow(True)
        ax.vlines(x, lo, hi, color=col, lw=1.1, zorder=3)
        ax.plot(x, y, color=col, lw=1.0, zorder=3, alpha=0.6)
        ax.plot(x, y, "o", ms=4.6, color=col, mec="white", mew=0.8, zorder=4)
        xr = x.max() - x.min()
        ax.set_xlim(x.min() - 0.12 * xr, x.max() + 0.12 * xr)
        ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(4))
        ax.xaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%.2f"))
        rr = s7[(s7.cell == c) & (s7.estimand == "G_excess") & (s7.distance == "cos_max")]
        ax.annotate(f"{COUNTRY_NAME[country]} held out", (0, 1), xycoords="axes fraction",
                    xytext=(0, 15), textcoords="offset points", fontsize=8, fontweight="bold",
                    ha="left", va="bottom")
        if len(rr):
            q = rr.iloc[0]
            ax.annotate(f"ρ = {fnum(q.spearman_rho, True, 2)}, n = {int(q.n_units):,}", (0, 1),
                        xycoords="axes fraction", xytext=(0, 4), textcoords="offset points", fontsize=7,
                        color=INK2, ha="left", va="bottom")
        if i == 0:
            ax.set_ylabel("Reduction in forecast error\nfrom embeddings (%)", labelpad=3)
    ftext(fig, (left + W_FULL - right) / 2, 0.18,
          "Embedding similarity to the closest training district (cosine; mean of each fifth of districts)",
          ha="center", va="bottom")
    return fig, dict(cells=cells)


# ============================================================================= Fig S2
CONTEXT_SHORT = {"COVID-era reporting": "COVID era", "Brazil record epidemic": "record epidemic",
                 "Peru record season": "record season",
                 "Taiwan 2021: no local cases (all-zero year)": "no local cases",
                 "Taiwan 2023 outbreak": "outbreak"}


def figS2(s8: pd.DataFrame):
    d = s8[s8.estimand == "G_excess"].copy()
    d["country"] = d.cell.str[:2].map(CODE_COUNTRY)
    d["split"] = d.cell.str[3:]
    countries = [c for c in COUNTRY_ORDER if c in set(d.country)]
    H = 4.85
    fig = plt.figure(figsize=(W_FULL, H))
    left, right, gapx, gapy = 0.62, 0.12, 0.45, 0.62
    w = (W_FULL - left - right - gapx) / 2
    h = (H - 0.62 - 0.55 - gapy) / 2
    pos = [(left, 0.62 + h + gapy), (left + w + gapx, 0.62 + h + gapy), (left, 0.62), (left + w + gapx, 0.62)]
    for i, c in enumerate(countries):
        sub = d[d.country == c]
        col = COUNTRY_COLOR[c]
        ax = axes_in(fig, *pos[i], w, h)
        years = sorted(sub.test_year.unique())
        splits = [s for s in SPLIT_ORDER if s in set(sub.split)]
        ns = len(splits)
        ests = sub.pct_of_ref.values
        # robust y-range: keep the estimates, clip very wide intervals
        lo_all, hi_all = sub.lo95_pct.values, sub.hi95_pct.values
        e_abs = np.nanmax(np.abs(ests))
        ylo = max(np.nanmin(lo_all), np.nanmin(ests) - 0.6 * e_abs) if e_abs > 10 else np.nanmin(lo_all)
        yhi = min(np.nanmax(hi_all), np.nanmax(ests) + 0.6 * e_abs) if e_abs > 10 else np.nanmax(hi_all)
        ylo, yhi = min(ylo, -1.2), max(yhi, 1.2)
        pad = 0.06 * (yhi - ylo)
        yl = (ylo - pad, yhi + pad)
        ax.set_ylim(*yl)
        ax.set_xlim(years[0] - 0.55, years[-1] + 0.55)
        ax.axhline(0, color=INK2, lw=0.7, zorder=1)
        covid = [yr for yr in years if any("COVID" in str(v) for v in sub[sub.test_year == yr].context.dropna())]
        for yr in covid:
            ax.axvspan(yr - 0.5, yr + 0.5, color="#f2f1ed", lw=0, zorder=0)
        if covid:
            ax.text(min(covid) - 0.45, 0.985, "COVID era", transform=ax.get_xaxis_transform(),
                    ha="left", va="top", fontsize=7, color=MUTED)
        for j, sp in enumerate(splits):
            dx = (j - (ns - 1) / 2) * min(0.14, 0.7 / max(ns, 1))
            ss = sub[sub.split == sp].sort_values("test_year")
            for _, q in ss.iterrows():
                xx = q.test_year + dx
                lo, hi = q.lo95_pct, q.hi95_pct
                lo_c, hi_c = max(lo, yl[0]), min(hi, yl[1])
                ax.plot([xx, xx], [lo_c, hi_c], color=col, lw=0.9, zorder=3, solid_capstyle="butt")
                if lo < yl[0]:
                    ax.plot(xx, yl[0], marker="v", ms=3.4, color=col, mew=0, zorder=4, clip_on=False)
                if hi > yl[1]:
                    ax.plot(xx, yl[1], marker="^", ms=3.4, color=col, mew=0, zorder=4, clip_on=False)
                filled = bool(lo > 0 or hi < 0)
                if yl[0] <= q.pct_of_ref <= yl[1]:
                    ax.plot(xx, q.pct_of_ref, marker=SPLIT_MARKER[sp], ms=4.2, mfc=col if filled else "white",
                            mec=col, mew=0.9, zorder=5)
        labels = []
        for yr in years:
            ctx = sub[sub.test_year == yr].context.dropna()
            short = CONTEXT_SHORT.get(str(ctx.iloc[0]), str(ctx.iloc[0])) if len(ctx) else ""
            short = "" if "COVID" in short else short
            labels.append(f"{yr}\n{short}" if short else f"{yr}")
        ax.set_xticks(years)
        ax.set_xticklabels(labels, fontsize=7.5, linespacing=1.15)
        ax.tick_params(axis="x", length=0)
        ax.yaxis.grid(True, color=GRID, lw=0.5); ax.set_axisbelow(True)
        ax.text(0.0, 1.03, COUNTRY_NAME[c], transform=ax.transAxes, fontsize=8, fontweight="bold",
                ha="left", va="bottom")
        if i % 2 == 0:
            ax.set_ylabel("Reduction in forecast error\nfrom embeddings (%)", labelpad=3)
    # split key, entries placed by measured width
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    x, yk = left, H - 0.17
    for sp in SPLIT_ORDER:
        if sp not in set(d.split):
            continue
        k = axes_in(fig, x, yk - 0.06, 0.12, 0.12); k.set_axis_off(); k.set_xlim(0, 1); k.set_ylim(0, 1)
        k.plot(0.5, 0.5, SPLIT_MARKER[sp], ms=4.6, mfc="white", mec=INK2, mew=0.9, clip_on=False)
        t = ftext(fig, x + 0.14, yk, f"{sp} {SPLIT_NAME[sp].lower()}", fontsize=7.5, color=INK2, va="center",
                  ha="left")
        x += 0.14 + t.get_window_extent(rend).width / fig.dpi + 0.16
    return fig, {}


# ============================================================================= Fig S3
LADDER_ROWS = [("L0", "L0 seasonal naive"), ("L1", "L1 case history (reference)"),
               ("L2", "L2 + weekly climate"), ("L3", "L3 + remote sensing, population"),
               ("L4", "L4 + embeddings"), ("L3+C*", "L3 + location control C*"),
               ("L4+C*", "L4 + location control C*")]


def figS3(t2: pd.DataFrame):
    cells = [f"{k}_S1" for k in ("BR", "CO", "PE", "TW") if f"{k}_S1" in set(t2.cell)]
    col_w = "WIS pooled h{1,4}"
    n = len(cells)
    pitch = 0.23
    H = len(LADDER_ROWS) * pitch + 1.05
    fig = plt.figure(figsize=(W_FULL, H))
    x_lab, w_lab = 0.0, 1.78
    gap = 0.24
    w = (W_FULL - w_lab - 0.10 - gap * (n - 1)) / n
    yl = (-len(LADDER_ROWS) + 0.4, 0.6)
    ah = (yl[1] - yl[0]) * pitch
    ay = 0.62
    lab = axes_in(fig, x_lab, ay, w_lab, ah); lab.set_axis_off(); lab.set_ylim(*yl); lab.set_xlim(0, 1)
    for i, (code, name) in enumerate(LADDER_ROWS):
        lab.text(0.03, -i, name, va="center", ha="left", fontsize=8)
    for j, c in enumerate(cells):
        country = CODE_COUNTRY[c[:2]]
        colr = COUNTRY_COLOR[country]
        sub = t2[t2.cell == c].set_index("label")[col_w]
        ref = sub.get("L1", np.nan)
        red = {k: 100 * (ref - sub[k]) / ref for k, _ in LADDER_ROWS if k in sub.index}
        core = [abs(v) for k, v in red.items() if k != "L0"]
        core_sorted = sorted(core)
        cap = max(1.0, 2.6 * (core_sorted[-2] if len(core_sorted) > 1 else core_sorted[-1]))
        inside = [v for k, v in red.items() if abs(v) <= cap]
        lo, hi = min(inside + [-0.5]), max(inside + [0.5])
        pad = 0.15 * (hi - lo)
        xl = (lo - pad, hi + pad)
        ax = axes_in(fig, w_lab + 0.10 + j * (w + gap), ay, w, ah)
        ax.set_ylim(*yl); ax.set_xlim(*xl)
        ax.axvline(0, color=INK2, lw=0.7, zorder=1)
        ax.spines["left"].set_visible(False); ax.set_yticks([])
        ax.xaxis.grid(True, color=GRID, lw=0.5); ax.set_axisbelow(True)
        ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(3, steps=[1, 2, 2.5, 5, 10]))
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
            lambda v, _: (f"{v:g}" if abs(v) >= 1e-9 else "0").replace("-", MINUS)))
        for i, (code, _) in enumerate(LADDER_ROWS):
            if code not in red:
                continue
            v = red[code]
            if xl[0] <= v <= xl[1]:
                ax.plot(v, -i, "o", ms=4.8, mfc=colr if code != "L1" else "white", mec=colr, mew=1.0, zorder=4)
            else:
                edge = xl[0] if v < xl[0] else xl[1]
                ax.plot(edge, -i, marker="<" if v < xl[0] else ">", ms=5.5, color=colr, mew=0, zorder=4,
                        clip_on=False)
                ax.annotate(f"{fnum(v)}%", (edge, -i), xytext=(6 if v < xl[0] else -6, 0),
                            textcoords="offset points", ha="left" if v < xl[0] else "right", va="center",
                            fontsize=7, color=INK2, zorder=6,
                            bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none"))
        ax.text(0.0, 1.0 + 0.06 / ah, COUNTRY_NAME[country], transform=ax.transAxes, fontsize=8,
                fontweight="bold", ha="left", va="bottom")
        x_cues(ax, left="← worse", right="better →", dy=-13, size=7)
    ftext(fig, w_lab + 0.06 + (W_FULL - w_lab - 0.06) / 2, ay - 0.34,
          "Reduction in forecast error relative to L1 (%)", ha="center", va="top")
    n_rows = {c: int(t2[t2.cell == c].n_rows.iloc[0]) for c in cells}
    return fig, dict(cells=cells, n_rows=n_rows)


# ============================================================================= captions
def captions(meta: dict, t1: pd.DataFrame) -> str:
    m2 = meta["fig2"]
    n_av, n_c = m2["n_avail"], m2["n_cells"]
    pend = (f" Cells not yet available: {', '.join(m2['pending'])}." if m2["pending"] else "")
    outl = (f" {', '.join(m2['outliers'])} is drawn on its own scale at left (axis break)."
            if m2["outliers"] else "")
    s3_note = ""
    for c, n in (meta.get("figS3") or {}).get("n_rows", {}).items():
        r1 = t1[t1.cell == c]
        if len(r1) and np.isfinite(r1.n_rows.iloc[0]) and int(r1.n_rows.iloc[0]) != n:
            s3_note += (f" {COUNTRY_NAME[CODE_COUNTRY[c[:2]]]}: the ladder table covers {n:,} rows, "
                        f"not the {int(r1.n_rows.iloc[0]):,} of the primary cell (Fig 2).")
    holm_m = int(t1.n_family_available.dropna().iloc[0]) if "n_family_available" in t1 else n_av
    holm_note = (f"Holm's correction is over the {holm_m} available cells; the final family has {n_c}"
                 if holm_m < n_c else f"Holm's correction is over all {n_c} cells")
    m4 = meta["fig4"]
    cs = m4["cstar"].get("BR_S1_nohist", "C*")
    cname = CONTROL_NAME.get(cs, cs)
    take = m4.get("takeaway", "")
    s2_note = ("" if "BR_S2_nohist" in m4["cells"] else
               " Brazil S2 (the arm's headline split) is not yet in the kit tables; the figure adds it "
               "automatically when it appears.")
    lines = [
        "# Figure captions (suggested)",
        "",
        "Generated by `scripts/paper/make_pub_figures.py` from the results-kit tables; cell counts, the selected "
        "control and pending notes update on rerun. WIS = weighted interval score on log(1 + cases); lower is "
        "better.",
        "",
        "**Fig 1. Study design and information timing.** Each comparison changes one block of inputs while "
        "the model, rows and configuration stay fixed; primary scores use only forecasts whose inputs and "
        "training labels end at the origin. (A) The feature ladder L0–L4 and the four models behind the "
        "three gains: the embedding gain (L3 to L4), the identity gain (L3 to L3 + C*) and the primary excess "
        "gain (L3 + C* to L4 + C*); the location control C* is chosen at the 2019 origin. (B) The five "
        "evaluation splits, drawn on generic clusters of hexagons standing for districts (light: training, "
        "dark: test, dashed: dropped buffer). (C) What one forecast at origin o may use: case and climate "
        "inputs up to week o, remote sensing from the last three complete months, yearly inputs from the year "
        "before the target's epidemiological year, and training targets up to the end of the previous year. "
        "Targets in the first h weeks of a year (origin in the previous year) are dropped from primary "
        "scoring.",
        "",
        f"**Fig 2. Excess gain from AlphaEarth embeddings in each country and evaluation split.** Points show "
        f"the reduction in mean WIS when the embeddings are added to a model that already has the "
        f"validation-selected location control (L3 + C* to L4 + C*), as a percentage of WIS(L3); positive "
        f"values mean the embeddings improved forecasts. Horizons 1 and 4 weeks pooled; lines are 95% "
        f"confidence intervals from Diebold–Mariano tests with an EWC variance estimator and the HLN "
        f"correction. Filled points: Holm-adjusted p < 0.05; {holm_note}. The grey band marks the ±1% "
        f"equivalence margin.{outl}{pend} S1 new years; S2 held-out states; S3 held-out buffered blocks; "
        f"S4 held-out random districts; S5 held-out country.",
        "",
        "**Fig 3. Where the excess gain comes from.** The excess gain of Fig 2 split additively into "
        "contributions from three kinds of target weeks: weeks with cases, zeros listed by the source "
        "(recorded zeros, Brazil 2020–2021 only) and weeks we filled with zero; the three contributions "
        "sum to the total at right. Values are percentage points of WIS(L3), horizons 1 and 4 pooled, with "
        "95% confidence intervals (filled: interval excludes 0). Strata depend on the outcome and are "
        "descriptive. Off-scale values are printed beside an arrow at the panel edge.",
        "",
        f"**Fig 4. Forecasting without case history (Brazil, exploratory arm).** Models use climate, remote "
        f"sensing and population only (N3), plus a location input. (A) Mean WIS for each model, horizons 1 and "
        f"4 pooled; C* is {cs} ({cname}), chosen at the 2019 origin, and C1 (the district's pre-2018 case "
        f"average) is a separate static-history rung. (B) Gains as a percentage of the base model's WIS, with "
        f"95% confidence intervals (filled: interval excludes 0); the grey band marks ±1%.{take}{s2_note}",
        "",
        "**Fig S1. Embedding similarity and the excess gain when a whole country is held out (S5).** Districts "
        "of the held-out country are split into fifths by the cosine similarity between their AlphaEarth "
        "embedding and that of the most similar training district. Points show each fifth's excess gain as a "
        "percentage of the country's overall WIS(L3), with 95% confidence intervals; ρ is the "
        "district-level Spearman correlation between similarity and gain. Vertical scales differ between "
        "panels.",
        "",
        "**Fig S2. Excess gain by test year.** Each point is one country × split × test year, as a "
        "percentage of that year's WIS(L3), horizons 1 and 4 pooled, with 95% confidence intervals (filled: "
        "interval excludes 0); marker shape gives the split. Shaded years are COVID-era reporting. Intervals "
        "running past the panel are cut with an arrowhead; in Taiwan 2021 there were no local cases, so WIS(L3) "
        "is tiny and percentages are very large. Vertical scales differ between panels.",
        "",
        "**Fig S3. The feature ladder in the new-years split (S1).** Reduction in mean WIS relative to L1 (case "
        "history only), horizons 1 and 4 pooled, for each level and for L3/L4 with the validation-selected "
        f"location control. Points beyond the panel are drawn as arrows with their value.{s3_note}",
        "",
    ]
    return "\n".join(lines)


# ============================================================================= main
def main():
    global TAB, OUT
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", nargs="*", help="subset, e.g. Fig2 FigS1")
    ap.add_argument("--tables", default=str(TAB), help="kit tables directory (default: docs/results/tables)")
    ap.add_argument("--out", default=str(OUT), help="output directory (default: docs/results/figures/pub)")
    args = ap.parse_args()
    TAB, OUT = Path(args.tables), Path(args.out)
    setup_style()
    t1 = read("T1_primary_family")
    want = set(args.only) if args.only else None
    meta = {}
    made = []

    def run(name, fn):
        if want is None or name in want:
            res = fn()
            fig, m = (res if isinstance(res, tuple) else (res, {}))
            made.extend(save(fig, name))
            return m
        return None

    run("Fig1", fig1)
    meta["fig2"] = run("Fig2", lambda: fig2(t1)) or fig2_meta_only(t1)
    run("Fig3", lambda: fig3(t1, read("T5_strata")))
    meta["fig4"] = run("Fig4", lambda: fig4(read("T6b_nohist_estimands"), read("T6c_nohist_ladder"),
                                            read("T4_cstar_selection"))) or {"cells": [], "cstar": {}}
    run("FigS1", lambda: figS1(read("S7_embedding_distance"), read("S7b_embedding_distance_bins")))
    run("FigS2", lambda: figS2(read("S8_per_year")))
    meta["figS3"] = run("FigS3", lambda: figS3(read("T2_ladder"))) or {}
    if want is None:
        (OUT / "CAPTIONS.md").write_text(captions(meta, t1))
        made.append(OUT / "CAPTIONS.md")
    for p in made:
        print(p)


def fig2_meta_only(t1):
    rows, _ = family_rows(t1)
    cells = [r for r in rows if r["kind"] == "cell"]
    avail = [r for r in cells if is_available(r["rec"])]
    return dict(n_avail=len(avail), n_cells=len(cells),
                pending=[f"{COUNTRY_NAME[r['country']]} {r['split']}" for r in cells if not is_available(r["rec"])],
                outliers=[f"{COUNTRY_NAME[r['country']]} {r['split']}" for r in avail
                          if abs(r["rec"]["pct_of_WIS_ref"]) > 5])


if __name__ == "__main__":
    main()
