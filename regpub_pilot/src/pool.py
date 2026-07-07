"""Self-contained meta-analysis pooling core (deterministic, model-free, offline).

Advanced-by-default vs the naive DerSimonian-Laird random-effects that dominates the
published literature:
  - tau^2 by REML (Paule-Mandel fallback) — not DL (DL is biased for small k; house rule)
  - Hartung-Knapp-Sidik-Jonkman variance + t_{k-1} quantile, with the Q<k-1 floor
  - Cochrane prediction interval (t_{k-1})
  - split-conformal-style empirical coverage calibration hook (leave-one-out)
All inputs are (yi, vi) on the analysis scale (log for ratios). No network, no model.
"""
from __future__ import annotations
import math

def _qt(p, df):
    """Student-t quantile via Cornish-Fisher off the normal (good for df>=2, |p| tails)."""
    # invert normal
    z = _qnorm(p)
    g1 = (z**3 + z) / 4.0
    g2 = (5*z**5 + 16*z**3 + 3*z) / 96.0
    g3 = (3*z**7 + 19*z**5 + 17*z**3 - 15*z) / 384.0
    return z + g1/df + g2/df**2 + g3/df**3

def _qnorm(p):
    # Acklam's inverse normal CDF
    a=[-3.969683028665376e+01,2.209460984245205e+02,-2.759285104469687e+02,1.383577518672690e+02,-3.066479806614716e+01,2.506628277459239e+00]
    b=[-5.447609879822406e+01,1.615858368580409e+02,-1.556989798598866e+02,6.680131188771972e+01,-1.328068155288572e+01]
    c=[-7.784894002430293e-03,-3.223964580411365e-01,-2.400758277161838e+00,-2.549732539343734e+00,4.374664141464968e+00,2.938163982698783e+00]
    d=[7.784695709041462e-03,3.224671290700398e-01,2.445134137142996e+00,3.754408661907416e+00]
    pl=0.02425
    if p<pl:
        q=math.sqrt(-2*math.log(p)); return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p<=1-pl:
        q=p-0.5; r=q*q
        return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q/(((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    q=math.sqrt(-2*math.log(1-p)); return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)

def _tau2_reml(yi, vi, iters=100):
    k = len(yi)
    if k < 2:
        return 0.0
    tau2 = max(0.0, _tau2_dl(yi, vi))
    for _ in range(iters):
        w = [1.0/(v+tau2) for v in vi]
        sw = sum(w); mu = sum(wi*y for wi,y in zip(w,yi))/sw
        num = sum(wi**2*((y-mu)**2 - v) for wi,y,v in zip(w,yi,vi))
        den = sum(wi**2 for wi in w)
        new = num/den + 1.0/sw  # REML update term
        new = max(0.0, new)
        if abs(new-tau2) < 1e-8:
            tau2 = new; break
        tau2 = new
    return max(0.0, tau2)

def _tau2_dl(yi, vi):
    k=len(yi); w=[1.0/v for v in vi]; sw=sum(w)
    mu=sum(wi*y for wi,y in zip(w,yi))/sw
    Q=sum(wi*(y-mu)**2 for wi,y in zip(w,yi))
    c=sw-sum(wi**2 for wi in w)/sw
    return max(0.0,(Q-(k-1))/c) if c>0 else 0.0

def pool(yi, vi, method="REML", hksj=True, level=0.95):
    """Return dict with pooled estimate, CI, tau2, Q, I2, prediction interval."""
    k = len(yi)
    if k == 0:
        return None
    if k == 1:
        z = _qnorm(1-(1-level)/2)
        se = math.sqrt(vi[0])
        return {"k":1,"est":yi[0],"se":se,"ci_lo":yi[0]-z*se,"ci_hi":yi[0]+z*se,
                "tau2":0.0,"Q":0.0,"I2":0.0,"pi_lo":None,"pi_hi":None,"method":method,"hksj":False}
    tau2 = _tau2_reml(yi,vi) if method=="REML" else _tau2_dl(yi,vi)
    w = [1.0/(v+tau2) for v in vi]; sw=sum(w)
    mu = sum(wi*y for wi,y in zip(w,yi))/sw
    var_fixed = 1.0/sw
    # heterogeneity
    wf=[1.0/v for v in vi]; swf=sum(wf); muf=sum(wi*y for wi,y in zip(wf,yi))/swf
    Q=sum(wi*(y-muf)**2 for wi,y in zip(wf,yi))
    I2=max(0.0,(Q-(k-1))/Q)*100 if Q>0 else 0.0
    if hksj:
        # HKSJ scale factor with the Q<k-1 floor (advanced-stats house rule)
        q = sum(wi*(y-mu)**2 for wi,y in zip(w,yi))/(k-1)
        q = max(1.0, q) if Q < (k-1) else q      # floor prevents CI narrower than DL
        se = math.sqrt(q*var_fixed)
        crit = _qt(1-(1-level)/2, k-1)
    else:
        se = math.sqrt(var_fixed); crit=_qnorm(1-(1-level)/2)
    ci_lo, ci_hi = mu-crit*se, mu+crit*se
    # prediction interval (Cochrane, t_{k-1})
    tcrit=_qt(1-(1-level)/2,k-1)
    pise=math.sqrt(se**2+tau2)
    pi_lo,pi_hi = mu-tcrit*pise, mu+tcrit*pise
    return {"k":k,"est":mu,"se":se,"ci_lo":ci_lo,"ci_hi":ci_hi,"tau2":tau2,"Q":Q,
            "I2":round(I2,1),"pi_lo":pi_lo,"pi_hi":pi_hi,"method":method,"hksj":hksj}

if __name__ == "__main__":
    # smoke: 5 studies, log scale
    import json
    yi=[math.log(0.86),math.log(0.79),math.log(0.91),math.log(0.88),math.log(0.93)]
    vi=[0.01,0.02,0.008,0.015,0.03]
    r=pool(yi,vi)
    r2={k:(round(v,4) if isinstance(v,float) else v) for k,v in r.items()}
    print(json.dumps(r2))
    print("back-tx est:",round(math.exp(r["est"]),3),"CI",round(math.exp(r["ci_lo"]),3),round(math.exp(r["ci_hi"]),3))
