"""selfverify_dr.py -- independent from-scratch re-derivation of the Stage-3
headline (HONEST NULL), used when external vendors are unreachable.

Does NOT import dr_bakeoff's scorer. Re-derives, on a DISJOINT seed stream, four
independent confirmations of "AdaptShrink does not robustly beat two-stage REML
at matched coverage on the dose-response slope under publication selection":

  C1  fresh-seed matched-coverage (MCIW0) recomputed by hand + paired bootstrap.
  C2  95th-percentile |error| ratio (adaptshrink / reml) -- a metric-free check.
  C3  structural invalidity of PET/PEESE: positive bias under NO selection.
  C4  mechanism: kernel weights ~ equal across 3 near-identical valid members,
      so the aggregate collapses onto the field standard.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import drma  # noqa: E402
import sim_doseresponse as S  # noqa: E402
from ubcma.adaptshrink import adaptshrink_estimator  # noqa: E402


def members(df):
    fr = drma.drma_two_stage(df, n_col="peryears", transform="linear", method="reml")
    ff = drma.drma_two_stage(df, n_col="peryears", transform="linear", method="fixed")
    fo = drma.drma_one_stage(df, n_col="peryears", transform="linear")
    r = (float(fr.coef[0]), float(np.sqrt(fr.vcov[0, 0])))
    f = (float(ff.coef[0]), float(np.sqrt(ff.vcov[0, 0])))
    o = (float(fo.coef[0]), float(np.sqrt(fo.vcov[0, 0])))
    asr = adaptshrink_estimator(np.zeros(1), np.ones(1),
                                members=("two_stage_reml", "two_stage_fixed", "one_stage"),
                                precomputed={"two_stage_reml": r, "two_stage_fixed": f,
                                             "one_stage": o}, kappa=1.0)
    return r[0], asr["mu"], asr["weights"], [r[0], f[0], o[0]]


def c1_c2_c4(strength="strong", reps=300, seed0=99999):
    err_r, err_a, weights, spreads = [], [], [], []
    for s in range(reps):
        df, beta = S.gen_published(seed0 + s, strength)
        if df is None:
            continue
        mu_r, mu_a, w, mus = members(df)
        err_r.append(abs(mu_r - beta))
        err_a.append(abs(mu_a - beta))
        weights.append([w["two_stage_reml"], w["two_stage_fixed"], w["one_stage"]])
        spreads.append(np.std(mus))
    err_r = np.array(err_r); err_a = np.array(err_a)
    q = 0.95
    mciw0_r = 2 * np.quantile(err_r, q)
    mciw0_a = 2 * np.quantile(err_a, q)
    # paired bootstrap of (adaptshrink - reml) MCIW0
    rng = np.random.default_rng(2026)
    n = len(err_r)
    idx = rng.integers(0, n, size=(4000, n))
    diff = 2 * (np.quantile(err_a[idx], q, axis=1) - np.quantile(err_r[idx], q, axis=1))
    lo, hi = np.quantile(diff, [0.025, 0.975])
    print(f"[C1] strong selection, fresh seeds, n={n}")
    print(f"     MCIW0 reml={mciw0_r:.5f}  adaptshrink={mciw0_a:.5f}  ratio={mciw0_a/mciw0_r:.4f}")
    print(f"     paired-bootstrap dMCIW0(AS-REML)={2*(np.quantile(err_a,q)-np.quantile(err_r,q)):+.5f}"
          f"  CI[{lo:+.5f},{hi:+.5f}]  robust_win(AS)={bool(hi<0)}")
    print(f"[C2] 95th-pct |error| ratio AS/REML = {np.quantile(err_a,q)/np.quantile(err_r,q):.4f}"
          f"  (>=1 => no efficiency gain)")
    w = np.array(weights).mean(axis=0)
    print(f"[C4] mean kernel weights [reml,fixed,one] = [{w[0]:.3f},{w[1]:.3f},{w[2]:.3f}]"
          f"  mean member-spread(SD) = {np.mean(spreads):.5f}  (tiny => members coincide)")
    return bool(hi < 0)


def c3(reps=300, seed0=77777):
    """PET/PEESE positive bias under NO selection => structurally invalid."""
    pet, peese, reml = [], [], []
    for s in range(reps):
        df, beta = S.gen_published(seed0 + s, "none")
        if df is None:
            continue
        fr = drma.drma_two_stage(df, n_col="peryears", transform="linear", method="reml")
        bi = fr.bi.ravel()
        sei = np.array([np.sqrt(S_[0, 0]) for S_ in fr.Sigma_list])
        reml.append(float(fr.coef[0]) - beta)
        for store, mod in ((pet, sei), (peese, sei ** 2)):
            w = 1.0 / sei ** 2
            X = np.column_stack([np.ones_like(sei), mod])
            WX = X * w[:, None]
            b = np.linalg.solve(X.T @ WX, WX.T @ bi)
            store.append(float(b[0]) - beta)
    print(f"[C3] NO-selection bias: reml={np.mean(reml):+.4f}  "
          f"PET={np.mean(pet):+.4f}  PEESE={np.mean(peese):+.4f}  "
          f"(PET/PEESE biased under null => invalid members)")


if __name__ == "__main__":
    print("=== Independent from-scratch re-derivation (vendors unreachable) ===")
    robust = c1_c2_c4()
    c3()
    print("\nHEADLINE:", "ROBUST WIN for AdaptShrink" if robust
          else "HONEST NULL -- AdaptShrink does NOT robustly beat two-stage REML "
               "on the DR slope under selection (consistent with the harness truth-gate).")
