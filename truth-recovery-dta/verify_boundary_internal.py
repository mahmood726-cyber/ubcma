"""verify_boundary_internal.py -- from-scratch internal re-derivation of the
DTA Phase-3 boundary map, independent of ubcma and of dta_bakeoff.py.

A 4th independent code path (alongside ubcma's own truth-gate, the agy vendor,
and the codex_pc2 vendor) that reads ONLY the committed per-rep CSVs and:

  (1) recomputes the MCIW0-2D constant-region AREA + deterministic dArea
      (ours - HC) for every boundary cell (k x selection-strength), per the
      VENDOR_REDERIVE metric spec; and
  (2) checks that the boundary grid reproduces the Phase-2 focus grid
      bit-exactly on the overlapping cells (k6_thr/k10_thr/k20_thr x
      {none,moderate,strong}), confirming the DGP/seed pipeline is
      deterministic and the boundary grid is a faithful extension.

Does NOT import ubcma. numpy/pandas only. Writes
verify_boundary_internal_result.json.

Run:  python truth-recovery-dta/verify_boundary_internal.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent


def area(g: pd.DataFrame) -> float:
    """MCIW0-2D constant-region area (VENDOR_REDERIVE spec)."""
    e = np.column_stack([g.m1 - g.true_m1, g.m2 - g.true_m2])
    W = np.cov(e, rowvar=False)            # ddof=1 (numpy default)
    detW = float(np.linalg.det(W))
    assert detW > 0, "detW <= 0"
    Wi = np.linalg.inv(W)
    d2 = np.einsum("ij,jk,ik->i", e, Wi, e)
    q = float(np.quantile(d2, 0.95))       # linear interpolation (default)
    return float(np.pi * q * np.sqrt(detW))


def darea_cell(df: pd.DataFrame, cell: str, strength: str):
    g = df[(df.cell == cell) & (df.strength == strength)]
    r = g[(g.method == "reitsma") & g.converged
          & np.isfinite(g.m1) & np.isfinite(g.m2)]
    a = g[(g.method == "adaptshrink_dta") & g.converged
          & np.isfinite(g.m1) & np.isfinite(g.m2)]
    R = sorted(set(r.rep) & set(a.rep))    # paired set: both converged
    r = r[r.rep.isin(R)].sort_values("rep")
    a = a[a.rep.isin(R)].sort_values("rep")
    ar, aa = area(r), area(a)
    return ar, aa, aa - ar, len(R)


def kof(cell: str) -> int:
    return int(cell.split("k")[1].split("_")[0])


def main() -> None:
    bnd = pd.read_csv(HERE / "dta_boundary_perrep.csv")
    foc = pd.read_csv(HERE / "dta_focus_perrep.csv")

    cells = sorted(bnd.cell.unique(), key=kof)
    out_cells = []
    print("# From-scratch internal re-derivation (no ubcma import)")
    print(f"{'cell':<9}{'strength':<10}{'area_HC':>10}{'area_ours':>11}"
          f"{'dArea':>11}{'n':>5}")
    for cell in cells:
        for s in ["none", "moderate", "strong"]:
            ar, aa, d, n = darea_cell(bnd, cell, s)
            out_cells.append({"cell": cell, "strength": s, "k": kof(cell),
                              "area_reitsma": ar, "area_adaptshrink": aa,
                              "darea": d, "n_reps": n})
            print(f"{cell:<9}{s:<10}{ar:>10.4f}{aa:>11.4f}{d:>+11.4f}{n:>5}")

    # (2) bit-exact overlap consistency vs focus grid
    overlap = ["k6_thr", "k10_thr", "k20_thr"]
    maxd, n_checked = 0.0, 0
    for cell in overlap:
        for s in ["none", "moderate", "strong"]:
            for meth in ["reitsma", "adaptshrink_dta"]:
                gb = bnd[(bnd.cell == cell) & (bnd.strength == s)
                         & (bnd.method == meth)]
                gf = foc[(foc.cell == cell) & (foc.strength == s)
                         & (foc.method == meth)]
                if len(gb) == 0 or len(gf) == 0:
                    continue
                m = gb.merge(gf, on="rep", suffixes=("_b", "_f"))
                maxd = max(maxd,
                           float(np.abs(m.m1_b - m.m1_f).max()),
                           float(np.abs(m.m2_b - m.m2_f).max()),
                           float(np.abs(m.area_raw_b - m.area_raw_f).max()))
                n_checked += len(m)

    print(f"\n# overlap consistency: {n_checked} matched rows over "
          f"{overlap} x 3 strengths x 2 methods")
    print(f"# max|dm1|=max|dm2|=max|darea_raw| = {maxd:.3e}  "
          f"({'BIT-EXACT' if maxd == 0.0 else 'NOT bit-exact'})")

    result = {"seat": "internal_rederive", "imported_ubcma": False,
              "input": "dta_boundary_perrep.csv",
              "metric": "MCIW0-2D constant-region area (VENDOR_REDERIVE spec)",
              "cells": out_cells,
              "overlap_consistency": {
                  "cells": overlap, "matched_rows": n_checked,
                  "max_abs_dev": maxd, "bit_exact": maxd == 0.0}}
    (HERE / "verify_boundary_internal_result.json").write_text(
        json.dumps(result, indent=2))
    print("\nWrote verify_boundary_internal_result.json")


if __name__ == "__main__":
    main()
