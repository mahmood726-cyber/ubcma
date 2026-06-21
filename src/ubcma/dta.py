"""AdaptShrink-DTA: selection- and small-sample-robust diagnostic test accuracy
meta-analysis.

This module generalizes the univariate AdaptShrink program (``adaptshrink.py``)
to the **bivariate** DTA setting. Each study contributes a 2x2 table
(TP, FP, FN, TN); on the logit scale it contributes

    y1 = logit(Se),  y2 = logit(Sp)

with within-study variances ``s1^2 = 1/TP + 1/FN``, ``s2^2 = 1/TN + 1/FP`` and
**zero within-study covariance** (the diseased and non-diseased patient groups
are independent). The bivariate random-effects (Reitsma / van Houwelingen) model
treats the marginal of each study as

    (y1_i, y2_i) ~ N( M , Sigma + S_i ),   S_i = diag(s1_i^2, s2_i^2)

and estimates the summary operating point ``M = (M1, M2)`` together with the
between-study covariance ``Sigma = [[t1^2, rho t1 t2],[rho t1 t2, t2^2]]``.

Estimators provided
-------------------
* ``reitsma`` -- ML of the bivariate normal-normal model (the field-to-beat;
  validated against ``mada::reitsma`` and ``metafor::rma.mv``).
* ``reitsma_reml`` -- the same model fit by REML (small-sample-corrected variant).
* ``reitsma_indep`` -- the same with ``rho`` fixed at 0 (Riley-style small-k
  stabilizer / separate-variances bivariate).
* ``hsroc`` -- the Rutter-Gatsonis HSROC model (the second standard DTA model),
  the bivariate GLMM fit by the exact binomial likelihood via adaptive
  Gauss-Hermite quadrature (validated against ``lme4::glmer``).
* ``sep_univariate`` -- pool logit-Se and logit-Sp independently (naive lower
  bound).
* ``adaptshrink_dta`` -- the new estimator: adaptive shrinkage of ``Sigma``
  toward independence with a ``k``/condition-gated intensity ``delta``, plus an
  optional Deeks-asymmetry-gated SROC selection correction. Reduces to
  ``reitsma`` when ``delta=0`` and no asymmetry is detected.

Region utilities (for the matched-coverage bake-off)
----------------------------------------------------
The summary point has GLS covariance ``V = (sum_i (Sigma + S_i)^{-1})^{-1}``; the
``(1-alpha)`` confidence region is the ellipse ``{e: e' V^{-1} e <= chi2_{2,1-a}}``
with **area = pi * chi2_{2,1-a} * sqrt(det V)``. ``ellipse_area`` and
``in_region`` expose this for the area-based MCIW0-2D criterion.

Truth-first: every default constant (the shrinkage gate ``kappa0, b, delta_max,
C``, the Deeks gate ``p_gate``) is fixed a priori and reported in the result
dict; nothing is tuned to a simulation target.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import minimize
from scipy.stats import chi2, norm

_EPS = 1e-12

# 97.5% standard-normal quantile (two-sided 95% univariate interval).
Z975 = 1.959963984540054

# --- AdaptShrink-DTA a-priori constants (NOT tuned to any target) ---
AS_KAPPA0 = 8.0      # small-k shrinkage curvature: delta_k = kappa0/(kappa0+(k-3))
AS_BOUNDARY_BOOST = 0.25   # extra shrink when rho-hat is on the boundary / ill-cond
AS_SELECTION_BOOST = 0.35  # extra shrink when Deeks funnel asymmetry is detected
AS_DELTA_MAX = 0.9         # cap on total shrinkage intensity
AS_COND_MAX = 1e3          # condition-number threshold flagging an unstable Sigma
AS_RHO_BOUNDARY = 0.95     # |rho-hat| at/above this is treated as a boundary hit
AS_DEEKS_PGATE = 0.10      # Deeks asymmetry p-value gate for the selection correction


# ---------------------------------------------------------------------------
# 2x2 table -> logit-scale study data
# ---------------------------------------------------------------------------
@dataclass
class DTAStudies:
    """Per-study logit-scale data for a DTA meta-analysis.

    Attributes
    ----------
    y1, y2 : logit(Se), logit(Sp) per study, shape (k,).
    s1sq, s2sq : within-study variances of y1, y2, shape (k,).
    tp, fp, fn, tn : raw 2x2 counts (post continuity-correction), shape (k,).
    """
    y1: np.ndarray
    y2: np.ndarray
    s1sq: np.ndarray
    s2sq: np.ndarray
    tp: np.ndarray
    fp: np.ndarray
    fn: np.ndarray
    tn: np.ndarray

    @property
    def k(self) -> int:
        return int(len(self.y1))


def from_counts(
    tp: np.ndarray,
    fp: np.ndarray,
    fn: np.ndarray,
    tn: np.ndarray,
    cc: float = 0.5,
    correction_control: str = "all",
) -> DTAStudies:
    """Build logit-scale study data from raw 2x2 counts.

    Continuity correction (mirrors ``mada::reitsma`` defaults ``correction=0.5``,
    ``correction.control="all"``):

    * ``"all"``    -- if ANY study has a zero cell, add ``cc`` to EVERY cell of
      EVERY study (the mada default).
    * ``"single"`` -- add ``cc`` only to the cells of studies that have a zero.
    * ``"none"``   -- no correction.
    """
    tp = np.asarray(tp, float)
    fp = np.asarray(fp, float)
    fn = np.asarray(fn, float)
    tn = np.asarray(tn, float)
    any_zero = bool(np.any((tp == 0) | (fp == 0) | (fn == 0) | (tn == 0)))
    if correction_control == "all":
        need = np.ones(len(tp), bool) if any_zero else np.zeros(len(tp), bool)
    elif correction_control == "single":
        need = (tp == 0) | (fp == 0) | (fn == 0) | (tn == 0)
    elif correction_control == "none":
        need = np.zeros(len(tp), bool)
    else:
        raise ValueError(f"unknown correction_control: {correction_control}")
    tp = tp + need * cc
    fp = fp + need * cc
    fn = fn + need * cc
    tn = tn + need * cc

    se = tp / (tp + fn)
    sp = tn / (tn + fp)
    y1 = np.log(se / (1.0 - se))
    y2 = np.log(sp / (1.0 - sp))
    # Var(logit p_hat) by the delta method with counts a,b: 1/a + 1/b.
    s1sq = 1.0 / tp + 1.0 / fn
    s2sq = 1.0 / tn + 1.0 / fp
    return DTAStudies(y1, y2, s1sq, s2sq, tp, fp, fn, tn)


# ---------------------------------------------------------------------------
# Bivariate normal-normal model: likelihood, GLS point, GLS covariance
# ---------------------------------------------------------------------------
def _sigma_from_params(log_t1: float, log_t2: float, z_rho: float) -> np.ndarray:
    """Build Sigma from unconstrained params (log sds, fisher-z of rho)."""
    t1 = np.exp(log_t1)
    t2 = np.exp(log_t2)
    rho = np.tanh(z_rho)
    cov = rho * t1 * t2
    return np.array([[t1 * t1, cov], [cov, t2 * t2]])


def _accumulate(Sigma: np.ndarray, Y: np.ndarray, S: np.ndarray):
    """Vectorized GLS accumulators for the bivariate normal-normal model.

    Every per-study marginal precision is the inverse of the 2x2
    ``Vi = Sigma + S_i`` (``S_i`` diagonal), computed analytically:
        Vi = [[a_i, b], [b, c_i]],  det_i = a_i c_i - b^2,
        Wi = (1/det_i) [[c_i, -b], [-b, a_i]].
    Returns ``(A, rhs, logdet_sum, quad_sum, ok)`` where ``A = sum Wi`` (2x2),
    ``rhs = sum Wi y_i`` (2,), ``quad_sum = sum y_i' Wi y_i``. ``ok`` is False if
    any ``Vi`` is not positive-definite.
    """
    s11, s12, s22 = Sigma[0, 0], Sigma[0, 1], Sigma[1, 1]
    y1 = Y[:, 0]
    y2 = Y[:, 1]
    a = s11 + S[:, 0, 0]              # (k,)
    c = s22 + S[:, 1, 1]             # (k,)  (S off-diagonal is 0)
    b = s12                          # scalar (constant across studies)
    det = a * c - b * b
    if np.any(det <= 0) or np.any(~np.isfinite(det)):
        return None, None, None, None, False
    inv = 1.0 / det
    # Wi entries
    w11 = c * inv
    w22 = a * inv
    w12 = -b * inv
    A = np.array([[w11.sum(), w12.sum()], [w12.sum(), w22.sum()]])
    rhs = np.array([(w11 * y1 + w12 * y2).sum(),
                    (w12 * y1 + w22 * y2).sum()])
    quad_sum = float((w11 * y1 * y1 + 2.0 * w12 * y1 * y2 + w22 * y2 * y2).sum())
    logdet_sum = float(np.log(det).sum())
    return A, rhs, logdet_sum, quad_sum, True


def _neg_loglik(params: np.ndarray, Y: np.ndarray, S: np.ndarray,
                fix_rho0: bool, reml: bool = False) -> float:
    """Profile -2*loglik/2 over (M1,M2) given Sigma params (GLS-concentrated ML).

    With ``reml=True`` add the restricted-likelihood correction ``+0.5*log det A``
    (``A = sum_i W_i`` is the GLS precision of the summary point). For the
    bivariate location model whose per-study design is the identity this is the
    exact REML penalty; it removes the downward small-sample bias of the
    between-study variance components -- the standard small-sample correction.
    """
    log_t1, log_t2 = params[0], params[1]
    z_rho = 0.0 if fix_rho0 else params[2]
    Sigma = _sigma_from_params(log_t1, log_t2, z_rho)
    A, rhs, logdet_sum, quad_sum, ok = _accumulate(Sigma, Y, S)
    if not ok:
        return 1e12
    detA = A[0, 0] * A[1, 1] - A[0, 1] ** 2
    if detA <= 0 or not np.isfinite(detA):
        return 1e12
    M = np.array([A[1, 1] * rhs[0] - A[0, 1] * rhs[1],
                  -A[0, 1] * rhs[0] + A[0, 0] * rhs[1]]) / detA
    quad = quad_sum - rhs @ M
    nll = 0.5 * (logdet_sum + quad)
    if reml:
        nll += 0.5 * np.log(detA)
    return nll


def _gls_point_cov(Y: np.ndarray, S: np.ndarray, Sigma: np.ndarray):
    """Return (M, V) GLS summary point and its covariance for a fixed Sigma."""
    A, rhs, _, _, ok = _accumulate(Sigma, Y, S)
    if not ok:
        raise np.linalg.LinAlgError("non-PD marginal covariance")
    V = np.linalg.inv(A)
    M = V @ rhs
    return M, V


def _fit_sigma(Y: np.ndarray, S: np.ndarray, fix_rho0: bool, reml: bool = False):
    """ML- (or REML-) fit Sigma; return (Sigma, converged). Multi-start."""
    # Moment start: between-study var ~ max(var(y) - mean(s^2), small).
    v1 = max(np.var(Y[:, 0], ddof=1) - np.mean(S[:, 0, 0]), 1e-3)
    v2 = max(np.var(Y[:, 1], ddof=1) - np.mean(S[:, 1, 1]), 1e-3)
    starts = [
        np.array([0.5 * np.log(v1), 0.5 * np.log(v2), 0.0]),
        np.array([np.log(0.3), np.log(0.3), 0.0]),
        np.array([np.log(0.6), np.log(0.6), np.arctanh(-0.4)]),
    ]
    p0_dim = 2 if fix_rho0 else 3
    best = None
    for s0 in starts:
        x0 = s0[:p0_dim]
        try:
            res = minimize(_neg_loglik, x0, args=(Y, S, fix_rho0, reml),
                           method="Nelder-Mead",
                           options={"xatol": 1e-7, "fatol": 1e-9, "maxiter": 4000})
        except Exception:
            continue
        if best is None or (res.fun < best.fun):
            best = res
    if best is None:
        return None, False
    log_t1, log_t2 = best.x[0], best.x[1]
    z_rho = 0.0 if fix_rho0 else best.x[2]
    Sigma = _sigma_from_params(log_t1, log_t2, z_rho)
    return Sigma, bool(best.success or best.fun < 1e11)


def _stack(studies: DTAStudies):
    Y = np.column_stack([studies.y1, studies.y2])
    k = studies.k
    S = np.zeros((k, 2, 2))
    S[:, 0, 0] = studies.s1sq
    S[:, 1, 1] = studies.s2sq
    return Y, S


def _summarize(M: np.ndarray, V: np.ndarray, Sigma: np.ndarray,
               alpha: float, extra: dict | None = None) -> dict:
    """Pack a result dict: logit point, back-transformed Se/Sp, region, CIs."""
    se_sum = float(1.0 / (1.0 + np.exp(-M[0])))
    sp_sum = float(1.0 / (1.0 + np.exp(-M[1])))
    z = norm.ppf(1.0 - alpha / 2.0)
    # marginal logit CIs -> back-transform
    se_lo = float(1.0 / (1.0 + np.exp(-(M[0] - z * np.sqrt(V[0, 0])))))
    se_hi = float(1.0 / (1.0 + np.exp(-(M[0] + z * np.sqrt(V[0, 0])))))
    sp_lo = float(1.0 / (1.0 + np.exp(-(M[1] - z * np.sqrt(V[1, 1])))))
    sp_hi = float(1.0 / (1.0 + np.exp(-(M[1] + z * np.sqrt(V[1, 1])))))
    out = {
        "M1": float(M[0]), "M2": float(M[1]),
        "se_summary": se_sum, "sp_summary": sp_sum,
        "V": V.tolist(), "Sigma": Sigma.tolist(),
        "se_ci": (se_lo, se_hi), "sp_ci": (sp_lo, sp_hi),
        "region_area": float(ellipse_area(V, alpha)),
        "converged": True,
        "tau1": float(np.sqrt(max(Sigma[0, 0], 0.0))),
        "tau2": float(np.sqrt(max(Sigma[1, 1], 0.0))),
        "rho": float(Sigma[0, 1] / np.sqrt(max(Sigma[0, 0] * Sigma[1, 1], _EPS))),
    }
    if extra:
        out.update(extra)
    return out


def _fail() -> dict:
    return {"M1": float("nan"), "M2": float("nan"),
            "se_summary": float("nan"), "sp_summary": float("nan"),
            "V": None, "Sigma": None, "region_area": float("nan"),
            "converged": False}


# ---------------------------------------------------------------------------
# Region utilities
# ---------------------------------------------------------------------------
def ellipse_area(V: np.ndarray, alpha: float = 0.05) -> float:
    """Area of the (1-alpha) confidence ellipse {e: e' V^{-1} e <= chi2_{2,1-a}}.

    Area = pi * c * sqrt(det V) with c = chi2_{2,1-alpha}.
    """
    V = np.asarray(V, float)
    det = np.linalg.det(V)
    if not np.isfinite(det) or det <= 0:
        return float("nan")
    c = chi2.ppf(1.0 - alpha, df=2)
    return float(np.pi * c * np.sqrt(det))


def in_region(e: np.ndarray, V: np.ndarray, scale: float = 1.0,
              alpha: float = 0.05) -> bool:
    """Is error vector e inside the (scaled) (1-alpha) ellipse of covariance V?"""
    V = np.asarray(V, float) * scale
    try:
        Vinv = np.linalg.inv(V)
    except np.linalg.LinAlgError:
        return False
    c = chi2.ppf(1.0 - alpha, df=2)
    d2 = float(e @ Vinv @ e)
    return d2 <= c


# ---------------------------------------------------------------------------
# Estimators
# ---------------------------------------------------------------------------
def reitsma(studies: DTAStudies, alpha: float = 0.05) -> dict:
    """Bivariate random-effects ML (Reitsma / van Houwelingen). Field-to-beat."""
    Y, S = _stack(studies)
    if studies.k < 2:
        return _fail()
    Sigma, ok = _fit_sigma(Y, S, fix_rho0=False)
    if not ok or Sigma is None:
        return _fail()
    try:
        M, V = _gls_point_cov(Y, S, Sigma)
    except np.linalg.LinAlgError:
        return _fail()
    return _summarize(M, V, Sigma, alpha, {"method": "reitsma"})


def reitsma_reml(studies: DTAStudies, alpha: float = 0.05) -> dict:
    """Bivariate random-effects fit by REML (small-sample-corrected variant).

    Same model as ``reitsma`` but the between-study covariance is estimated by
    restricted maximum likelihood, which corrects the downward small-sample bias
    of the ML variance components. This is the recognised small-sample-corrected
    bivariate comparator (the DTA analogue of REML-vs-ML in standard MA).
    """
    Y, S = _stack(studies)
    if studies.k < 2:
        return _fail()
    Sigma, ok = _fit_sigma(Y, S, fix_rho0=False, reml=True)
    if not ok or Sigma is None:
        return _fail()
    try:
        M, V = _gls_point_cov(Y, S, Sigma)
    except np.linalg.LinAlgError:
        return _fail()
    return _summarize(M, V, Sigma, alpha, {"method": "reitsma_reml"})


def reitsma_indep(studies: DTAStudies, alpha: float = 0.05) -> dict:
    """Bivariate model with rho fixed at 0 (Riley-style small-k stabilizer)."""
    Y, S = _stack(studies)
    if studies.k < 2:
        return _fail()
    Sigma, ok = _fit_sigma(Y, S, fix_rho0=True)
    if not ok or Sigma is None:
        return _fail()
    try:
        M, V = _gls_point_cov(Y, S, Sigma)
    except np.linalg.LinAlgError:
        return _fail()
    return _summarize(M, V, Sigma, alpha, {"method": "reitsma_indep"})


def sep_univariate(studies: DTAStudies, alpha: float = 0.05) -> dict:
    """Pool logit-Se and logit-Sp separately (DerSimonian-Laird), rho ignored.

    Naive lower-bound comparator: ignores between-study correlation entirely.
    """
    if studies.k < 2:
        return _fail()

    def _dl(y, s2):
        w = 1.0 / s2
        mu_fe = np.sum(w * y) / np.sum(w)
        Q = float(np.sum(w * (y - mu_fe) ** 2))
        k = len(y)
        c = np.sum(w) - np.sum(w ** 2) / np.sum(w)
        tau2 = max((Q - (k - 1)) / c, 0.0) if c > 0 else 0.0
        wr = 1.0 / (s2 + tau2)
        mu = np.sum(wr * y) / np.sum(wr)
        var = 1.0 / np.sum(wr)
        return mu, var, tau2

    m1, v1, t1sq = _dl(studies.y1, studies.s1sq)
    m2, v2, t2sq = _dl(studies.y2, studies.s2sq)
    M = np.array([m1, m2])
    V = np.array([[v1, 0.0], [0.0, v2]])
    Sigma = np.array([[t1sq, 0.0], [0.0, t2sq]])
    return _summarize(M, V, Sigma, alpha, {"method": "sep_univariate"})


def _shrinkage_delta(Sigma_hat: np.ndarray, k: int,
                     asymmetry: bool = False) -> tuple[float, dict]:
    """A-priori shrinkage intensity delta in [0, delta_max].

    Three additive, a-priori components (NOT tuned to a target):
      delta_k        small-k instability of rho-hat (-> more shrink as k falls);
      delta_boundary rho-hat on the boundary / Sigma ill-conditioned;
      delta_sel      Deeks funnel asymmetry detected (selection likely corrupts
                     the between-study correlation -> shrink it harder).
    """
    rho = Sigma_hat[0, 1] / np.sqrt(max(Sigma_hat[0, 0] * Sigma_hat[1, 1], _EPS))
    delta_k = AS_KAPPA0 / (AS_KAPPA0 + max(k - 3, 1))
    try:
        cond = float(np.linalg.cond(Sigma_hat))
    except np.linalg.LinAlgError:
        cond = np.inf
    boundary = (abs(rho) >= AS_RHO_BOUNDARY) or (cond >= AS_COND_MAX)
    delta = (delta_k
             + (AS_BOUNDARY_BOOST if boundary else 0.0)
             + (AS_SELECTION_BOOST if asymmetry else 0.0))
    delta = float(np.clip(delta, 0.0, AS_DELTA_MAX))
    return delta, {"delta_k": float(delta_k), "rho_hat": float(rho),
                   "cond": cond, "boundary": bool(boundary),
                   "asymmetry": bool(asymmetry)}


def _shrink_sigma(Sigma_hat: np.ndarray, delta: float) -> np.ndarray:
    """Shrink the CORRELATION of Sigma_hat toward identity by intensity delta.

    Keeps the (stably estimated) marginal between-study variances; shrinks only
    the (unstable) correlation: R_AS = (1-delta) R_hat + delta I.
    """
    t1 = np.sqrt(max(Sigma_hat[0, 0], _EPS))
    t2 = np.sqrt(max(Sigma_hat[1, 1], _EPS))
    rho = Sigma_hat[0, 1] / (t1 * t2)
    rho_as = (1.0 - delta) * rho
    cov = rho_as * t1 * t2
    return np.array([[t1 * t1, cov], [cov, t2 * t2]])


def deeks_asymmetry(studies: DTAStudies) -> dict:
    """Deeks' funnel-plot asymmetry test for DTA.

    Regress lnDOR on 1/sqrt(ESS) (ESS = effective sample size,
    4*n1*n0/(n1+n0)) weighted by ESS; the slope's t-test p-value is the
    asymmetry signal. Returns slope, p, and the inverse-ESS values.
    """
    tp, fp, fn, tn = studies.tp, studies.fp, studies.fn, studies.tn
    lndor = np.log((tp * tn) / (fp * fn))
    n1 = tp + fn
    n0 = fp + tn
    ess = 4.0 * n1 * n0 / (n1 + n0)
    x = 1.0 / np.sqrt(ess)
    k = len(x)
    if k < 4 or np.allclose(x, x[0]):
        return {"slope": float("nan"), "p": float("nan"), "ess": ess,
                "lndor": lndor, "n_ok": k}
    # weighted least squares of lndor ~ a + slope*x, weights = ess
    w = ess
    X = np.column_stack([np.ones(k), x])
    WX = X * w[:, None]
    XtWX = X.T @ WX
    XtWy = WX.T @ lndor
    try:
        beta = np.linalg.solve(XtWX, XtWy)
    except np.linalg.LinAlgError:
        return {"slope": float("nan"), "p": float("nan"), "ess": ess,
                "lndor": lndor, "n_ok": k}
    resid = lndor - X @ beta
    dof = k - 2
    sigma2 = float(np.sum(w * resid ** 2) / dof) if dof > 0 else float("nan")
    cov_beta = sigma2 * np.linalg.inv(XtWX)
    se_slope = float(np.sqrt(max(cov_beta[1, 1], _EPS)))
    t_stat = beta[1] / se_slope
    from scipy.stats import t as _t
    p = float(2.0 * _t.sf(abs(t_stat), df=dof)) if dof > 0 else float("nan")
    return {"slope": float(beta[1]), "intercept": float(beta[0]),
            "p": p, "ess": ess, "lndor": lndor, "n_ok": k}


def adaptshrink_dta(studies: DTAStudies, alpha: float = 0.05,
                    selection_gate: bool = True) -> dict:
    """AdaptShrink-DTA: asymmetry-gated adaptive shrinkage of the between-study
    covariance toward independence.

    Steps:
      1. ML-fit Sigma_hat (Reitsma).
      2. (if ``selection_gate``) run Deeks' funnel-asymmetry test. Selection on
         the SROC corrupts the between-study correlation, so a detected
         asymmetry (p < p_gate) *increases* the shrinkage intensity rather than
         applying a fragile point correction.
      3. Compute the a-priori shrinkage intensity delta from
         (k, |rho_hat|, cond, asymmetry).
      4. Sigma_AS = shrink the CORRELATION of Sigma_hat toward 0 by delta, keep
         the (stable) marginal variances. Recompute GLS (M, V) with Sigma_AS --
         a genuinely different point + region than Reitsma.

    Design note: an earlier v1 applied a PET-PEESE-style point shift to the
    summary lnDOR when Deeks fired. In the matched-coverage bake-off that shift
    was high-variance (the regression slope is unstable at DTA sample sizes) and
    *inflated* the error cloud even under no selection (Deeks false-fires ~10%).
    Routing the same asymmetry signal through the (bounded) shrinkage intensity
    is the low-variance alternative and is what ships. Reduces to Reitsma when
    delta=0 and no asymmetry is detected.
    """
    Y, S = _stack(studies)
    k = studies.k
    if k < 2:
        return _fail()
    Sigma_hat, ok = _fit_sigma(Y, S, fix_rho0=False)
    if not ok or Sigma_hat is None:
        return _fail()

    sel = {"detected": False, "p": float("nan"), "slope": float("nan")}
    asym = False
    if selection_gate:
        dk = deeks_asymmetry(studies)
        sel["p"] = dk["p"]
        sel["slope"] = dk["slope"]
        asym = bool(np.isfinite(dk["p"]) and dk["p"] < AS_DEEKS_PGATE)
        sel["detected"] = asym

    delta, gate_info = _shrinkage_delta(Sigma_hat, k, asymmetry=asym)
    Sigma_as = _shrink_sigma(Sigma_hat, delta)
    try:
        M, V = _gls_point_cov(Y, S, Sigma_as)
    except np.linalg.LinAlgError:
        return _fail()

    extra = {"method": "adaptshrink_dta", "delta": delta, "selection": sel}
    extra.update({f"gate_{kk}": vv for kk, vv in gate_info.items()})
    return _summarize(M, V, Sigma_as, alpha, extra)


_GH_NODES = 8   # adaptive GH nodes per random-effect dimension


def _glmm_logintegrand(b1, b2, tp, fn, fp, tn, mu1, mu2, Sinv, logdetS):
    """log p(data_i | b) + log N(b;0,Sigma), vectorized over studies.

    ``b1, b2`` are the random-effect deviations of (logit Se, logit Sp) from the
    means (mu1, mu2). Binomial normalizing constants are constant in ``b`` and
    drop out (they cancel between optimizer and region).
    """
    eta1 = np.clip(mu1 + b1, -40.0, 40.0)            # logit Se
    eta2 = np.clip(mu2 + b2, -40.0, 40.0)            # logit Sp
    lse = tp * (-np.logaddexp(0.0, -eta1)) + fn * (-np.logaddexp(0.0, eta1))
    lsp = tn * (-np.logaddexp(0.0, -eta2)) + fp * (-np.logaddexp(0.0, eta2))
    quad = (Sinv[0, 0] * b1 * b1 + 2.0 * Sinv[0, 1] * b1 * b2
            + Sinv[1, 1] * b2 * b2)
    lpri = -0.5 * quad - np.log(2.0 * np.pi) - 0.5 * logdetS
    return lse + lsp + lpri


def _glmm_mode(tp, fn, fp, tn, mu1, mu2, Sinv, n_newton=8):
    """Per-study Newton mode + precision (-Hessian) of the GLMM log-integrand.

    Vectorized over the k studies. Returns (b1_m, b2_m, P) with ``P`` the
    (k,2,2) precision at the mode used for the adaptive-GHQ whitening.
    """
    k = len(tp)
    n1 = tp + fn
    n0 = fp + tn
    b1 = np.zeros(k)
    b2 = np.zeros(k)
    si11, si12, si22 = Sinv[0, 0], Sinv[0, 1], Sinv[1, 1]
    w1 = np.zeros(k)
    w2 = np.zeros(k)
    for _ in range(n_newton):
        se = 1.0 / (1.0 + np.exp(-np.clip(mu1 + b1, -40.0, 40.0)))
        sp = 1.0 / (1.0 + np.exp(-np.clip(mu2 + b2, -40.0, 40.0)))
        g1 = (tp - n1 * se) - (si11 * b1 + si12 * b2)
        g2 = (tn - n0 * sp) - (si12 * b1 + si22 * b2)
        w1 = n1 * se * (1.0 - se)
        w2 = n0 * sp * (1.0 - sp)
        h11 = -(w1 + si11)
        h22 = -(w2 + si22)
        h12 = -si12
        det = h11 * h22 - h12 * h12
        det = np.where(np.abs(det) < 1e-12, -1e-12, det)
        db1 = -(h22 * g1 - h12 * g2) / det
        db2 = -(-h12 * g1 + h11 * g2) / det
        b1 = b1 + np.clip(db1, -4.0, 4.0)
        b2 = b2 + np.clip(db2, -4.0, 4.0)
    P = np.empty((k, 2, 2))
    P[:, 0, 0] = w1 + si11
    P[:, 1, 1] = w2 + si22
    P[:, 0, 1] = P[:, 1, 0] = si12
    return b1, b2, P


def _glmm_negll(params, tp, fn, fp, tn, n1, n0, gh_x, gh_w):
    """Negative exact-binomial bivariate-GLMM log-likelihood via adaptive GHQ.

    params = [mu1, mu2, log_tau1, log_tau2, atanh_rho] -- the same model as the
    Rutter-Gatsonis HSROC (Harbord 2007 reparameterization), fit by the exact
    binomial likelihood (cf. Reitsma's within-study normal approximation).
    """
    from scipy.special import logsumexp
    mu1, mu2 = params[0], params[1]
    t1 = np.exp(np.clip(params[2], -8.0, 4.0))
    t2 = np.exp(np.clip(params[3], -8.0, 4.0))
    rho = np.tanh(np.clip(params[4], -8.0, 8.0))
    c = rho * t1 * t2
    Sigma = np.array([[t1 * t1, c], [c, t2 * t2]])
    detS = Sigma[0, 0] * Sigma[1, 1] - Sigma[0, 1] ** 2
    if detS <= 1e-18 or not np.isfinite(detS):
        return 1e12
    Sinv = np.array([[Sigma[1, 1], -Sigma[0, 1]],
                     [-Sigma[0, 1], Sigma[0, 0]]]) / detS
    logdetS = np.log(detS)
    b1m, b2m, P = _glmm_mode(tp, fn, fp, tn, mu1, mu2, Sinv)
    sign, logdetP = np.linalg.slogdet(P)
    if np.any(sign <= 0) or not np.all(np.isfinite(logdetP)):
        return 1e12
    try:
        Cov = np.linalg.inv(P)
        L = np.linalg.cholesky(Cov)              # (k,2,2)
    except np.linalg.LinAlgError:
        return 1e12
    rt2 = np.sqrt(2.0)
    X1, X2 = np.meshgrid(gh_x, gh_x, indexing="ij")
    x = np.column_stack([X1.ravel(), X2.ravel()])   # (Q,2)
    logw = np.log(gh_w)
    LW = (logw[:, None] + logw[None, :]).ravel()    # (Q,)
    Lx = np.einsum("kij,qj->kqi", L, rt2 * x)        # (k,Q,2)
    b1n = b1m[:, None] + Lx[:, :, 0]
    b2n = b2m[:, None] + Lx[:, :, 1]
    Qn = _glmm_logintegrand(b1n, b2n, tp[:, None], fn[:, None],
                            fp[:, None], tn[:, None], mu1, mu2, Sinv, logdetS)
    halflogdetCov = -0.5 * logdetP
    xnorm2 = np.sum(x ** 2, axis=1)
    terms = Qn + (LW + xnorm2)[None, :]
    ll_i = (np.log(2.0) + halflogdetCov) + logsumexp(terms, axis=1)
    if not np.all(np.isfinite(ll_i)):
        return 1e12
    return float(-np.sum(ll_i))


def _num_hessian(f, x: np.ndarray, eps: float = 1e-4) -> np.ndarray:
    """Central-difference Hessian of scalar f at x."""
    n = len(x)
    H = np.zeros((n, n))
    h = eps * (1.0 + np.abs(x))
    f0 = f(x)
    for i in range(n):
        for j in range(i, n):
            if i == j:
                xi = x.copy(); xi[i] = x[i] + h[i]; fpv = f(xi)
                xi[i] = x[i] - h[i]; fmv = f(xi)
                H[i, i] = (fpv - 2.0 * f0 + fmv) / (h[i] * h[i])
            else:
                xpp = x.copy(); xpp[i] += h[i]; xpp[j] += h[j]
                xpm = x.copy(); xpm[i] += h[i]; xpm[j] -= h[j]
                xmp = x.copy(); xmp[i] -= h[i]; xmp[j] += h[j]
                xmm = x.copy(); xmm[i] -= h[i]; xmm[j] -= h[j]
                H[i, j] = H[j, i] = (
                    (f(xpp) - f(xpm) - f(xmp) + f(xmm)) / (4.0 * h[i] * h[j]))
    return H


def hsroc(studies: DTAStudies, alpha: float = 0.05) -> dict:
    """HSROC (Rutter-Gatsonis 2001) summary operating point + confidence region.

    The HSROC model is the bivariate generalized linear mixed model (Harbord
    2007 reparameterization) fit by the **exact binomial** likelihood, integrated
    over the study random effects by adaptive (Laplace-centred) Gauss-Hermite
    quadrature. It is the second standard DTA field-to-beat alongside the
    normal-normal Reitsma model and differs from it most where the within-study
    normal approximation is poor -- sparse / zero-cell tables and small per-arm
    n. The fit is parameterized as ``(mu1, mu2, log tau1, log tau2, atanh rho)``
    and warm-started from the normal-normal fit (essentially at the GLMM
    optimum), so a single local optimization converges; the summary point is
    ``(mu1, mu2)`` and its covariance is the (mu1, mu2) block of the inverse
    observed information. Reported HSROC shape ``beta = log(tau2/tau1)``.
    """
    k = studies.k
    if k < 2:
        return _fail()
    tp = np.asarray(studies.tp, float); fn = np.asarray(studies.fn, float)
    fp = np.asarray(studies.fp, float); tn = np.asarray(studies.tn, float)
    n1 = tp + fn
    n0 = tn + fp
    gh_x, gh_w = np.polynomial.hermite.hermgauss(_GH_NODES)

    def f(p):
        return _glmm_negll(p, tp, fn, fp, tn, n1, n0, gh_x, gh_w)

    # Warm start: the normal-normal Reitsma fit sits essentially at the exact-
    # binomial GLMM optimum -> one local optimization suffices.
    Y, S = _stack(studies)
    Sig0, ok0 = _fit_sigma(Y, S, fix_rho0=False)
    if ok0 and Sig0 is not None:
        try:
            M0, _ = _gls_point_cov(Y, S, Sig0)
        except np.linalg.LinAlgError:
            M0 = np.array([np.mean(studies.y1), np.mean(studies.y2)])
        t1_0 = np.sqrt(max(Sig0[0, 0], 1e-3))
        t2_0 = np.sqrt(max(Sig0[1, 1], 1e-3))
        rho0 = float(np.clip(Sig0[0, 1] / (t1_0 * t2_0), -0.95, 0.95))
        p0 = np.array([M0[0], M0[1], np.log(t1_0), np.log(t2_0),
                       np.arctanh(rho0)])
    else:
        p0 = np.array([float(np.mean(studies.y1)), float(np.mean(studies.y2)),
                       np.log(0.5), np.log(0.5), 0.0])

    best = None
    for x0 in (p0, np.array([p0[0], p0[1], np.log(0.8), np.log(0.8), 0.0])):
        try:
            r1 = minimize(f, x0, method="Nelder-Mead",
                          options={"xatol": 1e-7, "fatol": 1e-9,
                                   "maxiter": 4000})
            r2 = minimize(f, r1.x, method="L-BFGS-B",
                          bounds=[(-20, 20), (-20, 20), (-7, 4),
                                  (-7, 4), (-6, 6)],
                          options={"maxiter": 300, "ftol": 1e-12, "gtol": 1e-8})
            res = r2 if r2.fun <= r1.fun else r1
        except Exception:
            continue
        if best is None or res.fun < best.fun:
            best = res
    if best is None or not np.isfinite(best.fun) or best.fun >= 1e11:
        return _fail()

    phat = best.x
    M = np.array([phat[0], phat[1]])
    try:
        H = _num_hessian(f, phat)
        C = np.linalg.inv(H)
        V = C[np.ix_([0, 1], [0, 1])]
        V = 0.5 * (V + V.T)
        if (not np.all(np.isfinite(V))) or np.linalg.det(V) <= 0:
            return _fail()
    except np.linalg.LinAlgError:
        return _fail()
    t1 = float(np.exp(phat[2])); t2 = float(np.exp(phat[3]))
    rho = float(np.tanh(phat[4]))
    Sigma_report = np.array([[t1 * t1, rho * t1 * t2],
                             [rho * t1 * t2, t2 * t2]])
    return _summarize(M, V, Sigma_report, alpha, {
        "method": "hsroc",
        "hsroc_beta": float(np.log(t2 / t1)),
        "hsroc_tau1": t1, "hsroc_tau2": t2, "hsroc_rho": rho,
    })


# Convenience dispatcher mirroring the univariate `_run_method` shape.
_DTA_METHODS = {
    "reitsma": reitsma,
    "reitsma_reml": reitsma_reml,
    "reitsma_indep": reitsma_indep,
    "sep_univariate": sep_univariate,
    "hsroc": hsroc,
    "adaptshrink_dta": adaptshrink_dta,
}


def run_dta_method(name: str, studies: DTAStudies, alpha: float = 0.05) -> dict:
    fn = _DTA_METHODS.get(name)
    if fn is None:
        raise ValueError(f"unknown DTA method: {name}")
    return fn(studies, alpha=alpha)
