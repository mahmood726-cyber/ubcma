"""Export the per-analysis HbA1c records that feed the external-magnitude estimate, so an external
vendor can independently re-derive kappa_MD / kappa_pooled / corr(kappa,1-lambda) WITHOUT any of our
code. Mirrors aact_kappa.py's extraction exactly; writes one row per kept HbA1c mean-difference
analysis: class, published flag, |MD| on NGSP-% scale. Run: python transport_nma/export_records.py
"""
import duckdb, json, io, sys, csv
import numpy as np
from pathlib import Path
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

A = r"F:\AACT-storage\AACT\2026-04-12"
HERE = Path(__file__).resolve().parent
con = duckdb.connect()


def t(n):
    return f"read_csv('{A}/{n}.txt', delim='|', header=true, quote='', ignore_errors=true, auto_detect=true, all_varchar=true)"


CLASSES = {
    'metformin': ['metformin'], 'SGLT2': ['gliflozin'], 'DPP4': ['gliptin'],
    'GLP1': ['glutide', 'exenatide', 'liraglutide', 'dulaglutide', 'semaglutide', 'lixisenatide', 'tirzepatide'],
    'SU': ['glipizide', 'glimepiride', 'glyburide', 'gliclazide', 'glibenclamide', 'sulfonylurea'],
    'TZD': ['glitazone', 'pioglitazone', 'rosiglitazone'], 'insulin': ['insulin'],
    'AGI': ['acarbose', 'miglitol', 'voglibose'], 'glinide': ['repaglinide', 'nateglinide'],
}

con.execute(f"""CREATE TEMP TABLE t2dm AS SELECT DISTINCT nct_id FROM {t('conditions')}
 WHERE lower(name) LIKE '%type 2 diabetes%' OR lower(name) LIKE '%type ii diabetes%';""")
con.execute(f"""CREATE TEMP TABLE pub AS SELECT DISTINCT nct_id FROM {t('study_references')}
 WHERE reference_type IN ('DERIVED','RESULT') AND pmid IS NOT NULL AND pmid<>'';""")
pubset = set(r[0] for r in con.execute("SELECT nct_id FROM pub").fetchall())
rows = con.execute(f"""SELECT o.nct_id, lower(coalesce(o.units,'')) units, TRY_CAST(a.param_value AS DOUBLE) md
 FROM {t('outcomes')} o JOIN {t('outcome_analyses')} a ON a.outcome_id = o.id JOIN t2dm d ON o.nct_id = d.nct_id
 WHERE (lower(o.title) LIKE '%hba1c%' OR lower(o.title) LIKE '%hemoglobin a1c%' OR lower(o.title) LIKE '%glycated%'
        OR lower(o.title) LIKE '%glycosylated hemoglobin%' OR lower(o.title) LIKE '%hemoglobin a1%')
   AND lower(coalesce(a.param_type,'')) LIKE '%mean difference%' AND a.param_value IS NOT NULL;""").fetchall()
con.execute(f"""CREATE TEMP TABLE iv AS SELECT nct_id, lower(name) nm FROM {t('interventions')} WHERE nct_id IN (SELECT nct_id FROM t2dm);""")
names = {}
for nct, nm in con.execute("SELECT nct_id, nm FROM iv").fetchall():
    names.setdefault(nct, []).append(nm or "")


def classes_of(nct):
    s = " ".join(names.get(nct, []))
    return [c for c, kws in CLASSES.items() if any(k in s for k in kws)]


out = []
for nct, units, md in rows:
    f = 0.0915 if ('mmol/mol' in units or 'mmol / mol' in units) else 1.0
    amd = abs(md * f)
    if not np.isfinite(amd) or amd > 5:
        continue
    for c in classes_of(nct):
        out.append((nct, c, 1 if nct in pubset else 0, round(amd, 5)))

with open(HERE / "aact_hba1c_records.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["nct_id", "drug_class", "published", "abs_md_pct"])
    w.writerows(out)
print(f"wrote aact_hba1c_records.csv  ({len(out)} records, {len(set(r[0] for r in out))} trials)")
