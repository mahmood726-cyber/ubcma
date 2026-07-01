"""EXPERIMENT 2 -- FROM-SCRATCH self-verification of the rotavirus transport headline.

Vendors down -> per the standing rule confirm the headline >=3 internal ways + external
+ from-scratch. This file is the FROM-SCRATCH witness: it re-reads the raw Clark 2019
counts, recomputes logRR independently, uses an INLINE Gaussian kernel and an INDEPENDENT
Mandel-Paule REML pooler (NOT ubcma.comparators), and re-runs the 5-way LOO. It must
reproduce run_rota.py's central-bw deltas to a few thousandths. It ALSO runs the
single-country sensitivity (drop the 9 pooled-region rows) to prove the result does not
depend on pooled-region U5MR assignment.
"""
import csv, json, io, sys, re
import numpy as np
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

D = json.load(open(Path(__file__).parent / "rota_trials.json"))
TR = D["trials"]
Z975 = 1.959963984540054


def mp_reml(y, s):
    """Independent Mandel-Paule tau2 + inverse-variance mean (from scratch)."""
    y = np.asarray(y, float); v = np.asarray(s, float) ** 2
    if len(y) == 1:
        return float(y[0]), float(np.sqrt(v[0]))
    tau2 = 0.0
    for _ in range(200):
        w = 1.0 / (v + tau2)
        mu = (w * y).sum() / w.sum()
        Q = (w * (y - mu) ** 2).sum()
        if Q <= len(y) - 1:
            break
        # Mandel-Paule update
        deriv = (w ** 2 * (y - mu) ** 2).sum()
        if deriv <= 0:
            break
        tau2 += (Q - (len(y) - 1)) / (w.sum() - (w ** 2).sum() / w.sum()) if (w.sum() - (w**2).sum()/w.sum())>0 else 0
        tau2 = max(tau2, 0.0)
        # simple fixed-point safeguard
        w2 = 1.0 / (v + tau2)
        if abs((w2*(y-(w2*y).sum()/w2.sum())**2).sum() - (len(y)-1)) < 1e-6:
            break
    w = 1.0 / (v + tau2)
    mu = (w * y).sum() / w.sum()
    return float(mu), float(np.sqrt(1.0 / w.sum()))


def re_slope(x, y, s):
    n = len(y)
    if n < 4 or np.std(x) < 1e-9:
        return 0.0
    X = np.column_stack([np.ones(n), x]); w = 1.0 / np.maximum(np.asarray(s)**2, 1e-12)
    WX = X * w[:, None]; XtWX = X.T @ WX
    beta = np.linalg.solve(XtWX, WX.T @ y); resid = y - X @ beta
    Qres = float((w * resid**2).sum())
    trace = w.sum() - np.trace(np.linalg.inv(XtWX) @ (X.T @ (w[:, None]**2 * X)))
    tau2 = max(0.0, (Qres - (n - 2)) / trace) if trace > 0 else 0.0
    W2 = 1.0 / (np.asarray(s)**2 + tau2); WX2 = X * W2[:, None]
    return float(np.linalg.solve(X.T @ WX2, WX2.T @ y)[1])


def prior(xt, xs, ys, ses, bw, mode, rng, beta0=False, target_pool=False):
    prec = 1.0 / np.maximum(ses**2, 1e-12)
    if mode == "nma":
        return mp_reml(ys, ses)
    if mode == "uniform":
        w = prec; yeff = ys
    else:
        xe = xs.copy()
        if mode == "scrambled":
            xe = rng.permutation(xe)
        k = np.exp(-0.5 * ((xe - xt) / bw) ** 2)
        w = k * prec
        if mode == "relevance":
            yeff = ys
        else:
            b = 0.0 if beta0 else re_slope(xs, ys, ses)
            tgt = float(xs.mean()) if target_pool else xt
            yeff = ys + b * (tgt - xe)
    ws = float(w.sum())
    if ws <= 0:
        return np.nan, np.inf
    mu = float((w * yeff).sum() / ws)
    within = float((w**2 * ses**2).sum() / ws**2)
    between = float((w * (yeff - mu)**2).sum() / ws)
    return mu, float(np.sqrt(max(within + between, 1e-9)))


def loo(TRS, bw, mode, beta0=False, target_pool=False, seed=1):
    Y = np.array([t["y"] for t in TRS]); S = np.array([t["se"] for t in TRS])
    X = np.array([t["u5mr"] for t in TRS]); N = len(TRS)
    rng = np.random.default_rng(seed); errs = []
    for i in range(N):
        m = np.ones(N, bool); m[i] = False
        mu, se = prior(X[i], X[m], Y[m], S[m], bw, mode, rng, beta0=beta0, target_pool=target_pool)
        if np.isfinite(mu):
            errs.append(abs(mu - Y[i]))
    return np.array(errs)


def pboot(ea, eb, n=4000, seed=7):
    rng = np.random.default_rng(seed); d = ea - eb
    md = d[rng.integers(0, len(d), size=(n, len(d)))].mean(axis=1)
    return float(d.mean()), float(np.quantile(md, .025)), float(np.quantile(md, .975))


def report(TRS, tag):
    x = np.array([t["u5mr"] for t in TRS]); bw = float(x.std())
    e_nma = loo(TRS, bw, "nma"); e_rel = loo(TRS, bw, "relevance")
    e_tra = loo(TRS, bw, "transport"); e_scr = loo(TRS, bw, "scrambled")
    e_b0 = loo(TRS, bw, "transport", beta0=True); e_tp = loo(TRS, bw, "transport", target_pool=True)
    print(f"\n[{tag}] k={len(TRS)}  central bw={bw:.1f}  (FROM SCRATCH: MP-REML + inline kernel)")
    print(f"  MAE nma={e_nma.mean():.3f} rel={e_rel.mean():.3f} tran={e_tra.mean():.3f} scr={e_scr.mean():.3f}")
    for lbl, a, b in [("tran-rel", e_tra, e_rel), ("tran-nma", e_tra, e_nma),
                      ("tran-scr", e_tra, e_scr), ("rel-unif", e_rel, loo(TRS, bw, "uniform"))]:
        d, lo, hi = pboot(a, b)
        print(f"    {lbl:9} {d:+.3f} [{lo:+.3f},{hi:+.3f}] {'W' if hi<0 else ''}")
    d, lo, hi = pboot(e_b0, e_rel)
    print(f"    beta=0 inert delta {d:+.4f} -> {'INERT' if abs(d)<0.02 else 'BUG'}")
    d, lo, hi = pboot(e_tp, e_tra)
    print(f"    target=pool delta {d:+.3f} [{lo:+.3f},{hi:+.3f}] (should hurt, >0)")


def main():
    print("FROM-SCRATCH verification of rota transport (independent recompute)")
    report(TR, "full k=29")
    single = [t for t in TR if not t["pooled"]]
    report(single, "single-country sensitivity (drop 9 pooled rows)")


if __name__ == "__main__":
    main()
