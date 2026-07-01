"""Modern / state-of-the-art comparators for the registry-scale borrowing field.

Every method is implemented from scratch in numpy/scipy/sklearn (the canonical
packages RBesT, REBayes, deconvolveR, bayesmeta are NOT installed on this host;
metafor 5.0.1 is available and used as an external RE cross-check). Citations are
in each docstring; a consolidated list is in REPORT_BORROWING_FIELD.md.

Two evaluation regimes (both truth-gated against the REAL held-out effect y_t):
  B1  transductive  : target fully held out; predict y_t from the others.
  B2  dynamic-borrow: target has 'own' data = m same-MA siblings (down-sampling);
                      fuse own (+) cross-MA field prior. This is the regime the
                      power/commensurate/robust-MAP/SAM methods were built for.
"""
from __future__ import annotations
import numpy as np
from scipy.stats import norm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel

Z975 = 1.959963984540054


# ----------------------------------------------------------------------------
# random-effects tau^2 (DerSimonian-Laird) -- shared helper
# ----------------------------------------------------------------------------
def dl_tau2(y, se):
    y = np.asarray(y, float); v = np.asarray(se, float) ** 2
    if len(y) < 2:
        return 0.0, (float(y[0]) if len(y) else np.nan), (float(se[0]) if len(y) else np.inf)
    w = 1.0 / v
    mu = (w * y).sum() / w.sum()
    Q = (w * (y - mu) ** 2).sum()
    c = w.sum() - (w ** 2).sum() / w.sum()
    tau2 = max(0.0, (Q - (len(y) - 1)) / c) if c > 0 else 0.0
    wr = 1.0 / (v + tau2)
    mu_re = (wr * y).sum() / wr.sum()
    se_re = np.sqrt(1.0 / wr.sum())
    return float(tau2), float(mu_re), float(se_re)


# ----------------------------------------------------------------------------
# 1. Robust MAP prior  (Schmidli et al. 2014, Biometrics 70:1023; RBesT/Weber
#    et al. 2021 JSS 100(19)).  MAP = RE posterior-predictive for a new study;
#    robustified by a heavy vague mixture component that auto-adapts to conflict.
# ----------------------------------------------------------------------------
def robust_map(y_donors, se_donors, w_rob=0.2, vague_scale=None):
    """Return (mix means, mix sds, mix weights) of a 2-component robust MAP prior
    for a NEW study's effect. Component 0 = informative MAP, 1 = vague."""
    tau2, mu, se_mu = dl_tau2(y_donors, se_donors)
    # MAP predictive for a new study marginalises the between-study SD:
    map_sd = np.sqrt(se_mu ** 2 + tau2)
    if vague_scale is None:
        vague_scale = 5.0 * (np.std(y_donors) + np.mean(se_donors) + 1e-6)
    means = np.array([mu, mu])
    sds = np.array([map_sd, vague_scale])
    wts = np.array([1 - w_rob, w_rob])
    return means, sds, wts


def mixture_posterior_mean(means, sds, wts, y0, se0):
    """Conjugate normal update of a normal MIXTURE prior with one obs (y0,se0).
    Returns posterior mean (Schmidli 2014 eq.; robust component down-weights on
    conflict). Used for B2 dynamic borrowing and for interval construction."""
    post_means, post_vars, log_ev = [], [], []
    for m, s, w in zip(means, sds, wts):
        pv = 1.0 / (1.0 / s ** 2 + 1.0 / se0 ** 2)
        pm = pv * (m / s ** 2 + y0 / se0 ** 2)
        # marginal likelihood of y0 under this component (for updating weights)
        mv = s ** 2 + se0 ** 2
        le = np.log(max(w, 1e-300)) - 0.5 * (np.log(2 * np.pi * mv) + (y0 - m) ** 2 / mv)
        post_means.append(pm); post_vars.append(pv); log_ev.append(le)
    log_ev = np.array(log_ev); post_means = np.array(post_means); post_vars = np.array(post_vars)
    pw = np.exp(log_ev - log_ev.max()); pw /= pw.sum()
    mean = float((pw * post_means).sum())
    var = float((pw * (post_vars + post_means ** 2)).sum() - mean ** 2)
    return mean, np.sqrt(max(var, 1e-12))


# ----------------------------------------------------------------------------
# 2. Power prior  (Ibrahim & Chen 2000, Stat Sci 15:46; normalized/adaptive a0
#    Duan et al. 2006).  Historical (field prior) likelihood raised to a0 in [0,1].
# ----------------------------------------------------------------------------
def power_prior_fuse(y0, se0, mu_p, se_p, a0=None):
    """Fuse own (y0,se0) with field prior (mu_p,se_p). a0 fixed or adaptive
    (a0 = commensurability from prior-data agreement)."""
    if not np.isfinite(mu_p):
        return y0, se0
    if a0 is None:                      # adaptive a0 from conflict (bounded 0..1)
        Q = (y0 - mu_p) ** 2 / (se0 ** 2 + se_p ** 2)
        a0 = float(np.clip(np.exp(-0.5 * Q), 0.0, 1.0))
    p_own = 1.0 / se0 ** 2
    p_pri = a0 / se_p ** 2
    mu = (p_own * y0 + p_pri * mu_p) / (p_own + p_pri)
    return float(mu), float(np.sqrt(1.0 / (p_own + p_pri)))


# ----------------------------------------------------------------------------
# 3. Commensurate prior  (Hobbs et al. 2011, Biometrics 67:1047; 2012 Bayesian
#    Anal 7:639).  Commensurability parameter governs borrowing; spike near
#    agreement, slab under conflict.
# ----------------------------------------------------------------------------
def commensurate_fuse(y0, se0, mu_p, se_p):
    if not np.isfinite(mu_p):
        return y0, se0
    # commensurability tau_c^2 estimated from observed discrepancy (empirical Bayes):
    disc = (y0 - mu_p) ** 2 - (se0 ** 2 + se_p ** 2)
    tau_c2 = max(0.0, disc)                       # 0 => full borrow; large => none
    p_own = 1.0 / se0 ** 2
    p_pri = 1.0 / (se_p ** 2 + tau_c2)
    mu = (p_own * y0 + p_pri * mu_p) / (p_own + p_pri)
    return float(mu), float(np.sqrt(1.0 / (p_own + p_pri)))


# ----------------------------------------------------------------------------
# 4. SAM prior -- Self-Adapting Mixture  (Yang et al. 2023, Stat Med 42:2626).
#    Mixture weight from a likelihood ratio of prior-vs-vague at the own data.
# ----------------------------------------------------------------------------
def sam_fuse(y0, se0, mu_p, se_p, vague_scale=None):
    if not np.isfinite(mu_p):
        return y0, se0
    if vague_scale is None:
        vague_scale = 5.0 * (abs(mu_p) + se_p + 1.0)
    f_inf = norm.pdf(y0, mu_p, np.sqrt(se_p ** 2 + se0 ** 2))
    f_vag = norm.pdf(y0, mu_p, np.sqrt(vague_scale ** 2 + se0 ** 2))
    R = f_inf / (f_vag + 1e-300)
    w = R / (R + 1.0)                              # adaptive weight on informative
    means = np.array([mu_p, mu_p]); sds = np.array([se_p, vague_scale])
    wts = np.array([w, 1 - w])
    return mixture_posterior_mean(means, sds, wts, y0, se0)


# ----------------------------------------------------------------------------
# 5. Gaussian-process learned-kernel field  (Rasmussen & Williams 2006, GPML;
#    sklearn GaussianProcessRegressor).  Data-driven "gravity": ARD-RBF over
#    study covariates (year, log-precision, one-hot specialty & MA) with
#    per-point sampling-variance noise; hyper-parameters by marginal likelihood.
#    Exact leave-one-out via R&W eq. 5.12 (one fit per family).
# ----------------------------------------------------------------------------
def gp_features(sub):
    yr = sub["yz"].fillna(0.0).values
    lp = np.log(sub["prec"].values)
    lp = (lp - lp.mean()) / (lp.std() + 1e-9)
    spec = np.asarray(sub["specialty"].values)
    ma = np.asarray(sub["ma"].values)
    sp_oh = np.stack([(spec == s).astype(float) for s in np.unique(spec)], 1)
    ma_oh = np.stack([(ma == m).astype(float) for m in np.unique(ma)], 1)
    return np.column_stack([yr, lp, sp_oh, ma_oh])


def gp_field_loo(sub):
    """Return per-study LOO (mu, sd) arrays for one family (index-aligned to sub)."""
    X = gp_features(sub)
    y = sub["yi"].values.astype(float)
    alpha = (sub["se"].values ** 2).astype(float)
    ymean = y.mean()
    k = (ConstantKernel(1.0, (1e-2, 1e2))
         * RBF(length_scale=np.ones(X.shape[1]), length_scale_bounds=(1e-2, 1e3))
         + WhiteKernel(1e-3, (1e-6, 1e1)))
    gp = GaussianProcessRegressor(kernel=k, alpha=alpha, optimizer="fmin_l_bfgs_b",
                                  n_restarts_optimizer=1, normalize_y=False)
    gp.fit(X, y - ymean)
    K = gp.kernel_(X) + np.diag(alpha)
    Kinv = np.linalg.inv(K)
    a = Kinv @ (y - ymean)
    d = np.diag(Kinv)
    mu = (y - ymean) - a / d + ymean          # R&W 5.12 LOO mean
    sd = np.sqrt(1.0 / d)
    return mu, sd


def gp_field_kfold(sub, n_folds=10, seed=0):
    """HONEST GP check: refit hyper-parameters on each training fold (no shared-
    hyperparameter optimism), predict held-out fold. Returns index-aligned mu."""
    X = gp_features(sub); y = sub["yi"].values.astype(float)
    alpha = (sub["se"].values ** 2).astype(float)
    n = len(y); rng = np.random.default_rng(seed)
    order = rng.permutation(n); folds = np.array_split(order, n_folds)
    mu = np.full(n, np.nan)
    for te in folds:
        tr = np.setdiff1d(np.arange(n), te)
        ym = y[tr].mean()
        k = (ConstantKernel(1.0, (1e-2, 1e2))
             * RBF(np.ones(X.shape[1]), (1e-2, 1e3)) + WhiteKernel(1e-3, (1e-6, 1e1)))
        gp = GaussianProcessRegressor(kernel=k, alpha=alpha[tr], n_restarts_optimizer=0)
        gp.fit(X[tr], y[tr] - ym)
        mu[te] = gp.predict(X[te]) + ym
    return mu


# ----------------------------------------------------------------------------
# 6. g-modeling / NPMLE empirical Bayes  (Efron 2016, JASA 111:1131;
#    Koenker & Mizera 2014, JASA 109:674; deconvolveR/REBayes -- not installed).
#    Nonparametric prior g on a grid by EM; posterior mean shrinkage.
# ----------------------------------------------------------------------------
def npmle_g(y, se, grid=None, iters=300):
    y = np.asarray(y, float); se = np.asarray(se, float)
    if grid is None:
        lo, hi = y.min() - 2 * se.mean(), y.max() + 2 * se.mean()
        grid = np.linspace(lo, hi, 60)
    L = norm.pdf(y[:, None], grid[None, :], se[:, None]) + 1e-300
    pi = np.ones(len(grid)) / len(grid)
    for _ in range(iters):
        num = L * pi[None, :]
        r = num / num.sum(1, keepdims=True)
        pi = r.mean(0)
    return grid, pi


def gmodel_post_mean(grid, pi, y0, se0):
    """E[theta | y0] under prior (grid,pi)."""
    w = pi * norm.pdf(grid, y0, se0)
    if w.sum() <= 0:
        return float((grid * pi).sum())
    return float((grid * w).sum() / w.sum())


# ----------------------------------------------------------------------------
# 7. Hierarchical cross-MA empirical Bayes (nested partial pooling; the principled
#    Bayesian 'borrow across meta-analyses' backbone -- Gelman & Hill 2007 ch.12;
#    Higgins-Thompson-Spiegelhalter 2009 JRSS-A random-effects predictive).
#    Study within MA within family; MA means share a family hyperprior.
# ----------------------------------------------------------------------------
def hier_crossMA_predict(df, i):
    t = df.iloc[i]
    fam = df[(df.family == t.family)]
    # MA-level RE means (leave target out of its own MA)
    ma_means, ma_ses, ma_ids = [], [], []
    for ma, g in fam.groupby("ma"):
        gg = g.drop(index=i) if (ma == t.ma and i in g.index) else g
        if len(gg) == 0:
            continue
        _, mu_j, se_j = dl_tau2(gg["yi"].values, gg["se"].values)
        ma_means.append(mu_j); ma_ses.append(se_j); ma_ids.append(ma)
    ma_means = np.array(ma_means); ma_ses = np.array(ma_ses)
    # between-MA variance (MoM)
    w = 1.0 / ma_ses ** 2
    M = (w * ma_means).sum() / w.sum()
    Q = (w * (ma_means - M) ** 2).sum()
    c = w.sum() - (w ** 2).sum() / w.sum()
    tau_b2 = max(0.0, (Q - (len(ma_means) - 1)) / c) if c > 0 and len(ma_means) > 1 else 0.0
    # target MA mean, shrunk toward family mean M
    j = ma_ids.index(t.ma)
    B = tau_b2 / (tau_b2 + ma_ses[j] ** 2)                 # weight on own-MA mean
    mu_t = B * ma_means[j] + (1 - B) * M
    se_t = np.sqrt(B * ma_ses[j] ** 2 + (1 - B) ** 2 * (1.0 / w.sum()) + tau_b2 * (1 - B))
    return float(mu_t), float(max(se_t, 1e-6))
