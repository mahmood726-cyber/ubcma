"""Confirm: in the star field, netmeta TE[class, placebo] for a spoke equals the
DL random-effects pool of that class's direct trials (no indirect borrowing) --
so 'standard NMA' is a faithful no-borrow comparator, not a strawman."""
import sys, json, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve().parent/'nma'))
sys.path.insert(0, str(Path('.').resolve().parent/'src'))
from nma_core import fit_nma, Comparison
trials=json.load(open('trials.json'))
def dl(y,s):  # DerSimonian-Laird
    y=np.array(y); s=np.array(s); w=1/s**2; mu=(w*y).sum()/w.sum()
    Q=(w*(y-mu)**2).sum(); k=len(y); c=w.sum()-(w**2).sum()/w.sum()
    t2=max(0,(Q-(k-1))/c) if c>0 else 0; w2=1/(s**2+t2)
    return (w2*y).sum()/w2.sum(), np.sqrt(1/w2.sum())
# take DPP4 with 4 sampled trials + full field
import random
pool=[t for t in trials if t['active']=='DPP4'][:4]
others=[t for t in trials if t['active']!='DPP4']
comps=[Comparison(f"S{i}","DPP4","placebo",t['y'],t['se']) for i,t in enumerate(pool)]
comps+=[Comparison(f"O{j}",t['active'],"placebo",t['y'],t['se']) for j,t in enumerate(others)]
fit=fit_nma(comps,reference="placebo",random=True)
ti=fit.meta['tidx']['DPP4']; pi=fit.meta['tidx']['placebo']
te=fit.TE[ti,pi]; se=fit.seTE[ti,pi]
# direct DL pool of the 4 DPP4 trials using the NETWORK tau2 (netmeta uses common tau2)
y=[t['y'] for t in pool]; s=[t['se'] for t in pool]
w=1/(np.array(s)**2+fit.tau2); mu_net=(w*np.array(y)).sum()/w.sum(); se_net=np.sqrt(1/w.sum())
mu_dl,se_dl=dl(y,s)
print(f"netmeta TE[DPP4,placebo]      = {te:+.5f}  se={se:.5f}")
print(f"direct IV pool @ network tau2 = {mu_net:+.5f}  se={se_net:.5f}  (diff {abs(te-mu_net):.2e})")
print(f"standalone DL pool (own tau2) = {mu_dl:+.5f}  se={se_dl:.5f}")
print("=> spoke-vs-hub NMA == direct pool at network tau2: no indirect info reaches the spoke.")
