import duckdb, sys
A = r"F:\AACT-storage\AACT\2026-04-12"
con = duckdb.connect()
def t(name): return f"read_csv('{A}\{name}.txt', delim='|', header=true, quote='', ignore_errors=true, auto_detect=true, all_varchar=true)"

# 1) T2DM nct_ids
q1 = f"""
SELECT count(DISTINCT nct_id) FROM {t('conditions')}
WHERE lower(name) LIKE '%type 2 diabetes%' OR lower(name) LIKE '%type ii diabetes%'
   OR lower(downcase_name) LIKE '%type 2 diabetes%'
"""
try:
    print("T2DM trials:", con.execute(q1).fetchone())
except Exception as e:
    print("q1 err (downcase?):", str(e)[:200])
    q1b = f"SELECT count(DISTINCT nct_id) FROM {t('conditions')} WHERE lower(name) LIKE '%type 2 diabetes%'"
    print("T2DM trials:", con.execute(q1b).fetchone())

# 2) HbA1c outcomes overall
q2 = f"""
SELECT count(*) FROM {t('outcomes')}
WHERE lower(title) LIKE '%hba1c%' OR lower(title) LIKE '%glycated h%'
   OR lower(title) LIKE '%glycosylated h%' OR lower(title) LIKE '%hemoglobin a1c%'
   OR lower(title) LIKE '%a1c%'
"""
print("HbA1c outcomes (all):", con.execute(q2).fetchone())

# 3) outcome_analyses param_type distribution
q3 = f"""
SELECT param_type, count(*) c FROM {t('outcome_analyses')}
GROUP BY 1 ORDER BY c DESC LIMIT 15
"""
print("param_type top:")
for r in con.execute(q3).fetchall(): print("   ", r)
