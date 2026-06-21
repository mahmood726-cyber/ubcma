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
* ``reitsma_indep`` -- the same with ``rho`` fixed at 0 (Riley-style small-k
  stabilizer / separate-variances bivariate).
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


def _neg_loglik(params: np.ndarray, Y: np.ndarray, S: np.ndarray,
                fix_rho0: bool) -> float:
    """Profile -2*loglik over (M1,M2) given Sigma params (GLS-concentrated ML).

    For fixed Sigma the MLE of M is GLS; plugging it back gives a likelihood
    that depends only on the Sigma params. Y is (k,2), S is (k,2,2) within-study.
    """
    log_t1, log_t2 = params[0], params[1]
    z_rho = 0.0 if fix_rho0 else params[2]
    Sigma = _sigma_from_params(log_t1, log_t2, z_rho)
    k = Y.shape[0]
    A = np.zeros((2, 2))      # sum of precisions
    b = np.zeros(2)           # sum precision * y
    logdet_sum = 0.0
    quad_sum = 0.0
    Wi_list = np.empty((k, 2, 2))
    for i in range(k):
        Vi = Sigma + S[i]
        sign, logdet = np.linalg.slogdet(Vi)
        if sign <= 0 or not np.isfinite(logdet):
            return 1e12
        Wi = np.linalg.inv(Vi)
        Wi_list[i] = Wi
        A += Wi
        b += Wi @ Y[i]
        logdet_sum += logdet
        quad_sum += Y[i] @ Wi @ Y[i]
    try:
        Ainv = np.linalg.inv(A)
    except np.linalg.LinAlgError:
        return 1e12
    M = Ainv @ b
    # quad form: sum (y_i - M)' Wi (y_i - M) = quad_sum - b' M
    quad = quad_sum - b @ M
    nll = 0.5 * (logdet_sum + quad)
    return float(nll)


def _gls_point_cov(Y: np.ndarray, S: np.ndarray, Sigma: np.ndarray):
    """Return (M, V) GLS summary point and its covariance for a fixed Sigma."""
    k = Y.shape[0]
    A = np.zeros((2, 2))
    b = np.zeros(2)
    for i in range(k):
        Wi = np.linalg.inv(Sigma + S[i])
        A += Wi
        b += Wi @ Y[i]
    V = np.linalg.inv(A)
    M = V @ b
    return M, V


def _fit_sigma(Y: np.ndarray, S: np.ndarray, fix_rho0: bool):
    """ML-fit Sigma; return (Sigma, converged). Multi-start for robustness."""
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
            res = minimize(_neg_loglik, x0, args=(Y, S, fix_rho0),
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


def _shrinkage_delta(Sigma_hat: np.ndarray, k: int) -> tuple[float, dict]:
    """A-priori condition/k-gated shrinkage intensity delta in [0, delta_max]."""
    rho = Sigma_hat[0, 1] / np.sqrt(max(Sigma_hat[0, 0] * Sigma_hat[1, 1], _EPS))
    delta_k = AS_KAPPA0 / (AS_KAPPA0 + max(k - 3, 1))
    try:
        cond = float(np.linalg.cond(Sigma_hat))
    except np.linalg.LinAlgError:
        cond = np.inf
    boundary = (abs(rho) >= AS_RHO_BOUNDARY) or (cond >= AS_COND_MAX)
    delta = delta_k + (AS_BOUNDARY_BOOST if boundary else 0.0)
    delta = float(np.clip(delta, 0.0, AS_DELTA_MAX))
    return delta, {"delta_k": float(delta_k), "rho_hat": float(rho),
                   "cond": cond, "boundary": bool(boundary)}


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
    """AdaptShrink-DTA: Sigma-shrinkage + Deeks-gated SROC selection correction.

    Steps:
      1. ML-fit Sigma_hat (Reitsma).
      2. Compute a-priori shrinkage intensity delta from (k, |rho_hat|, cond).
      3. Sigma_AS = shrink correlation toward 0 by delta. Recompute GLS (M, V)
         using Sigma_AS (a genuinely different point + region than Reitsma).
      4. (optional) If Deeks' asymmetry p < p_gate, apply a regression small-
         study correction to the summary lnDOR and project it back onto the
         summary operating point along the SROC.

    Reduces to Reitsma when delta=0 and no asymmetry is detected.
    """
    Y, S = _stack(studies)
    k = studies.k
    if k < 2:
        return _fail()
    Sigma_hat, ok = _fit_sigma(Y, S, fix_rho0=False)
    if not ok or Sigma_hat is None:
        return _fail()
    delta, gate_info = _shrinkage_delta(Sigma_hat, k)
    Sigma_as = _shrink_sigma(Sigma_hat, delta)
    try:
        M, V = _gls_point_cov(Y, S, Sigma_as)
    except np.linalg.LinAlgError:
        return _fail()

    # --- Deeks-asymmetry-gated SROC selection correction ---
    sel = {"applied": False, "p": float("nan"), "slope": float("nan")}
    if selection_gate:
        dk = deeks_asymmetry(studies)
        sel["p"] = dk["p"]
        sel["slope"] = dk["slope"]
        if np.isfinite(dk["p"]) and dk["p"] < AS_DEEKS_PGATE:
            # PET-PEESE analogue on lnDOR: the asymmetry slope * mean(1/sqrt(ESS))
            # is the small-study inflation of the pooled lnDOR. Remove it, holding
            # the threshold/SROC position (M1 - M2 ~ const) fixed: move the
            # operating point DOWN the SROC so lnDOR = M1 + M2 drops by the
            # estimated inflation, split evenly between the two logit coords.
            ess_corr = dk["slope"] * float(np.mean(1.0 / np.sqrt(dk["ess"])))
            # current pooled lnDOR on the summary scale ~ M1 + M2
            shift = 0.5 * ess_corr
            M = np.array([M[0] - shift, M[1] - shift])
            sel["applied"] = True
            sel["shift"] = float(shift)

    extra = {"method": "adaptshrink_dta", "delta": delta, "selection": sel}
    extra.update({f"gate_{kk}": vv for kk, vv in gate_info.items()})
    return _summarize(M, V, Sigma_as, alpha, extra)


# Convenience dispatcher mirroring the univariate `_run_method` shape.
_DTA_METHODS = {
    "reitsma": reitsma,
    "reitsma_indep": reitsma_indep,
    "sep_univariate": sep_univariate,
    "adaptshrink_dta": adaptshrink_dta,
}


def run_dta_method(name: str, studies: DTAStudies, alpha: float = 0.05) -> dict:
    fn = _DTA_METHODS.get(name)
    if fn is None:
        raise ValueError(f"unknown DTA method: {name}")
    return fn(studies, alpha=alpha)
