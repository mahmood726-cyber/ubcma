"""Pilot-2 borrowing field: relevance gravity on a CONTINUOUS effect-modifier
covariate x (here: GLP1 dose). This is the regime pilot-1 lacked -- a covariate
that genuinely predicts effect heterogeneity, so the relevance kernel has real
structure to grip.

Identical machinery to pilot-1's borrowing_field.py EXCEPT the relevance kernel
is a Gaussian on covariate distance |x_s - x_t| (the gravity), instead of
mechanism-class + baseline. We deliberately REUSE pilot-1's hardened stand-down
(stand_down_delta) and the validated AdaptShrink fusion, so the only thing that
changes between pilots is whether the covariate carries a learnable signal.

Three priors are supported, the negative-control battery:
  * relevance : w_s = K(|x_s - x_t| / bw) * (1/se_s^2)         [the thesis]
  * uniform   : w_s = (1/se_s^2)            (shrink-to-field-mean null)
  * scrambled : relevance kernel but covariates permuted across sources
"""
from __future__ import annotations
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ubcma.adaptshrink import adaptshrink_estimator  # noqa: E402
from ubcma.comparators import reml_estimator  # noqa: E402
from borrowing_field import stand_down_delta, HARDEN, Q_MAX  # share exact hardened logic

Z975 = 1.959963984540054


def covariate_prior(x_t, xs, ys, ses, bw, mode="relevance", rng=None):
    """Form (mu_p, se_p, ess) from field sources weighted by covariate relevance.

    mode: 'relevance' (Gaussian kernel on |x_s - x_t| x precision),
          'uniform'   (precision only -> field-mean shrinkage null),
          'scrambled' (relevance kernel but covariates permuted -> gravity broken).
    """
    xs = np.asarray(xs, float); ys = np.asarray(ys, float); ses = np.asarray(ses, float)
    if len(xs) == 0:
        return float("nan"), float("inf"), 0.0
    prec = 1.0 / np.maximum(ses ** 2, 1e-9)
    if mode == "uniform":
        w = prec
    else:
        xeff = xs.copy()
        if mode == "scrambled":
            r = rng if rng is not None else np.random.default_rng(0)
            xeff = r.permutation(xeff)
        k = np.exp(-0.5 * ((xeff - x_t) / bw) ** 2)
        w = k * prec
    wsum = float(w.sum())
    if wsum <= 0:
        return float("nan"), float("inf"), 0.0
    mu_p = float((w * ys).sum() / wsum)
    within = float((w ** 2 * ses ** 2).sum() / wsum ** 2)
    between = float((w * (ys - mu_p) ** 2).sum() / wsum)
    se_p = float(np.sqrt(max(within + between, 1e-9)))
    ess = float(wsum ** 2 / (w ** 2).sum())
    return mu_p, se_p, ess


def own_estimate(own_y, own_se):
    own_y = np.asarray(own_y, float); own_se = np.asarray(own_se, float)
    if len(own_y) == 1:
        return float(own_y[0]), float(own_se[0])
    r = reml_estimator(own_y, own_se)
    return float(r["mu"]), float(r["se"])


def borrow_estimate2(own_y, own_se, x_t, xs, ys, ses, bw,
                     mode="relevance", alpha=0.05, rng=None,
                     harden=HARDEN, q_max=Q_MAX, fusion="precision"):
    """Borrowing-field estimate using the covariate-relevance prior + hardened
    stand-down. Returns dict with mu, ci, delta, Q.

    fusion:
      'precision' (pilot-2 default) -- conflict-discounted PRECISION fusion
          (power-prior / commensurate-prior style): the prior contributes
          effective precision delta/se_p^2. A precise own-estimate (small se0)
          AUTOMATICALLY dominates a wrong prior, so a confident-but-wrong prior
          cannot harm -- no disagreement-penalty floor.
      'adaptshrink' (pilot-1) -- the 2-member AdaptShrink panel fusion. Kept for
          comparison; its median-disagreement weight has a floor that leaves a
          wrong prior ~16% weight even when own data is precise (the pilot-1
          rich-regime harm). Diagnostic only.
    """
    mu0, se0 = own_estimate(own_y, own_se)
    mu_p, se_p, ess = covariate_prior(x_t, xs, ys, ses, bw, mode=mode, rng=rng)
    delta, Q = stand_down_delta(mu0, se0, mu_p, se_p, harden=harden, q_max=q_max)
    if not np.isfinite(mu_p) or delta <= 1e-6:
        return {"mu": mu0, "se": se0, "ci_low": mu0 - Z975 * se0,
                "ci_high": mu0 + Z975 * se0, "delta": delta, "Q": Q,
                "mu_prior": mu_p, "borrowed": False}

    if fusion == "precision":
        p_own = 1.0 / max(se0 ** 2, 1e-12)
        p_pri = delta / max(se_p ** 2, 1e-12)        # power-prior effective precision
        mu = (p_own * mu0 + p_pri * mu_p) / (p_own + p_pri)
        se = float(np.sqrt(1.0 / (p_own + p_pri)))
        return {"mu": float(mu), "se": se, "ci_low": mu - Z975 * se,
                "ci_high": mu + Z975 * se, "delta": delta, "Q": Q,
                "mu_prior": mu_p, "se_prior": se_p, "borrowed": True}

    se_p_eff = se_p / np.sqrt(delta)
    res = adaptshrink_estimator(
        np.asarray(own_y, float), np.asarray(own_se, float),
        members=("own", "prior"),
        precomputed={"own": (mu0, se0), "prior": (mu_p, se_p_eff)},
        kappa=1.0, alpha=alpha, use_t=False,
    )
    res = dict(res)
    res.update({"delta": delta, "Q": Q, "mu_prior": mu_p, "se_prior": se_p,
                "borrowed": True})
    return res
