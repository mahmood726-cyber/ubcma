"""Compute the three deliverables + raw discrepancy rates, and emit a stratified
hand-validation sample.

Deliverables:
  1. Abstract-extraction USABILITY RATE (+ reason breakdown)
  2. Registry-results COVERAGE
  3. Per-class discrepancy rate (contradicts vs silent_on vs concordant)
Plus a validation sample for hand-adjudicated precision/recall.
"""
from __future__ import annotations
import json, collections, os
from common import OUT, DATA, load_json, save_json

def load_rows():
    rows = []
    with open(f"{OUT}/trials.jsonl", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows

def pct(n, d):
    return round(100.0 * n / d, 1) if d else None

def compute(rows):
    N = len(rows)
    completed = [r for r in rows if r["reg"]["overall_status"] == "COMPLETED"]
    with_results = [r for r in completed if r["reg"]["has_results"]]
    usable_reg = [r for r in with_results if r["reg"]["usable_registry"]]
    # 'index abstract' the scientist can actually retrieve for a trial = databank-confirmed
    with_index = [r for r in rows if r["index_pmid"] and r.get("index_confirmed")]
    with_index_any = [r for r in rows if r["index_pmid"]]
    with_reporting = [r for r in rows if r.get("n_reporting", 0) > 0]

    # --- Deliverable 2: registry coverage ---
    coverage = {
        "n_total": N,
        "n_completed": len(completed),
        "n_results_posted": len(with_results),
        "pct_completed_with_results": pct(len(with_results), len(completed)),
        "n_results_usable": len(usable_reg),
        "pct_results_posted_usable": pct(len(usable_reg), len(with_results)),
        "pct_completed_usable_registry": pct(len(usable_reg), len(completed)),
        "n_completed_with_reporting_pub": len([r for r in completed if r.get("n_reporting", 0) > 0]),
        "pct_completed_with_reporting_pub": pct(len([r for r in completed if r.get("n_reporting", 0) > 0]), len(completed)),
    }

    # --- Deliverable 1: abstract usability (per trial index abstract) ---
    reasons = collections.Counter(r["abstract"]["reason"] for r in with_index)
    usable = [r for r in with_index if r["abstract"]["usable"]]
    USABLE_REASONS = {"effect_with_ci", "means_sd", "effect_with_p"}
    usability = {
        "denominator_note": "trials with a databank-confirmed index abstract "
                            "(what a scientist can actually retrieve for the trial)",
        "n_with_index_abstract": len(with_index),
        "n_with_any_index_abstract": len(with_index_any),
        "n_usable": len(usable),
        "usability_rate_pct": pct(len(usable), len(with_index)),
        "reason_breakdown": dict(reasons.most_common()),
        "usable_reason_breakdown": {k: v for k, v in reasons.items() if k in USABLE_REASONS},
        "unusable_reason_breakdown": {k: v for k, v in reasons.items() if k not in USABLE_REASONS},
    }

    # --- Three-state poolability ---
    # effect-extraction reliability proxy: among usable abstracts that assert a CI-anchored
    # point, how many are self-consistent (point inside CI = NOT corrected).
    ci_effects = [r for r in with_index if (r["abstract"].get("effect") or {}).get("ci_lo") is not None]
    corrected = [r for r in ci_effects if (r["abstract"]["effect"] or {}).get("point_corrected")]
    extract_reliability = {
        "n_ci_anchored_effects": len(ci_effects),
        "n_point_outside_ci_corrected": len(corrected),
        "pct_self_consistent": pct(len(ci_effects) - len(corrected), len(ci_effects)),
        "note": "point-only (no-CI) extractions are NOT checkable and are less reliable; "
                "see hand-validation in PILOT_REPORT for adjudicated point-extraction precision",
    }

    states = collections.Counter(r["state"] for r in rows)
    poolability = {
        "BOTH_usable_dual_source": states.get("BOTH", 0),
        "ONE_usable_single_source": states.get("ONE", 0),
        "NEITHER_honest_exclusion": states.get("NEITHER", 0),
        "poolable_total": states.get("BOTH", 0) + states.get("ONE", 0),
        "poolable_pct": pct(states.get("BOTH", 0) + states.get("ONE", 0), N),
    }

    # --- Deliverable 3: per-class discrepancy rates ---
    classes = ["non_publication", "enrollment_mismatch", "direction_flip",
               "significance_flip", "primary_endpoint"]
    disc = {}
    for c in classes:
        cnt = collections.Counter()
        for r in rows:
            fl = r["flags"].get(c)
            if fl:
                cnt[fl["status"]] += 1
        contr = cnt.get("contradicts", 0) + cnt.get("switch_candidate", 0)
        conc = cnt.get("concordant", 0)
        denom_diffable = contr + conc  # both stated a fact -> comparable
        disc[c] = {
            "contradicts": cnt.get("contradicts", 0),
            "switch_candidate": cnt.get("switch_candidate", 0),
            "concordant": conc,
            "silent_on": cnt.get("silent_on", 0),
            "na": cnt.get("na", 0),
            "raw_discrepancy_rate_pct_of_diffable": pct(contr, denom_diffable),
            "diffable_denominator": denom_diffable,
        }
    disc["ma_omission"] = {"status": "GAP",
        "note": "requires a published-MA included-trials corpus; not attempted in first cut"}

    return {"coverage": coverage, "usability": usability,
            "extract_reliability": extract_reliability,
            "poolability": poolability, "discrepancy": disc}

def validation_sample(rows, per_bucket=8):
    """Stratified sample for hand adjudication: draw from each contradiction class +
    a concordant/usable control, deterministically (sorted by NCT)."""
    buckets = collections.defaultdict(list)
    for r in sorted(rows, key=lambda x: x["nct"]):
        for c, fl in r["flags"].items():
            if fl.get("status") in ("contradicts", "switch_candidate"):
                buckets[f"{c}:{fl['status']}"].append(r["nct"])
        if r["index_pmid"] and r["abstract"]["usable"]:
            buckets["abstract_usable_control"].append(r["nct"])
        if r["index_pmid"] and not r["abstract"]["usable"]:
            buckets[f"abstract_unusable:{r['abstract']['reason']}"].append(r["nct"])
    sample = {k: v[:per_bucket] for k, v in buckets.items()}
    return sample

def main():
    rows = load_rows()
    m = compute(rows)
    save_json(f"{OUT}/metrics.json", m)
    save_json(f"{OUT}/validation_sample.json", validation_sample(rows))
    print(json.dumps(m, indent=2))
    print("\n[metrics] -> out/metrics.json, out/validation_sample.json")

if __name__ == "__main__":
    main()
