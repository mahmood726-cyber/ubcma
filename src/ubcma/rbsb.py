r"""RBSB: Robust Bayesian Sequential Borrowing (PILOT, reference implementation).

Faithful minimal reimplementation of the estimator in

    Hermansson, Dunsire, Svensson, Jaki (2026),
    "Robust Bayesian Sequential Borrowing for Multi-Population Clinical
    Programmes", arXiv:2604.22431.

This lives ALONGSIDE :mod:`ubcma.adaptshrink` as a pilot in the dynamic-borrowing
lane. It is NOT promoted into any live method, manuscript, or the public
``ubcma`` API. It is closed-form and dependency-light (numpy + a Normal density)
so the sanity limits below are exhaustively unit-tested offline.

The construction (Section 2.2 of the paper)
-------------------------------------------
A programme observes ordered populations j = 1..K, each summarised by an
asymptotically-sufficient pair ``theta_j = (mu_hat_j, se_hat_j)`` with

    mu_hat_j | mu_j ~ N(mu_j, se_hat_j).

A unit-information Normal prior is the pseudo-study ``theta_0 = (mu0, s0)``
(mu0 = 0 encodes no-effect; s0 = information of one observation on the parameter
scale). Borrowing is strictly *path-dependent*: information flows only along
contiguous adjacent paths in the pre-specified order.

Adjacent-only paths ending at study j:

    P_{1:j} = { S_{i:j} = {i, i+1, ..., j} : 1 <= i <= j }        (Eqs. 3-4)

Each path is pooled by precision, *including* the unit-information prior
(Section 2.2, precision-weighted pooling of (mu0, s0) with the studies in S):

    tau0 = 1/s0^2 ,  tau_l = 1/se_hat_l^2
    tau_S = tau0 + sum_{l in S} tau_l
    s_S^2 = 1/tau_S
    mu_S  = ( tau0*mu0 + sum_{l in S} tau_l*mu_hat_l ) / tau_S

(The illustrative two-study line in the paper's Section 2 omits tau0 for
exposition; the formal Section 2.2 pooling equation — implemented here — carries
tau0 in every path. The prior enters each informative path as a regulariser AND
appears once more as the standalone robustifying *vague* component; the paper
states this is intended, not double counting, because the prior is never itself
a *path*.)

Robust mixture prior for study j+1 (Eq. 2):

    pi(mu_{j+1} | theta_{1:j})
        = w_{j+1} * sum_{S in P_{1:j}} W_S N(mu_S, s_S)
          + (1 - w_{j+1}) * N(mu0, s0)

with fixed, pre-specified step weights ``w_j in [0,1]`` (w_1 = 0, no borrowing at
the first study) and data-updated posterior path weights (Eq. 5, w*_1 := 0):

    W_{S_{i:j}} = (1 - w*_i) * prod_{l=i+1}^{j} w*_l ,   i = 1..j
                                          (empty product = 1 for the singleton)

The posterior mixture weight after observing theta_j:

    w*_j = w_j * m_inf(theta_j)
           / ( w_j * m_inf(theta_j) + (1 - w_j) * m_vag(theta_j) )

    m_inf(theta_j) = sum_{S in P_{1:j-1}} W_S * phi( mu_hat_j; mu_S,
                                             sqrt(s_S^2 + se_hat_j^2) )
    m_vag(theta_j) = phi( mu_hat_j; mu0, sqrt(s0^2 + se_hat_j^2) )

where phi(x; m, s) is the Normal(m, s) density. w*_j is the aggregate posterior
weight on the informative block versus the vague block, giving transparent,
data-driven attenuation: under prior-data conflict m_inf -> 0 so w*_j -> 0 and
borrowing switches off automatically.

Sanity limits guaranteed by construction (asserted in tests/test_rbsb.py):
  * k=1: no informative paths -> prior is purely the unit-information vague
    component -> posterior is the conjugate unit-information update (reference,
    no borrowing).
  * uninformative ordering (all w_j = 0): every step uses only the vague
    component, w*_j = 0, so each population's estimate is its own conjugate
    unit-information update, independent of the other studies and their order
    (reduces to no-borrowing shrinkage).
  * K=2: reduces EXACTLY to the two-component robust-MAP (Schmidli et al. 2014)
    posterior with informative prior N(mu_S={1}, s_S={1}) and vague N(mu0, s0).
  * path weights are a proper mixture: sum_{S in P_{1:j}} W_S = 1.

Truth-first: no quantitative headline from the paper is reproduced or asserted
here; only the estimator construction and its limits are validated.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, List, Optional, Sequence

import numpy as np

_SQRT_2PI = math.sqrt(2.0 * math.pi)


def _norm_pdf(x: float, mean: float, sd: float) -> float:
    """Normal(mean, sd) density at x. Pure so tests need no scipy."""
    z = (x - mean) / sd
    return math.exp(-0.5 * z * z) / (sd * _SQRT_2PI)


def _pool_path(mu0: float, s0: float, mus: Sequence[float],
               ses: Sequence[float]) -> tuple[float, float]:
    """Precision-weighted pool of the unit-information prior (mu0, s0) with the
    studies (mus, ses) on a contiguous path. Returns (mu_S, s_S)."""
    tau0 = 1.0 / (s0 * s0)
    tau_S = tau0
    num = tau0 * mu0
    for mu, se in zip(mus, ses):
        tau = 1.0 / (se * se)
        tau_S += tau
        num += tau * mu
    mu_S = num / tau_S
    s_S = math.sqrt(1.0 / tau_S)
    return mu_S, s_S


@dataclass
class RBSBStep:
    """Per-population result after sequential borrowing up to and including j."""
    index: int                       # 1-based study index j
    mu_hat: float
    se_hat: float
    w_prior: float                   # pre-specified borrowing weight w_j
    w_star: float                    # data-updated posterior informative weight w*_j
    post_mean: float                 # posterior mean of mu_j (borrowed estimate)
    post_sd: float                   # posterior sd of mu_j
    m_inf: float = float("nan")      # informative marginal likelihood of theta_j
    m_vag: float = float("nan")      # vague marginal likelihood of theta_j
    path_weights: dict[str, float] = field(default_factory=dict)  # W_S over P_{1:j}


@dataclass
class RBSBResult:
    steps: List[RBSBStep]
    mu0: float
    s0: float

    @property
    def final(self) -> RBSBStep:
        return self.steps[-1]

    # Convenience accessors mirroring the other estimators' dict-ish outputs.
    @property
    def mu(self) -> float:
        return self.final.post_mean

    @property
    def se(self) -> float:
        return self.final.post_sd

    def as_dict(self) -> dict[str, Any]:
        return {
            "mu0": self.mu0, "s0": self.s0,
            "mu": self.mu, "se": self.se,
            "w_star": [s.w_star for s in self.steps],
            "post_mean": [s.post_mean for s in self.steps],
            "post_sd": [s.post_sd for s in self.steps],
        }


def _paths_ending_at(j_upper: int) -> List[tuple[int, int]]:
    """Adjacent-only paths S_{i:j_upper} = (i, j_upper) for i = 1..j_upper.
    Returns list of (i, j_upper) with 1-based inclusive endpoints."""
    return [(i, j_upper) for i in range(1, j_upper + 1)]


def _path_weights(w_star: Sequence[float], j_upper: int) -> dict[tuple[int, int], float]:
    """Posterior path weights W_{S_{i:j_upper}} via Eq. 5, using w*_1..w*_{j_upper}.

    ``w_star`` is 1-indexed conceptually; we pass a 0-indexed list where
    w_star[t] == w*_{t+1}. Convention w*_1 := 0 must already be encoded in the
    caller's list. Returns { (i, j_upper): W }.
    """
    weights: dict[tuple[int, int], float] = {}
    for i in range(1, j_upper + 1):
        prod = 1.0
        for l in range(i + 1, j_upper + 1):
            prod *= w_star[l - 1]           # w*_l
        weights[(i, j_upper)] = (1.0 - w_star[i - 1]) * prod   # (1 - w*_i) * prod
    return weights


def rbsb_estimator(
    mu_hat: Sequence[float],
    se_hat: Sequence[float],
    w: Optional[Sequence[float]] = None,
    *,
    mu0: float = 0.0,
    s0: float = 1.0,
) -> RBSBResult:
    """Robust Bayesian Sequential Borrowing over an ordered programme.

    Parameters
    ----------
    mu_hat, se_hat : ordered per-population effect estimates and standard errors
        (index 0 is the first study in the programme order).
    w : per-step borrowing weights w_j in [0, 1]. ``w[0]`` is forced to 0 (no
        borrowing at the first study, by convention). If None, defaults to 0.5
        for every step j >= 2 (a neutral prior degree of borrowing) — this is an
        analyst choice and should be pre-specified per the paper.
    mu0, s0 : unit-information prior mean and scale on the parameter (analysis)
        scale. mu0 = 0 encodes the no-effect convention; s0 must be chosen on the
        working scale (the paper stresses s0 materially affects borrowing). The
        default s0 = 1.0 suits standardized / log-scale effects and is NOT a
        universal constant.

    Returns
    -------
    RBSBResult with a per-population :class:`RBSBStep` (posterior mean/sd of each
    mu_j after adjacent-only borrowing, plus the data-updated weight w*_j and the
    normalized path weights over P_{1:j}).
    """
    mu = np.asarray(mu_hat, dtype=float)
    se = np.asarray(se_hat, dtype=float)
    K = mu.shape[0]
    if K == 0:
        raise ValueError("rbsb_estimator needs at least one study")
    if se.shape[0] != K:
        raise ValueError("mu_hat and se_hat must have equal length")
    if np.any(se <= 0):
        raise ValueError("all standard errors must be positive")

    if w is None:
        w_list = [0.0] + [0.5] * (K - 1)
    else:
        w_list = [float(x) for x in w]
        if len(w_list) != K:
            raise ValueError("w must have the same length as mu_hat")
        w_list[0] = 0.0                       # w_1 = 0 by convention
    if any((x < 0.0 or x > 1.0) for x in w_list):
        raise ValueError("borrowing weights w_j must lie in [0, 1]")

    tau0 = 1.0 / (s0 * s0)
    w_star: List[float] = []                  # w_star[t] == w*_{t+1}
    steps: List[RBSBStep] = []

    for j in range(1, K + 1):                 # 1-based study index
        muj = float(mu[j - 1])
        sej = float(se[j - 1])
        wj = w_list[j - 1]

        # --- informative marginal likelihood m_inf(theta_j) over P_{1:j-1} ----
        if j == 1:
            # No informative paths exist; w*_1 := 0 by convention.
            m_inf = 0.0
            m_vag = _norm_pdf(muj, mu0, math.sqrt(s0 * s0 + sej * sej))
            wstar_j = 0.0
            pw_prior: dict[tuple[int, int], float] = {}
        else:
            pw_prior = _path_weights(w_star, j - 1)   # W_S over P_{1:j-1}
            m_inf = 0.0
            for (i_lo, i_hi), WS in pw_prior.items():
                mu_S, s_S = _pool_path(mu0, s0, mu[i_lo - 1:i_hi],
                                       se[i_lo - 1:i_hi])
                m_inf += WS * _norm_pdf(muj, mu_S, math.sqrt(s_S * s_S + sej * sej))
            m_vag = _norm_pdf(muj, mu0, math.sqrt(s0 * s0 + sej * sej))
            denom = wj * m_inf + (1.0 - wj) * m_vag
            wstar_j = (wj * m_inf / denom) if denom > 0.0 else 0.0

        w_star.append(wstar_j)

        # --- posterior for mu_j: conjugate update of each prior component ------
        # Prior components: informative paths S in P_{1:j-1} with prior weight
        # w_j * W_S, plus the vague N(mu0, s0) with prior weight (1 - w_j). The
        # posterior component weight is prior_weight * (that component's marginal
        # likelihood of theta_j); aggregate informative weight is exactly w*_j.
        comps: List[tuple[float, float, float]] = []   # (weight, post_mean, post_var)
        if j == 1 or wj == 0.0 or m_inf == 0.0:
            # Pure vague posterior (also the k=1 and uninformative-ordering case).
            pm, pv = _conjugate(mu0, s0, muj, sej)
            comps.append((1.0, pm, pv))
        else:
            # Informative block: each path, renormalised within the block by its
            # marginal likelihood so the block's total weight is w*_j.
            block_ml: List[tuple[float, float, float]] = []
            ml_sum = 0.0
            for (i_lo, i_hi), WS in pw_prior.items():
                mu_S, s_S = _pool_path(mu0, s0, mu[i_lo - 1:i_hi],
                                       se[i_lo - 1:i_hi])
                ml = WS * _norm_pdf(muj, mu_S, math.sqrt(s_S * s_S + sej * sej))
                pm, pv = _conjugate(mu_S, s_S, muj, sej)
                block_ml.append((ml, pm, pv))
                ml_sum += ml
            for ml, pm, pv in block_ml:
                frac = (ml / ml_sum) if ml_sum > 0.0 else 0.0
                comps.append((wstar_j * frac, pm, pv))
            pm_v, pv_v = _conjugate(mu0, s0, muj, sej)
            comps.append((1.0 - wstar_j, pm_v, pv_v))

        post_mean = sum(wt * pm for wt, pm, _ in comps)
        # Mixture variance = E[var] + Var[mean] across components.
        post_var = sum(wt * (pv + pm * pm) for wt, pm, pv in comps) - post_mean ** 2
        post_sd = math.sqrt(max(post_var, 0.0))

        pw_current = _path_weights(w_star, j)          # W_S over P_{1:j}
        steps.append(RBSBStep(
            index=j, mu_hat=muj, se_hat=sej, w_prior=wj, w_star=wstar_j,
            post_mean=post_mean, post_sd=post_sd, m_inf=m_inf, m_vag=m_vag,
            path_weights={f"{lo}:{hi}": v for (lo, hi), v in pw_current.items()},
        ))

    return RBSBResult(steps=steps, mu0=mu0, s0=s0)


def _conjugate(prior_mean: float, prior_sd: float, obs_mu: float,
               obs_se: float) -> tuple[float, float]:
    """Conjugate Normal-Normal update: prior N(prior_mean, prior_sd) with a
    single observation obs_mu of known se obs_se. Returns (post_mean, post_var)."""
    tp = 1.0 / (prior_sd * prior_sd)
    to = 1.0 / (obs_se * obs_se)
    post_var = 1.0 / (tp + to)
    post_mean = post_var * (tp * prior_mean + to * obs_mu)
    return post_mean, post_var


def robust_map_2component(
    informative_mean: float, informative_sd: float,
    vague_mean: float, vague_sd: float,
    w: float, obs_mu: float, obs_se: float,
) -> dict[str, float]:
    """Independent two-component robust-MAP (Schmidli et al. 2014) update.

    Provided as the reference against which RBSB's K=2 behaviour is checked (it
    is coded from the robust-MAP definition, NOT from RBSB, so the K=2 sanity
    test is a genuine cross-check rather than a tautology).

    Prior = w * N(informative) + (1 - w) * N(vague). Returns the posterior mean,
    sd, and the posterior weight on the informative component.
    """
    m_inf = _norm_pdf(obs_mu, informative_mean,
                      math.sqrt(informative_sd ** 2 + obs_se ** 2))
    m_vag = _norm_pdf(obs_mu, vague_mean,
                      math.sqrt(vague_sd ** 2 + obs_se ** 2))
    denom = w * m_inf + (1.0 - w) * m_vag
    w_star = (w * m_inf / denom) if denom > 0.0 else 0.0

    pm_i, pv_i = _conjugate(informative_mean, informative_sd, obs_mu, obs_se)
    pm_v, pv_v = _conjugate(vague_mean, vague_sd, obs_mu, obs_se)
    post_mean = w_star * pm_i + (1.0 - w_star) * pm_v
    post_var = (w_star * (pv_i + pm_i ** 2)
                + (1.0 - w_star) * (pv_v + pm_v ** 2)) - post_mean ** 2
    return {
        "w_star": w_star,
        "post_mean": post_mean,
        "post_sd": math.sqrt(max(post_var, 0.0)),
    }
