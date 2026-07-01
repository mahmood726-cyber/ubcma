"""PILOT-4 HUNT step 1: which continuous between-group MEAN-DIFFERENCE outcome
families in AACT have (a) many trials, (b) wide COUNTRY/region spread? Those are
the only places a population covariate could be a *strong, transportable* effect
modifier. Pure survey -- no borrowing machinery, no covariate yet.
"""
from __future__ import annotations
import duckdb, re
A = r"F:\AACT-storage\AACT\2026-04-12"
con = duckdb.connect()
def t(n): return (f"read_csv('{A}/{n}.txt', delim='|', header=true, quote='', "
                  f"ignore_errors=true, auto_detect=true, all_varchar=true)")

# all between-group mean-difference analyses with usable CI
con.execute(f"""CREATE TEMP TABLE md AS
 SELECT a.nct_id, a.id AS analysis_id, o.title AS otitle,
        TRY_CAST(a.param_value AS DOUBLE) v,
        TRY_CAST(a.ci_lower_limit AS DOUBLE) lo,
        TRY_CAST(a.ci_upper_limit AS DOUBLE) hi
 FROM {t('outcome_analyses')} a
 JOIN {t('outcomes')} o ON a.outcome_id=o.id AND a.nct_id=o.nct_id
 WHERE lower(a.param_type) LIKE '%mean difference%'
   AND a.ci_lower_limit IS NOT NULL AND a.ci_upper_limit IS NOT NULL
   AND TRY_CAST(a.param_value AS DOUBLE) IS NOT NULL;""")
print("total between-group MD analyses:", con.execute("SELECT count(*) FROM md").fetchone()[0])
print("distinct trials with >=1 MD analysis:",
      con.execute("SELECT count(DISTINCT nct_id) FROM md").fetchone()[0])

# trial -> n distinct recruiting countries (real, not removed)
con.execute(f"""CREATE TEMP TABLE tc AS
 SELECT nct_id, count(DISTINCT name) ncty
 FROM {t('countries')} WHERE removed='f' GROUP BY nct_id;""")

# keyword buckets over outcome titles -> count distinct trials + country spread
KW = {
 'HbA1c (done)': r'hba1c|glycated h|glycosylated h|hemoglobin a1c',
 'systolic BP':  r'systolic blood pressure|sbp',
 'diastolic BP': r'diastolic blood pressure',
 'LDL chol':     r'ldl|low.?density lipo',
 'depression':   r'madrs|ham-?d|hamilton depress|montgomery|phq|depression sever',
 'pain (VAS/NRS)': r'pain (score|intensity|vas|nrs)|visual analog',
 'FEV1/lung':    r'fev1|forced expiratory',
 'weight/BMI':   r'body weight|weight \(|bmi|body mass',
 'eGFR/renal':   r'egfr|glomerular filtr',
 '6MWD':         r'6.?minute walk|six.?minute walk',
 'HAQ/disability': r'haq|disability index',
 'anxiety':      r'anxiety|ham-?a|gad-?7',
 'cognition/ADAS': r'adas|mmse|cogniti',
}
rows = con.execute("SELECT nct_id, otitle FROM md").fetchall()
import collections
bytrial = collections.defaultdict(set)  # bucket -> set of nct
for nct, ot in rows:
    s = (ot or '').lower()
    for b, pat in KW.items():
        if re.search(pat, s):
            bytrial[b].add(nct)
# country spread per bucket
cty = dict(con.execute("SELECT nct_id, ncty FROM tc").fetchall())
print(f"\n{'bucket':18} {'ntrials':>7} {'w/cty':>6} {'multi-cty':>9} {'med_ncty':>8}")
for b in KW:
    ncts = bytrial[b]
    withc = [cty[n] for n in ncts if n in cty]
    multi = sum(1 for c in withc if c >= 2)
    med = sorted(withc)[len(withc)//2] if withc else 0
    print(f"{b:18} {len(ncts):7d} {len(withc):6d} {multi:9d} {med:8d}")
