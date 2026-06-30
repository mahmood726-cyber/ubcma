"""GWAM-style registry-linkage integrity ratio per drug class: fraction of
REGISTERED T2DM trials naming that class (interventions table) that actually
posted results. Low lambda = selection-prone class -> borrow from it less."""
import duckdb, json
A=r"F:\AACT-storage\AACT\2026-04-12"
con=duckdb.connect()
def t(n): return f"read_csv('{A}/{n}.txt', delim='|', header=true, quote='', ignore_errors=true, auto_detect=true, all_varchar=true)"
con.execute(f"""CREATE TEMP TABLE t2dm AS SELECT DISTINCT nct_id FROM {t('conditions')}
 WHERE lower(name) LIKE '%type 2 diabetes%' OR lower(name) LIKE '%type ii diabetes%';""")
con.execute(f"""CREATE TEMP TABLE iv AS SELECT i.nct_id, lower(i.name) nm,
   (s.results_first_posted_date IS NOT NULL AND s.results_first_posted_date<>'') posted
 FROM {t('interventions')} i JOIN t2dm d ON i.nct_id=d.nct_id
 JOIN {t('studies')} s ON i.nct_id=s.nct_id;""")
CLASSES={'metformin':['metformin'],
 'SGLT2':['gliflozin'],'DPP4':['gliptin'],
 'GLP1':['glutide','exenatide','liraglutide','dulaglutide','semaglutide','lixisenatide','tirzepatide'],
 'SU':['glipizide','glimepiride','glyburide','gliclazide','glibenclamide','sulfonylurea'],
 'TZD':['glitazone'],'insulin':['insulin'],'AGI':['acarbose','miglitol','voglibose'],
 'glinide':['repaglinide','nateglinide']}
lam={}
for c,kws in CLASSES.items():
    cond=" OR ".join(f"nm LIKE '%{k}%'" for k in kws)
    r=con.execute(f"SELECT count(DISTINCT nct_id), count(DISTINCT CASE WHEN posted THEN nct_id END) FROM iv WHERE {cond}").fetchone()
    tot,pos=r
    lam[c]= (pos/tot) if tot else None
    print(f"  {c:9} registered={tot:5d}  results-posted={pos:5d}  lambda={lam[c]:.3f}" if tot else f"  {c}: none")
json.dump(lam, open('class_lambda.json','w'), indent=2)
print("wrote class_lambda.json")
