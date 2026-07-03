"""Selection-robust point estimators and calibrated confidence intervals.

This module adds three things the classical UBCMA comparator set lacked:

1. ``henmi_copas`` -- the ACTUAL Henmi & Copas (2010) confidence interval
   (a faithful port of ``metafor::hc``), robust to publication bias.  The
   pre-existing ``comparators.copas_selection`` is the Copas & Shi (2000)
   selection-MLE, a different and numerically fragile method; the named
   adversary in the truth-recovery bake-off is Henmi-Copas, so we implement it
   properly here and validate it against metafor to 1e-6.

2. ``adaptshrink`` -- a selection-robust POINT estimator.  It adaptively
   shrinks the efficient random-effects mean toward the PET small-study-effect
   corrected intercept, with the shrinkage weight driven by the strength of
   funnel-plot asymmetry.  No asymmetry -> behaves like the efficient RE mean;
   strong asymmetry -> trusts the bias-corrected intercept.  This trades a
   little variance for a large reduction in selection bias, which is what makes
   honest coverage of the true mu affordable at a narrow width.

3. ``conformal_ci`` -- a "conformal-forward" confidence interval for mu.  It
   calibrates the interval half-width from the empirical leave-one-study-out
   variability of the point estimator (a jackknife / conformal spread) rather
   than from a parametric likelihood.  Because it never assumes the selection
   mechanism is the one the model posits, it stays honest under
   misspecification, and because it uses the actual wobble of a bias-corrected
   centre it stays narrow.

Everything here is deterministic given (y, se): no RNG, fully reproducible.
"""
from __future__ import annotations

from typing import Any, Callable

import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq, minimize
from scipy.stats import gamma as gamma_dist
from scipy.stats import norm
from scipy.stats import t as t_dist

__all__ = [
    "fixed_effect",
    "dl_tau2",
    "pet_fit",
    "henmi_copas",
    "adaptshrink",
    "conformal_ci",
    "adaptshrink_conformal",
]


# ---------------------------------------------------------------------------
# Basic building blocks
# ---------------------------------------------------------------------------

def fixed_effect(y: np.ndarray, se: np.ndarray) -> tuple[float, np.ndarray]:
    """Inverse-variance (equal-effects) weighted mean and its weights."""
    w = 1.0 / np.square(se)
    mu = float(np.sum(w * y) / np.sum(w))
    return mu, w


def dl_tau2(y: np.ndarray, se: np.ndarray) -> dict[str, float]:
    """DerSimonian-Laird tau^2 plus the fixed-effect mean and Q used to get it."""
    w = 1.0 / np.square(se)
    sw = np.sum(w)
    mu_fe = float(np.sum(w * y) / sw)
    Q = float(np.sum(w * np.square(y - mu_fe)))
    c = float(sw - np.sum(np.square(w)) / sw)
    tau2 = max(0.0, (Q - (len(y) - 1)) / c) if c > 1e-12 else 0.0
    return {"tau2": tau2, "mu_fe": mu_fe, "Q": Q, "c": c, "sw": sw}


def random_effects(y: np.ndarray, se: np.ndarray) -> dict[str, float]:
    """DL random-effects mean and its model SE."""
    d = dl_tau2(y, se)
    w = 1.0 / (np.square(se) + d["tau2"])
    mu = float(np.sum(w * y) / np.sum(w))
    se_mu = float(np.sqrt(1.0 / np.sum(w)))
    return {"mu": mu, "se": se_mu, "tau2": d["tau2"]}


def pet_fit(y: np.ndarray, se: np.ndarray) -> dict[str, float]:
    """PET (precision-effect test) WLS fit: y = b0 + b1*se, weighted by 1/se^2.

    ``b0`` is the small-study-effect bias-corrected effect (the effect a study
    of infinite precision would report).  ``t1`` is the asymmetry t-statistic
    (the Egger-type small-study-effect signal).  Dispersion is estimated
    multiplicatively from the weighted residuals, matching standard PET-PEESE /
    Egger practice.
    """
    k = len(y)
    w = 1.0 / np.square(se)
    X = np.column_stack([np.ones(k), se])
    xtw = X.T * w
    xtwx = xtw @ X
    cov = np.linalg.pinv(xtwx)
    beta = cov @ (xtw @ y)
    resid = y - X @ beta
    dof = max(k - 2, 1)
    sigma2 = float(np.sum(w * np.square(resid)) / dof)
    covb = cov * sigma2
    b0, b1 = float(beta[0]), float(beta[1])
    se_b0 = float(np.sqrt(max(covb[0, 0], 1e-18)))
    se_b1 = float(np.sqrt(max(covb[1, 1], 1e-18)))
    t1 = b1 / se_b1 if se_b1 > 0 else 0.0
    return {"b0": b0, "b1": b1, "t1": float(t1), "se_b0": se_b0, "se_b1": se_b1,
            "dof": dof}


def vevea_hedges(y: np.ndarray, se: np.ndarray, cut: float = 0.025) -> dict[str, float]:
    """Vevea & Hedges (1995) step weight-function selection model (2-interval).

    Models publication probability as a step function of the one-sided p-value
    p_i = 1 - Phi(y_i/se_i):  a significant study (p <= `cut`) has selection weight
    1; a non-significant study has weight omega in (0, 1].  The published density is
    g_i(y) = w(y) f_i(y) / A_i(mu, tau2, omega), where f_i = N(mu, se_i^2 + tau2) and
    A_i = P(sig | f_i) + omega * P(not sig | f_i) is the per-study normalising
    constant that makes the selection model proper.  We maximise the resulting
    weighted log-likelihood over (mu, tau2 >= 0, omega in (0,1]) -- the classic
    weight-function selection-model bias correction, purpose-built for STEP
    selection (Vevea-Hedges is the data-generating model of the 'step' mechanism).

    Returns mu (selection-corrected mean), its se (numerical-Hessian), tau2, omega.
    """
    y = np.asarray(y, float); se = np.asarray(se, float)
    k = len(y)
    zc = norm.ppf(1.0 - cut)                        # one-sided sig cutoff on y/se
    sig = (y / se) > zc                             # published-as-significant mask
    y0 = float(np.sum(y / se**2) / np.sum(1.0 / se**2))   # FE start

    def negll(theta):
        mu = theta[0]; tau2 = np.exp(theta[1]); omega = 1.0 / (1.0 + np.exp(-theta[2]))
        v = se**2 + tau2; sd = np.sqrt(v)
        # marginal density of each observed y_i under N(mu, v)
        logf = -0.5 * np.log(2 * np.pi * v) - 0.5 * (y - mu)**2 / v
        # P(significant | f_i) = P(y > zc*se) under N(mu, v)
        p_sig = 1.0 - norm.cdf((zc * se - mu) / sd)
        A = p_sig + omega * (1.0 - p_sig)           # per-study normaliser in (0,1]
        A = np.clip(A, 1e-12, None)
        logw = np.where(sig, 0.0, np.log(max(omega, 1e-12)))
        ll = np.sum(logw + logf - np.log(A))
        return -ll if np.isfinite(ll) else 1e12

    best = None
    for t2_0 in (-4.0, -1.0, 1.0):                  # multistart over tau2
        for w0 in (0.0, -1.5):                      # omega ~ 0.5, ~0.18
            try:
                r = minimize(negll, np.array([y0, t2_0, w0]), method="Nelder-Mead",
                             options=dict(xatol=1e-7, fatol=1e-7, maxiter=4000))
                if best is None or r.fun < best.fun:
                    best = r
            except Exception:
                continue
    if best is None:
        return {"mu": y0, "se": float(np.sqrt(1.0 / np.sum(1.0 / se**2))), "tau2": 0.0, "omega": 1.0}
    mu = float(best.x[0]); tau2 = float(np.exp(best.x[1])); omega = float(1.0 / (1.0 + np.exp(-best.x[2])))
    # SE of mu from the numerical second derivative of the profile in mu
    h = 1e-4
    f0 = negll(best.x)
    xp = best.x.copy(); xp[0] += h; fp = negll(xp)
    xm = best.x.copy(); xm[0] -= h; fm = negll(xm)
    curv = (fp - 2 * f0 + fm) / h**2
    se_mu = float(np.sqrt(1.0 / curv)) if curv > 1e-9 else float(np.sqrt(1.0 / np.sum(1.0 / se**2)))
    return {"mu": mu, "se": se_mu, "tau2": tau2, "omega": omega}


# ---------------------------------------------------------------------------
# Henmi & Copas (2010) -- faithful port of metafor::hc
# ---------------------------------------------------------------------------

def henmi_copas(y: np.ndarray, se: np.ndarray, alpha: float = 0.05) -> dict[str, Any]:
    """Henmi & Copas (2010) confidence interval, robust to publication bias.

    Faithful port of ``metafor::hc`` (v5.0-1).  The point estimate is the
    fixed-effect inverse-variance weighted mean (less sensitive to selection
    because it down-weights the small, most-selected studies); heterogeneity
    enters only through the variance.  The CI multiplier ``u0`` is NOT a t- or
    z-quantile: Henmi-Copas derive the reference distribution of the pivot from
    the joint distribution of (beta, Q), approximating Q by a gamma whose
    shape/scale depend on the pivot location, and solve for the quantile by
    integrating against the normal and root-finding.  We reproduce that exactly.

    Validated against ``metafor::hc`` to < 1e-6 (see
    ``truth-recovery/validate_henmi_copas.R`` and ``test_robust_methods.py``).
    """
    k = len(y)
    if k < 2:
        return {"mu": float(y[0]) if k else float("nan"), "se": float("nan"),
                "tau": 0.0, "ci_low": float("nan"), "ci_high": float("nan"),
                "u0": float("nan")}
    vi = np.square(se)
    wi = 1.0 / vi
    W1 = float(np.sum(wi))
    W2 = float(np.sum(wi ** 2) / W1)
    W3 = float(np.sum(wi ** 3) / W1)
    W4 = float(np.sum(wi ** 4) / W1)
    beta = float(np.sum(wi * y) / W1)
    Q = float(np.sum(wi * (y - beta) ** 2))
    tau2 = max(0.0, (Q - (k - 1)) / (W1 - W2)) if (W1 - W2) > 1e-12 else 0.0

    vb = (tau2 * W2 + 1.0) / W1
    se_beta = float(np.sqrt(vb))
    VR = 1.0 + tau2 * W2
    SDR = float(np.sqrt(VR))

    def EQ(r: float) -> float:
        return ((k - 1) + tau2 * (W1 - W2)
                + tau2 ** 2 * ((1.0 / VR ** 2) * r ** 2 - 1.0 / VR) * (W3 - W2 ** 2))

    def VQ(r: float) -> float:
        rsq = r ** 2
        recipvr2 = 1.0 / VR ** 2
        return (2 * (k - 1) + 4 * tau2 * (W1 - W2)
                + 2 * tau2 ** 2 * (W1 * W2 - 2 * W3 + W2 ** 2)
                + 4 * tau2 ** 2 * (recipvr2 * rsq - 1.0 / VR) * (W3 - W2 ** 2)
                + 4 * tau2 ** 3 * (recipvr2 * rsq - 1.0 / VR) * (W4 - 2 * W2 * W3 + W2 ** 3)
                + 2 * tau2 ** 4 * (recipvr2 - 2 * (1.0 / VR ** 3) * rsq) * (W3 - W2 ** 2) ** 2)

    def scale_fn(r: float) -> float:
        return VQ(r) / EQ(r)

    def shape_fn(r: float) -> float:
        return EQ(r) ** 2 / VQ(r)

    def finv(f: float) -> float:
        return (W1 / W2 - 1.0) * (f ** 2 - 1.0) + (k - 1)

    def eqn(x: float) -> float:
        def integrand(r: float) -> float:
            sc = scale_fn(SDR * r)
            sh = shape_fn(SDR * r)
            q = finv(r / x)
            # pgamma(q, shape, scale); gamma cdf is 0 for q<0
            cdf = gamma_dist.cdf(q, a=sh, scale=sc) if (q > 0 and sc > 0 and sh > 0) else 0.0
            return cdf * norm.pdf(r)
        integral, _ = quad(integrand, x, np.inf, limit=400, epsabs=1e-12, epsrel=1e-12)
        return integral - alpha / 2.0

    try:
        t0 = brentq(eqn, 1e-10, 2.0, xtol=1e-13, rtol=1e-14, maxiter=100000)
    except Exception:
        # fall back to a wide-bracket search if the default upper bound is too low
        t0 = brentq(eqn, 1e-10, 50.0, xtol=1e-13, rtol=1e-14, maxiter=100000)
    u0 = SDR * t0
    return {
        "mu": beta,
        "se": se_beta,
        "tau": float(np.sqrt(tau2)),
        "ci_low": beta - u0 * se_beta,
        "ci_high": beta + u0 * se_beta,
        "u0": float(u0),
    }


# ---------------------------------------------------------------------------
# AdaptShrink -- adaptive bias-corrected point estimator
# ---------------------------------------------------------------------------

def _shrink_weight(t1: float, floor_df: float = 1.0, rule: str = "smooth") -> float:
    """Adaptive shrinkage weight toward the PET intercept, from funnel asymmetry.

    ``t1`` is the funnel-asymmetry t-statistic.  Both rules give omega = 0 when
    there is no asymmetry and omega -> 1 as asymmetry grows, trading the
    efficient RE mean for the bias-corrected PET intercept.

    rule="posjs"  : positive-part James-Stein, omega = max(0, 1 - floor_df/t1^2).
                    Standard and parameter-free, but has a kink at t1^2=floor_df
                    that injects spurious jackknife variance.
    rule="smooth" : omega = t1^2 / (t1^2 + floor_df).  Smooth everywhere (no
                    kink), so leave-one-out estimates wobble less and the
                    conformal interval is tighter at the same bias correction.
                    Default for the headline method.
    """
    t2 = float(t1) ** 2
    if rule == "posjs":
        if t2 <= floor_df:
            return 0.0
        return float(min(1.0, max(0.0, 1.0 - floor_df / t2)))
    # smooth
    return float(t2 / (t2 + floor_df)) if (t2 + floor_df) > 0 else 0.0


def adaptshrink(
    y: np.ndarray,
    se: np.ndarray,
    floor_df: float = 1.0,
    rule: str = "posjs",
) -> dict[str, Any]:
    """Selection-robust point estimate: adaptive shrinkage RE <-> PET intercept.

    Returns the point estimate ``mu`` and the ingredients (omega, the two
    anchors, the asymmetry statistic).  Deterministic given (y, se).
    """
    re = random_effects(y, se)
    pet = pet_fit(y, se)
    omega = _shrink_weight(pet["t1"], floor_df=floor_df, rule=rule)
    mu = (1.0 - omega) * re["mu"] + omega * pet["b0"]
    return {
        "mu": float(mu),
        "omega": float(omega),
        "mu_re": re["mu"],
        "b0_pet": pet["b0"],
        "t1": pet["t1"],
        "tau2": re["tau2"],
    }


# ---------------------------------------------------------------------------
# Conformal-forward confidence interval for mu
# ---------------------------------------------------------------------------

def _jackknife_spread(
    y: np.ndarray, se: np.ndarray, point_fn: Callable[[np.ndarray, np.ndarray], float]
) -> tuple[float, np.ndarray, float]:
    """Leave-one-study-out estimates and the jackknife SE of ``point_fn``."""
    k = len(y)
    loo = np.empty(k)
    for i in range(k):
        idx = np.arange(k) != i
        loo[i] = point_fn(y[idx], se[idx])
    loo_mean = float(np.mean(loo))
    # standard jackknife SE of the estimator
    se_jack = float(np.sqrt((k - 1) / k * np.sum(np.square(loo - loo_mean))))
    return loo_mean, loo, se_jack


def conformal_ci(
    y: np.ndarray,
    se: np.ndarray,
    point_fn: Callable[[np.ndarray, np.ndarray], float],
    alpha: float = 0.05,
    scale: float = 1.0,
    use_t: bool = True,
) -> dict[str, Any]:
    """Conformal-forward CI for mu around an arbitrary point estimator.

    The half-width is calibrated from the empirical leave-one-study-out wobble
    of ``point_fn`` (a jackknife / conformal measure of estimator variability),
    NOT from a parametric likelihood.  ``scale`` is a single multiplicative
    recalibration factor (1.0 = raw / out-of-the-box).  The matched-coverage
    bake-off estimates one ``scale`` per method on a disjoint seed-set so that
    widths are compared at equal coverage.

    Reference distribution: t_{k-1} (use_t) or normal.
    """
    k = len(y)
    mu = float(point_fn(y, se))
    _, _, se_jack = _jackknife_spread(y, se, point_fn)
    if use_t and k > 1:
        crit = float(t_dist.ppf(1.0 - alpha / 2.0, df=k - 1))
    else:
        crit = float(norm.ppf(1.0 - alpha / 2.0))
    half = scale * crit * se_jack
    return {
        "mu": mu,
        "se": se_jack,
        "ci_low": mu - half,
        "ci_high": mu + half,
        "scale": float(scale),
    }


def adaptshrink_conformal(
    y: np.ndarray,
    se: np.ndarray,
    alpha: float = 0.05,
    scale: float = 1.0,
    floor_df: float = 1.0,
    rule: str = "posjs",
) -> dict[str, Any]:
    """The headline method: AdaptShrink centre + conformal-forward interval."""
    point_fn = lambda yy, ss: adaptshrink(yy, ss, floor_df=floor_df, rule=rule)["mu"]
    ci = conformal_ci(y, se, point_fn, alpha=alpha, scale=scale)
    extra = adaptshrink(y, se, floor_df=floor_df, rule=rule)
    ci.update({"omega": extra["omega"], "t1": extra["t1"]})
    return ci
