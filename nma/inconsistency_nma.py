"""inconsistency_nma.py -- Component C: inconsistency-aware interval inflation.

A consistency NMA (netmeta) assumes direct and indirect evidence agree. When they
disagree (design-by-treatment interaction), the consistency league reports
intervals that are too narrow for the true uncertainty -> deployable
under-coverage. Component C detects this with a generalized-Q decomposition and
inflates the league intervals by a gated multiplicative dispersion factor, the
structural analog of the univariate AdaptShrink "widen when members disagree".

Q decomposition (White 2012 / Jackson generalized form)
-------------------------------------------------------
The generalized Cochran Q of the consistency common-effect fit splits into

    Q_total = Q_het (within-design heterogeneity) + Q_inc (between-design
              inconsistency),       df_inc = df_total - df_het

where the within-design part is obtained by a *design-saturated* fit (each design
-- the set of treatments compared in a study -- is pooled on its own), so Q_het
is the pure replication scatter and Q_inc is the direct-vs-indirect conflict. For
an all-2-arm network df_inc = (#edges) - (n-1) = the number of independent loops
(inconsistency is only estimable around loops; a star has df_inc = 0). The
construction is multi-arm-safe (designs pooled with the engine's exact block
weights).

The gated inflation
-------------------
    phi = sqrt(max(1, Q_inc / df_inc))   if the design-by-treatment chi^2 test
                                          rejects (p < alpha_gate) and df_inc > 0
    phi = 1                               otherwise (consistent network -> no harm)

seTE_inflated = phi * seTE. Honest ceiling (nma/REPORT_NMA_BAKEOFF.md): in
networks with several independent loops phi restores deployable coverage to
near-nominal; in single-loop sparse networks it substantially improves but does
not fully reach nominal, because one contradicted loop is a large structured bias
that symmetric widening (and a 1-df detection) can only partly cover.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np
from scipy.stats import chi2

from nma_core import Comparison, _assemble, _dl_tau2, _generalized_Q

_EPS = 1e-12


def _subset_Q(sub: list[Comparison], tau2: float = 0.0) -> tuple[float, int]:
    """Generalized Q and its df for a subset of comparison rows.

    With tau2 > 0 the weights are the random-effects block precisions (variance
    inflated by the network tau^2), so that genuine heterogeneity does NOT
    masquerade as inconsistency -- the design-by-treatment test is performed in
    the RE framework (Krahn 2013), which keeps the null Q_inc ~ chi^2(df_inc).
    """
    treats = sorted({c.t1 for c in sub} | {c.t2 for c in sub})
    tidx = {t: i for i, t in enumerate(treats)}
    n = len(treats)
    B, W, y, _ = _assemble(sub, tidx, n, tau2=tau2)
    L = B.T @ W @ B
    Lp = np.linalg.pinv(L, rcond=1e-12)
    Q, _ = _generalized_Q(B, W, y, Lp)
    by_study: dict[str, set] = {}
    for c in sub:
        by_study.setdefault(c.studlab, set()).update([c.t1, c.t2])
    indep = sum(len(a) - 1 for a in by_study.values())
    df = max(indep - (n - 1), 0)
    return Q, df


def q_decomposition(comps: Sequence[Comparison] | Sequence[tuple]) -> dict:
    """Split the consistency-model generalized Q into heterogeneity + inconsistency.

    Q_het is the sum of within-design generalized Q over designs (each design =
    studies sharing the same treatment set, pooled on their own); Q_inc is the
    residual between-design conflict. The decomposition is done at random-effects
    weights (the network generalized-DL tau^2) so heterogeneity is not mistaken
    for inconsistency.
    """
    comps = [c if isinstance(c, Comparison) else Comparison(*c) for c in comps]
    # network generalized-DL tau^2 for the RE weights
    treats = sorted({c.t1 for c in comps} | {c.t2 for c in comps})
    tidx = {t: i for i, t in enumerate(treats)}
    n = len(treats)
    by_study: dict[str, set] = {}
    for c in comps:
        by_study.setdefault(c.studlab, set()).update([c.t1, c.t2])
    indep = sum(len(a) - 1 for a in by_study.values())
    df_net = max(indep - (n - 1), 0)
    tau2, _, _ = _dl_tau2(comps, tidx, n, df_net)

    Q_total, df_total = _subset_Q(comps, tau2=tau2)

    # group studies by design (the set of treatments compared in that study)
    studies: dict[str, list[Comparison]] = {}
    for c in comps:
        studies.setdefault(c.studlab, []).append(c)
    designs: dict[frozenset, list[Comparison]] = {}
    for rows in studies.values():
        d = frozenset({c.t1 for c in rows} | {c.t2 for c in rows})
        designs.setdefault(d, []).extend(rows)

    Q_het = 0.0
    df_het = 0
    for rows in designs.values():
        # within-design replication only exists when a design has >1 study
        if len({c.studlab for c in rows}) < 2:
            continue
        Qd, dfd = _subset_Q(rows, tau2=tau2)
        Q_het += Qd
        df_het += dfd

    Q_inc = max(Q_total - Q_het, 0.0)
    df_inc = max(df_total - df_het, 0)
    p_inc = float(chi2.sf(Q_inc, df_inc)) if df_inc > 0 else 1.0
    return {"Q_total": float(Q_total), "df_total": int(df_total),
            "Q_het": float(Q_het), "df_het": int(df_het),
            "Q_inc": float(Q_inc), "df_inc": int(df_inc), "p_inc": p_inc}


def inconsistency_factor(comps: Sequence[Comparison] | Sequence[tuple],
                         alpha_gate: float = 0.10) -> dict:
    """Gated multiplicative interval-inflation factor phi for inconsistency.

    phi = sqrt(max(1, Q_inc/df_inc)) when the design-by-treatment chi^2 test
    rejects at alpha_gate and df_inc > 0; phi = 1 otherwise.
    """
    d = q_decomposition(comps)
    fire = d["df_inc"] > 0 and d["p_inc"] < alpha_gate
    if fire:
        phi = float(np.sqrt(max(1.0, d["Q_inc"] / d["df_inc"])))
    else:
        phi = 1.0
    d["fired"] = bool(fire)
    d["phi"] = phi
    return d
