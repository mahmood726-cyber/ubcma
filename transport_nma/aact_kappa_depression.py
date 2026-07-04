"""EXTERNAL-VALIDATION REPLICATION in a 2nd therapeutic domain: antidepressants (Turner 2008's
own domain, the core analogy this method cites). Tests the transport-NMA manuscript's #1 stated
limitation ("single network/endpoint"): does the AACT registered-vs-published effect gap ALSO grow
with registry selection severity (1-lambda) outside diabetes/HbA1c?

Same machinery as aact_kappa.py, re-parameterised for depression:
  domain      = major depressive disorder trials (conditions)
  classes     = SSRI / SNRI / TCA / atypical / MAOI (intervention-name keyword sets)
  lambda_c    = results-posted / registered per class (depression trials)     [computed here]
  endpoint    = HAM-D (Hamilton Depression Rating Scale) change, single scale for comparability
  kappa_MD(c) = mean|HAM-D MD|_published / mean|HAM-D MD|_registered-only - 1  (PubMed-linked split)

Truth-first: honest whether corr(kappa_MD, 1-lambda) reproduces the diabetes +0.50 or not.
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

CLASSES = {
 'SSRI':['fluoxetine','sertraline','paroxetine','citalopram','escitalopram','fluvoxamine'],
 'SNRI':['venlafaxine','desvenlafaxine','duloxetine','milnacipran','levomilnacipran'],
 'TCA':['amitriptyline','nortriptyline','imipramine','clomipramine','desipramine','doxepin'],
 'atypical':['bupropion','mirtazapine','trazodone','vortioxetine','vilazodone','agomelatine','nefazodone'],
 'MAOI':['phenelzine','tranylcypromine','moclobemide','isocarboxazid'],
}

# depression trials
con.execute(f"""CREATE TEMP TABLE dep AS SELECT DISTINCT nct_id FROM {t('conditions')}
 WHERE lower(name) LIKE '%major depress%' OR lower(name) LIKE '%depressive disorder%'
    OR lower(name)='depression';""")
# published = PubMed-linked
con.execute(f"""CREATE TEMP TABLE pub AS SELECT DISTINCT nct_id FROM {t('study_references')}
 WHERE reference_type IN ('DERIVED','RESULT') AND pmid IS NOT NULL AND pmid<>'';""")
pubset = set(r[0] for r in con.execute("SELECT nct_id FROM pub").fetchall())

# lambda per class (results-posted / registered among depression trials)
con.execute(f"""CREATE TEMP TABLE iv AS SELECT i.nct_id, lower(i.name) nm,
   (s.results_first_posted_date IS NOT NULL AND s.results_first_posted_date<>'') posted
 FROM {t('interventions')} i JOIN dep d ON i.nct_id=d.nct_id
 JOIN {t('studies')} s ON i.nct_id=s.nct_id;""")
LAM = {}
for c, kws in CLASSES.items():
    cond = " OR ".join(f"nm LIKE '%{k}%'" for k in kws)
    tot, pos = con.execute(f"SELECT count(DISTINCT nct_id), count(DISTINCT CASE WHEN posted THEN nct_id END) FROM iv WHERE {cond}").fetchone()
    LAM[c] = (pos/tot) if tot else None

# HAM-D mean-difference analyses
con.execute(f"""CREATE TEMP TABLE hamd AS
 SELECT o.nct_id, TRY_CAST(a.param_value AS DOUBLE) md
 FROM {t('outcomes')} o
 JOIN {t('outcome_analyses')} a ON a.outcome_id=o.id
 JOIN dep d ON o.nct_id=d.nct_id
 WHERE (lower(o.title) LIKE '%ham-d%' OR lower(o.title) LIKE '%hamd%'
        OR lower(o.title) LIKE '%hamilton depression%' OR lower(o.title) LIKE '%hamilton rating scale for depression%'
        OR lower(o.title) LIKE '%hdrs%')
   AND lower(coalesce(a.param_type,'')) LIKE '%mean difference%'
   AND a.param_value IS NOT NULL;""")
rows = con.execute("SELECT nct_id, md FROM hamd WHERE md IS NOT NULL").fetchall()

# trial -> intervention names for class assignment
con.execute(f"""CREATE TEMP TABLE ivn AS SELECT nct_id, lower(name) nm FROM {t('interventions')}
 WHERE nct_id IN (SELECT nct_id FROM dep);""")
names = {}
for nct, nm in con.execute("SELECT nct_id, nm FROM ivn").fetchall():
    names.setdefault(nct, []).append(nm or "")
def classes_of(nct):
    s = " ".join(names.get(nct, []))
    return [c for c, kws in CLASSES.items() if any(k in s for k in kws)]

per = {c: {'pub': [], 'reg': []} for c in CLASSES}
kept = 0
for nct, md in rows:
    if md is None or not np.isfinite(md):
        continue
    amd = abs(md)
    if amd > 30:            # HAM-D total is 0-52; a between-arm MD > 30 is a coding error
        continue
    cs = classes_of(nct)
    if not cs:
        continue
    kept += 1
    b = 'pub' if nct in pubset else 'reg'
    for c in cs:
        per[c][b].append(amd)

print("="*84)
print("EXTERNAL-VALIDATION REPLICATION -- antidepressants / HAM-D (Turner 2008 domain)")
print("="*84)
print(f"  kept HAM-D mean-difference analyses: {kept}")
print(f"  {'class':10}{'lambda':>8}{'1-lam':>7}{'n_pub':>7}{'n_reg':>7}{'|MD|pub':>9}{'|MD|reg':>9}{'kappa_MD':>10}")
out = {}
xs, ys, ws = [], [], []
for c in CLASSES:
    p = np.array(per[c]['pub']); r = np.array(per[c]['reg'])
    lam = LAM[c]
    kmd = (p.mean()/r.mean() - 1.0) if (len(p) and len(r) and r.mean() > 0) else None
    out[c] = dict(lam=lam, n_pub=len(p), n_reg=len(r),
                  mean_pub=float(p.mean()) if len(p) else None,
                  mean_reg=float(r.mean()) if len(r) else None, kappa_md=kmd)
    def f(x, w=9, d=3): return (f"{x:>{w}.{d}f}" if x is not None else " "*(w-1)+"-")
    print(f"  {c:10}{f(lam,8)}{f((1-lam) if lam is not None else None,7)}{len(p):>7}{len(r):>7}"
          f"{f(p.mean() if len(p) else None)}{f(r.mean() if len(r) else None)}{f(kmd,10)}")
    if kmd is not None and lam is not None and min(len(p), len(r)) >= 8:
        xs.append(1-lam); ys.append(kmd); ws.append(min(len(p), len(r)))

if len(xs) >= 3:
    xs, ys, ws = map(np.array, (xs, ys, ws))
    corr = float(np.corrcoef(xs, ys)[0, 1])
    slope = float(np.sum(ws*xs*ys)/np.sum(ws*xs**2))
    kpool = float(np.sum(ws*np.maximum(0, ys))/np.sum(ws))
    print(f"\n  adequately-powered classes (min n>=8): {int(len(xs))}")
    print(f"  corr(kappa_MD, 1-lambda) = {corr:+.3f}   (diabetes/HbA1c reference: +0.50)")
    print(f"  WLS slope (external B) = {slope:.3f} ; kappa_pooled = {kpool:.3f}")
    verdict = ("REPRODUCES (positive corr, external gap grows with severity)" if corr > 0.3
               else "WEAK/DOES NOT reproduce" if corr < 0.15 else "PARTIAL")
    print(f"  VERDICT: {verdict}")
    out["_summary"] = dict(corr=corr, slope=slope, kappa_pooled=kpool, n_classes=int(len(xs)), verdict=verdict)
else:
    print(f"\n  only {len(xs)} adequately-powered classes -- INSUFFICIENT to test correlation (honest boundary)")
    out["_summary"] = dict(corr=None, n_classes=int(len(xs)), verdict="insufficient power")
json.dump(out, open(HERE/"aact_kappa_depression.json", "w"), indent=1)
print("wrote aact_kappa_depression.json")
