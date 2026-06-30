"""PILOT-3 figure: (A) the transport regime (population obesity of donor trials vs
single-country targets), (B) calibrated beta-sweep crossover (method is correct),
(C) real-data verdict (relevance beats NMA; transport does NOT beat relevance)."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = [r for r in json.load(open("trials_transport.json")) if r["pop_ob"] is not None]
sim = json.load(open("sim_transport_results.json"))
loo = json.load(open("pilot3_loo_summary.json"))

fig, ax = plt.subplots(1, 3, figsize=(15, 4.6))

# A: obesity regime
donors = [r["pop_ob"] for r in R if not r["single_country"]]
tg = [(r["pop_ob"], r["target_country"], r["active"]) for r in R if r["single_country"]]
ax[0].hist(donors, bins=12, color="#bbb", alpha=.8, label="donor trials (country-mix)")
for ob, c, cls in tg:
    col = "#1f77b4" if ob < 15 else "#d62728"
    ax[0].axvline(ob, color=col, lw=1.4, alpha=.7)
ax[0].axvline(np.median([r["pop_ob"] for r in R]), color="k", ls="--", lw=2, label="donor median")
ax[0].set_xlabel("population adult obesity prevalence (%)")
ax[0].set_ylabel("# trials")
ax[0].set_title("A. Transport regime: single-country targets\n(blue=Asian low-ob, red=US high-ob) are FAR from donors")
ax[0].legend(fontsize=8)

# B: beta sweep
betas = sorted(float(k) for k in sim["sweep"])
mae_rel = [sim["sweep"][str(b)]["mae"]["relevance"] for b in betas]
mae_trn = [sim["sweep"][str(b)]["mae"]["transport"] for b in betas]
mae_nma = [sim["sweep"][str(b)]["mae"]["nma"] for b in betas]
ax[1].plot(betas, mae_nma, "o-", color="#999", label="standard NMA")
ax[1].plot(betas, mae_rel, "s-", color="#2ca02c", label="relevance-only")
ax[1].plot(betas, mae_trn, "^-", color="#d62728", label="relevance x transport")
ax[1].axvline(0.006, color="k", ls=":", lw=1.5)
ax[1].annotate("real beta\n(0.006)", (0.006, 1.2), fontsize=8, ha="left")
ax[1].set_xlabel("true obesity effect-modification slope  beta (HbA1c % per obesity %)")
ax[1].set_ylabel("MAE to known truth")
ax[1].set_title("B. Calibrated sim (known truth): method IS correct\ntransport flat; relevance fails as beta grows. Real beta -> inert")
ax[1].legend(fontsize=8)

# C: real-data contrasts
br = loo["by_regime"]["ALL (Asian targets)"] if "ALL (Asian targets)" in loo["by_regime"] else loo["by_regime"]["ALL"]
contrasts = [("relevance\n- NMA", br["relevance_vs_nma"]),
             ("transport\n- relevance", br["transport_vs_relevance"]),
             ("transport\n- scrambled", br["transport_vs_scrambled"])]
ys = np.arange(len(contrasts))[::-1]
for yv, (lab, vals) in zip(ys, contrasts):
    d, lo, hi = vals[0], vals[1], vals[2]
    col = "#2ca02c" if hi < 0 else "#888"
    ax[2].plot([lo, hi], [yv, yv], color=col, lw=3)
    ax[2].plot(d, yv, "o", color=col, ms=8)
ax[2].axvline(0, color="k", lw=1)
ax[2].set_yticks(ys); ax[2].set_yticklabels([c[0] for c in contrasts], fontsize=9)
ax[2].set_xlabel("delta MAE on REAL held-out effects  (<0 = first method better)")
ax[2].set_title("C. REAL data verdict (n=12 LOO)\nrelevance beats NMA (green); transport ~ relevance (n.s.)")

plt.tight_layout()
plt.savefig("fig_borrowing_pilot3.png", dpi=130)
print("wrote fig_borrowing_pilot3.png")
