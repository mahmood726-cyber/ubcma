"""drma.py -- aggregate-data dose-response meta-analysis (two-stage + one-stage).

A from-scratch implementation of the Greenland-Longnecker / Orsini-Crippa
dose-response meta-analysis, the engine behind R's `dosresmeta`. It is the
modern aggregate-data dose-response field we validate against (to ~1e-6) and
then subject to the AdaptShrink matched-coverage discipline.

Pipeline
--------
Each study reports, for a common reference exposure category (dose x0) and
several non-reference categories, an adjusted (log) relative risk y_i and its
variance v_i. Because every non-reference y_i is measured *against the same
reference group*, the y_i within a study are CORRELATED -- they share the
reference arm. Ignoring that correlation biases the pooled trend.

  Stage 0 (Greenland-Longnecker covariance reconstruction, `gl_covariance`):
    From the reported category counts (cases A_i, totals/person-time N_i) and
    the reported variances v_i, reconstruct the full within-study covariance
    matrix S of the non-reference log-RRs. The off-diagonal correlation comes
    from the shared reference arm; the diagonal is held at the reported v_i.
    Counts that are not exactly consistent with the adjusted RRs are corrected
    by the GL Newton iteration (`gl_reconstruct`).

  Stage 1 (within-study GLS, `first_stage`):
    Regress y_i on a dose transformation g(x) (linear, or restricted cubic
    spline) THROUGH the reference (no intercept: g is centered at x0), using S
    as the GLS weight. Returns each study's coefficient vector b_i and its
    covariance Sigma_i = (X' S^-1 X)^-1.

  Stage 2 (across-study multivariate random-effects pooling, `mvmeta`):
    Pool the b_i with a p-dimensional random-effects model b_i ~ N(beta, Si+Psi)
    by REML (or fixed effect). p=1 recovers ordinary univariate REML.

A `one_stage` pooled-GLS variant (single big GLS with a common slope and
study-stratified reference, fixed-effect) is provided for cross-checking.

Validated against `dosresmeta` 2.2.0 on the canonical `alcohol_crc` JSS dataset
(8 cohort studies, incidence-rate type) -- see doseresponse/test_drma.py and
doseresponse/reference/.

Conventions
-----------
type in {'cc','ir','ci'}: case-control, incidence-rate (person-time), and
cumulative-incidence cohorts respectively -- these select the GL variance form,
exactly as dosresmeta's covar.logrr. The reference row of each study has y=0 and
v that is NA/0; it is identified by v==0.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np
from scipy.optimize import minimize

_EPS = 1e-12


# --------------------------------------------------------------------------- #
#  Stage 0: Greenland-Longnecker covariance reconstruction                    #
# --------------------------------------------------------------------------- #
def gl_reconstruct(y, v, cases, n, type_, tol=1e-5, max_iter=500):
    """Greenland-Longnecker (1992) adjusted-count reconstruction.

    Returns adjusted case counts A (same length as input; reference included)
    consistent with the reported adjusted log-RRs and totals. Ports the Newton
    iteration in dosresmeta::grl exactly.
    """
    y = np.asarray(y, float)
    v = np.asarray(v, float).copy()
    v[~np.isfinite(v)] = 0.0
    cases = np.asarray(cases, float)
    n = np.asarray(n, float)
    nz = v != 0.0            # non-reference categories
    ref = ~nz
    if ref.sum() != 1:
        raise ValueError("exactly one reference category (v==0) required per study")
    is_ir = str(type_) == "ir"
    total_cases = cases.sum()
    Ax = cases.astype(float).copy()
    m = int(nz.sum())
    for _ in range(max_iter):
        A0 = total_cases - Ax[nz].sum()
        if is_ir:
            cx = 1.0 / Ax
        else:
            cx = 1.0 / Ax + 1.0 / (n - Ax)
        cx0 = float(cx[ref][0])
        if is_ir:
            e = (y[nz] + np.log(A0) + np.log(n[nz])
                 - np.log(Ax[nz]) - np.log(n[ref][0]))
        else:
            e = (y[nz] + np.log(A0) + np.log(n[nz] - Ax[nz])
                 - np.log(Ax[nz]) - np.log(n[ref][0] - A0))
        H = np.full((m, m), cx0)
        H[np.diag_indices(m)] = cx[nz] + cx0
        step = np.linalg.solve(H, e)
        Axp = Ax.copy()
        Axp[ref] = A0
        Axp[nz] = Ax[nz] + step
        delta = float(np.sum((Axp[nz] - Ax[nz]) ** 2))
        Ax = Axp
        if delta < tol:
            break
    return Ax, n


def gl_covariance(y, v, cases, n, type_):
    """Full within-study covariance S of the NON-reference log-RRs.

    Diagonal = reported v_i; off-diagonal correlation reconstructed from the
    shared reference arm via GL counts. Ports dosresmeta::covar.logrr.
    """
    v = np.asarray(v, float).copy()
    v[~np.isfinite(v)] = 0.0
    A, N = gl_reconstruct(y, v, cases, n, type_)
    nz = v != 0.0
    ref = ~nz
    A0, N0 = float(A[ref][0]), float(N[ref][0])
    Ai, Ni = A[nz], N[nz]
    t = str(type_)
    if t == "cc":
        s0 = 1.0 / A0 + 1.0 / (N0 - A0)
        si = s0 + 1.0 / Ai + 1.0 / (Ni - Ai)
    elif t == "ir":
        s0 = 1.0 / A0
        si = s0 + 1.0 / Ai
    elif t == "ci":
        s0 = 1.0 / A0 - 1.0 / N0
        si = s0 + 1.0 / Ai - 1.0 / Ni
    else:
        raise ValueError(f"unknown type {t!r} (expected cc/ir/ci)")
    rcorr = s0 / np.sqrt(np.outer(si, si))
    np.fill_diagonal(rcorr, 1.0)
    vnz = v[nz]
    S = np.sqrt(np.outer(vnz, vnz)) * rcorr
    return S


# --------------------------------------------------------------------------- #
#  Dose transformations (design basis)                                        #
# --------------------------------------------------------------------------- #
def _pos3(u):
    return np.where(u > 0, u, 0.0) ** 3


def rcs_basis(x, knots):
    """Harrell restricted-cubic-spline basis (norm=2), matching rms::rcs.

    For k knots returns a (len(x), k-1) matrix: column 0 is x, then k-2
    nonlinear terms each divided by (t_k - t_1)^2.
    """
    x = np.asarray(x, float)
    t = np.asarray(knots, float)
    k = len(t)
    if k < 3:
        raise ValueError("rcs needs >=3 knots")
    X = np.zeros((x.shape[0], k - 1))
    X[:, 0] = x
    denom = t[k - 1] - t[k - 2]
    scale = (t[k - 1] - t[0]) ** 2
    for j in range(k - 2):
        X[:, j + 1] = (
            _pos3(x - t[j])
            - _pos3(x - t[k - 2]) * (t[k - 1] - t[j]) / denom
            + _pos3(x - t[k - 1]) * (t[k - 2] - t[j]) / denom
        ) / scale
    return X


def design(dose, ref_dose, transform="linear", knots=None):
    """Reference-centered design matrix g(dose) - g(ref_dose).

    Linear: a single column (dose - ref_dose). Spline: the RCS basis difference.
    """
    dose = np.asarray(dose, float)
    if transform == "linear":
        return (dose - ref_dose).reshape(-1, 1)
    if transform == "rcs":
        if knots is None:
            raise ValueError("rcs transform requires knots")
        B = rcs_basis(dose, knots)
        Bref = rcs_basis(np.array([ref_dose]), knots)
        return B - Bref
    raise ValueError(f"unknown transform {transform!r}")


# --------------------------------------------------------------------------- #
#  Stage 1: within-study GLS                                                   #
# --------------------------------------------------------------------------- #
@dataclass
class StudyFit:
    b: np.ndarray          # coefficient vector (p,)
    Sigma: np.ndarray      # covariance (p, p)
    S: np.ndarray          # within-study log-RR covariance (m, m)
    X: np.ndarray          # reference-centered design (m, p)


def first_stage(dose, y, v, cases, n, type_, transform="linear", knots=None):
    """GLS dose-response fit for ONE study. Returns StudyFit."""
    y = np.asarray(y, float)
    v = np.asarray(v, float).copy()
    v[~np.isfinite(v)] = 0.0
    nz = v != 0.0
    ref = ~nz
    ref_dose = float(np.asarray(dose, float)[ref][0])
    S = gl_covariance(y, v, cases, n, type_)
    Xfull = design(dose, ref_dose, transform, knots)
    X = Xfull[nz]
    ynz = y[nz]
    Sinv = np.linalg.inv(S)
    XtSi = X.T @ Sinv
    Sigma = np.linalg.inv(XtSi @ X)
    b = Sigma @ (XtSi @ ynz)
    return StudyFit(b=b, Sigma=Sigma, S=S, X=X)


# --------------------------------------------------------------------------- #
#  Stage 2: multivariate random-effects pooling (mvmeta REML)                 #
# --------------------------------------------------------------------------- #
@dataclass
class DRMAFit:
    coef: np.ndarray       # pooled coefficients (p,)
    vcov: np.ndarray       # covariance of pooled coefficients (p, p)
    Psi: np.ndarray        # between-study covariance (p, p)
    method: str
    bi: np.ndarray         # stacked per-study coefficients (k, p)
    Sigma_list: list       # per-study within covariances
    knots: object = None
    transform: str = "linear"
    ref_dose: float = 0.0
    loglik: float = float("nan")
    converged: bool = True


def _gls_mean(bi, Wlist):
    p = bi.shape[1]
    A = np.zeros((p, p))
    bvec = np.zeros(p)
    for b, W in zip(bi, Wlist):
        A += W
        bvec += W @ b
    Vbeta = np.linalg.inv(A)
    beta = Vbeta @ bvec
    return beta, Vbeta


def _unpack_chol(theta, p):
    """Lower-triangular Cholesky factor from unconstrained params (diag via exp)."""
    L = np.zeros((p, p))
    idx = 0
    for i in range(p):
        for j in range(i + 1):
            if i == j:
                L[i, j] = np.exp(theta[idx])
            else:
                L[i, j] = theta[idx]
            idx += 1
    return L


def _reml_negloglik(theta, bi, Slist, p):
    L = _unpack_chol(theta, p)
    Psi = L @ L.T
    Wlist = []
    logdet_sum = 0.0
    for S in Slist:
        M = S + Psi
        sign, logdet = np.linalg.slogdet(M)
        if sign <= 0:
            return 1e12
        logdet_sum += logdet
        Wlist.append(np.linalg.inv(M))
    A = np.zeros((p, p))
    bvec = np.zeros(p)
    for b, W in zip(bi, Wlist):
        A += W
        bvec += W @ b
    sign, logdetA = np.linalg.slogdet(A)
    if sign <= 0:
        return 1e12
    Vbeta = np.linalg.inv(A)
    beta = Vbeta @ bvec
    quad = 0.0
    for b, W in zip(bi, Wlist):
        r = b - beta
        quad += r @ W @ r
    # REML log-likelihood (up to a constant): -1/2 [ sum log|S+Psi| + quad + log|A| ]
    nll = 0.5 * (logdet_sum + quad + logdetA)
    return nll


def mvmeta(bi, Slist, method="reml", max_restarts=4):
    """Multivariate random-effects meta-analysis of study coefficients.

    method='fixed' -> Psi=0 GLS. method='reml' -> maximize the REML log-lik over
    the between-study covariance Psi (parameterized by its Cholesky factor),
    matching mixmeta/mvmeta's REML estimate. p=1 reduces to univariate REML.
    """
    bi = np.asarray(bi, float)
    k, p = bi.shape
    Slist = [np.asarray(S, float) for S in Slist]

    if method == "fixed":
        Wlist = [np.linalg.inv(S) for S in Slist]
        beta, Vbeta = _gls_mean(bi, Wlist)
        return beta, Vbeta, np.zeros((p, p)), float("nan")

    if method != "reml":
        raise ValueError("method must be 'fixed' or 'reml'")

    n_par = p * (p + 1) // 2
    # Starting value: method-of-moments-ish (half the average within-var, on diag)
    avg_within = np.mean([np.diag(S) for S in Slist], axis=0)
    best = None
    rng = np.random.default_rng(0)
    for r in range(max_restarts):
        theta0 = np.zeros(n_par)
        idx = 0
        for i in range(p):
            for j in range(i + 1):
                if i == j:
                    base = 0.5 * np.log(max(avg_within[i] * 0.5, 1e-8))
                    theta0[idx] = base + (0.0 if r == 0 else rng.normal(0, 1.0))
                idx += 1
        res = minimize(_reml_negloglik, theta0, args=(bi, Slist, p),
                       method="Nelder-Mead",
                       options={"xatol": 1e-10, "fatol": 1e-12, "maxiter": 20000})
        if best is None or res.fun < best.fun:
            best = res
    L = _unpack_chol(best.x, p)
    Psi = L @ L.T
    Wlist = [np.linalg.inv(S + Psi) for S in Slist]
    beta, Vbeta = _gls_mean(bi, Wlist)
    return beta, Vbeta, Psi, float(-best.fun)


# --------------------------------------------------------------------------- #
#  Top-level two-stage fit                                                     #
# --------------------------------------------------------------------------- #
def drma_two_stage(df, *, id_col="id", dose_col="dose", y_col="logrr",
                   se_col="se", cases_col="cases", n_col=None, type_col="type",
                   transform="linear", knots=None, method="reml"):
    """Two-stage dose-response meta-analysis from a long aggregate-data frame.

    df rows are (study, dose, logrr, se, cases, n, type); the reference row of
    each study has se NA/0. n_col is the totals/person-time column.
    """
    studies = list(dict.fromkeys(df[id_col].tolist()))
    bi, Slist = [], []
    ref_doses = []
    for sid in studies:
        g = df[df[id_col] == sid]
        type_ = str(g[type_col].iloc[0])
        v = g[se_col].to_numpy(float) ** 2
        fit = first_stage(
            g[dose_col].to_numpy(float), g[y_col].to_numpy(float), v,
            g[cases_col].to_numpy(float), g[n_col].to_numpy(float), type_,
            transform=transform, knots=knots,
        )
        bi.append(fit.b)
        Slist.append(fit.Sigma)
        vv = np.where(np.isfinite(v), v, 0.0)
        ref_doses.append(float(g[dose_col].to_numpy(float)[vv == 0.0][0]))
    bi = np.array(bi)
    beta, Vbeta, Psi, ll = mvmeta(bi, Slist, method=method)
    return DRMAFit(coef=beta, vcov=Vbeta, Psi=np.atleast_2d(Psi), method=method,
                   bi=bi, Sigma_list=Slist, knots=knots, transform=transform,
                   ref_dose=float(np.median(ref_doses)), loglik=ll)


def predict_logrr(fit: DRMAFit, dose, ref_dose=0.0):
    """Pooled predicted log-RR (and SE) at given dose(s) vs ref_dose."""
    X = design(np.atleast_1d(dose), ref_dose, fit.transform, fit.knots)
    yhat = X @ fit.coef
    se = np.sqrt(np.einsum("ij,jk,ik->i", X, fit.vcov, X))
    return yhat, se


# --------------------------------------------------------------------------- #
#  One-stage pooled GLS (fixed-effect common slope) -- cross-check            #
# --------------------------------------------------------------------------- #
def drma_one_stage(df, *, id_col="id", dose_col="dose", y_col="logrr",
                   se_col="se", cases_col="cases", n_col=None, type_col="type",
                   transform="linear", knots=None):
    """Single pooled GLS with a common dose-response and study-specific
    reference (fixed-effect). Stacks all studies into one block-diagonal GLS.
    """
    studies = list(dict.fromkeys(df[id_col].tolist()))
    Xblocks, yblocks, Sblocks = [], [], []
    for sid in studies:
        g = df[df[id_col] == sid]
        type_ = str(g[type_col].iloc[0])
        v = g[se_col].to_numpy(float) ** 2
        vv = np.where(np.isfinite(v), v, 0.0)
        nz = vv != 0.0
        ref_dose = float(g[dose_col].to_numpy(float)[~nz][0])
        S = gl_covariance(g[y_col].to_numpy(float), vv,
                          g[cases_col].to_numpy(float),
                          g[n_col].to_numpy(float), type_)
        Xfull = design(g[dose_col].to_numpy(float), ref_dose, transform, knots)
        Xblocks.append(Xfull[nz])
        yblocks.append(g[y_col].to_numpy(float)[nz])
        Sblocks.append(S)
    X = np.vstack(Xblocks)
    yv = np.concatenate(yblocks)
    p = X.shape[1]
    A = np.zeros((p, p))
    rhs = np.zeros(p)
    for Xb, yb, Sb in zip(Xblocks, yblocks, Sblocks):
        Sinv = np.linalg.inv(Sb)
        A += Xb.T @ Sinv @ Xb
        rhs += Xb.T @ Sinv @ yb
    Vbeta = np.linalg.inv(A)
    beta = Vbeta @ rhs
    return DRMAFit(coef=beta, vcov=Vbeta, Psi=np.zeros((p, p)), method="one_stage_fixed",
                   bi=np.array([]), Sigma_list=Sblocks, knots=knots,
                   transform=transform)
