"""Independent publication-bias-adjusted meta-analysis comparators.

The functions in this file are intentionally self-contained and use only
NumPy/SciPy.  Effects are assumed to be approximately normal with known
standard errors, and "significant positive" means z = y / se > 1.959964.
"""

from __future__ import annotations

import math
from typing import Callable, Optional, Tuple

import numpy as np
from scipy import optimize, stats
from scipy.special import log_ndtr


Z_CUT = 1.959963984540054
Z_975 = 1.959963984540054
MIN_K = 4
EPS = np.finfo(float).eps


def _failure(mu: float = np.nan) -> dict:
    return {
        "mu": float(mu) if np.isfinite(mu) else np.nan,
        "ci_low": np.nan,
        "ci_high": np.nan,
        "converged": False,
    }


def _success(mu: float, ci_low: float, ci_high: float) -> dict:
    ok = np.all(np.isfinite([mu, ci_low, ci_high])) and ci_low <= ci_high
    return {
        "mu": float(mu) if np.isfinite(mu) else np.nan,
        "ci_low": float(ci_low) if ok else np.nan,
        "ci_high": float(ci_high) if ok else np.nan,
        "converged": bool(ok),
    }


def _clean_inputs(y, se) -> Tuple[np.ndarray, np.ndarray]:
    y = np.asarray(y, dtype=float).reshape(-1)
    se = np.asarray(se, dtype=float).reshape(-1)
    if y.shape != se.shape:
        raise ValueError("y and se must have the same shape")
    keep = np.isfinite(y) & np.isfinite(se) & (se > 0)
    return y[keep], se[keep]


def _logdiffexp(log_big: np.ndarray, log_small: np.ndarray) -> np.ndarray:
    """log(exp(log_big) - exp(log_small)) for log_big >= log_small."""
    log_big, log_small = np.broadcast_arrays(
        np.asarray(log_big, dtype=float),
        np.asarray(log_small, dtype=float),
    )
    delta = np.minimum(log_small - log_big, 0.0)
    out = np.full(delta.shape, -np.inf, dtype=float)
    mask = delta < -1e-15
    out[mask] = log_big[mask] + np.log1p(-np.exp(delta[mask]))
    return out


def _clip_unit(x: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(x, dtype=float), 0.0, 1.0)


def _u_significant(z: np.ndarray, theta: np.ndarray) -> np.ndarray:
    """P_theta(Z <= z | Z > Z_CUT), for observed z > Z_CUT."""
    a = Z_CUT - theta
    b = z - theta
    use_sf = (a + b) > 0.0

    log_num_cdf = _logdiffexp(log_ndtr(b), log_ndtr(a))
    log_num_sf = _logdiffexp(log_ndtr(-a), log_ndtr(-b))
    log_num = np.where(use_sf, log_num_sf, log_num_cdf)
    log_den = log_ndtr(-a)
    log_u = np.minimum(log_num - log_den, 0.0)
    return _clip_unit(np.exp(np.maximum(log_u, -745.0)))


def _u_nonsignificant(z: np.ndarray, theta: np.ndarray) -> np.ndarray:
    """P_theta(Z <= z | Z <= Z_CUT), for observed z <= Z_CUT."""
    log_u = log_ndtr(z - theta) - log_ndtr(Z_CUT - theta)
    log_u = np.minimum(log_u, 0.0)
    return _clip_unit(np.exp(np.maximum(log_u, -745.0)))


def _conditional_u(y: np.ndarray, se: np.ndarray, mu: float, sig: np.ndarray) -> np.ndarray:
    z = y / se
    theta = mu / se
    u = np.empty_like(y, dtype=float)
    if np.any(sig):
        u[sig] = _u_significant(z[sig], theta[sig])
    if np.any(~sig):
        u[~sig] = _u_nonsignificant(z[~sig], theta[~sig])
    return u


def _initial_mu_range(y: np.ndarray, se: np.ndarray) -> Tuple[float, float]:
    weights = 1.0 / np.square(se)
    center = float(np.sum(weights * y) / np.sum(weights))
    spread = max(
        float(np.nanstd(y)) if y.size > 1 else 0.0,
        float(np.max(se)),
        abs(center),
        1.0,
    )
    lo = min(float(np.min(y)), center) - 8.0 * spread
    hi = max(float(np.max(y)), center) + 8.0 * spread
    return lo, hi


def _bracket_decreasing(
    f: Callable[[float], float],
    y: np.ndarray,
    se: np.ndarray,
    max_expand: int = 80,
) -> Optional[Tuple[float, float]]:
    lo, hi = _initial_mu_range(y, se)
    for _ in range(max_expand):
        flo = f(lo)
        fhi = f(hi)
        if np.isfinite(flo) and np.isfinite(fhi) and flo >= 0.0 and fhi <= 0.0:
            return lo, hi
        width = hi - lo
        lo -= width
        hi += width
    return None


def _solve_decreasing(
    f: Callable[[float], float],
    y: np.ndarray,
    se: np.ndarray,
) -> Tuple[float, bool]:
    bracket = _bracket_decreasing(f, y, se)
    if bracket is not None:
        try:
            return float(optimize.brentq(f, bracket[0], bracket[1], xtol=1e-10, rtol=1e-10)), True
        except (FloatingPointError, ValueError, RuntimeError):
            pass

    lo, hi = _initial_mu_range(y, se)
    res = optimize.minimize_scalar(lambda m: f(m) ** 2, bounds=(lo, hi), method="bounded")
    if res.success and np.isfinite(res.x):
        return float(res.x), abs(float(f(res.x))) < 1e-4
    return np.nan, False


def _irwin_hall_quantiles(n: int) -> Tuple[float, float]:
    if n <= 0:
        return np.nan, np.nan
    try:
        q_low, q_high = stats.irwinhall(n).ppf([0.025, 0.975])
        if np.all(np.isfinite([q_low, q_high])):
            return float(q_low), float(q_high)
    except AttributeError:
        pass
    mean = n / 2.0
    sd = math.sqrt(n / 12.0)
    return max(0.0, mean - Z_975 * sd), min(float(n), mean + Z_975 * sd)


def _conditional_sum_ci(
    y: np.ndarray,
    se: np.ndarray,
    sig: np.ndarray,
) -> Tuple[float, float, bool]:
    n = y.size
    q_low, q_high = _irwin_hall_quantiles(n)
    if not np.all(np.isfinite([q_low, q_high])):
        return np.nan, np.nan, False

    def sum_u(mu: float) -> float:
        return float(np.sum(_conditional_u(y, se, mu, sig)))

    # sum_u decreases with mu.  The lower confidence endpoint is where the
    # observed sum first falls below the upper null quantile.
    lo, ok_lo = _solve_decreasing(lambda m: sum_u(m) - q_high, y, se)
    hi, ok_hi = _solve_decreasing(lambda m: sum_u(m) - q_low, y, se)
    return lo, hi, bool(ok_lo and ok_hi and lo <= hi)


def p_curve(y, se) -> dict:
    """Simonsohn-Nelson-Simmons-style p-curve effect estimate.

    Only significant-positive studies are used.  For a candidate mu, each
    observed z statistic is transformed by its conditional CDF given
    z > 1.959964.  Under the true mu those transformed values are uniform, so
    the point estimate solves mean(U) = 0.5 and the CI inverts sum(U).
    """
    y, se = _clean_inputs(y, se)
    if y.size < MIN_K:
        return _failure()
    sig_all = (y / se) > Z_CUT
    y_sig = y[sig_all]
    se_sig = se[sig_all]
    if y_sig.size < MIN_K:
        return _failure()

    sig = np.ones(y_sig.size, dtype=bool)

    def estimating(mu: float) -> float:
        return float(np.mean(_conditional_u(y_sig, se_sig, mu, sig)) - 0.5)

    mu, ok = _solve_decreasing(estimating, y_sig, se_sig)
    if not ok or not np.isfinite(mu):
        return _failure(mu)
    ci_low, ci_high, ci_ok = _conditional_sum_ci(y_sig, se_sig, sig)
    if not ci_ok:
        return _failure(mu)
    return _success(mu, ci_low, ci_high)


def p_uniform_star(y, se) -> dict:
    """van Aert-van Assen p-uniform* estimate using all studies.

    Significant-positive and non-significant studies are transformed within
    their own observed selection regions.  Conditioning this way leaves a
    Uniform(0, 1) variable under the true mu for both regions, so the estimate
    solves average conditional probability = 0.5.
    """
    y, se = _clean_inputs(y, se)
    if y.size < MIN_K:
        return _failure()
    sig = (y / se) > Z_CUT
    if not np.any(sig) or np.all(sig):
        return _failure()

    def estimating(mu: float) -> float:
        return float(np.mean(_conditional_u(y, se, mu, sig)) - 0.5)

    mu, ok = _solve_decreasing(estimating, y, se)
    if not ok or not np.isfinite(mu):
        return _failure(mu)
    ci_low, ci_high, ci_ok = _conditional_sum_ci(y, se, sig)
    if not ci_ok:
        return _failure(mu)
    return _success(mu, ci_low, ci_high)


def _dl_tau(y: np.ndarray, se: np.ndarray) -> float:
    weights = 1.0 / np.square(se)
    mu_fe = float(np.sum(weights * y) / np.sum(weights))
    q = float(np.sum(weights * np.square(y - mu_fe)))
    c = float(np.sum(weights) - np.sum(np.square(weights)) / np.sum(weights))
    if c <= 0.0:
        return 0.0
    return math.sqrt(max(0.0, (q - (y.size - 1.0)) / c))


def _selection_nll(params: np.ndarray, y: np.ndarray, se: np.ndarray, sig: np.ndarray) -> float:
    mu, log_tau, log_w = params
    tau = math.exp(float(np.clip(log_tau, -50.0, 50.0)))
    log_w = float(np.clip(log_w, -50.0, 50.0))
    sd = np.sqrt(np.square(se) + tau * tau)
    z = (y - mu) / sd
    log_f = stats.norm.logpdf(z) - np.log(sd)

    cut_y = Z_CUT * se
    a = (cut_y - mu) / sd
    log_p_sig = log_ndtr(-a)
    log_p_non = log_ndtr(a)
    log_norm = np.logaddexp(log_p_sig, log_w + log_p_non)
    log_weight = np.where(sig, 0.0, log_w)

    ll = log_f + log_weight - log_norm
    if not np.all(np.isfinite(ll)):
        return np.inf
    return float(-np.sum(ll))


def _finite_difference_hessian(
    fun: Callable[[np.ndarray], float],
    x: np.ndarray,
    mu_scale: float,
) -> Optional[np.ndarray]:
    x = np.asarray(x, dtype=float)
    n = x.size
    h = np.array([1e-4 * max(mu_scale, 1.0), 1e-4, 1e-4], dtype=float)
    f0 = fun(x)
    if not np.isfinite(f0):
        return None
    hess = np.empty((n, n), dtype=float)
    for i in range(n):
        ei = np.zeros(n)
        ei[i] = h[i]
        fp = fun(x + ei)
        fm = fun(x - ei)
        if not np.isfinite(fp + fm):
            return None
        hess[i, i] = (fp - 2.0 * f0 + fm) / (h[i] * h[i])
        for j in range(i + 1, n):
            ej = np.zeros(n)
            ej[j] = h[j]
            fpp = fun(x + ei + ej)
            fpm = fun(x + ei - ej)
            fmp = fun(x - ei + ej)
            fmm = fun(x - ei - ej)
            vals = np.array([fpp, fpm, fmp, fmm])
            if not np.all(np.isfinite(vals)):
                return None
            hess[i, j] = hess[j, i] = (fpp - fpm - fmp + fmm) / (4.0 * h[i] * h[j])
    return 0.5 * (hess + hess.T)


def vevea_hedges_step(y, se) -> dict:
    """Two-step one-sided Vevea-Hedges weight-function selection model.

    The selected-study density is proportional to the random-effects normal
    density times a selection weight: 1 when z > 1.959964 and w otherwise.
    Each study likelihood is normalized by the corresponding model-implied
    selection probability, P(sig) + w P(non-sig).
    """
    y, se = _clean_inputs(y, se)
    if y.size < MIN_K:
        return _failure()
    sig = (y / se) > Z_CUT
    if not np.any(sig) or np.all(sig):
        return _failure()

    weights = 1.0 / np.square(se)
    mu_fe = float(np.sum(weights * y) / np.sum(weights))
    tau0 = _dl_tau(y, se)
    mu_scale = max(
        float(np.nanstd(y)) if y.size > 1 else 0.0,
        float(np.max(se)),
        abs(mu_fe),
        1.0,
    )
    mu_lo = min(float(np.min(y)), mu_fe) - 8.0 * mu_scale
    mu_hi = max(float(np.max(y)), mu_fe) + 8.0 * mu_scale
    tau_floor = max(1e-8, 1e-8 * mu_scale)
    tau_ceiling = max(10.0 * mu_scale, tau_floor * 10.0)
    bounds = [
        (mu_lo, mu_hi),
        (math.log(tau_floor), math.log(tau_ceiling)),
        (math.log(1e-4), math.log(100.0)),
    ]

    starts = []
    for mu0 in (mu_fe, float(np.median(y)), float(np.mean(y))):
        for tau_start in (max(tau0, tau_floor * 10.0), 0.05 * mu_scale, 0.25 * mu_scale):
            starts.append(np.array([mu0, math.log(max(tau_start, tau_floor)), math.log(0.3)]))
    starts.append(np.array([mu_fe, math.log(max(tau0, tau_floor * 10.0)), math.log(1.0)]))

    best = None
    for start in starts:
        try:
            res = optimize.minimize(
                _selection_nll,
                start,
                args=(y, se, sig),
                method="L-BFGS-B",
                bounds=bounds,
                options={"maxiter": 1000, "ftol": 1e-10, "gtol": 1e-6},
            )
        except (FloatingPointError, ValueError, RuntimeError):
            continue
        if res.success and np.isfinite(res.fun):
            if best is None or res.fun < best.fun:
                best = res

    if best is None:
        return _failure()

    xhat = np.asarray(best.x, dtype=float)
    mu_hat = float(xhat[0])
    near_boundary = any(
        abs(xhat[i] - bounds[i][0]) < 1e-5 or abs(xhat[i] - bounds[i][1]) < 1e-5
        for i in range(3)
    )
    if near_boundary:
        return _failure(mu_hat)

    fun = lambda p: _selection_nll(p, y, se, sig)
    hess = _finite_difference_hessian(fun, xhat, mu_scale)
    if hess is None:
        return _failure(mu_hat)
    try:
        eigvals = np.linalg.eigvalsh(hess)
        if not np.all(eigvals > 1e-7):
            return _failure(mu_hat)
        cov = np.linalg.inv(hess)
    except np.linalg.LinAlgError:
        return _failure(mu_hat)

    var_mu = float(cov[0, 0])
    if not np.isfinite(var_mu) or var_mu <= 0.0:
        return _failure(mu_hat)
    se_mu = math.sqrt(var_mu)
    return _success(mu_hat, mu_hat - Z_975 * se_mu, mu_hat + Z_975 * se_mu)


def _naive_fixed_mean(y: np.ndarray, se: np.ndarray) -> float:
    weights = 1.0 / np.square(se)
    return float(np.sum(weights * y) / np.sum(weights))


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    true_mu = 0.3
    true_tau = 0.1
    n_source = 70
    se = rng.uniform(0.08, 0.20, size=n_source)
    theta = rng.normal(true_mu, true_tau, size=n_source)
    y = rng.normal(theta, se)
    is_sig = (y / se) > Z_CUT
    keep_prob = np.where(is_sig, 1.0, 0.3)
    keep = rng.uniform(size=n_source) < keep_prob
    y_obs = y[keep]
    se_obs = se[keep]

    naive = _naive_fixed_mean(y_obs, se_obs)
    naive_err = abs(naive - true_mu)
    print(f"selected_k={y_obs.size} significant_k={int(np.sum((y_obs / se_obs) > Z_CUT))}")
    print(f"naive_fixed_mean={naive:.6f} abs_error={naive_err:.6f}")

    for name, func in (
        ("p_curve", p_curve),
        ("p_uniform_star", p_uniform_star),
        ("vevea_hedges_step", vevea_hedges_step),
    ):
        out = func(y_obs, se_obs)
        err = abs(out["mu"] - true_mu) if np.isfinite(out["mu"]) else np.inf
        passed = bool(out["converged"] and err < naive_err)
        print(
            f"{name}: mu={out['mu']:.6f} ci=({out['ci_low']:.6f}, "
            f"{out['ci_high']:.6f}) converged={out['converged']} "
            f"abs_error={err:.6f}"
        )
        print(f"{name} {'PASS' if passed else 'FAIL'}")
