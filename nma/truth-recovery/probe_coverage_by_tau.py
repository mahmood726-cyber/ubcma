"""probe_coverage_by_tau.py -- the clearest evidence for AdaptShrink-NMA's
deployable-coverage win: per-direct-comparison coverage split by that edge's
TRUE tau, in a sparse star where direct edges get little indirect support.

Common-tau^2 (the field default) uses one heterogeneity for every comparison, so
it OVER-covers low-tau edges (intervals too wide) and UNDER-covers high-tau edges
(intervals too narrow for the real heterogeneity). AdaptShrink-NMA shrinks each
edge's own DL tau^2 toward the common one by data/geometry, tightening low-tau
intervals and widening high-tau ones -> coverage closer to nominal on BOTH bands.

Truth-first: seeded; writes nma/truth-recovery/probe_coverage_by_tau.csv. No
oracle is used -- this is the deployable (kappa=1) interval a practitioner gets.

Run: PYTHONPATH=nma python nma/truth-recovery/probe_coverage_by_tau.py --reps 300
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # nma/
import nma_sim as S  # noqa: E402
from nma_core import fit_nma  # noqa: E402
from adaptshrink_nma import adaptshrink_nma  # noqa: E402

Z = 1.959963984540054
BASE_SEED = 20260621


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=300)
    ap.add_argument("--tau-high", type=float, default=0.40)
    ap.add_argument("--out", default="nma/truth-recovery/probe_coverage_by_tau.csv")
    args = ap.parse_args()

    spec = S.NetSpec(geom="star", n=6, studies_per_comp=(3, 5),
                     hetero="heterogeneous", tau_low=0.05, tau_high=args.tau_high,
                     multiarm_frac=0.0, selection="none")
    methods = {
        "common_DL": lambda c: fit_nma(c, random=True),
        "adaptshrink": lambda c: adaptshrink_nma(c, nu=4.0),
        "comp_specific": lambda c: adaptshrink_nma(c, nu=0.0),
    }
    acc = {m: {"low": [0, 0, []], "high": [0, 0, []]} for m in methods}
    for r in range(args.reps):
        comps, d_true, type_tau = S.generate(spec, BASE_SEED + r)
        treats = sorted({c.t1 for c in comps} | {c.t2 for c in comps})
        if len(treats) < spec.n:
            continue
        for mname, fn in methods.items():
            fit = fn(comps)
            tidx = fit.meta["tidx"]
            for leaf in range(1, spec.n):
                typ = frozenset((0, leaf))
                if typ not in type_tau:
                    continue
                band = "low" if type_tau[typ] < 0.2 else "high"
                a, b = "0", str(leaf)
                if a not in tidx or b not in tidx:
                    continue
                dh = fit.TE[tidx[b], tidx[a]]
                se = fit.seTE[tidx[b], tidx[a]]
                true = d_true[leaf] - d_true[0]
                cov = int(dh - Z * se <= true <= dh + Z * se)
                acc[mname][band][0] += cov
                acc[mname][band][1] += 1
                acc[mname][band][2].append(2 * Z * se)

    rows = []
    for m in methods:
        for band in ("low", "high"):
            c, nrec, widths = acc[m][band]
            rows.append({"method": m, "tau_band": band,
                         "true_tau": spec.tau_low if band == "low" else args.tau_high,
                         "coverage": round(c / nrec, 4), "mean_width": round(float(np.mean(widths)), 4),
                         "n": nrec})
    out = pd.DataFrame(rows)
    out.to_csv(args.out, index=False)

    print(f"# Deployable coverage of DIRECT hub-leaf comparisons, by edge true tau")
    print(f"# star n={spec.n}, studies{spec.studies_per_comp}, tau_low={spec.tau_low} "
          f"tau_high={args.tau_high}, reps={args.reps} (no oracle, kappa=1)\n")
    print(f"{'method':<15}{'tau_band':>10}{'coverage':>10}{'mean_width':>12}")
    for _, x in out.iterrows():
        print(f"{x['method']:<15}{x['tau_band']:>10}{x['coverage']:>10.3f}{x['mean_width']:>12.3f}")
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
