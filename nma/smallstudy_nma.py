"""smallstudy_nma.py -- Component B: network small-study / selection correction.

The field default (common-tau^2 graph-theoretic NMA = netmeta) does NOT correct
small-study / selective-reporting effects: when small studies are preferentially
reported in one direction, every direct contrast is biased and the GLS pools the
biased directs into biased basic parameters. This module adds the network analog
of PET-PEESE, GATED on a network-funnel asymmetry test, exactly the
funnel-asymmetry gate of the univariate AdaptShrink.

The network meta-regression
---------------------------
Work in the basic-parameter (reference) parameterization. With reference
treatment r, basic parameters d_t = effect(t) - effect(r) (d_r = 0). Each
comparison row i is y_i = d_{t1} - d_{t2} + error, weighted by the verified
engine's block precision W (so multi-arm correlation and the RE tau^2 structure
stay netmeta-exact). Augment the design with a single network-wide small-study
slope on a precision covariate:

    y = B_basic d  +  beta * s  +  error,     s_i = se_i (PET) or se_i^2 (PEESE)

Solving the weighted least squares gives the bias-adjusted basic parameters d as
the fitted value at s -> 0, plus one extra slope beta shared across the whole
network (so it is estimable even when individual edges are sparse). With no
covariate this reduces EXACTLY to the engine league (verified to ~1e-15).

  * `network_asymmetry`  -- the network Egger test (PET slope z / two-sided p).
  * `network_smallstudy_league` -- augmented-WLS league (PET or PEESE).

Design notes (honest)
---------------------
  * Single global slope assumes a consistent small-study DIRECTION across the
    network (the comparison-adjusted-funnel assumption, Chaimani 2012). When that
    holds the correction de-biases; when contrasts have heterogeneous small-study
    directions a single slope is mis-specified -- documented, not hidden.
  * A point correction can only WIN matched-coverage efficiency where the
    selection bias DOMINATES sampling variance (dense / well-powered networks).
    In sparse networks the bias is dominated by per-contrast variance, so the
    gate (and the SNR shrink in adaptshrink_nma) correctly declines -- see
    nma/REPORT_NMA_BAKEOFF.md.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np
from scipy.stats import norm

from nma_core import Comparison, NMAFit, _assemble, _dl_tau2, _league

_EPS = 1e-12


def _prep(comps: Sequence[Comparison], tau2_map: dict | None = None):
    """Assemble the engine's incidence B (m x n), block precision W, y, se.

    Uses the network generalized-DL tau^2 (netmeta default) for the RE weights,
    or the comparison-specific tau2_map (component A) when supplied -- so the
    small-study correction composes with the heterogeneity-structure shrinkage.
    """
    treatments = sorted({c.t1 for c in comps} | {c.t2 for c in comps})
    tidx = {t: i for i, t in enumerate(treatments)}
    n = len(treatments)
    by_study: dict[str, set] = {}
    for c in comps:
        by_study.setdefault(c.studlab, set()).update([c.t1, c.t2])
    indep = sum(len(a) - 1 for a in by_study.values())
    df_Q = max(indep - (n - 1), 0)
    tau2, _, _ = _dl_tau2(comps, tidx, n, df_Q)
    B, W, y, _ = _assemble(comps, tidx, n, tau2=tau2, tau2_map=tau2_map)
    se = np.array([c.se for c in comps], dtype=float)
    return treatments, tidx, n, B, W, y, se, tau2


def _augmented_solve(B, W, y, se, n, reference_idx, kind):
    """Weighted least squares of y on [basic design | precision covariate].

    Returns (theta_full (n,), cov_full (n,n), beta, var_beta) where theta_full is
    in the reference parameterization (theta[reference_idx] = 0) and cov_full is
    its (singular at the reference) covariance, ready for _league.
    """
    keep = [j for j in range(n) if j != reference_idx]
    Bb = B[:, keep]                                  # m x (n-1)
    if kind is None:
        X = Bb
    else:
        s = se if kind == "pet" else se ** 2
        X = np.hstack([Bb, s.reshape(-1, 1)])
    XtW = X.T @ W
    cov = np.linalg.pinv(XtW @ X, rcond=1e-12)
    coef = cov @ (XtW @ y)
    d = coef[: n - 1]
    cov_d = cov[: n - 1, : n - 1]
    # embed back to the full n-dim reference parameterization (reference = 0)
    theta = np.zeros(n)
    theta[keep] = d
    cov_full = np.zeros((n, n))
    cov_full[np.ix_(keep, keep)] = cov_d
    beta = float(coef[n - 1]) if kind is not None else 0.0
    var_beta = float(cov[n - 1, n - 1]) if kind is not None else 0.0
    return theta, cov_full, beta, var_beta


def network_asymmetry(comps: Sequence[Comparison] | Sequence[tuple],
                      reference: str | None = None,
                      tau2_map: dict | None = None) -> dict:
    """Network-funnel asymmetry test (the network Egger analog).

    Fits the PET augmented model (covariate = se) and tests the slope beta. A
    significant positive beta means small (high-se) studies are systematically
    more extreme -> small-study/selection effect. Two-sided p via the normal.
    """
    comps = [c if isinstance(c, Comparison) else Comparison(*c) for c in comps]
    treatments, tidx, n, B, W, y, se, tau2 = _prep(comps, tau2_map)
    if reference is None:
        reference = treatments[0]
    ridx = tidx[reference]
    _, _, beta, var_beta = _augmented_solve(B, W, y, se, n, ridx, "pet")
    z = beta / np.sqrt(var_beta) if var_beta > _EPS else 0.0
    p = float(2.0 * norm.sf(abs(z)))
    return {"beta": float(beta), "se_beta": float(np.sqrt(max(var_beta, 0.0))),
            "z": float(z), "p": p, "tau2": float(tau2)}


def network_smallstudy_league(comps: Sequence[Comparison] | Sequence[tuple],
                              reference: str | None = None,
                              kind: str = "peese",
                              tau2_map: dict | None = None) -> NMAFit:
    """Bias-adjusted league via the augmented network meta-regression.

    kind='peese' (covariate se^2, recommended when effects are non-null) or
    'pet' (covariate se). kind=None reproduces the engine league exactly.
    The reported seTE come from the augmented-WLS covariance, so they correctly
    widen for the extra estimated slope.
    """
    comps = [c if isinstance(c, Comparison) else Comparison(*c) for c in comps]
    treatments, tidx, n, B, W, y, se, tau2 = _prep(comps, tau2_map)
    if reference is None:
        reference = treatments[0]
    ridx = tidx[reference]
    theta, cov_full, beta, var_beta = _augmented_solve(B, W, y, se, n, ridx, kind)
    TE, seTE = _league(theta, cov_full, treatments)
    k = len({c.studlab for c in comps})
    return NMAFit(
        treatments=treatments, theta=theta, Lplus=cov_full, TE=TE, seTE=seTE,
        tau2=float(tau2), tau=float(np.sqrt(tau2)), Q=0.0, df_Q=0, I2=0.0,
        n=n, k=k, m=len(comps), reference=reference, random=True,
        meta={"treatments": treatments, "tidx": tidx, "beta": beta,
              "var_beta": var_beta, "kind": kind},
    )
