"""Replication figure: per-slice relevance-vs-null advantage by tier + pooled estimate."""
import json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
res = json.load(open("loo_results_v2.json"))

SHORT = {
 "T2DM_HbA1c_GLP1only:ALL:dose": "GLP1 dose -> HbA1c  (anchor)",
 "Obesity_weight:ALL:baseline": "GLP1 baseline-wt -> weight  (NEW)",
 "Obesity_weight:tirzepatide:dose": "tirzepatide dose -> weight",
 "Obesity_weight:ALL:dose": "GLP1 dose -> weight",
 "Depression:vortioxetine:dose": "vortioxetine dose -> MADRS",
 "T2DM_HbA1c:dapagliflozin:dose": "dapagliflozin dose -> HbA1c",
 "T2DM_HbA1c:ALL:dose": "cross-class dose -> HbA1c",
}
TIERCOL = {"clean": "#1a7a3a", "nearmiss": "#c8851a", "flat": "#888888"}
order = ["clean", "nearmiss", "flat"]
rows = sorted(res.items(), key=lambda kv: (order.index(kv[1].get("tier","flat")), kv[0]))

fig, ax = plt.subplots(figsize=(9.2, 5.4))
ys = []
for i, (lab, r) in enumerate(rows):
    c = r["central"]
    # scale-free fractional advantage vs uniform
    f = c["d_rel_uni"]/c["mae_uni"]
    lo = c["ci_rel_uni"][0]/c["mae_uni"]; hi = c["ci_rel_uni"][1]/c["mae_uni"]
    y = len(rows)-i
    ys.append((y, lab))
    col = TIERCOL[r.get("tier","flat")]
    ax.plot([lo, hi], [y, y], color=col, lw=2.2, zorder=2)
    ax.scatter([f], [y], color=col, s=70, zorder=3,
               marker=("o" if r["beats_both"] else "x"))
    ax.text(0.34, y, SHORT.get(lab, lab), va="center", fontsize=9)
    ax.text(0.34, y-0.32, f"n={r['n']}, tier={r.get('tier')}, beats both={'YES' if r['beats_both'] else 'no'}",
            va="center", fontsize=7, color="#555")
ax.axvline(0, color="k", lw=0.8, ls="--")
# pooled clean vs uniform
clean = [r for _,r in res.items() if r.get("tier")=="clean"]
fr = [r["central"]["d_rel_uni"]/r["central"]["mae_uni"] for r in clean]
se = [((r["central"]["ci_rel_uni"][1]-r["central"]["ci_rel_uni"][0])/(2*1.96))/r["central"]["mae_uni"] for r in clean]
w = 1/np.array(se)**2; mu = (w*np.array(fr)).sum()/w.sum()
Q = (w*(np.array(fr)-mu)**2).sum(); c0 = w.sum()-(w**2).sum()/w.sum()
tau2 = max(0,(Q-(len(fr)-1))/c0); w2 = 1/(np.array(se)**2+tau2)
mu2 = (w2*np.array(fr)).sum()/w2.sum(); sem = np.sqrt(1/w2.sum())
ax.plot([mu2-1.96*sem, mu2+1.96*sem], [0.2,0.2], color="#0a4", lw=3, zorder=2)
ax.scatter([mu2],[0.2], marker="D", color="#0a4", s=90, zorder=3)
ax.text(0.34, 0.2, f"POOLED (clean, N=2): {mu2:+.0%} [{mu2-1.96*sem:+.0%},{mu2+1.96*sem:+.0%}]",
        va="center", fontsize=8.5, fontweight="bold", color="#0a4")
ax.set_xlim(-0.7, 0.33)
ax.set_ylim(-0.4, len(rows)+0.6)
ax.set_yticks([])
ax.set_xlabel("Fractional MAE change of relevance vs no-relevance (uniform) null\n"
              "(left = relevance better; o = beats both nulls, x = does not)")
ax.set_title("Borrowing-field replication across AACT slices (real leave-one-trial-out)", fontsize=11)
for t,c in TIERCOL.items():
    ax.scatter([],[],color=c,label=t)
ax.legend(loc="lower left", fontsize=8, frameon=False)
plt.tight_layout()
plt.savefig("fig_borrowing_replication.png", dpi=130)
print("wrote fig_borrowing_replication.png")
