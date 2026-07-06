"""Generate manuscript figures FROM committed result files only.

Sources (all committed, branch truth-recovery-misspec):
  fig1: truth-recovery/field2_{c2,l2}_domination_*.csv  (variant dominance)
  fig2: truth-recovery/field2_c2_domination_*.csv        (tau-stratified frontier)
  fig3: truth-recovery/field2_c2_domination_adaptshrink_auto.csv (heatmap)
  fig4: truth-recovery/mc_strong_table.csv               (matched-coverage)
  fig5: manuscript/worked_example.json                   (aspirin forest)
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parent.parent
TR = ROOT / "truth-recovery"
FIG = Path(__file__).resolve().parent / "figures"
FIG.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 150})

C_AUTO = "#1b5e9b"; C_ENS = "#9ecae1"; C_CAL = "#6baed6"; C_PG = "#fdae6b"
C_WIN = "#2c7d46"; C_LOSS = "#c0392b"; C_COVFAIL = "#e8b84b"

def dom(tag, v):
    return pd.read_csv(TR / f"field2_{tag}_domination_{v}.csv")

# ---------- FIG 1: variant dominance, continuous + binary ----------
variants = ["adaptshrink_ens", "adaptshrink_ens_calib", "adaptshrink_petgate", "adaptshrink_auto"]
labels = ["ens", "ens_calib", "petgate", "auto (τ-aware)"]
cont = [int(dom("c2", v)["dominates_field"].sum()) for v in variants]
binr = [int(dom("l2", v)["dominates_field"].sum()) for v in variants]
cont_tot, bin_tot = 54, 36
fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.8))
for ax, vals, tot, title in [(axes[0], cont, cont_tot, "Continuous (SMD) grid"),
                             (axes[1], binr, bin_tot, "Binary / log-OR grid")]:
    cols = [C_ENS, C_CAL, C_PG, C_AUTO]
    bars = ax.bar(labels, vals, color=cols, edgecolor="black", linewidth=0.6)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_ylim(0, tot * 1.12)
    ax.set_ylabel(f"cells dominated (of {tot})")
    ax.set_title(title, fontsize=11)
    for b, val in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, val + tot * 0.015,
                f"{val}/{tot}", ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.tick_params(axis="x", rotation=15)
fig.suptitle("Field-domination at matched coverage: τ-aware AdaptShrink (auto) leads every variant",
             fontsize=11, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(FIG / "fig1_variant_dominance.png", bbox_inches="tight")
plt.close(fig)

# ---------- FIG 2: tau-stratified frontier (continuous) ----------
taus = [0.1, 0.3, 0.5]
def tau_counts(v):
    d = dom("c2", v); g = d.groupby("tau")["dominates_field"].agg(["sum", "count"])
    return [(int(g.loc[t, "sum"]), int(g.loc[t, "count"])) for t in taus]
series = {lab: tau_counts(v) for lab, v in zip(labels, variants)}
x = np.arange(len(taus)); w = 0.2
fig, ax = plt.subplots(figsize=(7.6, 4.2))
cols = [C_ENS, C_CAL, C_PG, C_AUTO]
for i, (lab, col) in enumerate(zip(labels, cols)):
    vals = [s for s, _ in series[lab]]
    bars = ax.bar(x + (i - 1.5) * w, vals, w, label=lab, color=col, edgecolor="black", linewidth=0.5)
    for b, (s, tot) in zip(bars, series[lab]):
        ax.text(b.get_x() + b.get_width() / 2, s + 0.2, str(s), ha="center", va="bottom", fontsize=8)
ax.set_xticks(x); ax.set_xticklabels([f"τ = {t}\n(of {series['auto (τ-aware)'][i][1]} cells)" for i, t in enumerate(taus)])
ax.set_ylabel("cells dominated")
ax.set_title("Moving the no-free-lunch boundary: the high-τ corner (0 → 8/18 at τ = 0.5)", fontsize=11, fontweight="bold")
ax.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.12))
ax.annotate("ens: 0/18", xy=(2 - 1.5 * w, 0.3), xytext=(1.55, 4.5),
            fontsize=8, color=C_LOSS, arrowprops=dict(arrowstyle="->", color=C_LOSS))
ax.annotate("auto: 8/18", xy=(2 + 1.5 * w, 8), xytext=(2.0, 9),
            fontsize=8, color=C_AUTO, fontweight="bold", arrowprops=dict(arrowstyle="->", color=C_AUTO))
fig.tight_layout()
fig.savefig(FIG / "fig2_tau_frontier.png", bbox_inches="tight")
plt.close(fig)

# ---------- FIG 3: dominance heatmap, adaptshrink_auto continuous ----------
d = dom("c2", "adaptshrink_auto").copy()
mus = sorted(d["mu"].unique()); taus3 = sorted(d["tau"].unique())
ks = sorted(d["k"].unique()); mechs = ["none", "step", "copas"]
rows = [(mu, t) for mu in mus for t in taus3]
cols2 = [(k, m) for k in ks for m in mechs]
M = np.full((len(rows), len(cols2)), np.nan)
txt = np.empty((len(rows), len(cols2)), dtype=object)
for i, (mu, t) in enumerate(rows):
    for j, (k, m) in enumerate(cols2):
        r = d[(d.mu == mu) & (d.tau == t) & (d.k == k) & (d.mechanism == m)]
        if len(r):
            r = r.iloc[0]
            if bool(r["dominates_field"]):
                M[i, j] = 2
            elif r["n_loss"] > 0:
                M[i, j] = 0
            else:
                M[i, j] = 1
            txt[i, j] = f"{r['raw_cov']:.2f}"
        else:
            txt[i, j] = ""
from matplotlib.colors import ListedColormap
cmap = ListedColormap([C_LOSS, C_COVFAIL, C_WIN])
fig, ax = plt.subplots(figsize=(8.4, 5.4))
ax.imshow(M, cmap=cmap, vmin=0, vmax=2, aspect="auto")
ax.set_xticks(range(len(cols2)))
ax.set_xticklabels([f"k={k}\n{m}" for k, m in cols2], fontsize=8)
ax.set_yticks(range(len(rows)))
ax.set_yticklabels([f"μ={mu}, τ={t}" for mu, t in rows], fontsize=8)
for i in range(len(rows)):
    for j in range(len(cols2)):
        if txt[i, j]:
            ax.text(j, i, txt[i, j], ha="center", va="center", fontsize=7.5, color="white")
ax.set_title("adaptshrink_auto per-cell verdict (continuous grid); cell text = deployable coverage",
             fontsize=10.5, fontweight="bold")
legend = [Patch(facecolor=C_WIN, label="dominates field"),
          Patch(facecolor=C_COVFAIL, label="narrower/tied but deployable cov <0.90"),
          Patch(facecolor=C_LOSS, label="loses ≥1 comparator")]
ax.legend(handles=legend, frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3)
fig.tight_layout()
fig.savefig(FIG / "fig3_auto_heatmap.png", bbox_inches="tight")
plt.close(fig)

# ---------- FIG 4: matched-coverage efficiency (strong, k=40) ----------
t = pd.read_csv(TR / "mc_strong_table.csv")
order = ["adaptshrink", "ubcma", "trim_and_fill", "pet_peese", "copas", "reml_hksj"]
disp = {"adaptshrink": "AdaptShrink", "ubcma": "UBCMA", "trim_and_fill": "trim&fill",
        "pet_peese": "PET-PEESE", "copas": "Copas-Shi (HC)", "reml_hksj": "REML-HKSJ"}
mechs4 = ["smooth", "step", "copas"]
fig, axes = plt.subplots(1, 3, figsize=(11.5, 4.0), sharey=True)
for ax, mech in zip(axes, mechs4):
    sub = t[t.mechanism == mech].set_index("method")
    vals = [sub.loc[m, "mciw0"] for m in order]
    covs = [sub.loc[m, "raw_cov"] for m in order]
    cols = [C_AUTO if m == "adaptshrink" else "#bbbbbb" for m in order]
    y = np.arange(len(order))
    ax.barh(y, vals, color=cols, edgecolor="black", linewidth=0.5)
    ax.set_yticks(y); ax.set_yticklabels([disp[m] for m in order], fontsize=8.5)
    ax.invert_yaxis()
    ax.set_title(f"mechanism = {mech}", fontsize=10)
    ax.set_xlabel("MCIW0 (matched-cov width, lower=better)")
    for yi, (v, c) in enumerate(zip(vals, covs)):
        ax.text(v + 0.005, yi, f"cov {c:.2f}", va="center", fontsize=7.5,
                color=(C_WIN if c >= 0.90 else C_LOSS))
axes[0].set_ylabel("")
fig.suptitle("Matched-coverage efficiency vs deployable coverage (strong selection, μ=0.2, τ=0.1, k=40, 300 reps)",
             fontsize=10.5, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(FIG / "fig4_matched_coverage.png", bbox_inches="tight")
plt.close(fig)

# ---------- FIG 5: aspirin worked-example forest ----------
we = json.loads((Path(__file__).resolve().parent / "worked_example.json").read_text())
studies = we["studies"]
mlist = [("dl_hksj", "DerSimonian-Laird (HKSJ)"), ("reml_hksj", "REML (HKSJ)"),
         ("pet_peese", "PET-PEESE"), ("trim_and_fill", "Trim-and-fill"),
         ("copas", "Copas-Shi"), ("henmi_copas", "Henmi-Copas (metafor::hc)"),
         ("ubcma", "UBCMA"), ("adaptshrink_petgate", "AdaptShrink petgate"),
         ("adaptshrink_ens_calib", "AdaptShrink ens_calib"),
         ("adaptshrink_auto", "AdaptShrink auto")]
rows_y = []; ylabels = []; yy = 0
fig, ax = plt.subplots(figsize=(8.2, 6.6))
# studies
for s in studies:
    lo = s["yi"] - 1.96 * s["sei"]; hi = s["yi"] + 1.96 * s["sei"]
    ax.plot([lo, hi], [yy, yy], color="#888", lw=1.2)
    ax.plot(s["yi"], yy, "s", color="#444", ms=5)
    ylabels.append(s["id"]); rows_y.append(yy); yy -= 1
yy -= 0.6
ax.axhline(yy + 0.3, color="#ccc", lw=0.8)
for key, lab in mlist:
    m = we["methods"][key]
    if not np.isfinite(m["ci_low"]) or not np.isfinite(m["ci_high"]):
        ax.plot(m["mu"], yy, "D", color=C_LOSS, ms=6)
    else:
        is_as = key.startswith("adaptshrink")
        col = C_AUTO if key == "adaptshrink_auto" else ("#2c7d46" if is_as else "#333")
        ax.plot([m["ci_low"], m["ci_high"]], [yy, yy], color=col, lw=2.0 if key == "adaptshrink_auto" else 1.4)
        ax.plot(m["mu"], yy, "D", color=col, ms=7 if key == "adaptshrink_auto" else 5)
        ax.text(0.62, yy, f"{m['mu']:+.3f} [{m['ci_low']:+.3f}, {m['ci_high']:+.3f}]",
                va="center", fontsize=7.8, fontweight="bold" if key == "adaptshrink_auto" else "normal")
    ylabels.append(lab); rows_y.append(yy); yy -= 1
ax.axvline(0, color="red", ls="--", lw=0.8)
ax.set_yticks(rows_y); ax.set_yticklabels(ylabels, fontsize=8.5)
ax.set_xlabel("log odds ratio (negative = protective)")
ax.set_xlim(-0.65, 1.15)
ax.set_title("Worked example: aspirin secondary-prevention (k=6, real data)\nτ̂(DL)=%.3f → auto selects ens_calib; funnel-asymmetry t=%.2f"
             % (we["tau_hat_DL"], we["pet_t1"]), fontsize=10, fontweight="bold")
ax.text(0.62, max(rows_y) + 0.4, "pooled estimate [95% CI]", fontsize=7.8, style="italic")
fig.tight_layout()
fig.savefig(FIG / "fig5_aspirin_forest.png", bbox_inches="tight")
plt.close(fig)

print("wrote:", *(p.name for p in sorted(FIG.glob("*.png"))))
