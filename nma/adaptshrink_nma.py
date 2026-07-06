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
from smallstudy_nma import network_asymmetry, network_smallstudy_league
from inconsistency_nma import inconsistency_factor

_EPS = 1e-12

# Two-sided gate level for the network-funnel asymmetry test (component B).
ASYM_GATE_P = 0.05
# Gate level for the design-by-treatment inconsistency test (component C).
INCONS_GATE_P = 0.10


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

    Orientation is canonicalized: the engine uses signed incidence
    (te = effect(t1) - effect(t2)), so the SAME pair recorded in opposite
    directions -- (A,B, te=+1) vs (B,A, te=-1) -- is identical evidence. Grouping
    by frozenset with the RAW te would treat those as maximally conflicting and
    spuriously inflate the direct tau^2 (e.g. 0 -> ~1.99). We re-express every
    observation in the sorted-label orientation (lo vs hi), negating te when the
    stored order is reversed, so direct heterogeneity is orientation-invariant.
    """
    out: dict[frozenset, list[tuple[float, float]]] = {}
    for c in comps:
        lo, hi = sorted((c.t1, c.t2))
        te = c.te if (c.t1, c.t2) == (lo, hi) else -c.te
        out.setdefault(frozenset((c.t1, c.t2)), []).append((te, c.se ** 2))
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


def adaptshrink_nma_auto(comps: Sequence[Comparison] | Sequence[tuple],
                         reference: str | None = None,
                         nu: float = 4.0,
                         asym_gate_p: float = ASYM_GATE_P,
                         incons_gate_p: float = INCONS_GATE_P,
                         smallstudy_kind: str = "peese",
                         enable_b: bool = True,
                         enable_c: bool = True) -> NMAFit:
    """Integrated AdaptShrink-NMA (components A + B + C with gates).

    Composition (each later component is additive and gated, so the estimator
    reduces to the netmeta field default on a clean, consistent, symmetric
    network):

      A (always)  adaptive heterogeneity-structure shrinkage -> tau2_map; sets
                  the random-effects block weights (milestone-1: nearer-nominal,
                  more uniform deployable coverage; no harm under homogeneity).
      B (gated)   if the network-funnel asymmetry test rejects (PET-slope two-
                  sided p < asym_gate_p), blend the league toward the PEESE
                  small-study-corrected league by an SNR shrink
                  lambda = beta^2 / (beta^2 + Var(beta)). Full correction when the
                  slope is large and well-estimated; ~none when marginal. This is
                  the only component that moves the POINT estimate -> the matched-
                  coverage efficiency win in selection-biased networks.
      C (gated)   if the design-by-treatment inconsistency test rejects (p <
                  incons_gate_p), inflate seTE by phi = sqrt(max(1, Q_inc/df_inc))
                  -> restores deployable coverage when direct/indirect conflict.

    The switch is data-driven: tau-hat & geometry drive A's per-comparison
    shrinkage, the asymmetry test gates B, the inconsistency test gates C. All
    gate decisions are returned in `fit.meta` for transparency.
    """
    comps = [c if isinstance(c, Comparison) else Comparison(*c) for c in comps]

    # ---- A: heterogeneity-structure shrinkage sets the RE weights -------------
    tau2_map = compute_shrunk_tau2(comps, nu=nu)
    fitA = fit_nma(comps, reference=reference, random=True, tau2_map=tau2_map)
    ref = fitA.reference
    fit_common = fit_nma(comps, reference=ref, random=True)

    info = {"nu": nu, "tau2_map": {tuple(sorted(k)): v for k, v in tau2_map.items()},
            "b_fired": False, "c_fired": False, "lambda_b": 0.0, "phi_c": 1.0}

    # ---- regime switch for the POINT-estimate base ---------------------------
    # B's win regime (selection in dense/well-powered nets) is DISJOINT from A's
    # (sparse heterogeneous-tau). On the homogeneous, data-rich networks where
    # selection bias is correctable, A's per-comparison tau^2 only injects
    # point-estimate noise. So when the asymmetry gate fires we de-bias the
    # field-default common-DL point; otherwise we keep A's calibrated league.
    asym = network_asymmetry(comps, reference=ref, tau2_map=None) if enable_b else None
    b_gate = enable_b and asym["p"] < asym_gate_p
    if b_gate:
        TE = fit_common.TE.copy()
        seTE = fit_common.seTE.copy()
    else:
        TE = fitA.TE.copy()
        seTE = fitA.seTE.copy()

    # ---- B: asymmetry-gated, SNR-shrunk small-study point correction ----------
    if b_gate:
        info["asym_p"] = asym["p"]
        info["asym_beta"] = asym["beta"]
        fitB = network_smallstudy_league(comps, reference=ref,
                                         kind=smallstudy_kind, tau2_map=None)
        beta = fitB.meta["beta"]
        var_beta = fitB.meta["var_beta"]
        lam = float(beta ** 2 / (beta ** 2 + var_beta)) if var_beta > _EPS else 0.0
        TE = (1.0 - lam) * TE + lam * fitB.TE
        seTE = (1.0 - lam) * seTE + lam * fitB.seTE
        info["b_fired"] = True
        info["lambda_b"] = lam
    elif enable_b:
        info["asym_p"] = asym["p"]
        info["asym_beta"] = asym["beta"]

    # ---- C: inconsistency-gated interval inflation ---------------------------
    if enable_c:
        inc = inconsistency_factor(comps, alpha_gate=incons_gate_p)
        info["inc_p"] = inc["p_inc"]
        info["df_inc"] = inc["df_inc"]
        if inc["fired"]:
            seTE = seTE * inc["phi"]
            info["c_fired"] = True
            info["phi_c"] = inc["phi"]

    fit = NMAFit(
        treatments=fitA.treatments, theta=fitA.theta, Lplus=fitA.Lplus,
        TE=TE, seTE=seTE, tau2=fitA.tau2, tau=fitA.tau, Q=fitA.Q, df_Q=fitA.df_Q,
        I2=fitA.I2, n=fitA.n, k=fitA.k, m=fitA.m, reference=ref, random=True,
        meta={"treatments": fitA.treatments, "tidx": fitA.meta["tidx"], **info},
    )
    return fit
