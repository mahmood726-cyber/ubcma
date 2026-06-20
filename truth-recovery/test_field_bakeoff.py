"""Tests for the field-wide bake-off scorer (synthetic fixtures, no re-sim).

Run: PYTHONPATH=src python -m pytest truth-recovery/test_field_bakeoff.py -q
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, HERE)

import field_bakeoff as F  # noqa: E402


def _cell_rows(mech, headline_err_sd, comp_bias, n=120, seed=0, headline="adaptshrink_ens"):
    """Build a one-cell per-rep frame: headline low-error, comparator biased."""
    rng = np.random.default_rng(seed)
    rows = []
    cell = {"mu": 0.2, "tau": 0.1, "k": 40, "mechanism": mech, "strength": "strong"}
    for r in range(n):
        e_h = rng.normal(0.0, headline_err_sd)
        mu_h = 0.2 + e_h
        e_c = comp_bias + rng.normal(0.0, 0.03)
        mu_c = 0.2 + e_c
        for method, mu, hw in ((headline, mu_h, 0.10), ("copas", mu_c, 0.06)):
            rows.append({**cell, "rep": r, "method": method, "true_mu": 0.2,
                         "mu_hat": mu, "ci_low": mu - hw, "ci_high": mu + hw,
                         "converged": True})
    return pd.DataFrame(rows)


def test_robust_avg_within_hull_and_widens():
    tight = {"a": (0.20, 0.03), "b": (0.205, 0.03), "c": (0.195, 0.03)}
    wide = {"a": (0.05, 0.03), "b": (0.20, 0.03), "c": (0.35, 0.03)}
    rt, rw = F._robust_avg(tight), F._robust_avg(wide)
    assert min(v[0] for v in tight.values()) <= rt["mu"] <= max(v[0] for v in tight.values())
    assert (rw["ci_high"] - rw["ci_low"]) > (rt["ci_high"] - rt["ci_low"])
    assert F._robust_avg({})["converged"] is False


def test_score_tables_basic():
    df = _cell_rows("copas", headline_err_sd=0.03, comp_bias=0.10)
    sc = F.score_tables(df)
    assert set(["adaptshrink_ens", "copas"]).issubset(set(sc["method"]))
    h = sc[sc.method == "adaptshrink_ens"].iloc[0]
    c = sc[sc.method == "copas"].iloc[0]
    assert h["mciw0"] < c["mciw0"]            # low-error headline -> narrower matched width
    assert abs(h["mciw0_test_cov"] - 0.95) <= 0.08


def test_bootstrap_and_domination_win():
    # headline clearly better than the biased comparator -> as_win + dominates
    df = _cell_rows("copas", headline_err_sd=0.03, comp_bias=0.10)
    pair = F.bootstrap_pairwise(df, "adaptshrink_ens", n_boot=1000)
    v = pair[pair.comparator == "copas"].iloc[0]
    assert v["verdict"] == "as_win" and v["ci_hi"] < 0
    sc = F.score_tables(df)
    dom = F.field_domination(sc, pair, "adaptshrink_ens")
    assert bool(dom.iloc[0]["dominates_field"]) is True
    assert int(dom.iloc[0]["n_loss"]) == 0


def test_domination_detects_loss():
    # headline WORSE than comparator (comparator unbiased, headline biased+noisy)
    df = _cell_rows("none", headline_err_sd=0.10, comp_bias=0.0)
    pair = F.bootstrap_pairwise(df, "adaptshrink_ens", n_boot=1000)
    v = pair[pair.comparator == "copas"].iloc[0]
    assert v["verdict"] == "as_loss" and v["ci_lo"] > 0
    sc = F.score_tables(df)
    dom = F.field_domination(sc, pair, "adaptshrink_ens")
    assert bool(dom.iloc[0]["dominates_field"]) is False
    assert "copas" in dom.iloc[0]["loses_to"]


def test_grid_shape():
    grid = F.build_grid()
    assert len(grid) == len(F.MUS) * len(F.TAUS) * len(F.KS) * len(F.MECHS)
    assert all(c["strength"] == "strong" for c in grid)
    assert any(c["mechanism"] == "none" for c in grid)   # negative control present
    assert any(c["k"] == 10 for c in grid)               # small-k present


def test_field2_logor_generator_no_crash_on_fallback():
    # Regression: generate_logor must not raise UnboundLocalError when no draw
    # reaches the selection threshold (null + strong step -> few significant).
    import field_bakeoff2 as F2
    import misspec_harness as H2
    for mu in (0.0, 0.4):
        for mech in ("none", "step", "copas"):
            df, m = F2.generate_logor(mech, "strong", H2.Spec(mu=mu, tau=0.15, k=10), 999)
            assert len(df) >= 1 and m == mu
            assert set(["yi", "sei", "quality_score", "study_id"]).issubset(df.columns)


def test_field2_auto_selector_and_grids():
    import field_bakeoff2 as F2
    # tau-aware selector picks ens_calib at low tau_hat, petgate at high.
    assert F2.TAU0 == 0.2
    assert "adaptshrink_auto" in F2.SCORED and "adaptshrink_petgate" in F2.SCORED
    # broadened grids expose the new axes
    cont = F2.build_grid("continuous")
    logor = F2.build_grid("logor")
    assert any(c["k"] == 5 for c in cont)              # small k
    assert any(c["tau"] == 0.5 for c in cont)          # high tau
    assert all(c["outcome"] == "logor" for c in logor) and len(logor) >= 12


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
