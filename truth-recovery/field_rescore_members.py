"""field_rescore_members.py -- test alternative AdaptShrink ensembles, no re-sim.

The explicit gate (field_rescore_gated.py) failed: a per-rep selection signal is
confounded by heterogeneity. A cleaner idea exploits the robust disagreement-
penalised weighting we already use: ADD the efficient RE estimator as an ensemble
member. Then under no-selection / high-tau (all methods agree) RE keeps weight and
the ensemble is efficient; under selection RE is the upward outlier and the
disagreement penalty w_j = 1/(se_j^2 + (mu_j-median)^2) down-weights it
automatically -- gating without a gate.

Every candidate ensemble is rebuilt from members already saved per-replicate in
field_<tag>_perrep.csv (reml_hksj, pet_peese, trim_and_fill, ubcma, vevea_hedges,
p_uniform_star, ...), so member sets can be swept instantly and re-run through the
exact field-domination truth-gate before any fresh simulation.

Usage:
    PYTHONPATH=src python truth-recovery/field_rescore_members.py --tag v1
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import field_bakeoff as F  # noqa: E402

Z975 = 1.959963984540054
OUT = Path("truth-recovery")
CELL_KEYS = F.CELL_KEYS

CANDIDATES = {
    "ens_base": ("ubcma", "pet_peese", "trim_and_fill"),                       # current
    "ens_re":   ("ubcma", "pet_peese", "trim_and_fill", "reml_hksj"),          # +RE
    "ens_re_vev": ("ubcma", "pet_peese", "trim_and_fill", "reml_hksj", "vevea_hedges"),
    "ens_modern": ("ubcma", "pet_peese", "reml_hksj", "vevea_hedges", "p_uniform_star"),
    "ens_re_noTF": ("ubcma", "pet_peese", "reml_hksj"),                        # +RE, drop TF
    "ens_full": ("ubcma", "pet_peese", "trim_and_fill", "reml_hksj",
                 "vevea_hedges", "p_uniform_star", "henmi_copas"),
}


def build_ensemble(raw: pd.DataFrame, members, name: str) -> pd.DataFrame:
    """Rebuild a robust-average ensemble per (cell,rep) from saved members."""
    key = CELL_KEYS + ["rep"]
    tabs = {}
    for m in members:
        t = raw[raw.method == m].set_index(key)
        tabs[m] = t
    # align on the intersection of all members' rows
    idx = None
    for t in tabs.values():
        idx = t.index if idx is None else idx.intersection(t.index)
    rows = []
    truemu = tabs[members[0]].loc[idx, "true_mu"]
    for pos, k in enumerate(idx):
        precomp = {}
        for m in members:
            r = tabs[m].loc[k]
            mu, lo, hi, conv = r["mu_hat"], r["ci_low"], r["ci_high"], r["converged"]
            if conv and np.isfinite(mu) and np.isfinite(lo) and np.isfinite(hi):
                se = (hi - lo) / 2.0 / Z975
                if np.isfinite(se) and se > 0:
                    precomp[m] = (mu, se)
        ens = F._robust_avg(precomp)
        rows.append((k, ens))
    out = pd.DataFrame([dict(zip(CELL_KEYS + ["rep"], k),
                             method=name, true_mu=float(truemu.loc[k]),
                             mu_hat=e["mu"], ci_low=e["ci_low"], ci_high=e["ci_high"],
                             converged=bool(e["converged"]))
                        for k, e in rows])
    return out


def evaluate(raw, name, members):
    gated = build_ensemble(raw, members, name)
    aug = pd.concat([raw, gated], ignore_index=True)
    score = F.score_tables(aug)
    pair = F.bootstrap_pairwise(aug, name)
    dom = F.field_domination(score, pair, name)
    nd = int(dom["dominates_field"].sum())
    nloss = int((dom["n_loss"] > 0).sum())
    sc = score[score.method == name]
    mean_cov = float(sc["raw_cov"].mean())
    under = int((sc["raw_cov"] < 0.80).sum())
    tau_lo = int(dom[dom.tau <= 0.1]["dominates_field"].sum())
    tau_hi = int(dom[dom.tau == 0.3]["dominates_field"].sum())
    return {"name": name, "dom": nd, "loss_cells": nloss, "tau_lo": tau_lo,
            "tau_hi": tau_hi, "mean_cov": mean_cov, "under": under,
            "dom_df": dom, "score": sc}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="v1")
    ap.add_argument("--best", default=None,
                    help="if set, write per-cell domination CSV for this candidate")
    args = ap.parse_args()
    raw = pd.read_csv(OUT / f"field_{args.tag}_perrep.csv")
    print(f"{'candidate':<14}{'dom/54':>8}{'loss':>6}{'tau<=.1':>9}{'tau=.3':>8}"
          f"{'cov':>7}{'under':>7}")
    results = {}
    for name, members in CANDIDATES.items():
        r = evaluate(raw, name, members)
        results[name] = r
        print(f"{name:<14}{r['dom']:>6}/54{r['loss_cells']:>6}"
              f"{r['tau_lo']:>6}/36{r['tau_hi']:>6}/18{r['mean_cov']:>7.3f}{r['under']:>7}")
    if args.best and args.best in results:
        r = results[args.best]
        r["dom_df"].to_csv(OUT / f"field_{args.tag}_domination_{args.best}.csv", index=False)
        print(f"\nwrote field_{args.tag}_domination_{args.best}.csv")


if __name__ == "__main__":
    main()
