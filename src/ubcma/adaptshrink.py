"""AdaptShrink: robust adaptive aggregation of bias-correction estimators.

Motivation
----------
Under *unknown* publication-selection mechanisms, no single estimator is
uniformly best. The bake-off in `truth-recovery/` shows the naive
random-effects estimator and the in-repo Copas comparator are biased UP by
selection (bias ~ +0.10 under strong misspecification), trim-and-fill is biased
DOWN (~ -0.07), while PET-PEESE (~ +0.06) and UBCMA (~ +0.02) sit closer to the
truth. The errors of these *bias-corrected* members partly straddle the truth,
so a robust weighted combination of them can have both lower bias (opposing
biases cancel) and lower variance (averaging independent error) than any single
member.

AdaptShrink does NOT see the truth. It is an oracle-free estimator:

  1. Collect a panel of bias-corrected estimates (default: ubcma, pet_peese,
     trim_and_fill), each with a point estimate `mu_j` and standard error
     `se_j`.
  2. Form a robust median `m`. Penalize members that disagree with the
     consensus: weight `w_j = 1 / (se_j^2 + (mu_j - m)^2)`. This simultaneously
     down-weights noisy members (large se_j) and outlying members (large
     disagreement), which is exactly the behaviour we want when one member's
     selection model is misspecified.
  3. Point estimate: `mu_AS = sum(w_j mu_j) / sum(w_j)`.
  4. Interval: a model-averaging variance that adds the within-member sampling
     variance to the between-member spread (Burnham & Anderson style), then a
     single transparent calibration multiplier `kappa` (default 1.0). The
     between-member term is what lets the interval widen automatically when the
     panel disagrees -- i.e. when selection is severe and the members diverge.

The calibration multiplier `kappa` is the ONLY tunable; it is reported
explicitly and is the lever the matched-coverage scorer uses to put every
method on an equal coverage footing. With `kappa=1.0` the interval is the raw
model-averaging interval.

Truth-first: nothing here is hand-tuned to a target number. The default member
set and weighting rule are fixed a priori; the bake-off then measures, honestly,
whether this beats Henmi-Copas at matched coverage.
"""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np
from scipy.stats import norm
from scipy.stats import t as t_dist

from .comparators import copas_selection, pet_peese, reml_estimator, trim_and_fill

# Two-sided 97.5% normal quantile; used to convert a CI half-width back to an
# effective symmetric SE when a member only exposes an interval.
AS_Z975 = 1.959963984540054

# Default panel: the bias-CORRECTED estimators. The naive RE and Copas members
# are deliberately excluded from the default because under selection they share
# the same upward bias and would just out-vote the corrections.
DEFAULT_MEMBERS = ("ubcma", "pet_peese", "trim_and_fill")

_EPS = 1e-9

# Floor for a member's reported se. A member claiming se=0 (a "certain"
# estimate) must not be dropped by a `sem > 0` filter — that discards it
# entirely, leaving the aggregate to the noisy members. Flooring instead lets
# inverse-variance weighting give a near-exact member the dominant weight it
# deserves, while keeping every weight finite.
_SE_FLOOR = 1e-6


def _member_estimates(
    names: Sequence[str],
    y: np.ndarray,
    se: np.ndarray,
    quality_score: np.ndarray | None,
    precomputed: dict[str, tuple[float, float]] | None,
) -> list[tuple[str, float, float]]:
    """Return [(name, mu, se), ...] for each requested member.

    `precomputed` lets a caller (e.g. the bake-off harness) pass member
    estimates that were already computed for the comparator table, so AdaptShrink
    does not refit them. Any member not supplied is computed here from the cheap
    closed-form comparators. The 'ubcma' member, if requested and not
    precomputed, must be supplied -- we never refit UBCMA inside AdaptShrink
    because it is the expensive member and the harness already has it.
    """
    # Sanitize the study inputs used to compute any non-precomputed member. A
    # non-finite or non-positive se makes the weighted comparators (pet_peese,
    # reml, trim_and_fill) divide by ~0 -> LinAlgError ("SVD did not converge").
    # Drop those studies EXPLICITLY (fail closed, not a swallowed crash) and only
    # compute members when >= 2 valid studies remain — the comparators
    # (regression slope, heterogeneity) are undefined below that.
    y = np.asarray(y, dtype=float)
    se = np.asarray(se, dtype=float)
    valid = np.isfinite(y) & np.isfinite(se) & (se > 0)
    y_c, se_c = y[valid], se[valid]
    can_compute = y_c.size >= 2

    _COMPUTED = {"reml", "reml_hksj", "pet_peese", "trim_and_fill", "copas"}
    out: list[tuple[str, float, float]] = []
    for name in names:
        if precomputed and name in precomputed:
            mu, sem = precomputed[name]
        elif name in _COMPUTED:
            if not can_compute:
                continue  # too few valid studies to estimate this member
            try:
                if name in ("reml", "reml_hksj"):
                    r = reml_estimator(y_c, se_c, hksj=(name == "reml_hksj"))
                elif name == "pet_peese":
                    r = pet_peese(y_c, se_c)
                elif name == "trim_and_fill":
                    r = trim_and_fill(y_c, se_c)
                else:
                    r = copas_selection(y_c, se_c)
            except np.linalg.LinAlgError:
                # Defense in depth: a member that fails numerically on otherwise-
                # valid data is simply unavailable (reflected in n_members), not
                # a crash. Not a blanket except — only the numerical failure.
                continue
            mu, sem = r["mu"], r["se"]
        else:
            # ubcma or any unknown member with no precomputed value: skip rather
            # than refit (caller is responsible for supplying it).
            continue
        if np.isfinite(mu) and np.isfinite(sem):
            # Floor (don't drop) so a claimed-exact member dominates via inverse
            # variance rather than silently vanishing.
            out.append((name, float(mu), float(max(sem, _SE_FLOOR))))
    return out


def adaptshrink_estimator(
    y: np.ndarray,
    se: np.ndarray,
    quality_score: np.ndarray | None = None,
    members: Sequence[str] = DEFAULT_MEMBERS,
    precomputed: dict[str, tuple[float, float]] | None = None,
    kappa: float = 1.0,
    alpha: float = 0.05,
    use_t: bool = True,
) -> dict[str, Any]:
    """Robust adaptive-shrinkage aggregate of a panel of estimators.

    Parameters
    ----------
    y, se : observed effects and standard errors (used only to compute any
        member not supplied via `precomputed`).
    members : which estimators form the panel.
    precomputed : {name: (mu, se)} estimates already available (avoids refits).
    kappa : transparent CI calibration multiplier (1.0 = raw model-averaging CI).
    alpha : two-sided level (0.05 -> 95% CI).
    use_t : use a t critical value with df = (#members - 1) for the between-model
        spread; falls back to normal when only one member survives.
    """
    panel = _member_estimates(members, y, se, quality_score, precomputed)
    if not panel:
        return {
            "mu": float("nan"), "se": float("nan"),
            "ci_low": float("nan"), "ci_high": float("nan"),
            "converged": False, "n_members": 0, "weights": {},
        }

    mus = np.array([p[1] for p in panel], dtype=float)
    ses = np.array([p[2] for p in panel], dtype=float)
    s2 = np.square(ses)

    m_med = float(np.median(mus))
    disagreement = np.square(mus - m_med)
    w = 1.0 / (s2 + disagreement + _EPS)
    w_sum = float(np.sum(w))
    mu_as = float(np.sum(w * mus) / w_sum)

    # Model-averaging variance: within-member sampling variance of the weighted
    # mean plus the between-member spread around the aggregate.
    within_var = float(np.sum(np.square(w) * s2) / (w_sum ** 2))
    between_var = float(np.sum(w * np.square(mus - mu_as)) / w_sum)
    total_se = float(np.sqrt(max(within_var + between_var, _EPS)))

    n = len(panel)
    if use_t and n >= 2:
        crit = float(t_dist.ppf(1.0 - alpha / 2.0, df=n - 1))
    else:
        crit = float(norm.ppf(1.0 - alpha / 2.0))
    half = kappa * crit * total_se

    return {
        "mu": mu_as,
        "se": total_se,
        "ci_low": mu_as - half,
        "ci_high": mu_as + half,
        "converged": True,
        "n_members": n,
        "within_var": within_var,
        "between_var": between_var,
        "kappa": float(kappa),
        "weights": {p[0]: float(wi / w_sum) for p, wi in zip(panel, w)},
        "members": {p[0]: {"mu": p[1], "se": p[2]} for p in panel},
    }
