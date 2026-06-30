"""Extract the T2DM HbA1c borrowing field from AACT: active-vs-placebo mean
differences with arm classification, covariates, and a registry-integrity proxy.
Truth-first: every row is a real reported between-group analysis; we keep only
sane HbA1c MDs and record provenance (nct_id, analysis_id)."""
import duckdb, numpy as np, re, json
A = r"F:\AACT-storage\AACT\2026-04-12"
con = duckdb.connect()
def t(n): return f"read_csv('{A}/{n}.txt', delim='|', header=true, quote='', ignore_errors=true, auto_detect=true, all_varchar=true)"

con.execute(f"""CREATE TEMP TABLE t2dm AS SELECT DISTINCT nct_id FROM {t('conditions')}
 WHERE lower(name) LIKE '%type 2 diabetes%' OR lower(name) LIKE '%type ii diabetes%';""")
con.execute(f"""CREATE TEMP TABLE hba1c_out AS SELECT id AS outcome_id, nct_id FROM {t('outcomes')}
 WHERE (lower(title) LIKE '%hba1c%' OR lower(title) LIKE '%glycated hemoglobin%'
   OR lower(title) LIKE '%glycosylated hemoglobin%' OR lower(title) LIKE '%hemoglobin a1c%');""")
con.execute(f"""CREATE TEMP TABLE eff AS
 SELECT a.nct_id, a.outcome_id, a.id AS analysis_id, a.param_type,
        TRY_CAST(a.param_value AS DOUBLE) md, TRY_CAST(a.ci_lower_limit AS DOUBLE) lo,
        TRY_CAST(a.ci_upper_limit AS DOUBLE) hi, TRY_CAST(a.ci_percent AS DOUBLE) cipct
 FROM {t('outcome_analyses')} a
 JOIN hba1c_out o ON a.outcome_id=o.outcome_id AND a.nct_id=o.nct_id
 JOIN t2dm d ON a.nct_id=d.nct_id
 WHERE lower(a.param_type) LIKE '%mean difference%'
   AND a.ci_lower_limit IS NOT NULL AND a.ci_upper_limit IS NOT NULL;""")
# group titles per analysis
con.execute(f"""CREATE TEMP TABLE grp AS
 SELECT oag.outcome_analysis_id AS analysis_id, rg.title AS arm_title
 FROM {t('outcome_analysis_groups')} oag
 JOIN {t('result_groups')} rg ON oag.result_group_id=rg.id;""")
rows = con.execute("""SELECT e.nct_id, e.analysis_id, e.md, e.lo, e.hi, e.cipct,
   string_agg(g.arm_title,' ||| ') arms, count(*) narm
 FROM eff e LEFT JOIN grp g ON e.analysis_id=g.analysis_id
 GROUP BY 1,2,3,4,5,6""").fetchall()

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
    if 'placebo' in s and not any(any(k in s for k in v) for v in CLASSES.values()):
        return 'placebo'
    hits=[c for c,kws in CLASSES.items() if any(k in s for k in kws)]
    if 'placebo' in s and len(hits)==0: return 'placebo'
    if len(hits)==1: return hits[0]
    return None  # ambiguous / combo / unknown

out=[]
for nct, aid, md, lo, hi, cip, arms, narm in rows:
    if md is None or lo is None or hi is None or hi<=lo: continue
    if abs(md)>=5: continue
    cls=[classify(a) for a in (arms.split(' ||| ') if arms else [])]
    cls=[c for c in cls if c]
    arms_set=set(cls)
    # active-vs-placebo: exactly one placebo + exactly one active class among the arms
    actives=[c for c in arms_set if c!='placebo']
    if 'placebo' not in arms_set or len(actives)!=1: continue
    active=actives[0]
    cipv=cip if cip else 95.0
    z={90:1.6449,95:1.95996,99:2.5758}.get(int(round(cipv)),1.95996)
    se=(hi-lo)/(2*z)
    if not (se>0 and se<3): continue
    out.append(dict(nct_id=nct, analysis_id=int(aid), active=active, md=float(md), se=float(se)))
print("active-vs-placebo HbA1c effects:", len(out))
from collections import Counter
print("by class:", dict(Counter(r['active'] for r in out)))
ncts=sorted({r['nct_id'] for r in out})
print("unique trials:", len(ncts))

# --- covariates + integrity per trial ---
nlist="','".join(ncts)
cov = con.execute(f"""SELECT nct_id, TRY_CAST(enrollment AS DOUBLE) enroll,
   substr(start_date,1,4) yr, results_first_posted_date rp, phase, overall_status
   FROM {t('studies')} WHERE nct_id IN ('{nlist}')""").fetchall()
covd={c[0]:dict(enroll=c[1],yr=c[2],results_posted=(c[3] is not None and c[3]!=''),phase=c[4]) for c in cov}
# baseline HbA1c per trial (mean across baseline arms)
base = con.execute(f"""SELECT nct_id, avg(TRY_CAST(param_value_num AS DOUBLE)) bl
   FROM {t('baseline_measurements')}
   WHERE nct_id IN ('{nlist}')
     AND (lower(title) LIKE '%hba1c%' OR lower(title) LIKE '%glycated hemoglobin%'
          OR lower(title) LIKE '%hemoglobin a1c%' OR lower(title) LIKE '%a1c%')
     AND param_value_num IS NOT NULL
   GROUP BY 1""").fetchall()
based={b[0]:b[1] for b in base if b[1] and 5<b[1]<14}
for r in out:
    c=covd.get(r['nct_id'],{}); r['enroll']=c.get('enroll'); r['year']=c.get('yr')
    r['results_posted']=c.get('results_posted',False); r['baseline_hba1c']=based.get(r['nct_id'])
nb=sum(1 for r in out if r['baseline_hba1c']); print(f"with baseline HbA1c: {nb}/{len(out)}")
json.dump(out, open('field.json','w'), indent=0)
print("wrote field.json")
