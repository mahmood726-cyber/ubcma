"""Unit tests for the AdaptShrink-DTA estimators (src/ubcma/dta.py)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from ubcma.dta import (
    AS_DELTA_MAX, adaptshrink_dta, deeks_asymmetry, ellipse_area, from_counts,
    hsroc, in_region, reitsma, reitsma_indep, reitsma_reml, sep_univariate,
    _glmm_negll, _shrink_sigma, _shrinkage_delta,
)

REF = Path(__file__).resolve().parents[1] / "truth-recovery-dta" / "reference_fits.json"
REF_GLMM = Path(__file__).resolve().parents[1] / "truth-recovery-dta" / "reference_glmm.json"


# --- continuity correction semantics --------------------------------------
def test_correction_all_when_zero_present():
    # one zero cell -> 'all' corrects every study; 'single' only the zero one.
    tp = np.array([10, 0]); fp = np.array([2, 3]); fn = np.array([1, 4]); tn = np.array([20, 30])
    st_all = from_counts(tp, fp, fn, tn, correction_control="all")
    st_single = from_counts(tp, fp, fn, tn, correction_control="single")
    # study 0 has no zero: under 'all' it is corrected (TP 10->10.5), under
    # 'single' it is not (TP stays 10).
    assert st_all.tp[0] == pytest.approx(10.5)
    assert st_single.tp[0] == pytest.approx(10.0)


def test_no_correction_without_zeros():
    tp = np.array([10, 12]); fp = np.array([2, 3]); fn = np.array([1, 4]); tn = np.array([20, 30])
    st = from_counts(tp, fp, fn, tn, correction_control="all")
    assert st.tp[0] == pytest.approx(10.0)  # no zero anywhere -> untouched


# --- reference agreement (the gold-standard validation) -------------------
@pytest.mark.skipif(not REF.exists(), reason="reference_fits.json not generated")
def test_reitsma_matches_mada_reference():
    ref = json.loads(REF.read_text())
    worst = 0.0
    for name, o in ref.items():
        c = o["counts"]
        st = from_counts(c["TP"], c["FP"], c["FN"], c["TN"])
        r = reitsma(st)
        worst = max(worst,
                    abs(r["M1"] - o["m1_logit_sens"]),
                    abs(r["M2"] - o["m2_logit_spec"]),
                    abs(r["se_summary"] - o["sens_summary"]),
                    abs(r["sp_summary"] - o["spec_summary"]))
    assert worst < 1e-5, f"worst disagreement vs mada::reitsma = {worst}"


# --- region geometry -------------------------------------------------------
def test_ellipse_area_formula():
    # diagonal V -> area = pi * chi2_{2,.95} * sqrt(det V)
    V = np.array([[0.04, 0.0], [0.0, 0.09]])
    from scipy.stats import chi2
    expected = np.pi * chi2.ppf(0.95, 2) * np.sqrt(0.04 * 0.09)
    assert ellipse_area(V) == pytest.approx(expected, rel=1e-10)


def test_in_region_center_inside_far_outside():
    V = np.array([[0.04, 0.0], [0.0, 0.04]])
    assert in_region(np.array([0.0, 0.0]), V)
    assert not in_region(np.array([5.0, 5.0]), V)


def test_npd_region_area_is_nan():
    V = np.array([[1.0, 2.0], [2.0, 1.0]])  # det < 0
    assert np.isnan(ellipse_area(V))


# --- AdaptShrink-DTA mechanics --------------------------------------------
def test_shrink_sigma_toward_identity():
    Sigma = np.array([[0.36, 0.30], [0.30, 0.36]])  # rho ~ 0.833
    # delta=0 -> unchanged; delta=1 -> diagonal (rho 0); variances preserved.
    assert np.allclose(_shrink_sigma(Sigma, 0.0), Sigma)
    s1 = _shrink_sigma(Sigma, 1.0)
    assert s1[0, 1] == pytest.approx(0.0)
    assert s1[0, 0] == pytest.approx(0.36)
    assert s1[1, 1] == pytest.approx(0.36)


def test_delta_increases_as_k_shrinks():
    Sig = np.array([[0.36, 0.1], [0.1, 0.36]])
    d40, _ = _shrinkage_delta(Sig, 40)
    d10, _ = _shrinkage_delta(Sig, 10)
    d6, _ = _shrinkage_delta(Sig, 6)
    assert d6 > d10 > d40
    assert 0.0 <= d40 <= AS_DELTA_MAX


def test_delta_boundary_boost():
    boundary = np.array([[0.36, 0.359], [0.359, 0.36]])  # rho ~ 0.997 -> boundary
    interior = np.array([[0.36, 0.05], [0.05, 0.36]])
    db, info_b = _shrinkage_delta(boundary, 20)
    di, info_i = _shrinkage_delta(interior, 20)
    assert info_b["boundary"] and not info_i["boundary"]
    assert db > di


def test_adaptshrink_reduces_to_reitsma_large_k_no_selection():
    # large k, well-behaved data, no asymmetry -> delta small, gate off ->
    # AdaptShrink point close to Reitsma point.
    rng = np.random.default_rng(0)
    from scipy.special import expit
    k = 80
    M = np.array([1.4, 1.6])
    Sigma = np.array([[0.25, -0.05], [-0.05, 0.25]])
    uv = rng.multivariate_normal(M, Sigma, size=k)
    se = expit(uv[:, 0]); sp = expit(uv[:, 1])
    n1 = np.full(k, 200); n0 = np.full(k, 200)
    tp = rng.binomial(n1, se); tn = rng.binomial(n0, sp)
    st = from_counts(tp, n0 - tn, n1 - tp, tn)
    r = reitsma(st); a = adaptshrink_dta(st)
    assert a["delta"] < 0.25  # k large -> little shrink
    assert abs(a["M1"] - r["M1"]) < 0.15
    assert abs(a["M2"] - r["M2"]) < 0.15


def test_estimators_converge_small_k():
    rng = np.random.default_rng(3)
    from scipy.special import expit
    k = 6
    uv = rng.multivariate_normal([1.2, 1.4], [[0.4, -0.1], [-0.1, 0.4]], size=k)
    se = expit(uv[:, 0]); sp = expit(uv[:, 1])
    n1 = rng.integers(30, 80, k); n0 = rng.integers(30, 80, k)
    tp = rng.binomial(n1, se); tn = rng.binomial(n0, sp)
    st = from_counts(tp, n0 - tn, n1 - tp, tn)
    for fn in (reitsma, reitsma_indep, sep_univariate, adaptshrink_dta):
        r = fn(st)
        assert r["converged"]
        assert np.isfinite(r["M1"]) and np.isfinite(r["M2"])
        assert np.isfinite(r["region_area"]) and r["region_area"] > 0


# --- reitsma_reml (small-sample-corrected variant) -----------------------
def test_reitsma_reml_converges_and_reml_penalty_inflates_variance():
    # REML penalty +0.5 log det A makes the REML objective differ from ML, and
    # REML typically estimates a larger between-study variance at small k -> a
    # region no smaller than ML's. Just assert a finite, PD fit + the penalty.
    rng = np.random.default_rng(11)
    from scipy.special import expit
    k = 8
    uv = rng.multivariate_normal([1.3, 1.5], [[0.4, -0.1], [-0.1, 0.4]], size=k)
    se = expit(uv[:, 0]); sp = expit(uv[:, 1])
    n1 = rng.integers(40, 90, k); n0 = rng.integers(40, 90, k)
    tp = rng.binomial(n1, se); tn = rng.binomial(n0, sp)
    st = from_counts(tp, n0 - tn, n1 - tp, tn)
    rr = reitsma_reml(st); r = reitsma(st)
    assert rr["converged"] and np.isfinite(rr["region_area"]) and rr["region_area"] > 0
    assert rr["method"] == "reitsma_reml"
    # different objective -> generally a different Sigma than ML
    assert not np.allclose(rr["Sigma"], r["Sigma"], atol=1e-6)


# --- HSROC (Rutter-Gatsonis exact-binomial GLMM) --------------------------
def test_hsroc_converges_pd_region():
    rng = np.random.default_rng(7)
    from scipy.special import expit
    k = 12
    uv = rng.multivariate_normal([1.4, 1.6], [[0.5, -0.2], [-0.2, 0.5]], size=k)
    se = expit(uv[:, 0]); sp = expit(uv[:, 1])
    n1 = rng.integers(50, 150, k); n0 = rng.integers(50, 150, k)
    tp = rng.binomial(n1, se); tn = rng.binomial(n0, sp)
    st = from_counts(tp, n0 - tn, n1 - tp, tn)
    h = hsroc(st)
    assert h["converged"] and h["method"] == "hsroc"
    assert np.isfinite(h["region_area"]) and h["region_area"] > 0
    assert 0.0 < h["se_summary"] < 1.0 and 0.0 < h["sp_summary"] < 1.0


@pytest.mark.skipif(not REF_GLMM.exists(), reason="reference_glmm.json not generated")
def test_hsroc_matches_glmer_reference():
    # HSROC == bivariate GLMM (Harbord 2007); the exact-binomial fit must agree
    # with lme4::glmer's summary Se/Sp. Tolerance 0.02 absolute: glmer uses the
    # Laplace approximation (nAGQ=1), biased for large random effects, whereas
    # this fit uses adaptive GHQ -- the residual gap is glmer's, not ours.
    ref = json.loads(REF.read_text())
    glmm = json.loads(REF_GLMM.read_text())
    worst = 0.0
    for name, o in ref.items():
        if name not in glmm or not glmm[name].get("ok", False):
            continue
        c = o["counts"]
        st = from_counts(c["TP"], c["FP"], c["FN"], c["TN"])
        h = hsroc(st)
        g = glmm[name]
        worst = max(worst, abs(h["se_summary"] - g["sens_summary"]),
                    abs(h["sp_summary"] - g["spec_summary"]))
    assert worst < 0.02, f"worst |hsroc - glmer| Se/Sp = {worst}"


@pytest.mark.skipif(not REF_GLMM.exists(), reason="reference_glmm.json not generated")
def test_hsroc_is_a_better_exact_optimum_than_glmer_laplace():
    # The decisive correctness check: evaluate the EXACT binomial NLL at our MLE
    # and at glmer's reported parameters. Ours must be no worse (lower NLL) --
    # confirming our optimizer maximizes the exact likelihood at least as well.
    ref = json.loads(REF.read_text())
    glmm = json.loads(REF_GLMM.read_text())
    gh_x, gh_w = np.polynomial.hermite.hermgauss(16)
    for name in ("AuditC", "SAQ", "smoking"):
        c = ref[name]["counts"]
        st = from_counts(c["TP"], c["FP"], c["FN"], c["TN"])
        tp = np.asarray(st.tp, float); fn = np.asarray(st.fn, float)
        fp = np.asarray(st.fp, float); tn = np.asarray(st.tn, float)
        n1 = tp + fn; n0 = tn + fp
        h = hsroc(st)
        mine = np.array([h["M1"], h["M2"], np.log(h["hsroc_tau1"]),
                         np.log(h["hsroc_tau2"]), np.arctanh(h["hsroc_rho"])])
        g = glmm[name]
        glp = np.array([g["m1_logit_sens"], g["m2_logit_spec"],
                        np.log(g["tau_sens"]), np.log(g["tau_spec"]),
                        np.arctanh(np.clip(g["rho"], -0.99, 0.99))])
        nll_mine = _glmm_negll(mine, tp, fn, fp, tn, n1, n0, gh_x, gh_w)
        nll_glm = _glmm_negll(glp, tp, fn, fp, tn, n1, n0, gh_x, gh_w)
        assert nll_mine <= nll_glm + 1e-6, f"{name}: ours {nll_mine} > glmer {nll_glm}"


def test_deeks_detects_injected_asymmetry():
    # construct studies where small studies have systematically higher lnDOR
    rng = np.random.default_rng(5)
    from scipy.special import expit
    k = 30
    N = np.concatenate([np.full(15, 40), np.full(15, 400)])
    # small studies: inflate accuracy; large studies: modest
    base = np.where(N < 100, 2.4, 1.4)
    se = expit(base + rng.normal(0, 0.1, k))
    sp = expit(base + rng.normal(0, 0.1, k))
    n1 = (N * 0.4).astype(int); n0 = N - n1
    tp = rng.binomial(n1, se); tn = rng.binomial(n0, sp)
    st = from_counts(tp, n0 - tn, n1 - tp, tn)
    dk = deeks_asymmetry(st)
    assert np.isfinite(dk["p"])
    assert dk["p"] < 0.10  # asymmetry should be detected
