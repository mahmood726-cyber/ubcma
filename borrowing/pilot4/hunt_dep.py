"""PILOT-4 HUNT step 3: DEPRESSION slice (antidepressant vs placebo) + modifier
screen. Antidepressant RCTs are overwhelmingly placebo-controlled and the
region / national-income gradient in drug-placebo separation is one of the
strongest, best-documented population-level modifiers of a measured trial effect
(rising placebo response in high-income/US settings -> smaller separation).

Scale heterogeneity handled by (a) recording the rating scale and testing the
covariate slope WITHIN scale (scale fixed effects), and (b) a parallel run on the
single most common scale (MADRS, 0-60) only.

Covariates per recruiting country (latest yr): WB log GDP/capita, IHME SDI,
WB under-5 mortality, WB obesity. Same Simpson guard (class+scale FE) + permutation.
"""
from __future__ import annotations
import duckdb, csv, json
import numpy as np
from collections import defaultdict, Counter
from pathlib import Path

A = r"F:\AACT-storage\AACT\2026-04-12"
WB = Path("F:/WorldBankData/api_data")
SDI = Path("C:/Projects/ihme-data-lakehouse/data/bronze/gbd_covariates/"
           "gbd-2023-socio-demographic-index-sdi_SDI_Values__1950-2023_[CSV].csv")
con = duckdb.connect()
def t(n): return (f"read_csv('{A}/{n}.txt', delim='|', header=true, quote='', "
                  f"ignore_errors=true, auto_detect=true, all_varchar=true)")

CLASSES = {
 'SSRI': ['fluoxetine','sertraline','paroxetine','citalopram','escitalopram','fluvoxamine'],
 'SNRI': ['venlafaxine','desvenlafaxine','duloxetine','levomilnacipran','milnacipran'],
 'atypical': ['bupropion','mirtazapine','vortioxetine','vilazodone','agomelatine','trazodone',
              'nefazodone','reboxetine','tianeptine','gepirone'],
 'adjunct_AAP': ['aripiprazole','brexpiprazole','quetiapine','olanzapine','cariprazine','risperidone'],
 'glutamate': ['esketamine','ketamine','rapastinel','zuranolone','dextromethorphan'],
 'TCA': ['amitriptyline','imipramine','nortriptyline','clomipramine','desipramine','doxepin'],
}
def classify(title):
    if not title: return None
    s = title.lower()
    hits = [c for c,kws in CLASSES.items() if any(k in s for k in kws)]
    if 'placebo' in s and not hits: return 'placebo'
    if len(hits) == 1: return hits[0]
    return None

def scale_of(title):
    s = (title or '').lower()
    if 'madrs' in s or 'montgomery' in s: return 'MADRS'
    if 'hamd-17' in s or 'ham-d-17' in s or 'hamilton' in s and '17' in s: return 'HAMD17'
    if 'hamd' in s or 'ham-d' in s or 'hamilton' in s or 'hdrs' in s or 'hrsd' in s: return 'HAMD'
    if 'qids' in s: return 'QIDS'
    if 'phq' in s: return 'PHQ'
    if 'bdi' in s or 'beck' in s: return 'BDI'
    if 'cgi' in s: return 'CGI'
    return 'other'

con.execute(f"""CREATE TEMP TABLE dep_out AS
 SELECT id AS outcome_id, nct_id, title FROM {t('outcomes')}
 WHERE (lower(title) LIKE '%madrs%' OR lower(title) LIKE '%montgomery%'
        OR lower(title) LIKE '%hamilton depress%' OR lower(title) LIKE '%ham-d%'
        OR lower(title) LIKE '%hamd%' OR lower(title) LIKE '%hdrs%' OR lower(title) LIKE '%hrsd%'
        OR lower(title) LIKE '%depression rating%' OR lower(title) LIKE '%depressive symptom%')
   AND (lower(title) LIKE '%chang%' OR lower(title) LIKE '%from baseline%'
        OR lower(title) LIKE '%reduction%' OR lower(title) LIKE '%difference%');""")
con.execute(f"""CREATE TEMP TABLE eff AS
 SELECT a.nct_id, a.id AS analysis_id, o.title AS otitle,
        TRY_CAST(a.param_value AS DOUBLE) md, TRY_CAST(a.ci_lower_limit AS DOUBLE) lo,
        TRY_CAST(a.ci_upper_limit AS DOUBLE) hi, TRY_CAST(a.ci_percent AS DOUBLE) cipct
 FROM {t('outcome_analyses')} a JOIN dep_out o ON a.outcome_id=o.outcome_id AND a.nct_id=o.nct_id
 WHERE lower(a.param_type) LIKE '%mean difference%'
   AND a.ci_lower_limit IS NOT NULL AND a.ci_upper_limit IS NOT NULL
   AND TRY_CAST(a.param_value AS DOUBLE) IS NOT NULL;""")
con.execute(f"""CREATE TEMP TABLE grp AS
 SELECT oag.outcome_analysis_id AS analysis_id, rg.title AS arm_title
 FROM {t('outcome_analysis_groups')} oag
 JOIN {t('result_groups')} rg ON oag.result_group_id=rg.id;""")
rows = con.execute("""SELECT e.nct_id, e.analysis_id, e.otitle, e.md, e.lo, e.hi, e.cipct,
   string_agg(g.arm_title,' ||| ') arms
 FROM eff e LEFT JOIN grp g ON e.analysis_id=g.analysis_id GROUP BY 1,2,3,4,5,6,7""").fetchall()

bytrial = {}  # nct -> best (smallest se) antidepressant-vs-placebo row
for nct, aid, otitle, md, lo, hi, cip, arms in rows:
    if None in (md, lo, hi) or hi <= lo: continue
    cls = [classify(a) for a in (arms.split(' ||| ') if arms else [])]
    cls = set(c for c in cls if c)
    actives = [c for c in cls if c != 'placebo']
    if 'placebo' not in cls or len(actives) != 1: continue
    z = {90:1.6449,95:1.95996,99:2.5758}.get(int(round(cip or 95.0)), 1.95996)
    se = (hi - lo) / (2*z)
    sc = scale_of(otitle)
    if not (0 < se < 12) or abs(md) > 30: continue
    # sign convention: greater symptom reduction on drug -> make 'benefit' negative
    y = float(md)
    key = nct
    if key not in bytrial or se < bytrial[key]['se']:
        bytrial[key] = dict(nct_id=nct, active=actives[0], scale=sc, y=y, se=float(se))
trials = list(bytrial.values())
print(f"antidepressant-vs-placebo depression trials: {len(trials)}")
print("by class:", dict(Counter(r['active'] for r in trials)))
print("by scale:", dict(Counter(r['scale'] for r in trials)))

ncts = sorted(bytrial); nlist = "','".join(ncts)
tc = defaultdict(list)
for nct, name in con.execute(f"""SELECT nct_id, name FROM {t('countries')}
   WHERE removed='f' AND nct_id IN ('{nlist}')""").fetchall():
    tc[nct].append(name)

def load_wb(path):
    best = {}
    for r in csv.DictReader(open(path, encoding="utf-8-sig")):
        v = r["value"]
        if not v: continue
        try: yr=int(r["date"]); val=float(v)
        except ValueError: continue
        nm=r["country_name"]
        if nm not in best or yr>best[nm][0]: best[nm]=(yr,val)
    return {k:v[1] for k,v in best.items()}
fe = load_wb(WB/"source_14_Gender Statistics/SH_STA_OB18_FE_ZS.csv")
ma = load_wb(WB/"source_14_Gender Statistics/SH_STA_OB18_MA_ZS.csv")
OBES={k:(fe[k]+ma[k])/2 for k in fe if k in ma}
GDP = load_wb(WB/"source_2_World Development Indicators/NY_GDP_PCAP_CD.csv")
MORT= load_wb(WB/"source_2_World Development Indicators/SH_DYN_MORT.csv")
SDIm={}
for r in csv.DictReader(open(SDI, encoding="utf-8-sig")):
    try:
        if int(r["year_id"])!=2019: continue
        SDIm[r["location_name"]]=float(r["mean_value"])
    except (ValueError,KeyError): pass
ALIAS_WB={"South Korea":"Korea, Rep.","Russia":"Russian Federation","Slovakia":"Slovak Republic",
  "Taiwan":None,"Hong Kong":"Hong Kong SAR, China","Puerto Rico":None,"Czech Republic":"Czechia",
  "Turkey":"Turkiye","Egypt":"Egypt, Arab Rep.","Iran":"Iran, Islamic Rep.","Venezuela":"Venezuela, RB",
  "Korea, Republic of":"Korea, Rep.","Vietnam":"Viet Nam"}
ALIAS_SDI={"South Korea":"Republic of Korea","Korea, Republic of":"Republic of Korea",
  "Russia":"Russian Federation","Czech Republic":"Czechia","United States":"United States of America",
  "UK":"United Kingdom","Vietnam":"Viet Nam","Taiwan":"Taiwan (Province of China)",
  "Iran":"Iran (Islamic Republic of)","Hong Kong":"China","Turkey":"Turkiye",
  "Venezuela":"Venezuela (Bolivarian Republic of)","Bulgaria":"Bulgaria"}
def lk(d,c,al):
    if c in d: return d[c]
    a=al.get(c,c)
    return d[a] if (a and a in d) else None
def cov(nct,d,al):
    vals=[lk(d,c,al) for c in tc.get(nct,[])]; vals=[v for v in vals if v is not None]
    return (sum(vals)/len(vals)) if vals else None
for r in trials:
    r["countries"]=tc.get(r["nct_id"],[]); r["n_countries"]=len(r["countries"])
    r["pop_ob"]=cov(r["nct_id"],OBES,ALIAS_WB)
    g=cov(r["nct_id"],GDP,ALIAS_WB); r["pop_loggdp"]=(np.log(g) if g else None)
    r["pop_mort"]=cov(r["nct_id"],MORT,ALIAS_WB)
    r["pop_sdi"]=cov(r["nct_id"],SDIm,ALIAS_SDI)
    r["single_country"]=(r["n_countries"]==1)
json.dump(trials, open("dep_trials.json","w"), indent=1)

def wls_slope(y,x,w,fe_groups=None):
    y,x,w=map(np.asarray,(y,x,w)); cols=[np.ones_like(y),x]
    if fe_groups is not None:
        for g in sorted(set(fe_groups))[1:]:
            cols.append(np.array([1.0 if k==g else 0.0 for k in fe_groups]))
    X=np.column_stack(cols); W=np.diag(w)
    try:
        XtWX=X.T@W@X; beta=np.linalg.solve(XtWX,X.T@W@y); covm=np.linalg.inv(XtWX)
    except np.linalg.LinAlgError: return float("nan"),float("nan")
    return float(beta[1]), float(np.sqrt(covm[1,1]))
def perm_p(y,x,w,fe_groups,slope_obs,nperm=4000,seed=0):
    rng=np.random.default_rng(seed); cnt=0
    for _ in range(nperm):
        s,_=wls_slope(y,rng.permutation(x),w,fe_groups)
        if abs(s)>=abs(slope_obs)-1e-12: cnt+=1
    return (cnt+1)/(nperm+1)

def screen(sub, tag):
    print(f"\n===== MODIFIER SCREEN [{tag}] n={len(sub)} =====")
    y=np.array([r["y"] for r in sub]); se=np.array([r["se"] for r in sub])
    w=1.0/se**2; cls=[r["active"] for r in sub]; scl=[r["scale"] for r in sub]
    fe=[f"{a}|{s}" for a,s in zip(cls,scl)]
    out={}
    for label,key in [("log GDPpc","pop_loggdp"),("SDI","pop_sdi"),
                      ("under-5 mort","pop_mort"),("obesity %","pop_ob")]:
        m=[r for r in sub if r.get(key) is not None]
        if len(m)<12: print(f"{label:13}: {len(m)} trials -- skip"); continue
        yy=np.array([r["y"] for r in m]); ww=1.0/np.array([r["se"] for r in m])**2
        xx=np.array([r[key] for r in m]); xz=(xx-xx.mean())/xx.std()
        sc_g=[r["scale"] for r in m]; cs_g=[f"{r['active']}|{r['scale']}" for r in m]
        ms,_=wls_slope(yy,xz,ww); pm=perm_p(yy,xz,ww,None,ms)
        ss,_=wls_slope(yy,xz,ww,sc_g); ps=perm_p(yy,xz,ww,sc_g,ss)
        cs,_=wls_slope(yy,xz,ww,cs_g); pc=perm_p(yy,xz,ww,cs_g,cs)
        out[key]=dict(label=label,n=len(m),marg=round(ms,3),marg_p=round(pm,4),
                      scaleadj=round(ss,3),scaleadj_p=round(ps,4),
                      classscaleadj=round(cs,3),classscaleadj_p=round(pc,4),y_sd=round(yy.std(),2))
        print(f"{label:13} (n={len(m)}, y_sd={yy.std():.2f}): marg {ms:+.2f}/SD p={pm:.3f} | "
              f"+scaleFE {ss:+.2f} p={ps:.3f} | +class&scaleFE {cs:+.2f} p={pc:.3f}")
    return out

allscreen = screen(trials, "ALL scales")
madrs = [r for r in trials if r["scale"]=="MADRS"]
mscreen = screen(madrs, "MADRS only") if len(madrs)>=12 else {}
json.dump({"all":allscreen,"madrs":mscreen}, open("dep_modifier_screen.json","w"), indent=1)
print("\nwrote dep_trials.json + dep_modifier_screen.json")
