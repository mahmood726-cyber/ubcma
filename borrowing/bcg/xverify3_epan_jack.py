"""THIRD internal path for the dat.bcg transport headline -- methodologically distinct
from run_bcg.py (Gaussian kernel, paired bootstrap) and selfverify_bcg.py (Gaussian,
bootstrap, Mandel-Paule). Here: EPANECHNIKOV kernel + delete-1 JACKKNIFE CI (no
bootstrap). Robustness of the transport-vs-NMA / transport-vs-relevance signs to
kernel shape AND resampling method. Recomputes logRR from raw 2x2 inline.
"""
import csv, io, sys, numpy as np
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
SRC = Path(r"F:\public-data\metadat\dat.bcg.csv")
Y, S, LAT = [], [], []
for r in csv.DictReader(open(SRC)):
    a, b = float(r["tpos"]), float(r["tneg"]); c, d = float(r["cpos"]), float(r["cneg"])
    Y.append(np.log((a/(a+b))/(c/(c+d)))); S.append(np.sqrt(1/a-1/(a+b)+1/c-1/(c+d)))
    LAT.append(float(r["ablat"]))
Y = np.array(Y); S = np.array(S); LAT = np.array(LAT); N = len(Y)


def re_slope(lat, y, s):
    n = len(y)
    if n < 4 or np.std(lat) < 1e-9: return 0.0
    X = np.column_stack([np.ones(n), lat]); w = 1/np.maximum(s**2, 1e-12)
    WX = X*w[:, None]; XtWX = X.T@WX; beta = np.linalg.solve(XtWX, WX.T@y)
    resid = y-X@beta; Qres = float((w*resid**2).sum())
    trace = w.sum()-np.trace(np.linalg.inv(XtWX)@(X.T@(w[:, None]**2*X)))
    tau2 = max(0.0, (Qres-(n-2))/trace) if trace > 0 else 0.0
    W2 = 1/(s**2+tau2); WX2 = X*W2[:, None]
    return float(np.linalg.solve(X.T@WX2, WX2.T@y)[1])


def dl_pool(y, s):  # DerSimonian-Laird RE pool for the NMA arm (3rd distinct pooler)
    if len(y) == 1: return float(y[0])
    w = 1/s**2; mu = (w*y).sum()/w.sum(); Q = (w*(y-mu)**2).sum()
    c = w.sum()-(w**2).sum()/w.sum(); tau2 = max(0.0, (Q-(len(y)-1))/c) if c > 0 else 0.0
    w2 = 1/(s**2+tau2); return float((w2*y).sum()/w2.sum())


def epan(u):  # Epanechnikov kernel (compact support) -- different shape from Gaussian
    return np.maximum(1-u**2, 0.0)


def pred(xt, xs, ys, ses, bw, mode):
    prec = 1/np.maximum(ses**2, 1e-12)
    if mode == "nma": return dl_pool(ys, ses)
    if mode == "uniform": w, yeff = prec, ys
    else:
        w = epan((xs-xt)/(1.6*bw))*prec  # widen support so >=2 donors contribute
        if w.sum() <= 0: w = prec
        if mode == "relevance": yeff = ys
        else:
            b = re_slope(xs, ys, ses); yeff = ys + b*(xt-xs)
    ws = w.sum()
    return float((w*yeff).sum()/ws) if ws > 0 else np.nan


def loo_errs(bw, mode):
    e = []
    for i in range(N):
        m = np.ones(N, bool); m[i] = False
        mu = pred(LAT[i], LAT[m], Y[m], S[m], bw, mode)
        if np.isfinite(mu): e.append(abs(mu-Y[i]))
    return np.array(e)


def jackknife_ci(ea, eb):
    """Delete-1 jackknife CI for mean(ea-eb)."""
    d = ea-eb; n = len(d); thetahat = d.mean()
    loo = np.array([np.delete(d, i).mean() for i in range(n)])
    ps = n*thetahat - (n-1)*loo
    se = np.sqrt(ps.var(ddof=1)/n)
    return thetahat, thetahat-1.96*se, thetahat+1.96*se


bw = float(LAT.std())
print(f"3RD PATH (Epanechnikov kernel + jackknife CI, DL pooler), n={N}, bw=SD={bw:.3f}:")
e_nma = loo_errs(bw, "nma"); e_uni = loo_errs(bw, "uniform")
e_rel = loo_errs(bw, "relevance"); e_tra = loo_errs(bw, "transport")
print(f"  MAE nma={e_nma.mean():.3f} uni={e_uni.mean():.3f} rel={e_rel.mean():.3f} tran={e_tra.mean():.3f}")
for tag, ea, eb in [("tran-rel", e_tra, e_rel), ("tran-nma", e_tra, e_nma),
                    ("rel-unif", e_rel, e_uni)]:
    d, lo, hi = jackknife_ci(ea, eb)
    print(f"  {tag:9} {d:+.3f} [{lo:+.3f},{hi:+.3f}]  {'WIN' if hi < 0 else 'n.s.'}")
print("  -> sign of tran-nma (transport beats NMA) and tran-rel (n.s. margin) must match run_bcg.py")
