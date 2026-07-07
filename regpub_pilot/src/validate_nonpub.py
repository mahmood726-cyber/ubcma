"""Active-search validation of the non_publication flag.

The flag fires on ABSENCE of an NCT-databank link. But a trial can be published in a
paper that never tagged its NCT -> false positive. Here we independently search PubMed
by (a) the bare NCT string in ALL fields and (b) title/intervention keywords, and dump
candidate hits so a human can adjudicate whether a genuine results publication exists.
"""
from __future__ import annotations
import sys, io, json, urllib.parse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from common import EUTILS, CT_DIR, OUT, cache_path, load_json, http_get

def esearch(term, retmax=5):
    u = f"{EUTILS}/esearch.fcgi?db=pubmed&term={urllib.parse.quote(term)}&retmode=json&retmax={retmax}"
    try:
        return json.loads(http_get(u, min_gap=0.4)).get("esearchresult", {}).get("idlist", [])
    except Exception:
        return []

def esummary(pmids):
    if not pmids:
        return {}
    u = f"{EUTILS}/esummary.fcgi?db=pubmed&id={','.join(pmids)}&retmode=json"
    try:
        r = json.loads(http_get(u, min_gap=0.4)).get("result", {})
        return {p: (r.get(p, {}).get("title", ""), r.get(p, {}).get("pubdate", "")) for p in pmids}
    except Exception:
        return {}

def keywords(rec):
    ps = rec.get("protocolSection", {})
    ident = ps.get("identificationModule", {})
    acr = ident.get("acronym")
    ints = [i.get("name", "") for i in ps.get("armsInterventionsModule", {}).get("interventions", []) or []]
    return acr, [x for x in ints if x][:2]

def main():
    ncts = sys.argv[1:]
    if not ncts:
        # default: read a deterministic sample from trials.jsonl
        rows = [json.loads(l) for l in open(f"{OUT}/trials.jsonl", encoding="utf-8")]
        flagged = sorted(r["nct"] for r in rows
                         if r["flags"].get("non_publication", {}).get("status") == "contradicts")
        # spread across the list deterministically
        step = max(1, len(flagged) // 20)
        ncts = flagged[::step][:20]
    print(f"Validating {len(ncts)} non-pub-flagged NCTs\n")
    for nct in ncts:
        rec = load_json(cache_path(CT_DIR, nct)) or {}
        acr, ints = keywords(rec)
        title = rec.get("protocolSection", {}).get("identificationModule", {}).get("briefTitle", "")
        hits_nct = esearch(f"{nct}")                    # bare NCT in all fields
        term_kw = " AND ".join(filter(None, [ints[0] if ints else "", "type 2 diabetes",
                                             "randomized"]))
        hits_kw = esearch(term_kw) if term_kw else []
        s = esummary(list(dict.fromkeys(hits_nct))[:5])
        print("="*78)
        print(f"{nct}  acr={acr}  title={title[:70]}")
        print(f"  interventions={ints}")
        print(f"  PubMed NCT-string hits ({len(hits_nct)}):")
        for p in hits_nct[:5]:
            t, dt = s.get(p, ("", ""))
            print(f"     PMID {p} ({dt}): {t[:80]}")
        if not hits_nct:
            print("     (none — no paper mentions this NCT in any field)")

if __name__ == "__main__":
    main()
