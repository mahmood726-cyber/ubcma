"""Inference utilities for UBCMA: profile likelihood and bootstrap CIs for mu_target."""
from __future__ import annotations

import warnings
from typing import Any

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, logsumexp
from scipy.stats import chi2

from .data import MetaAnalysisDataset
from .model import UBCMAFit, UBCMAResult

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _safe_exp(x: np.ndarray | float) -> np.ndarray | float:
    return np.exp(np.clip(x, -20.0, 20.0))


def _log_normal_pdf(x, mean, sd) -> np.ndarray:
    sd = np.maximum(sd, 1e-9)
    z = (x - mean) / sd
    return -0.5 * np.log(2.0 * np.pi) - np.log(sd) - 0.5 * z * z


def _reconstruct_raw_params(result: UBCMAResult, data: MetaAnalysisDataset) -> np.ndarray:
    """Reconstruct the raw (unconstrained) parameter vector from a UBCMAResult.

    Parameter layout (must match model.py _build_start / unpack):
      [mu, beta..., delta..., lambda_bias...,
       gamma_common(4), gamma_quality...,
       log_tau1, log(tau2-tau1), logit(mix_weight)]
    """
    p = result.params
    mu = float(p["mu"])
    beta = np.asarray(p["beta"], dtype=float)
    delta = np.asarray(p["delta"], dtype=float)
    lambda_bias = np.asarray(p["lambda_bias"], dtype=float)
    gamma_common = np.asarray(p["gamma_common"], dtype=float)
    gamma_quality = np.asarray(p["gamma_quality"], dtype=float)
    tau1 = float(p["tau1"])
    tau2 = float(p["tau2"])
    mix_weight = float(p["mix_weight"])

    log_tau1 = np.log(np.maximum(tau1, 1e-9))
    tau2_inc = tau2 - tau1
    log_tau2_inc = np.log(np.maximum(tau2_inc, 1e-9))
    # logit(mix_weight)
    w = np.clip(mix_weight, 1e-9, 1.0 - 1e-9)
    logit_mix = np.log(w / (1.0 - w))

    vec = np.concatenate([
        [mu],
        beta,
        delta,
        lambda_bias,
        gamma_common,
        gamma_quality,
        [log_tau1, log_tau2_inc, logit_mix],
    ])
    return vec


def _build_objective_fn(fitter: UBCMAFit, data: MetaAnalysisDataset):
    """Reconstruct the objective closure from the fitter and data (identical to model.py)."""
    y = data.y.astype(float)
    se = data.se.astype(float)
    moderators = data.moderators.astype(float)
    design = data.design.astype(float)
    quality = data.quality.astype(float)
    quality_score = data.quality_score.astype(float)

    if quality.shape[1]:
        selection_quality = quality
    elif np.any(quality_score):
        selection_quality = quality_score.reshape(-1, 1)
    else:
        selection_quality = np.zeros((data.n_studies, 0), dtype=float)

    precision = 1.0 / se
    precision_z = (precision - precision.mean()) / max(precision.std(ddof=0), 1e-9)

    n_moderators = moderators.shape[1]
    n_design = design.shape[1]
    n_quality = quality.shape[1]
    n_selection_quality = selection_quality.shape[1]

    def unpack(params: np.ndarray) -> dict[str, Any]:
        idx = 0
        mu = params[idx]; idx += 1
        beta = params[idx: idx + n_moderators]; idx += n_moderators
        delta = params[idx: idx + n_design]; idx += n_design
        lambda_bias = params[idx: idx + n_quality]; idx += n_quality
        gamma_common = params[idx: idx + 4]; idx += 4
        gamma_quality = params[idx: idx + n_selection_quality]; idx += n_selection_quality
        tau1 = _safe_exp(params[idx]); idx += 1
        tau2 = tau1 + _safe_exp(params[idx]); idx += 1
        mix_weight = expit(params[idx])

        base_loc = (
            mu
            + (moderators @ beta if n_moderators else 0.0)
            + (design @ delta if n_design else 0.0)
        )
        bias_shift = quality @ lambda_bias if n_quality else np.zeros_like(y)
        loc = base_loc + bias_shift
        return {
            "mu": float(mu),
            "beta": beta,
            "delta": delta,
            "lambda_bias": lambda_bias,
            "gamma_common": gamma_common,
            "gamma_quality": gamma_quality,
            "tau1": float(tau1),
            "tau2": float(tau2),
            "mix_weight": float(mix_weight),
            "location": np.asarray(loc, dtype=float),
            "bias_shift": np.asarray(bias_shift, dtype=float),
        }

    def log_prior(params: np.ndarray, parsed: dict[str, Any]) -> float:
        mu_pen = -0.5 * (parsed["mu"] / 2.5) ** 2
        beta_pen = -0.5 * np.sum(np.square(parsed["beta"] / 1.5))
        delta_pen = -0.5 * np.sum(np.square(parsed["delta"] / 1.5))
        bias_pen = -0.5 * np.sum(np.square(parsed["lambda_bias"] / 0.75))
        gamma_common_pen = -0.5 * np.sum(np.square(parsed["gamma_common"] / 1.0))
        gamma_quality_pen = -0.5 * np.sum(np.square(parsed["gamma_quality"] / 0.75))
        tau_pen = -0.5 * ((parsed["tau1"] / 0.5) ** 2 + (parsed["tau2"] / 1.0) ** 2)
        mix_pen = -0.5 * ((parsed["mix_weight"] - 0.8) / 0.2) ** 2
        return float(
            mu_pen + beta_pen + delta_pen + bias_pen
            + gamma_common_pen + gamma_quality_pen + tau_pen + mix_pen
        )

    def objective(params: np.ndarray) -> float:
        parsed = unpack(params)
        tau1 = parsed["tau1"]
        tau2 = parsed["tau2"]
        w_main = parsed["mix_weight"]
        loc = parsed["location"]
        gamma_common = parsed["gamma_common"]
        gamma_quality = parsed["gamma_quality"]
        sd1 = np.sqrt(np.square(se) + tau1 ** 2)
        sd2 = np.sqrt(np.square(se) + tau2 ** 2)
        log_comp = np.vstack([
            np.log(w_main + 1e-12) + _log_normal_pdf(y, loc, sd1),
            np.log(1.0 - w_main + 1e-12) + _log_normal_pdf(y, loc, sd2),
        ])
        log_density = logsumexp(log_comp, axis=0)
        p_select_obs = fitter._selection_probability(
            y, se, precision_z, selection_quality, gamma_common, gamma_quality,
        )
        normalizer = (
            w_main * fitter._expected_selection_probability(
                loc, sd1, se, precision_z, selection_quality, gamma_common, gamma_quality,
            )
            + (1.0 - w_main) * fitter._expected_selection_probability(
                loc, sd2, se, precision_z, selection_quality, gamma_common, gamma_quality,
            )
        )
        normalizer = np.maximum(normalizer, 1e-9)
        total = np.sum(log_density + np.log(p_select_obs) - np.log(normalizer))
        return float(-(total + log_prior(params, parsed)))

    return objective, unpack


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def profile_likelihood_ci(
    result: UBCMAResult,
    data: MetaAnalysisDataset,
    fitter: UBCMAFit,
    alpha: float = 0.05,
    n_points: int = 40,
    resolution: float = 1e-4,
) -> dict[str, Any]:
    """Profile likelihood CI for mu_target.

    Walks the penalised log-likelihood along mu while re-optimising all
    nuisance parameters at each step.  Bisection is used to find the two
    mu values where the profile objective rises by chi2(1, alpha)/2 above
    the MLE.

    Parameters
    ----------
    result : UBCMAResult
        A fitted UBCMA result.
    data : MetaAnalysisDataset
        The dataset used for fitting.
    fitter : UBCMAFit
        The fitter instance (provides objective and selection helpers).
    alpha : float
        Significance level for the CI (default 0.05 => 95% CI).
    n_points : int
        Number of evenly-spaced mu values to store in profile_curve.
    resolution : float
        Bisection convergence tolerance for mu.

    Returns
    -------
    dict with keys:
        ci_low, ci_high, alpha, mle_mu, mle_objective, threshold, profile_curve
    """
    objective, unpack = _build_objective_fn(fitter, data)
    mle_params = _reconstruct_raw_params(result, data)
    mle_mu = float(result.params["mu"])
    mle_obj = float(objective(mle_params))

    # Threshold: profile obj must exceed mle_obj + half_chi2
    half_chi2 = 0.5 * float(chi2.ppf(1.0 - alpha, df=1))
    threshold = mle_obj + half_chi2

    # Nuisance parameter indices: everything except index 0 (mu)
    _last_nuisance = mle_params[1:].copy()
    n_nuisance = len(_last_nuisance)

    def profile_at(mu_val: float) -> float:
        """Profile objective: minimize over nuisance with mu fixed.
        Warm-starts from previous solution for speed."""
        nonlocal _last_nuisance

        def nuisance_obj(nuisance: np.ndarray) -> float:
            params = np.empty(1 + n_nuisance)
            params[0] = mu_val
            params[1:] = nuisance
            return objective(params)

        res = minimize(
            nuisance_obj,
            _last_nuisance,
            method="L-BFGS-B",
            options={"maxiter": 20, "ftol": 1e-3},
        )
        _last_nuisance = res.x.copy()
        return float(res.fun)

    # Approximate SE from DerSimonian-Laird baseline for initial bracket
    dl_se = float(result.baseline.get("wls_reference_se", 0.2))
    if not np.isfinite(dl_se) or dl_se <= 0:
        dl_se = 0.2

    def find_boundary(direction: float) -> float:
        """Find the mu where profile crosses threshold in the given direction (+1 or -1)."""
        nonlocal _last_nuisance
        _last_nuisance = mle_params[1:].copy()  # reset warm-start for each direction
        bracket_half = 5.0 * dl_se
        # a = below threshold (near MLE), b = above threshold (far from MLE)
        a_mu = mle_mu
        a_val = mle_obj  # profile at MLE = mle_obj by definition

        b_mu = mle_mu + direction * bracket_half
        b_val = profile_at(b_mu)

        # Double bracket until threshold is crossed (max 5 doublings)
        for _ in range(5):
            if b_val >= threshold:
                break
            bracket_half *= 2.0
            b_mu = mle_mu + direction * bracket_half
            b_val = profile_at(b_mu)

        if b_val < threshold:
            warnings.warn(
                f"Profile likelihood: threshold not crossed in direction {direction:+.0f}. "
                "Returning inf. Consider increasing bracket or checking convergence.",
                RuntimeWarning,
                stacklevel=3,
            )
            return float("inf") if direction > 0 else float("-inf")

        # Bisection: lo_val < threshold <= hi_val
        # lo = below threshold (near MLE), hi = above threshold (away from MLE)
        lo_mu, lo_val = a_mu, a_val  # near MLE, below threshold
        hi_mu, hi_val = b_mu, b_val  # far from MLE, above threshold

        for _ in range(20):
            if abs(hi_mu - lo_mu) < resolution:
                break
            mid = 0.5 * (lo_mu + hi_mu)
            mid_val = profile_at(mid)
            if mid_val < threshold:
                lo_mu, lo_val = mid, mid_val
            else:
                hi_mu, hi_val = mid, mid_val

        # Return the crossing point (closer to the above-threshold side)
        return float(0.5 * (lo_mu + hi_mu))

    # --- Find CI bounds ---
    ci_high = find_boundary(direction=+1.0)
    ci_low = find_boundary(direction=-1.0)

    # --- Profile curve (optional, for visualization) ---
    profile_curve = []
    if n_points > 0:
        curve_mus = np.linspace(mle_mu - 5.0 * dl_se, mle_mu + 5.0 * dl_se, n_points)
        for mu_val in curve_mus:
            obj_val = profile_at(float(mu_val))
            profile_curve.append({"mu": float(mu_val), "objective": float(obj_val)})

    # Sanity: ensure ci_low <= mle_mu <= ci_high
    if np.isfinite(ci_low) and np.isfinite(ci_high) and ci_low > ci_high:
        ci_low, ci_high = ci_high, ci_low

    return {
        "ci_low": ci_low,
        "ci_high": ci_high,
        "alpha": float(alpha),
        "mle_mu": mle_mu,
        "mle_objective": mle_obj,
        "threshold": float(threshold),
        "profile_curve": profile_curve,
    }


def bootstrap_ci(
    data: MetaAnalysisDataset,
    fitter: UBCMAFit,
    n_boot: int = 2000,
    alpha: float = 0.05,
    method: str = "percentile",
    seed: int = 42,
) -> dict[str, Any]:
    """Nonparametric bootstrap CI for mu_target.

    Resamples studies with replacement, refits with n_restarts=0 for speed.

    Parameters
    ----------
    data : MetaAnalysisDataset
        The original dataset.
    fitter : UBCMAFit
        The fitter instance (settings are reused, but n_restarts overridden to 0).
    n_boot : int
        Number of bootstrap replicates.
    alpha : float
        Significance level.
    method : str
        "percentile" or "bca".
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    dict with keys:
        ci_low, ci_high, alpha, method, n_boot, n_failed, n_succeeded, distribution
    """
    rng = np.random.default_rng(seed)
    n_studies = data.n_studies

    # Fast fitter: no restarts
    fast_fitter = UBCMAFit(
        quadrature_points=fitter.quadrature_points,
        significance_softness=fitter.significance_softness,
        direction_softness=fitter.direction_softness,
        maxiter=fitter.maxiter,
        n_restarts=0,
        restart_seed=fitter.restart_seed,
    )

    boot_mus: list[float] = []
    n_failed = 0

    for _ in range(n_boot):
        idx = rng.integers(0, n_studies, size=n_studies)
        # Resample all arrays
        boot_data = MetaAnalysisDataset(
            y=data.y[idx],
            se=data.se[idx],
            quality=data.quality[idx] if data.quality.shape[1] else data.quality,
            quality_score=data.quality_score[idx],
            moderators=data.moderators[idx] if data.moderators.shape[1] else data.moderators,
            moderator_reference_values=data.moderator_reference_values,
            design=data.design[idx] if data.design.shape[1] else data.design,
            study_ids=[data.study_ids[i] for i in idx],
            quality_names=data.quality_names,
            moderator_names=data.moderator_names,
            design_names=data.design_names,
            raw=data.raw.iloc[idx].reset_index(drop=True),
        )
        try:
            boot_result = fast_fitter.fit(boot_data, allow_failed=True)
            boot_mus.append(float(boot_result.params["mu"]))
        except Exception:
            n_failed += 1

    n_succeeded = len(boot_mus)
    n_total = n_succeeded + n_failed

    # Require 80% successful refits
    if n_succeeded < 0.8 * n_boot:
        warnings.warn(
            f"Bootstrap: only {n_succeeded}/{n_boot} ({100 * n_succeeded / n_boot:.0f}%) "
            "replicates succeeded. CIs may be unreliable. Returning NaN CIs.",
            RuntimeWarning,
            stacklevel=2,
        )
        return {
            "ci_low": float("nan"),
            "ci_high": float("nan"),
            "alpha": float(alpha),
            "method": method,
            "n_boot": n_boot,
            "n_failed": n_failed,
            "n_succeeded": n_succeeded,
            "distribution": np.asarray(boot_mus),
        }

    dist = np.asarray(boot_mus)

    if method == "percentile":
        ci_low = float(np.percentile(dist, 100.0 * alpha / 2.0))
        ci_high = float(np.percentile(dist, 100.0 * (1.0 - alpha / 2.0)))

    elif method == "bca":
        ci_low, ci_high = _bca_ci(dist, data, fast_fitter, alpha)

    else:
        raise ValueError(f"Unknown bootstrap method: {method!r}. Use 'percentile' or 'bca'.")

    return {
        "ci_low": ci_low,
        "ci_high": ci_high,
        "alpha": float(alpha),
        "method": method,
        "n_boot": n_boot,
        "n_failed": n_failed,
        "n_succeeded": n_succeeded,
        "distribution": dist,
    }


def _bca_ci(
    dist: np.ndarray,
    data: MetaAnalysisDataset,
    fitter: UBCMAFit,
    alpha: float,
) -> tuple[float, float]:
    """BCa (bias-corrected accelerated) bootstrap CI.

    Bias-correction z0: proportion of bootstrap estimates below MLE.
    Acceleration a_hat: from jackknife.
    """
    from scipy.stats import norm as _norm

    # Fit on original data to get MLE
    try:
        mle_result = fitter.fit(data, allow_failed=True)
        mle_mu = float(mle_result.params["mu"])
    except Exception:
        warnings.warn("BCa: original data fit failed; falling back to percentile.", RuntimeWarning, stacklevel=3)
        ci_low = float(np.percentile(dist, 100.0 * alpha / 2.0))
        ci_high = float(np.percentile(dist, 100.0 * (1.0 - alpha / 2.0)))
        return ci_low, ci_high

    # Bias-correction: proportion of boot estimates below MLE
    prop_below = float(np.mean(dist < mle_mu))
    prop_below = np.clip(prop_below, 1e-9, 1.0 - 1e-9)
    z0 = float(_norm.ppf(prop_below))

    # Acceleration: jackknife
    n = data.n_studies
    jack_mus = []
    for i in range(n):
        idx = [j for j in range(n) if j != i]
        jack_data = MetaAnalysisDataset(
            y=data.y[idx],
            se=data.se[idx],
            quality=data.quality[idx] if data.quality.shape[1] else data.quality,
            quality_score=data.quality_score[idx],
            moderators=data.moderators[idx] if data.moderators.shape[1] else data.moderators,
            moderator_reference_values=data.moderator_reference_values,
            design=data.design[idx] if data.design.shape[1] else data.design,
            study_ids=[data.study_ids[j] for j in idx],
            quality_names=data.quality_names,
            moderator_names=data.moderator_names,
            design_names=data.design_names,
            raw=data.raw.iloc[idx].reset_index(drop=True),
        )
        try:
            jr = fitter.fit(jack_data, allow_failed=True)
            jack_mus.append(float(jr.params["mu"]))
        except Exception:
            jack_mus.append(mle_mu)  # fallback: use MLE

    jack_mus = np.asarray(jack_mus)
    jack_mean = jack_mus.mean()
    diff = jack_mean - jack_mus
    denom = 6.0 * (np.sum(diff ** 2) ** 1.5)
    a_hat = float(np.sum(diff ** 3) / denom) if abs(denom) > 1e-15 else 0.0

    # Adjusted quantiles
    z_alpha_lo = float(_norm.ppf(alpha / 2.0))
    z_alpha_hi = float(_norm.ppf(1.0 - alpha / 2.0))

    def _adjusted_q(z_alpha: float) -> float:
        num = z0 + z_alpha
        adj = z0 + num / (1.0 - a_hat * num)
        return float(_norm.cdf(adj))

    q_lo = _adjusted_q(z_alpha_lo)
    q_hi = _adjusted_q(z_alpha_hi)
    q_lo = np.clip(q_lo, 0.001, 0.999)
    q_hi = np.clip(q_hi, 0.001, 0.999)

    ci_low = float(np.percentile(dist, 100.0 * q_lo))
    ci_high = float(np.percentile(dist, 100.0 * q_hi))
    return ci_low, ci_high
