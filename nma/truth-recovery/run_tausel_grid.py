"""run_tausel_grid.py -- AdaptShrink-NMA Phase-4 boundary map.

Full tau x selection-strength x network-size grid, holding everything else at the
dense well-powered headline regime (geom=full, 8-15 studies/edge, homogeneous tau,
effect_sd=0.5). The ONLY things that vary across the 60 cells are the three axes:

  tau       in {0.05, 0.10, 0.20, 0.30}
  selection in {none, moderate, strong}
  n         in {5, 6, 8, 10, 12}      (4..11 basic contrasts)

For every cell we run matched-seed replicates (identical BASE_SEED, so cells differ
only by the axis), then compute -- for adaptshrink_auto vs the netmeta field default
common_DL -- the paired-bootstrap MCIW0 point-efficiency advantage (dMCIW0) and its
robust-win flag, alongside the deployable metrics (bias, coverage, cov uniformity,
ranking). Output is one tidy boundary-map CSV + a full gate JSON.

Cells run in a small process pool (default 3 workers; 4-core box, leave 1 free).

Run: PYTHONPATH=nma python nma/truth-recovery/run_tausel_grid.py --reps 600 --workers 3
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))  # nma/

import nma_sim as S  # noqa: E402
import nma_bakeoff as BK  # noqa: E402

TAUS = [0.05, 0.10, 0.20, 0.30]
SELS = ["none", "moderate", "strong"]
NS = [5, 6, 8, 10, 12]

AUTO = "adaptshrink_auto"
BASE = BK.BASELINE  # common_DL


def cell_id(tau, sel, n):
    return f"t{int(round(tau*100)):02d}_{sel}_n{n}"


def make_spec(tau, sel, n):
    return S.NetSpec(geom="full", n=n, studies_per_comp=(8, 15),
                     hetero="homogeneous", tau_homog=tau, selection=sel,
                     effect_sd=0.5)


def run_cell(payload):
    """Worker: run one grid cell, return a compact result dict (picklable)."""
    tau, sel, n, reps = payload
    cid = cell_id(tau, sel, n)
    t0 = time.time()
    spec = make_spec(tau, sel, n)
    perrep, rankrows = BK.run_replicates(spec, reps, BK.BASE_SEED, BK.NU_DEFAULT,
                                         small_values="undesirable")
    tab = BK.matched_coverage(perrep)
    agg = BK.aggregate_by_method(tab).set_index("method")
    boot = {b["method"]: b for b in BK.bootstrap_vs_baseline(perrep)}
    rank = rankrows.groupby("method").agg(
        spearman=("spearman", "mean"), top1=("top1_correct", "mean"))
    nscored = int(perrep["rep"].nunique())

    def m(method, col):
        return float(agg.loc[method, col]) if method in agg.index else float("nan")

    def rk(method, col):
        return float(rank.loc[method, col]) if method in rank.index else float("nan")

    ba = boot.get(AUTO, {})
    row = {
        "cell": cid, "tau": tau, "selection": sel, "n": n, "ncontrast": n - 1,
        "reps": reps, "nscored": nscored,
        # point-efficiency truth-gate (auto vs field default)
        "dMCIW0": ba.get("mciw0_diff", float("nan")),
        "dMCIW0_lo": ba.get("mciw0_ci_lo", float("nan")),
        "dMCIW0_hi": ba.get("mciw0_ci_hi", float("nan")),
        "MCIW0_robust": bool(ba.get("mciw0_robust_win", False)),
        # own-width interval truth-gate
        "dMCIW": ba.get("mciw_diff", float("nan")),
        "dMCIW_lo": ba.get("mciw_ci_lo", float("nan")),
        "dMCIW_hi": ba.get("mciw_ci_hi", float("nan")),
        "MCIW_robust": bool(ba.get("mciw_robust_win", False)),
        # deployable metrics
        "mciw0_auto": m(AUTO, "mciw0"), "mciw0_DL": m(BASE, "mciw0"),
        "bias_auto": m(AUTO, "bias"), "bias_DL": m(BASE, "bias"),
        "rawcov_auto": m(AUTO, "raw_cov"), "rawcov_DL": m(BASE, "raw_cov"),
        "covunif_auto": m(AUTO, "cov_unif"), "covunif_DL": m(BASE, "cov_unif"),
        "spearman_auto": rk(AUTO, "spearman"), "spearman_DL": rk(BASE, "spearman"),
        "top1_auto": rk(AUTO, "top1"), "top1_DL": rk(BASE, "top1"),
        "secs": round(time.time() - t0, 1),
    }
    row["d_rawcov"] = row["rawcov_auto"] - row["rawcov_DL"]
    # full gate detail for the JSON
    gate = {"cell": cid, "spec": {k: str(v) for k, v in vars(spec).items()},
            "reps": reps, "nscored": nscored,
            "bootstrap_vs_baseline": list(boot.values())}
    return row, gate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=600)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--out-prefix", default=str(HERE / "nma_tausel_grid"))
    ap.add_argument("--only", default="", help="comma cell-ids to restrict (debug)")
    args = ap.parse_args()

    jobs = [(tau, sel, n, args.reps) for tau in TAUS for sel in SELS for n in NS]
    if args.only:
        keep = set(args.only.split(","))
        jobs = [j for j in jobs if cell_id(j[0], j[1], j[2]) in keep]
    print(f"# tau x selection x n grid: {len(jobs)} cells, reps={args.reps}, "
          f"workers={args.workers}")

    t0 = time.time()
    results = []
    with Pool(processes=args.workers) as pool:
        for i, (row, gate) in enumerate(pool.imap_unordered(run_cell, jobs), 1):
            results.append((row, gate))
            flag = "ROBUST" if row["MCIW0_robust"] else ""
            print(f"  [{i:2d}/{len(jobs)}] {row['cell']:18s} "
                  f"dMCIW0={row['dMCIW0']:+.4f} "
                  f"[{row['dMCIW0_lo']:+.4f},{row['dMCIW0_hi']:+.4f}] "
                  f"dcov={row['d_rawcov']:+.3f}  {row['secs']:5.0f}s {flag}")

    rows = [r for r, _ in results]
    gates = {r["cell"]: g for r, g in results}
    df = pd.DataFrame(rows).sort_values(["selection", "tau", "n"]).reset_index(drop=True)
    df.to_csv(f"{args.out_prefix}_map.csv", index=False)
    with open(f"{args.out_prefix}_gates.json", "w") as f:
        json.dump(gates, f, indent=2, default=str)
    secs = round(time.time() - t0, 1)
    print(f"\nWrote {args.out_prefix}_map.csv ({len(df)} cells) and _gates.json "
          f"({secs}s wall)")

    # boundary summary: robust MCIW0 wins
    wins = df[df["MCIW0_robust"]]
    print(f"\n# MCIW0 robust wins: {len(wins)}/{len(df)} cells")
    for sel in SELS:
        sub = df[df["selection"] == sel]
        w = sub[sub["MCIW0_robust"]]
        print(f"  selection={sel:9s}: {len(w):2d}/{len(sub)} robust  "
              f"(taus/ns: {sorted(set(zip(w['tau'], w['n'])))})")


if __name__ == "__main__":
    main()
