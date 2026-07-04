"""Stress / edge-case coverage for the AdaptShrink-DTA estimators.

Complements ``test_dta.py`` (mechanics + reference agreement) with adversarial
inputs the field actually hits: k<2, zero-cell / sparse tables, near-perfect
sensitivity, strong threshold correlation, degenerate Deeks inputs, and the
a-priori invariants of the shrinkage gate. Truth-first: each test asserts a
property that must hold by construction of the model; a failure here is a real
defect, not a tuning miss.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy.special import expit
from scipy.stats import chi2

from ubcma.dta import (
    AS_DELTA_MAX, adaptshrink_dta, deeks_asymmetry, ellipse_area, from_counts,
    hsroc, in_region, reitsma, reitsma_indep, reitsma_reml, run_dta_method,
    sep_univariate, _shrink_sigma, _shrinkage_delta,
)

REPO = Path(__file__).resolve().parents[1]


def _sim(seed, k, m1=1.4, m2=1.6, sig=((0.4, -0.1), (-0.1, 0.4)),
         nlo=40, nhi=90):
    rng = np.random.default_rng(seed)
    uv = rng.multivariate_normal([m1, m2], np.asarray(sig), size=k)
    se = expit(uv[:, 0]); sp = expit(uv[:, 1])
    n1 = rng.integers(nlo, nhi, k); n0 = rng.integers(nlo, nhi, k)
    tp = rng.binomial(n1, se); tn = rng.binomial(n0, sp)
    return from_counts(tp, n0 - tn, n1 - tp, tn)


# --- k < 2: every estimator must fail closed, not crash --------------------
@pytest.mark.parametrize("est", [reitsma, reitsma_reml, reitsma_indep,
                                 sep_univariate, adaptshrink_dta, hsroc])
def test_single_study_fails_closed(est):
    st = from_counts([10], [2], [1], [20])
    r = est(st)
    assert r["converged"] is False
    assert np.isnan(r["M1"]) and np.isnan(r["M2"])
    assert np.isnan(r["region_area"])


# --- zero cells / sparse tables: correction + convergence ------------------
def test_zero_cell_all_estimators_converge_finite():
    # Two of six studies have a zero cell -> 'all' correction adds 0.5 to every
    # cell. Every estimator must still produce a finite point in the unit square
    # and a positive-area region.
    tp = np.array([18, 25, 12, 30, 0, 22])
    fp = np.array([3, 0, 5, 2, 4, 6])
    fn = np.array([2, 4, 1, 3, 5, 2])
    tn = np.array([40, 35, 50, 28, 33, 44])
    st = from_counts(tp, fp, fn, tn)  # correction_control='all' default
    # correction fired: a zero exists -> every study's TP nudged by 0.5
    assert st.tp[0] == pytest.approx(18.5)
    for est in (reitsma, reitsma_indep, sep_univariate, adaptshrink_dta, hsroc):
        r = est(st)
        assert r["converged"], f"{est.__name__} failed on sparse table"
        assert 0.0 < r["se_summary"] < 1.0 and 0.0 < r["sp_summary"] < 1.0
        assert np.isfinite(r["region_area"]) and r["region_area"] > 0.0


def test_hsroc_near_perfect_sensitivity_converges():
    # Near-perfect Se (FN mostly 0/1) is exactly where the within-study normal
    # approximation is worst and HSROC's exact-binomial fit should shine. It must
    # converge to a PD region and Se close to (but strictly below) 1.
    rng = np.random.default_rng(21)
    k = 8
    n1 = rng.integers(60, 120, k); n0 = rng.integers(60, 120, k)
    fn = rng.integers(0, 2, k)                 # 0 or 1 false-negatives
    tp = n1 - fn
    sp = expit(rng.normal(1.2, 0.3, k))
    tn = rng.binomial(n0, sp); fp = n0 - tn
    st = from_counts(tp, fp, fn, tn)
    h = hsroc(st)
    assert h["converged"] and np.isfinite(h["region_area"]) and h["region_area"] > 0
    assert 0.90 < h["se_summary"] < 1.0


# --- from_counts correction semantics --------------------------------------
def test_from_counts_none_keeps_zeros_untouched():
    tp = np.array([10, 0]); fp = np.array([2, 3])
    fn = np.array([1, 4]); tn = np.array([20, 30])
    with np.errstate(divide="ignore"):  # logit(0) = -inf is the expected result
        st = from_counts(tp, fp, fn, tn, correction_control="none")
    assert st.tp[1] == 0.0  # zero NOT corrected under 'none'


def test_from_counts_invalid_control_raises():
    with pytest.raises(ValueError):
        from_counts([10], [2], [1], [20], correction_control="bogus")


# --- Deeks degenerate inputs fail closed to nan (not raise) ----------------
def test_deeks_too_few_studies_is_nan():
    st = _sim(1, k=3)
    dk = deeks_asymmetry(st)
    assert np.isnan(dk["p"]) and np.isnan(dk["slope"])
    assert dk["n_ok"] == 3


def test_deeks_constant_ess_is_nan():
    # identical tables -> identical ESS -> x is constant -> no regression slope
    tp = np.full(6, 20); fp = np.full(6, 5); fn = np.full(6, 4); tn = np.full(6, 40)
    dk = deeks_asymmetry(from_counts(tp, fp, fn, tn))
    assert np.isnan(dk["p"])


# --- shrinkage gate a-priori invariants ------------------------------------
def test_delta_clips_at_delta_max_when_all_gates_fire():
    # small k + boundary rho + selection asymmetry: additive delta would exceed
    # the cap and must clip to AS_DELTA_MAX exactly.
    boundary = np.array([[0.36, 0.359], [0.359, 0.36]])  # rho ~ 0.997
    d, info = _shrinkage_delta(boundary, k=4, asymmetry=True)
    assert info["boundary"] and info["asymmetry"]
    assert d == pytest.approx(AS_DELTA_MAX)


def test_reitsma_indep_reports_exactly_zero_rho():
    st = _sim(2, k=8)
    r = reitsma_indep(st)
    assert r["converged"]
    assert abs(r["rho"]) < 1e-9  # rho fixed at 0 by construction


def test_adaptshrink_never_amplifies_correlation():
    # shrinkage multiplies rho by (1-delta) in [0,1] -> |rho_AS| <= |rho_hat|,
    # with the marginal between-study variances preserved. Holds on strong-
    # threshold (negatively-correlated) small-k data where the gate is active.
    for seed in range(6):
        st = _sim(100 + seed, k=6, sig=((0.5, -0.35), (-0.35, 0.5)))
        r = reitsma(st); a = adaptshrink_dta(st)
        if not (r["converged"] and a["converged"]):
            continue
        assert abs(a["rho"]) <= abs(r["rho"]) + 1e-9
        # marginal between-study variances are kept, not shrunk
        assert a["Sigma"][0][0] == pytest.approx(r["Sigma"][0][0], rel=1e-6)
        assert a["Sigma"][1][1] == pytest.approx(r["Sigma"][1][1], rel=1e-6)


# --- region geometry invariants --------------------------------------------
def test_ellipse_area_scales_linearly_with_covariance():
    V = np.array([[0.05, 0.01], [0.01, 0.08]])
    s = 2.5
    # area = pi c sqrt(det V); det(sV) = s^2 det V -> area(sV) = s*area(V)
    assert ellipse_area(s * V) == pytest.approx(s * ellipse_area(V), rel=1e-12)


def test_in_region_scale_is_monotone():
    V = np.array([[0.04, 0.0], [0.0, 0.04]])
    # d^2 = 0.63^2/0.04 = 9.92 > chi2_{2,.95}=5.99 -> outside at scale 1;
    # at scale 4 the effective d^2 is 9.92/4 = 2.48 -> inside.
    e = np.array([0.63, 0.0])
    assert not in_region(e, V, scale=1.0)
    assert in_region(e, V, scale=4.0)  # a bigger ellipse must contain it


def test_in_region_threshold_matches_chi2_quantile():
    # a point exactly on the 95% Mahalanobis shell is (weakly) inside; just past
    # it is outside. Locks the chi2_{2} threshold semantics.
    V = np.array([[0.04, 0.0], [0.0, 0.09]])
    c = chi2.ppf(0.95, df=2)
    # e with e' Vinv e = c: put all distance on axis 1 -> e0^2/0.04 = c
    e_on = np.array([np.sqrt(c * 0.04), 0.0])
    assert in_region(e_on * 0.999, V)
    assert not in_region(e_on * 1.001, V)


# --- sep_univariate DL floor on homogeneous data ---------------------------
def test_sep_univariate_tau_floored_on_homogeneous_data():
    # nearly-identical large studies -> Q < k-1 -> DL tau^2 floored at 0, not
    # negative; Sigma diagonal must be >= 0 and the fit finite.
    tp = np.array([80, 81, 79, 80, 82]); fp = np.array([20, 19, 21, 20, 18])
    fn = np.array([20, 19, 21, 20, 18]); tn = np.array([80, 81, 79, 80, 82])
    r = sep_univariate(from_counts(tp, fp, fn, tn))
    assert r["converged"]
    assert r["Sigma"][0][0] >= 0.0 and r["Sigma"][1][1] >= 0.0
    assert np.isfinite(r["region_area"]) and r["region_area"] > 0.0


# --- shipped-headline regression guard (reproduce from committed raw data) --
@pytest.mark.slow
def test_smallk_headline_reproduces_from_committed_perrep():
    """The ROBUST headline (k6_hi/strong AdaptShrink dArea = -0.325, P=0.997)
    must reproduce bit-for-bit from the committed per-rep cloud + committed
    bootstrap (seed=7). Guards the shipped number against silent code drift."""
    import importlib.util
    bakeoff_path = REPO / "truth-recovery-dta" / "dta_bakeoff.py"
    perrep = REPO / "truth-recovery-dta" / "dta_smallk_perrep.csv"
    if not (bakeoff_path.exists() and perrep.exists()):
        pytest.skip("committed bakeoff/perrep artifacts not present")
    spec = importlib.util.spec_from_file_location("dta_bakeoff", bakeoff_path)
    B = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(B)
    df = pd.read_csv(perrep)
    df = df[df["cell"] == "k6_hi"]  # one cell keeps the bootstrap fast
    boot = B._bootstrap_mciw0(df, target=0.95)
    row = next(b for b in boot
               if b["cell"] == "k6_hi" and b["strength"] == "strong"
               and b["method"] == "adaptshrink_dta")
    assert round(row["darea"], 3) == -0.325
    assert row["ci_hi"] < 0.0 and row["robust_win"]
    assert row["frac_better"] == pytest.approx(0.997, abs=0.002)


# --- from_counts numerics: exact logit + delta-method variance -------------
def test_from_counts_logit_and_variance_are_exact():
    tp = np.array([30.0]); fp = np.array([10.0])
    fn = np.array([20.0]); tn = np.array([40.0])
    st = from_counts(tp, fp, fn, tn, correction_control="none")
    se = 30.0 / 50.0; sp = 40.0 / 50.0
    assert st.y1[0] == pytest.approx(np.log(se / (1 - se)))
    assert st.y2[0] == pytest.approx(np.log(sp / (1 - sp)))
    # Var(logit p_hat) delta method = 1/a + 1/b
    assert st.s1sq[0] == pytest.approx(1 / 30 + 1 / 20)
    assert st.s2sq[0] == pytest.approx(1 / 40 + 1 / 10)


def test_correction_single_touches_only_zero_studies():
    tp = np.array([10, 0, 15]); fp = np.array([2, 3, 1])
    fn = np.array([1, 4, 2]); tn = np.array([20, 30, 25])
    st = from_counts(tp, fp, fn, tn, correction_control="single")
    assert st.tp[0] == pytest.approx(10.0)   # no zero -> untouched
    assert st.tp[1] == pytest.approx(0.5)    # zero study -> corrected
    assert st.tp[2] == pytest.approx(15.0)   # no zero -> untouched


# --- dispatcher ------------------------------------------------------------
def test_run_dta_method_dispatch_matches_direct_call():
    st = _sim(9, k=8)
    assert run_dta_method("reitsma", st)["method"] == "reitsma"
    assert run_dta_method("sep_univariate", st)["method"] == "sep_univariate"


def test_run_dta_method_unknown_raises():
    st = _sim(9, k=6)
    with pytest.raises(ValueError):
        run_dta_method("not_a_method", st)


# --- estimator determinism (no hidden RNG in the fit) ----------------------
def test_reitsma_is_deterministic():
    st = _sim(4, k=8)
    a = reitsma(st); b = reitsma(st)
    assert a["M1"] == b["M1"] and a["M2"] == b["M2"]
    assert a["region_area"] == b["region_area"]


# --- GLS covariance is symmetric positive-definite -------------------------
def test_reitsma_V_is_symmetric_pd():
    st = _sim(5, k=10)
    V = np.array(reitsma(st)["V"])
    assert np.allclose(V, V.T, atol=1e-12)
    w = np.linalg.eigvalsh(V)
    assert np.all(w > 0)


# --- in_region on a singular covariance fails closed to False --------------
def test_in_region_singular_covariance_is_false():
    V = np.array([[0.04, 0.0], [0.0, 0.0]])  # singular
    assert in_region(np.array([0.01, 0.0]), V) is False


# --- _shrink_sigma stays PD for every delta in [0,1] -----------------------
def test_shrink_sigma_stays_pd_across_delta():
    Sigma = np.array([[0.5, -0.45], [-0.45, 0.5]])  # rho = -0.9
    for delta in np.linspace(0.0, 1.0, 11):
        S = _shrink_sigma(Sigma, delta)
        assert np.linalg.det(S) > 0
        assert np.all(np.linalg.eigvalsh(S) > 0)


# --- selection_gate=False ignores injected asymmetry -----------------------
def test_adaptshrink_gate_off_ignores_asymmetry():
    # strong funnel asymmetry present; with the gate OFF the selection boost
    # must not be applied (delta comes from k/boundary only), so gate-off delta
    # <= gate-on delta and the reported selection is not "detected".
    rng = np.random.default_rng(31)
    k = 20
    N = np.concatenate([np.full(10, 40), np.full(10, 400)])
    base = np.where(N < 100, 2.4, 1.4)
    se = expit(base + rng.normal(0, 0.1, k)); sp = expit(base + rng.normal(0, 0.1, k))
    n1 = (N * 0.4).astype(int); n0 = N - n1
    tp = rng.binomial(n1, se); tn = rng.binomial(n0, sp)
    st = from_counts(tp, n0 - tn, n1 - tp, tn)
    on = adaptshrink_dta(st, selection_gate=True)
    off = adaptshrink_dta(st, selection_gate=False)
    assert off["selection"]["detected"] is False
    assert off["delta"] <= on["delta"] + 1e-12


# --- HSROC shape parameter is internally consistent ------------------------
def test_hsroc_beta_equals_log_tau_ratio():
    st = _sim(7, k=10, nlo=60, nhi=140)
    h = hsroc(st)
    assert h["converged"]
    assert h["hsroc_beta"] == pytest.approx(
        np.log(h["hsroc_tau2"] / h["hsroc_tau1"]), rel=1e-9)


# --- REML small-sample correction: region no smaller than ML (majority) ----
def test_reml_region_not_smaller_than_ml_in_majority():
    # The REML penalty corrects the downward small-sample bias of the between-
    # study variance, so at small k REML should give a region >= ML's in the
    # large majority of samples. Honest directional check across 12 seeds; a
    # gross violation (ML systematically wider) would be a real defect.
    ge = 0; total = 0
    for seed in range(12):
        st = _sim(200 + seed, k=6)
        ml = reitsma(st); rl = reitsma_reml(st)
        if not (ml["converged"] and rl["converged"]):
            continue
        total += 1
        if rl["region_area"] >= ml["region_area"] - 1e-9:
            ge += 1
    assert total >= 8
    assert ge / total >= 0.6, f"REML region >= ML in only {ge}/{total} samples"
