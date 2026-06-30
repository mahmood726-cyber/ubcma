"""PILOT-2 feasibility probe: is there an AACT HbA1c slice where a COVARIATE
genuinely predicts effect heterogeneity? (the regime pilot-1 lacked).

We pull active-vs-placebo HbA1c mean-difference effects (same extraction as
build_field) but now attach candidate effect modifiers:
  * baseline HbA1c  (textbook modifier: bigger baseline -> bigger reduction)
  * max dose tier   (parsed from intervention names, within-class)
  * enrollment, start year, follow-up weeks (from outcome time_frame)
For each candidate we run a random-effects meta-regression (effect ~ x) and
report the slope, its 95% CI, and the share of between-trial variance explained.
A modifier "exists" if the slope CI excludes 0 AND there is real spread in x.
"""
import duckdb, numpy as np, re, json
from collections import Counter, defaultdict
A = r"F:\AACT-storage\AACT\2026-04-12"
con = duckdb.connect()
def t(n): return f"read_csv('{A}/{n}.txt', delim='|', header=true, quote='', ignore_errors=true, auto_detect=true, all_varchar=true)"

con.execute(f"""CREATE TEMP TABLE t2dm AS SELECT DISTINCT nct_id FROM {t('conditions')}
 WHERE lower(name) LIKE '%type 2 diabetes%' OR lower(name) LIKE '%type ii diabetes%';""")
con.execute(f"""CREATE TEMP TABLE hba1c_out AS SELECT id AS outcome_id, nct_id, time_frame FROM {t('outcomes')}
 WHERE (lower(title) LIKE '%hba1c%' OR lower(title) LIKE '%glycated hemoglobin%'
   OR lower(title) LIKE '%glycosylated hemoglobin%' OR lower(title) LIKE '%hemoglobin a1c%');""")
con.execute(f"""CREATE TEMP TABLE eff AS
 SELECT a.nct_id, a.outcome_id, a.id AS analysis_id,
        TRY_CAST(a.param_value AS DOUBLE) md, TRY_CAST(a.ci_lower_limit AS DOUBLE) lo,
        TRY_CAST(a.ci_upper_limit AS DOUBLE) hi, TRY_CAST(a.ci_percent AS DOUBLE) cipct,
        o.time_frame
 FROM {t('outcome_analyses')} a
 JOIN hba1c_out o ON a.outcome_id=o.outcome_id AND a.nct_id=o.nct_id
 JOIN t2dm d ON a.nct_id=d.nct_id
 WHERE lower(a.param_type) LIKE '%mean difference%'
   AND a.ci_lower_limit IS NOT NULL AND a.ci_upper_limit IS NOT NULL;""")
con.execute(f"""CREATE TEMP TABLE grp AS
 SELECT oag.outcome_analysis_id AS analysis_id, rg.title AS arm_title
 FROM {t('outcome_analysis_groups')} oag
 JOIN {t('result_groups')} rg ON oag.result_group_id=rg.id;""")
rows = con.execute("""SELECT e.nct_id, e.analysis_id, e.md, e.lo, e.hi, e.cipct, e.time_frame,
   string_agg(g.arm_title,' ||| ') arms
 FROM eff e LEFT JOIN grp g ON e.analysis_id=g.analysis_id
 GROUP BY 1,2,3,4,5,6,7""").fetchall()

CLASSES = {
 'metformin':['metformin'],
 'SGLT2':['gliflozin','dapagliflozin','empagliflozin','canagliflozin','ertugliflozin','sotagliflozin','ipragliflozin','luseogliflozin','tofogliflozin','bexagliflozin'],
 'DPP4':['gliptin','sitagliptin','vildagliptin','saxagliptin','linagliptin','alogliptin','teneligliptin','gemigliptin','anagliptin','omarigliptin','trelagliptin'],
 'GLP1':['glutide','exenatide','liraglutide','dulaglutide','semaglutide','lixisenatide','albiglutide','tirzepatide','taspoglutide','glp-1','glp1'],
 'SU':['glipizide','glimepiride','glyburide','gliclazide','glibenclamide','sulfonylurea','glibornuride','gliquidone'],
 'TZD':['pioglitazone','rosiglitazone','glitazone','lobeglitazone'],
 'insulin':['insulin','glargine','degludec','lispro','aspart','detemir','glulisine'],
 'AGI':['acarbose','miglitol','voglibose'],
 'glinide':['repaglinide','nateglinide','mitiglinide'],
}
def classify(title):
    if not title: return None
    s=title.lower()
    hits=[c for c,kws in CLASSES.items() if any(k in s for k in kws)]
    if 'placebo' in s and len(hits)==0: return 'placebo'
    if len(hits)==1: return hits[0]
    return None

def parse_dose(title):
    """max numeric dose (mg) mentioned in the active arm title."""
    if not title: return None
    ds=re.findall(r'(\d+\.?\d*)\s*mg', title.lower())
    if not ds: return None
    vals=[float(d) for d in ds]
    return max(vals) if vals else None

def parse_weeks(tf):
    if not tf: return None
    s=tf.lower()
    m=re.search(r'(\d+\.?\d*)\s*week', s)
    if m: return float(m.group(1))
    m=re.search(r'(\d+\.?\d*)\s*month', s)
    if m: return float(m.group(1))*4.345
    m=re.search(r'(\d+\.?\d*)\s*year', s)
    if m: return float(m.group(1))*52.14
    return None

out=[]
for nct, aid, md, lo, hi, cip, tf, arms in rows:
    if md is None or lo is None or hi is None or hi<=lo: continue
    if abs(md)>=5: continue
    armlist = arms.split(' ||| ') if arms else []
    cls=[classify(a) for a in armlist]
    cls=[c for c in cls if c]
    arms_set=set(cls)
    actives=[c for c in arms_set if c!='placebo']
    if 'placebo' not in arms_set or len(actives)!=1: continue
    active=actives[0]
    cipv=cip if cip else 95.0
    z={90:1.6449,95:1.95996,99:2.5758}.get(int(round(cipv)),1.95996)
    se=(hi-lo)/(2*z)
    if not (se>0 and se<3): continue
    # dose from the active (non-placebo) arm titles
    active_titles=[a for a in armlist if classify(a)==active]
    dose=None
    for a in active_titles:
        d=parse_dose(a)
        if d is not None: dose=max(dose,d) if dose else d
    out.append(dict(nct_id=nct, analysis_id=int(aid), active=active, md=float(md), se=float(se),
                    dose=dose, weeks=parse_weeks(tf)))
print("active-vs-placebo HbA1c effects:", len(out))
print("by class:", dict(Counter(r['active'] for r in out)))
ncts=sorted({r['nct_id'] for r in out})
print("unique trials:", len(ncts))

# covariates per trial
nlist="','".join(ncts)
cov = con.execute(f"""SELECT nct_id, TRY_CAST(enrollment AS DOUBLE) enroll,
   substr(start_date,1,4) yr FROM {t('studies')} WHERE nct_id IN ('{nlist}')""").fetchall()
covd={c[0]:dict(enroll=c[1],yr=c[2]) for c in cov}
base = con.execute(f"""SELECT nct_id, avg(TRY_CAST(param_value_num AS DOUBLE)) bl, count(*) nb
   FROM {t('baseline_measurements')}
   WHERE nct_id IN ('{nlist}')
     AND (lower(title) LIKE '%hba1c%' OR lower(title) LIKE '%glycated hemoglobin%'
          OR lower(title) LIKE '%hemoglobin a1c%' OR lower(title) LIKE '%a1c%')
     AND param_value_num IS NOT NULL
   GROUP BY 1""").fetchall()
based={b[0]:b[1] for b in base if b[1] and 5<b[1]<14}
for r in out:
    c=covd.get(r['nct_id'],{}); r['enroll']=c.get('enroll')
    r['year']=float(c['yr']) if c.get('yr') and c['yr'].isdigit() else None
    r['baseline']=based.get(r['nct_id'])

# aggregate to trial x class level (IV pool within)
g=defaultdict(list)
for r in out: g[(r['nct_id'],r['active'])].append(r)
trials=[]
for (nct,cls),rs in g.items():
    y=np.array([r['md'] for r in rs]); s=np.array([r['se'] for r in rs])
    w=1/s**2; mu=float((w*y).sum()/w.sum()); se=float(np.sqrt(1/w.sum()))
    def avg(key):
        vs=[r[key] for r in rs if r.get(key) is not None]
        return float(np.mean(vs)) if vs else None
    trials.append(dict(nct_id=nct, active=cls, y=mu, se=se,
        baseline=avg('baseline'), dose=avg('dose'), weeks=avg('weeks'),
        enroll=avg('enroll'), year=avg('year')))
print(f"\nindependent trial-effects: {len(trials)}")

def metareg(trials, key, classfilter=None):
    """RE meta-regression y ~ x via moment-based tau2; report slope, CI, R2_resid."""
    ts=[t for t in trials if t.get(key) is not None and (classfilter is None or t['active'] in classfilter)]
    if len(ts)<6: return None
    y=np.array([t['y'] for t in ts]); s=np.array([t['se'] for t in ts]); x=np.array([t[key] for t in ts])
    if np.std(x)<1e-9: return None
    # iterate tau2 (DL-ish) for WLS slope
    tau2=0.0
    for _ in range(50):
        w=1/(s**2+tau2)
        X=np.column_stack([np.ones_like(x), x])
        WX=X*w[:,None]
        beta=np.linalg.solve(X.T@WX, WX.T@y)
        resid=y-X@beta
        df=len(ts)-2
        Q=float((w*resid**2).sum())
        # method-of-moments tau2 update
        P=np.diag(w)-WX@np.linalg.solve(X.T@WX,WX.T)
        trP=np.trace(P@np.diag(s**2))
        tau2_new=max(0.0,(Q-df)/ (np.trace(P) if np.trace(P)>0 else 1))
        if abs(tau2_new-tau2)<1e-8: tau2=tau2_new; break
        tau2=tau2_new
    w=1/(s**2+tau2)
    X=np.column_stack([np.ones_like(x), x]); WX=X*w[:,None]
    cov=np.linalg.inv(X.T@WX); beta=cov@(WX.T@y)
    slope=beta[1]; se_slope=np.sqrt(cov[1,1])
    # variance explained: tau2 with vs without x
    w0=1/(s**2+0.0); mu0=(w0*y).sum()/w0.sum()
    Q0=float((w0*(y-mu0)**2).sum()); df0=len(ts)-1
    c0=w0.sum()-(w0**2).sum()/w0.sum()
    tau2_0=max(0.0,(Q0-df0)/c0) if c0>0 else 0.0
    R2=1-tau2/tau2_0 if tau2_0>0 else 0.0
    return dict(key=key, n=len(ts), slope=float(slope), se=float(se_slope),
                ci=[float(slope-1.96*se_slope),float(slope+1.96*se_slope)],
                xspread=[float(x.min()),float(x.max())], xsd=float(np.std(x)),
                tau2_uncond=float(tau2_0), tau2_cond=float(tau2), R2_between=float(R2),
                sig=bool(abs(slope)>1.96*se_slope))

print("\n=== META-REGRESSION: does covariate predict effect? (all classes) ===")
for key in ['baseline','dose','weeks','enroll','year']:
    r=metareg(trials,key)
    if r:
        flag=' *** SIGNIFICANT ***' if r['sig'] else ''
        print(f"  {key:9} n={r['n']:3d} slope={r['slope']:+.4f} [{r['ci'][0]:+.4f},{r['ci'][1]:+.4f}] "
              f"xrange=[{r['xspread'][0]:.1f},{r['xspread'][1]:.1f}] R2_between={r['R2_between']:.2f}{flag}")
    else:
        print(f"  {key:9} insufficient data")

print("\n=== within rich classes (GLP1/DPP4/SGLT2) ===")
for cf in [['GLP1'],['DPP4'],['SGLT2'],['GLP1','DPP4','SGLT2']]:
    for key in ['baseline','dose','weeks']:
        r=metareg(trials,key,classfilter=cf)
        if r and r['n']>=8:
            flag=' ***' if r['sig'] else ''
            print(f"  {'+'.join(cf):18} {key:9} n={r['n']:3d} slope={r['slope']:+.4f} "
                  f"[{r['ci'][0]:+.4f},{r['ci'][1]:+.4f}] xsd={r['xsd']:.2f} R2={r['R2_between']:.2f}{flag}")

# coverage report
for key in ['baseline','dose','weeks','enroll','year']:
    n=sum(1 for t in trials if t.get(key) is not None)
    print(f"coverage {key:9}: {n}/{len(trials)}")
json.dump(trials, open('probe_trials.json','w'), indent=0)
print("\nwrote probe_trials.json")
