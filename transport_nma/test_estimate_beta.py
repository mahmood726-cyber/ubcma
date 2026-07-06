"""Regression test for transport_truthgate.estimate_beta (effect-modification slope).

Run: PYTHONPATH=transport_nma:nma python -m pytest transport_nma/test_estimate_beta.py -q
"""
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "nma"))

from nma_core import Comparison            # noqa: E402
from transport_truthgate import estimate_beta, _verdict  # noqa: E402


def test_beta_not_confounded_by_treatment_baseline():
    """Regression (P0-2): two active treatments with DIFFERENT placebo-relative
    baselines assigned to low- vs high-X studies must NOT manufacture a slope
    when the true effect-modifier is 0. The old pooled regression returned
    beta_hat=2.0 (= the between-treatment effect gap / dX); the within-treatment
    estimator returns 0 (no within-treatment X spread -> not identifiable)."""
    sim = []
    for s in range(6):
        t = "A" if s < 3 else "B"
        d0 = -2.0 if t == "A" else 0.0        # different baselines
        sim.append(Comparison(f"s{s}", t, "placebo", d0, 0.1))
    Xstudy = {f"s{s}": (0.0 if s < 3 else 1.0) for s in range(6)}
    beta_hat = estimate_beta(sim, Xstudy, Xref=0.5)
    assert abs(beta_hat) < 1e-9, beta_hat


def test_beta_recovers_true_within_treatment_slope():
    """When each treatment spans a range of X, the within estimator recovers the
    true effect-modification slope free of the treatment baselines."""
    beta_true = 0.5
    Xref = 1.0
    sim = []
    Xstudy = {}
    sid = 0
    for t, d0 in (("A", -2.0), ("B", +1.0)):     # different baselines
        for X in (0.0, 1.0, 2.0):                 # within-treatment X spread
            te = d0 + beta_true * (X - Xref)
            sim.append(Comparison(f"s{sid}", t, "placebo", te, 0.1))
            Xstudy[f"s{sid}"] = X
            sid += 1
    beta_hat = estimate_beta(sim, Xstudy, Xref=Xref)
    assert abs(beta_hat - beta_true) < 1e-9, beta_hat


def test_beta_zero_when_no_covariate_spread():
    """No X variation at all -> slope not identifiable -> fail closed to 0."""
    sim = [Comparison(f"s{i}", "A", "placebo", -1.0, 0.1) for i in range(4)]
    Xstudy = {f"s{i}": 0.7 for i in range(4)}
    assert estimate_beta(sim, Xstudy, Xref=0.5) == 0.0


def test_verdict_fails_closed_on_nan_ci():
    """Regression (P1-5): a non-finite CI must NOT be reported as the benign
    'inert/tie' (fail-OPEN) — it is 'undefined'. Finite CIs keep their
    directional verdicts."""
    assert _verdict(float("nan"), float("nan")) == "undefined"
    assert _verdict(0.1, float("nan")) == "undefined"
    assert _verdict(-0.2, -0.1) == "WINS"       # CI entirely below 0
    assert _verdict(0.1, 0.2) == "HARMS"        # CI entirely above 0
    assert _verdict(-0.1, 0.1) == "inert/tie"   # CI straddles 0
