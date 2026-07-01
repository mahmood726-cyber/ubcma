"""Figure: registry-scale borrowing field -- the sparse-frontier crossover."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ds = json.load(open("downsample_results.json"))
ms = sorted(int(k) for k in ds)
within = [ds[str(m)]["within"] for m in ms]
field = [ds[str(m)]["field"] for m in ms]
delta = [ds[str(m)]["delta"] for m in ms]
lo = [ds[str(m)]["lo"] for m in ms]
hi = [ds[str(m)]["hi"] for m in ms]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))

ax1.plot(ms, within, "o-", color="#1f77b4", label="within-MA only")
ax1.plot(ms, field, "s-", color="#d62728", label="cross-MA field (home-anchored)")
ax1.set_xlabel("home-MA siblings retained (m)")
ax1.set_ylabel("mean |held-out reconstruction error|")
ax1.set_title("A. Reconstruction error vs home richness")
ax1.legend(frameon=False, fontsize=9)
ax1.set_xticks(ms)
ax1.grid(alpha=0.25)

col = ["#2ca02c" if l > 0 else "#d62728" for l in lo]
ax2.bar(range(len(ms)), delta, color=col, alpha=0.85)
ax2.errorbar(range(len(ms)), delta, yerr=[np.array(delta)-np.array(lo),
             np.array(hi)-np.array(delta)], fmt="none", ecolor="k", capsize=4)
ax2.axhline(0, color="k", lw=0.8)
ax2.set_xticks(range(len(ms))); ax2.set_xticklabels(ms)
ax2.set_xlabel("home-MA siblings retained (m)")
ax2.set_ylabel("within - field  (>0 = field helps)")
ax2.set_title("B. Field advantage: real only at m=1 (single sibling)")
ax2.annotate("field HELPS\n(starved home)", (0, delta[0]), textcoords="offset points",
             xytext=(18, -6), fontsize=8, color="#2ca02c")
ax2.annotate("field HARMS once >=2 siblings", (2, delta[2]),
             textcoords="offset points", xytext=(-10, -28), fontsize=8, color="#d62728")

fig.suptitle("Registry-scale borrowing field: cross-MA borrowing helps only at the sparse frontier",
             fontsize=11, y=1.02)
fig.tight_layout()
fig.savefig("fig_field.png", dpi=140, bbox_inches="tight")
print("wrote fig_field.png")
