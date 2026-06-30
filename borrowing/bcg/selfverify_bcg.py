"""FROM-SCRATCH independent re-derivation of the dat.bcg transport headline.

NO imports of ubcma / borrowing_transport / run_bcg. Everything recomputed inline
from the raw dat.bcg.csv 2x2 cells: logRR, an independent Mandel-Paule REML pool
(NMA arm), inline latitude kernel, inline LOO-safe RE meta-reg slope, inline
standardisation shift, inline paired bootstrap. Must reproduce run_bcg.py to ~2dp.
(Vendor cross-check substitute / second code path.)
"""
import csv, io, sys, numpy as np
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
SRC = Path(r"F:\public-data\metadat\dat.bcg.csv")
Z = 1.959963984540054

# (re)build logRR + SE straight from the 2x2 -- independent of prep_bcg.py
Y, S, LAT = [], [], []
for r in csv.DictReader(open(SRC)):
    a, b = float(r["tpos"]), float(r["tneg"]); c, d = float(r["cpos"]), float(r["cneg"])
    Y.append(np.log((a/(a+b))/(c/(c+d))))
    S.append(np.sqrt(1/a - 1/(a+b) + 1/c - 1/(c+d)))
    LAT.append(float(r["ablat"]))
Y = np.array(Y); S = np.array(S); LAT = np.array(LAT); N = len(Y)


def reml_mp(y, s):
    """Mandel-Paule random-effects pooled mean (independent of ubcma.reml)."""
    if len(y) == 1:
        return float(y[0]), float(s[0])
    tau2 = 0.0
    for _ in range(200):
        w = 1.0 / (s**2 + tau2); mu = (w*y).sum()/w.sum()
        Q = (w*(y-mu)**2).sum()
        if abs(Q - (len(y)-1)) < 1e-8:
            break
        # Newton step on Q(tau2) = k-1
        dQ = -(((w**2)*(y-mu)**2).sum())
        tau2 = max(0.0, tau2 - (Q-(len(y)-1))/dQ) if dQ != 0 else tau2
    w = 1.0/(s**2+tau2); mu = (w*y).sum()/w.sum()
    return float(mu), float(np.sqrt(1.0/w.sum()))


def re_slope(lat, y, s):
    n = len(y)
    if n < 4 or np.std(lat) < 1e-9:
        return 0.0
    X = np.column_stack([np.ones(n), lat]); w = 1.0/np.maximum(s**2, 1e-12)
    WX = X*w[:, None]; XtWX = X.T@WX
    beta = np.linalg.solve(XtWX, WX.T@y); resid = y - X@beta
    Qres = float((w*resid**2).sum())
    trace = w.sum() - np.trace(np.linalg.inv(XtWX)@(X.T@(w[:, None]**2*X)))
    tau2 = max(0.0, (Qres-(n-2))/trace) if trace > 0 else 0.0
    W2 = 1.0/(s**2+tau2); WX2 = X*W2[:, None]
    return float(np.linalg.solve(X.T@WX2, WX2.T@y)[1])


def prior(xt, xs, ys, ses, bw, mode, rng, beta0=None, tgt=None):
    prec = 1.0/np.maximum(ses**2, 1e-12)
    if mode == "nma":
        return reml_mp(ys, ses)[0]
    if mode == "uniform":
        w = prec; yeff = ys
    else:
        xe = rng.permutation(xs) if mode == "scrambled" else xs.copy()
        w = np.exp(-0.5*((xe-xt)/bw)**2)*prec
        if mode == "relevance":
            yeff = ys
        else:
            b = beta0 if beta0 is not None else re_slope(xs, ys, ses)
            t = xt if tgt is None else tgt
            yeff = ys + b*(t - xe)
    ws = w.sum()
    return float((w*yeff).sum()/ws) if ws > 0 else np.nan


def loo_mae(bw, mode, beta0=None, target_pool=False, seed=1):
    rng = np.random.default_rng(seed); e = []
    for i in range(N):
        m = np.ones(N, bool); m[i] = False
        tgt = float(LAT[m].mean()) if target_pool else None
        mu = prior(LAT[i], LAT[m], Y[m], S[m], bw, mode, rng, beta0=beta0, tgt=tgt)
        if np.isfinite(mu):
            e.append(abs(mu-Y[i]))
    return np.array(e)


def boot(ea, eb, n=4000, seed=7):
    rng = np.random.default_rng(seed); d = ea-eb
    bi = rng.integers(0, len(d), size=(n, len(d))); md = d[bi].mean(axis=1)
    return d.mean(), np.quantile(md, .025), np.quantile(md, .975)


bw = float(LAT.std())
print(f"FROM-SCRATCH dat.bcg (n={N}, bw=SD={bw:.3f}, full-set RE slope={re_slope(LAT,Y,S):+.4f}):")
e_nma = loo_mae(bw, "nma"); e_uni = loo_mae(bw, "uniform")
e_rel = loo_mae(bw, "relevance"); e_tra = loo_mae(bw, "transport"); e_scr = loo_mae(bw, "scrambled")
print(f"  MAE  nma={e_nma.mean():.3f} uni={e_uni.mean():.3f} rel={e_rel.mean():.3f} "
      f"tran={e_tra.mean():.3f} scr={e_scr.mean():.3f}")
for tag, ea, eb in [("tran-rel", e_tra, e_rel), ("tran-nma", e_tra, e_nma),
                    ("tran-scr", e_tra, e_scr), ("rel-unif", e_rel, e_uni)]:
    d, lo, hi = boot(ea, eb)
    print(f"  {tag:9} {d:+.3f} [{lo:+.3f},{hi:+.3f}]  {'WIN' if hi < 0 else 'n.s.'}")
e_b0 = loo_mae(bw, "transport", beta0=0.0)
e_tp = loo_mae(bw, "transport", target_pool=True)
print(f"  CONTROL beta=0 inertia: MAE {e_b0.mean():.3f} (=rel {e_rel.mean():.3f}? "
      f"delta {boot(e_b0,e_rel)[0]:+.4f})")
d, lo, hi = boot(e_tp, e_tra)
print(f"  CONTROL target=pool: MAE {e_tp.mean():.3f} vs real {e_tra.mean():.3f} "
      f"delta {d:+.3f}[{lo:+.3f},{hi:+.3f}]")
