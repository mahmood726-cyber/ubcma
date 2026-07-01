"""Figure: registry-scale field vs the MODERN frontier."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = json.load(open("benchmark_results.json"))
b1 = {r["method"]: r for r in R["B1"]}
cal = {r["method"]: r for r in R["conformal"]}
b2 = R["B2"]

fig, ax = plt.subplots(1, 3, figsize=(15, 4.4))

# A: B1 MAE
order = ["global", "gmodel", "field_hand", "withinMA", "hier_crossMA", "robust_map", "gp_field"]
lbl = {"global": "no-borrow\n(global)", "gmodel": "g-modeling\nEB", "field_hand": "hand field\n(AdaptShrink)",
       "withinMA": "within-MA", "hier_crossMA": "hier.\ncross-MA", "robust_map": "robust\nMAP", "gp_field": "GP learned\nkernel"}
maes = [b1[m]["MAE"] for m in order]
cols = ["#999999", "#999999", "#c44", "#1f77b4", "#2a9", "#2a9", "#2ca02c"]
ax[0].bar(range(len(order)), maes, color=cols)
ax[0].axhline(b1["withinMA"]["MAE"], ls="--", color="#1f77b4", lw=0.8)
ax[0].set_xticks(range(len(order))); ax[0].set_xticklabels([lbl[m] for m in order], fontsize=8)
ax[0].set_ylabel("held-out MAE"); ax[0].set_ylim(0.22, 0.34)
ax[0].set_title("A. Reconstruction error (modern comparators)\nGP learned kernel beats within-MA")
for i, v in enumerate(maes):
    ax[0].text(i, v + 0.002, f"{v:.3f}", ha="center", fontsize=7)

# B: conformal vs model coverage
methods = order
mcov = [b1[m]["cover"] for m in methods]
ccov = [cal[m]["conf_cover"] for m in methods]
x = np.arange(len(methods))
ax[1].plot(x, mcov, "o-", color="#c44", label="model-based PI")
ax[1].plot(x, ccov, "s-", color="#2ca02c", label="conformal / jackknife+")
ax[1].axhline(0.90, ls="--", color="k", lw=0.8, label="nominal 90%")
ax[1].set_xticks(x); ax[1].set_xticklabels([lbl[m].replace("\n", " ") for m in methods], rotation=40, ha="right", fontsize=7)
ax[1].set_ylabel("empirical coverage"); ax[1].set_ylim(0.6, 1.02)
ax[1].legend(fontsize=8, frameon=False)
ax[1].set_title("B. Calibration: conformal restores\nnominal coverage for every method")

# C: B2 dynamic borrowing at m=1
mm = ["own_only", "precision_fuse", "sam", "commensurate", "robust_map", "power_prior"]
mlbl = {"own_only": "own only\n(no borrow)", "precision_fuse": "precision\nfusion (ours)",
        "sam": "SAM", "commensurate": "commens.", "robust_map": "robust\nMAP", "power_prior": "power\nprior"}
vals = [b2["1"][m] for m in mm]
c2 = ["#999999", "#c44", "#88b", "#88b", "#88b", "#2ca02c"]
ax[2].bar(range(len(mm)), vals, color=c2)
ax[2].set_xticks(range(len(mm))); ax[2].set_xticklabels([mlbl[m] for m in mm], fontsize=8)
ax[2].set_ylabel("held-out MAE (m=1 sibling)"); ax[2].set_ylim(0.33, 0.39)
ax[2].set_title("C. Dynamic borrowing at the sparse frontier\nmodern priors beat our precision fusion")
for i, v in enumerate(vals):
    ax[2].text(i, v + 0.001, f"{v:.3f}", ha="center", fontsize=7)

fig.suptitle("Registry-scale borrowing field benchmarked against the modern frontier "
             "(GP kernel · robust-MAP · hierarchical Bayes · power/commensurate/SAM · conformal)",
             fontsize=11, y=1.03)
fig.tight_layout()
fig.savefig("fig_field_modern.png", dpi=140, bbox_inches="tight")
print("wrote fig_field_modern.png")
