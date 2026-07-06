"""Regression test for the transport-sim coverage computation.

Run: PYTHONPATH=borrowing python -m pytest borrowing/test_transport_coverage.py -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sim_transport import _covered, Z975  # noqa: E402


def test_coverage_is_not_tautological():
    """Regression (P0-1): coverage must be whether the truth lies inside the
    ESTIMATE's CI (mu_p +/- z*se), not inside an interval centred on the truth
    itself. The old inline check `float(truth-half <= truth <= truth+half) or
    ...` short-circuited to 1.0 always (the first clause is a tautology), so
    every method reported coverage 1.0 and the matched-coverage comparison was
    meaningless."""
    # Estimate exactly at the truth -> covered for any positive se.
    assert _covered(1.0, 0.5, 1.0) == 1.0
    # Estimate FAR from the truth with a tiny se -> NOT covered. The old
    # tautology would have returned 1.0 here regardless of the estimate.
    assert _covered(5.0, 1e-6, 1.0) == 0.0
    assert _covered(-3.0, 0.1, 0.0) == 0.0


def test_coverage_respects_ci_width_boundary():
    """Truth just inside vs just outside the estimate's 95% CI flips coverage."""
    mu, se, truth = 0.0, 1.0, 0.0
    half = Z975 * se
    assert _covered(mu, se, truth + half - 1e-9) == 1.0   # just inside
    assert _covered(mu, se, truth + half + 1e-9) == 0.0   # just outside


def test_coverage_widens_with_se():
    """A wider interval (larger se) captures a truth that a tight one misses."""
    mu, truth = 0.0, 1.5
    assert _covered(mu, 0.1, truth) == 0.0     # tight CI misses
    assert _covered(mu, 1.0, truth) == 1.0     # wide CI captures
