"""grid_independent.py -- harness-INDEPENDENT recompute of the grid MCIW0 +
paired-bootstrap robust-win test, straight from the gridcell_*_perrep.csv files.

Does NOT import nma_bakeoff / nma_core. Re-implements the metric + bootstrap from
the spec, as a fourth (internal) cross-check of the grid map and a reference for the
external vendors. Writes result_claude_grid.json.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

GRID = Path(__file__).resolve().parent / "grid"
TARGET = 0.95
B = 2000
AUTO, BASE = "adaptshrink_auto", "common_DL"


def err_matrix(df, method, reps, contrasts):
    sub = df[df["method"] == method]
    piv = sub.pivot_table(index="rep", columns="contrast", values="abserr")
    return piv.reindex(index=reps, columns=contrasts)


def verify(path):
    df = pd.read_csv(path)
    df = df[np.isfinite(df["d_hat"]) & np.isfinite(df["d_true"])].copy()
    df["abserr"] = np.abs(df["d_hat"] - df["d_true"])
    contrasts = sorted(df["contrast"].unique())
    reps = np.array(sorted(df["rep"].unique()))
    bm = err_matrix(df, BASE, reps, contrasts)
    am = err_matrix(df, AUTO, reps, contrasts)
    valid = (~bm.isna().any(axis=1)) & (~am.isna().any(axis=1))
    bv, av = bm[valid].to_numpy(), am[valid].to_numpy()
    R = len(bv)

    def mciw0(mat):  # 2*mean_over_contrasts(q95 over rows)
        return 2.0 * np.mean(np.quantile(mat, TARGET, axis=0))

    point = mciw0(av) - mciw0(bv)
    rng = np.random.default_rng(7)
    idx = rng.integers(0, R, size=(B, R))
    d0 = np.empty(B)
    for j in range(B):
        rows = idx[j]
        d0[j] = mciw0(av[rows]) - mciw0(bv[rows])
    lo, hi = np.quantile(d0, [0.025, 0.975])
    return {"n_paired_reps": int(R), "mciw0_method": float(mciw0(av)),
            "mciw0_baseline": float(mciw0(bv)), "dMCIW0": float(point),
            "ci_low": float(lo), "ci_high": float(hi),
            "robust_win": bool(hi < 0.0)}


def main():
    cells = sorted(GRID.glob("gridcell_*_perrep.csv"))
    out = {"cells": {}, "verifier": "claude_independent"}
    print(f"{'cell':18s}{'dMCIW0':>10}{'ci_low':>10}{'ci_high':>10}{'robust':>8}")
    for p in cells:
        cid = p.stem.replace("gridcell_", "").replace("_perrep", "")
        r = verify(p)
        out["cells"][cid] = r
        print(f"{cid:18s}{r['dMCIW0']:>+10.4f}{r['ci_low']:>+10.4f}"
              f"{r['ci_high']:>+10.4f}{str(r['robust_win']):>8}")
    (Path(__file__).resolve().parent / "result_claude_grid.json").write_text(
        json.dumps(out, indent=2))
    print("\nwrote result_claude_grid.json")


if __name__ == "__main__":
    main()
