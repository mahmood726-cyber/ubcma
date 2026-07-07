"""Measure legally-open full-text availability for the pilot's PMIDs via Europe PMC.

READ-ONLY measurement. Europe PMC REST search API (open, no key) tells us per article:
  inEPMC       = 'Y' if machine-readable full text is hosted IN Europe PMC (fetchable
                 via the open fullTextXML endpoint) -> this is what we could actually pull.
  isOpenAccess = 'Y' if in the Open Access subset (liberal reuse license).
  inPMC        = 'Y' if in PubMed Central.
  license      = e.g. cc by, cc0, cc by-nc.

Mission gate: only inEPMC='Y' (or PMC-OA) counts as pullable full text a scientist with
NO institutional access can legally obtain. We report both the OA-subset fraction and the
broader inEPMC (free full text in EPMC) fraction, and never count paywalled/abstract-only.

Responses cached to ./cache/ so re-runs are offline and reproducible.
"""
from __future__ import annotations
import json, os, time, hashlib, urllib.request, urllib.parse, urllib.error, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(HERE, "cache"); os.makedirs(CACHE, exist_ok=True)
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

_LAST = {"t": 0.0}
def _throttle(gap=0.34):
    dt = time.time() - _LAST["t"]
    if dt < gap: time.sleep(gap - dt)
    _LAST["t"] = time.time()

def http_get(url, retries=4):
    last = None
    for i in range(retries):
        _throttle()
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "ubcma-regpub-opendata-scan/0.1 (research; read-only feasibility)",
                "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", errors="replace")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            last = e; time.sleep(min(2**i, 8))
    raise RuntimeError(f"GET failed: {url} :: {last}")

def load_pmids():
    areas = {}
    for area in ("t2d", "onc"):
        idx = set(); union = set()
        for line in open(os.path.join(ROOT, "out", f"trials_{area}.jsonl"), encoding="utf-8"):
            d = json.loads(line)
            ip = d.get("index_pmid")
            if ip: idx.add(str(ip))
        links = json.load(open(os.path.join(ROOT, "data", f"links_{area}.json"), encoding="utf-8"))
        for nct, v in links.items():
            for p in v.get("union", []): union.add(str(p))
        areas[area] = {"index": idx, "union": union}
    return areas

def query_batch(pmids):
    """Query EPMC for a batch of PMIDs; return {pmid: record} for those found in MED."""
    q = " OR ".join(f"EXT_ID:{p}" for p in pmids)
    query = f"({q}) AND SRC:MED"
    key = hashlib.sha1(query.encode()).hexdigest()[:16]
    cp = os.path.join(CACHE, key + ".json")
    if os.path.exists(cp):
        data = json.load(open(cp, encoding="utf-8"))
    else:
        params = {"query": query, "resultType": "core", "format": "json", "pageSize": "100"}
        url = f"{EPMC}?" + urllib.parse.urlencode(params)
        data = json.loads(http_get(url))
        json.dump(data, open(cp, "w", encoding="utf-8"), ensure_ascii=False)
    out = {}
    for r in data.get("resultList", {}).get("result", []):
        pmid = str(r.get("pmid") or r.get("id"))
        out[pmid] = {
            "inEPMC": r.get("inEPMC"),
            "isOpenAccess": r.get("isOpenAccess"),
            "inPMC": r.get("inPMC"),
            "license": r.get("license"),
            "pmcid": r.get("pmcid"),
            "hasPDF": r.get("hasPDF"),
        }
    return out

def measure_set(pmids):
    pmids = sorted(pmids)
    recs = {}
    for i in range(0, len(pmids), 20):
        recs.update(query_batch(pmids[i:i+20]))
    n = len(pmids)
    found = sum(1 for p in pmids if p in recs)
    inepmc = sum(1 for p in pmids if recs.get(p, {}).get("inEPMC") == "Y")
    oa = sum(1 for p in pmids if recs.get(p, {}).get("isOpenAccess") == "Y")
    inpmc = sum(1 for p in pmids if recs.get(p, {}).get("inPMC") == "Y")
    lic = collections.Counter(recs.get(p, {}).get("license") for p in pmids if recs.get(p, {}).get("inEPMC") == "Y")
    return {
        "n": n, "found_in_MED": found,
        "inEPMC_fulltext": inepmc, "pct_inEPMC": round(100*inepmc/n, 1) if n else None,
        "isOpenAccess_subset": oa, "pct_OA": round(100*oa/n, 1) if n else None,
        "inPMC": inpmc, "pct_inPMC": round(100*inpmc/n, 1) if n else None,
        "license_of_inEPMC": dict(lic), "records": recs,
    }

def main():
    areas = load_pmids()
    result = {}
    for area, sets in areas.items():
        result[area] = {}
        for kind in ("index", "union"):
            m = measure_set(sets[kind])
            recs = m.pop("records")
            result[area][kind] = m
            print(f"[{area}/{kind}] n={m['n']} inEPMC={m['inEPMC_fulltext']} ({m['pct_inEPMC']}%) "
                  f"OA={m['isOpenAccess_subset']} ({m['pct_OA']}%) inPMC={m['inPMC']} ({m['pct_inPMC']}%)")
        # save per-record OA map for index set (used by the lift script)
    op = os.path.join(HERE, "out", "oa_fulltext.json")
    json.dump(result, open(op, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("wrote", op)

    # Also persist the index-set per-PMID OA records (needed to compute poolable-lift)
    idx_records = {}
    for area, sets in areas.items():
        rr = {}
        for i, p in enumerate(sorted(sets["index"])):
            pass
        recs = {}
        pl = sorted(sets["index"])
        for i in range(0, len(pl), 20):
            recs.update(query_batch(pl[i:i+20]))
        idx_records[area] = recs
    json.dump(idx_records, open(os.path.join(HERE, "out", "oa_index_records.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("wrote index per-PMID OA records")

if __name__ == "__main__":
    main()
