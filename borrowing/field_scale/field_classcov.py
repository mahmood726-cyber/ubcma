"""PROTOTYPE (isolated, does NOT modify the shipped field_learned): the committed
grouped-ARD GP AUGMENTED with a leakage-free CLASS covariate, to test the concrete
fix target named by the donor-ceiling result (REPORT_DONOR_CEILING.md):

    "the residual is a METHOD gap -> the concrete fix target is a leakage-free
     class/effect-level covariate (drug-class/mechanism embedding ...) so the field
     can route a novel MA's level from a same-class donor WITHOUT the ma-identity match."

The shipped kernel is
    K = sf2 * exp(-0.5[ Dyr/l_yr^2 + Dlp/l_lp^2 + 1[sp!=]/l_sp^2 + 1[ma!=]/l_ma^2 ]).
The held-out novel MA gets a DISTINCT ma-code, so the ma-match term never fires against
any donor; specialty+precision+year alone recover only 37% of the cold gap (donor_ceiling).

This module adds ONE extra grouped-ARD dimension -- a CLASS match term 1[cls!=]/l_cls^2
with its own marginal-likelihood-fit length scale. The class label is derived ONLY from
registry metadata already in the MA name (`aact_<condition>_<drugclass>`), NEVER from the
effect value yi -> leakage-free. Two grains are provided:
  - 'drug'  : the drug-class token (last component)  -> groups a novel MA with a same-DRUG
              donor (the level-matched sibling in the donor-injection test).
  - 'cond'  : the condition token (middle component) -> groups by therapeutic area only
              (a novel MA with ALL same-condition donors, at mixed levels).
Corpus (non-AACT) MAs and any label not matching the aact pattern get class == their own
ma label (each its own singleton class) -> no artificial grouping, still leakage-free.

Everything else (heteroscedastic se^2 noise diagonal, L-BFGS marginal-likelihood fit with
analytic gradient, frozen-transform cross-prediction) mirrors field_learned EXACTLY so the
ONLY change under test is the added class term. With l_cls -> large (exp bound) the kernel
reduces to the committed 4-group kernel; the fit is free to ignore the class covariate, so
this cannot do WORSE than committed at the marginal-likelihood optimum (up to local optima).
"""
from __future__ import annotations
import re
import numpy as np
from scipy.optimize import minimize

# reuse the committed leakage-free continuous/categorical encoders unchanged
import field_learned as fl


# ---------------------------------------------------------------------------
# class-label derivation (leakage-free: from the MA NAME metadata, never yi)
# ---------------------------------------------------------------------------
_AACT = re.compile(r"^aact_([^_]+)_(.+)$")


def _base_label(ma: str) -> str:
    """strip the donor-injection '__sib' suffix so a split MA and its sibling share a class."""
    return ma[:-5] if ma.endswith("__sib") else ma


def class_label(ma: str, grain: str) -> str:
    """grain in {'drug','cond'}. Non-aact / non-matching labels -> own singleton class."""
    base = _base_label(ma)
    m = _AACT.match(base)
    if not m:
        return base                       # corpus MA: its own class (no grouping)
    cond, drug = m.group(1), m.group(2)
    return drug if grain == "drug" else cond


def build_features_cls(sub, grain: str):
    """committed 4-column embedding + a 5th integer CLASS code (leakage-free)."""
    X4 = fl.build_features(sub)           # [yr, lp, spec_code, ma_code]  (committed, unchanged)
    ma = np.asarray(sub["ma"].to_numpy())
    cls = np.array([class_label(m, grain) for m in ma])
    cls_code = np.unique(cls, return_inverse=True)[1].astype(float)
    return np.column_stack([X4, cls_code])   # [yr, lp, spec, ma, cls]


# ---------------------------------------------------------------------------
# 5-group grouped-ARD GP  (theta = log[sf2, l_yr, l_lp, l_sp, l_ma, l_cls, nugget])
# identical algebra to field_learned, one extra match dimension
# ---------------------------------------------------------------------------
def _dist_components5(X):
    yr, lp, sp, ma, cl = X[:, 0], X[:, 1], X[:, 2], X[:, 3], X[:, 4]
    Dyr = (yr[:, None] - yr[None, :]) ** 2
    Dlp = (lp[:, None] - lp[None, :]) ** 2
    Msp = (sp[:, None] != sp[None, :]).astype(float)
    Mma = (ma[:, None] != ma[None, :]).astype(float)
    Mcl = (cl[:, None] != cl[None, :]).astype(float)
    return Dyr, Dlp, Msp, Mma, Mcl


def _dist_cross5(Xa, Xb):
    Dyr = (Xa[:, 0][:, None] - Xb[:, 0][None, :]) ** 2
    Dlp = (Xa[:, 1][:, None] - Xb[:, 1][None, :]) ** 2
    Msp = (Xa[:, 2][:, None] != Xb[:, 2][None, :]).astype(float)
    Mma = (Xa[:, 3][:, None] != Xb[:, 3][None, :]).astype(float)
    Mcl = (Xa[:, 4][:, None] != Xb[:, 4][None, :]).astype(float)
    return Dyr, Dlp, Msp, Mma, Mcl


def _kmat5(comps, theta):
    sf2, l_yr, l_lp, l_sp, l_ma, l_cl, _ = np.exp(theta)
    Dyr, Dlp, Msp, Mma, Mcl = comps
    q = (Dyr / l_yr ** 2 + Dlp / l_lp ** 2 + Msp / l_sp ** 2
         + Mma / l_ma ** 2 + Mcl / l_cl ** 2)
    return sf2 * np.exp(-0.5 * q)


def _obj5(theta, comps, y, alpha):
    sf2, l_yr, l_lp, l_sp, l_ma, l_cl, nugget = np.exp(theta)
    Dyr, Dlp, Msp, Mma, Mcl = comps
    Kf = _kmat5(comps, theta)
    K = Kf + np.diag(alpha + nugget)
    try:
        L = np.linalg.cholesky(K)
    except np.linalg.LinAlgError:
        return 1e12, np.zeros(7)
    a = np.linalg.solve(L.T, np.linalg.solve(L, y))
    nlml = float(0.5 * y @ a + np.log(np.diag(L)).sum() + 0.5 * len(y) * np.log(2 * np.pi))
    Kinv = np.linalg.solve(L.T, np.linalg.solve(L, np.eye(len(y))))
    W = np.outer(a, a) - Kinv
    def tr(dK):
        return -0.5 * float(np.sum(W * dK))
    g = np.array([
        tr(Kf),
        tr(Kf * (Dyr / l_yr ** 2)),
        tr(Kf * (Dlp / l_lp ** 2)),
        tr(Kf * (Msp / l_sp ** 2)),
        tr(Kf * (Mma / l_ma ** 2)),
        tr(Kf * (Mcl / l_cl ** 2)),
        -0.5 * nugget * float(np.trace(W)),
    ])
    return nlml, g


def gp_fit5(sub, X, n_restarts=1):
    """Fit the 5-group GP by marginal likelihood on a PRE-COMPUTED frozen X (rows aligned)."""
    y = sub["yi"].to_numpy(float)
    alpha = sub["se"].to_numpy(float) ** 2
    ymean = float(y.mean())
    yc = y - ymean
    comps = _dist_components5(X)
    sy = np.log(np.var(yc) + 1e-6)
    base = np.array([sy, 0.0, 0.0, 0.0, 0.0, 0.0, np.log(1e-2)])
    starts = [base]
    rng = np.random.default_rng(0)
    for _ in range(n_restarts):
        starts.append(base + rng.normal(0, 0.7, 7))
    bnds = [(-8, 6), (-4, 6), (-4, 6), (-4, 6), (-4, 6), (-4, 6), (np.log(1e-6), np.log(1.0))]
    best = None
    for t0 in starts:
        r = minimize(_obj5, t0, args=(comps, yc, alpha), method="L-BFGS-B",
                     jac=True, bounds=bnds, options=dict(maxiter=200))
        if best is None or r.fun < best.fun:
            best = r
    theta = best.x
    K = _kmat5(comps, theta) + np.diag(alpha + np.exp(theta[6]))
    return dict(X=X, y=y, yc=yc, ymean=ymean, alpha=alpha, comps=comps,
                theta=theta, K=K, Kinv=np.linalg.inv(K))


def gp_cross_predict5(block, X, tr_idx, te_idx):
    """5-group analogue of cold_transfer.gp_cross_predict (frozen transform X shared)."""
    st = gp_fit5(block.iloc[tr_idx], X=X[tr_idx])
    theta, ymean = st["theta"], st["ymean"]
    Ks = _kmat5(_dist_cross5(st["X"], X[te_idx]), theta)
    a = st["Kinv"] @ st["yc"]
    mu = Ks.T @ a + ymean
    sf2 = np.exp(theta[0])
    v = st["Kinv"] @ Ks
    var = sf2 - np.einsum("ij,ij->j", Ks, v)
    return mu, np.sqrt(np.maximum(var, 1e-9))


def predict_kfold5(sub, grain, n_folds=10, seed=0):
    """Honest k-fold with the 5-group kernel (frozen transform), for the corpus regression check."""
    X = build_features_cls(sub, grain)
    y = sub["yi"].to_numpy(float)
    n = len(y)
    nf = min(n_folds, n)
    rng = np.random.default_rng(seed)
    folds = np.array_split(rng.permutation(n), nf)
    mu = np.full(n, np.nan)
    for te in folds:
        tr = np.setdiff1d(np.arange(n), te)
        if len(tr) < 2:
            continue
        st = gp_fit5(sub.iloc[tr], X=X[tr])
        theta, ymean = st["theta"], st["ymean"]
        Ks = _kmat5(_dist_cross5(st["X"], X[te]), theta)
        a = st["Kinv"] @ st["yc"]
        mu[te] = Ks.T @ a + ymean
    return mu
