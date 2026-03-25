"""Comparator methods for the simulation study.

Implements standard meta-analysis estimators:
  - REML (restricted maximum likelihood)
  - Trim-and-fill (Duval & Tweedie 2000)
  - PET-PEESE (Stanley & Doucouliagos)
  - Copas selection model (Copas & Shi 2000)
  - Quality-effects (Doi et al. 2015)
"""
from __future__ import annotations

from typing import Any

import numpy as np
from scipy.optimize import minimize_scalar, minimize
from scipy.stats import norm, t as t_dist


def reml_estimator(y: np.ndarray, se: np.ndarray, hksj: bool = False) -> dict[str, float]:
    """Restricted maximum likelihood random-effects estimator."""
    s2 = np.square(se)

    def _reml_nll(log_tau2: float) -> float:
        tau2 = np.exp(log_tau2)
        w = 1.0 / (s2 + tau2)
        mu = np.sum(w * y) / np.sum(w)
        ll = -0.5 * (
            np.sum(np.log(s2 + tau2))
            + np.sum(w * np.square(y - mu))
            + np.log(np.sum(w))
        )
        return -ll

    result = minimize_scalar(_reml_nll, bounds=(-20, 5), method="bounded")
    tau2 = np.exp(result.x)
    tau = np.sqrt(max(tau2, 0.0))
    w = 1.0 / (s2 + tau2)
    mu = float(np.sum(w * y) / np.sum(w))
    se_mu = float(np.sqrt(1.0 / np.sum(w)))
    if hksj:
        hk = knapp_hartung_adjustment(y, se, mu, tau2)
        return {
            "mu": mu,
            "se": float(hk["se_adjusted"]),
            "tau": float(tau),
            "ci_low": hk["ci_low"],
            "ci_high": hk["ci_high"],
        }
    z = norm.ppf(0.975)
    return {
        "mu": mu,
        "se": se_mu,
        "tau": float(tau),
        "ci_low": mu - z * se_mu,
        "ci_high": mu + z * se_mu,
    }


def trim_and_fill(
    y: np.ndarray, se: np.ndarray, side: str = "right", max_iter: int = 20
) -> dict[str, Any]:
    """Duval & Tweedie trim-and-fill estimator (R0+ rank-based)."""
    k = len(y)
    w = 1.0 / np.square(se)
    mu0 = float(np.sum(w * y) / np.sum(w))

    k0 = 0
    y_fill = y
    se_fill = se

    for _ in range(max_iter):
        deviations = y - mu0
        abs_dev = np.abs(deviations)
        ranks = np.argsort(np.argsort(abs_dev)) + 1  # proper ranks

        if side == "right":
            s_n = np.sum(ranks[deviations > 0])
        else:
            s_n = np.sum(ranks[deviations < 0])

        k0 = max(0, int(round((4 * s_n - k * (k + 1) / 2) / (2 * k - 1))))

        if k0 == 0:
            break

        if side == "right":
            idx_extreme = np.argsort(y)[-k0:]
        else:
            idx_extreme = np.argsort(y)[:k0]

        y_fill = np.concatenate([y, 2 * mu0 - y[idx_extreme]])
        se_fill = np.concatenate([se, se[idx_extreme]])
        w_fill = 1.0 / np.square(se_fill)
        mu0_new = float(np.sum(w_fill * y_fill) / np.sum(w_fill))
        if abs(mu0_new - mu0) < 1e-6:
            mu0 = mu0_new
            break
        mu0 = mu0_new

    se_adj = float(np.sqrt(1.0 / np.sum(1.0 / np.square(se_fill))))
    z = norm.ppf(0.975)
    return {
        "mu": mu0,
        "se": se_adj,
        "ci_low": mu0 - z * se_adj,
        "ci_high": mu0 + z * se_adj,
        "k_imputed": k0,
        "k_total": k + k0,
    }


def pet_peese(y: np.ndarray, se: np.ndarray) -> dict[str, float]:
    """PET-PEESE bias-correction method."""
    k = len(y)
    w = 1.0 / np.square(se)

    # PET: y = b0 + b1*SE + error
    x_pet = np.column_stack([np.ones(k), se])
    xtw = x_pet.T * w
    beta_pet = np.linalg.pinv(xtw @ x_pet) @ (xtw @ y)
    cov_pet = np.linalg.pinv(xtw @ x_pet)
    intercept_se = np.sqrt(max(cov_pet[0, 0], 0.0))
    z_test = beta_pet[0] / max(intercept_se, 1e-9)
    p_val = 2 * (1 - norm.cdf(abs(z_test)))

    if p_val > 0.05:
        mu = float(beta_pet[0])
        se_mu = float(intercept_se)
    else:
        # PEESE: y = b0 + b1*SE^2 + error
        x_peese = np.column_stack([np.ones(k), np.square(se)])
        xtw2 = x_peese.T * w
        beta_peese = np.linalg.pinv(xtw2 @ x_peese) @ (xtw2 @ y)
        cov_peese = np.linalg.pinv(xtw2 @ x_peese)
        mu = float(beta_peese[0])
        se_mu = float(np.sqrt(max(cov_peese[0, 0], 0.0)))

    z = norm.ppf(0.975)
    return {
        "mu": mu,
        "se": se_mu,
        "ci_low": mu - z * se_mu,
        "ci_high": mu + z * se_mu,
        "pet_p_value": float(p_val),
        "method_used": "PET" if p_val > 0.05 else "PEESE",
    }


def copas_selection(
    y: np.ndarray,
    se: np.ndarray,
    rho_grid: np.ndarray | None = None,
) -> dict[str, Any]:
    """Copas & Shi (2000) probit selection model with inverse Mills ratio."""
    if rho_grid is None:
        rho_grid = np.linspace(0.0, 0.99, 20)

    s2 = np.square(se)
    gamma0_init = 0.0
    gamma1_init = 0.5

    results = []
    for rho in rho_grid:
        def _copas_nll(params, _rho=rho):
            mu, log_tau2, g0, g1 = params
            tau2 = np.exp(log_tau2)
            sigma2 = s2 + tau2
            sigma = np.sqrt(sigma2)

            u = g0 + g1 / se
            phi_u = norm.pdf(u)
            Phi_u = np.maximum(norm.cdf(u), 1e-9)
            inv_mills = phi_u / Phi_u

            adj_mean = mu + _rho * sigma * inv_mills
            adj_var = sigma2 * (1.0 - _rho ** 2 * u * inv_mills - _rho ** 2 * inv_mills ** 2)
            adj_var = np.maximum(adj_var, 1e-9)

            ll = -0.5 * np.sum(np.log(adj_var) + np.square(y - adj_mean) / adj_var)
            ll += np.sum(np.log(Phi_u))
            return -ll

        try:
            w = 1.0 / s2
            mu_init = float(np.sum(w * y) / np.sum(w))
            res = minimize(
                _copas_nll,
                [mu_init, -2.0, gamma0_init, gamma1_init],
                method="L-BFGS-B",
                options={"maxiter": 100},
            )
            mu_adj = float(res.x[0])
            tau_adj = float(np.sqrt(max(np.exp(res.x[1]), 0.0)))
        except Exception:
            mu_adj = float("nan")
            tau_adj = float("nan")

        w_adj = 1.0 / (s2 + max(tau_adj ** 2, 0.0)) if np.isfinite(tau_adj) else 1.0 / s2
        se_adj = float(np.sqrt(1.0 / np.sum(w_adj)))

        results.append({
            "rho": float(rho),
            "mu": mu_adj,
            "se": se_adj,
            "tau": tau_adj,
        })

    valid = [r for r in results if np.isfinite(r["mu"])]
    mus = [r["mu"] for r in valid] if valid else [float("nan")]
    z = norm.ppf(0.975)
    best = valid[0] if valid else {"mu": float("nan"), "se": float("nan")}
    return {
        "mu": best["mu"],
        "se": best["se"],
        "ci_low": best["mu"] - z * best["se"],
        "ci_high": best["mu"] + z * best["se"],
        "sensitivity_range": (min(mus), max(mus)),
        "rho_grid_results": results,
    }


def quality_effects(
    y: np.ndarray,
    se: np.ndarray,
    quality_scores: np.ndarray | None = None,
) -> dict[str, float]:
    """Quality-effects model (Doi et al. 2015, IVhet-based)."""
    s2 = np.square(se)
    w_iv = 1.0 / s2

    if quality_scores is not None and len(quality_scores) == len(y):
        q = np.asarray(quality_scores, dtype=float)
        q_weights = np.maximum(1.0 - q, 0.01)
        w = w_iv * q_weights
    else:
        w = w_iv.copy()

    mu = float(np.sum(w * y) / np.sum(w))
    se_mu = float(np.sqrt(1.0 / np.sum(w)))
    z = norm.ppf(0.975)
    return {
        "mu": mu,
        "se": se_mu,
        "ci_low": mu - z * se_mu,
        "ci_high": mu + z * se_mu,
    }


def knapp_hartung_adjustment(
    y: np.ndarray, se: np.ndarray, mu: float, tau2: float,
    alpha: float = 0.05,
) -> dict[str, float]:
    """HKSJ-adjusted SE and CI using t-distribution.

    Implements IntHout et al. (2014) / Rover et al. (2015) with floor at 1.0.
    """
    k = len(y)
    s2 = np.square(se)
    w = 1.0 / (s2 + tau2)
    se_mu = float(np.sqrt(1.0 / np.sum(w)))

    q_hksj = float(np.sum(w * np.square(y - mu)) / (k - 1))
    q_hksj = max(q_hksj, 1.0)  # floor per Rover et al. 2015
    se_adj = se_mu * np.sqrt(q_hksj)

    df = k - 1
    t_crit = float(t_dist.ppf(1.0 - alpha / 2.0, df=df))
    return {
        "mu": mu,
        "se_adjusted": float(se_adj),
        "ci_low": mu - t_crit * se_adj,
        "ci_high": mu + t_crit * se_adj,
        "q_hksj": q_hksj,
        "df": df,
    }
