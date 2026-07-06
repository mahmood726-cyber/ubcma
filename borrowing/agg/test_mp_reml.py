"""Regression test for mp_reml zero-variance guard (transport P1-6/7).

Run: PYTHONPATH=borrowing/agg python -m pytest borrowing/agg/test_mp_reml.py -q
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from aggregate_transport import mp_reml  # noqa: E402


def test_mp_reml_survives_zero_se_study():
    """A zero-SE study made w = 1/(v+tau2) infinite -> pooled mean/SE NaN. With
    the variance floor the study dominates (large finite weight) instead."""
    mu, se = mp_reml([0.5, 0.3, 0.4], [0.0, 0.1, 0.1])
    assert np.isfinite(mu) and np.isfinite(se), (mu, se)
    # the zero-SE (most precise) study dominates -> pooled mean near its value
    assert 0.4 < mu <= 0.5, mu


def test_mp_reml_unchanged_on_well_conditioned_data():
    """The floor is a no-op for real variances (v > 1e-12), so ordinary pooling
    is unchanged (R-parity preserved)."""
    mu, se = mp_reml([0.2, 0.3, 0.25], [0.1, 0.1, 0.1])
    assert abs(mu - 0.25) < 1e-9
    assert abs(se - np.sqrt(1.0 / (3 / 0.01))) < 1e-9   # homogeneous -> tau2=0
