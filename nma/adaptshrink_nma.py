"""adaptshrink_nma.py -- AdaptShrink generalized to network meta-analysis.

The univariate AdaptShrink shrinks a *scalar* tau^2 (and averages a panel of
bias-corrected point estimators). AdaptShrink-NMA instead adaptively shrinks the
**heterogeneity structure across comparisons**: each comparison type gets its own
direct heterogeneity tau^2_c, shrunk toward the network-common tau^2 by a weight
that depends on how much direct data and direct (vs borrowed-indirect) evidence
that comparison has. It is built on the verified graph-theoretic engine
(`nma_core`), so multi-arm correlation and the GLS league stay netmeta-exact.

Component (A) -- adaptive heterogeneity-structure shrinkage (implemented here):

    tau^2_c(lambda_c) = lambda_c * tau^2_common + (1 - lambda_c) * tau^2_c,direct
    lambda_c          = nu / (nu + (n_c - 1) * s_c)
    s_c               = var_network_c / var_direct_c  in (0, 1]

  * tau^2_c,direct : DerSimonian-Laird tau^2 from the DIRECT studies of c only.
  * tau^2_common   : the network generalized-DL tau^2 (netmeta default).
  * n_c            : number of direct studies for comparison c.
  * s_c            : geometry weight. ~1 when c's network estimate is driven by
                     its own direct evidence (trust its own tau^2 -> shrink less);
                     small when c borrows lots of indirect strength
                     (var_network << var_direct -> shrink toward common more).
  * nu             : the single transparent tuning constant (the AdaptShrink
                     `kappa` analog). nu -> 0 recovers comparison-specific tau^2;
                     nu -> inf recovers common-tau^2. Reported explicitly and
                     calibrated only on a held-out split in the matched-coverage
                     scorer.

Components (B) network-funnel-asymmetry-gated small-study correction and
(C) inconsistency-aware interval inflation are designed in DESIGN_BRIEF.md and
land in iteration 2; (C) has a hook here (`incons_inflate`).
"""
from __future__ import annotations

from typing import Sequence

import numpy as np

from nma_core import Comparison, NMAFit, fit_nma, _study_blocks

_EPS = 1e-12


def _dl_univariate(y: np.ndarray, v: np.ndarray) -> float:
    """Classic DerSimonian-Laird tau^2 for a single set of direct estimates."""
    k = len(y)
    if k < 2:
        return 0.0
    w = 1.0 / v
    mu = np.sum(w * y) / np.sum(w)
    Q = float(np.sum(w * (y - mu) ** 2))
    C = float(np.sum(w) - np.sum(w ** 2) / np.sum(w))
    if C <= _EPS:
        return 0.0
    return max(0.0, (Q - (k - 1)) / C)


def _direct_by_type(comps: Sequence[Comparison]) -> dict[frozenset, list[tuple[float, float]]]:
    """Collect direct (te, var) observations for each comparison type.

    Each pairwise row (including those from multi-arm studies) is direct evidence
    for its own treatment pair.
    """
    out: dict[frozenset, list[tuple[float, float]]] = {}
    for c in comps:
        out.setdefault(frozenset((c.t1, c.t2)), []).append((c.te, c.se ** 2))
    return out


def _network_var_for_type(fit: NMAFit, a: str, b: str) -> float:
    tidx = fit.meta["tidx"]
    return float(fit.seTE[tidx[a], tidx[b]] ** 2)


def compute_shrunk_tau2(comps: Sequence[Comparison], nu: float = 4.0,
                        return_detail: bool = False):
    """Return tau2_map {frozenset: tau^2_c(shrunk)} for AdaptShrink-NMA.

    nu is the transparent shrinkage constant. Larger nu -> more shrink toward the
    common tau^2 (stable, sparse-network-friendly); nu=0 -> comparison-specific.
    """
    # common tau^2 from the network DL fit (netmeta default)
    fit_common = fit_nma(comps, random=True)
    tau2_common = fit_common.tau2

    direct = _direct_by_type(comps)
    tau2_map: dict[frozenset, float] = {}
    detail = {}
    for typ, obs in direct.items():
        a, b = tuple(typ)
        n_c = len(obs)
        y = np.array([o[0] for o in obs])
        v = np.array([o[1] for o in obs])

        if n_c < 2:
            # no direct heterogeneity estimate -> fully borrow common
            lam = 1.0
            tau2_dir = tau2_common
            s_c = 0.0
        else:
            tau2_dir = _dl_univariate(y, v)
            # direct-only fixed-effect variance vs network variance for this type
            var_dir = 1.0 / float(np.sum(1.0 / v))
            var_net = _network_var_for_type(fit_common, a, b)
            s_c = float(np.clip(var_net / max(var_dir, _EPS), 0.0, 1.0))
            lam = nu / (nu + (n_c - 1) * s_c)

        tau2_c = lam * tau2_common + (1.0 - lam) * tau2_dir
        tau2_map[typ] = float(max(tau2_c, 0.0))
        detail[typ] = {"n_c": n_c, "tau2_direct": float(tau2_dir),
                       "s_c": float(s_c), "lambda": float(lam),
                       "tau2_shrunk": tau2_map[typ]}

    if return_detail:
        return tau2_map, tau2_common, detail
    return tau2_map


def adaptshrink_nma(comps: Sequence[Comparison] | Sequence[tuple],
                    reference: str | None = None,
                    nu: float = 4.0,
                    kappa: float = 1.0,
                    incons_inflate: bool = False) -> NMAFit:
    """Fit AdaptShrink-NMA: graph-theoretic NMA with adaptively-shrunk
    comparison-specific heterogeneity.

    Parameters
    ----------
    nu     : heterogeneity-shrinkage constant (transparent tuning lever).
    kappa  : interval calibration multiplier on seTE (1.0 = raw); the
             matched-coverage scorer is what sets this on a held-out split.
    incons_inflate : hook for component (C); not yet active (iteration 2).
    """
    comps = [c if isinstance(c, Comparison) else Comparison(*c) for c in comps]
    tau2_map = compute_shrunk_tau2(comps, nu=nu)
    fit = fit_nma(comps, reference=reference, random=True, tau2_map=tau2_map)
    if kappa != 1.0:
        fit.seTE = fit.seTE * kappa
    fit.meta["nu"] = nu
    fit.meta["kappa"] = kappa
    fit.meta["tau2_map"] = {tuple(sorted(k)): v for k, v in tau2_map.items()}
    return fit
