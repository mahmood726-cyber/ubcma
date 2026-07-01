"""One-stage random-effects LOGISTIC dose-response meta-analysis (exact binomial).

The two-stage Greenland-Longnecker DRMA in `drma.py` reconstructs within-study log-RR
covariance from cell counts and is validated to ~1e-9 vs `dosresmeta` on incidence-rate /
case-control data. It is STRUCTURALLY INAPPLICABLE to sparse dose-*toxicity* data such as
`dat.ursino2021` (dose-finding DLT counts): most studies have a ZERO-EVENT reference dose,
so the reference log-RR is log(0) = -Inf and GL covariance is undefined -- a continuity
fudge cannot repair a reference-arm structural zero.

The correct model for such data -- and the one Ursino et al. (2021, Stat Methods Med Res)
used -- is a one-stage random-intercept binomial logistic dose-response fitted by EXACT
binomial likelihood:

    events_{ji} ~ Binomial(total_{ji}, p_{ji}),   logit p_{ji} = (b0 + u_j) + b1 * dose_{ji},
    u_j ~ N(0, sigma^2).

The study random effect u_j is integrated out by **Liu-Pierce adaptive Gauss-Hermite
quadrature** (the same rule lme4::glmer uses for nAGQ>1), so the fit matches glmer's AGQ
rather than only its Laplace approximation. Zero cells are handled natively by the exact
binomial -- no continuity correction. This is the binary/exact-likelihood analogue of the
MBNMA saturated model and gives a SECOND real-data validation anchor (a different outcome
family from the incidence-rate alcohol_crc anchor).

Validated against `lme4::glmer(cbind(events, total-events) ~ dose ~ (1|study),
family=binomial, nAGQ=<same>)` in `test_drma_binomial.py` / `xverify_binomial.R`.
"""
import numpy as np
from dataclasses import dataclass
from scipy.optimize import minimize
from scipy.special import roots_hermite


@dataclass
class BinomialDRFit:
    b0: float            # intercept (logit)
    b1: float            # dose slope (logit per dose-unit)
    sigma: float         # study random-intercept SD
    se_b0: float
    se_b1: float
    se_logsigma: float
    loglik: float
    nAGQ: int
    n_studies: int

    def predict_logit(self, dose):
        return self.b0 + self.b1 * np.asarray(dose, float)


def _study_loglik(u, y, n, eta_fixed):
    """log P(y | u) for one study across its dose rows (exact binomial, no constants)."""
    eta = eta_fixed + u
    # log binomial pmf up to the (u-free) n-choose-y constant:
    #   y*eta - n*log(1+exp(eta))   (numerically stable)
    return float((y * eta - n * np.logaddexp(0.0, eta)).sum())


def _study_marginal_loglik(y, n, eta_fixed, sigma, gh_x, gh_w, newton_iter=12):
    """log integral of exp(loglik(u)) * N(u;0,sigma^2) du via Liu-Pierce adaptive GHQ.

    g(u) = studyloglik(u) - u^2/(2 sigma^2) - 0.5 log(2 pi sigma^2)
    marginal = int exp(g(u)) du ; AGQ centres nodes at the mode of g and scales by curvature.
    """
    s2 = sigma * sigma
    # ---- Newton to the mode of g(u) ----
    u = 0.0
    for _ in range(newton_iter):
        eta = eta_fixed + u
        p = 1.0 / (1.0 + np.exp(-eta))
        gp = float((y - n * p).sum()) - u / s2          # g'(u)
        gpp = -float((n * p * (1.0 - p)).sum()) - 1.0 / s2  # g''(u) < 0
        step = gp / gpp
        u -= step
        if abs(step) < 1e-10:
            break
    u_hat = u
    eta = eta_fixed + u_hat
    p = 1.0 / (1.0 + np.exp(-eta))
    gpp = -float((n * p * (1.0 - p)).sum()) - 1.0 / s2
    s_hat = 1.0 / np.sqrt(-gpp)                          # adaptive scale
    # ---- Liu-Pierce adaptive GH:  int exp(g) du ~ sqrt(2) s_hat sum w_q e^{z_q^2} e^{g(node)} ----
    nodes = u_hat + np.sqrt(2.0) * s_hat * gh_x
    log_norm = -0.5 * np.log(2.0 * np.pi * s2)
    terms = np.empty(len(gh_x))
    for q, uq in enumerate(nodes):
        g = _study_loglik(uq, y, n, eta_fixed) - uq * uq / (2.0 * s2) + log_norm
        terms[q] = np.log(gh_w[q]) + gh_x[q] ** 2 + g
    # log( sqrt(2) s_hat * sum exp(terms) )
    m = terms.max()
    return 0.5 * np.log(2.0) + np.log(s_hat) + m + np.log(np.exp(terms - m).sum())


def _neg_marginal_loglik(theta, studies, gh_x, gh_w):
    b0, b1, logsigma = theta
    sigma = np.exp(logsigma)
    ll = 0.0
    for (dose, y, n) in studies:
        eta_fixed = b0 + b1 * dose
        ll += _study_marginal_loglik(y, n, eta_fixed, sigma, gh_x, gh_w)
    return -ll


def fit_logistic_dr(df, *, dose_col="dose", events_col="events", total_col="total",
                    id_col="study", nAGQ=15, dose_scale=1.0):
    """Fit the one-stage random-intercept binomial logistic dose-response.

    dose_scale divides the dose before fitting (numerical conditioning); the returned
    slope b1 is on the SCALED dose (match the same scaling in the glmer gold-standard).
    """
    gh_x, gh_w = roots_hermite(nAGQ)
    studies = []
    for _, sub in df.groupby(id_col, sort=True):
        dose = sub[dose_col].to_numpy(float) / dose_scale
        y = sub[events_col].to_numpy(float)
        n = sub[total_col].to_numpy(float)
        studies.append((dose, y, n))

    # ---- starting values: pooled FIXED-effect logistic (b0,b1) by Newton-IRLS ----
    #      (starting the slope at 0 lets the joint optimiser collapse sigma->0; a good
    #       fixed-effect slope is essential for the RE optimum to be found.)
    b0_0, b1_0 = _pooled_logistic(studies)
    theta0 = np.array([b0_0, b1_0, np.log(0.5)])
    # Powell is derivative-free and robust on this smooth, mildly-ridged surface;
    # then Nelder-Mead refine, then BFGS polish. Keep the best.
    best = None
    for meth, opts in [("Powell", dict(xtol=1e-9, ftol=1e-10, maxiter=20000, maxfev=20000)),
                       ("Nelder-Mead", dict(xatol=1e-9, fatol=1e-10, maxiter=20000, maxfev=20000))]:
        r = minimize(_neg_marginal_loglik, theta0 if best is None else best.x,
                     args=(studies, gh_x, gh_w), method=meth, options=opts)
        if best is None or r.fun <= best.fun:
            best = r
    rb = minimize(_neg_marginal_loglik, best.x, args=(studies, gh_x, gh_w), method="BFGS",
                  options=dict(gtol=1e-9, maxiter=1000))
    if rb.fun <= best.fun:
        best = rb
    b0, b1, logsigma = best.x
    theta = best.x

    # ---- SEs from numerical Hessian of the negative log-lik ----
    H = _num_hessian(lambda t: _neg_marginal_loglik(t, studies, gh_x, gh_w), theta)
    cov = np.linalg.inv(H)
    se = np.sqrt(np.diag(cov))
    return BinomialDRFit(b0=float(b0), b1=float(b1), sigma=float(np.exp(logsigma)),
                         se_b0=float(se[0]), se_b1=float(se[1]), se_logsigma=float(se[2]),
                         loglik=float(-_neg_marginal_loglik(theta, studies, gh_x, gh_w)),
                         nAGQ=nAGQ, n_studies=len(studies))


def _pooled_logistic(studies, iters=50):
    """Fixed-effect pooled logistic (b0 + b1*dose) by Newton-IRLS -> starting values."""
    dose = np.concatenate([d for d, _, _ in studies])
    y = np.concatenate([y for _, y, _ in studies])
    n = np.concatenate([n for _, _, n in studies])
    X = np.column_stack([np.ones_like(dose), dose])
    beta = np.array([np.log((y.sum() + 0.5) / (n.sum() - y.sum() + 0.5)), 0.0])
    for _ in range(iters):
        eta = X @ beta; p = 1.0 / (1.0 + np.exp(-eta))
        W = n * p * (1.0 - p)
        grad = X.T @ (y - n * p)
        H = X.T @ (X * W[:, None])
        step = np.linalg.solve(H + 1e-8 * np.eye(2), grad)
        beta = beta + step
        if np.max(np.abs(step)) < 1e-10:
            break
    return float(beta[0]), float(beta[1])


def _num_hessian(f, x, eps=1e-4):
    n = len(x); H = np.zeros((n, n)); fx = f(x)
    for i in range(n):
        for j in range(i, n):
            xi = x.copy()
            if i == j:
                xi[i] = x[i] + eps; fpp = f(xi)
                xi[i] = x[i] - eps; fmm = f(xi)
                H[i, i] = (fpp - 2 * fx + fmm) / eps ** 2
            else:
                xi = x.copy(); xi[i] += eps; xi[j] += eps; fpp = f(xi)
                xi = x.copy(); xi[i] += eps; xi[j] -= eps; fpm = f(xi)
                xi = x.copy(); xi[i] -= eps; xi[j] += eps; fmp = f(xi)
                xi = x.copy(); xi[i] -= eps; xi[j] -= eps; fmm = f(xi)
                H[i, j] = H[j, i] = (fpp - fpm - fmp + fmm) / (4 * eps ** 2)
    return H


if __name__ == "__main__":
    import io, sys, pandas as pd
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    df = pd.read_csv("F:/public-data/metadat/dat.ursino2021.csv")
    fit = fit_logistic_dr(df, nAGQ=15, dose_scale=100.0)
    print(f"ursino2021 one-stage RE logistic dose-response (nAGQ={fit.nAGQ}, dose/100, {fit.n_studies} studies)")
    print(f"  intercept b0 = {fit.b0:+.6f}  (se {fit.se_b0:.6f})")
    print(f"  dose slope b1 = {fit.b1:+.6f}  (se {fit.se_b1:.6f})   [logit per 100 dose-units]")
    print(f"  study RE SD sigma = {fit.sigma:.6f}")
    print(f"  marginal logLik = {fit.loglik:.6f}")
