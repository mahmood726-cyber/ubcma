"""INDEPENDENT from-scratch verification of the learned-kernel headline.

Reads ONLY corpus_full_1177.csv (no import of field_learned / field / corpus).
Re-implements the two predictors a DIFFERENT way from the primary build:
  * learned kernel  -> sklearn GaussianProcessRegressor with a ONE-HOT ARD-RBF
    kernel (per-category length scales), honest 10-fold refit -- a different kernel
    parameterisation and a different GP engine than the primary custom grouped-ARD
    GP. If both agree the learned kernel beats within-MA, the win is robust to the
    kernel/engine choice.
  * within-MA       -> inverse-variance + year-kernel pool of same-MA siblings.

This is the internal stand-in for the external Codex Seat A check when the laptop
is unreachable; the same spec is in LEARNED_VERIFY_TASK.md for the external run.
Run:  python borrowing/field_scale/verify_learned_independent.py
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel

HERE = Path(__file__).resolve().parent
df = pd.read_csv(HERE / "corpus_full_1177.csv")


def stdz(x):
    x = np.asarray(x, float)
    m = np.isfinite(x)
    if m.sum() < 2 or np.nanstd(x[m]) < 1e-9:
        return np.zeros_like(x)
    out = np.zeros_like(x)
    out[m] = (x[m] - np.nanmean(x[m])) / (np.nanstd(x[m]) + 1e-9)
    return out


def onehot_features(sub):
    yr = stdz(sub["year"].to_numpy())
    lp = stdz(np.log(1.0 / sub["se"].to_numpy() ** 2))
    spec = sub["specialty"].to_numpy()
    ma = sub["ma"].to_numpy()
    sp = np.stack([(spec == s).astype(float) for s in np.unique(spec)], 1)
    mm = np.stack([(ma == m).astype(float) for m in np.unique(ma)], 1)
    return np.column_stack([yr, lp, sp, mm])


def gp_kfold(sub, n_folds=10, seed=0):
    X = onehot_features(sub)
    y = sub["yi"].to_numpy(float)
    alpha = sub["se"].to_numpy(float) ** 2
    n = len(y)
    rng = np.random.default_rng(seed)
    folds = np.array_split(rng.permutation(n), min(n_folds, n))
    mu = np.full(n, np.nan)
    for te in folds:
        tr = np.setdiff1d(np.arange(n), te)
        if len(tr) < 2:
            continue
        ym = y[tr].mean()
        k = (ConstantKernel(1.0, (1e-2, 1e2))
             * RBF(np.ones(X.shape[1]), (1e-2, 1e3)) + WhiteKernel(1e-3, (1e-6, 1e1)))
        gp = GaussianProcessRegressor(kernel=k, alpha=alpha[tr], n_restarts_optimizer=0)
        gp.fit(X[tr], y[tr] - ym)
        mu[te] = gp.predict(X[te]) + ym
    return mu


def within_ma(sub):
    y = sub["yi"].to_numpy(float)
    se = sub["se"].to_numpy(float)
    ma = sub["ma"].to_numpy()
    yr = stdz(sub["year"].to_numpy())
    n = len(y)
    pred = np.full(n, np.nan)
    for i in range(n):
        sib = (ma == ma[i]) & (np.arange(n) != i)
        if sib.sum() == 0:
            continue
        w = 1.0 / se[sib] ** 2
        if np.isfinite(yr[i]):
            w = w * np.exp(-0.5 * ((yr[sib] - yr[i]) / 1.0) ** 2)
        if w.sum() <= 0:
            continue
        pred[i] = (w * y[sib]).sum() / w.sum()
    return pred


def pboot(a, b, n=5000, seed=7):
    m = np.isfinite(a) & np.isfinite(b)
    d = (a - b)[m]
    rng = np.random.default_rng(seed)
    bi = rng.integers(0, len(d), size=(n, len(d)))
    md = d[bi].mean(1)
    return float(d.mean()), float(np.quantile(md, 0.025)), float(np.quantile(md, 0.975)), int(len(d))


if __name__ == "__main__":
    n = len(df)
    gp = np.full(n, np.nan)
    wm = np.full(n, np.nan)
    per_fam = {}
    for fam, sub in df.groupby("family"):
        idx = sub.index.to_numpy()
        seeds = (0, 1, 2, 3, 4)
        mu = np.nanmean([gp_kfold(sub.reset_index(drop=True), seed=s) for s in seeds], 0)
        gp[idx] = mu
        wm[idx] = within_ma(sub.reset_index(drop=True))
        per_fam[fam] = float(np.nanmean(np.abs(mu - sub["yi"].to_numpy())))
    y = df["yi"].to_numpy()
    mae_gp = float(np.nanmean(np.abs(gp - y)))
    mae_wm = float(np.nanmean(np.abs(wm - y)))
    d, lo, hi, npair = pboot(np.abs(gp - y), np.abs(wm - y))
    out = dict(engine="sklearn one-hot ARD-RBF (independent)",
               nodes=n, MAs=int(df.ma.nunique()),
               learned_kernel_MAE=mae_gp, within_MA_MAE=mae_wm,
               per_family_learned_MAE=per_fam,
               learned_minus_within=dict(delta=d, lo=lo, hi=hi, n=npair))
    print(json.dumps(out, indent=2))
    print("\nVERDICT:", "learned kernel BEATS within-MA (CI<0)" if hi < 0
          else ("within-MA better" if lo > 0 else "n.s."))
    json.dump(out, open(HERE / "verify_learned_independent.json", "w"), indent=2)
