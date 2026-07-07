"""Measure INCREMENTAL open full text beyond Europe PMC, via OpenAlex (Unpaywall-derived OA).

The Europe PMC scan (measure_oa_fulltext.py) already found ~53% of index pubs have full
text IN Europe PMC. This asks: of the REMAINDER (not inEPMC), how many have a legal OA copy
somewhere else (publisher gold/hybrid, repository green, bronze) that we could fetch? That is
the true incremental value of adding OpenAlex/Unpaywall as source #2 -- measured, not estimated.

OpenAlex maps PMID->DOI+open_access for ALL articles (not just PMC); its OA status is
Unpaywall-derived, so one open API answers both "what's the DOI" and "is there a legal OA copy".
  PMID  --OpenAlex works?filter=pmid:...-->  doi + open_access{is_oa, oa_status, oa_url}
Responses cached to ./cache_upw/. (NCBI ID Converter was tried first but is PMC-only -> 0 hits
on the non-PMC remainder, which is exactly the set we care about.)
"""
from __future__ import annotations
import json, os, time, hashlib, urllib.request, urllib.parse, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(HERE, "cache_upw"); os.makedirs(CACHE, exist_ok=True)
EMAIL = "mahmood726@gmail.com"   # polite-pool mailto
OPENALEX = "https://api.openalex.org/works"

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
            req = urllib.request.Request(url, headers={"User-Agent": "ubcma-opendata-scan/0.1", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 404:  # Unpaywall: DOI not in their db
                return None
            time.sleep(min(2**i, 8))
        except (urllib.error.URLError, TimeoutError) as e:
            last = e; time.sleep(min(2**i, 8))
    raise RuntimeError(f"GET failed: {url} :: {last}")

def cached(name, fn):
    cp = os.path.join(CACHE, name + ".json")
    if os.path.exists(cp):
        return json.load(open(cp, encoding="utf-8"))
    v = fn()
    json.dump(v, open(cp, "w", encoding="utf-8"), ensure_ascii=False)
    return v

def openalex_oa(pmids):
    """OpenAlex works filtered by pmid, batches of 50 -> {pmid: {doi, is_oa, oa_status, oa_url}}."""
    out = {}
    for i in range(0, len(pmids), 50):
        batch = pmids[i:i+50]
        key = "oax_" + hashlib.sha1(",".join(batch).encode()).hexdigest()[:12]
        def fetch():
            filt = "pmid:" + "|".join(batch)
            params = {"filter": filt, "per-page": "50",
                      "select": "id,doi,ids,open_access", "mailto": EMAIL}
            return json.loads(http_get(OPENALEX + "?" + urllib.parse.urlencode(params)))
        d = cached(key, fetch)
        for w in d.get("results", []):
            pmid_url = (w.get("ids") or {}).get("pmid") or ""
            pmid = pmid_url.rstrip("/").split("/")[-1] if pmid_url else None
            if not pmid:
                continue
            oa = w.get("open_access") or {}
            out[str(pmid)] = {
                "doi": w.get("doi"),
                "is_oa": bool(oa.get("is_oa")),
                "oa_status": oa.get("oa_status"),
                "oa_url": oa.get("oa_url"),
            }
    return out

def load_oa_records():
    return json.load(open(os.path.join(HERE, "out", "oa_index_records.json"), encoding="utf-8"))

def main():
    oa = load_oa_records()
    result = {}
    for area in ("t2d", "onc"):
        recs = oa[area]
        index_pmids = sorted(recs.keys())
        not_inepmc = [p for p in index_pmids if recs[p].get("inEPMC") != "Y"]
        oax = openalex_oa(not_inepmc)
        n_rem = len(not_inepmc)
        n_doi = sum(1 for p in not_inepmc if oax.get(p, {}).get("doi"))
        oa_found = 0; by_host = {}; by_status = {}; recovered = []
        for p in not_inepmc:
            u = oax.get(p)
            if u and u.get("is_oa"):
                oa_found += 1
                st = u.get("oa_status") or "unknown"
                by_status[st] = by_status.get(st, 0) + 1
                recovered.append({"pmid": p, "doi": u.get("doi"), "oa_status": st, "url": u.get("oa_url")})
        # cross-tab against the full index set
        n_index = len(index_pmids)
        n_inepmc = sum(1 for p in index_pmids if recs[p].get("inEPMC") == "Y")
        combined = n_inepmc + oa_found
        result[area] = {
            "n_index": n_index,
            "inEPMC": n_inepmc, "pct_inEPMC": round(100*n_inepmc/n_index, 1),
            "remainder_not_inEPMC": n_rem,
            "remainder_with_DOI": n_doi,
            "remainder_OA_via_openalex": oa_found,
            "pct_remainder_recovered": round(100*oa_found/n_rem, 1) if n_rem else None,
            "by_oa_status": by_status,
            "COMBINED_fulltext_available": combined,
            "pct_COMBINED": round(100*combined/n_index, 1),
            "incremental_pts_over_EPMC": round(100*oa_found/n_index, 1),
        }
        print(f"\n=== {area.upper()} index n={n_index} ===")
        print(f"  inEPMC full text            : {n_inepmc} ({result[area]['pct_inEPMC']}%)")
        print(f"  remainder (not inEPMC)      : {n_rem}  (DOI resolved: {n_doi})")
        print(f"  remainder OA via OpenAlex   : {oa_found} ({result[area]['pct_remainder_recovered']}% of remainder)")
        print(f"    by oa status              : {by_status}")
        print(f"  COMBINED full text avail    : {combined} ({result[area]['pct_COMBINED']}%)  "
              f"[+{result[area]['incremental_pts_over_EPMC']} pts over EPMC alone]")
    json.dump(result, open(os.path.join(HERE, "out", "unpaywall_increment.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("\nwrote out/unpaywall_increment.json")

    # Per-PMID combined full-text map (for the combined-lift computation)
    combined_map = {}
    for area in ("t2d", "onc"):
        recs = oa[area]
        index_pmids = sorted(recs.keys())
        not_inepmc = [p for p in index_pmids if recs[p].get("inEPMC") != "Y"]
        oax = openalex_oa(not_inepmc)   # cached, no new network
        m = {}
        for p in index_pmids:
            inepmc = recs[p].get("inEPMC") == "Y"
            u = oax.get(p, {})
            m[p] = {
                "inEPMC": inepmc,
                "oa_elsewhere": bool(u.get("is_oa")) and not inepmc,
                "oa_status": u.get("oa_status"),
                "any_fulltext": inepmc or bool(u.get("is_oa")),
                # redistributable = CC-licensed OA (exclude bronze = free-to-read-no-license)
                "redistributable": inepmc and recs[p].get("isOpenAccess") == "Y"
                    or (u.get("oa_status") in ("gold", "green", "hybrid", "diamond")),
            }
        combined_map[area] = m
    json.dump(combined_map, open(os.path.join(HERE, "out", "combined_fulltext_map.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("wrote out/combined_fulltext_map.json")

if __name__ == "__main__":
    main()
