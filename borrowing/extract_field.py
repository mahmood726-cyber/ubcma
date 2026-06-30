import duckdb
A = r"F:\AACT-storage\AACT\2026-04-12"
con = duckdb.connect()
def t(name): return f"read_csv('{A}/{name}.txt', delim='|', header=true, quote='', ignore_errors=true, auto_detect=true, all_varchar=true)"

con.execute(f"""
CREATE TEMP TABLE t2dm AS
SELECT DISTINCT nct_id FROM {t('conditions')}
WHERE lower(name) LIKE '%type 2 diabetes%' OR lower(name) LIKE '%type ii diabetes%';
""")
con.execute(f"""
CREATE TEMP TABLE hba1c_out AS
SELECT id AS outcome_id, nct_id, title, units, param_type AS out_param_type
FROM {t('outcomes')}
WHERE (lower(title) LIKE '%hba1c%' OR lower(title) LIKE '%glycated hemoglobin%'
    OR lower(title) LIKE '%glycosylated hemoglobin%' OR lower(title) LIKE '%hemoglobin a1c%')
  AND (lower(title) LIKE '%chang%' OR lower(title) LIKE '%reduction%'
    OR lower(title) NOT LIKE '%percentage of%');
""")
# analyses: mean-difference family with both CI limits and numeric param_value
con.execute(f"""
CREATE TEMP TABLE eff AS
SELECT a.nct_id, a.outcome_id, a.id AS analysis_id,
       a.param_type, TRY_CAST(a.param_value AS DOUBLE) AS md,
       TRY_CAST(a.ci_lower_limit AS DOUBLE) AS lo,
       TRY_CAST(a.ci_upper_limit AS DOUBLE) AS hi,
       TRY_CAST(a.ci_percent AS DOUBLE) AS cipct, a.p_value, a.method
FROM {t('outcome_analyses')} a
JOIN hba1c_out o ON a.outcome_id = o.outcome_id AND a.nct_id = o.nct_id
JOIN t2dm d ON a.nct_id = d.nct_id
WHERE lower(a.param_type) LIKE '%mean difference%'
  AND a.ci_lower_limit IS NOT NULL AND a.ci_upper_limit IS NOT NULL;
""")
n = con.execute("SELECT count(*) FROM eff").fetchone()[0]
print("raw MD analysis rows:", n)
# sanity: distribution of md and implied se (95% CI)
rows = con.execute("""
SELECT md, lo, hi, cipct FROM eff
WHERE md IS NOT NULL AND lo IS NOT NULL AND hi IS NOT NULL AND hi> lo
""").fetchall()
import numpy as np
md = np.array([r[0] for r in rows]); lo=np.array([r[1] for r in rows]); hi=np.array([r[2] for r in rows])
cip=np.array([r[3] if r[3] else 95.0 for r in rows])
z = {90:1.6449,95:1.95996,99:2.5758}
zz = np.array([z.get(int(round(c)),1.95996) for c in cip])
se = (hi-lo)/(2*zz)
# keep plausible HbA1c MDs: |md|<5 (%), se in (0,3)
ok = (np.abs(md)<5) & (se>0) & (se<3)
print(f"usable effect rows (sane HbA1c MD): {ok.sum()} / {len(md)}")
print(f"  md: median={np.median(md[ok]):.3f}  q05={np.quantile(md[ok],.05):.3f}  q95={np.quantile(md[ok],.95):.3f}")
print(f"  se: median={np.median(se[ok]):.3f}  q05={np.quantile(se[ok],.05):.3f}  q95={np.quantile(se[ok],.95):.3f}")
con.execute("COPY eff TO 'eff_raw.parquet' (FORMAT parquet)")
print("wrote eff_raw.parquet")
