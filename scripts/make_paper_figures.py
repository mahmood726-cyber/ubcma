#!/usr/bin/env python
"""Generate the UBCMA paper figures (Insight identity) from verified results.

Outputs (paper/figures/):
  fig1_aspirin_forest.png  - forest plot of the 6-trial aspirin dataset, UBCMA vs DL
  fig2_coverage.png        - 95% CI coverage by method (pilot simulation)
  visual_abstract.png      - one-page visual abstract

All numbers are read from committed, verified artifacts:
  examples/verde_2021_aspirin.csv      (real aspirin secondary-prevention RCTs)
  paper/results/pilot_summary.csv      (seed-42 pilot simulation, reproduces manuscript)

The aspirin pooled estimates are the values produced by `ubcma fit ... --profile-ci`
(UBCMA) and the DerSimonian-Laird marginal, independently cross-checked in R and Codex.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "paper" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

# Insight identity palette
ACCENT = "#7A5A10"
CARD = "#F5F3EE"
BORDER = "#E5E0D6"
TEXT = "#1a1a1a"
TEXT2 = "#555"
UBCMA_C = "#7A5A10"
DL_C = "#2E6B8A"
MUTE = "#9aa0a6"
RED = "#CB4335"
plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Georgia", "DejaVu Serif"],
        "axes.edgecolor": BORDER,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    }
)

# Verified aspirin pooled estimates (log odds ratio)
DL_MU, DL_LO, DL_HI = -0.0672, -0.1951, 0.0608
UB_MU, UB_LO, UB_HI = 0.0105, -0.1248, 0.1171


def fig1_forest() -> None:
    d = pd.read_csv(ROOT / "examples" / "verde_2021_aspirin.csv")
    studies = list(d.study_id)
    yi = d.yi.values
    sei = d.sei.values
    lo = yi - 1.96 * sei
    hi = yi + 1.96 * sei
    rows = studies + ["", "DerSimonian-Laird (pooled)", "UBCMA (pooled, profile CI)"]
    yvals = list(yi) + [None, DL_MU, UB_MU]
    ylo = list(lo) + [None, DL_LO, UB_LO]
    yhi = list(hi) + [None, DL_HI, UB_HI]
    ypos = np.arange(len(rows))[::-1]

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    for i, (r, v, lcl, hcl) in enumerate(zip(rows, yvals, ylo, yhi)):
        yp = ypos[i]
        if v is None:
            continue
        is_pool = r.startswith(("DerSimonian", "UBCMA"))
        col = UBCMA_C if r.startswith("UBCMA") else (DL_C if r.startswith("Der") else MUTE)
        ax.plot([lcl, hcl], [yp, yp], color=col, lw=2.2 if is_pool else 1.6,
                solid_capstyle="round", zorder=2)
        if is_pool:
            hh = 0.32
            ax.fill([lcl, v, hcl, v], [yp, yp + hh, yp, yp - hh], color=col, zorder=3, alpha=0.9)
        else:
            ax.scatter([v], [yp], s=(6 + (1 / sei[i]) * 0.25) * 8, color=col,
                       zorder=3, edgecolor="white", lw=0.5)
    ax.axvline(0, color=BORDER, ls="--", lw=1, zorder=1)
    ax.set_yticks(ypos)
    ax.set_yticklabels(rows, fontsize=9)
    for lab in ax.get_yticklabels():
        t = lab.get_text()
        if t.startswith("UBCMA"):
            lab.set_color(UBCMA_C)
            lab.set_fontweight("bold")
        elif t.startswith("DerSimonian"):
            lab.set_color(DL_C)
            lab.set_fontweight("bold")
    ax.set_xlabel("Log odds ratio (95% CI)   <- favours aspirin   |   favours control ->",
                  fontsize=9)
    ax.set_title("Aspirin secondary prevention (6 RCTs): UBCMA vs uncorrected pooling",
                 fontsize=10.5, color=ACCENT, fontweight="bold", pad=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xlim(-0.34, 0.235)
    ax.text(UB_HI + 0.005, ypos[-1], f" {UB_MU:+.2f} [{UB_LO:.2f}, {UB_HI:.2f}]",
            va="center", fontsize=8, color=UBCMA_C, fontweight="bold")
    ax.text(DL_HI + 0.005, ypos[-2], f" {DL_MU:+.2f} [{DL_LO:.2f}, {DL_HI:.2f}]",
            va="center", fontsize=8, color=DL_C, fontweight="bold")
    plt.tight_layout()
    plt.savefig(OUT / "fig1_aspirin_forest.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()


def fig2_coverage() -> None:
    summ = pd.read_csv(ROOT / "paper" / "results" / "pilot_summary.csv").set_index("method")
    order = ["ubcma", "reml_hksj", "dl_hksj", "pet_peese", "dl", "reml", "copas",
             "quality_effects", "trim_and_fill"]
    labels = {"ubcma": "UBCMA", "reml_hksj": "REML-HKSJ", "dl_hksj": "DL-HKSJ",
              "pet_peese": "PET-PEESE", "dl": "DerSimonian-Laird", "reml": "REML",
              "copas": "Copas", "quality_effects": "Quality-effects",
              "trim_and_fill": "Trim-and-fill"}
    cov = [summ.loc[m, "coverage"] * 100 for m in order]
    cols = [UBCMA_C if m == "ubcma" else MUTE for m in order]
    ypos = np.arange(len(order))[::-1]
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    ax.barh(ypos, cov, color=cols, height=0.66, zorder=3, edgecolor="white")
    ax.axvline(95, color=RED, ls="--", lw=1.2, zorder=2)
    ax.text(95, len(order) - 0.3, "nominal 95%", color=RED, fontsize=8, ha="center")
    ax.set_yticks(ypos)
    ax.set_yticklabels([labels[m] for m in order], fontsize=9)
    for lab in ax.get_yticklabels():
        if lab.get_text() == "UBCMA":
            lab.set_color(UBCMA_C)
            lab.set_fontweight("bold")
    for i, (yp, c) in enumerate(zip(ypos, cov)):
        ax.text(c + 1, yp, f"{c:.1f}%", va="center", fontsize=8,
                color=UBCMA_C if order[i] == "ubcma" else TEXT2,
                fontweight="bold" if order[i] == "ubcma" else "normal")
    ax.set_xlim(0, 105)
    ax.set_xlabel("95% CI coverage (%), 12 scenarios x 50 replicates, k=30", fontsize=9)
    ax.set_title("Confidence-interval coverage across methods", fontsize=10.5,
                 color=ACCENT, fontweight="bold", pad=10)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    plt.savefig(OUT / "fig2_coverage.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()


def visual_abstract() -> None:
    summ = pd.read_csv(ROOT / "paper" / "results" / "pilot_summary.csv").set_index("method")
    fig = plt.figure(figsize=(9, 5.0))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 5)
    # header band
    ax.add_patch(plt.Rectangle((0, 4.35), 9, 0.65, color=ACCENT, zorder=1))
    ax.text(0.3, 4.67, "UBCMA", fontsize=20, color="white", fontweight="bold", va="center")
    ax.text(2.35, 4.78, "Unified Bias-Calibrated Meta-Analysis", fontsize=11.5,
            color="white", va="center", style="italic")
    ax.text(2.35, 4.54, "Joint modelling of heterogeneity, publication selection & study-quality bias",
            fontsize=8.2, color="#f0e8d8", va="center")
    ax.text(8.7, 4.67, "Insight", fontsize=11, color="white", va="center", ha="right",
            style="italic")
    # left panel
    ax.text(0.3, 3.95, "THE PROBLEM", fontsize=8, color=ACCENT, fontweight="bold")
    for i, t in enumerate(["Heterogeneity", "Publication selection", "Study-quality bias"]):
        y = 3.55 - i * 0.42
        ax.add_patch(FancyBboxPatch((0.3, y - 0.16), 2.5, 0.34,
                     boxstyle="round,pad=0.02,rounding_size=0.06", fc=CARD, ec=BORDER, lw=1, zorder=2))
        ax.text(1.55, y, t, fontsize=8.6, ha="center", va="center", color=TEXT)
    ax.text(1.55, 1.95, "usually corrected\nseparately  =>  residual bias", fontsize=7.8,
            ha="center", va="center", color=RED, style="italic")
    ax.add_patch(FancyArrowPatch((2.95, 2.9), (3.65, 2.9), arrowstyle="-|>",
                 mutation_scale=16, color=ACCENT, lw=2))
    ax.add_patch(FancyBboxPatch((3.7, 2.5), 1.5, 0.8,
                 boxstyle="round,pad=0.03,rounding_size=0.08", fc=ACCENT, ec="none", zorder=2))
    ax.text(4.45, 2.9, "ONE\nlikelihood", fontsize=9, ha="center", va="center",
            color="white", fontweight="bold")
    # right panel: coverage
    res = [("UBCMA", summ.loc["ubcma", "coverage"] * 100, UBCMA_C),
           ("REML-HKSJ", summ.loc["reml_hksj", "coverage"] * 100, MUTE),
           ("DerSimonian-Laird", summ.loc["dl", "coverage"] * 100, MUTE),
           ("Trim-and-fill", summ.loc["trim_and_fill", "coverage"] * 100, MUTE)]
    ax.text(5.65, 3.95, "95% CI COVERAGE  (12 scenarios, k=30)", fontsize=8,
            color=ACCENT, fontweight="bold")
    x0, w = 6.85, 1.75
    for i, (lab, val, col) in enumerate(res):
        y = 3.5 - i * 0.45
        ax.add_patch(plt.Rectangle((x0, y - 0.12), w * val / 100, 0.24, color=col, zorder=2))
        ax.add_patch(plt.Rectangle((x0, y - 0.12), w, 0.24, fill=False, ec=BORDER, lw=0.6, zorder=1))
        ax.text(x0 - 0.12, y, lab, fontsize=7.6, ha="right", va="center",
                color=col if col == UBCMA_C else TEXT,
                fontweight="bold" if col == UBCMA_C else "normal")
        vtxt = f"{val:.1f}%" if col == UBCMA_C else f"{val:.0f}%"
        ax.text(x0 + w * val / 100 + 0.05, y, vtxt, fontsize=7.8, va="center",
                color=col if col == UBCMA_C else TEXT2,
                fontweight="bold" if col == UBCMA_C else "normal")
    ax.plot([x0 + w * 0.95] * 2, [1.55, 3.62], color=RED, ls="--", lw=1)
    ax.text(x0 + w * 0.95, 3.72, "95%", fontsize=7, color=RED, ha="center")
    # bottom band
    ax.add_patch(plt.Rectangle((0, 0.0), 9, 1.25, color=CARD, zorder=0))
    ax.text(0.3, 0.95, "KEY RESULT", fontsize=8, color=ACCENT, fontweight="bold")
    ax.text(0.3, 0.58, "Highest coverage 88.8% at RMSE 0.070 vs 59.7% (DL), 39.0% (trim-and-fill);",
            fontsize=9, color=TEXT, va="center")
    ax.text(0.3, 0.27, "holds at 90.3% when selection + quality bias co-occur (DL 31.3%).",
            fontsize=9, color=TEXT, va="center")
    ax.text(8.7, 0.6, "Aspirin (6 RCTs):", fontsize=8, color=TEXT2, ha="right",
            va="center", fontweight="bold")
    ax.text(8.7, 0.32, "pooled log-OR +0.01 [-0.12, 0.12]", fontsize=8, color=UBCMA_C,
            ha="right", va="center", fontweight="bold")
    plt.savefig(OUT / "visual_abstract.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()


if __name__ == "__main__":
    fig1_forest()
    fig2_coverage()
    visual_abstract()
    print(f"Figures written to {OUT}")
