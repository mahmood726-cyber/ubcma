"""test_dr_bakeoff.py -- fast regression checks for the Stage-3 bake-off.

Not a full run (that is dr_bakeoff.py --reps 300); these lock in the harness
contract and the two structural facts behind the honest null.
Run: PYTHONPATH=doseresponse:src python -m pytest doseresponse/test_dr_bakeoff.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import dr_bakeoff as B  # noqa: E402
import sim_doseresponse as S  # noqa: E402


def test_selection_biases_slope_upward():
    """Moderate/strong selection biases the naive pooled slope UP; none ~0."""
    m_none, beta = S.naive_pool_bias_check("none", n=120)
    m_strong, _ = S.naive_pool_bias_check("strong", n=120)
    assert abs(m_none - beta) < 0.004           # ~unbiased without selection
    assert m_strong - beta > 0.008              # clear upward bias under selection


def test_pet_peese_invalid_under_no_selection():
    """The structural fact behind the null: regression correctors are biased
    even with NO selection, so they cannot serve as bias-corrected members."""
    raw = B.run_replicates("none", reps=60, tau_slope=0.02)
    def bias(method):
        g = raw[(raw.method == method) & raw.converged]
        return float(np.mean(g.mu_hat - g.true_mu))
    assert abs(bias("two_stage_reml")) < 0.004
    assert bias("trend_pet") > 0.05             # invalid: large + bias under null
    assert bias("trend_peese") > 0.02


def test_adaptshrink_finite_and_ties_baseline():
    """AdaptShrink converges and lands within a hair of two-stage REML (collapses
    onto the field standard because the valid members coincide)."""
    raw = B.run_replicates("strong", reps=60)
    gate = B.truth_gate(raw, B.matched_coverage_table(raw))
    assert gate["G1_finite_point_ok"]
    as_rows = [b for b in gate["bootstrap_mciw0_vs_baseline"] if b["method"] == "adaptshrink"]
    assert as_rows and not as_rows[0]["robust_win"]   # no robust win => honest null


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
