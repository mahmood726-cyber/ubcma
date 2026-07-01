"""Tests for the modern publication-bias comparators.

Run: PYTHONPATH=src python -m pytest tests/test_modern_comparators.py -q

Validation strategy (offline, no R): (1) determinism; (2) the conditional-pp
formula matches an independent agy/Codex derivation; (3) under FIXED-effect step
selection each estimator recovers the truth far better than the naive selected
mean; (4) graceful degradation on tiny/degenerate inputs. The point estimates
were additionally cross-checked head-to-head against an independently-derived
Codex implementation (agreement ~0.000 for p_curve/vevea).
"""
import numpy as np
import pytest

from ubcma.modern_comparators import (
    C,
    _cond_pp,
    p_curve,
    p_uniform_star,
    vevea_hedges_step,
)


def _step_selected(mu, tau, k, rng, keep_ns=0.25, pool=1500):
    se = rng.uniform(0.05, 0.25, size=pool)
    th = rng.normal(mu, tau, size=pool)
    y = rng.normal(th, se)
    sig = y / se >= C
    keep = np.where(sig, True, rng.uniform(size=pool) < keep_ns)
    return y[keep][:k], se[keep][:k]


def test_cond_pp_formula():
    # q_i(mu) = sf((y-mu)/se) / sf(c - mu/se); at mu=0 reduces to sf(z)/sf(c).
    y = np.array([0.4, 0.5]); se = np.array([0.1, 0.1])
    from scipy.stats import norm
    got = _cond_pp(y, se, 0.0)
    exp = norm.sf(y / se) / norm.sf(C)
    assert np.allclose(got, exp, atol=1e-12)
    # conditional pp in [0,1] and monotonically INCREASES with mu (a fixed
    # observed z becomes less extreme as the assumed true effect rises).
    assert np.all((got >= 0) & (got <= 1))
    assert np.all(_cond_pp(y, se, 0.5) > got)


def test_determinism():
    rng = np.random.default_rng(0)
    y, se = _step_selected(0.3, 0.0, 60, rng)
    for fn in (p_curve, p_uniform_star, vevea_hedges_step):
        a, b = fn(y, se), fn(y, se)
        assert a["mu"] == b["mu"]
        assert (a["ci_low"], a["ci_high"]) == (b["ci_low"], b["ci_high"])


@pytest.mark.parametrize("fn", [p_curve, p_uniform_star, vevea_hedges_step])
def test_recovers_truth_under_fixed_effect_selection(fn):
    # Fixed effect (tau=0): every method should beat the (upward-biased) naive
    # selected mean, averaged over seeds.
    true_mu = 0.3
    naive_err, meth_err = [], []
    for s in range(12):
        rng = np.random.default_rng(100 + s)
        y, se = _step_selected(true_mu, 0.0, 70, rng)
        naive_err.append(abs(float(np.mean(y)) - true_mu))
        r = fn(y, se)
        if r["converged"] and np.isfinite(r["mu"]):
            meth_err.append(abs(r["mu"] - true_mu))
    assert len(meth_err) >= 8
    assert np.mean(meth_err) < np.mean(naive_err)


def test_pcurve_overestimates_under_heterogeneity():
    # Documented property: significant-only p-curve is biased UP when tau>0.
    # This is the WHY for p-uniform*/selection models; pin it so a "fix" that
    # silently removes the property is caught.
    true_mu = 0.0
    errs = []
    for s in range(10):
        rng = np.random.default_rng(200 + s)
        y, se = _step_selected(true_mu, 0.15, 80, rng)
        r = p_curve(y, se)
        if r["converged"]:
            errs.append(r["mu"] - true_mu)
    assert np.mean(errs) > 0.03  # systematically above truth


def test_ci_brackets_point_and_finite_most_cells():
    rng = np.random.default_rng(7)
    n_conv = 0
    for s in range(10):
        y, se = _step_selected(0.3, 0.1, 60, np.random.default_rng(300 + s))
        for fn in (p_curve, p_uniform_star, vevea_hedges_step):
            r = fn(y, se)
            if r["converged"]:
                n_conv += 1
                assert r["ci_low"] <= r["mu"] <= r["ci_high"]
    assert n_conv >= 24  # most of 30 fits converge with a finite bracketing CI


def test_degenerate_inputs():
    # k<4 / no-significant-studies must degrade gracefully (no exception).
    y = np.array([0.1, 0.2]); se = np.array([0.1, 0.1])
    for fn in (p_curve, p_uniform_star, vevea_hedges_step):
        r = fn(y, se)
        assert ("converged" in r) and (r["converged"] in (True, False))


def test_dispatcher_exposes_modern_methods():
    import pandas as pd

    from ubcma.data import MetaAnalysisDataset
    from ubcma.simulation_study import _run_method
    rng = np.random.default_rng(1)
    y, se = _step_selected(0.3, 0.1, 30, rng)
    k = len(y)
    df = pd.DataFrame({"study_id": [f"s{i}" for i in range(k)], "yi": y, "sei": se,
                       "rob_selection": np.zeros(k), "rob_measurement": np.zeros(k),
                       "rob_reporting": np.zeros(k), "quality_score": np.zeros(k)})
    data = MetaAnalysisDataset.from_dataframe(
        df, effect_col="yi", se_col="sei", study_id_col="study_id",
        quality_cols=["rob_selection", "rob_measurement", "rob_reporting"])
    for m in ("p_curve", "p_uniform_star", "vevea_hedges", "henmi_copas",
              "adaptshrink_solo"):
        r = _run_method(m, y, se, df["quality_score"].to_numpy(), data)
        assert "mu_hat" in r and "converged" in r


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
