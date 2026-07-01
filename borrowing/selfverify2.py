"""INDEPENDENT re-derivation of the pilot-2 headline, sharing NO functions with
real_glp1.py / borrowing_field2.py. Reads only probe_trials.json. Confirms:
  (i)  GLP1 dose predicts effect (OLS + WLS slope, both signs/CI),
  (ii) LOO pure-prior: dose-relevance-weighted prediction beats the uniform
       (field-mean) and scrambled priors on REAL held-out effects.
A second pair of eyes on the decisive numbers (truth = real observed effects).
"""
import json, numpy as np

T = [t for t in json.load(open("probe_trials.json"))
     if t["active"] == "GLP1" and t.get("dose") is not None]
x = np.array([t["dose"] for t in T]); y = np.array([t["y"] for t in T])
s = np.array([t["se"] for t in T]); n = len(T)

# (i) plain OLS slope (no weighting) + inverse-variance WLS slope -- independent path
def ols(x, y):
    X = np.column_stack([np.ones_like(x), x])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ b
    s2 = (resid @ resid) / (len(x) - 2)
    cov = s2 * np.linalg.inv(X.T @ X)
    return b[1], np.sqrt(cov[1, 1])
b_ols, se_ols = ols(x, y)
w = 1 / s ** 2
X = np.column_stack([np.ones_like(x), x]); WX = X * w[:, None]
cov = np.linalg.inv(X.T @ WX); b_wls = (cov @ (WX.T @ y))[1]; se_wls = np.sqrt(cov[1, 1])
print(f"(i) GLP1 dose->effect  OLS slope={b_ols:+.4f} (z={b_ols/se_ols:+.2f})  "
      f"WLS slope={b_wls:+.4f} (z={b_wls/se_wls:+.2f})  [both negative & |z|>2 => real]")

# (ii) LOO pure-prior prediction, recomputed inline (Gaussian dose kernel)
def loo_mae(bw, mode, seed=0):
    rng = np.random.default_rng(seed); errs = []
    for i in range(n):
        idx = [j for j in range(n) if j != i]
        xx = x[idx].copy(); yy = y[idx]; ss = s[idx]
        prec = 1 / ss ** 2
        if mode == "uniform":
            wt = prec
        else:
            if mode == "scrambled":
                xx = rng.permutation(xx)
            wt = np.exp(-0.5 * ((xx - x[i]) / bw) ** 2) * prec
        pred = (wt * yy).sum() / wt.sum()
        errs.append(abs(pred - y[i]))
    return np.array(errs)

bw = float(np.std(x))
er = loo_mae(bw, "relevance"); eu = loo_mae(bw, "uniform"); es = loo_mae(bw, "scrambled")
def boot(a, b, seed=11, nb=4000):
    rng = np.random.default_rng(seed); d = a - b
    bi = rng.integers(0, len(d), size=(nb, len(d)))
    lo, hi = np.quantile(d[bi].mean(1), [.025, .975])
    return d.mean(), lo, hi
for name, e in [("relevance", er), ("uniform", eu), ("scrambled", es)]:
    print(f"(ii) bw={bw:.2f}  {name:10} LOO-MAE={e.mean():.3f}")
d1, l1, h1 = boot(er, eu); d2, l2, h2 = boot(er, es)
print(f"     relevance - uniform   = {d1:+.3f} [{l1:+.3f},{h1:+.3f}]  "
      f"{'WIN' if h1 < 0 else 'n.s.'}")
print(f"     relevance - scrambled = {d2:+.3f} [{l2:+.3f},{h2:+.3f}]  "
      f"{'WIN' if h2 < 0 else 'n.s.'}")
