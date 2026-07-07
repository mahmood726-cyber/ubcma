"""Sanity tests for the deterministic extractors against known-truth trials.

EMPA-REG (NCT01131676 / PMID 26378978): registry primary 3-point MACE HR 0.86,
CI 0.74-0.99, p<0.0001 (and 0.0382 superiority). Abstract is structured.
"""
import sys, json, urllib.request
sys.path.insert(0, ".")
from common import cache_path, CT_DIR, PM_DIR, load_json, save_json, http_get, EUTILS
from extract import extract_registry, classify_abstract
from link_pubmed import fetch_abstract

def _ensure_ctgov(nct):
    p = cache_path(CT_DIR, nct)
    d = load_json(p)
    if d is None:
        d = json.loads(http_get(f"https://clinicaltrials.gov/api/v2/studies/{nct}"))
        save_json(p, d)
    return d

def test_registry_empareg():
    d = _ensure_ctgov("NCT01131676")
    r = extract_registry(d)
    assert r["nct"] == "NCT01131676"
    assert r["enrollment_actual"] == 7064, r["enrollment_actual"]
    assert r["has_results"] and r["usable_registry"]
    rp = r["registry_primary"]
    assert rp["family"] == "ratio", rp["param_type"]
    assert abs(rp["point"] - 0.86) < 1e-9, rp["point"]
    assert abs(rp["ci_lo"] - 0.74) < 1e-9 and abs(rp["ci_hi"] - 0.99) < 1e-9
    assert rp["significant"] is True   # CI excludes 1 and p<0.05
    print("  [ok] registry EMPA-REG: HR", rp["point"], "CI", rp["ci_lo"], rp["ci_hi"], "sig", rp["significant"])

def test_abstract_empareg():
    rec = fetch_abstract("26378978")
    c = classify_abstract(rec)
    assert c["has_abstract"]
    # Zinman abstract reports "hazard ratio ... 0.86 ... 95% CI" -> effect_with_ci usable
    assert c["usable"], c
    print("  [ok] abstract EMPA-REG: usable via", c["reason"], "| effect:", c["effect"])

def test_synthetic_reasons():
    def mk(txt, label="RESULTS"):
        return {"pmid": "X", "abstract": txt, "abstract_sections": [{"label": label, "text": txt}]}
    assert classify_abstract(mk("The primary outcome occurred in 12% vs 15%, a relative reduction of 20%."))["reason"] == "relative_only"
    assert classify_abstract(mk("Median survival was 14.2 months (IQR 9-20)."))["reason"] == "median_no_dispersion"
    assert classify_abstract(mk("The difference was statistically significant (p<0.001)."))["reason"] == "pvalue_only"
    r = classify_abstract(mk("HbA1c fell 8.1 ± 1.2 in the treatment arm and 7.9 ± 1.1 in placebo."))
    assert r["usable"] and r["reason"] == "means_sd", r
    r = classify_abstract(mk("The hazard ratio was 0.75 (95% CI 0.60 to 0.94)."))
    assert r["usable"] and r["reason"] == "effect_with_ci" and abs(r["effect"]["point"]-0.75)<1e-9, r
    assert r["effect"]["significant"] is True
    assert classify_abstract(mk("Treatment was well tolerated with no new safety signals."))["reason"] == "narrative_only"
    print("  [ok] synthetic reason classification")

if __name__ == "__main__":
    for fn in (test_registry_empareg, test_abstract_empareg, test_synthetic_reasons):
        fn()
    print("ALL EXTRACT TESTS PASSED")
