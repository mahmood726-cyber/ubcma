"""Gravitational borrowing field (minimal pilot, gaps #1+#2 only).

A target comparison's effect is estimated by FUSING its own (sparse) direct
evidence with a BORROWING PRIOR formed from *other* trials in the registry
field. Each source trial s contributes to the prior with weight

    w_s  =  K_relevance(x_s, x_target)  x  lambda_s  x  (1 / se_s^2)

where
  * K_relevance = mechanism-class similarity x baseline-HbA1c Gaussian kernel
    (covariate / indication distance -- the "gravity"),
  * lambda_s    = GWAM registry-linkage integrity ratio of the source's class
    (selection-integrity term; low lambda = selection-prone -> borrow less),
  * 1/se_s^2    = sampling precision.

The prior (mu_p, se_p) is then fused with the own-data estimate (mu0, se0)
through the validated AdaptShrink kernel, which supplies an honest
model-averaging interval that widens when the two disagree.

STAND-DOWN (required): before fusion the prior's influence is discounted by a
data-driven factor delta in (0, 1] computed from the prior-data CONFLICT
statistic Q = (mu0 - mu_p)^2 / (se0^2 + se_p^2). When the borrowed prior
conflicts with the own data (large Q), delta -> 0, the prior's effective SE is
inflated, and the fused estimate falls back toward the no-borrowing estimate
with a widened interval. This is the "reduce toward no-borrowing when
over-borrowing is detected" guarantee.

NOTHING here is tuned to a target number. The relevance map, kernel bandwidth,
and stand-down constants (eta, c0) are fixed a priori and reported. The
matched-coverage truth gate then measures, honestly, whether this beats
standard NMA on sparse held-out effects.
"""
from __future__ import annotations

import sys
from pathlib import Path
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ubcma.adaptshrink import adaptshrink_estimator  # noqa: E402
from ubcma.comparators import reml_estimator  # noqa: E402

# ---- a-priori relevance structure (pre-registered, not tuned to outcomes) ----
# Mechanism groups for the cross-class "indication distance".
MECHANISM = {
    "GLP1": "incretin", "DPP4": "incretin",
    "SGLT2": "glucosuric",
    "SU": "secretagogue", "glinide": "secretagogue",
    "metformin": "sensitizer", "TZD": "sensitizer",
    "insulin": "insulin", "AGI": "agi",
}
MECH_SAME_GROUP = 0.6   # same mechanism group, different class
MECH_DIFF_GROUP = 0.3   # different mechanism group
BASELINE_BW = 1.0       # Gaussian bandwidth (HbA1c %) for baseline distance
ETA = 0.5               # stand-down sharpness
C0 = 1.0                # stand-down threshold (Q below this => no discount)
DEFAULT_BASELINE = 8.1  # field-typical baseline HbA1c when a trial lacks it


@dataclass
class Source:
    active: str
    y: float
    se: float
    baseline: float
    lam: float


def mech_similarity(class_s: str, class_t: str) -> float:
    """Cross-class mechanism/indication similarity in [0, 1]. Same class is
    excluded upstream (true cross-class borrowing), so the max here is for a
    different class in the same mechanism group."""
    if class_s == class_t:
        return 1.0
    return MECH_SAME_GROUP if MECHANISM.get(class_s) == MECHANISM.get(class_t) else MECH_DIFF_GROUP


def borrowing_prior(target_class: str, target_baseline: float,
                    sources: list[Source], bw: float = BASELINE_BW,
                    uniform: bool = False) -> tuple[float, float, float]:
    """Form the borrowing prior (mu_p, se_p, ess) from cross-class sources.

    uniform=True strips the relevance kernel and the integrity lambda (weight =
    precision only) -> a plain inverse-variance field-mean shrinkage prior. This
    is the null that isolates whether the covariate-"gravity" + integrity
    machinery contributes anything beyond shrinking toward the field mean.

    Returns (nan, inf, 0) if no source has positive weight.
    """
    if not sources:
        return float("nan"), float("inf"), 0.0
    tb = target_baseline if np.isfinite(target_baseline) else DEFAULT_BASELINE
    mus = np.array([s.y for s in sources], float)
    se = np.array([s.se for s in sources], float)
    w = np.empty(len(sources))
    for i, s in enumerate(sources):
        prec = 1.0 / max(s.se ** 2, 1e-9)
        if uniform:
            w[i] = prec
            continue
        sb = s.baseline if (s.baseline is not None and np.isfinite(s.baseline)) else DEFAULT_BASELINE
        k_base = np.exp(-0.5 * ((sb - tb) / bw) ** 2)
        rel = mech_similarity(s.active, target_class) * k_base
        w[i] = rel * max(s.lam, 1e-3) * prec
    wsum = float(w.sum())
    if wsum <= 0:
        return float("nan"), float("inf"), 0.0
    mu_p = float((w * mus).sum() / wsum)
    # prior SE = sampling variance of the weighted mean + between-source spread
    # (the field is heterogeneous; the prior must not pretend to be a single
    # precise study). This is the honest uncertainty the stand-down then scales.
    within = float((w ** 2 * se ** 2).sum() / wsum ** 2)
    between = float((w * (mus - mu_p) ** 2).sum() / wsum)
    se_p = float(np.sqrt(max(within + between, 1e-9)))
    ess = float(wsum ** 2 / (w ** 2).sum())  # effective number of sources
    return mu_p, se_p, ess


def stand_down_delta(mu0: float, se0: float, mu_p: float, se_p: float,
                     eta: float = ETA, c0: float = C0) -> tuple[float, float]:
    """Conflict-driven discount delta in (0, 1] on the prior's influence.

    Q = (mu0 - mu_p)^2 / (se0^2 + se_p^2) is a 1-df prior-data conflict
    statistic. delta = exp(-eta * max(0, Q - c0)). Returns (delta, Q).
    """
    if not (np.isfinite(mu0) and np.isfinite(mu_p) and np.isfinite(se_p)):
        return 0.0, float("inf")
    Q = (mu0 - mu_p) ** 2 / (se0 ** 2 + se_p ** 2 + 1e-12)
    delta = float(np.exp(-eta * max(0.0, Q - c0)))
    return delta, float(Q)


def borrow_estimate(own_y: np.ndarray, own_se: np.ndarray, target_class: str,
                    target_baseline: float, sources: list[Source],
                    alpha: float = 0.05, uniform_prior: bool = False) -> dict:
    """Borrowing-field estimate for one target comparison.

    own_y, own_se : the sparse direct trial effects available for the target.
    sources       : cross-class field trials (target class excluded).
    uniform_prior : if True, use a plain field-mean prior (no relevance/lambda)
        -- the null comparator for the negative-control diagnostic.
    """
    # own-data (no-borrow) estimate: REML random-effects pool of available trials
    if len(own_y) == 1:
        mu0, se0 = float(own_y[0]), float(own_se[0])
    else:
        r = reml_estimator(np.asarray(own_y, float), np.asarray(own_se, float))
        mu0, se0 = float(r["mu"]), float(r["se"])

    mu_p, se_p, ess = borrowing_prior(target_class, target_baseline, sources,
                                      uniform=uniform_prior)
    delta, Q = stand_down_delta(mu0, se0, mu_p, se_p)

    if not np.isfinite(mu_p) or delta <= 1e-6:
        # nothing to borrow / full stand-down -> own estimate, widened minimally
        z = 1.959963984540054
        return {"mu": mu0, "se": se0, "ci_low": mu0 - z * se0, "ci_high": mu0 + z * se0,
                "delta": delta, "Q_conflict": Q, "mu_prior": mu_p, "se_prior": se_p,
                "prior_ess": ess, "borrowed": False}

    # stand-down inflates the prior's SE; AdaptShrink fuses own + discounted prior
    se_p_eff = se_p / np.sqrt(delta)
    res = adaptshrink_estimator(
        np.asarray(own_y, float), np.asarray(own_se, float),
        members=("own", "prior"),
        precomputed={"own": (mu0, se0), "prior": (mu_p, se_p_eff)},
        kappa=1.0, alpha=alpha, use_t=False,
    )
    res = dict(res)
    res.update({"delta": delta, "Q_conflict": Q, "mu_prior": mu_p,
                "se_prior": se_p, "se_prior_eff": float(se_p_eff),
                "prior_ess": ess, "borrowed": True})
    return res
