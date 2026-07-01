"""Map the MADRS antidepressant-vs-placebo slice into the pilot-3 transport
schema so the SAME borrowing machinery runs. Candidate population modifier =
WB under-5 mortality (the only covariate with a nominally significant
class+scale-adjusted slope in the screen). Adds baseline MADRS severity for the
relevance kernel. pop_ob := pop_mort so borrowing_transport.py works unchanged.
"""
import duckdb, json
import numpy as np
A = r"F:\AACT-storage\AACT\2026-04-12"
con = duckdb.connect()
def t(n): return (f"read_csv('{A}/{n}.txt', delim='|', header=true, quote='', "
                  f"ignore_errors=true, auto_detect=true, all_varchar=true)")

trials = [r for r in json.load(open("dep_trials.json"))
          if r["scale"] == "MADRS" and r.get("pop_mort") is not None]
ncts = sorted(r["nct_id"] for r in trials); nlist = "','".join(ncts)
# baseline MADRS severity (mean across baseline arms)
base = con.execute(f"""SELECT nct_id, avg(TRY_CAST(param_value_num AS DOUBLE)) bl
   FROM {t('baseline_measurements')}
   WHERE nct_id IN ('{nlist}')
     AND (lower(title) LIKE '%madrs%' OR lower(title) LIKE '%montgomery%')
     AND param_value_num IS NOT NULL GROUP BY 1""").fetchall()
based = {b[0]: b[1] for b in base if b[1] and 15 < b[1] < 50}

out = []
for r in trials:
    out.append(dict(
        nct_id=r["nct_id"], active=r["active"], y=r["y"], se=r["se"],
        baseline=based.get(r["nct_id"]), scale="MADRS",
        pop_ob=r["pop_mort"],          # <- candidate modifier mapped to the engine's slot
        pop_mort=r["pop_mort"], pop_sdi=r.get("pop_sdi"),
        countries=r["countries"], n_countries=r["n_countries"],
        single_country=r["single_country"],
        target_country=r["countries"][0] if r["single_country"] else None,
    ))
json.dump(out, open("dep_madrs_transport.json", "w"), indent=1)
ob = np.array([r["pop_ob"] for r in out])
print(f"MADRS transport slice: {len(out)} trials")
print(f"  under-5 mort (pop_ob slot): min {ob.min():.1f} med {np.median(ob):.1f} max {ob.max():.1f} SD {ob.std():.2f}")
print(f"  with baseline severity: {sum(1 for r in out if r['baseline'])}/{len(out)}")
print(f"  single-country targets : {sum(1 for r in out if r['single_country'])}")
from collections import Counter
print("  single-country countries:", Counter(r['target_country'] for r in out if r['single_country']))
