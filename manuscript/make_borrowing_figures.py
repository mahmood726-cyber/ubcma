"""Figures for the Registry-Informed Relevance-Weighted Borrowing report.

TRUTH-FIRST: this script reads ONLY committed result artifacts in
F:\\ubcma\\borrowing and re-plots them. It computes no new estimates. Every
number on every axis is traceable to one of:

  - probe_trials.json          (real GLP1 dose-response points; pilot-2)
  - pilot_bootstrap.json       (pilot-1 paired-bootstrap MCIW0 contrasts)
  - sim_gate_results.json      (pilot-2 calibrated boundary map, beta sweep)
  - pilot3_loo_summary.json    (pilot-3 real LOO paired-bootstrap contrasts)
  - sim_transport_results.json (pilot-3 known-truth beta sweep)

Run:  python manuscript/make_borrowing_figures.py
Out:  manuscript/figures_borrowing/fig{1,2,3}_*.png
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "borrowing")
OUT = os.path.join(HERE, "figures_borrowing")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
})

C_WIN = "#1b7837"     # green  = relevance/transport helps
C_HARM = "#b2182b"    # red    = harm
C_NULL = "#888888"    # grey   = inert / null
C_BLUE = "#2166ac"
C_ORANGE = "#d6604d"


def load(name):
    with open(os.path.join(SRC, name), "r", encoding="utf-8") as f:
        return json.load(f)


# ----------------------------------------------------------------------------
# FIG 1 — Pilot 1: the inertia result (relevance near-inert; one robust harm)
# ----------------------------------------------------------------------------
def fig1():
    boot = load("pilot_bootstrap.json")
    idx = {(r["target"], r["regime"], r["contrast"]): r for r in boot}
    cells = [("DPP4", "sparse"), ("SGLT2", "sparse"), ("GLP1", "sparse"),
             ("DPP4", "rich"), ("SGLT2", "rich"), ("GLP1", "rich")]
    labels = [f"{t}\n{rg}" for t, rg in cells]

    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.0))

    # Panel A: borrow vs NMA
    ax = axes[0]
    for i, (t, rg) in enumerate(cells):
        r = idx[(t, rg, "borrow_vs_nma")]
        d, lo, hi = r["mciw0_diff"], r["ci_lo"], r["ci_hi"]
        col = C_HARM if r["robust_harm"] else (C_WIN if r["robust_win"] else C_NULL)
        ax.errorbar(i, d, yerr=[[d - lo], [hi - d]], fmt="o", color=col,
                    capsize=4, ms=7, lw=2)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(range(len(cells)))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel(r"$\Delta$MCIW0  vs standard NMA")
    ax.set_title("A. Borrowing field vs NMA")
    ax.annotate("robust harm\n(GLP1 outlier, rich)", xy=(5, 0.2556), xytext=(2.4, 0.20),
                fontsize=8, color=C_HARM,
                arrowprops=dict(arrowstyle="->", color=C_HARM, lw=1))
    ax.annotate("only robust win", xy=(0, -0.0387), xytext=(0.9, -0.13),
                fontsize=8, color=C_WIN, ha="left",
                arrowprops=dict(arrowstyle="->", color=C_WIN, lw=1))
    ax.text(0.02, 0.97, "below 0 = narrower (better)", transform=ax.transAxes,
            fontsize=7.5, va="top", style="italic", color="#555")

    # Panel B: gravity isolation — borrow vs shrink_mean (null)
    ax = axes[1]
    for i, (t, rg) in enumerate(cells):
        r = idx[(t, rg, "borrow_vs_shrink_mean")]
        d, lo, hi = r["mciw0_diff"], r["ci_lo"], r["ci_hi"]
        ax.errorbar(i, d, yerr=[[d - lo], [hi - d]], fmt="s", color=C_BLUE,
                    capsize=4, ms=6, lw=1.6)
    ax.axhline(0, color="k", lw=0.8)
    ax.axhspan(-0.04, 0.04, color="#cfe6ff", alpha=0.5, zorder=0)
    ax.set_xticks(range(len(cells)))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel(r"$\Delta$MCIW0  vs no-relevance null")
    ax.set_title("B. Does the relevance gravity add anything?")
    ax.set_ylim(axes[0].get_ylim())
    ax.text(0.5, 0.92, "all cells |Δ| < 0.04\n→ relevance ≈ inert",
            transform=ax.transAxes, ha="center", fontsize=8.5, color=C_BLUE)

    fig.suptitle("Pilot 1 (flat-covariate slice): the borrowing field reduces to "
                 "generic shrinkage — and harms the outlier",
                 fontsize=11.5, fontweight="bold", y=1.01)
    fig.tight_layout()
    p = os.path.join(OUT, "fig1_pilot1_inertia.png")
    fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    print("wrote", p)


# ----------------------------------------------------------------------------
# FIG 2 — Pilot 2: relevance is real when a covariate predicts heterogeneity
# ----------------------------------------------------------------------------
def fig2():
    trials = load("probe_trials.json")
    sim = load("sim_gate_results.json")
    g = [t for t in trials if t.get("active") == "GLP1" and t.get("dose")]
    dose = np.array([t["dose"] for t in g])
    y = np.array([t["y"] for t in g])
    se = np.array([t["se"] for t in g])

    # committed meta-regression line (real_glp1_summary.json)
    summ = load("real_glp1_summary.json")
    b0, b1 = summ["intercept"], summ["slope"]

    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.0))

    # Panel A: real GLP1 dose-response
    ax = axes[0]
    ax.errorbar(dose, y, yerr=1.96 * se, fmt="o", color=C_BLUE, ms=6,
                capsize=3, lw=1, alpha=0.85, label="real GLP1 trials (n=12)")
    xs = np.linspace(dose.min(), dose.max(), 50)
    ax.plot(xs, b0 + b1 * xs, color=C_HARM, lw=2,
            label=f"slope {b1:.3f} %HbA1c/mg\n(perm p={summ['perm_p']}, R²={summ['R2']:.2f})")
    ax.set_xlabel("GLP1 dose (mg)")
    ax.set_ylabel(r"HbA1c effect vs placebo (%)")
    ax.set_title("A. A real, strong effect modifier")
    ax.legend(fontsize=7.5, loc="upper right")

    # Panel B: boundary map — relevance vs nulls across DGP slope (sparse off-centre)
    ax = axes[1]
    slopes = ["flat(0)", "half", "real", "steep"]
    beta = {"flat(0)": 0.0, "half": -0.0461, "real": -0.0922, "steep": -0.1476}
    # average the two off-centre sparse cells (low, high) used in the report
    def avg_contrast(slope, key):
        rows = [r for r in sim if r["slope"] == slope and r["regime"] == "sparse"
                and r["pos"] in ("low", "high")]
        return np.mean([r[key]["d"] for r in rows])
    rel_unif = [avg_contrast(s, "rel_vs_uniform") for s in slopes]
    rel_scr = [avg_contrast(s, "rel_vs_scrambled") for s in slopes]
    x = np.arange(len(slopes))
    ax.plot(x, rel_unif, "o-", color=C_WIN, lw=2, ms=7, label="relevance − uniform null")
    ax.plot(x, rel_scr, "s--", color=C_ORANGE, lw=2, ms=6, label="relevance − scrambled null")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{beta[s]:.3f}\n({s.split('(')[0]})" for s in slopes], fontsize=8)
    ax.set_xlabel("DGP modifier slope β")
    ax.set_ylabel(r"$\Delta$MCIW0 (off-centre, sparse)")
    ax.set_title("B. Inert at β=0, beats both nulls at real β")
    ax.legend(fontsize=7.5, loc="lower left")
    ax.annotate("inert\n(= pilot 1)", xy=(0, rel_unif[0]), xytext=(0.05, 0.018),
                fontsize=8, color=C_NULL, ha="left",
                arrowprops=dict(arrowstyle="->", color=C_NULL, lw=1))

    fig.suptitle("Pilot 2 (GLP1-dose slice): relevance-weighted borrowing beats both "
                 "nulls exactly when the covariate carries signal",
                 fontsize=11.5, fontweight="bold", y=1.01)
    fig.tight_layout()
    p = os.path.join(OUT, "fig2_pilot2_relevance.png")
    fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    print("wrote", p)


# ----------------------------------------------------------------------------
# FIG 3 — Pilot 3: transportability conditional result + power threshold
# ----------------------------------------------------------------------------
def fig3():
    loo = load("pilot3_loo_summary.json")["by_regime"]["ALL"]
    sim = load("sim_transport_results.json")

    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.0))

    # Panel A: real LOO contrasts
    ax = axes[0]
    contrasts = [
        ("relevance − NMA", loo["relevance_vs_nma"]),
        ("transport − relevance", loo["transport_vs_relevance"]),
        ("transport − NMA", loo["transport_vs_nma"]),
        ("transport − scrambled", loo["transport_vs_scrambled"]),
    ]
    for i, (lab, v) in enumerate(contrasts):
        d, lo, hi, robust = v
        col = C_WIN if (robust and d < 0) else C_NULL
        ax.errorbar(d, i, xerr=[[d - lo], [hi - d]], fmt="o", color=col,
                    capsize=4, ms=7, lw=2)
    ax.axvline(0, color="k", lw=0.8)
    ax.set_yticks(range(len(contrasts)))
    ax.set_yticklabels([c[0] for c in contrasts], fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlabel(r"$\Delta$MAE on real held-out effects")
    ax.set_title("A. Real LOO contrasts")
    ax.text(0.97, 0.06, "left of 0 = better", transform=ax.transAxes,
            ha="right", fontsize=7.5, style="italic", color="#555")

    # Panel B: known-truth beta sweep — transport flat, relevance/NMA blow up
    ax = axes[1]
    sweep = sim["sweep"]
    betas = sorted(float(b) for b in sweep)
    mae_t = [sweep[f"{b}" if f"{b}" in sweep else str(b)]["mae"]["transport"] for b in betas]
    # robust key lookup
    def m(b, k):
        key = next(kk for kk in sweep if abs(float(kk) - b) < 1e-9)
        return sweep[key]["mae"][k]
    mae_t = [m(b, "transport") for b in betas]
    mae_r = [m(b, "relevance") for b in betas]
    mae_n = [m(b, "nma") for b in betas]
    ax.plot(betas, mae_n, "^-", color=C_NULL, lw=1.6, ms=6, label="NMA")
    ax.plot(betas, mae_r, "s-", color=C_BLUE, lw=1.8, ms=6, label="relevance-only")
    ax.plot(betas, mae_t, "o-", color=C_WIN, lw=2.2, ms=7, label="transport")
    ax.axvline(sim["real_beta"], color=C_HARM, ls=":", lw=1.5)
    ax.text(sim["real_beta"] + 0.002, ax.get_ylim()[1] * 0.55,
            "real β=0.006\n(inert corner)", color=C_HARM, fontsize=7.5, va="center")
    ax.axvspan(0.01, 0.02, color="#ffe9b3", alpha=0.6, zorder=0)
    ax.text(0.022, ax.get_ylim()[1] * 0.40, "crossover\nβ≈0.01–0.02",
            fontsize=7.5, color="#996600")
    ax.set_xlabel(r"true population-modifier slope $\beta$")
    ax.set_ylabel("MAE to known truth")
    ax.set_title("B. Known-truth β-sweep")
    ax.legend(fontsize=7.5, loc="upper left")

    fig.suptitle("Pilot 3 (population/obesity transport): correct machinery, but the real "
                 "modifier is below the power threshold",
                 fontsize=11.5, fontweight="bold", y=1.01)
    fig.tight_layout()
    p = os.path.join(OUT, "fig3_pilot3_transport.png")
    fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    print("wrote", p)


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    print("done")
