"""Measure registry cross-coverage + mission-relevance (countries) on the pilot corpus.

READ-ONLY. Uses the already-cached CT.gov v2 full records (data/ctgov/) keyed by NCT.
No network. Answers, for T2D + oncology:
  - How many of our CT.gov trials ALSO carry a secondary registry ID (EudraCT, ISRCTN,
    WHO UTN, CTRI, ChiCTR, JPRN, ...) -> overlap / dual-registration rate.
  - Country distribution -> mission relevance (non-US, African, Asian site presence).

Note the honest framing: the pilot corpus was SAMPLED from CT.gov, so by construction
100% of it is on CT.gov. ICTRP/regional registries cannot add coverage to THIS set; their
value is (a) the dual-registration overlap measured here, and (b) *additional* trials not
on CT.gov, which this script does NOT measure (needs an ICTRP query; estimated separately).
"""
from __future__ import annotations
import json, os, hashlib, glob, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CT = os.path.join(ROOT, "data", "ctgov")

# Country buckets for mission relevance
AFRICA = {"Algeria","Angola","Benin","Botswana","Burkina Faso","Cameroon","Egypt","Ethiopia",
    "Ghana","Kenya","Malawi","Mali","Morocco","Mozambique","Nigeria","Rwanda","Senegal",
    "South Africa","Tanzania","Tunisia","Uganda","Zambia","Zimbabwe","Ivory Coast","Cote D'Ivoire"}
ASIA = {"China","India","Indonesia","Japan","Korea, Republic of","South Korea","Malaysia",
    "Pakistan","Philippines","Singapore","Sri Lanka","Taiwan","Thailand","Vietnam","Bangladesh",
    "Hong Kong","Nepal","Cambodia","Myanmar","Mongolia"}

# Which secondary-ID types / domains map to which registry
def classify_secondary(sid):
    """Return a registry label from a secondaryIdInfo dict."""
    t = (sid.get("type") or "").upper()
    dom = (sid.get("domain") or "").upper()
    idv = (sid.get("id") or "").upper()
    if t == "EUDRACT_NUMBER" or "EUDRACT" in dom:
        return "EudraCT/EU-CTR"
    if "ISRCTN" in idv or "ISRCTN" in dom:
        return "ISRCTN"
    if "CTRI" in idv or "CTRI" in dom:
        return "CTRI (India)"
    if "CHICTR" in idv or "CHICTR" in dom:
        return "ChiCTR (China)"
    if "JPRN" in idv or "UMIN" in idv or "JAPIC" in idv or "JRCT" in idv or "JPRN" in dom:
        return "JPRN (Japan)"
    if "ACTRN" in idv or "ANZCTR" in dom:
        return "ANZCTR"
    if "PACTR" in idv:
        return "PACTR (Africa)"
    if "NTR" in idv and "NETHERLAND" in dom:
        return "NTR (Netherlands)"
    if "DRKS" in idv:
        return "DRKS (Germany)"
    if "IRCT" in idv:
        return "IRCT (Iran)"
    if "U1111" in idv or (dom == "WHO"):
        return "WHO UTN"
    return None

def load_records(ncts):
    recs = {}
    for nct in ncts:
        h = hashlib.sha1(nct.encode()).hexdigest()[:16]
        p = os.path.join(CT, h + ".json")
        if os.path.exists(p):
            recs[nct] = json.load(open(p, encoding="utf-8"))
    return recs

def measure(area):
    idx = json.load(open(os.path.join(ROOT, "data", f"ctgov_index_{area}.json"), encoding="utf-8"))
    ncts = idx["ncts"]
    recs = load_records(ncts)
    n_total = len(ncts)
    n_cached = len(recs)

    reg_counts = collections.Counter()   # registry label -> #trials carrying >=1 such ID
    n_any_secondary = 0
    n_any_nonUS_registry = 0              # any secondary registry that is regional/non-US
    NONUS_REG = {"EudraCT/EU-CTR","ISRCTN","CTRI (India)","ChiCTR (China)","JPRN (Japan)",
                 "ANZCTR","PACTR (Africa)","NTR (Netherlands)","DRKS (Germany)","IRCT (Iran)","WHO UTN"}

    # country stats
    n_with_locs = 0
    n_us_any = 0; n_us_only = 0; n_nonus_any = 0; n_africa = 0; n_asia = 0; n_no_us_site = 0
    country_freq = collections.Counter()

    for nct, d in recs.items():
        ps = d.get("protocolSection", {})
        idm = ps.get("identificationModule", {})
        sids = idm.get("secondaryIdInfos", []) or []
        labels = set()
        for s in sids:
            lab = classify_secondary(s)
            if lab:
                labels.add(lab)
        if labels:
            n_any_secondary += 1
        for lab in labels:
            reg_counts[lab] += 1
        if labels & NONUS_REG:
            n_any_nonUS_registry += 1

        locs = ps.get("contactsLocationsModule", {}).get("locations", []) or []
        countries = set()
        for l in locs:
            c = l.get("country")
            if c:
                countries.add(c)
                country_freq[c] += 1
        if countries:
            n_with_locs += 1
            has_us = "United States" in countries
            has_africa = bool(countries & AFRICA)
            has_asia = bool(countries & ASIA)
            nonus = countries - {"United States"}
            if has_us: n_us_any += 1
            if has_us and not nonus: n_us_only += 1
            if nonus: n_nonus_any += 1
            if not has_us: n_no_us_site += 1
            if has_africa: n_africa += 1
            if has_asia: n_asia += 1

    return {
        "area": area,
        "n_total_ncts": n_total,
        "n_cached_records": n_cached,
        "secondary_registry": {
            "n_trials_any_secondary_registry": n_any_secondary,
            "pct_any_secondary_registry": round(100*n_any_secondary/n_cached, 1) if n_cached else None,
            "n_trials_any_nonUS_registry": n_any_nonUS_registry,
            "pct_any_nonUS_registry": round(100*n_any_nonUS_registry/n_cached, 1) if n_cached else None,
            "by_registry": dict(reg_counts.most_common()),
        },
        "countries": {
            "n_with_location_data": n_with_locs,
            "n_us_any": n_us_any,
            "n_us_only": n_us_only,
            "pct_us_only": round(100*n_us_only/n_with_locs, 1) if n_with_locs else None,
            "n_nonUS_any_site": n_nonus_any,
            "pct_nonUS_any_site": round(100*n_nonus_any/n_with_locs, 1) if n_with_locs else None,
            "n_no_US_site_at_all": n_no_us_site,
            "pct_no_US_site": round(100*n_no_us_site/n_with_locs, 1) if n_with_locs else None,
            "n_with_africa_site": n_africa,
            "n_with_asia_site": n_asia,
            "top_countries": dict(country_freq.most_common(20)),
        },
    }

def main():
    out = {a: measure(a) for a in ("t2d", "onc")}
    op = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "registry_coverage.json")
    json.dump(out, open(op, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    for a, r in out.items():
        s = r["secondary_registry"]; c = r["countries"]
        print(f"\n=== {a.upper()}  (n_cached={r['n_cached_records']}/{r['n_total_ncts']}) ===")
        print(f"  any secondary registry ID : {s['n_trials_any_secondary_registry']} ({s['pct_any_secondary_registry']}%)")
        print(f"  any non-US registry ID    : {s['n_trials_any_nonUS_registry']} ({s['pct_any_nonUS_registry']}%)")
        print(f"  by registry               : {s['by_registry']}")
        print(f"  location data present     : {c['n_with_location_data']}")
        print(f"  US-only sites             : {c['n_us_only']} ({c['pct_us_only']}%)")
        print(f"  >=1 non-US site           : {c['n_nonUS_any_site']} ({c['pct_nonUS_any_site']}%)")
        print(f"  NO US site at all         : {c['n_no_US_site_at_all']} ({c['pct_no_US_site']}%)")
        print(f"  >=1 Africa site           : {c['n_with_africa_site']}")
        print(f"  >=1 Asia site             : {c['n_with_asia_site']}")
    print(f"\nwrote {op}")

if __name__ == "__main__":
    main()
