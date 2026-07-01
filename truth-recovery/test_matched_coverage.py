"""Tests for the matched-coverage truth-gate scorer.

These verify the SCORER MATH on synthetic fixtures with a known answer (a
low-error method must beat a biased high-error one at matched coverage). They do
NOT re-run the slow simulation; the headline numbers are produced by
`matched_coverage_bakeoff.py` and recorded in REPORT_MATCHED_COVERAGE.md.

Run: PYTHONPATH=src python -m pytest truth-recovery/test_matched_coverage.py -q
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, HERE)

import matched_coverage_bakeoff as MC  # noqa: E402


def _make_perrep(n=120, seed=0):
    """Synthetic per-rep frame: 'ubcma' low-error/unbiased, 'copas' biased+wide.

    Errors are constructed so the truth is known: ubcma should win at matched
    coverage. Both get CIs wide enough that constant-width calibration is stable.
    """
    rng = np.random.default_rng(seed)
    true_mu = 0.2
    rows = []
    for r in range(n):
        # low-error unbiased method
        e_good = rng.normal(0.0, 0.03)
        mu_good = true_mu + e_good
        hw_good = 0.06
        # biased, higher-variance method (like HC under misspecification)
        e_bad = 0.10 + rng.normal(0.0, 0.04)
        mu_bad = true_mu + e_bad
        hw_bad = 0.06
        for method, mu, hw in (("ubcma", mu_good, hw_good),
                               ("copas", mu_bad, hw_bad)):
            rows.append({
                "mechanism": "copas", "strength": "strong", "rep": r,
                "method": method, "true_mu": true_mu, "mu_hat": mu,
                "ci_low": mu - hw, "ci_high": mu + hw, "converged": True,
            })
    return pd.DataFrame(rows)


def test_low_error_method_wins_matched_coverage():
    df = _make_perrep()
    table = MC.matched_coverage_table(df, target=0.95)
    t = table.set_index("method")
    assert t.loc["ubcma", "mciw0"] < t.loc["copas", "mciw0"]
    # the (unbiased) winner's constant-width calibration generalizes ~target
    assert abs(t.loc["ubcma", "mciw0_test_cov"] - 0.95) <= 0.08


def test_bootstrap_flags_robust_win():
    df = _make_perrep()
    boot = MC._bootstrap_mciw0(df, target=0.95, n_boot=1000, seed=1)
    ub = [b for b in boot if b["method"] == "ubcma"][0]
    assert ub["robust_win"] is True
    assert ub["ci_hi"] < 0.0
    assert ub["mciw0_diff"] < 0.0


def test_truth_gate_records_verified_win():
    df = _make_perrep()
    table = MC.matched_coverage_table(df, target=0.95)
    gate = MC._truth_gate(df, table, target=0.95)
    assert gate["G1_finite_ok"] is True
    wins = [w for w in gate["verified_wins_vs_HC"] if w["method"] == "ubcma"]
    assert len(wins) == 1 and wins[0]["ratio"] < 1.0
    robust = [w for w in gate["robust_wins_vs_HC"] if w["method"] == "ubcma"]
    assert len(robust) == 1


def test_no_win_when_errors_equal():
    # Two methods with identical error distributions -> no robust win either way.
    rng = np.random.default_rng(3)
    rows = []
    for r in range(120):
        for method in ("ubcma", "copas"):
            e = rng.normal(0.0, 0.04)
            mu = 0.2 + e
            rows.append({
                "mechanism": "copas", "strength": "strong", "rep": r,
                "method": method, "true_mu": 0.2, "mu_hat": mu,
                "ci_low": mu - 0.06, "ci_high": mu + 0.06, "converged": True,
            })
    df = pd.DataFrame(rows)
    gate = MC._truth_gate(df, MC.matched_coverage_table(df, 0.95), target=0.95)
    assert gate["robust_wins_vs_HC"] == []


def test_no_fabricated_rows_pass_gate():
    # A non-finite estimate on a 'converged' row must fail G1.
    df = _make_perrep(n=40)
    df.loc[0, "mu_hat"] = np.nan  # converged but NaN -> fabrication guard
    gate = MC._truth_gate(df, MC.matched_coverage_table(df, 0.95), target=0.95)
    assert gate["G1_finite_ok"] is False
    assert gate["pass"] is False


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
