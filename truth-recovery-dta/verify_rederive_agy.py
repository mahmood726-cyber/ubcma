"""Independent verification of MCIW0-2D constant-region AREA and paired bootstrap.

This script carries out the matched-coverage re-derivation task from the raw
per-replicate CSV only, without importing or reading any project sources.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import numpy as np
import pandas as pd


def compute_area_from_errors(E: np.ndarray) -> float:
    """Computes the MCIW0-2D constant-region AREA for a given stack of errors.
    
    E is an N x 2 array of errors (m_i - true_m_i).
    """
    # W = numpy.cov(E, rowvar=False) (ddof=1 is default)
    W = np.cov(E, rowvar=False)
    detW = np.linalg.det(W)
    if detW <= 0:
        raise ValueError(f"detW must be positive, got {detW}")
        
    # W_inv = W^{-1}
    W_inv = np.linalg.inv(W)
    
    # d2_i = e_i^T W^{-1} e_i
    # Row-wise dot product of E and E @ W_inv
    d2 = np.sum(E * (E @ W_inv), axis=1)
    
    # q = numpy.quantile(d2, 0.95) (method='linear' is default)
    q = np.quantile(d2, 0.95)
    
    # AREA = pi * q * sqrt(detW)
    area = np.pi * q * np.sqrt(detW)
    return float(area)


def main() -> None:
    # 1. Locate the CSV file supporting C:, D:, F: candidate roots
    here = Path(__file__).resolve().parent
    csv_path = here / "dta_focus_perrep.csv"
    if not csv_path.exists():
        for drive in ["F", "C", "D"]:
            candidate = Path(f"{drive}:/ubcma-dta/truth-recovery-dta/dta_focus_perrep.csv")
            if candidate.exists():
                csv_path = candidate
                break

    if not csv_path.exists():
        raise FileNotFoundError("Could not locate dta_focus_perrep.csv")
        
    print(f"Reading data from: {csv_path}")
    df = pd.read_csv(csv_path)
    
    target_cells = [
        {"cell": "k10_hi", "strength": "strong"},
        {"cell": "k6_thr", "strength": "strong"},
        {"cell": "k10_thr", "strength": "strong"},
        {"cell": "k20_thr", "strength": "strong"},
    ]
    
    results = []
    
    # Set seed for reproducibility of bootstrap
    # We use a fixed seed 42 to make the bootstrap deterministic for this run
    rng = np.random.default_rng(42)
    n_boot = 2000
    
    for tc in target_cells:
        cell = tc["cell"]
        strength = tc["strength"]
        
        # Filter for this cell and strength
        df_cell = df[(df["cell"] == cell) & (df["strength"] == strength)]
        
        # Separate methods
        df_reitsma = df_cell[df_cell["method"] == "reitsma"]
        df_adapt = df_cell[df_cell["method"] == "adaptshrink_dta"]
        
        # Filter converged & finite reps for reitsma
        reitsma_valid = df_reitsma[
            (df_reitsma["converged"].astype(str).str.lower() == "true") &
            df_reitsma["m1"].notna() & df_reitsma["m2"].notna() &
            np.isfinite(df_reitsma["m1"]) & np.isfinite(df_reitsma["m2"])
        ]
        
        # Filter converged & finite reps for adaptshrink_dta
        adapt_valid = df_adapt[
            (df_adapt["converged"].astype(str).str.lower() == "true") &
            df_adapt["m1"].notna() & df_adapt["m2"].notna() &
            np.isfinite(df_adapt["m1"]) & np.isfinite(df_adapt["m2"])
        ]
        
        # Find common reps where BOTH converged and are finite
        common_reps = np.intersect1d(reitsma_valid["rep"], adapt_valid["rep"])
        n_reps = len(common_reps)
        
        # Align by rep index
        r_reitsma = reitsma_valid.set_index("rep").loc[common_reps]
        r_adapt = adapt_valid.set_index("rep").loc[common_reps]
        
        # Compute error matrices
        E_reitsma = np.column_stack((
            r_reitsma["m1"] - r_reitsma["true_m1"],
            r_reitsma["m2"] - r_reitsma["true_m2"]
        ))
        
        E_adapt = np.column_stack((
            r_adapt["m1"] - r_adapt["true_m1"],
            r_adapt["m2"] - r_adapt["true_m2"]
        ))
        
        # Calculate point estimates
        area_reitsma = compute_area_from_errors(E_reitsma)
        area_adapt = compute_area_from_errors(E_adapt)
        darea = area_adapt - area_reitsma
        
        # Paired bootstrap
        diffs_b = []
        for _ in range(n_boot):
            boot_idx = rng.choice(n_reps, size=n_reps, replace=True)
            E_reitsma_b = E_reitsma[boot_idx]
            E_adapt_b = E_adapt[boot_idx]
            
            area_reitsma_b = compute_area_from_errors(E_reitsma_b)
            area_adapt_b = compute_area_from_errors(E_adapt_b)
            diffs_b.append(area_adapt_b - area_reitsma_b)
            
        diffs_b = np.array(diffs_b)
        
        ci_lo = float(np.quantile(diffs_b, 0.025))
        ci_hi = float(np.quantile(diffs_b, 0.975))
        frac_better = float(np.mean(diffs_b < 0.0))
        robust_win = bool(ci_hi < 0.0)
        
        results.append({
            "cell": cell,
            "strength": strength,
            "area_reitsma": area_reitsma,
            "area_adaptshrink": area_adapt,
            "darea": darea,
            "ci_lo": ci_lo,
            "ci_hi": ci_hi,
            "frac_better": frac_better,
            "robust_win": robust_win,
            "n_reps": n_reps
        })
        
    # Write JSON output
    output_data = {
        "seat": "agy",
        "cells": results,
        "imported_ubcma": False
    }
    
    out_path = here / "verify_rederive_agy_result.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
        f.write("\n")
        
    print(f"\nWritten result to: {out_path}\n")
    
    # Print the resulting table
    print(f"{'cell':<10} | {'strength':<10} | {'reitsma':<10} | {'adaptshrink':<12} | {'darea':<10} | {'ci_lo':<10} | {'ci_hi':<10} | {'frac_better':<12} | {'robust':<6}")
    print("-" * 95)
    for r in results:
        print(f"{r['cell']:<10} | "
              f"{r['strength']:<10} | "
              f"{r['area_reitsma']:10.4f} | "
              f"{r['area_adaptshrink']:12.4f} | "
              f"{r['darea']:10.4f} | "
              f"{r['ci_lo']:10.4f} | "
              f"{r['ci_hi']:10.4f} | "
              f"{r['frac_better']:12.4f} | "
              f"{str(r['robust_win']):<6}")


if __name__ == "__main__":
    main()
