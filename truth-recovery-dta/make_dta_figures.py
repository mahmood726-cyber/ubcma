"""make_dta_figures.py -- figures for the AdaptShrink-DTA Phase 2 report.

Every figure is built ONLY from committed seeded result files
(`dta_full_table.csv`, `dta_focus_table.csv`, `dta_focus_truthgate.json`,
`dta_sparse_table.csv`); nothing is hand-entered. Re-run after the bake-off:

  PYTHONPATH=src python truth-recovery-dta/make_dta_figures.py

Outputs (truth-recovery-dta/):
  fig_dta_winmap_full.png   full-grid MCIW0-2D area ratio adaptshrink/reitsma,
                            by (k, rho, prev) x selection strength.
  fig_dta_field_focus.png   focus-grid MCIW0-2D area per method per cell (the
                            field-to-beat incl. HSROC + REML).
  fig_dta_robust_matrix.png focus-grid: does adaptshrink robustly beat each
                            field member? (paired bootstrap, 97.5% CI).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
HC = "reitsma"
OURS = "adaptshrink_dta"
STRENGTHS = ["none", "moderate", "strong"]


def _ratio_map(table_csv: Path, out_png: Path):
    """Heatmap of OURS/HC MCIW0-2D area across the full grid."""
    if not table_csv.exists():
        print(f"[skip] {table_csv.name} missing")
        return
    t = pd.read_csv(table_csv)
    piv = t.pivot_table(index=["cell", "strength"], columns="method",
                        values="mciw0_area")
    if OURS not in piv.columns or HC not in piv.columns:
        print(f"[skip] {table_csv.name}: missing methods")
        return
    piv = piv.dropna(subset=[OURS, HC])
    piv["ratio"] = piv[OURS] / piv[HC]
    piv = piv.reset_index()

    def parse(cell):
        m = re.match(r"k(\d+)_rho([-\d.]+)_p([\d.]+)", cell)
        if m:
            return int(m.group(1)), float(m.group(2)), float(m.group(3))
        return (0, 0.0, 0.0)
    parsed = piv["cell"].map(parse)
    piv["k"] = [p[0] for p in parsed]
    piv["rho"] = [p[1] for p in parsed]
    piv["prev"] = [p[2] for p in parsed]
    rows = (piv[["k", "rho", "prev"]].drop_duplicates()
            .sort_values(["k", "rho", "prev"]))
    row_labels = [f"k={int(r.k)} ρ={r.rho:g} p={r.prev:g}"
                  for r in rows.itertuples()]
    M = np.full((len(rows), len(STRENGTHS)), np.nan)
    for i, r in enumerate(rows.itertuples()):
        for j, s in enumerate(STRENGTHS):
            sub = piv[(piv.k == r.k) & (piv.rho == r.rho) & (piv.prev == r.prev)
                      & (piv.strength == s)]
            if len(sub):
                M[i, j] = sub["ratio"].iloc[0]

    fig, ax = plt.subplots(figsize=(6.2, max(5, 0.30 * len(rows) + 1)))
    vmax = float(np.nanmax(np.abs(np.log2(M))))
    im = ax.imshow(np.log2(M), aspect="auto", cmap="RdBu_r",
                   vmin=-vmax, vmax=vmax)
    ax.set_xticks(range(len(STRENGTHS)))
    ax.set_xticklabels([s for s in STRENGTHS])
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(row_labels, fontsize=6)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            if np.isfinite(M[i, j]):
                ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center",
                        fontsize=5.5,
                        color="black" if abs(np.log2(M[i, j])) < 0.4 else "white")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("log2(adaptshrink / reitsma  MCIW0-2D area)\n<0 = adaptshrink "
                 "smaller region (better)", fontsize=7)
    ax.set_title("AdaptShrink-DTA vs Reitsma: matched-coverage region-area ratio\n"
                 "(full grid; blue = adaptshrink wins)", fontsize=9)
    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    print(f"[ok] {out_png.name}")


def _field_bars(table_csv: Path, out_png: Path, title: str):
    """Grouped bars of MCIW0-2D area per method, per (cell,strength)."""
    if not table_csv.exists():
        print(f"[skip] {table_csv.name} missing")
        return
    t = pd.read_csv(table_csv)
    cells = sorted(t["cell"].unique())
    methods = ["reitsma", "reitsma_reml", "reitsma_indep", "hsroc",
               "sep_univariate", "adaptshrink_dta"]
    methods = [m for m in methods if m in t["method"].unique()]
    colors = {"reitsma": "#444", "reitsma_reml": "#888",
              "reitsma_indep": "#b0b0b0", "hsroc": "#1f77b4",
              "sep_univariate": "#d9d9d9", "adaptshrink_dta": "#d62728"}
    ncell = len(cells)
    fig, axes = plt.subplots(ncell, 1, figsize=(8, 1.7 * ncell + 1),
                             squeeze=False)
    for ci, cell in enumerate(cells):
        ax = axes[ci][0]
        x = np.arange(len(STRENGTHS))
        w = 0.8 / len(methods)
        for mi, m in enumerate(methods):
            vals = []
            for s in STRENGTHS:
                sub = t[(t.cell == cell) & (t.strength == s) & (t.method == m)]
                vals.append(sub["mciw0_area"].iloc[0] if len(sub) else np.nan)
            ax.bar(x + mi * w, vals, w, label=m, color=colors.get(m, None))
        ax.set_xticks(x + 0.4 - w / 2)
        ax.set_xticklabels(STRENGTHS)
        ax.set_ylabel("MCIW0-2D", fontsize=8)
        ax.set_title(cell, fontsize=8)
        if ci == 0:
            ax.legend(fontsize=6, ncol=3, loc="upper right")
    fig.suptitle(title, fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.98))
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    print(f"[ok] {out_png.name}")


def _robust_matrix(gate_json: Path, out_png: Path):
    """Matrix: does adaptshrink robustly beat each field member per cell?"""
    if not gate_json.exists():
        print(f"[skip] {gate_json.name} missing")
        return
    g = json.loads(gate_json.read_text())
    rows = g.get("ours_vs_field", [])
    if not rows:
        print(f"[skip] {gate_json.name}: no ours_vs_field")
        return
    df = pd.DataFrame(rows)
    df["cs"] = df["cell"] + " / " + df["strength"]
    members = sorted(df["vs"].unique())
    css = sorted(df["cs"].unique())
    M = np.full((len(css), len(members)), np.nan)
    for i, cs in enumerate(css):
        for j, mem in enumerate(members):
            sub = df[(df.cs == cs) & (df.vs == mem)]
            if len(sub):
                r = sub.iloc[0]
                M[i, j] = 1.0 if r["ours_robust_beats"] else (
                    0.5 if r["darea_ours_minus_x"] < 0 else 0.0)
    fig, ax = plt.subplots(figsize=(1.3 * len(members) + 2,
                                    0.32 * len(css) + 1.5))
    im = ax.imshow(M, aspect="auto", cmap="RdYlGn", vmin=0, vmax=1)
    ax.set_xticks(range(len(members)))
    ax.set_xticklabels(members, rotation=35, ha="right", fontsize=7)
    ax.set_yticks(range(len(css)))
    ax.set_yticklabels(css, fontsize=6)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            if np.isfinite(M[i, j]):
                lab = {1.0: "WIN", 0.5: "~", 0.0: "x"}[M[i, j]]
                ax.text(j, i, lab, ha="center", va="center", fontsize=6)
    ax.set_title("Does adaptshrink_dta robustly beat each field member?\n"
                 "(green WIN = 97.5% CI of area gain < 0; ~ = better but not "
                 "robust; x = not better)", fontsize=8)
    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    print(f"[ok] {out_png.name}")


def main():
    _ratio_map(HERE / "dta_full_table.csv", HERE / "fig_dta_winmap_full.png")
    _field_bars(HERE / "dta_focus_table.csv", HERE / "fig_dta_field_focus.png",
                "Field-to-beat MCIW0-2D area (focus grid, with HSROC)")
    _robust_matrix(HERE / "dta_focus_truthgate.json",
                   HERE / "fig_dta_robust_matrix.png")


if __name__ == "__main__":
    main()
