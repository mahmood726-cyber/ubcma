import json, numpy as np
from collections import defaultdict
raw=json.load(open('field.json'))
# aggregate multiple analyses within (nct_id, active class) by inverse-variance pooling
g=defaultdict(list)
for r in raw: g[(r['nct_id'],r['active'])].append(r)
trials=[]
for (nct,cls),rs in g.items():
    y=np.array([r['md'] for r in rs]); s=np.array([r['se'] for r in rs])
    w=1/s**2; mu=float((w*y).sum()/w.sum()); se=float(np.sqrt(1/w.sum()))
    bl=[r['baseline_hba1c'] for r in rs if r['baseline_hba1c']]
    en=[r['enroll'] for r in rs if r['enroll']]
    trials.append(dict(nct_id=nct, active=cls, y=mu, se=se,
        baseline=float(np.mean(bl)) if bl else None,
        enroll=float(np.mean(en)) if en else None,
        results_posted=rs[0]['results_posted']))
print(f"independent trial-effects: {len(trials)}")
from collections import Counter
cc=Counter(t['active'] for t in trials); print("by class:",dict(cc))
def reml(y,s):
    s2=s**2
    from scipy.optimize import minimize_scalar
    def nll(lt):
        t2=np.exp(lt); w=1/(s2+t2); mu=(w*y).sum()/w.sum()
        return 0.5*(np.sum(np.log(s2+t2))+np.sum(w*(y-mu)**2)+np.log(w.sum()))
    r=minimize_scalar(nll,bounds=(-12,3),method='bounded'); t2=np.exp(r.x)
    w=1/(s2+t2); mu=(w*y).sum()/w.sum(); se=np.sqrt(1/w.sum())
    return mu,se,np.sqrt(t2)
print("\nper-class REML pooled (truth candidates):")
for cls in ['GLP1','DPP4','SGLT2','TZD','insulin']:
    ts=[t for t in trials if t['active']==cls]
    if len(ts)<2: 
        if ts: print(f"  {cls:8} k={len(ts)} y={ts[0]['y']:+.3f}")
        continue
    y=np.array([t['y'] for t in ts]); s=np.array([t['se'] for t in ts])
    mu,se,tau=reml(y,s)
    bl=[t['baseline'] for t in ts if t['baseline']]
    print(f"  {cls:8} k={len(ts):2d}  REML mu={mu:+.3f} se={se:.3f} tau={tau:.3f}  "
          f"y-range[{y.min():+.2f},{y.max():+.2f}]  baseline~{np.mean(bl):.2f}" if bl else
          f"  {cls:8} k={len(ts):2d}  REML mu={mu:+.3f} se={se:.3f} tau={tau:.3f}")
json.dump(trials, open('trials.json','w'), indent=0)
print("\nwrote trials.json")
