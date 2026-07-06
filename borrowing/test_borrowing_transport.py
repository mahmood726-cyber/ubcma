"""Regression test for transport_prior non-finite weight fail-closed (P1-8).

A zero bandwidth or a missing/at-target covariate makes a kernel weight NaN
(0/0). The `wsum <= 0` guard is False for NaN, so the prior used to proceed with
NaN weights (returning nan mu/se/ess) instead of failing closed.

Run: PYTHONPATH=borrowing python -m pytest borrowing/test_borrowing_transport.py -q
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from borrowing_transport import transport_prior  # noqa: E402

TARGET = {"active": "GLP1", "baseline": 7.5, "pop_ob": 32.0}
FAILCLOSED = (float("inf"), 0.0)   # (se, ess) sentinel for a fail-closed prior


def _is_failclosed(mu, se, ess):
    return (not np.isfinite(mu)) and se == float("inf") and ess == 0.0


def test_zero_bandwidth_donor_at_target_fails_closed():
    # a donor exactly at the target obesity + zero bandwidth -> 0/0 NaN weight
    donors = [
        {"y": -1.0, "se": 0.1, "pop_ob": 32.0, "active": "GLP1", "baseline": 7.0},
        {"y": -0.8, "se": 0.1, "pop_ob": 34.0, "active": "GLP1", "baseline": 8.0},
    ]
    mu, se, ess = transport_prior(TARGET, donors, bw_ob=0.0, mode="transport")
    assert _is_failclosed(mu, se, ess), (mu, se, ess)


def test_missing_covariate_fails_closed():
    donors = [
        {"y": -1.0, "se": 0.1, "pop_ob": float("nan"), "active": "GLP1", "baseline": 7.0},
        {"y": -0.8, "se": 0.1, "pop_ob": 34.0, "active": "GLP1", "baseline": 8.0},
    ]
    mu, se, ess = transport_prior(TARGET, donors, bw_ob=2.0, mode="transport")
    assert _is_failclosed(mu, se, ess), (mu, se, ess)


def test_well_conditioned_prior_still_finite():
    donors = [
        {"y": -1.0, "se": 0.1, "pop_ob": 30.0, "active": "GLP1", "baseline": 7.0},
        {"y": -0.8, "se": 0.1, "pop_ob": 34.0, "active": "GLP1", "baseline": 8.0},
    ]
    mu, se, ess = transport_prior(TARGET, donors, bw_ob=2.0, mode="transport")
    assert np.isfinite(mu) and np.isfinite(se) and ess > 0
