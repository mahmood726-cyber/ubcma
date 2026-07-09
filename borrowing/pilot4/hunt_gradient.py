"""PILOT-4 HUNT step 4 (the precondition test): transportability can only be
tested where trials actually SAMPLE a population gradient. For every condition
bucket among trials with a between-group MD analysis, join recruiting countries
-> IHME SDI and measure the SDI SPREAD across the bucket's trials. Slices with
near-zero SDI spread (like depression: CV~0.04) cannot exercise transportability
no matter how strong the modifier. Find where -- if anywhere -- the gradient is wide.
"""
from __future__ import annotations
import duckdb, csv, os, re
import numpy as np
from collections import defaultdict
from pathlib import Path

A = r"F:\AACT-storage\AACT\2026-04-12"
_SDI_REL = ("data/bronze/gbd_covariates/"
            "gbd-2023-socio-demographic-index-sdi_SDI_Values__1950-2023_[CSV].csv")
def _resolve_sdi():
    # ihme-data-lakehouse is a sibling repo; resolve via env var or common
    # project roots (candidate-root discovery, no machine-specific literal).
    env = os.environ.get("IHME_DATA_LAKEHOUSE")
    cands = ([Path(env) / _SDI_REL] if env else []) + [
        Path(drive) / "Projects" / "ihme-data-lakehouse" / _SDI_REL for drive in ("C:/", "F:/")
    ]
    for c in cands:
        if c.exists():
            return c
    return cands[-1]  # best-effort; read fails loudly if truly absent
SDI = _resolve_sdi()
con = duckdb.connect()
def t(n): return (f"read_csv('{A}/{n}.txt', delim='|', header=true, quote='', "
                  f"ignore_errors=true, auto_detect=true, all_varchar=true)")

# trials with >=1 between-group MD analysis
con.execute(f"""CREATE TEMP TABLE mdtrials AS
 SELECT DISTINCT nct_id FROM {t('outcome_analyses')}
 WHERE lower(param_type) LIKE '%mean difference%' AND ci_lower_limit IS NOT NULL;""")
nmd = con.execute("SELECT count(*) FROM mdtrials").fetchone()[0]
print("trials with MD analysis:", nmd)

# country lists for those trials
tc = defaultdict(list)
for nct, name in con.execute(f"""SELECT c.nct_id, c.name FROM {t('countries')} c
   JOIN mdtrials m ON c.nct_id=m.nct_id WHERE c.removed='f'""").fetchall():
    tc[nct].append(name)

# SDI 2019 by location name (+ alias)
SDIm={}
for r in csv.DictReader(open(SDI, encoding="utf-8-sig")):
    try:
        if int(r["year_id"])!=2019: continue
        SDIm[r["location_name"]]=float(r["mean_value"])
    except (ValueError,KeyError): pass
ALIAS={"South Korea":"Republic of Korea","Korea, Republic of":"Republic of Korea",
  "Russia":"Russian Federation","Czech Republic":"Czechia","United States":"United States of America",
  "UK":"United Kingdom","Vietnam":"Viet Nam","Taiwan":"Taiwan (Province of China)",
  "Iran":"Iran (Islamic Republic of)","Hong Kong":"China","Turkey":"Turkiye",
  "Tanzania":"United Republic of Tanzania","Moldova":"Republic of Moldova",
  "Venezuela":"Venezuela (Bolivarian Republic of)","Bolivia":"Bolivia (Plurinational State of)",
  "Laos":"Lao People's Democratic Republic","Syria":"Syrian Arab Republic",
  "Cote D'Ivoire":"Cote d'Ivoire","Ivory Coast":"Cote d'Ivoire","DR Congo":"Democratic Republic of the Congo"}
def sdi(nct):
    vals=[]
    for c in tc.get(nct,[]):
        v=SDIm.get(c) or SDIm.get(ALIAS.get(c,c))
        if v is not None: vals.append(v)
    return (sum(vals)/len(vals)) if vals else None

# condition buckets
BUCKETS = {
 'type 2 diabetes': r'type 2 diabet|type ii diabet',
 'hypertension':    r'hypertension|blood pressure',
 'depression(MDD)': r'depress',
 'HIV':             r'\bhiv\b|human immunodef',
 'tuberculosis':    r'tuberculosis|\btb\b',
 'malaria':         r'malaria|plasmodium',
 'asthma':          r'asthma',
 'COPD':            r'copd|chronic obstructive',
 'pain/OA':         r'osteoarthritis|chronic pain|low back pain',
 'schizophrenia':   r'schizophren',
 'heart failure':   r'heart failure',
 'obesity':         r'obesity|overweight',
 'hepatitis C':     r'hepatitis c|\bhcv\b',
 'COVID-19':        r'covid|sars-cov',
 'malnutrition':    r'malnutrition|stunting|wasting',
 'diarrhea/enteric':r'diarrh|rotavirus|cholera|enteric',
 'rheumatoid arth': r'rheumatoid',
}
# trial -> conditions
cond = defaultdict(list)
for nct, name in con.execute(f"""SELECT c.nct_id, lower(c.name) FROM {t('conditions')} c
   JOIN mdtrials m ON c.nct_id=m.nct_id""").fetchall():
    cond[nct].append(name)

print(f"\n{'bucket':18} {'ntrials':>7} {'wSDI':>5} {'SDI_min':>7} {'SDI_med':>7} {'SDI_max':>7} {'CV':>5}")
rows=[]
for b, pat in BUCKETS.items():
    ncts=[n for n in tc if any(re.search(pat,c) for c in cond.get(n,[]))]
    sv=[sdi(n) for n in ncts]; sv=[s for s in sv if s is not None]
    if len(sv)<10:
        print(f"{b:18} {len(ncts):7d} {len(sv):5d}  (too few w/ SDI)"); continue
    sv=np.array(sv); cv=sv.std()/sv.mean()
    rows.append((b,len(ncts),len(sv),sv.min(),np.median(sv),sv.max(),cv))
    print(f"{b:18} {len(ncts):7d} {len(sv):5d} {sv.min():7.3f} {np.median(sv):7.3f} {sv.max():7.3f} {cv:5.3f}")

print("\n-> buckets ranked by SDI spread (gradient width = precondition for transportability):")
for b,nt,ws,lo,md,hi,cv in sorted(rows,key=lambda r:-r[6]):
    print(f"   {b:18} CV={cv:.3f}  range=[{lo:.3f},{hi:.3f}]  n={ws}")
