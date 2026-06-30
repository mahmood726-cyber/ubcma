"""Diagnostics on the depression slice: (1) covariate SPREAD (is trial-site
selection compressing the population gradient?), (2) robustness of the only
significant hit (under-5 mortality, class+scale-adjusted) via leave-one-out and
which trials drive it."""
import json, numpy as np
trials = json.load(open("dep_trials.json"))

def desc(key, label):
    v = sorted(r[key] for r in trials if r.get(key) is not None)
    if not v: print(f"{label}: none"); return
    v = np.array(v)
    print(f"{label:13}: n={len(v)} min={v.min():.2f} q25={np.quantile(v,.25):.2f} "
          f"med={np.median(v):.2f} q75={np.quantile(v,.75):.2f} max={v.max():.2f} "
          f"CV={v.std()/abs(v.mean()):.2f}")
print("=== covariate spread across depression trials ===")
desc("pop_loggdp","log GDPpc"); desc("pop_sdi","SDI")
desc("pop_mort","under-5 mort"); desc("pop_ob","obesity %")

# single-country breakdown (cleanest population anchors)
sc = [r for r in trials if r["single_country"]]
from collections import Counter
print(f"\nsingle-country trials: {len(sc)} / {len(trials)}")
print("countries (single):", Counter(r["countries"][0] for r in sc if r["countries"]))
print("countries (all, flattened top):",
      Counter(c for r in trials for c in r["countries"]).most_common(12))

# robustness of under-5-mort class+scale-adjusted slope
def wls_slope(y,x,w,fe=None):
    y,x,w=map(np.asarray,(y,x,w)); cols=[np.ones_like(y),x]
    if fe is not None:
        for g in sorted(set(fe))[1:]: cols.append(np.array([1.0 if k==g else 0.0 for k in fe]))
    X=np.column_stack(cols); W=np.diag(w)
    try:
        b=np.linalg.solve(X.T@W@X,X.T@W@y); return float(b[1])
    except np.linalg.LinAlgError: return float("nan")

m=[r for r in trials if r.get("pop_mort") is not None]
y=np.array([r["y"] for r in m]); w=1.0/np.array([r["se"] for r in m])**2
x=np.array([r["pop_mort"] for r in m]); xz=(x-x.mean())/x.std()
fe=[f"{r['active']}|{r['scale']}" for r in m]
full=wls_slope(y,xz,w,fe)
print(f"\nunder-5 mort class+scale slope (full, /SD): {full:+.3f}")
# leave-one-out
loo=[]
for i in range(len(m)):
    idx=[j for j in range(len(m)) if j!=i]
    s=wls_slope(y[idx],(x[idx]-x[idx].mean())/x[idx].std(),w[idx],[fe[j] for j in idx])
    loo.append((s, m[i]["nct_id"], m[i]["countries"], x[i], m[i]["y"]))
loo_s=np.array([l[0] for l in loo])
print(f"LOO slope range: [{loo_s.min():+.3f}, {loo_s.max():+.3f}]  (sign-stable: {(loo_s>0).all() or (loo_s<0).all()})")
# which trials have highest under-5 mortality (drive the high-mort end)?
print("\nhighest under-5-mort trials (gradient anchors):")
for r in sorted(m, key=lambda r:-r["pop_mort"])[:8]:
    print(f"  {r['nct_id']} mort={r['pop_mort']:5.1f} y={r['y']:+.2f} se={r['se']:.2f} "
          f"{r['active']:11} {r['scale']:6} {r['countries']}")
