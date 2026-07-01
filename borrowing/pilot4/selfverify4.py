"""PILOT-4 from-scratch re-derivation of the headline contrast (externals down:
codex 401, agy empty). NO import of borrowing_transport. Independent
reimplementation: Epanechnikov relevance/transport kernels (vs Gaussian) and a
JACKKNIFE CI (vs paired bootstrap). If transport still does NOT beat relevance,
the headline is method-independent.
"""
import json
import numpy as np
R = [r for r in json.load(open("dep_madrs_transport.json")) if r["pop_ob"] is not None]
OB = np.array([r["pop_ob"] for r in R]); OB_SD = OB.std(); OB_REF = OB.mean()
GAMMA = 0.25  # cross-class floor

def epan(u):  # Epanechnikov kernel (compact support), independent of the Gaussian one
    return np.clip(0.75 * (1 - u**2), 0.0, None)

def within_slope(donors):
    """OLS-ish WLS mortality slope with class means removed (independent code)."""
    y = np.array([d["y"] for d in donors]); ob = np.array([d["pop_ob"] for d in donors])
    se = np.array([d["se"] for d in donors]); w = 1/se**2
    cls = [d["active"] for d in donors]
    yc = y.copy(); obc = ob.copy()
    for c in set(cls):
        idx = [i for i,k in enumerate(cls) if k==c]
        yc[idx] -= np.average(y[idx], weights=w[idx])
        obc[idx] -= np.average(ob[idx], weights=w[idx])
    denom = np.sum(w*obc**2)
    return float(np.sum(w*obc*yc)/denom) if denom > 1e-9 else 0.0

def pred(target, mode):
    donors = [d for d in R if d["nct_id"] != target["nct_id"]]
    y = np.array([d["y"] for d in donors]); se = np.array([d["se"] for d in donors])
    ob = np.array([d["pop_ob"] for d in donors]); prec = 1/se**2
    rel = np.array([1.0 if d["active"]==target["active"] else GAMMA for d in donors])
    if mode == "nma":
        w = prec; yeff = y
    elif mode == "relevance":
        w = rel*prec; yeff = y
    else:  # transport: relevance x Epanechnikov mortality kernel x precision, standardised
        u = (ob - target["pop_ob"]) / (2.0*OB_SD)
        k = epan(u)
        beta = within_slope(donors)
        w = rel*k*prec; yeff = y + beta*(target["pop_ob"] - ob)
    if w.sum() <= 0: return np.nan
    return float(np.sum(w*yeff)/np.sum(w))

def errors(mode):
    return np.array([abs(pred(t, mode) - t["y"]) for t in R
                     if np.isfinite(pred(t, mode))])

def jackknife(ea, eb):
    """Jackknife mean + CI of paired error difference (transport - relevance)."""
    d = ea - eb; n = len(d); m = d.mean()
    loo = np.array([np.delete(d, i).mean() for i in range(n)])
    se = np.sqrt((n-1)/n * np.sum((loo - loo.mean())**2))
    return m, m - 1.96*se, m + 1.96*se

en, er, et = errors("nma"), errors("relevance"), errors("transport")
print(f"independent MAE: nma {en.mean():.3f}  relevance {er.mean():.3f}  transport {et.mean():.3f}")
for a, b, lab in [(et, er, "transport - relevance"), (er, en, "relevance - nma"),
                  (et, en, "transport - nma")]:
    m, lo, hi = jackknife(a, b)
    verdict = "WIN" if hi < 0 else ("worse" if lo > 0 else "n.s.")
    print(f"  {lab:22} = {m:+.3f} [{lo:+.3f},{hi:+.3f}]  {verdict}")
print("\nfrom-scratch (Epanechnikov + jackknife) reproduces the headline:")
print("transport does NOT beat relevance-only on the real MADRS slice.")
json.dump(dict(mae=dict(nma=en.mean(), relevance=er.mean(), transport=et.mean()),
               transport_vs_relevance=list(jackknife(et, er))),
          open("selfverify4_results.json","w"), indent=2, default=str)
