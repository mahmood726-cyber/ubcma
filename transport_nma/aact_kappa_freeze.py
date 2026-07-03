"""Freeze the EXTERNAL magnitude estimates from aact_kappa.json (no sim tuning).
Two frozen deployable estimators of the selection strength kappa (NO oracle):
  (1) kappa_pooled   = n-weighted mean of max(0, kappa_MD_c) over adequately-powered classes
                       (min(n_pub,n_reg) >= NMIN) -- an absolute effect-inflation scale.
  (2) kappa_slope    = WLS slope of kappa_MD_c on (1-lambda_c) through the origin over the same
                       classes -- an external estimate of B in the registry model bias=B*(1-lambda).
Also emits the per-class clamped magnitude m_c = max(0, kappa_MD_c) for a per-class corrector.
"""
import json, numpy as np
from pathlib import Path
HERE = Path(__file__).resolve().parent
K = json.load(open(HERE/"aact_kappa.json"))
LAM = json.load(open(Path(r"F:\ubcma\borrowing\class_lambda.json")))
NMIN = 8
rows = []
for c, d in K.items():
    kmd = d.get("kappa_md")
    npub = d["pub"]["n"]; nreg = d["reg"]["n"]
    if kmd is None or min(npub, nreg) < NMIN:
        continue
    lam = LAM.get(c)
    if lam is None:
        continue
    w = min(npub, nreg)                 # conservative weight = smaller arm
    rows.append((c, kmd, 1.0-lam, w, npub, nreg))

print(f"adequately-powered classes (min(n_pub,n_reg)>={NMIN}): {[r[0] for r in rows]}")
kmds = np.array([r[1] for r in rows]); one_m_lam = np.array([r[2] for r in rows])
w = np.array([r[3] for r in rows], float)
kmd_clamp = np.maximum(0.0, kmds)
kappa_pooled = float(np.sum(w*kmd_clamp)/np.sum(w))
# WLS slope through origin of kappa_MD on (1-lambda)
kappa_slope = float(np.sum(w*one_m_lam*kmds)/np.sum(w*one_m_lam**2))
kappa_slope = max(0.0, kappa_slope)
# correlation (unweighted) for honesty
r_corr = float(np.corrcoef(one_m_lam, kmds)[0,1]) if len(rows) > 2 else float("nan")
per_class = {c: max(0.0, K[c]["kappa_md"]) for c in K if K[c].get("kappa_md") is not None}

frozen = dict(kappa_pooled=kappa_pooled, kappa_slope=kappa_slope,
              corr_kmd_vs_1mlam=r_corr, nmin=NMIN,
              classes_used=[r[0] for r in rows], per_class_clamped=per_class)
json.dump(frozen, open(HERE/"aact_kappa_frozen.json","w"), indent=1)
print(f"  kappa_pooled  = {kappa_pooled:.4f}   (absolute effect-inflation scale)")
print(f"  kappa_slope   = {kappa_slope:.4f}   (external B est: kappa_MD ~ B*(1-lambda))")
print(f"  corr(kappa_MD, 1-lambda) = {r_corr:+.3f}   (does gap grow with selection-severity?)")
print("  per-class clamped m_c:", {k: round(v,3) for k,v in per_class.items()})
print("wrote aact_kappa_frozen.json")
