"""dta_sim.py -- 2x2 table generator for the AdaptShrink-DTA bake-off.

Bivariate logit-normal data-generating process (the standard DTA simulation
model; same family Reitsma assumes, so any failure is identifiability/selection,
not gross misspecification):

  per study i:
    N_i  ~ study size (lognormal, floored)        -> small N => sparse/zero cells
    n1_i = round(prev * N_i)  (diseased),  n0_i = N_i - n1_i
    (u1_i, u2_i) ~ N( (M1, M2), Sigma )            Sigma = [[t1^2, rho t1 t2],
                                                            [rho t1 t2, t2^2]]
    se_i = expit(u1_i),  sp_i = expit(u2_i)
    TP_i ~ Binom(n1_i, se_i),  FN_i = n1_i - TP_i
    TN_i ~ Binom(n0_i, sp_i),  FP_i = n0_i - TN_i

Threshold heterogeneity is induced by rho < 0 (a higher implicit threshold raises
Sp while lowering Se). The TRUE target for coverage is the data-generating
summary operating point (M1, M2) = (logit Se, logit Sp).

Selection (Deeks-style small-study/SROC effect): publication probability rises
with the study's diagnostic odds ratio (lnDOR). Because small studies have
higher-variance lnDOR, this preferentially publishes small studies that happened
to look impressive -- the classic small-study effect on the SROC, which biases
the summary operating point UP the SROC. 'none' = no selection (negative
control).

Truth-first: fully seeded; the true (M1, M2) is returned alongside the selected
table so the bake-off scores error against the real generating point.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.special import expit, logit

BASE_SEED = 20260621


@dataclass
class DTASpec:
    se: float = 0.85          # target summary sensitivity
    sp: float = 0.85          # target summary specificity
    tau1: float = 0.5         # between-study SD of logit(Se)
    tau2: float = 0.5         # between-study SD of logit(Sp)
    rho: float = -0.4         # between-study correlation (neg = threshold het)
    k: int = 20               # number of studies (pre-selection draws)
    prev: float = 0.3         # disease prevalence (n1 / N)
    n_med: float = 120.0      # median study size (lognormal)
    n_sigma: float = 0.6      # lognormal sigma of study size (spread/sparsity)
    n_min: int = 20           # floor on study size

    @property
    def M(self) -> np.ndarray:
        return np.array([logit(self.se), logit(self.sp)])

    @property
    def Sigma(self) -> np.ndarray:
        c = self.rho * self.tau1 * self.tau2
        return np.array([[self.tau1 ** 2, c], [c, self.tau2 ** 2]])


# Selection strengths: g1 multiplies standardized lnDOR in the publication logit.
_SEL = {"none": None,
        "moderate": {"g0": 0.4, "g1": 0.8},
        "strong":   {"g0": 0.0, "g1": 1.6}}


def _draw_tables(rng: np.random.Generator, spec: DTASpec, k: int):
    """Draw k raw 2x2 tables from the bivariate logit-normal DGP."""
    M = spec.M
    Sigma = spec.Sigma
    uv = rng.multivariate_normal(M, Sigma, size=k)
    se = expit(uv[:, 0])
    sp = expit(uv[:, 1])
    N = np.maximum(np.round(rng.lognormal(np.log(spec.n_med), spec.n_sigma, k)),
                   spec.n_min).astype(int)
    n1 = np.maximum(np.round(spec.prev * N).astype(int), 1)
    n0 = np.maximum(N - n1, 1)
    tp = rng.binomial(n1, se)
    tn = rng.binomial(n0, sp)
    fn = n1 - tp
    fp = n0 - tn
    return tp, fp, fn, tn


def _lndor(tp, fp, fn, tn):
    """Continuity-corrected lnDOR for the selection model (not for the fit)."""
    a = tp + 0.5
    b = fp + 0.5
    c = fn + 0.5
    d = tn + 0.5
    return np.log((a * d) / (b * c))


def generate(spec: DTASpec, strength: str, seed: int):
    """Return (tp, fp, fn, tn, true_M) for a selected DTA meta-analysis.

    Draws are over-sampled and Deeks-selected down to >= min(k, 4) survivors so
    the post-selection count is comparable to the requested k across strengths.
    """
    rng = np.random.default_rng(seed)
    sel_cfg = _SEL[strength]
    need = max(min(spec.k, 6), 4)
    # Over-draw so that after selection we still have ~k studies.
    draw_k = spec.k if sel_cfg is None else int(np.ceil(spec.k * 2.2))

    for _ in range(60):
        tp, fp, fn, tn = _draw_tables(rng, spec, draw_k)
        if sel_cfg is None:
            sel = np.ones(draw_k, bool)
        else:
            ld = _lndor(tp, fp, fn, tn)
            z = (ld - ld.mean()) / max(ld.std(ddof=0), 1e-9)
            p = expit(sel_cfg["g0"] + sel_cfg["g1"] * z)
            sel = rng.uniform(size=draw_k) < p
        if sel.sum() >= need:
            # Trim to at most k survivors (keep the first k selected) so cell
            # size is comparable across strengths.
            idx = np.flatnonzero(sel)[: spec.k]
            return tp[idx], fp[idx], fn[idx], tn[idx], spec.M
        seed += 7919
        rng = np.random.default_rng(seed)

    # Fallback: no selection.
    tp, fp, fn, tn = _draw_tables(rng, spec, spec.k)
    return tp, fp, fn, tn, spec.M
