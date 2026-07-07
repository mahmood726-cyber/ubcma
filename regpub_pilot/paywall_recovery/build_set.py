"""Step 1 — define the PAYWALLED loss pocket and pull open metadata.

Paywalled = a confirmed-index target whose MAIN TEXT we could NOT parse under the
pilot's no-paywall premise (fulltext_fetch status != 'parsed'). For each, we query
the Europe PMC REST 'core' record (a legitimate open metadata API — the same one the
pilot already uses) to learn, per paper:
  - pmcid / inEPMC / isOpenAccess / license   (author-manuscript vs OA-subset route)
  - hasSuppl  ('Y' => EPMC holds a supplementary-file bundle for it)
  - hasPDF, source, journal, doi, firstPublicationDate
  - fullTextUrlList (each url tagged availability = 'Open access' / 'Subscription required')

NO article text is fetched here — metadata only. Cached to cache/epmc_core_{pmid}.json.
Run:  python build_set.py
"""
from __future__ import annotations
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
from fetch_fulltext import http_get_bytes  # sanctioned throttled fetch path
from common import OUT

CACHE = os.path.join(HERE, "cache")
OUTD = os.path.join(HERE, "out")
os.makedirs(CACHE, exist_ok=True); os.makedirs(OUTD, exist_ok=True)

EPMC_SEARCH = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search"
               "?query={q}&resultType=core&format=json&pageSize=100")

PARSED_STATUS = {"parsed"}

def paywalled_targets():
    """Return {area: {pmid: fetch_result}} for targets whose main text is NOT parsed."""
    pocket = {}
    for area in ("onc", "t2d"):
        p = os.path.join(OUT, f"fulltext_fetch_{area}.json")
        d = json.load(open(p, encoding="utf-8"))
        pk = {}
        for r in d["results"]:
            if r["status"] not in PARSED_STATUS:
                pk[str(r["pmid"])] = r
        pocket[area] = pk
    return pocket

def fetch_core_batch(pmids):
    """One EPMC core query for a batch of PMIDs. Returns {pmid: record}."""
    q = "(" + " OR ".join(f"EXT_ID:{p}" for p in pmids) + ") AND SRC:MED"
    import urllib.parse
    url = EPMC_SEARCH.format(q=urllib.parse.quote(q))
    raw, ct = http_get_bytes(url, accept="application/json")
    out = {}
    if not raw:
        return out, ct
    try:
        d = json.loads(raw.decode("utf-8", "replace"))
    except Exception as e:
        return out, f"json_err:{e}"
    for rec in d.get("resultList", {}).get("result", []):
        pid = str(rec.get("pmid") or rec.get("id"))
        out[pid] = rec
    return out, "ok"

def main():
    pocket = paywalled_targets()
    all_pmids = sorted({p for area in pocket for p in pocket[area]})
    print(f"paywalled pocket: onc={len(pocket['onc'])} t2d={len(pocket['t2d'])} "
          f"total-unique={len(all_pmids)}")

    # fetch/cached core records
    core = {}
    to_fetch = []
    for pmid in all_pmids:
        cp = os.path.join(CACHE, f"epmc_core_{pmid}.json")
        if os.path.exists(cp):
            core[pmid] = json.load(open(cp, encoding="utf-8"))
        else:
            to_fetch.append(pmid)
    print(f"cached={len(core)} to_fetch={len(to_fetch)}")

    B = 15
    for i in range(0, len(to_fetch), B):
        batch = to_fetch[i:i+B]
        recs, status = fetch_core_batch(batch)
        for pmid in batch:
            rec = recs.get(pmid, {"_missing": True, "pmid": pmid})
            json.dump(rec, open(os.path.join(CACHE, f"epmc_core_{pmid}.json"), "w",
                                encoding="utf-8"))
            core[pmid] = rec
        print(f"  fetched {i+len(batch)}/{len(to_fetch)} status={status} "
              f"(got {sum(1 for p in batch if not recs.get(p,{}).get('_missing') and p in recs)})")

    # assemble a flat table
    def avail_channels(rec):
        urls = (rec.get("fullTextUrlList") or {}).get("fullTextUrl", []) or []
        open_urls = [u for u in urls if u.get("availability") == "Open access"]
        sub_urls = [u for u in urls if u.get("availability") != "Open access"]
        return open_urls, sub_urls

    rows = []
    for pmid in all_pmids:
        rec = core.get(pmid, {})
        area = "onc" if pmid in pocket["onc"] else "t2d"
        fr = pocket[area].get(pmid, {})
        open_urls, sub_urls = avail_channels(rec)
        rows.append({
            "pmid": pmid, "area": area,
            "fetch_status": fr.get("status"), "fetch_channel": fr.get("channel"),
            "pmcid": rec.get("pmcid"),
            "inEPMC": rec.get("inEPMC"), "inPMC": rec.get("inPMC"),
            "isOpenAccess": rec.get("isOpenAccess"),
            "license": rec.get("license"),
            "hasSuppl": rec.get("hasSuppl"),
            "hasPDF": rec.get("hasPDF"),
            "source": rec.get("source"),
            "doi": rec.get("doi"),
            "journal": ((rec.get("journalInfo") or {}).get("journal") or {}).get("title"),
            "pubYear": rec.get("pubYear"),
            "pubType": rec.get("pubTypeList", {}).get("pubType") if isinstance(rec.get("pubTypeList"), dict) else None,
            "n_open_url": len(open_urls),
            "n_sub_url": len(sub_urls),
            "open_url_sites": [u.get("site") for u in open_urls],
            "missing_epmc": rec.get("_missing", False),
        })
    json.dump(rows, open(os.path.join(OUTD, "paywalled_set.json"), "w", encoding="utf-8"),
              indent=1)
    print(f"\nwrote paywalled_set.json ({len(rows)} rows)")

    # quick coverage snapshot
    from collections import Counter
    hs = Counter(r["hasSuppl"] for r in rows)
    print("hasSuppl:", dict(hs))
    print("has_pmcid:", sum(1 for r in rows if r["pmcid"]))
    print("isOpenAccess=Y:", sum(1 for r in rows if r["isOpenAccess"] == "Y"))
    print("any Open-access fullTextUrl:", sum(1 for r in rows if r["n_open_url"] > 0))
    print("missing from EPMC entirely:", sum(1 for r in rows if r["missing_epmc"]))

if __name__ == "__main__":
    main()
