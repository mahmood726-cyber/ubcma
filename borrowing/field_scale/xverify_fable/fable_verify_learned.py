import os
import numpy as np, pandas as pd, json
from pathlib import Path
from scipy.optimize import minimize
from scipy.linalg import cho_factor, cho_solve

RNG_MASTER = 12345
# Portable paths: the corpus lives one dir up from this script; the result is
# written alongside the script by default, or to FABLE_OUT if the caller sets it.
# (No hardcoded F:\ubcma or C:\Users\<name>\... machine-specific paths.)
_HERE = Path(__file__).resolve().parent
CSV = os.environ.get("FABLE_CSV") or str(_HERE.parent / "corpus_full_1177.csv")
OUT = os.environ.get("FABLE_OUT") or str(_HERE / "fable_learned_result.json")

df = pd.read_csv(CSV)

# ---- grouped-ARD kernel GP, implemented from scratch ----
# kernel(i,j) = sf2 * exp(-0.5*( dx1^2/l1^2 + dx2^2/l2^2 + [spec_i!=spec_j]/l3^2 + [ma_i!=ma_j]/l4^2 ))
# noise diag = se_i^2 + nugget
# hyperparams (log space): log_sf2, log_l1, log_l2, log_l3, log_l4, log_nugget

def build_dist2(X1, X2, C1, C2, M1, M2, params):
    l1, l2, l3, l4 = params['l1'], params['l2'], params['l3'], params['l4']
    d1 = (X1[:,None]-X2[None,:])**2 / l1**2
    d2 = (C1[:,None]-C2[None,:])**2 / l2**2  # C = continuous feature 2 (log precision)
    # wait naming; keep continuous1=year, continuous2=logprec
    return d1, d2

def kernel(xa, xb, p):
    # xa,xb: dict arrays year, logprec, spec(int), ma(int)
    d1 = (xa['year'][:,None]-xb['year'][None,:])**2 / p['l1']**2
    d2 = (xa['logprec'][:,None]-xb['logprec'][None,:])**2 / p['l2']**2
    dsp = (xa['spec'][:,None]!=xb['spec'][None,:]).astype(float) / p['l3']**2
    dma = (xa['ma'][:,None]!=xb['ma'][None,:]).astype(float) / p['l4']**2
    return p['sf2']*np.exp(-0.5*(d1+d2+dsp+dma))

def unpack(theta):
    sf2,l1,l2,l3,l4,nug = np.exp(theta)
    return dict(sf2=sf2,l1=l1,l2=l2,l3=l3,l4=l4,nugget=nug)

def neg_lml(theta, X, y, se2):
    p = unpack(theta)
    K = kernel(X,X,p)
    K[np.diag_indices_from(K)] += se2 + p['nugget']
    try:
        c,low = cho_factor(K, lower=True)
    except Exception:
        return 1e12
    alpha = cho_solve((c,low), y)
    lml = -0.5*y@alpha - np.sum(np.log(np.diag(c))) - 0.5*len(y)*np.log(2*np.pi)
    return -lml

def fit_hyper(X, y, se2):
    # y already mean-centered
    theta0 = np.log(np.array([np.var(y)+1e-6, 1.0,1.0,1.0,1.0, 0.01*(np.mean(se2)+1e-6)]))
    bounds = [(np.log(1e-6),np.log(1e3))]*6
    best=None
    for scale in [1.0, 0.5, 2.0]:
        t0 = theta0.copy(); t0[1:5]=np.log(scale)
        r = minimize(neg_lml, t0, args=(X,y,se2), method='L-BFGS-B', bounds=bounds,
                     options=dict(maxiter=80))
        if best is None or r.fun<best.fun:
            best=r
    return best.x

def gp_predict(Xtr,ytr,se2tr,Xte,theta):
    p=unpack(theta)
    m=np.mean(ytr)
    yc=ytr-m
    K=kernel(Xtr,Xtr,p); K[np.diag_indices_from(K)]+=se2tr+p['nugget']
    c,low=cho_factor(K,lower=True)
    alpha=cho_solve((c,low),yc)
    Ks=kernel(Xte,Xtr,p)
    return Ks@alpha + m

def subset(X, idx):
    return {k:v[idx] for k,v in X.items()}

# per-family CV
def run_family(dfx, seeds=(11,22,33,44,55)):
    dfx=dfx.reset_index(drop=True)
    year=dfx.year.values.astype(float); year=np.where(np.isnan(year),np.nan,year)
    logprec=np.log(1.0/dfx.se.values**2)
    spec=pd.factorize(dfx.specialty)[0]
    ma=pd.factorize(dfx.ma)[0]
    yi=dfx.yi.values.astype(float)
    se2=dfx.se.values**2
    n=len(dfx)
    # collect abs errors averaged over seeds, per study
    ae_accum=np.zeros(n); cnt=np.zeros(n)
    for seed in seeds:
        rng=np.random.default_rng(seed)
        order=rng.permutation(n)
        folds=np.array_split(order,10)
        for f in folds:
            te=f; tr=np.setdiff1d(np.arange(n),te)
            # standardize continuous features on TRAIN only
            ytr_year=year[tr]; mu_y=np.nanmean(ytr_year); sd_y=np.nanstd(ytr_year); sd_y=sd_y if sd_y>1e-8 else 1.0
            def std_year(v):
                z=(v-mu_y)/sd_y
                return np.where(np.isnan(z),0.0,z)
            mu_p=np.mean(logprec[tr]); sd_p=np.std(logprec[tr]); sd_p=sd_p if sd_p>1e-8 else 1.0
            Xall=dict(year=std_year(year), logprec=(logprec-mu_p)/sd_p, spec=spec, ma=ma)
            Xtr=subset(Xall,tr); Xte=subset(Xall,te)
            m=np.mean(yi[tr])
            theta=fit_hyper(Xtr, yi[tr]-m, se2[tr])
            pred=gp_predict(Xtr,yi[tr],se2[tr],Xte,theta)
            ae=np.abs(pred-yi[te])
            ae_accum[te]+=ae; cnt[te]+=1
    per_study_ae=ae_accum/cnt
    return per_study_ae, yi

# within-MA baseline (leave-one-out inverse-variance pool of other studies same ma)
def within_ma(dfx):
    dfx=dfx.reset_index(drop=True)
    yi=dfx.yi.values.astype(float); se2=dfx.se.values**2; ma=dfx.ma.values
    n=len(dfx); ae=np.full(n,np.nan)
    for i in range(n):
        mask=(ma==ma[i]); mask[i]=False
        if mask.sum()==0:
            ae[i]=np.nan; continue
        w=1.0/se2[mask]
        pred=np.sum(w*yi[mask])/np.sum(w)
        ae[i]=abs(pred-yi[i])
    return ae

fams=['SMD','COR','LOR']
all_learned_ae=[]; all_within_ae=[]; per_family={}
learned_by_study=[]; within_by_study=[]
for fam in fams:
    dfx=df[df.family==fam].copy()
    lae,yi=run_family(dfx)
    wae=within_ma(dfx)
    per_family[fam]=float(np.nanmean(lae))
    all_learned_ae.append(lae); all_within_ae.append(wae)
    print(fam,'learned MAE',np.nanmean(lae),'within MAE',np.nanmean(wae),'n',len(lae))

learned=np.concatenate(all_learned_ae)
within=np.concatenate(all_within_ae)
# paired: only where both defined
valid=~np.isnan(learned)&~np.isnan(within)
L=learned[valid]; W=within[valid]
diff=L-W
delta=float(np.mean(diff))
# paired bootstrap CI over per-study abs errors
rng=np.random.default_rng(999)
B=10000; n=len(diff)
boot=np.empty(B)
for b in range(B):
    idx=rng.integers(0,n,n)
    boot[b]=np.mean(diff[idx])
lo,hi=np.percentile(boot,[2.5,97.5])

result=dict(
  engine="fable5_from_scratch_numpy_gp_groupedARD",
  nodes=int(len(df)),
  MAs=int(df.ma.nunique()),
  learned_kernel_MAE=float(np.nanmean(learned)),
  within_MA_MAE=float(np.nanmean(within)),
  per_family_learned_MAE={k:round(v,4) for k,v in per_family.items()},
  learned_minus_within=dict(delta=delta, lo=float(lo), hi=float(hi), n=int(n))
)
with open(OUT,'w') as f: json.dump(result,f,indent=2)
print(json.dumps(result,indent=2))
