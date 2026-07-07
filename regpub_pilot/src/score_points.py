"""Objective point-extraction precision: for trials where the REGISTRY has a usable
primary effect (ground truth for the same trial's primary), compare the abstract-side
point estimate from (a) the deterministic regex and (b) the verified LLM datapoint.

A point is 'correct' if same family and within tolerance of the registry value:
  ratio: |log(p_abs/p_reg)| < 0.10   (~10% multiplicative)
  diff : |p_abs - p_reg| <= max(0.1, 5% of |p_reg|)
Registry and abstract occasionally report different co-primaries/timepoints; those
surface as mismatches and are inspected in the hand-validation (report caveat).
"""
from __future__ import annotations
import sys, io, json, math
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
from common import OUT, CT_DIR, cache_path, load_json
from extract import extract_registry, classify_abstract
from common import PM_DIR

def close(fam, a, b):
    if a is None or b is None:
        return None
    if fam == "ratio":
        if a <= 0 or b <= 0:
            return abs(a - b) < 0.05
        return abs(math.log(a / b)) < 0.10
    return abs(a - b) <= max(0.1, 0.05 * abs(b))

def main():
    area = sys.argv[1] if len(sys.argv) > 1 else "t2d"
    rows = [json.loads(l) for l in open(f"{OUT}/enriched_{area}.jsonl", encoding="utf-8")]
    det_tot = det_ok = llm_tot = llm_ok = 0
    mism = []
    for r in rows:
        rec = load_json(cache_path(CT_DIR, r["nct"])) or {}
        reg = extract_registry(rec)
        rp = reg.get("registry_primary") or {}
        if not reg["usable_registry"] or rp.get("point") is None or rp.get("family") not in ("ratio", "diff"):
            continue
        rfam, rpt = rp["family"], rp["point"]
        # deterministic abstract effect
        prec = load_json(cache_path(PM_DIR, r["pmid"])) or {}
        det = classify_abstract(prec)
        de = det.get("effect") or {}
        if de.get("point") is not None and de.get("family") == rfam:
            det_tot += 1
            ok = close(rfam, de["point"], rpt)
            det_ok += 1 if ok else 0
        # LLM datapoint
        dp = r.get("datapoint") or {}
        lp = dp.get("point")
        lfam = "ratio" if (dp.get("effect_type") or "").upper() in ("HR", "OR", "RR", "RATE_RATIO") else ("diff" if dp.get("effect_type") == "mean_difference" else None)
        if lp is not None and lfam == rfam:
            llm_tot += 1
            ok = close(rfam, lp, rpt)
            llm_ok += 1 if ok else 0
            if not ok:
                mism.append((r["nct"], r["pmid"], rfam, "reg", rpt, "llm", lp, dp.get("provenance", {}).get("source_span", "")[:80]))
    print(f"REGISTRY-anchored point precision (same-family comparisons):")
    print(f"  deterministic regex: {det_ok}/{det_tot} = {round(100*det_ok/det_tot,1) if det_tot else None}%")
    print(f"  LLM verified       : {llm_ok}/{llm_tot} = {round(100*llm_ok/llm_tot,1) if llm_tot else None}%")
    print(f"\nLLM mismatches vs registry (inspect — may be co-primary/timepoint diffs):")
    for m in mism:
        print("  ", m)
    save = {"det_ok": det_ok, "det_tot": det_tot,
            "det_precision_pct": round(100*det_ok/det_tot,1) if det_tot else None,
            "llm_ok": llm_ok, "llm_tot": llm_tot,
            "llm_precision_pct": round(100*llm_ok/llm_tot,1) if llm_tot else None,
            "mismatches": [{"nct": m[0], "pmid": m[1], "family": m[2], "reg": m[4], "llm": m[6], "span": m[7]} for m in mism]}
    from common import save_json
    save_json(f"{OUT}/point_precision_{area}.json", save)

if __name__ == "__main__":
    main()
