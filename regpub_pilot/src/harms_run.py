"""Run harms-omission + routing-rule analysis per disease, per the pre-registration.

Outputs out/harms_<area>.json:
  - registry serious-AE completeness (of results-posted trials)
  - harms-omission / under-report / concordant rates (denominator = registry-has-SAE AND
    databank-confirmed RESULTS abstract)
  - routing rule: registry-table-only vs abstract-prose-only availability of a usable number
"""
from __future__ import annotations
import sys, io, json, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")
from common import CT_DIR, PM_DIR, OUT, cache_path, load_json, save_json, trials_out
from harms import extract_registry_harms, classify_abstract_harms, harms_verdict

def pct(n, d):
    return round(100.0 * n / d, 1) if d else None

def run(area):
    rows = [json.loads(l) for l in open(trials_out(area), encoding="utf-8")]
    # --- registry serious-AE completeness (of results-posted) ---
    results_posted = [r for r in rows if r["reg"].get("has_results")]
    n_sae = 0
    for r in results_posted:
        rec = load_json(cache_path(CT_DIR, r["nct"])) or {}
        if extract_registry_harms(rec).get("has_sae_data"):
            n_sae += 1
    sae_completeness = pct(n_sae, len(results_posted))

    # --- harms verdicts (denominator: registry-has-SAE AND confirmed results abstract) ---
    vc = collections.Counter()
    omitted_examples = []
    for r in rows:
        rec = load_json(cache_path(CT_DIR, r["nct"])) or {}
        reg_h = extract_registry_harms(rec)
        if not reg_h.get("has_sae_data"):
            continue
        pmid = r.get("index_pmid")
        confirmed = r.get("index_confirmed")
        abs_rec = load_json(cache_path(PM_DIR, pmid)) if pmid else None
        if not (pmid and confirmed):
            vc["na_no_confirmed_abstract"] += 1
            continue
        v = harms_verdict(reg_h, classify_abstract_harms(abs_rec))
        vc[v["status"]] += 1
        if v["status"] == "harms_omitted" and len(omitted_examples) < 12:
            omitted_examples.append({"nct": r["nct"], "pmid": pmid,
                                     "registry_serious": reg_h.get("total_serious_affected"),
                                     "at_risk": reg_h.get("total_at_risk")})
    # denominator for the omission RATE = trials with registry SAE + confirmed results abstract
    denom = (vc["harms_omitted"] + vc["harms_underreported"] + vc["harms_concordant"])
    harms = {
        "registry_sae_completeness_pct": sae_completeness,
        "n_results_posted": len(results_posted), "n_with_sae_data": n_sae,
        "harms_denominator": denom,
        "harms_omitted": vc["harms_omitted"],
        "harms_underreported": vc["harms_underreported"],
        "harms_concordant": vc["harms_concordant"],
        "harms_omission_rate_pct": pct(vc["harms_omitted"], denom),
        "harms_gap_rate_pct": pct(vc["harms_omitted"] + vc["harms_underreported"], denom),
        "excluded_nontrial_abstract": vc["na_nontrial_abstract"],
        "excluded_no_confirmed_abstract": vc["na_no_confirmed_abstract"],
        "excluded_no_abstract": vc["na_no_abstract"],
        "omitted_examples": omitted_examples,
    }

    # --- routing rule: registry-table vs abstract-prose provenance of a usable number ---
    reg_usable = [r for r in rows if r["reg"].get("usable_registry")]
    abs_usable = [r for r in rows if r.get("abstract") and r["abstract"].get("usable")]
    set_reg = {r["nct"] for r in reg_usable}
    set_abs = {r["nct"] for r in abs_usable}
    registry_only = set_reg - set_abs
    abstract_only = set_abs - set_reg
    both = set_reg & set_abs
    poolable = set_reg | set_abs
    routing = {
        "n_poolable": len(poolable),
        "registry_table_only": len(registry_only),
        "abstract_prose_only": len(abstract_only),
        "both": len(both),
        "registry_only_pct_of_poolable": pct(len(registry_only), len(poolable)),
        "abstract_only_pct_of_poolable": pct(len(abstract_only), len(poolable)),
        "registry_to_abstract_only_ratio": round(len(registry_only) / len(abstract_only), 2) if abstract_only else None,
    }
    out = {"area": area, "harms": harms, "routing": routing}
    save_json(f"{OUT}/harms_{area}.json", out)
    print(f"=== {area} ===")
    print(f"  registry SAE completeness: {sae_completeness}% ({n_sae}/{len(results_posted)} results-posted)")
    print(f"  harms omission: {harms['harms_omitted']}/{denom} = {harms['harms_omission_rate_pct']}% "
          f"(+ under-report {harms['harms_underreported']} -> gap {harms['harms_gap_rate_pct']}%; "
          f"concordant {harms['harms_concordant']})")
    print(f"  routing: registry-only {routing['registry_table_only']} vs abstract-only {routing['abstract_prose_only']} "
          f"(ratio {routing['registry_to_abstract_only_ratio']}x) of {routing['n_poolable']} poolable")
    return out

if __name__ == "__main__":
    areas = sys.argv[1:] or ["malaria", "tb", "t2d", "onc"]
    for a in areas:
        run(a)
