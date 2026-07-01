"""PRIMARY registry-scale borrowing estimator: LEARNED relevance kernel + conflict-
aware borrowing + conformal calibration.

This is the promoted method (REPORT_BORROWING_FIELD.md §8; supersedes the hand-set
AdaptShrink precision-fusion field, which is retained only as a weak baseline). The
gravitational "field" idea is kept, but its gravity is *learned from data* rather
than assumed from fixed gamma-weights:

  1. LEARNED KERNEL  -- a Gaussian process (Rasmussen & Williams 2006) with an
     ARD-RBF kernel over study covariates (standardised year, standardised
     log-precision, one-hot specialty, one-hot meta-analysis) and per-study
     sampling-variance noise (alpha_i = se_i^2). Hyper-parameters (per-dimension
     length scales + signal/noise variances) are fit by marginal likelihood, so
     the data decide which covariates carry relevance -- the ARD length scales ARE
     the learned "gravity".

  2. CONFLICT-AWARE BORROWING  -- when a target has its own data, the GP field
     prior (mu_p, se_p) is fused with the own estimate by an adaptive power prior
     (Ibrahim & Chen 2000; adaptive a0 from prior-data agreement), which
     down-weights the borrowed mass under conflict.

  3. CONFORMAL CALIBRATION  -- distribution-free CV+ / split-conformal intervals
     (Vovk et al. 2005; Lei et al. 2018; Barber et al. 2021) scored per family,
     giving finite-sample nominal coverage at controlled width regardless of GP
     mis-calibration.

EVALUATION CONTRACT (truth-first): the DEFAULT held-out score is the HONEST
k-fold refit (`predict_kfold`), which re-optimises hyper-parameters on each
training fold -- it removes the shared-hyperparameter optimism of the closed-form
R&W leave-one-out (`predict_loo`, provided for reference/speed only). No study's
own effect ever enters its own feature vector (yi is the reconstruction target
only; there is no leakage).
"""
from __future__ import annotations
import numpy as np
from scipy.optimize import minimize

Z975 = 1.959963984540054


# ---------------------------------------------------------------------------
# feature embedding (NO effect value enters -- leakage-free)
# ---------------------------------------------------------------------------
def _stdz(x):
    x = np.asarray(x, float)
    m = np.isfinite(x)
    if m.sum() < 2 or np.nanstd(x[m]) < 1e-9:
        return np.zeros_like(x)
    out = np.zeros_like(x)
    out[m] = (x[m] - np.nanmean(x[m])) / (np.nanstd(x[m]) + 1e-9)
    return out


def build_features(sub):
    """Leakage-free study-covariate embedding for one family block.

    Returns a matrix whose columns are [standardised year, standardised
    log-precision, integer specialty code, integer meta-analysis code]. The two
    continuous columns enter a squared-distance RBF; the two categorical codes
    enter a match/no-match kernel. NO effect value (yi) is ever a feature.
    """
    yr = (sub["yz"].fillna(0.0).to_numpy() if "yz" in sub
          else _stdz(sub["year"].to_numpy()))
    prec = sub["prec"].to_numpy() if "prec" in sub else 1.0 / sub["se"].to_numpy() ** 2
    lp = np.log(np.maximum(prec, 1e-12))
    lp = (lp - lp.mean()) / (lp.std() + 1e-9)
    spec = np.asarray(sub["specialty"].to_numpy())
    ma = np.asarray(sub["ma"].to_numpy())
    spec_code = np.unique(spec, return_inverse=True)[1].astype(float)
    ma_code = np.unique(ma, return_inverse=True)[1].astype(float)
    return np.column_stack([yr, lp, spec_code, ma_code])


# ---------------------------------------------------------------------------
# custom GP with a grouped-ARD kernel -- the LEARNED gravity
#   K(s,t) = sf2 * exp(-0.5 * [ (dyr/l_yr)^2 + (dlp/l_lp)^2
#                               + 1[spec_s!=spec_t]/l_sp^2
#                               + 1[ma_s  !=ma_t ]/l_ma^2 ])
# Hyper-parameters theta = log([sf2, l_yr, l_lp, l_sp, l_ma, nugget]) fit by
# marginal likelihood (Rasmussen & Williams 2006). The 4 length scales ARE the
# data-driven relevance metric: small l_ma -> same-MA gravity dominates, large
# l_ma -> the MA label barely matters, etc. Per-study sampling variance se^2
# enters the noise diagonal (heteroscedastic).
# ---------------------------------------------------------------------------
def _dist_components(X):
    yr, lp, sp, ma = X[:, 0], X[:, 1], X[:, 2], X[:, 3]
    Dyr = (yr[:, None] - yr[None, :]) ** 2
    Dlp = (lp[:, None] - lp[None, :]) ** 2
    Msp = (sp[:, None] != sp[None, :]).astype(float)
    Mma = (ma[:, None] != ma[None, :]).astype(float)
    return Dyr, Dlp, Msp, Mma


def _dist_cross(Xa, Xb):
    Dyr = (Xa[:, 0][:, None] - Xb[:, 0][None, :]) ** 2
    Dlp = (Xa[:, 1][:, None] - Xb[:, 1][None, :]) ** 2
    Msp = (Xa[:, 2][:, None] != Xb[:, 2][None, :]).astype(float)
    Mma = (Xa[:, 3][:, None] != Xb[:, 3][None, :]).astype(float)
    return Dyr, Dlp, Msp, Mma


def _kmat(comps, theta):
    sf2, l_yr, l_lp, l_sp, l_ma, _ = np.exp(theta)
    Dyr, Dlp, Msp, Mma = comps
    q = Dyr / l_yr ** 2 + Dlp / l_lp ** 2 + Msp / l_sp ** 2 + Mma / l_ma ** 2
    return sf2 * np.exp(-0.5 * q)


def _obj(theta, comps, y, alpha):
    """negative log marginal likelihood + analytic gradient wrt log-hyperparameters
    (Rasmussen & Williams 2006 eq. 5.8-5.9). One Cholesky per evaluation."""
    sf2, l_yr, l_lp, l_sp, l_ma, nugget = np.exp(theta)
    Dyr, Dlp, Msp, Mma = comps
    Kf = _kmat(comps, theta)                       # signal part (no noise)
    K = Kf + np.diag(alpha + nugget)
    try:
        L = np.linalg.cholesky(K)
    except np.linalg.LinAlgError:
        return 1e12, np.zeros(6)
    a = np.linalg.solve(L.T, np.linalg.solve(L, y))
    nlml = float(0.5 * y @ a + np.log(np.diag(L)).sum() + 0.5 * len(y) * np.log(2 * np.pi))
    Kinv = np.linalg.solve(L.T, np.linalg.solve(L, np.eye(len(y))))
    W = np.outer(a, a) - Kinv                       # aa^T - Kinv
    def tr(dK):
        return -0.5 * float(np.sum(W * dK))
    g = np.array([
        tr(Kf),                                     # d/dlog sf2
        tr(Kf * (Dyr / l_yr ** 2)),                 # d/dlog l_yr
        tr(Kf * (Dlp / l_lp ** 2)),                 # d/dlog l_lp
        tr(Kf * (Msp / l_sp ** 2)),                 # d/dlog l_sp
        tr(Kf * (Mma / l_ma ** 2)),                 # d/dlog l_ma
        -0.5 * nugget * float(np.trace(W)),         # d/dlog nugget
    ])
    return nlml, g


def gp_fit(sub, n_restarts=1):
    """Fit the grouped-ARD GP on one family block by marginal likelihood.
    Returns a dict with the fitted state used by predict_loo / cross-prediction."""
    X = build_features(sub)
    y = sub["yi"].to_numpy(float)
    alpha = sub["se"].to_numpy(float) ** 2
    ymean = float(y.mean())
    yc = y - ymean
    comps = _dist_components(X)
    sy = np.log(np.var(yc) + 1e-6)
    # theta0 = log[sf2, l_yr, l_lp, l_sp, l_ma, nugget]
    starts = [np.array([sy, 0.0, 0.0, 0.0, 0.0, np.log(1e-2)])]
    rng = np.random.default_rng(0)
    for _ in range(n_restarts):
        starts.append(np.array([sy, 0.0, 0.0, 0.0, 0.0, np.log(1e-2)])
                      + rng.normal(0, 0.7, 6))
    bnds = [(-8, 6), (-4, 6), (-4, 6), (-4, 6), (-4, 6), (np.log(1e-6), np.log(1.0))]
    best = None
    for t0 in starts:
        r = minimize(_obj, t0, args=(comps, yc, alpha), method="L-BFGS-B",
                     jac=True, bounds=bnds, options=dict(maxiter=200))
        if best is None or r.fun < best.fun:
            best = r
    theta = best.x
    K = _kmat(comps, theta) + np.diag(alpha + np.exp(theta[5]))
    return dict(X=X, y=y, yc=yc, ymean=ymean, alpha=alpha, comps=comps,
                theta=theta, K=K, Kinv=np.linalg.inv(K))


def predict_loo(sub):
    """Exact closed-form leave-one-out (R&W eq. 5.12) under fitted hyper-parameters.
    Shares hyper-parameters across folds -> mildly optimistic; use predict_kfold
    for the honest headline. Returns index-aligned (mu, sd)."""
    st = gp_fit(sub)
    Kinv, yc, ymean = st["Kinv"], st["yc"], st["ymean"]
    a = Kinv @ yc
    d = np.diag(Kinv)
    mu = yc - a / d + ymean
    sd = np.sqrt(1.0 / d)
    return mu, sd


def predict_kfold(sub, n_folds=10, seed=0):
    """HONEST held-out prediction: re-optimise hyper-parameters on each training
    fold, predict the held-out fold. This is the DEFAULT evaluation. Returns
    index-aligned (mu, sd)."""
    X = build_features(sub)
    y = sub["yi"].to_numpy(float)
    alpha = sub["se"].to_numpy(float) ** 2
    n = len(y)
    nf = min(n_folds, n)
    rng = np.random.default_rng(seed)
    folds = np.array_split(rng.permutation(n), nf)
    mu = np.full(n, np.nan)
    sd = np.full(n, np.nan)
    for te in folds:
        tr = np.setdiff1d(np.arange(n), te)
        if len(tr) < 2:
            continue
        sub_tr = sub.iloc[tr]
        st = gp_fit(sub_tr)
        theta, ymean = st["theta"], st["ymean"]
        # cross-covariance train(rows) x test(cols) under fitted theta
        ctr_te = _dist_cross(st["X"], X[te])
        Ks = _kmat(ctr_te, theta)                     # (n_tr, n_te)
        a = st["Kinv"] @ st["yc"]
        mu[te] = Ks.T @ a + ymean
        sf2 = np.exp(theta[0])
        v = st["Kinv"] @ Ks
        var = sf2 - np.einsum("ij,ij->j", Ks, v)
        sd[te] = np.sqrt(np.maximum(var, 1e-9))
    return mu, sd


def predict_kfold_corpus(df, n_folds=10, seeds=(0, 1, 2, 3, 4)):
    """Corpus-level honest k-fold prediction averaged over `seeds` (fold-noise
    reduction). Runs per family block. Returns (mu, sd) arrays aligned to df."""
    n = len(df)
    mus = np.full((len(seeds), n), np.nan)
    sds = np.full((len(seeds), n), np.nan)
    for si, sd_seed in enumerate(seeds):
        for _, sub in df.groupby("family"):
            idx = sub.index.to_numpy()
            m, s = predict_kfold(sub, n_folds=n_folds, seed=sd_seed)
            mus[si, idx] = m
            sds[si, idx] = s
    return np.nanmean(mus, 0), np.nanmean(sds, 0)


def predict_loo_corpus(df):
    n = len(df)
    mu = np.full(n, np.nan)
    sd = np.full(n, np.nan)
    for _, sub in df.groupby("family"):
        idx = sub.index.to_numpy()
        m, s = predict_loo(sub)
        mu[idx] = m
        sd[idx] = s
    return mu, sd


# ---------------------------------------------------------------------------
# conflict-aware borrowing (dynamic regime): fuse GP field prior with own data
# ---------------------------------------------------------------------------
def conflict_aware_fuse(y0, se0, mu_p, se_p, a0=None):
    """Adaptive power prior (Ibrahim & Chen 2000). a0 in [0,1] from prior-data
    agreement discounts the borrowed field mass under conflict. a0=None -> adaptive."""
    if not np.isfinite(mu_p) or not np.isfinite(se_p) or se_p <= 0:
        return float(y0), float(se0)
    if a0 is None:
        Q = (y0 - mu_p) ** 2 / (se0 ** 2 + se_p ** 2)
        a0 = float(np.clip(np.exp(-0.5 * Q), 0.0, 1.0))
    p_own = 1.0 / se0 ** 2
    p_pri = a0 / se_p ** 2
    mu = (p_own * y0 + p_pri * mu_p) / (p_own + p_pri)
    return float(mu), float(np.sqrt(1.0 / (p_own + p_pri)))


# ---------------------------------------------------------------------------
# conformal calibration (distribution-free): CV+ / split-conformal per family
# ---------------------------------------------------------------------------
def conformal_intervals(df, pred, alpha=0.10):
    """CV+/jackknife+-style conformal intervals from held-out abs-residuals, scored
    within each family (Vovk 2005; Lei 2018 JASA; Barber 2021 AoS). For target j,
    q = the ceil((n)(1-alpha))/n empirical quantile of the OTHER studies' held-out
    |residual|; interval = pred_j +/- q. Returns dict(cover, width, half[array])."""
    y = df["yi"].to_numpy(float)
    n = len(df)
    half = np.full(n, np.nan)
    cov = np.full(n, np.nan)
    for _, sub in df.groupby("family"):
        idx = sub.index.to_numpy()
        res = np.abs(pred[idx] - y[idx])
        ok = np.isfinite(res)
        gi, gr = idx[ok], res[ok]
        for j in range(len(gi)):
            others = np.delete(gr, j)
            if len(others) < 1:
                continue
            q = np.quantile(others, 1 - alpha, method="higher")
            half[gi[j]] = q
            cov[gi[j]] = float(gr[j] <= q)
    return dict(cover=float(np.nanmean(cov)), width=float(np.nanmean(2 * half)),
                half=half, covered=cov)


# ---------------------------------------------------------------------------
# convenience: MAE + model-based coverage for a (mu, sd) prediction
# ---------------------------------------------------------------------------
def score(df, mu, sd, z=Z975):
    y = df["yi"].to_numpy(float)
    se_t = df["se"].to_numpy(float)
    err = np.abs(mu - y)
    hw = z * np.sqrt(sd ** 2 + se_t ** 2)
    cov = ((mu - hw <= y) & (y <= mu + hw)).astype(float)
    cov[~np.isfinite(mu)] = np.nan
    return dict(MAE=float(np.nanmean(err)), cover=float(np.nanmean(cov)),
                width=float(np.nanmean(2 * hw)), err=err)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from corpus import load_corpus
    from field import prep
    df = prep(load_corpus())
    mu, sd = predict_kfold_corpus(df)
    s = score(df, mu, sd)
    cf = conformal_intervals(df, mu)
    print(f"corpus: {len(df)} nodes, {df.ma.nunique()} MAs, families={sorted(df.family.unique())}")
    print(f"LEARNED-KERNEL FIELD (honest 10-fold, 5-seed avg):")
    print(f"  MAE={s['MAE']:.4f}  model-cover={s['cover']:.3f}  model-width={s['width']:.3f}")
    print(f"  conformal-cover={cf['cover']:.3f}  conformal-width={cf['width']:.3f}")
