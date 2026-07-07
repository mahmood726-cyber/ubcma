"""Fetch a completed-interventional cardiometabolic sample from CT.gov API v2.

Strategy: page the list endpoint for NCT ids (cheap), then fetch + cache the full
per-NCT record (protocol + results + references inline). One pass yields both:
  - non-publication denominator = all completed interventional trials in the sample
  - overlap set                 = subset with results posted AND >=1 linked pub

Usage: python fetch_ctgov.py [TARGET]
"""
from __future__ import annotations
import sys, json, urllib.parse
from common import CTGOV_BASE, CT_DIR, DATA, http_get, cache_path, load_json, save_json, CONDITION

def page_ncts(target):
    """Return up to `target` NCT ids for completed interventional trials."""
    ncts, token = [], None
    while len(ncts) < target:
        params = {
            "query.cond": CONDITION,
            "filter.overallStatus": "COMPLETED",
            "aggFilters": "studyType:int",         # interventional only
            "fields": "NCTId",
            "pageSize": "100",
            "countTotal": "true",
        }
        if token:
            params["pageToken"] = token
        url = f"{CTGOV_BASE}/studies?" + urllib.parse.urlencode(params)
        d = json.loads(http_get(url))
        for s in d.get("studies", []):
            nct = s.get("protocolSection", {}).get("identificationModule", {}).get("nctId")
            if nct:
                ncts.append(nct)
        token = d.get("nextPageToken")
        if not token:
            break
    return ncts[:target]

def fetch_full(nct):
    p = cache_path(CT_DIR, nct)
    cached = load_json(p)
    if cached is not None:
        return cached
    url = f"{CTGOV_BASE}/studies/{nct}"
    d = json.loads(http_get(url))
    save_json(p, d)
    return d

def main():
    target = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    print(f"[ctgov] paging up to {target} completed interventional '{CONDITION}' NCTs ...")
    ncts = page_ncts(target)
    print(f"[ctgov] got {len(ncts)} NCT ids; fetching full records ...")
    idx = []
    for i, nct in enumerate(ncts, 1):
        try:
            d = fetch_full(nct)
        except Exception as e:
            print(f"  ! {nct} fetch failed: {e}")
            continue
        idx.append(nct)
        if i % 50 == 0:
            print(f"  ... {i}/{len(ncts)}")
    save_json(f"{DATA}/ctgov_index.json", {"condition": CONDITION, "ncts": idx})
    print(f"[ctgov] cached {len(idx)} full records -> data/ctgov/, index -> data/ctgov_index.json")

if __name__ == "__main__":
    main()
