"""make_nma_figures.py -- figures for the AdaptShrink-NMA manuscript.

Truth-first: reads ONLY the committed Phase-4 boundary-map CSV
(nma/truth-recovery/nma_tausel_grid_map.csv). No numbers are hand-entered; every
value plotted is taken from that file. Run:

    python manuscript/make_nma_figures.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "nma" / "truth-recovery" / "nma_tausel_grid_map.csv"
OUT = ROOT / "manuscript" / "figures_nma"
OUT.mkdir(parents=True, exist_ok=True)

TAUS = [0.05, 0.10, 0.20, 0.30]
NS = [5, 6, 8, 10, 12]
SELS = ["none", "moderate", "strong"]
BORDER = 0.002  # |CI bound| < BORDER => borderline (matches the report's gate)

df = pd.read_csv(SRC)


def flag(row):
    if not row["MCIW0_robust"]:
        return "."
    return "b" if abs(row["dMCIW0_hi"]) < BORDER else "W"


df["flag"] = df.apply(flag, axis=1)


# ---- Figure 1: the 60-cell boundary map (3 panels, tau x n heatmaps) ----------
def fig_boundary_map():
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.4), constrained_layout=True)
    vmax = float(np.abs(df["dMCIW0"]).max())
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax)
    cmap = plt.get_cmap("RdBu")  # blue = negative (auto narrower = win direction)
    im = None
    for ax, sel in zip(axes, SELS):
        sub = df[df["selection"] == sel]
        M = np.full((len(TAUS), len(NS)), np.nan)
        for _, r in sub.iterrows():
            i = TAUS.index(round(r["tau"], 2))
            j = NS.index(int(r["n"]))
            M[i, j] = r["dMCIW0"]
        im = ax.imshow(M, cmap=cmap, norm=norm, aspect="auto", origin="upper")
        for _, r in sub.iterrows():
            i = TAUS.index(round(r["tau"], 2))
            j = NS.index(int(r["n"]))
            fl = r["flag"]
            txt = f"{fl}\n{r['dMCIW0']:+.3f}"
            weight = "bold" if fl == "W" else "normal"
            color = "white" if abs(r["dMCIW0"]) > 0.6 * vmax else "black"
            ax.text(j, i, txt, ha="center", va="center", fontsize=7.5,
                    fontweight=weight, color=color)
        ax.set_xticks(range(len(NS)), [f"n={n}" for n in NS])
        ax.set_yticks(range(len(TAUS)), [f"τ={t:.2f}" for t in TAUS])
        ax.set_title(f"selection = {sel}", fontsize=11, fontweight="bold")
        ax.set_xlabel("network size")
    axes[0].set_ylabel("heterogeneity τ")
    cb = fig.colorbar(im, ax=axes, shrink=0.85, pad=0.015)
    cb.set_label("dMCIW0  (negative = AdaptShrink-NMA narrower at matched coverage)")
    fig.suptitle("Boundary map: bootstrap-robust matched-coverage efficiency win "
                 "(W = robust, b = borderline, . = no win)", fontsize=12)
    p = OUT / "fig1_boundary_map.png"
    fig.savefig(p, dpi=160)
    plt.close(fig)
    return p


# ---- Figure 2: deployable-coverage collapse under strong selection ------------
def fig_coverage_collapse():
    sub = df[df["selection"] == "strong"].copy()
    fig, ax = plt.subplots(figsize=(7.6, 5.0), constrained_layout=True)
    colors = plt.get_cmap("viridis")(np.linspace(0.1, 0.85, len(TAUS)))
    for t, c in zip(TAUS, colors):
        s = sub[np.isclose(sub["tau"], t)].sort_values("n")
        ax.plot(s["n"], s["rawcov_auto"], "-o", color=c,
                label=f"AdaptShrink-NMA, τ={t:.2f}")
        ax.plot(s["n"], s["rawcov_DL"], "--s", color=c, alpha=0.7,
                label=f"netmeta common-DL, τ={t:.2f}")
    ax.axhline(0.95, color="grey", lw=1, ls=":")
    ax.text(5.0, 0.955, "nominal 0.95", fontsize=8, color="grey")
    ax.set_xlabel("network size n")
    ax.set_ylabel("deployable coverage of the true contrasts (κ = 1)")
    ax.set_xticks(NS)
    ax.set_ylim(0.40, 1.0)
    ax.set_title("Strong selection: the field default's coverage collapses with n "
                 "and τ;\nAdaptShrink-NMA holds near nominal", fontsize=10.5)
    ax.legend(fontsize=7.0, ncol=2, loc="lower left")
    p = OUT / "fig2_coverage_collapse.png"
    fig.savefig(p, dpi=160)
    plt.close(fig)
    return p


# ---- Figure 3: the monotone efficiency frontier (dMCIW0) ----------------------
def fig_frontier():
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6), constrained_layout=True)
    # left: dMCIW0 vs n for each tau (strong)
    sub = df[df["selection"] == "strong"].copy()
    colors = plt.get_cmap("plasma")(np.linspace(0.1, 0.8, len(TAUS)))
    ax = axes[0]
    for t, c in zip(TAUS, colors):
        s = sub[np.isclose(sub["tau"], t)].sort_values("n")
        ax.plot(s["n"], s["dMCIW0"], "-o", color=c, label=f"τ={t:.2f}")
    ax.axhline(0.0, color="black", lw=1)
    ax.set_xlabel("network size n")
    ax.set_ylabel("dMCIW0 (negative = win direction)")
    ax.set_xticks(NS)
    ax.set_title("Strong selection: win strengthens monotonically in n\n"
                 "(no plateau through n=12)", fontsize=10)
    ax.legend(title="heterogeneity", fontsize=8)
    # right: dMCIW0 vs tau at n=12, all three selection regimes
    ax = axes[1]
    sel_color = {"none": "#1b9e77", "moderate": "#d95f02", "strong": "#7570b3"}
    for sel in SELS:
        s = df[(df["selection"] == sel) & (df["n"] == 12)].sort_values("tau")
        ax.plot(s["tau"], s["dMCIW0"], "-o", color=sel_color[sel], label=sel)
    ax.axhline(0.0, color="black", lw=1)
    ax.set_xlabel("heterogeneity τ")
    ax.set_ylabel("dMCIW0 at n=12")
    ax.set_xticks(TAUS)
    ax.set_title("At the largest network (n=12): heterogeneity amplifies the win\n"
                 "under selection; control stays positive", fontsize=10)
    ax.legend(title="selection", fontsize=8)
    p = OUT / "fig3_frontier.png"
    fig.savefig(p, dpi=160)
    plt.close(fig)
    return p


if __name__ == "__main__":
    for fn in (fig_boundary_map, fig_coverage_collapse, fig_frontier):
        print("wrote", fn())
