"""Dump the hand-validation sample as readable adjudication cards:
registry primary fact + abstract RESULTS text + the engine's auto-flags, so a human
can label each flag TP/FP and each usability verdict correct/incorrect.

Usage: python adjudicate_dump.py [class:status]   # optional filter, else all buckets
"""
from __future__ import annotations
import sys, io, json
# Windows cp1252 console/redirect trap (lessons.md): force UTF-8 stdout.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
from common import OUT, CT_DIR, PM_DIR, cache_path, load_json
from extract import extract_registry, classify_abstract
from diff import diff_trial

def card(nct, links):
    r = diff_trial(nct, links)
    reg = r["reg"]; rp = reg.get("registry_primary") or {}
    print("="*78)
    print(f"{nct}  | state={r['state']} | idx_pmid={r['index_pmid']} confirmed={r.get('index_confirmed')}")
    print(f"  REG start={reg.get('start_year')} enroll={reg.get('enrollment_actual')} "
          f"results={reg.get('has_results')} usable={reg.get('usable_registry')}")
    print(f"  REG primary endpoint(s): {reg.get('protocol_primary_endpoints')}")
    if rp:
        print(f"  REG primary result: {rp.get('measure_title','')[:80]!r}")
        print(f"     family={rp.get('family')} point={rp.get('point')} CI=({rp.get('ci_lo')},{rp.get('ci_hi')}) "
              f"p={rp.get('pvalue')} sig={rp.get('significant')}")
    ab = r.get("abstract")
    if ab:
        print(f"  ABS usable={ab.get('usable')} reason={ab.get('reason')} n={ab.get('abstract_n')} "
              f"effect={ab.get('effect')}")
        rec = load_json(cache_path(PM_DIR, r["index_pmid"])) if r["index_pmid"] else None
        if rec:
            res = " ".join(s["text"] for s in rec.get("abstract_sections", [])
                           if s.get("label") and "RESULT" in s["label"].upper()) or rec.get("abstract", "")
            print(f"  ABS title: {rec.get('title','')[:90]}")
            print(f"  ABS results: {res[:700]}")
    print("  FLAGS:")
    for c, fl in r["flags"].items():
        print(f"     {c}: {fl['status']} — {fl['detail']}")

def main():
    sample = load_json(f"{OUT}/validation_sample.json")
    links = load_json("../data/links.json")
    filt = sys.argv[1] if len(sys.argv) > 1 else None
    for bucket, ncts in sample.items():
        if filt and filt not in bucket:
            continue
        print("\n" + "#"*78 + f"\n# BUCKET: {bucket}  (n={len(ncts)})\n" + "#"*78)
        for nct in ncts:
            card(nct, links.get(nct, {}))

if __name__ == "__main__":
    main()
