"""Independent re-implementation of NMA Phase-2 (B + C).

Part B: network small-study meta-regression (PET / PEESE)
Part C: design-by-treatment Q decomposition (inconsistency) at tau^2 = 0

Does NOT read smallstudy_nma.py / inconsistency_nma.py / adaptshrink_nma.py.
MAY use nma.nma_core (engine verified to ~1e-11 vs netmeta).

Run from repo root F:\\ubcma with PYTHONPATH=.
"""

import csv
import math
import sys
from pathlib import Path

import numpy as np
from scipy.stats import chi2

# engine imports (already independently verified)
from nma.nma_core import (
    Comparison,
    _study_blocks,
    _assemble,
    _generalized_Q,
    fit_nma,
)

ROOT = Path("nma/reference")
DECOMP_REF = Path("nma/verify/decomp_reference.csv")
MINE_VALS = Path("nma/verify/phase2_mine_values.txt")


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------

def load_input(net: str) -> list[Comparison]:
    path = ROOT / f"{net}_input.csv"
    comps = []
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            comps.append(Comparison(
                studlab=row["studlab"],
                t1=row["treat1"],
                t2=row["treat2"],
                te=float(row["TE"]),
                se=float(row["seTE"]),
            ))
    return comps


def load_re_league(net: str) -> dict[tuple[str, str], float]:
    """Return {(t1,t2): TE_random} from netmeta reference."""
    te_path = ROOT / f"{net}_TE_random.csv"
    league = {}
    with te_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            # first column is row treatment, remaining columns are column treatments
            fields = list(row.keys())
            row_t = row[fields[0]]
            for col_t in fields[1:]:
                val = row.get(col_t, "")
                if val not in ("", "NA", "NaN"):
                    league[(row_t, col_t)] = float(val)
    return league


def load_scalars(net: str) -> dict[str, float]:
    path = ROOT / f"{net}_scalars.csv"
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            out = {}
            for k, v in row.items():
                try:
                    out[k.strip('"')] = float(v)
                except (ValueError, TypeError):
                    pass
            return out
    return {}


def load_decomp_ref() -> dict[str, dict[str, float]]:
    out = {}
    with DECOMP_REF.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            net = row["network"].strip('"')
            out[net] = {k.strip('"'): float(v) for k, v in row.items()
                        if k != "network" and v not in ("", "NA")}
    return out


# ---------------------------------------------------------------------------
# Part B: network PET / PEESE
# ---------------------------------------------------------------------------

def build_basic_design(B: np.ndarray, ref_idx: int) -> np.ndarray:
    """Drop reference column from global incidence to get B_basic (m x n-1)."""
    cols = [j for j in range(B.shape[1]) if j != ref_idx]
    return B[:, cols]


def wls_augmented(B_basic: np.ndarray, W: np.ndarray, y: np.ndarray,
                  s: np.ndarray | None = None):
    """Weighted least squares.  s = covariate column (None -> no covariate).

    Returns coef, XtWX_pinv.
    coef[-1] = slope beta if s is not None.
    """
    if s is not None:
        X = np.column_stack([B_basic, s])
    else:
        X = B_basic
    XtW = X.T @ W
    XtWX = XtW @ X
    pinv = np.linalg.pinv(XtWX, rcond=1e-12)
    coef = pinv @ (XtW @ y)
    return coef, pinv


def league_from_basic(coef: np.ndarray, treatments: list[str],
                      ref_idx: int) -> dict[tuple[str, str], float]:
    """Reconstruct full league from basic parameters d_t (ref -> 0)."""
    n = len(treatments)
    d = np.zeros(n)
    non_ref = [j for j in range(n) if j != ref_idx]
    d[non_ref] = coef[: len(non_ref)]
    league = {}
    for a in range(n):
        for b in range(n):
            if a != b:
                league[(treatments[a], treatments[b])] = float(d[a] - d[b])
    return league


def run_part_b(net: str, comps: list[Comparison],
               tau2: float, ref: str,
               re_league: dict[tuple[str, str], float]) -> dict:
    treatments = sorted({c.t1 for c in comps} | {c.t2 for c in comps})
    n = len(treatments)
    tidx = {t: i for i, t in enumerate(treatments)}
    ref_idx = tidx[ref]
    m = len(comps)

    B, W, y, blocks = _assemble(comps, tidx, n, tau2=tau2)

    # seTE for the covariate
    s_pet  = np.array([c.se for c in comps])
    s_peese = s_pet ** 2

    B_basic = build_basic_design(B, ref_idx)

    # B1: no covariate — confirm league matches RE to < 1e-8
    coef0, _ = wls_augmented(B_basic, W, y, s=None)
    my_league = league_from_basic(coef0, treatments, ref_idx)

    max_te_diff = 0.0
    for pair, te_mine in my_league.items():
        te_ref = re_league.get(pair)
        if te_ref is not None:
            max_te_diff = max(max_te_diff, abs(te_mine - te_ref))

    # B2: PET augmented
    coef_pet, pinv_pet = wls_augmented(B_basic, W, y, s=s_pet)
    beta_pet  = float(coef_pet[-1])
    var_beta  = float(pinv_pet[-1, -1])
    se_beta   = math.sqrt(max(var_beta, 0.0))
    z_pet     = beta_pet / se_beta if se_beta > 0 else float("nan")
    p_pet     = 2.0 * (1.0 - float(
        math.erf(abs(z_pet) / math.sqrt(2)) / 2 + 0.5  # placeholder
    ))
    # two-tailed p-value from standard normal
    from scipy.stats import norm as _norm
    p_pet = float(2.0 * _norm.sf(abs(z_pet)))

    # B3: PEESE adjusted league
    coef_peese, _ = wls_augmented(B_basic, W, y, s=s_peese)
    peese_league = league_from_basic(coef_peese, treatments, ref_idx)

    return {
        "B1_max_TE_diff": max_te_diff,
        "B2_beta": beta_pet,
        "B2_z": z_pet,
        "B2_p": p_pet,
        "B2_se_beta": se_beta,
        "B3_peese_league": {
            f"d[{t}-{ref}]": float(v)
            for (t, u), v in peese_league.items()
            if u == ref and t != ref
        },
        "treatments": treatments,
        "ref": ref,
    }


# ---------------------------------------------------------------------------
# Part C: Q decomposition at tau^2 = 0
# ---------------------------------------------------------------------------

def run_part_c(net: str, comps: list[Comparison]) -> dict:
    treatments = sorted({c.t1 for c in comps} | {c.t2 for c in comps})
    n = len(treatments)
    tidx = {t: i for i, t in enumerate(treatments)}

    B, W0, y, blocks = _assemble(comps, tidx, n, tau2=0.0)
    L0 = B.T @ W0 @ B
    Lplus0 = np.linalg.pinv(L0, rcond=1e-12)

    # Q_total and df_total
    Q_total, _ = _generalized_Q(B, W0, y, Lplus0)

    # df_total = (Σ arms_per_study - 1) - (n - 1)
    by_study: dict[str, set] = {}
    for c in comps:
        by_study.setdefault(c.studlab, set()).update([c.t1, c.t2])
    df_total = sum(len(arms) - 1 for arms in by_study.values()) - (n - 1)

    # Group studies (blocks) by design = frozenset of arms
    from collections import defaultdict
    design_blocks: dict[frozenset, list] = defaultdict(list)
    for blk in blocks:
        design = frozenset(blk["arms"])
        design_blocks[design].append(blk)

    Q_het = 0.0
    df_het = 0

    for design, dblocks in design_blocks.items():
        # Collect all rows for this design
        rows_d = []
        for blk in dblocks:
            rows_d.extend(blk["rows"])
        rows_d = sorted(rows_d)

        if len(rows_d) == 0:
            continue

        B_d = B[rows_d, :]
        W_d = W0[np.ix_(rows_d, rows_d)]
        y_d = y[rows_d]

        L_d = B_d.T @ W_d @ B_d
        Lplus_d = np.linalg.pinv(L_d, rcond=1e-12)
        Q_d, _ = _generalized_Q(B_d, W_d, y_d, Lplus_d)

        # df_d = (Σ arms_i - 1 for studies in design) - (unique arms in design - 1)
        total_indep_d = sum(len(blk["arms"]) - 1 for blk in dblocks)
        df_d = total_indep_d - (len(design) - 1)

        Q_het += Q_d
        df_het += df_d

    Q_inc = Q_total - Q_het
    df_inc = df_total - df_het

    return {
        "Q_total": float(Q_total),
        "df_total": int(df_total),
        "Q_het": float(Q_het),
        "df_het": int(df_het),
        "Q_inc": float(Q_inc),
        "df_inc": int(df_inc),
        "p_inc": float(chi2.sf(Q_inc, df_inc)) if df_inc > 0 else float("nan"),
    }


# ---------------------------------------------------------------------------
# Main: run both networks, report checks
# ---------------------------------------------------------------------------

def run_network(net: str, decomp_ref: dict) -> dict:
    comps     = load_input(net)
    scalars   = load_scalars(net)
    re_league = load_re_league(net)
    tau2      = scalars["tau2"]

    # Reference = first treatment alphabetically
    treatments = sorted({c.t1 for c in comps} | {c.t2 for c in comps})
    ref = treatments[0]

    b = run_part_b(net, comps, tau2, ref, re_league)
    c = run_part_c(net, comps)

    # Checks vs references
    dref = decomp_ref.get(net, {})
    c_Q_total_diff = abs(c["Q_total"] - dref.get("Q_total", float("nan")))
    c_Q_het_diff   = abs(c["Q_het"]   - dref.get("Q_het",   float("nan")))
    c_Q_inc_diff   = abs(c["Q_inc"]   - dref.get("Q_inc",   float("nan")))
    df_ok = (c["df_inc"] == int(dref.get("df_inc", -1)))

    b1_pass = b["B1_max_TE_diff"] < 1e-8
    c_pass  = c_Q_inc_diff < 1e-6 and df_ok

    print(f"\n===== {net} =====")
    print(f"B(1) max|TE diff vs RE league|: {b['B1_max_TE_diff']:.3e}  {'PASS' if b1_pass else 'FAIL'}")
    print(f"B(2) PET: beta={b['B2_beta']:.6f}  z={b['B2_z']:.4f}  p={b['B2_p']:.4f}")
    print(f"B(3) PEESE league vs {ref}:")
    for k, v in sorted(b["B3_peese_league"].items()):
        print(f"     {k}={v:.5f}")
    print(f"C (tau^2=0):")
    print(f"  Q_total={c['Q_total']:.7f}  df={c['df_total']}  ref={dref.get('Q_total', '?'):.7f}  diff={c_Q_total_diff:.2e}")
    print(f"  Q_het  ={c['Q_het']:.7f}  df={c['df_het']}  ref={dref.get('Q_het', '?'):.7f}  diff={c_Q_het_diff:.2e}")
    print(f"  Q_inc  ={c['Q_inc']:.7f}  df={c['df_inc']}  ref={dref.get('Q_inc', '?'):.7f}  diff={c_Q_inc_diff:.2e}  {'PASS' if c_pass else 'FAIL'}")

    return {"net": net, "B": b, "C": c, "b1_pass": b1_pass, "c_pass": c_pass}


def main():
    decomp_ref = load_decomp_ref()
    results = {}
    all_pass = True

    for net in ["smoking", "senn2013"]:
        r = run_network(net, decomp_ref)
        results[net] = r
        if not r["b1_pass"] or not r["c_pass"]:
            all_pass = False

    print("\n" + "=" * 50)
    verdict = "PASS" if all_pass else "FAIL"
    print(f"OVERALL: {verdict}")
    print("(B1 < 1e-8 and C Q_inc diff < 1e-6 and df exact for both networks)")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
