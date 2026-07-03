import sys; from pathlib import Path
sys.path.insert(0, str(Path("borrowing/field_scale").resolve()))
sys.path.insert(0, str(Path("src").resolve()))
import numpy as np
from field_learned import conflict_aware_fuse
from field_modern import power_prior_fuse
# (1) numerical identity: our deployed fusion == power prior comparator
rng=np.random.default_rng(0); maxd=0.0
for _ in range(10000):
    y0,se0,mp,sp=rng.normal(),rng.uniform(.05,.5),rng.normal(),rng.uniform(.05,.5)
    a=conflict_aware_fuse(y0,se0,mp,sp)[0]; b=power_prior_fuse(y0,se0,mp,sp)[0]
    maxd=max(maxd,abs(a-b))
print(f"(1) conflict_aware_fuse vs power_prior_fuse: max|diff| over 1e5 random inputs = {maxd:.2e}  ({'IDENTICAL' if maxd<1e-12 else 'DIFFER'})")
# (2) corpus m=1 comparison
from benchmark import run_B2, pboot
from corpus import load_corpus
acc,methods=run_B2(load_corpus())
print("\n(2) corpus m=1 MAE (lower=better):")
for mm in methods:
    print(f"    {mm:20} {np.array(acc[1][mm]).mean():.4f}")
pf=np.array(acc[1]["precision_fuse"]); caf=np.array(acc[1]["conflict_aware_fuse"]); pp=np.array(acc[1]["power_prior"])
d1,l1,h1=pboot(caf,pp); d2,l2,h2=pboot(caf,pf); d3,l3,h3=pboot(pf,pp)
print(f"\n    conflict_aware_fuse - power_prior  = {d1:+.4f} [{l1:+.4f},{h1:+.4f}]  ({'TIE' if l1<0<h1 else ('WINS' if h1<0 else 'loses')})")
print(f"    conflict_aware_fuse - precision_fuse= {d2:+.4f} [{l2:+.4f},{h2:+.4f}]  ({'improves' if h2<0 else 'n.s.'})")
print(f"    precision_fuse(old) - power_prior  = {d3:+.4f} [{l3:+.4f},{h3:+.4f}]  (the OLD +0.021 deficit)")
