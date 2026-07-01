import pandas as pd, numpy as np
df = pd.read_csv("pilot_perrep.csv")
df = df[df.converged & np.isfinite(df.mu_hat) & np.isfinite(df.ci_low) & np.isfinite(df.ci_high)].copy()
df["err"] = (df.mu_hat - df.true_mu).abs()
def mciw0(g):
    cal=g[g.rep%2==0].err.to_numpy(); tes=g[g.rep%2==1].err.to_numpy()
    ch=np.quantile(cal,0.95); return 2*ch, float(np.mean(tes<=ch))
print("== independent MCIW0 (separate code) ==")
for tg,rg in [("DPP4","sparse"),("GLP1","rich")]:
    for m in ["nma","borrow","shrink_mean"]:
        g=df[(df.target==tg)&(df.regime==rg)&(df.method==m)]
        w,c=mciw0(g); print(f"  {tg:5} {rg:6} {m:11} MCIW0={w:.4f} test_cov={c:.3f}")
def pboot(tg,rg,A,B,seed=7,nb=2000):
    g=df[(df.target==tg)&(df.regime==rg)]
    wide=g.pivot_table(index="rep",columns="method",values="err").dropna()
    a=wide[A].to_numpy(); b=wide[B].to_numpy(); rng=np.random.default_rng(seed)
    bi=rng.integers(0,len(a),size=(nb,len(a)))
    d=2*(np.quantile(a[bi],0.95,axis=1)-np.quantile(b[bi],0.95,axis=1))
    lo,hi=np.percentile(d,[2.5,97.5]); pt=2*(np.quantile(a,0.95)-np.quantile(b,0.95))
    return pt,lo,hi,hi<0,lo>0
print("== independent paired bootstrap ==")
for tg,rg in [("DPP4","sparse"),("GLP1","rich")]:
    for A in ["borrow","shrink_mean"]:
        pt,lo,hi,win,harm=pboot(tg,rg,A,"nma")
        print(f"  {tg:5} {rg:6} {A:11}_vs_nma  d={pt:+.4f} CI[{lo:+.4f},{hi:+.4f}] win={win} harm={harm}")
