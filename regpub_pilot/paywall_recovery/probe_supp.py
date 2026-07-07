"""Step 2 — probe the LEGITIMATE open-supplement channels for the paywalled pocket.

For every paywalled paper that has a PMCID (the author-manuscript / EPMC route), we
probe two sanctioned open endpoints and record, per paper, whether the supplement is
genuinely-open-and-usable (HTTP 200 + real bundle) or GATED (the endpoint refuses).
NO paywall is circumvented: a refusal is recorded as 'gated, not used' and we stop.

  Channel A  Europe PMC supplementaryFiles   (serves OA-subset only; refuses non-OA)
             https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/supplementaryFiles
  Channel B  NCBI PMC OA Web Service         (serves PMC Open Access Subset only)
             https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id={pmcid}

Both are the publisher/aggregator's own open redistribution APIs — if they serve it,
it is genuinely open; if they refuse, it is gated and we do not route around them.

Run:  python probe_supp.py
"""
from __future__ import annotations
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
from fetch_fulltext import http_get_bytes

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache"); OUTD = os.path.join(HERE, "out")
SUPP = os.path.join(HERE, "supp"); os.makedirs(SUPP, exist_ok=True)

EPMC_SUPP = "https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/supplementaryFiles"
NCBI_OA = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id={pmcid}"

def classify_epmc(raw, ct):
    if raw is None:
        return "miss", ct, None
    body = raw[:400].decode("utf-8", "replace") if raw[:5] not in (b"PK\x03\x04\x00", ) else ""
    if raw[:2] == b"PK":                       # ZIP magic -> real bundle
        return "OPEN", ct, len(raw)
    if "not open access" in body:
        return "GATED_not_oa", ct, None
    if "errCode" in body or "errMsg" in body:
        return "error", body[:160], None
    if "pdf" in (ct or "").lower() or raw[:4] == b"%PDF":
        return "OPEN", ct, len(raw)
    return "unknown", (ct or "")[:80], len(raw)

def classify_ncbi(raw, ct):
    if raw is None:
        return "miss", ct, None
    body = raw.decode("utf-8", "replace")
    if "idDoesNotExist" in body or "invalid" in body.lower():
        return "invalid", body[:160], None
    if "is not Open Access" in body or "not available" in body.lower() or "error" in body.lower() and "href" not in body:
        # OA service returns <error code="...">... for non-OA-subset
        if "<error" in body:
            import re
            m = re.search(r'<error[^>]*>(.*?)</error>', body, re.S)
            return "GATED_or_absent", (m.group(1)[:120] if m else body[:120]), None
    if "<link" in body and "href" in body:
        import re
        links = re.findall(r'href="([^"]+)"', body)
        return "OPEN_LINKS", ";".join(links)[:300], len(links)
    return "unknown", body[:160], None

def main():
    rows = json.load(open(os.path.join(OUTD, "paywalled_set.json"), encoding="utf-8"))
    pmcid_rows = [r for r in rows if r["pmcid"]]
    print(f"probing {len(pmcid_rows)} PMCID papers (of {len(rows)} paywalled)\n")

    log = []
    for r in pmcid_rows:
        pmcid = r["pmcid"]; pmid = r["pmid"]
        # Channel A: EPMC
        a_cache = os.path.join(CACHE, f"epmc_supp_{pmcid}.bin")
        if os.path.exists(a_cache + ".meta"):
            meta = json.load(open(a_cache + ".meta")); a_verdict = meta["verdict"]; a_info = meta["info"]; a_size = meta["size"]
            raw_a = open(a_cache, "rb").read() if os.path.exists(a_cache) else None
        else:
            raw_a, ct_a = http_get_bytes(EPMC_SUPP.format(pmcid=pmcid), accept="application/zip")
            a_verdict, a_info, a_size = classify_epmc(raw_a, ct_a)
            if a_verdict == "OPEN" and raw_a:
                open(a_cache, "wb").write(raw_a)
            json.dump({"verdict": a_verdict, "info": str(a_info), "size": a_size},
                      open(a_cache + ".meta", "w"))
        # Channel B: NCBI OA
        b_cache = os.path.join(CACHE, f"ncbi_oa_{pmcid}.json")
        if os.path.exists(b_cache):
            meta = json.load(open(b_cache)); b_verdict = meta["verdict"]; b_info = meta["info"]
        else:
            raw_b, ct_b = http_get_bytes(NCBI_OA.format(pmcid=pmcid), accept="application/xml")
            b_verdict, b_info, _ = classify_ncbi(raw_b, ct_b)
            json.dump({"verdict": b_verdict, "info": str(b_info)}, open(b_cache, "w"))
        log.append({"pmid": pmid, "pmcid": pmcid, "area": r["area"], "hasSuppl": r["hasSuppl"],
                    "isOpenAccess": r["isOpenAccess"], "journal": r["journal"], "pubYear": r["pubYear"],
                    "epmc_supp": a_verdict, "epmc_info": str(a_info)[:80], "epmc_size": a_size,
                    "ncbi_oa": b_verdict, "ncbi_info": str(b_info)[:120]})
        print(f"{r['area']} {pmid} {pmcid} hasSuppl={r['hasSuppl']} OA={r['isOpenAccess']:>1} | "
              f"EPMC={a_verdict:<14} NCBI={b_verdict}")

    json.dump(log, open(os.path.join(OUTD, "supp_probe.json"), "w", encoding="utf-8"), indent=1)
    from collections import Counter
    print("\n=== EPMC supplementaryFiles verdicts ===", dict(Counter(x["epmc_supp"] for x in log)))
    print("=== NCBI OA verdicts ===", dict(Counter(x["ncbi_oa"] for x in log)))
    openA = [x for x in log if x["epmc_supp"] == "OPEN"]
    openB = [x for x in log if x["ncbi_oa"] == "OPEN_LINKS"]
    print(f"\nGENUINELY-OPEN supplement via EPMC: {len(openA)}  via NCBI-OA: {len(openB)}")
    for x in openA: print("  EPMC-OPEN:", x["pmid"], x["pmcid"], x["journal"])
    for x in openB: print("  NCBI-OPEN:", x["pmid"], x["pmcid"], x["journal"], x["ncbi_info"][:80])

if __name__ == "__main__":
    main()
