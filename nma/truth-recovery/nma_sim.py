"""nma_sim.py -- seeded network meta-analysis data generator for the bake-off.

Generates a network of pairwise comparisons with a known truth, spanning the
grid axes in DESIGN_BRIEF.md: geometry, n treatments, studies-per-comparison,
multi-arm fraction, heterogeneity (homogeneous vs heterogeneous-across-
comparisons), inconsistency, and small-study selection.

Truth-first: every quantity is a seeded draw; nothing hand-entered. The "truth"
returned is the vector of basic parameters d_true[t] = effect of treatment t vs
the reference (treatment 0), plus the per-type tau used.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # nma/
from nma_core import Comparison  # noqa: E402


def geometry_edges(geom: str, n: int) -> list[tuple[int, int]]:
    """Direct-comparison edge set for a given network geometry."""
    if geom == "star":
        return [(0, t) for t in range(1, n)]
    if geom == "line":
        return [(t, t + 1) for t in range(n - 1)]
    if geom == "loop":
        return [(t, t + 1) for t in range(n - 1)] + [(0, n - 1)]
    if geom == "full":
        return list(combinations(range(n), 2))
    raise ValueError(geom)


@dataclass
class NetSpec:
    geom: str = "loop"
    n: int = 6
    studies_per_comp: tuple[int, int] = (1, 2)   # sparse
    multiarm_frac: float = 0.0
    hetero: str = "heterogeneous"                 # 'homogeneous' | 'heterogeneous'
    tau_low: float = 0.05
    tau_high: float = 0.30
    tau_homog: float = 0.15
    inconsistency: float = 0.0                    # SD of design-specific bias
    selection: str = "none"                       # 'none' | 'moderate' | 'strong'
    effect_sd: float = 0.5                         # spread of true basic effects
    se_range: tuple[float, float] = (0.10, 0.45)


def _type_tau(spec: NetSpec, edges) -> dict[frozenset, float]:
    """Per-comparison-type tau (fixed property of the network)."""
    taus = {}
    for i, (a, b) in enumerate(edges):
        if spec.hetero == "homogeneous":
            taus[frozenset((a, b))] = spec.tau_homog
        else:
            # alternate low/high by edge index -> heterogeneous heterogeneity
            taus[frozenset((a, b))] = spec.tau_low if (i % 2 == 0) else spec.tau_high
    return taus


def _selection_keep(y, se, strength, rng):
    """Small-study/selective-reporting filter favouring large positive z."""
    if strength == "none":
        return True
    z = y / se
    from scipy.stats import norm
    p_one = norm.sf(z)  # one-sided p, small for large +z
    w = {"moderate": np.array([1.0, 0.6, 0.4]),
         "strong": np.array([1.0, 0.35, 0.10])}[strength]
    cuts = np.array([0.025, 0.05])
    idx = int(np.searchsorted(cuts, p_one, side="right"))
    return rng.uniform() < w[idx]


def generate(spec: NetSpec, seed: int):
    """Return (comparisons, d_true, type_tau).

    d_true is an (n,) vector with d_true[0]=0 (reference); d_true[t] is the true
    effect of t vs reference. Comparison TE convention: effect(t1) - effect(t2).
    """
    rng = np.random.default_rng(seed)
    n = spec.n
    edges = geometry_edges(spec.geom, n)
    type_tau = _type_tau(spec, edges)

    # true basic effects (reference = 0)
    d_true = np.concatenate([[0.0], rng.normal(0.0, spec.effect_sd, n - 1)])

    # design-specific inconsistency bias: a per-edge offset added to that edge's
    # direct studies only (breaks consistency when inconsistency > 0)
    incons = {frozenset(e): (rng.normal(0, spec.inconsistency) if spec.inconsistency > 0 else 0.0)
              for e in edges}

    comps: list[Comparison] = []
    sid = 0
    lo, hi = spec.studies_per_comp
    for (a, b) in edges:
        n_c = int(rng.integers(lo, hi + 1))
        typ = frozenset((a, b))
        tau = type_tau[typ]
        base = (d_true[a] - d_true[b]) + incons[typ]
        for _ in range(n_c):
            multi = (spec.multiarm_frac > 0 and rng.uniform() < spec.multiarm_frac
                     and n >= 3)
            if multi:
                # 3-arm study a,b,c' sharing arm a; generate arm-level then contrasts
                others = [t for t in range(n) if t not in (a, b)]
                cc = int(rng.choice(others))
                arms = [a, b, cc]
                # arm-level latent estimates with shared baseline noise
                sigma = rng.uniform(*spec.se_range)
                re = {t: rng.normal(0, tau) for t in arms}  # study RE per arm-effect
                m = {t: rng.normal(d_true[t] + re[t], sigma) for t in arms}
                se_arm = sigma
                for (x, yv) in combinations(arms, 2):
                    te = m[x] - m[yv]
                    se = np.sqrt(2.0) * se_arm
                    comps.append(Comparison(f"s{sid}", str(x), str(yv), float(te), float(se)))
                sid += 1
            else:
                delta = rng.normal(0, tau)
                se = float(rng.uniform(*spec.se_range))
                y = float(rng.normal(base + delta, se))
                if not _selection_keep(y, se, spec.selection, rng):
                    continue
                comps.append(Comparison(f"s{sid}", str(a), str(b), y, se))
                sid += 1

    return comps, d_true, type_tau
