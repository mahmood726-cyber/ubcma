# Independent from-scratch reconfirm of the AdaptShrink mechanism (no repo imports):
# under one-sided selection, does shrinking the RE mean toward the PET intercept
# (by funnel asymmetry) give a smaller matched-coverage width than the RE mean?
import numpy as np
from scipy.stats import norm
MU, TAU, K, REPS = 0.2, 0.1, 40, 300
def gen(seed):
    rng = np.random.default_rng(seed); ys, ss = [], []
    tries = 0
    while len(ys) < K and tries < 100000:
        tries += 1
        s = rng.uniform(0.05, 0.5); th = rng.normal(MU, TAU); y = rng.normal(th, s)
        if rng.random() <= norm.cdf(y/s):      # smooth one-sided selection
            ys.append(y); ss.append(s)
    return np.array(ys), np.array(ss)
def dl_mean(y, s):
    v = s**2; w = 1/v; mu = (w*y).sum()/w.sum()
    Q = (w*(y-mu)**2).sum(); c = w.sum()-(w**2).sum()/w.sum()
    t2 = max(0.0,(Q-(K-1))/c) if c>0 else 0.0
    w2 = 1/(v+t2); return (w2*y).sum()/w2.sum()
def pet(y, s):
    X = np.column_stack([np.ones_like(s), s]); w = 1/s**2; WX = X*w[:,None]
    cov = np.linalg.inv(X.T@WX); b = cov@(WX.T@y)
    seb1 = np.sqrt(cov[1,1]); t1 = b[1]/seb1 if seb1>0 else 0.0
    return b[0], t1
er_re, er_as, b_re, b_as = [], [], [], []
for r in range(REPS):
    y, s = gen(r); re = dl_mean(y,s); b0,t1 = pet(y,s)
    om = t1**2/(t1**2+1); a = (1-om)*re + om*b0
    er_re.append(abs(re-MU)); er_as.append(abs(a-MU)); b_re.append(re-MU); b_as.append(a-MU)
er_re, er_as = np.array(er_re), np.array(er_as)
m_re = 2*np.quantile(er_re,0.95); m_as = 2*np.quantile(er_as,0.95)
rng = np.random.default_rng(7); n=2000; bi = rng.integers(0,REPS,size=(n,REPS))
d = np.array([2*(np.quantile(er_as[b],0.95)-np.quantile(er_re[b],0.95)) for b in bi])
lo,hi = np.quantile(d,[0.025,0.975])
print(f"MCIW0 RE={m_re:.4f}  AdaptShrink={m_as:.4f}  dMCIW0={m_as-m_re:+.4f} [{lo:+.4f},{hi:+.4f}]  robust_win={hi<0}")
print(f"mean bias RE={np.mean(b_re):+.4f}  AdaptShrink={np.mean(b_as):+.4f}")
