"""nma_core.py -- frequentist graph-theoretic network meta-analysis.

A from-scratch implementation of the Ruecker (2012) electrical-network / graph-
theoretic NMA estimator, the engine behind R's `netmeta`. It is the modern
contrast-based frequentist field we must validate against and then beat.

Why this construction (and not a naive per-comparison GLS):
  * Multi-arm studies contribute correlated pairwise contrasts. netmeta handles
    this by reconstructing, within each study, the arm-level variances from the
    observed pairwise variances (assuming within-study consistency), forming the
    full contrast covariance V_block, and using its Moore-Penrose pseudoinverse
    as the study weight block. This is the "reduce weights" approach of
    Ruecker & Schwarzer (2014) and is what gives netmeta-exact answers.
  * Random effects add a common heterogeneity tau^2 with the correct multi-arm
    structure: tau^2 on the diagonal, tau^2/2 for contrasts sharing an arm
    (the shared-control rule). Equivalently each block's per-arm variance gets
    + tau^2/2 before forming V_block -- which reproduces v_e + tau^2 for 2-arm
    comparisons and the tau^2/2 off-diagonal for multi-arm ones.

Verified to ~1e-6 against netmeta 3.6-1 on Senn2013 (multi-arm diabetes) and the
Hasselblad smoking-cessation network -- see nma/reference/test_netmeta_parity.py.

Conventions
-----------
A comparison row (treat1, treat2, TE, seTE) means TE = effect(treat1) -
effect(treat2), matching netmeta. Treatment "potentials" theta are centered
(sum to zero up to the pseudoinverse); reported league entries are differences
theta_t - theta_u, which are invariant to the centering.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Sequence

import numpy as np

_EPS = 1e-12


@dataclass
class Comparison:
    studlab: str
    t1: str
    t2: str
    te: float
    se: float


@dataclass
class NMAFit:
    treatments: list[str]
    theta: np.ndarray            # treatment potentials (n,), centered
    Lplus: np.ndarray            # pseudoinverse of weighted Laplacian (n,n)
    TE: np.ndarray               # n x n league of differences theta_t - theta_u
    seTE: np.ndarray             # n x n standard errors
    tau2: float
    tau: float
    Q: float
    df_Q: int
    I2: float
    n: int                       # n treatments
    k: int                       # k studies
    m: int                       # m comparisons (rows)
    reference: str
    random: bool
    meta: dict = field(default_factory=dict)


def _study_blocks(comps: Sequence[Comparison], tidx: dict[str, int]):
    """Group comparisons by study; return per-study (rows, global_idx, A, v).

    rows         : indices into the global comparison list
    arms         : local treatment labels in this study
    A            : (c x p) signed incidence of comparisons -> local arms
    v            : (c,) observed contrast variances (seTE^2)
    g1, g2       : (c,) global treatment indices for t1, t2 of each comparison
    """
    by_study: dict[str, list[int]] = {}
    for i, c in enumerate(comps):
        by_study.setdefault(c.studlab, []).append(i)

    blocks = []
    for studlab, rows in by_study.items():
        sub = [comps[i] for i in rows]
        arms = sorted({c.t1 for c in sub} | {c.t2 for c in sub})
        aidx = {t: j for j, t in enumerate(arms)}
        c_n = len(sub)
        p = len(arms)
        A = np.zeros((c_n, p))
        v = np.empty(c_n)
        g1 = np.empty(c_n, dtype=int)
        g2 = np.empty(c_n, dtype=int)
        for r, c in enumerate(sub):
            A[r, aidx[c.t1]] = 1.0
            A[r, aidx[c.t2]] = -1.0
            v[r] = c.se ** 2
            g1[r] = tidx[c.t1]
            g2[r] = tidx[c.t2]
        types = [(c.t1, c.t2) for c in sub]
        blocks.append({"studlab": studlab, "rows": rows, "arms": arms,
                       "A": A, "v": v, "g1": g1, "g2": g2, "p": p,
                       "types": types})
    return blocks


def _arm_variances(A: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Reconstruct per-arm variances sigma^2 from pairwise contrast variances.

    v_e = sigma^2_{t1} + sigma^2_{t2}; with |A| the 0/1 incidence this is the
    linear system v = |A| sigma^2, solved by least squares (exact for a
    consistent multi-arm study).
    """
    absA = np.abs(A)
    sig2, *_ = np.linalg.lstsq(absA, v, rcond=None)
    return sig2


def _block_tau2(blk: dict, tau2: float, tau2_map: dict | None) -> np.ndarray:
    """Per-comparison tau^2 for a study block (length c).

    Scalar `tau2` unless `tau2_map` (frozenset({t1,t2}) -> tau^2_c) is given, in
    which case each comparison uses its type-specific heterogeneity. Comparisons
    with no entry fall back to the scalar.
    """
    c_n = len(blk["v"])
    if tau2_map is None:
        return np.full(c_n, tau2)
    out = np.empty(c_n)
    for r, (a, b) in enumerate(blk["types"]):
        out[r] = tau2_map.get(frozenset((a, b)), tau2)
    return out


def _weight_block(blk: dict, tau2: float, tau2_map: dict | None = None) -> np.ndarray:
    """Study weight block = pinv(V_block).

    2-arm: V = [[v + tau^2]], W = 1/(v+tau^2).
    multi-arm: reconstruct arm variances, V = A diag(sigma^2 + tau^2/2) A',
               W = Moore-Penrose pseudoinverse of V.
    With comparison-specific tau^2 (tau2_map), the 2-arm comparison uses its own
    tau^2_c exactly; a multi-arm block uses the mean of its comparisons' tau^2_c
    with the shared-arm 0.5 A A' structure (keeps the block PSD and reduces to the
    homogeneous case when all tau^2_c are equal -- documented in DESIGN_BRIEF.md).
    """
    A, v, p = blk["A"], blk["v"], blk["p"]
    t2 = _block_tau2(blk, tau2, tau2_map)
    if p == 2:
        return np.array([[1.0 / (v[0] + t2[0])]])
    sig2 = _arm_variances(A, v)
    d = sig2 + 0.5 * float(np.mean(t2))
    V = A @ np.diag(d) @ A.T
    return np.linalg.pinv(V, rcond=1e-12)


def _assemble(comps, tidx, n, tau2, with_S: bool = False, tau2_map: dict | None = None):
    """Build global incidence B (m x n), block-diagonal W (m x m), y (m,).

    If `with_S`, also return S = block-diag(0.5 A A') = dV/dtau^2, the structure
    matrix used by the Jackson (2012) generalized DerSimonian-Laird estimator.
    `tau2_map` (frozenset({t1,t2}) -> tau^2_c) enables comparison-specific
    heterogeneity (used by AdaptShrink-NMA); None keeps the scalar tau^2 path
    that is verified netmeta-identical.
    """
    m = len(comps)
    B = np.zeros((m, n))
    W = np.zeros((m, m))
    S = np.zeros((m, m)) if with_S else None
    y = np.array([c.te for c in comps], dtype=float)
    blocks = _study_blocks(comps, tidx)
    for blk in blocks:
        rows = blk["rows"]
        for r, gi in zip(rows, blk["g1"]):
            B[r, gi] += 1.0
        for r, gi in zip(rows, blk["g2"]):
            B[r, gi] += -1.0
        Wb = _weight_block(blk, tau2, tau2_map)
        ri = np.array(rows)
        W[np.ix_(ri, ri)] = Wb
        if with_S:
            A = blk["A"]
            S[np.ix_(ri, ri)] = 0.5 * (A @ A.T)
    if with_S:
        return B, W, y, blocks, S
    return B, W, y, blocks


def _league(theta, Lplus, treatments):
    n = len(treatments)
    TE = np.zeros((n, n))
    seTE = np.zeros((n, n))
    diagL = np.diag(Lplus)
    for a in range(n):
        for b in range(n):
            TE[a, b] = theta[a] - theta[b]
            var = diagL[a] + diagL[b] - 2.0 * Lplus[a, b]
            seTE[a, b] = np.sqrt(max(var, 0.0))
    return TE, seTE


def _generalized_Q(B, W, y, Lplus):
    """Generalized Cochran Q from the common-effect fit (tau^2 = 0 weights)."""
    BtWy = B.T @ (W @ y)
    theta = Lplus @ BtWy
    Q = float(y @ (W @ y) - theta @ (B.T @ (W @ B)) @ theta)
    return max(Q, 0.0), theta


def _dl_tau2(comps, tidx, n, df_Q):
    """Generalized DerSimonian-Laird tau^2 (netmeta default, method.tau='DL').

    tau^2 = max(0, (Q - df) / C),  C = tr(W S) - tr(Lplus B' W S W B),
    where S = dV/dtau^2 is block-diagonal 0.5 A A' (the multi-arm random-effects
    structure). All evaluated at the common-effect (tau^2 = 0) weights. For a
    pure 2-arm network S = I and this reduces to the classic DL constant
    sum(w) - tr((X'WX)^-1 X'W^2 X); the S term is what makes it netmeta-exact on
    multi-arm networks (verified to ~1e-7).
    """
    B, W, y, _, S = _assemble(comps, tidx, n, tau2=0.0, with_S=True)
    L = B.T @ W @ B
    Lplus = np.linalg.pinv(L, rcond=1e-12)
    Q, _ = _generalized_Q(B, W, y, Lplus)
    WSW = W @ S @ W
    C = float(np.trace(W @ S) - np.trace(Lplus @ (B.T @ WSW @ B)))
    tau2 = max(0.0, (Q - df_Q) / C) if C > _EPS else 0.0
    return tau2, Q, C


def fit_nma(comparisons: Sequence[Comparison] | Sequence[tuple],
            reference: str | None = None,
            random: bool = True,
            tau2: float | None = None,
            tau2_map: dict | None = None) -> NMAFit:
    """Fit a graph-theoretic NMA.

    Parameters
    ----------
    comparisons : sequence of Comparison or (studlab, t1, t2, te, se) tuples.
    reference   : reference treatment (default: first alphabetically).
    random      : random-effects (True) or common-effect (False) model.
    tau2        : if given, use this tau^2 instead of estimating (used to feed
                  netmeta's tau^2 for engine-only parity, and by the bake-off).
    """
    comps = [c if isinstance(c, Comparison) else Comparison(*c) for c in comparisons]
    treatments = sorted({c.t1 for c in comps} | {c.t2 for c in comps})
    n = len(treatments)
    tidx = {t: i for i, t in enumerate(treatments)}
    if reference is None:
        reference = treatments[0]

    # Effective degrees of freedom for Q: independent comparisons - (n - 1).
    # Independent comparisons = sum over studies of (arms - 1).
    by_study: dict[str, set] = {}
    for c in comps:
        by_study.setdefault(c.studlab, set()).update([c.t1, c.t2])
    k = len(by_study)
    indep = sum(len(arms) - 1 for arms in by_study.values())
    df_Q = max(indep - (n - 1), 0)

    if tau2 is None:
        if random:
            tau2_est, Q, _ = _dl_tau2(comps, tidx, n, df_Q)
        else:
            tau2_est = 0.0
    else:
        tau2_est = float(tau2)

    use_tau2 = tau2_est if random else 0.0
    use_map = tau2_map if (random and tau2_map is not None) else None
    B, W, y, blocks = _assemble(comps, tidx, n, tau2=use_tau2, tau2_map=use_map)
    L = B.T @ W @ B
    Lplus = np.linalg.pinv(L, rcond=1e-12)
    theta = Lplus @ (B.T @ (W @ y))
    TE, seTE = _league(theta, Lplus, treatments)

    # Q and I^2 always reported from the common-effect fit (netmeta convention).
    B0, W0, y0, _ = _assemble(comps, tidx, n, tau2=0.0)
    L0 = B0.T @ W0 @ B0
    L0plus = np.linalg.pinv(L0, rcond=1e-12)
    Q, _ = _generalized_Q(B0, W0, y0, L0plus)
    I2 = max(0.0, (Q - df_Q) / Q) if Q > _EPS else 0.0

    return NMAFit(
        treatments=treatments, theta=theta, Lplus=Lplus, TE=TE, seTE=seTE,
        tau2=float(use_tau2), tau=float(np.sqrt(use_tau2)), Q=float(Q),
        df_Q=int(df_Q), I2=float(I2), n=n, k=k, m=len(comps),
        reference=reference, random=random,
        meta={"treatments": treatments, "tidx": tidx},
    )


def p_score(fit: NMAFit, small_values: str = "desirable") -> dict[str, float]:
    """Frequentist P-score (Ruecker & Schwarzer 2015) -- the netmeta SUCRA analog.

    For each treatment, the mean over all other treatments of the one-sided
    probability that it is better, using the normal approximation
    P(t better than u) = Phi(sign * (TE[t,u]) / seTE[t,u]).
    `small_values='desirable'` means smaller effects are better (e.g. MD of
    HbA1c); 'undesirable' means larger is better (e.g. log-OR of cessation).
    """
    from scipy.stats import norm
    treatments = fit.treatments
    n = fit.n
    sign = 1.0 if small_values == "undesirable" else -1.0
    P = np.zeros((n, n))
    for a in range(n):
        for b in range(n):
            if a == b:
                continue
            se = fit.seTE[a, b]
            if se <= _EPS:
                P[a, b] = 0.5
            else:
                P[a, b] = norm.cdf(sign * fit.TE[a, b] / se)
    pscore = {treatments[a]: float(np.sum(P[a, :]) / (n - 1)) for a in range(n)}
    return pscore
