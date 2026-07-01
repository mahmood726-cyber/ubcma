"""run_full_grid.py -- run the AdaptShrink-NMA matched-coverage bake-off across
the whole grid and consolidate into one map (one row per cell x method).

Seeded and reproducible: each cell uses nma_bakeoff.run_replicates with the fixed
BASE_SEED. Writes nma_full_grid_map.csv (summary metrics + bootstrap MCIW0/MCIW
robustness vs the field default) and nma_full_grid_gates.json (full gate detail).

Run: PYTHONPATH=nma python nma/truth-recovery/run_full_grid.py --reps 500
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import nma_bakeoff as BK  # noqa: E402

# headline selection cells get more reps for a tight bootstrap CI
REPS_OVERRIDE = {"select_strong_dense_n6": 800, "select_strong_dense": 600}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=500)
    ap.add_argument("--out-prefix", default="nma/truth-recovery/nma_full_grid")
    args = ap.parse_args()

    rows = []
    gates = {}
    for cell, spec in BK.CELLS.items():
        reps = REPS_OVERRIDE.get(cell, args.reps)
        sv = "undesirable"
        t0 = time.time()
        perrep, rankrows = BK.run_replicates(spec, reps, BK.BASE_SEED,
                                             BK.NU_DEFAULT, small_values=sv)
        tab = BK.matched_coverage(perrep)
        agg = BK.aggregate_by_method(tab)
        boot = {b["method"]: b for b in BK.bootstrap_vs_baseline(perrep)}
        rank = rankrows.groupby("method").agg(
            spearman=("spearman", "mean"), top1=("top1_correct", "mean"))
        nscored = int(perrep["rep"].nunique())
        for _, a in agg.iterrows():
            m = a["method"]
            b = boot.get(m, {})
            rows.append({
                "cell": cell, "geom": spec.geom, "n": spec.n,
                "studies": str(spec.studies_per_comp), "hetero": spec.hetero,
                "selection": spec.selection, "inconsistency": spec.inconsistency,
                "multiarm": spec.multiarm_frac, "reps": reps, "nscored": nscored,
                "method": m, "abs_bias": a["bias"], "raw_cov": a["raw_cov"],
                "cov_unif": a["cov_unif"], "mciw": a["mciw"], "mciw0": a["mciw0"],
                "spearman": float(rank.loc[m, "spearman"]) if m in rank.index else np.nan,
                "top1": float(rank.loc[m, "top1"]) if m in rank.index else np.nan,
                "dMCIW0": b.get("mciw0_diff", np.nan),
                "MCIW0_robust_win": b.get("mciw0_robust_win", False),
                "dMCIW": b.get("mciw_diff", np.nan),
                "MCIW_robust_win": b.get("mciw_robust_win", False),
            })
        gates[cell] = {"spec": {k: str(v) for k, v in vars(spec).items()},
                       "reps": reps, "nscored": nscored,
                       "bootstrap_vs_baseline": list(boot.values())}
        secs = round(time.time() - t0, 1)
        print(f"  {cell:24s} reps={reps:4d} scored={nscored:4d}  ({secs}s)")

    df = pd.DataFrame(rows)
    df.to_csv(f"{args.out_prefix}_map.csv", index=False)
    with open(f"{args.out_prefix}_gates.json", "w") as f:
        json.dump(gates, f, indent=2, default=str)
    print(f"\nWrote {args.out_prefix}_map.csv ({len(df)} rows) and _gates.json")

    # console summary: robust wins for the integrated estimator
    au = df[df["method"] == "adaptshrink_auto"]
    print("\n# adaptshrink_auto vs field default (common_DL) per cell:")
    print(f"{'cell':24s}{'raw_cov':>8}{'(DL)':>8}{'cov_unif':>9}{'MCIW0':>8}"
          f"{'dMCIW0':>9}{'robust':>8}")
    dl = df[df["method"] == "common_DL"].set_index("cell")
    for _, r in au.iterrows():
        c = r["cell"]
        print(f"{c:24s}{r['raw_cov']:>8.3f}{dl.loc[c,'raw_cov']:>8.3f}"
              f"{r['cov_unif']:>9.3f}{r['mciw0']:>8.4f}{r['dMCIW0']:>+9.4f}"
              f"{str(r['MCIW0_robust_win']):>8}")


if __name__ == "__main__":
    main()
