"""Forest plot of the expansion: per-slice + pooled transport-vs-relevance and the
settled headlines (transport-vs-NMA, relevance-vs-uniform) at the pre-registered central bw."""
import json, io, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
R = json.load(open(HERE / "aggregate_results.json"))["central"]

panels = [("tran_rel", "TRANSPORT - relevance\n(incremental g-computation step)"),
          ("tran_nma", "TRANSPORT - NMA\n(full method vs textbook)"),
          ("rel_unif", "relevance - uniform\n(kernel vs no-relevance)")]
fig, axes = plt.subplots(1, 3, figsize=(13, 3.4), sharex=False)
for ax, (pair, title) in zip(axes, panels):
    r = R[pair]
    rows = []
    for name, m, se, k in r["per_slice"]:
        rows.append((f"{name}  (k={k})", m, m - 1.96 * se, m + 1.96 * se, "#4477aa"))
    iv_mu, iv_se, iv_lo, iv_hi = r["iv"]
    rows.append(("POOLED (inv-var)", iv_mu, iv_lo, iv_hi, "#cc3311"))
    ys = np.arange(len(rows))[::-1]
    for y, (lab, m, lo, hi, col) in zip(ys, rows):
        ax.plot([lo, hi], [y, y], color=col, lw=2.4)
        ax.plot(m, y, "o", color=col, ms=7 if "POOLED" in lab else 5)
    ax.axvline(0, color="#888", ls="--", lw=1)
    ax.set_yticks(ys); ax.set_yticklabels([r[0] for r in rows], fontsize=8)
    ax.set_title(title, fontsize=9)
    ax.set_xlabel("paired MAE difference (logRR)", fontsize=8)
    ax.tick_params(labelsize=8)
fig.suptitle("Borrowing expansion: transportability & relevance pooled across BCG (latitude) + Rotavirus (U5MR), k=42  "
             "[central bw]", fontsize=10)
fig.tight_layout(rect=[0, 0, 1, 0.94])
out = HERE / "fig_expansion_forest.png"
fig.savefig(out, dpi=140)
print("wrote", out)
