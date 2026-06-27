"""Independent verification script for AdaptShrink-NMA Phase 2 (components B + C).

This script performs the independent verification task described in VERIFY_SPEC_PHASE2.md.
It does not read smallstudy_nma.py, inconsistency_nma.py, or adaptshrink_nma.py.
It implements the math using numpy and compares the results to the committed reference CSVs.
"""

import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import scipy.stats as stats

# Resolve paths dynamically relative to this script
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent

# Support PYTHONPATH=nma and PYTHONPATH=.
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "nma"))

try:
    from nma_core import Comparison, fit_nma, _assemble, _generalized_Q
except ImportError:
    from nma.nma_core import Comparison, fit_nma, _assemble, _generalized_Q


def load_comps(csv_path):
    df = pd.read_csv(csv_path)
    return [Comparison(str(r.studlab), str(r.treat1), str(r.treat2),
                       float(r.TE), float(r.seTE)) for r in df.itertuples()]


def verify_network(name, input_path, scalars_path, ref_te_path):
    # 1. Load data
    comps = load_comps(input_path)
    scal = pd.read_csv(scalars_path).iloc[0]
    tau2_DL = float(scal.tau2)
    
    # Sort treatments
    treatments = sorted({c.t1 for c in comps} | {c.t2 for c in comps})
    n = len(treatments)
    tidx = {t: i for i, t in enumerate(treatments)}
    
    # Reference treatment (first alphabetically)
    r = treatments[0]
    ref_idx = tidx[r]
    
    # Fit standard random-effects NMA to get weights at DL tau2
    # Get W at DL tau2 using _assemble
    B, W, y, blocks = _assemble(comps, tidx, n, tau2=tau2_DL)
    
    # B_basic: drop reference column (m x (n-1))
    B_basic = np.delete(B, ref_idx, axis=1)
    
    # Part B1: No-covariate model X = B_basic
    X_no = B_basic
    C_no = np.linalg.pinv(X_no.T @ W @ X_no, rcond=1e-12)
    coef_no = C_no @ (X_no.T @ W @ y)
    
    # Reconstruct league table from basic parameters (d_r = 0)
    other_treatments = [t for t in treatments if t != r]
    d_no = {r: 0.0}
    for idx, t in enumerate(other_treatments):
        d_no[t] = coef_no[idx]
        
    TE_no = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            TE_no[i, j] = d_no[treatments[i]] - d_no[treatments[j]]
            
    # Load reference TE_random
    te_ref = pd.read_csv(ref_te_path, index_col=0)
    # Reorder our league to reference league order
    ref_order = [tidx[t] for t in te_ref.columns]
    TE_no_reordered = TE_no[np.ix_(ref_order, ref_order)]
    max_diff_TE = np.max(np.abs(TE_no_reordered - te_ref.to_numpy()))
    
    # Part B2: PET (Egger Asymmetry Test)
    se = np.array([c.se for c in comps])
    X_pet = np.column_stack([B_basic, se])
    C_pet = np.linalg.pinv(X_pet.T @ W @ X_pet, rcond=1e-12)
    coef_pet = C_pet @ (X_pet.T @ W @ y)
    beta_pet = coef_pet[-1]
    var_beta_pet = C_pet[-1, -1]
    z_pet = beta_pet / np.sqrt(var_beta_pet)
    p_pet = 2.0 * (1.0 - stats.norm.cdf(np.abs(z_pet)))
    
    # Part B3: PEESE
    se2 = se ** 2
    X_peese = np.column_stack([B_basic, se2])
    C_peese = np.linalg.pinv(X_peese.T @ W @ X_peese, rcond=1e-12)
    coef_peese = C_peese @ (X_peese.T @ W @ y)
    d_peese = {r: 0.0}
    for idx, t in enumerate(other_treatments):
        d_peese[t] = coef_peese[idx]
        
    # Part C: Design-by-treatment Q decomposition
    # Q_total at tau2=0 (common-effect weights)
    B0, W0, y0, _ = _assemble(comps, tidx, n, tau2=0.0)
    L0 = B0.T @ W0 @ B0
    L0plus = np.linalg.pinv(L0, rcond=1e-12)
    Q_total, _ = _generalized_Q(B0, W0, y0, L0plus)
    
    # df_total
    by_study = {}
    for c in comps:
        by_study.setdefault(c.studlab, set()).update([c.t1, c.t2])
    indep = sum(len(arms) - 1 for arms in by_study.values())
    df_total = max(indep - (n - 1), 0)
    
    # Group study blocks by design
    # A design = frozenset of treatments in a study
    designs = {}
    for blk in blocks:
        design_key = frozenset(blk["arms"])
        designs.setdefault(design_key, []).append(blk)
        
    Q_het = 0.0
    df_het = 0
    for d_key, dblks in designs.items():
        # Gather all row indices belonging to studies of this design
        rows_d = []
        for blk in dblks:
            rows_d.extend(blk["rows"])
        rows_d = sorted(rows_d)
        
        if not rows_d:
            continue
            
        B_d = B0[rows_d, :]
        W_d = W0[np.ix_(rows_d, rows_d)]
        y_d = y0[rows_d]
        
        L_d = B_d.T @ W_d @ B_d
        Lplus_d = np.linalg.pinv(L_d, rcond=1e-12)
        Q_d, _ = _generalized_Q(B_d, W_d, y_d, Lplus_d)
        
        # Within-design df: (sum over studies of (arms - 1)) - (unique arms in design - 1)
        total_indep_d = sum(len(blk["arms"]) - 1 for blk in dblks)
        df_d = total_indep_d - (len(d_key) - 1)
        
        Q_het += Q_d
        df_het += df_d
        
    Q_inc = Q_total - Q_het
    df_inc = df_total - df_het
    
    return {
        "B1_maxTE": max_diff_TE,
        "B2_PET_beta": beta_pet,
        "B2_PET_z": z_pet,
        "B2_PET_p": p_pet,
        "C_Qtotal": Q_total,
        "C_df_total": df_total,
        "C_Qhet": Q_het,
        "C_df_het": df_het,
        "C_Qinc": Q_inc,
        "C_df_inc": df_inc,
        "d_peese": d_peese
    }


def main():
    results = {}
    networks = ["smoking", "senn2013"]
    for net in networks:
        input_path = REPO_ROOT / "nma" / "reference" / f"{net}_input.csv"
        scalars_path = REPO_ROOT / "nma" / "reference" / f"{net}_scalars.csv"
        ref_te_path = REPO_ROOT / "nma" / "reference" / f"{net}_TE_random.csv"
        results[net] = verify_network(net, input_path, scalars_path, ref_te_path)
        
    # Check PASS_OR_FAIL
    ref_decomp_path = REPO_ROOT / "nma" / "verify" / "decomp_reference.csv"
    ref_decomp = pd.read_csv(ref_decomp_path, index_col=0)
    
    passes = True
    for net in networks:
        res = results[net]
        ref_q_inc = float(ref_decomp.loc[net, "Q_inc"])
        ref_df_inc = int(ref_decomp.loc[net, "df_inc"])
        
        if res["B1_maxTE"] >= 1e-8:
            passes = False
            print(f"[{net}] B1 check failed: max_TE_diff = {res['B1_maxTE']:.3e} >= 1e-8")
        if abs(res["C_Qinc"] - ref_q_inc) >= 1e-6:
            passes = False
            print(f"[{net}] C check failed: Q_inc diff = {abs(res['C_Qinc'] - ref_q_inc):.3e} >= 1e-6")
        if res["C_df_inc"] != ref_df_inc:
            passes = False
            print(f"[{net}] C check failed: df_inc = {res['C_df_inc']} (expected {ref_df_inc})")
            
    status = "PASS" if passes else "FAIL"
    
    for net in networks:
        res = results[net]
        print(f"\n==={net.upper()}===")
        print(f"B1_maxTE: {res['B1_maxTE']:.15f}")
        print(f"B2_PET_beta: {res['B2_PET_beta']:.15f}")
        print(f"B2_PET_z: {res['B2_PET_z']:.15f}")
        print(f"B2_PET_p: {res['B2_PET_p']:.15e}")
        print(f"C_Qtotal: {res['C_Qtotal']:.15f} (df={res['C_df_total']})")
        print(f"C_Qhet: {res['C_Qhet']:.15f} (df={res['C_df_het']})")
        print(f"C_Qinc: {res['C_Qinc']:.15f} (df={res['C_df_inc']})")
        print(f"PEESE basic parameters (vs ref {net} first treatment):")
        for t, val in sorted(res['d_peese'].items()):
            print(f"  {t}: {val:.15f}")
        
    print(f"\n===PASS_OR_FAIL=== {status}")
    sys.exit(0 if passes else 1)


if __name__ == "__main__":
    main()