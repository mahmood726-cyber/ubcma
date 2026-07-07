"""Phase-1 full-text lift report + hand-validation harness (offline, model-free).

Combines the abstract+registry baseline with the full-text recoveries and produces:
  - the headline poolable-rate lift (per area + pooled),
  - the OA-available fraction and honest miss/bronze/unparseable bounds,
  - structural integrity checks (100% source-span; point-in-CI on every emitted number),
  - a hand-validation sample (with the registry primary effect as a cross-check anchor).

Reads only cached JSON + the fused outputs. No network, no model.
"""
from __future__ import annotations
import sys, os, io, json, glob
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
from common import OUT, CT_DIR, cache_path, load_json
from extract import extract_registry

def _fused_rows(area):
    """Trial-denominated: one row per trial (do NOT collapse by pmid)."""
    return [json.loads(l) for l in open(os.path.join(OUT, f"enriched_{area}.jsonl"), encoding="utf-8")]

def _ft(area):
    p = os.path.join(OUT, f"fulltext_enriched_{area}.jsonl")
    rows = [json.loads(l) for l in open(p, encoding="utf-8")] if os.path.exists(p) else []
    return {str(r["pmid"]): r for r in rows}

def _fetch_status(area):
    d = load_json(os.path.join(OUT, f"fulltext_fetch_{area}.json")) or {"results": []}
    return d["results"]

def integrity(area):
    """Every emitted full-text datapoint must (a) carry a source span, (b) have
    point inside CI when both present. Returns violation list (should be empty)."""
    viol = []
    for pmid, r in _ft(area).items():
        dp = r.get("datapoint")
        if not dp:
            continue
        span = dp.get("provenance", {}).get("source_span")
        if not span:
            viol.append((pmid, "no_source_span"))
        pt, lo, hi = dp.get("point"), dp.get("ci_lo"), dp.get("ci_hi")
        if pt is not None and lo is not None and hi is not None:
            a, b = min(lo, hi), max(lo, hi)
            if not (a - 1e-9 <= pt <= b + 1e-9):
                viol.append((pmid, f"point_outside_ci {pt}∉[{lo},{hi}]"))
    return viol

def validation_sample(area, k=12):
    """Surface emitted full-text datapoints for manual precision adjudication, with
    the registry primary effect (if any) as an independent anchor."""
    out = []
    for pmid, r in _ft(area).items():
        dp = r.get("datapoint")
        if not dp:
            continue
        reg = extract_registry(load_json(cache_path(CT_DIR, r["nct"])) or {})
        rp = reg.get("registry_primary") or {}
        out.append({
            "nct": r["nct"], "pmid": pmid, "channel": r["channel"],
            "source_doc": dp["provenance"]["source_doc"],
            "effect_type": dp.get("effect_type"), "point": dp.get("point"),
            "ci_lo": dp.get("ci_lo"), "ci_hi": dp.get("ci_hi"), "pvalue": dp.get("pvalue"),
            "confidence": dp["provenance"].get("confidence"),
            "registry_primary_effect": {"family": rp.get("family"), "point": rp.get("point"),
                                        "ci_lo": rp.get("ci_lo"), "ci_hi": rp.get("ci_hi"),
                                        "measure": rp.get("measure_title")},
            "source_span": dp["provenance"]["source_span"][:400],
        })
    out.sort(key=lambda x: x["pmid"])
    return out[:k] if k else out

def area_summary(area):
    base_rows = _fused_rows(area); ft = _ft(area)
    denom = len(base_rows)
    base = sum(1 for r in base_rows if r["fused_usable"])
    ft_rec = [r for r in ft.values() if r.get("ft_usable")]
    new = base + len(ft_rec)
    from collections import Counter
    fs = _fetch_status(area)
    fetch_ct = Counter(s["status"].split(":")[0] for s in fs)
    parsed = sum(1 for s in fs if s["status"] == "parsed")
    ch = Counter(r["channel"] for r in ft_rec)
    return {
        "area": area, "denominator": denom,
        "baseline_fused_usable": base, "baseline_pct": round(100*base/denom, 1),
        "gap_trials": denom - base,
        "gap_fetch_attempted": len(fs), "gap_fulltext_parsed": parsed,
        "gap_examined_by_extractor": len(ft),
        "ft_recovered": len(ft_rec), "ft_recovered_by_channel": dict(ch),
        "new_poolable": new, "new_poolable_pct": round(100*new/denom, 1),
        "lift_pts": round(100*(new-base)/denom, 1),
        "relative_increase_pct": round(100*(new-base)/base, 1) if base else None,
        "fetch_status_breakdown": dict(fetch_ct),
    }

def main():
    areas = ["t2d", "onc"]
    summ = {a: area_summary(a) for a in areas}
    # pooled
    dd = sum(summ[a]["denominator"] for a in areas)
    bb = sum(summ[a]["baseline_fused_usable"] for a in areas)
    nn = sum(summ[a]["new_poolable"] for a in areas)
    pooled = {"denominator": dd, "baseline": bb, "baseline_pct": round(100*bb/dd, 1),
              "new_poolable": nn, "new_poolable_pct": round(100*nn/dd, 1),
              "lift_pts": round(100*(nn-bb)/dd, 1),
              "relative_increase_pct": round(100*(nn-bb)/bb, 1)}
    integ = {a: integrity(a) for a in areas}
    report = {"per_area": summ, "pooled": pooled,
              "integrity_violations": integ,
              "source_linked_pct": 100.0 if not (integ["t2d"] or integ["onc"]) else None}
    save = os.path.join(OUT, "fulltext_lift_report.json")
    json.dump(report, open(save, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    # validation samples
    for a in areas:
        vs = validation_sample(a, k=0)
        json.dump(vs, open(os.path.join(OUT, f"ft_validation_{a}.json"), "w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)
        print(f"[{a}] wrote {len(vs)} emitted datapoints for validation")
    print("wrote", save)

if __name__ == "__main__":
    main()
