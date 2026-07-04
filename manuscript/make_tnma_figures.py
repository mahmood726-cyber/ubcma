"""Figures for the transport-NMA + registry-publication-bias manuscript.
Truth-first: every value is read from the committed transport_nma JSON artifacts.
Run: python manuscript/make_tnma_figures.py
"""
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(r"F:\ubcma"); TN = ROOT/"transport_nma"; OUT = ROOT/"manuscript"/"figures_tnma"
OUT.mkdir(exist_ok=True)
K = json.load(open(TN/"aact_kappa.json"))
FR = json.load(open(TN/"aact_kappa_frozen.json"))
TG = json.load(open(TN/"aact_kappa_truthgate_result.json"))["sweep"]
H2 = json.load(open(TN/"h2h_result.json"))["sweep"]
LAM = json.load(open(ROOT/"borrowing"/"class_lambda.json"))
plt.rcParams.update({"font.size": 11, "font.family": "DejaVu Sans", "axes.grid": True,
                     "grid.alpha": 0.3, "axes.axisbelow": True})
BLUE, RED, GREY, GREEN, ORANGE = "#2E5496", "#C0392B", "#7F8C8D", "#1E8449", "#E67E22"

# ---- Fig 1: corr(kappa_MD, 1-lambda) scatter (the no-oracle validation) ----
used = FR["classes_used"]
xs, ys, labs = [], [], []
for c in K:
    kmd = K[c].get("kappa_md")
    if kmd is None or c not in LAM:
        continue
    xs.append(1.0-LAM[c]); ys.append(kmd); labs.append(c)
xs, ys = np.array(xs), np.array(ys)
fig, ax = plt.subplots(figsize=(6.4, 4.6))
for x, y, c in zip(xs, ys, labs):
    inuse = c in used
    ax.scatter(x, y, s=90 if inuse else 55, c=(BLUE if inuse else GREY),
               edgecolor="k", linewidth=0.6, zorder=3, alpha=0.9 if inuse else 0.5)
    ax.annotate(c, (x, y), fontsize=8, xytext=(4, 4), textcoords="offset points",
                color=("k" if inuse else GREY))
m = np.array([r[2] >= 8 for r in [(c, None, min(K[c]["pub"]["n"], K[c]["reg"]["n"])) for c in labs]])
sl = FR["kappa_slope"]
gx = np.linspace(0, max(xs)*1.05, 50)
ax.plot(gx, sl*gx, color=RED, lw=2, label=f"WLS slope (through 0) = {sl:.2f} = external B̂")
ax.axhline(0, color="k", lw=0.8)
ax.set_xlabel("registry selection severity  (1 − λ),  λ = results-posted / registered")
ax.set_ylabel("published − registered HbA1c effect gap  κ_MD")
ax.set_title(f"External validation of the registry model (no oracle)\nPearson r = {FR['corr_kmd_vs_1mlam']:.2f}"
             "  (large = adequately-powered classes)")
ax.legend(loc="upper left", fontsize=9)
fig.tight_layout(); fig.savefig(OUT/"fig1_corr_validation.png", dpi=150); plt.close(fig)

# ---- Fig 2: head-to-head vs internal selection models (Regime A, B=0.15 & 0.30) ----
def row(sweep, regime, B, m):
    for r in sweep:
        if r["regime"] == regime and abs(r["B"]-B) < 1e-6:
            return r["rows"][m]
    return None
meths = [("registry_oracle", "registry-λ\n(oracle κ)", BLUE),
         ("PET", "PET-PEESE", RED), ("TF", "trim-and-fill", ORANGE), ("HC", "Henmi–Copas", GREY)]
fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.4), sharey=True)
for ax, B in zip(axes, (0.15, 0.30)):
    labels = [lab for _, lab, _ in meths]
    vals = [row(H2, "A", B, mk)["dmciw0"] for mk, _, _ in meths]
    los = [row(H2, "A", B, mk)["ci"][0] for mk, _, _ in meths]
    his = [row(H2, "A", B, mk)["ci"][1] for mk, _, _ in meths]
    cols = [c for _, _, c in meths]
    xpos = np.arange(len(meths))
    err = np.array([[v-lo for v, lo in zip(vals, los)], [hi-v for v, hi in zip(vals, his)]])
    ax.bar(xpos, vals, color=cols, edgecolor="k", linewidth=0.6, zorder=3)
    ax.errorbar(xpos, vals, yerr=err, fmt="none", ecolor="k", capsize=4, lw=1.1, zorder=4)
    ax.axhline(0, color="k", lw=1)
    ax.set_xticks(xpos); ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_title(f"selection strength B = {B:.2f}")
    ax.set_ylabel("ΔMCIW0 vs unadjusted NMA  (negative = better)")
fig.suptitle("Head-to-head: external registry-λ vs internal funnel selection models\n"
             "(senn2013 sim, matched-coverage; negative wins, positive harms)", fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.96]); fig.savefig(OUT/"fig2_headtohead.png", dpi=150); plt.close(fig)

# ---- Fig 3: external-kappa truth-gate curve (dMCIW0 vs true B), Regime A ----
Bs = sorted({r["B"] for r in TG})
def tgrow(regime, B, m):
    for r in TG:
        if r["regime"] == regime and abs(r["B"]-B) < 1e-6:
            return r["rows"][m]["dmciw0"]
    return None
series = [("oracle", "oracle (=B, upper bound)", BLUE, "--"),
          ("ext_pooled", f"ext_pooled (κ={FR['kappa_pooled']:.3f}, FROZEN)", GREEN, "-"),
          ("fixed0.5", "fixed κ=0.5 (naive)", RED, "-"),
          ("ext_pooled_gated", "ext_pooled + Egger gate", ORANGE, ":")]
fig, ax = plt.subplots(figsize=(6.8, 4.6))
for mk, lab, col, ls in series:
    ys = [tgrow("A", B, mk) for B in Bs]
    ax.plot(Bs, ys, ls, color=col, lw=2, marker="o", ms=4, label=lab)
ax.axhline(0, color="k", lw=1)
ax.axvline(FR["kappa_pooled"], color=GREEN, lw=0.8, ls=":", alpha=0.6)
ax.annotate("κ_pooled", (FR["kappa_pooled"], ax.get_ylim()[1]*0.9), color=GREEN, fontsize=8, rotation=90)
ax.set_xlabel("true selection strength B (unknown in practice)")
ax.set_ylabel("ΔMCIW0 vs unadjusted  (negative = better)")
ax.set_title("Frozen external κ recovers the magnitude\n(matches oracle at B≈0.15; small over-correction at B=0)")
ax.legend(loc="lower left", fontsize=8.5)
fig.tight_layout(); fig.savefig(OUT/"fig3_truthgate.png", dpi=150); plt.close(fig)

print("wrote", ", ".join(p.name for p in sorted(OUT.glob("*.png"))))
