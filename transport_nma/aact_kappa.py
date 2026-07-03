"""FIX3-EXTERNAL: per-class effect-inflation kappa from the AACT registered-vs-PUBLISHED
HbA1c effect-distribution gap (2026-04-12 snapshot).

Rationale (Turner 2008 NEJM logic, done inside the registry): AACT holds STRUCTURED
RESULTS for many registered T2DM trials. Whether a trial's results ALSO reached the
published literature is observable via PubMed linkage (study_references reference_type in
{DERIVED, RESULT} -> a PMID citing this NCT). Publication selection favours larger/
significant effects, so PUBLISHED trials should show systematically larger |effect| than
merely-results-posted (registered-only) trials. That gap, per drug class, is an EXTERNAL,
large-n estimate of the selection MAGNITUDE that the in-network funnel (4-6 studies) could
not recover (FIX3 internal-kappa negative). Endpoint restricted to HbA1c -> the SAME scale
as the senn2013 network we correct.

kappa_c (relative inflation) = (mean|effect|_published / mean|effect|_registered-only) - 1,
on a common NGSP-% scale, with |effect| = |mean difference| (mmol/mol -> % via x0.0915).
A significance-based variant uses mean |z| (z = MD / SE_from_CI). Both reported; both frozen
BEFORE any truth-gate scoring (no tuning to the sim).
"""
import duckdb, json, io, sys
import numpy as np
from pathlib import Path
try: sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception: pass

A = r"F:\AACT-storage\AACT\2026-04-12"
HERE = Path(__file__).resolve().parent
con = duckdb.connect()
def t(n): return f"read_csv('{A}/{n}.txt', delim='|', header=true, quote='', ignore_errors=true, auto_detect=true, all_varchar=true)"

# classes aligned with class_lambda.py / senn2013 network
CLASSES = {
 'metformin':['metformin'], 'SGLT2':['gliflozin'], 'DPP4':['gliptin'],
 'GLP1':['glutide','exenatide','liraglutide','dulaglutide','semaglutide','lixisenatide','tirzepatide'],
 'SU':['glipizide','glimepiride','glyburide','gliclazide','glibenclamide','sulfonylurea'],
 'TZD':['glitazone','pioglitazone','rosiglitazone'], 'insulin':['insulin'],
 'AGI':['acarbose','miglitol','voglibose'], 'glinide':['repaglinide','nateglinide'],
}

# T2DM trials
con.execute(f"""CREATE TEMP TABLE t2dm AS SELECT DISTINCT nct_id FROM {t('conditions')}
 WHERE lower(name) LIKE '%type 2 diabetes%' OR lower(name) LIKE '%type ii diabetes%';""")
# published = has a PubMed linkage (DERIVED or RESULT reference type)
con.execute(f"""CREATE TEMP TABLE pub AS SELECT DISTINCT nct_id FROM {t('study_references')}
 WHERE reference_type IN ('DERIVED','RESULT') AND pmid IS NOT NULL AND pmid<>'';""")
# HbA1c mean-difference analyses with a usable effect estimate + CI
con.execute(f"""CREATE TEMP TABLE hba1c AS
 SELECT o.nct_id, lower(coalesce(o.units,'')) units,
        TRY_CAST(a.param_value AS DOUBLE) md,
        TRY_CAST(a.ci_lower_limit AS DOUBLE) lo,
        TRY_CAST(a.ci_upper_limit AS DOUBLE) hi,
        TRY_CAST(a.p_value AS DOUBLE) p
 FROM {t('outcomes')} o
 JOIN {t('outcome_analyses')} a ON a.outcome_id = o.id
 JOIN t2dm d ON o.nct_id = d.nct_id
 WHERE (lower(o.title) LIKE '%hba1c%' OR lower(o.title) LIKE '%hemoglobin a1c%'
        OR lower(o.title) LIKE '%glycated%' OR lower(o.title) LIKE '%glycosylated hemoglobin%'
        OR lower(o.title) LIKE '%hemoglobin a1%')
   AND lower(coalesce(a.param_type,'')) LIKE '%mean difference%'
   AND a.param_value IS NOT NULL;""")

rows = con.execute("""SELECT nct_id, units, md, lo, hi, p FROM hba1c
   WHERE md IS NOT NULL""").fetchall()
pubset = set(r[0] for r in con.execute("SELECT nct_id FROM pub").fetchall())

# intervention name per trial (for class assignment)
con.execute(f"""CREATE TEMP TABLE iv AS SELECT nct_id, lower(name) nm FROM {t('interventions')}
 WHERE nct_id IN (SELECT nct_id FROM t2dm);""")
iv_rows = con.execute("SELECT nct_id, nm FROM iv").fetchall()
trial_names = {}
for nct, nm in iv_rows:
    trial_names.setdefault(nct, []).append(nm or "")

def classes_of(nct):
    names = " ".join(trial_names.get(nct, []))
    out = []
    for c, kws in CLASSES.items():
        if any(k in names for k in kws):
            out.append(c)
    return out

def to_pct(units, md, lo, hi):
    """normalise a difference to NGSP % scale (mmol/mol -> x0.0915)."""
    f = 0.0915 if ('mmol/mol' in units or 'mmol / mol' in units) else 1.0
    g = lambda x: (x*f if x is not None else None)
    return g(md), g(lo), g(hi)

# assemble per-class records
per = {c: {'pub': [], 'reg': []} for c in CLASSES}
kept = 0
for nct, units, md, lo, hi, p in rows:
    md2, lo2, hi2 = to_pct(units, md, lo, hi)
    if md2 is None or not np.isfinite(md2):
        continue
    amd = abs(md2)
    if amd > 5:            # implausible for an HbA1c mean difference in %; likely scale error
        continue
    se = None
    if lo2 is not None and hi2 is not None and np.isfinite(lo2) and np.isfinite(hi2) and hi2 > lo2:
        se = (hi2 - lo2) / (2*1.959963984540054)
    z = (abs(md2)/se) if (se and se > 0) else None
    cs = classes_of(nct)
    if not cs:
        continue
    kept += 1
    bucket = 'pub' if nct in pubset else 'reg'
    for c in cs:                       # a trial may inform multiple classes (combo/comparator)
        per[c][bucket].append((amd, z))

def summ(lst):
    amd = np.array([a for a,_ in lst], float)
    zz = np.array([z for _,z in lst if z is not None], float)
    return dict(n=len(amd), mean_amd=float(np.mean(amd)) if len(amd) else None,
                med_amd=float(np.median(amd)) if len(amd) else None,
                mean_z=float(np.mean(zz)) if len(zz) else None, n_z=len(zz))

print("="*92)
print("AACT registered-vs-PUBLISHED HbA1c effect gap (T2DM), per drug class")
print("  published = PubMed-linked (DERIVED/RESULT PMID);  registered-only = results but no linkage")
print("="*92)
print(f"  total HbA1c mean-difference analyses kept: {kept}  (published PMIDs in set: {len(pubset)})")
hdr = f"  {'class':10}{'n_pub':>7}{'n_reg':>7}{'|MD|pub':>9}{'|MD|reg':>9}{'kappa_MD':>10}{'zpub':>7}{'zreg':>7}{'kappa_z':>9}"
print(hdr)
out = {}
for c in CLASSES:
    sp, sr = summ(per[c]['pub']), summ(per[c]['reg'])
    kmd = kz = None
    if sp['mean_amd'] and sr['mean_amd']:
        kmd = sp['mean_amd']/sr['mean_amd'] - 1.0
    if sp['mean_z'] and sr['mean_z']:
        kz = sp['mean_z']/sr['mean_z'] - 1.0
    out[c] = dict(pub=sp, reg=sr, kappa_md=kmd, kappa_z=kz)
    def f(x, w=9, p=3): return (f"{x:>{w}.{p}f}" if x is not None else " "*(w-1)+"-")
    print(f"  {c:10}{sp['n']:>7}{sr['n']:>7}{f(sp['mean_amd'])}{f(sr['mean_amd'])}"
          f"{f(kmd,10)}{f(sp['mean_z'],7,2)}{f(sr['mean_z'],7,2)}{f(kz,9)}")

json.dump(out, open(HERE/"aact_kappa.json","w"), indent=1)
print("\nwrote aact_kappa.json")
print("kappa_MD > 0 => published trials report LARGER HbA1c effects than registered-only (selection).")
