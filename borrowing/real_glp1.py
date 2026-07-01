"""PILOT-2 real-data anchor (no simulation).

(1) Modifier-exists evidence: RE meta-regression of HbA1c effect on GLP1 dose,
    with a permutation test of the slope (truth-first: real reported effects).
(2) Leave-one-trial-out PREDICTIVE test on the real GLP1 dose field. For each
    held-out real trial t (the 'target', ZERO own data -> a pure transportability
    prediction), form a borrowing prior from the OTHER real trials, three ways:
      relevance (dose-distance kernel) / uniform (field mean) / scrambled.
    TRUTH = the trial's REAL observed effect y_t. Score |pred - y_t| and whether
    the prediction interval covers y_t. Paired bootstrap over the LOO folds.

This isolates the relevance kernel completely (no own-data dilution) on REAL
held-out effects -- the genuinely-real headline. The decisive matched-coverage
gate with controlled ground truth lives in sim_gate.py (calibrated to THESE
real parameters).
"""
import json, math, numpy as np
from borrowing_field2 import covariate_prior, Z975

GLP1 = [t for t in json.load(open("probe_trials.json"))
        if t["active"] == "GLP1" and t.get("dose") is not None]
x = np.array([t["dose"] for t in GLP1]); y = np.array([t["y"] for t in GLP1])
s = np.array([t["se"] for t in GLP1])
print(f"# Real GLP1 dose field: n={len(GLP1)} trials, dose range [{x.min():.2f},{x.max():.2f}] mg")


def re_slope(y, s, x, iters=80):
    """DL-ish RE meta-regression slope (WLS with moment tau2)."""
    tau2 = 0.0
    X = np.column_stack([np.ones_like(x), x])
    for _ in range(iters):
        w = 1.0 / (s ** 2 + tau2)
        WX = X * w[:, None]
        cov = np.linalg.inv(X.T @ WX); beta = cov @ (WX.T @ y)
        resid = y - X @ beta
        P = np.diag(w) - WX @ cov @ WX.T
        Q = float((w * resid ** 2).sum()); df = len(x) - 2
        trP = np.trace(P)
        tau2n = max(0.0, (Q - df) / trP) if trP > 0 else 0.0
        if abs(tau2n - tau2) < 1e-9:
            tau2 = tau2n; break
        tau2 = tau2n
    w = 1.0 / (s ** 2 + tau2); WX = X * w[:, None]
    cov = np.linalg.inv(X.T @ WX); beta = cov @ (WX.T @ y)
    return float(beta[1]), float(np.sqrt(cov[1, 1])), float(beta[0]), float(tau2)


slope, se_slope, intcpt, tau2 = re_slope(y, s, x)
ci = (slope - 1.96 * se_slope, slope + 1.96 * se_slope)
# permutation test of the slope: permute y vs x
rng = np.random.default_rng(20260630)
perm = np.array([abs(re_slope(y, s, rng.permutation(x))[0]) for _ in range(2000)])
pperm = float((perm >= abs(slope)).mean())
# residual tau2 vs unconditional tau2 (variance explained)
w0 = 1.0 / s ** 2; mu0 = (w0 * y).sum() / w0.sum()
Q0 = float((w0 * (y - mu0) ** 2).sum()); c0 = w0.sum() - (w0 ** 2).sum() / w0.sum()
tau2_0 = max(0.0, (Q0 - (len(x) - 1)) / c0) if c0 > 0 else 0.0
R2 = 1 - tau2 / tau2_0 if tau2_0 > 0 else 0.0
print(f"\n## (1) MODIFIER-EXISTS  (effect ~ dose, RE meta-regression)")
print(f"  slope = {slope:+.4f} %/mg   95% CI [{ci[0]:+.4f}, {ci[1]:+.4f}]   "
      f"Wald p={2*(1-0.5*(1+math.erf(abs(slope/se_slope)/2**.5))):.4g}")
print(f"  permutation p (2000) = {pperm:.4f}")
print(f"  between-trial var explained by dose R2 = {R2:.2f}  "
      f"(tau uncond={tau2_0**.5:.3f} -> cond={tau2**.5:.3f})")
print(f"  intercept(mu at 0 mg) = {intcpt:+.3f}")

# ---------- (2) LOO predictive test ----------
def loo(bw, mode, seed=1):
    errs, covered, preds = [], [], []
    rng = np.random.default_rng(seed)
    for i in range(len(GLP1)):
        m = np.ones(len(GLP1), bool); m[i] = False
        mu_p, se_p, ess = covariate_prior(x[i], x[m], y[m], s[m], bw, mode=mode, rng=rng)
        if not np.isfinite(mu_p):
            continue
        err = abs(mu_p - y[i])
        # prediction interval = prior uncertainty + held-out sampling se
        half = Z975 * np.sqrt(se_p ** 2 + s[i] ** 2)
        cov = (mu_p - half <= y[i] <= mu_p + half)
        errs.append(err); covered.append(cov); preds.append(mu_p)
    return np.array(errs), np.array(covered), np.array(preds)


def paired_boot(ea, eb, n=4000, seed=7):
    rng = np.random.default_rng(seed)
    d = ea - eb  # relevance - null ; want < 0 (relevance smaller error)
    bi = rng.integers(0, len(d), size=(n, len(d)))
    md = d[bi].mean(axis=1)
    lo, hi = np.quantile(md, [0.025, 0.975])
    return float(d.mean()), float(lo), float(hi), bool(hi < 0)


print(f"\n## (2) LOO PREDICTIVE TEST on real held-out effects (truth = real y_t)")
print(f"{'bw(mg)':>7}{'mode':>11}{'MAE':>8}{'cover':>7}   vs uniform: dMAE[95% CI]")
xsd = float(np.std(x))
for bw in [round(xsd / 2, 2), round(xsd, 2), round(1.5 * xsd, 2)]:
    er_rel, cv_rel, _ = loo(bw, "relevance")
    er_uni, cv_uni, _ = loo(bw, "uniform")
    er_scr, cv_scr, _ = loo(bw, "scrambled")
    d_ru, lo_ru, hi_ru, win_ru = paired_boot(er_rel, er_uni)
    d_rs, lo_rs, hi_rs, win_rs = paired_boot(er_rel, er_scr)
    print(f"{bw:>7}{'relevance':>11}{er_rel.mean():>8.3f}{cv_rel.mean():>7.2f}   "
          f"vs uniform {d_ru:+.3f}[{lo_ru:+.3f},{hi_ru:+.3f}]{'  WIN' if win_ru else ''}")
    print(f"{'':>7}{'uniform':>11}{er_uni.mean():>8.3f}{cv_uni.mean():>7.2f}")
    print(f"{'':>7}{'scrambled':>11}{er_scr.mean():>8.3f}{cv_scr.mean():>7.2f}   "
          f"rel vs scrambled {d_rs:+.3f}[{lo_rs:+.3f},{hi_rs:+.3f}]{'  WIN' if win_rs else ''}")

out = dict(n=len(GLP1), slope=slope, slope_ci=list(ci), perm_p=pperm, R2=R2,
           tau2_uncond=tau2_0, tau2_cond=tau2, intercept=intcpt,
           dose_range=[float(x.min()), float(x.max())], dose_sd=xsd)
json.dump(out, open("real_glp1_summary.json", "w"), indent=2)
print("\nwrote real_glp1_summary.json")
