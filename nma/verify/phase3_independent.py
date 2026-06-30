"""Harness-independent re-implementation of the Phase-3 MCIW0 truth-gate.

Reads ONLY the per-replicate CSV (no nma/ import). Re-derives MCIW0, dMCIW0 and
the paired-bootstrap robust-win CI from scratch per phase3_verify_spec.md. Used
as a self-check against nma_bakeoff.py and as the reference for cross-vendor
agreement.

Usage: python nma/verify/phase3_independent.py <perrep.csv> [more.csv ...]
"""
import sys
import numpy as np
import pandas as pd

TARGET = 0.95
Z = 1.959963984540054
BASE = "common_DL"


def mciw0_per_method(df, target=TARGET):
    """mean-over-contrasts MCIW0 + test-split coverage, per method."""
    out = {}
    for method, gm in df.groupby("method"):
        halves, covs = [], []
        for _, g in gm.groupby("contrast"):
            g = g[np.isfinite(g.d_hat) & np.isfinite(g.d_true)]
            e = np.abs(g.d_hat.to_numpy() - g.d_true.to_numpy())
            rep = g.rep.to_numpy()
            calib = rep % 2 == 0
            test = ~calib
            if calib.sum() < 4 or test.sum() < 4:
                continue
            c_half = np.quantile(e[calib], target)
            halves.append(2.0 * c_half)
            covs.append(np.mean(e[test] <= c_half))
        out[method] = (float(np.mean(halves)), float(np.mean(covs)))
    return out


def err_matrix(df, method):
    sub = df[df.method == method]
    piv = sub.pivot_table(index="rep", columns="contrast", values="abserr")
    return piv


def paired_bootstrap(df, method, n_boot=2000, seed=7, target=TARGET):
    rng = np.random.default_rng(seed)
    df = df.copy()
    df["abserr"] = np.abs(df.d_hat - df.d_true)
    contrasts = sorted(df.contrast.unique())
    reps = np.array(sorted(df.rep.unique()))
    bm = err_matrix(df, BASE).reindex(index=reps, columns=contrasts)
    mm = err_matrix(df, method).reindex(index=reps, columns=contrasts)
    valid = (~bm.isna().any(axis=1)) & (~mm.isna().any(axis=1))
    bv, mv = bm[valid].to_numpy(), mm[valid].to_numpy()
    npaired = len(bv)
    bi = rng.integers(0, npaired, size=(n_boot, npaired))
    d0 = np.empty(n_boot)
    for j in range(n_boot):
        idx = bi[j]
        d0[j] = (2.0 * np.mean(np.quantile(mv[idx], target, axis=0))
                 - 2.0 * np.mean(np.quantile(bv[idx], target, axis=0)))
    lo, hi = np.quantile(d0, [0.025, 0.975])
    point = (2.0 * np.mean(np.quantile(mv, target, axis=0))
             - 2.0 * np.mean(np.quantile(bv, target, axis=0)))
    return npaired, float(point), float(lo), float(hi), bool(hi < 0.0)


def main():
    for path in sys.argv[1:]:
        df = pd.read_csv(path)
        m0 = mciw0_per_method(df)
        base_mciw0 = m0[BASE][0]
        print(f"\n=== {path} ===")
        print(f"  contrasts={df.contrast.nunique()}  reps={df.rep.nunique()}  "
              f"MCIW0(common_DL)={base_mciw0:.4f} (test-cov {m0[BASE][1]:.3f})")
        for method in ("adaptshrink", "adaptshrink_auto"):
            if method not in m0:
                continue
            np_, point, lo, hi, robust = paired_bootstrap(df, method)
            print(f"  {method:<18} MCIW0={m0[method][0]:.4f}  dMCIW0={point:+.4f}  "
                  f"95%CI[{lo:+.4f},{hi:+.4f}]  robust={'YES' if robust else 'no'}  "
                  f"(n_paired={np_}, test-cov {m0[method][1]:.3f})")


if __name__ == "__main__":
    main()
