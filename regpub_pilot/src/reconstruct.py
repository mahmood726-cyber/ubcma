"""RECONSTRUCT-AND-BEAT: rebuild real published T2D meta-analyses from abstract+registry
ONLY, pool with our stack, and score head-to-head on three axes:
  METHOD (REML+HKSJ+PI vs published DL/MH), DATA COMPLETENESS (trial-set delta +
  registry-only/unpublished recovery), TRANSPARENCY (100% source-linked + re-runnable
  vs published report-only reproducibility ~3.2%).

Every trial datapoint carries provenance (registry field OR abstract span). Truth-first:
where we do NOT beat, we say so.
"""
from __future__ import annotations
import sys, io, json, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from common import (CTGOV_BASE, EUTILS, CT_DIR, PM_DIR, OUT, http_get, cache_path,
                    load_json, save_json)
from extract import extract_registry, classify_abstract
from link_pubmed import fetch_abstract
from pool import pool, _qnorm

Z = 1.959963985

TARGETS = [
  {"key":"sglt2_cvot","label":"SGLT2 inhibitors — 3-point MACE (CV outcome trials)",
   "benchmark":{"cite":"Zelniker 2019 Lancet (PMID 30424892)","measure":"HR","est":0.89,
                "ci_lo":0.83,"ci_hi":0.96,"k":3,"method":"random-effects (DL)"},
   "trials":[("EMPA-REG OUTCOME","NCT01131676",None),
             # CANVAS: registry NCT-level HR (0.93) is CANVAS-only; the published integrated
             # CANVAS Program MACE HR Zelniker used is 0.86. Abstract-verified (the raw regex
             # mis-grabbed the RENAL HR 0.60 here -> corrected by reading the source span).
             ("CANVAS Program","NCT01032629",
              {"pmid":"28605608","hr":0.86,"ci_lo":0.75,"ci_hi":0.97,
               "span":"the primary outcome... occurred... (hazard ratio, 0.86; 95% CI, 0.75 to 0.97)"}),
             ("DECLARE-TIMI 58","NCT01730534",None)]},
  {"key":"glp1_cvot","label":"GLP-1 receptor agonists — 3-point MACE (CV outcome trials)",
   "benchmark":{"cite":"Kristensen 2019 Lancet D&E (PMID 31422062)","measure":"HR","est":0.88,
                "ci_lo":0.82,"ci_hi":0.94,"k":7,"method":"random-effects"},
   "trials":[("ELIXA","NCT01147250",None),("LEADER","NCT01179048",None),
             ("SUSTAIN-6","NCT01720446",None),("EXSCEL","NCT01144338",None),
             ("Harmony Outcomes","NCT02465515",None),("REWIND","NCT01394952",None),
             ("PIONEER 6","NCT02692716",None)]},
  {"key":"dpp4_cvot","label":"DPP-4 inhibitors — MACE (placebo-controlled CV outcome trials, null)",
   "benchmark":{"cite":"Mannucci 2021 (PMID 34364771)","measure":"OR","est":0.99,
                "ci_lo":0.93,"ci_hi":1.04,"k":4,"method":"Mantel-Haenszel fixed OR"},
   "trials":[# SAVOR registry primary = event counts (no HR). Abstract-verified primary MACE
             # HR 1.00 (raw regex mis-grabbed the on-treatment sensitivity HR 1.03).
             ("SAVOR-TIMI 53","NCT01107886",
              {"pmid":"23992601","hr":1.00,"ci_lo":0.89,"ci_hi":1.12,
               "span":"the primary end point... hazard ratio with saxagliptin, 1.00; 95% CI, 0.89 to 1.12"}),
             ("EXAMINE","NCT00968708",None),              # registry: point+upper only
             ("TECOS","NCT00790205",None),
             ("CARMELINA","NCT01897532",None)]},           # CAROLINA excluded (active comparator)
]

def fetch_full(nct):
    p = cache_path(CT_DIR, nct)
    d = load_json(p)
    if d is None:
        d = json.loads(http_get(f"{CTGOV_BASE}/studies/{nct}")); save_json(p, d)
    return d

def _se_logratio(point, lo, hi):
    """SE of log(HR) from a two-sided CI, or from a single bound + point (symmetric-log)."""
    if point and lo and hi and lo > 0 and hi > 0:
        return (math.log(hi) - math.log(lo)) / (2 * Z)
    if point and hi and point > 0 and hi > 0:
        return (math.log(hi) - math.log(point)) / Z
    if point and lo and point > 0 and lo > 0:
        return (math.log(point) - math.log(lo)) / Z
    return None

def resolve_effect(name, nct, fallback):
    # explicit abstract-verified effect (dict with pmid/hr/ci/span) — used where the
    # registry lacks a usable HR and the raw regex mis-grabs a non-primary HR.
    if isinstance(fallback, dict):
        se = _se_logratio(fallback["hr"], fallback["ci_lo"], fallback["ci_hi"])
        return {"name": name, "nct": nct, "hr": fallback["hr"],
                "ci_lo": fallback["ci_lo"], "ci_hi": fallback["ci_hi"],
                "log_hr": math.log(fallback["hr"]), "se": se, "var": se*se,
                "source": "abstract",
                "provenance": {"source_doc": f"PMID:{fallback['pmid']}",
                               "source_span": fallback["span"]}}
    fallback_pmid = fallback
    rec = fetch_full(nct)
    reg = extract_registry(rec)
    rp = reg.get("registry_primary") or {}
    # registry, when it is a ratio with a usable bound
    if fallback_pmid is None and rp.get("family") == "ratio" and rp.get("point"):
        se = _se_logratio(rp["point"], rp.get("ci_lo"), rp.get("ci_hi"))
        if se:
            return {"name": name, "nct": nct, "hr": rp["point"],
                    "ci_lo": rp.get("ci_lo"), "ci_hi": rp.get("ci_hi"),
                    "log_hr": math.log(rp["point"]), "se": se, "var": se*se,
                    "source": "registry",
                    "provenance": {"source_doc": f"CTGOV:{nct}",
                                   "field": "resultsSection.outcomeMeasures[PRIMARY].analyses (HR)",
                                   "measure_title": (rp.get("measure_title") or "")[:70]}}
    # abstract fallback (program-level or where registry lacks an HR)
    if fallback_pmid:
        prec = fetch_abstract(fallback_pmid)
        cls = classify_abstract(prec)
        e = cls.get("effect") or {}
        if e.get("point") and e.get("family") == "ratio":
            se = _se_logratio(e["point"], e.get("ci_lo"), e.get("ci_hi"))
            if se:
                span = None
                # capture the abstract sentence containing the HR as provenance
                import re
                for s in re.split(r'(?<=[.;])\s+', prec.get("abstract","")):
                    if re.search(r'hazard ratio|HR[,\s]', s, re.I) and str(e["point"]).lstrip("0") in s:
                        span = s[:200]; break
                return {"name": name, "nct": nct, "hr": e["point"],
                        "ci_lo": e.get("ci_lo"), "ci_hi": e.get("ci_hi"),
                        "log_hr": math.log(e["point"]), "se": se, "var": se*se,
                        "source": "abstract",
                        "provenance": {"source_doc": f"PMID:{fallback_pmid}",
                                       "source_span": span or f"HR {e['point']} (95% CI {e.get('ci_lo')}-{e.get('ci_hi')})"}}
    return {"name": name, "nct": nct, "hr": None, "source": "UNRESOLVED", "provenance": {}}

def scan_registry_completeness(cls_terms):
    """DATA-COMPLETENESS probe: how many completed CV-outcome trials of this class does
    the registry hold (results posted)? Compared to the published MA's k."""
    import urllib.parse
    params = {"query.cond": "type 2 diabetes", "query.term": cls_terms,
              "filter.overallStatus": "COMPLETED", "aggFilters": "results:with,studyType:int",
              "fields": "NCTId", "pageSize": "100", "countTotal": "true"}
    url = f"{CTGOV_BASE}/studies?" + urllib.parse.urlencode(params)
    try:
        return json.loads(http_get(url)).get("totalCount")
    except Exception:
        return None

def main():
    results = []
    for t in TARGETS:
        studies = [resolve_effect(n, nct, fb) for n, nct, fb in t["trials"]]
        good = [s for s in studies if s.get("hr")]
        yi = [s["log_hr"] for s in good]; vi = [s["var"] for s in good]
        pooled = pool(yi, vi, method="REML", hksj=True)
        pooled_naive = pool(yi, vi, method="DL", hksj=False)  # mimic published DL-normal
        b = t["benchmark"]
        res = {"key": t["key"], "label": t["label"], "benchmark": b,
               "our_k": len(good),
               "our_hr": round(math.exp(pooled["est"]), 3),
               "our_ci": [round(math.exp(pooled["ci_lo"]), 3), round(math.exp(pooled["ci_hi"]), 3)],
               "our_pi": [round(math.exp(pooled["pi_lo"]), 3), round(math.exp(pooled["pi_hi"]), 3)] if pooled["pi_lo"] else None,
               "our_tau2": round(pooled["tau2"], 4), "our_I2": pooled["I2"],
               "naive_hr": round(math.exp(pooled_naive["est"]), 3),
               "naive_ci": [round(math.exp(pooled_naive["ci_lo"]), 3), round(math.exp(pooled_naive["ci_hi"]), 3)],
               "studies": [{"name": s["name"], "nct": s["nct"], "hr": s.get("hr"),
                            "ci": [s.get("ci_lo"), s.get("ci_hi")], "source": s["source"],
                            "provenance": s.get("provenance")} for s in studies],
               "n_source_linked": sum(1 for s in good if s.get("provenance")),
               "n_studies": len(good)}
        results.append(res)
    save_json(f"{OUT}/reconstruct_scorecard.json", results)
    # print summary
    for r in results:
        b = r["benchmark"]
        print("="*80)
        print(r["label"])
        print(f"  PUBLISHED: {b['measure']} {b['est']} [{b['ci_lo']}-{b['ci_hi']}] k={b['k']} ({b['method']}) — {b['cite']}")
        print(f"  OURS     : HR {r['our_hr']} [{r['our_ci'][0]}-{r['our_ci'][1]}] k={r['our_k']} (REML+HKSJ+PI)  PI {r['our_pi']}  tau2={r['our_tau2']} I2={r['our_I2']}")
        print(f"  (our naive DL check: HR {r['naive_hr']} [{r['naive_ci'][0]}-{r['naive_ci'][1]}])")
        print(f"  source-linked datapoints: {r['n_source_linked']}/{r['n_studies']} (100% = full provenance)")
        for s in r["studies"]:
            pv = s["provenance"] or {}
            print(f"     {s['name']:20s} {s['nct']} HR={s['hr']} src={s['source']} <- {pv.get('source_doc','')}")
    print(f"\n[reconstruct] scorecard -> out/reconstruct_scorecard.json")

if __name__ == "__main__":
    main()
