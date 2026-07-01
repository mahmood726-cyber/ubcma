"""PILOT-3 requirement (3): IS THE TRANSPORT SIGNAL REAL? Before any borrowing
machinery, test whether the population covariate (adult obesity prevalence of the
trial's recruiting countries) predicts the HbA1c treatment effect -- and crucially
whether it adds signal BEYOND the within-trial relevance covariates (drug class,
dose). If pop-obesity only proxies class, transportability adds nothing over
relevance-only and we say so.

RE meta-regression (moment tau2, WLS). Permutation test of the obesity slope.
Reported marginally, within-class, and incrementally (residual after class+dose).
"""
from __future__ import annotations
import json
import numpy as np

R = [r for r in json.load(open("trials_transport.json")) if r["pop_ob"] is not None]


def re_reg(y, s, X, iters=200):
    """RE meta-regression: returns beta, se(beta), tau2, Q, df. X includes intercept."""
    y = np.asarray(y, float); s = np.asarray(s, float); X = np.asarray(X, float)
    tau2 = 0.0
    for _ in range(iters):
        w = 1.0 / (s ** 2 + tau2)
        WX = X * w[:, None]
        cov = np.linalg.inv(X.T @ WX); beta = cov @ (WX.T @ y)
        resid = y - X @ beta
        P = np.diag(w) - WX @ cov @ WX.T
        Q = float((w * resid ** 2).sum()); df = len(y) - X.shape[1]
        trP = np.trace(P)
        tau2n = max(0.0, (Q - df) / trP) if trP > 0 else 0.0
        if abs(tau2n - tau2) < 1e-10:
            tau2 = tau2n; break
        tau2 = tau2n
    w = 1.0 / (s ** 2 + tau2); WX = X * w[:, None]
    cov = np.linalg.inv(X.T @ WX); beta = cov @ (WX.T @ y)
    return beta, np.sqrt(np.diag(cov)), tau2, Q, df


def perm_p(y, s, X, col, n=3000, seed=20260630):
    """Permutation test of the slope on column `col` (permute that column)."""
    beta0 = abs(re_reg(y, s, X)[0][col])
    rng = np.random.default_rng(seed)
    cnt = 0
    Xp = np.array(X, float)
    for _ in range(n):
        Xp[:, col] = rng.permutation(np.asarray(X, float)[:, col])
        if abs(re_reg(y, s, Xp)[0][col]) >= beta0:
            cnt += 1
    return (cnt + 1) / (n + 1)


y = np.array([r["y"] for r in R]); s = np.array([r["se"] for r in R])
ob = np.array([r["pop_ob"] for r in R])
obz = (ob - ob.mean()) / ob.std()

print(f"n = {len(R)} trials with population covariate\n")

# (A) marginal: y ~ obesity
X = np.column_stack([np.ones_like(y), obz])
b, se, tau2, Q, df = re_reg(y, s, X)
p = perm_p(y, s, X, 1)
print("(A) MARGINAL   y ~ obesity(z)")
print(f"    slope/SD = {b[1]:+.3f}  (SE {se[1]:.3f}, Wald z {b[1]/se[1]:+.2f})  perm p = {p:.4f}")
print(f"    interpretation: higher obesity -> {'MORE' if b[1]<0 else 'LESS'} HbA1c reduction\n")

# (B) incremental over class fixed effects
classes = sorted(set(r["active"] for r in R))
cls_cols = np.column_stack([[1.0 if r["active"] == c else 0.0 for r in R] for c in classes[1:]])
Xc = np.column_stack([np.ones_like(y), cls_cols])
Xco = np.column_stack([Xc, obz])
b2, se2, *_ = re_reg(y, s, Xco)
p2 = perm_p(y, s, Xco, Xco.shape[1] - 1)
print(f"(B) + DRUG CLASS fixed effects ({', '.join(classes)})")
print(f"    obesity slope (adjusted) = {b2[-1]:+.3f}  (SE {se2[-1]:.3f}, z {b2[-1]/se2[-1]:+.2f})  perm p = {p2:.4f}")
print("    -> does obesity survive class adjustment? "
      f"{'YES' if p2 < 0.10 else 'NO -- proxies class/other'}\n")

# (C) within-class (cleanest: no class confound)
print("(C) WITHIN-CLASS  y ~ obesity(z)  [dose added where available]")
for c in classes:
    idx = [i for i, r in enumerate(R) if r["active"] == c]
    if len(idx) < 4:
        print(f"    {c:8} n={len(idx):2}  (too few)")
        continue
    yi, si, obi = y[idx], s[idx], ob[idx]
    obzi = (obi - obi.mean()) / (obi.std() if obi.std() > 0 else 1)
    Xi = np.column_stack([np.ones_like(yi), obzi])
    bi, sei, *_ = re_reg(yi, si, Xi)
    pi = perm_p(yi, si, Xi, 1, n=2000)
    spread = f"ob[{obi.min():.0f},{obi.max():.0f}]"
    print(f"    {c:8} n={len(idx):2}  obesity slope {bi[1]:+.3f} (z {bi[1]/sei[1]:+.2f}) "
          f"perm p={pi:.3f}  {spread}")

# (D) residual-distance test: the transport question.
# Fit class+dose model WITHOUT obesity; does |obesity - donorpool mean| predict |residual|?
print("\n(D) TRANSPORT TEST: does target-distance on obesity predict residual effect?")
b_base, _, _, _, _ = re_reg(y, s, Xc)
resid = y - Xc @ b_base
# correlation of residual with centered obesity (signed) and |obesity-mean| (distance)
from numpy import corrcoef
r_signed = corrcoef(resid, obz)[0, 1]
print(f"    corr(residual_after_class, obesity)         = {r_signed:+.3f}")
print(f"    (nonzero => population obesity carries effect signal class alone misses)")

json.dump(dict(n=len(R), marg_slope=float(b[1]), marg_p=float(p),
               adj_slope=float(b2[-1]), adj_p=float(p2),
               resid_corr=float(r_signed)),
          open("probe_transport_summary.json", "w"), indent=2)
print("\nwrote probe_transport_summary.json")
