"""Modern publication-bias-correcting estimators for the field-wide bake-off.

These complement the classical/robust set (DL, REML, HKSJ, PET-PEESE,
trim-and-fill, Copas-Shi, Henmi-Copas) with the selection-aware methods that a
contemporary meta-analyst would reach for:

  * ``vevea_hedges_step`` -- Vevea & Hedges (1995) weight-function selection
    model with a one-sided p-value cutpoint at .025 (a 2-step weight function).
    A genuine selection-model MLE for (mu, tau^2, weight).
  * ``p_uniform_star`` -- van Aert & van Assen (2016) p-uniform*: estimates mu
    from the conditional-uniformity of (significant) studies' p-values, using a
    random-effects conditional likelihood. The modern successor to p-curve /
    p-uniform that is consistent under between-study heterogeneity.
  * ``p_curve`` -- Simonsohn, Nelson & Simmons (2014) p-curve effect estimation
    (significant-positive studies only; conditional p-values uniform at the true
    effect). Included as the well-known significant-only baseline.

All are normal-approximation estimators on (y, se): a study is
"significant-positive" when z = y/se >= c, c = Phi^{-1}(1 - .025) = 1.959964.
Everything is deterministic given (y, se) -- no RNG.

Honest scope notes (NOT implemented here, and why):
  * RoBMA (Bartos & Maier, robust Bayesian model averaging) needs bridge-sampled
    marginal likelihoods over a model ensemble (JAGS/Stan); there is no offline,
    cross-validatable pure-Python port, so faking it would violate truth-first.
    It is therefore declared absent rather than approximated.
  * Mathur & VanderWeele sensitivity targets a DIFFERENT estimand (the proportion
    of true effects above a threshold, and the selection ratio that would explain
    away an effect) -- not a CI for mu -- so it is not commensurable with the
    matched-coverage mu bake-off and is excluded by design, not by omission.
"""
from __future__ import annotations

from typing import Any

import numpy as np
from scipy.optimize import brentq, minimize
from scipy.stats import norm

C = 1.959963984540054  # Phi^{-1}(0.975); one-sided alpha = 0.025 cutpoint
_Z975 = C


def _sig_mask(y: np.ndarray, se: np.ndarray) -> np.ndarray:
    return (y / se) >= C


# ---------------------------------------------------------------------------
# Conditional p-value machinery (shared by p-curve and p-uniform)
# ---------------------------------------------------------------------------

def _cond_pp(y: np.ndarray, se: np.ndarray, mu: float) -> np.ndarray:
    """Conditional p-value of significant studies given significance, at effect mu.

    For a significant-positive study with z_i = y_i/se_i >= c, under y~N(mu,se^2)
    the probability of a result at least as extreme, conditional on being
    significant-positive, is
        pp_i(mu) = P(Z >= z_i) / P(Z >= c),   Z ~ N(mu/se_i, 1)
                 = sf(z_i - mu/se_i) / sf(c - mu/se_i).
    Under the true mu these are iid Uniform(0,1) (probability integral transform).
    """
    ncp = mu / se
    num = norm.sf(y / se - ncp)
    den = norm.sf(C - ncp)
    den = np.maximum(den, 1e-300)
    return np.clip(num / den, 0.0, 1.0)


def p_curve(y: np.ndarray, se: np.ndarray, alpha: float = 0.05,
            mu_lo: float = -2.0, mu_hi: float = 5.0) -> dict[str, Any]:
    """Simonsohn-Nelson-Simmons p-curve effect estimate (significant-only).

    Point estimate: the mu making the conditional p-values of the significant
    studies look Uniform(0,1) in the mean (mean pp = 1/2). CI: the set of mu not
    rejected by the sum statistic S(mu)=sum pp_i, which under mu has mean k/2 and
    variance k/12 (Irwin-Hall), inverted on each side.
    """
    m = _sig_mask(y, se)
    ys, ses = y[m], se[m]
    k = len(ys)
    if k < 1:
        return {"mu": float("nan"), "se": float("nan"), "ci_low": float("nan"),
                "ci_high": float("nan"), "converged": False, "k_sig": 0}

    def g(mu: float) -> float:  # mean pp - 0.5 ; decreasing in mu
        return float(np.mean(_cond_pp(ys, ses, mu)) - 0.5)

    mu_hat = _safe_brentq(g, mu_lo, mu_hi)
    z = norm.ppf(1.0 - alpha / 2.0)

    def S(mu: float) -> float:
        return float(np.sum(_cond_pp(ys, ses, mu)))

    half_band = z * np.sqrt(k / 12.0)
    lo = _safe_brentq(lambda mu: S(mu) - (k / 2.0 + half_band), mu_lo, mu_hi)
    hi = _safe_brentq(lambda mu: S(mu) - (k / 2.0 - half_band), mu_lo, mu_hi)
    ci_low, ci_high = sorted([lo, hi])
    return {"mu": mu_hat, "se": float((ci_high - ci_low) / (2 * z))
            if np.isfinite(ci_low) and np.isfinite(ci_high) else float("nan"),
            "ci_low": ci_low, "ci_high": ci_high,
            "converged": bool(np.isfinite(mu_hat)), "k_sig": int(k)}


def p_uniform_star(y: np.ndarray, se: np.ndarray, alpha: float = 0.05,
                   mu_lo: float = -2.0, mu_hi: float = 5.0) -> dict[str, Any]:
    """van Aert & van Assen (2016) p-uniform* (random-effects, all studies).

    p-uniform* augments the significant-only conditional-uniformity idea with the
    non-significant studies, which removes the heterogeneity bias of the original
    p-uniform/p-curve. We use the conditional-likelihood form: with marginal
    variance v_i = tau^2 + se_i^2, each study contributes the *conditional*
    density of y_i given its observed significance status, under selection that
    keeps significant-positive studies. tau^2 is profiled jointly with mu by ML;
    mu's CI is the profile-likelihood interval. Falls back to the fixed-effect
    conditional estimator when the RE optimiser fails.
    """
    k = len(y)
    if k < 3:
        return _puni_fixed(y, se, alpha, mu_lo, mu_hi)
    m = _sig_mask(y, se)

    def negll(params: np.ndarray) -> float:
        with np.errstate(over="ignore", invalid="ignore"):
            mu, log_t2 = params[0], params[1]
            v = np.square(se) + np.exp(np.clip(log_t2, -30, 20))
            sd = np.sqrt(v)
            # P(significant-positive) under N(mu, v): P(y >= c*se)
            p_sig = np.clip(norm.sf((C * se - mu) / sd), 1e-300, 1.0)
            p_nsig = np.clip(1.0 - p_sig, 1e-300, 1.0)
            dens = norm.pdf(y, loc=mu, scale=sd)
            cond = np.where(m, dens / p_sig, dens / p_nsig)
            val = -np.sum(np.log(np.maximum(cond, 1e-300)))
        return float(val) if np.isfinite(val) else 1e18

    from .model import dersimonian_laird
    base = dersimonian_laird(y, se)
    x0 = np.array([base["mu"], np.log(max(base["tau"] ** 2, 1e-4))])
    res = minimize(negll, x0, method="Nelder-Mead",
                   options={"xatol": 1e-7, "fatol": 1e-9, "maxiter": 4000})
    if not res.success or not np.isfinite(res.fun):
        return _puni_fixed(y, se, alpha, mu_lo, mu_hi)
    mu_hat = float(res.x[0])
    # Primary CI: Wald via inverse observed information (robust); profile fallback.
    se_mu, lo, hi = _wald_ci_mu(negll, res.x, alpha)
    if not (np.isfinite(lo) and np.isfinite(hi)):
        nll_min = float(res.fun)
        crit = 0.5 * norm.ppf(1.0 - alpha / 2.0) ** 2

        def prof(mu: float) -> float:
            r = minimize(lambda lt: negll(np.array([mu, lt[0]])),
                         np.array([res.x[1]]), method="Nelder-Mead",
                         options={"xatol": 1e-6, "fatol": 1e-8, "maxiter": 2000})
            return float(r.fun) - nll_min - crit
        span = max(1.0, 8.0 * abs(mu_hat) + 1.0)
        lo = _safe_brentq(prof, mu_hat - span, mu_hat)
        hi = _safe_brentq(prof, mu_hat, mu_hat + span)
    z = norm.ppf(1.0 - alpha / 2.0)
    return {"mu": mu_hat,
            "se": se_mu if np.isfinite(se_mu)
            else (float((hi - lo) / (2 * z)) if np.isfinite(lo) and np.isfinite(hi)
                  else float("nan")),
            "ci_low": lo, "ci_high": hi,
            "converged": bool(np.isfinite(mu_hat) and np.isfinite(lo) and np.isfinite(hi)),
            "tau2": float(np.exp(res.x[1])), "k_sig": int(m.sum())}


def _puni_fixed(y, se, alpha, mu_lo, mu_hi):
    """Fixed-effect p-uniform (significant-only, mean conditional pp = 1/2)."""
    m = _sig_mask(y, se)
    ys, ses = y[m], se[m]
    k = len(ys)
    if k < 1:
        return {"mu": float("nan"), "se": float("nan"), "ci_low": float("nan"),
                "ci_high": float("nan"), "converged": False, "k_sig": 0}
    mu_hat = _safe_brentq(lambda mu: float(np.mean(_cond_pp(ys, ses, mu)) - 0.5),
                          mu_lo, mu_hi)
    z = norm.ppf(1.0 - alpha / 2.0)
    band = z * np.sqrt(k / 12.0)
    S = lambda mu: float(np.sum(_cond_pp(ys, ses, mu)))
    lo = _safe_brentq(lambda mu: S(mu) - (k / 2.0 + band), mu_lo, mu_hi)
    hi = _safe_brentq(lambda mu: S(mu) - (k / 2.0 - band), mu_lo, mu_hi)
    ci_low, ci_high = sorted([lo, hi])
    return {"mu": mu_hat, "se": float((ci_high - ci_low) / (2 * z))
            if np.isfinite(ci_low) and np.isfinite(ci_high) else float("nan"),
            "ci_low": ci_low, "ci_high": ci_high,
            "converged": bool(np.isfinite(mu_hat)), "k_sig": int(k)}


# ---------------------------------------------------------------------------
# Vevea & Hedges (1995) weight-function selection model (2-step)
# ---------------------------------------------------------------------------

def vevea_hedges_step(y: np.ndarray, se: np.ndarray, alpha: float = 0.05
                      ) -> dict[str, Any]:
    """Vevea-Hedges (1995) selection model, one cutpoint at one-sided p = .025.

    Weight function w(p) = 1 for p <= .025 (significant-positive) and w (free,
    >0) otherwise. Marginal y_i ~ N(mu, v_i), v_i = tau^2 + se_i^2. The selected-
    data log-likelihood contribution of study i is
        log w_i + log phi(y_i; mu, v_i) - log A_i,
    A_i = Phi((mu - c*se_i)/sqrt(v_i)) + w*(1 - Phi((mu - c*se_i)/sqrt(v_i))).
    We MLE (mu, log tau^2, log w) and take mu's CI from the profile likelihood.
    """
    k = len(y)
    if k < 4:
        return {"mu": float("nan"), "se": float("nan"), "ci_low": float("nan"),
                "ci_high": float("nan"), "converged": False, "weight": float("nan")}
    s2 = np.square(se)
    sig = _sig_mask(y, se)

    def negll(params: np.ndarray) -> float:
        with np.errstate(over="ignore", invalid="ignore"):
            mu, log_t2, log_w = params
            v = s2 + np.exp(np.clip(log_t2, -30, 20))
            sd = np.sqrt(v)
            w = np.exp(np.clip(log_w, -30, 20))
            thr = (mu - C * se) / sd                      # P(sig) = Phi(thr)
            p_sig = np.clip(norm.cdf(thr), 1e-12, 1.0)
            A = np.maximum(p_sig + w * (1.0 - p_sig), 1e-300)
            logf = norm.logpdf(y, loc=mu, scale=sd)
            logw = np.where(sig, 0.0, np.clip(log_w, -30, 20))
            val = -np.sum(logw + logf - np.log(A))
        return float(val) if np.isfinite(val) else 1e18

    from .model import dersimonian_laird
    base = dersimonian_laird(y, se)
    x0 = np.array([base["mu"], np.log(max(base["tau"] ** 2, 1e-4)), np.log(0.5)])
    res = minimize(negll, x0, method="Nelder-Mead",
                   options={"xatol": 1e-7, "fatol": 1e-9, "maxiter": 6000})
    if not res.success or not np.isfinite(res.fun):
        return {"mu": float("nan"), "se": float("nan"), "ci_low": float("nan"),
                "ci_high": float("nan"), "converged": False, "weight": float("nan")}
    mu_hat = float(res.x[0])
    # Primary CI: Wald via inverse observed information (robust); profile fallback.
    se_mu, lo, hi = _wald_ci_mu(negll, res.x, alpha)
    if not (np.isfinite(lo) and np.isfinite(hi)):
        nll_min = float(res.fun)
        crit = 0.5 * norm.ppf(1.0 - alpha / 2.0) ** 2

        def prof(mu: float) -> float:
            r = minimize(lambda p: negll(np.array([mu, p[0], p[1]])),
                         res.x[1:], method="Nelder-Mead",
                         options={"xatol": 1e-6, "fatol": 1e-8, "maxiter": 3000})
            return float(r.fun) - nll_min - crit
        span = max(1.0, 10.0 * abs(mu_hat) + 1.0)
        lo = _safe_brentq(prof, mu_hat - span, mu_hat)
        hi = _safe_brentq(prof, mu_hat, mu_hat + span)
    z = norm.ppf(1.0 - alpha / 2.0)
    return {"mu": mu_hat,
            "se": se_mu if np.isfinite(se_mu)
            else (float((hi - lo) / (2 * z)) if np.isfinite(lo) and np.isfinite(hi)
                  else float("nan")),
            "ci_low": lo, "ci_high": hi,
            "converged": bool(np.isfinite(mu_hat) and np.isfinite(lo) and np.isfinite(hi)),
            "tau2": float(np.exp(res.x[1])), "weight": float(np.exp(res.x[2]))}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _num_hessian(f, x: np.ndarray, eps: float = 1e-4) -> np.ndarray:
    """Central-difference Hessian of scalar f at x."""
    n = len(x)
    H = np.zeros((n, n))
    fx = f(x)
    for i in range(n):
        for j in range(i, n):
            ei = np.zeros(n); ei[i] = eps
            ej = np.zeros(n); ej[j] = eps
            fpp = f(x + ei + ej); fpm = f(x + ei - ej)
            fmp = f(x - ei + ej); fmm = f(x - ei - ej)
            H[i, j] = H[j, i] = (fpp - fpm - fmp + fmm) / (4 * eps * eps)
    return H


def _wald_ci_mu(negll, x_opt: np.ndarray, alpha: float) -> tuple[float, float, float]:
    """Wald CI for the FIRST parameter (mu) via the inverse observed-information.

    Returns (se_mu, ci_low, ci_high); se_mu is nan if the Hessian is not usable.
    """
    try:
        H = _num_hessian(negll, x_opt)
        cov = np.linalg.inv(H)
        var_mu = float(cov[0, 0])
        if not np.isfinite(var_mu) or var_mu <= 0:
            return float("nan"), float("nan"), float("nan")
        se_mu = float(np.sqrt(var_mu))
        z = norm.ppf(1.0 - alpha / 2.0)
        mu = float(x_opt[0])
        return se_mu, mu - z * se_mu, mu + z * se_mu
    except Exception:
        return float("nan"), float("nan"), float("nan")


def _safe_brentq(f, lo: float, hi: float) -> float:
    """brentq that returns nan instead of raising when the bracket is invalid."""
    try:
        flo, fhi = f(lo), f(hi)
        if not (np.isfinite(flo) and np.isfinite(fhi)):
            return float("nan")
        if flo == 0.0:
            return float(lo)
        if fhi == 0.0:
            return float(hi)
        if flo * fhi > 0:
            return float("nan")
        return float(brentq(f, lo, hi, xtol=1e-9, rtol=1e-12, maxiter=200))
    except Exception:
        return float("nan")
