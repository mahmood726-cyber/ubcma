"""Validate nma_core against netmeta 3.6-1 to ~1e-6 on canonical networks.

Run: PYTHONPATH=nma python nma/reference/test_netmeta_parity.py
(or via pytest). Requires the CSVs produced by gen_netmeta_reference.R.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # nma/
from nma_core import Comparison, fit_nma, p_score  # noqa: E402

REF = Path(__file__).resolve().parent
TOL = 1e-6


def _load_comps(tag):
    df = pd.read_csv(REF / f"{tag}_input.csv")
    return [Comparison(str(r.studlab), str(r.treat1), str(r.treat2),
                       float(r.TE), float(r.seTE)) for r in df.itertuples()]


def _load_matrix(path):
    m = pd.read_csv(path, index_col=0)
    return m


def _compare_league(fit, te_path, sete_path, label, results):
    te_ref = _load_matrix(te_path)
    sete_ref = _load_matrix(sete_path)
    treats = list(te_ref.columns)
    # reorder our league to netmeta's treatment order
    tidx = {t: i for i, t in enumerate(fit.treatments)}
    order = [tidx[t] for t in treats]
    TE = fit.TE[np.ix_(order, order)]
    seTE = fit.seTE[np.ix_(order, order)]
    te_err = np.max(np.abs(TE - te_ref.to_numpy()))
    se_err = np.max(np.abs(seTE - sete_ref.to_numpy()))
    ok = te_err < TOL and se_err < TOL
    results.append((label, "TE", te_err, te_err < TOL))
    results.append((label, "seTE", se_err, se_err < TOL))
    return ok


def main():
    results = []
    scalar_checks = []
    for tag, small in [("senn2013", "desirable"), ("smoking", "undesirable")]:
        scal = pd.read_csv(REF / f"{tag}_scalars.csv").iloc[0]
        comps = _load_comps(tag)

        # --- ENGINE check: feed netmeta's tau^2, league must match to 1e-6 ---
        fit_re = fit_nma(comps, random=True, tau2=float(scal.tau2))
        _compare_league(fit_re, REF / f"{tag}_TE_random.csv",
                        REF / f"{tag}_seTE_random.csv", f"{tag}/random", results)

        fit_ce = fit_nma(comps, random=False)
        _compare_league(fit_ce, REF / f"{tag}_TE_common.csv",
                        REF / f"{tag}_seTE_common.csv", f"{tag}/common", results)

        # --- ESTIMATOR check: our DL tau^2 + Q + df vs netmeta ---
        fit_est = fit_nma(comps, random=True)
        scalar_checks.append((f"{tag} tau2", fit_est.tau2, float(scal.tau2),
                              abs(fit_est.tau2 - float(scal.tau2))))
        scalar_checks.append((f"{tag} Q", fit_est.Q, float(scal.Q),
                              abs(fit_est.Q - float(scal.Q))))
        scalar_checks.append((f"{tag} df.Q", fit_est.df_Q, int(scal["df.Q"]),
                              abs(fit_est.df_Q - int(scal["df.Q"]))))

        # --- RANKING check: P-score vs netmeta ---
        ps_ref = pd.read_csv(REF / f"{tag}_pscore.csv")
        ref_map = dict(zip(ps_ref["treat"].astype(str), ps_ref["Pscore.random"].astype(float)))
        ps = p_score(fit_est, small_values=small)
        ps_err = max(abs(ps[t] - ref_map[t]) for t in ref_map)
        scalar_checks.append((f"{tag} P-score(random)", "-", "-", ps_err))

    print("=" * 78)
    print("LEAGUE-TABLE PARITY vs netmeta 3.6-1  (engine fed netmeta tau^2 for RE)")
    print("=" * 78)
    print(f"{'network/model':<22}{'quantity':<8}{'max|abs err|':>16}{'<1e-6?':>10}")
    all_ok = True
    for label, q, err, ok in results:
        all_ok = all_ok and ok
        print(f"{label:<22}{q:<8}{err:>16.3e}{str(ok):>10}")

    print("\n" + "=" * 78)
    print("SCALAR / ESTIMATOR PARITY (our DL tau^2, Q, df, P-score vs netmeta)")
    print("=" * 78)
    print(f"{'quantity':<26}{'ours':>14}{'netmeta':>14}{'abs err':>14}")
    for name, ours, ref, err in scalar_checks:
        o = f"{ours:.8f}" if isinstance(ours, float) else str(ours)
        r = f"{ref:.8f}" if isinstance(ref, float) else str(ref)
        flag = "" if err < 1e-5 else "   <-- check"
        print(f"{name:<26}{o:>14}{r:>14}{err:>14.3e}{flag}")

    print("\nLEAGUE PARITY (engine):", "ALL PASS <1e-6" if all_ok else "FAILURES ABOVE")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
