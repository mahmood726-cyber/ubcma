"""Estimate the poolable/usable-rate lift from adding open full text (Europe PMC).

Data-grounded where possible; the ONLY estimated parameter is the conversion rate
(usable-given-full-text), swept over {0.70, 0.80, 0.90} and clearly marked ESTIMATE.

Method: join each trial's index publication (abstract.usable, abstract.pmid) with its
Europe PMC OA status (inEPMC full text). The addressable population = index pubs that are
NOT usable from the abstract today but DO have open full text in Europe PMC. Full text of
an RCT almost always carries the CONSORT results table (mean/SD/CI/effect+CI), so a large
share of the addressable set would become poolable; we bound it with the sweep.

Denominators:
  A = databank-confirmed index abstracts (the pilot's headline 28.5%/13.5% denom)
  B = all trials with any index-PMID abstract
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

oa = json.load(open(os.path.join(HERE, "out", "oa_index_records.json"), encoding="utf-8"))

def inepmc(area, pmid):
    r = oa.get(area, {}).get(str(pmid))
    return bool(r and r.get("inEPMC") == "Y")

def is_oa(area, pmid):
    r = oa.get(area, {}).get(str(pmid))
    return bool(r and r.get("isOpenAccess") == "Y")

def analyze(area):
    rows = [json.loads(l) for l in open(os.path.join(ROOT, "out", f"trials_{area}.jsonl"), encoding="utf-8")]
    rows = [t for t in rows if isinstance(t.get("abstract"), dict)]
    # denominator sets
    def cell(denom_pred):
        trials = [t for t in rows if denom_pred(t)]
        n = len(trials)
        usable = [t for t in trials if t["abstract"].get("usable")]
        not_usable = [t for t in trials if not t["abstract"].get("usable")]
        # addressable = currently-not-usable AND has full text
        addr_ft = [t for t in not_usable if inepmc(area, t["abstract"].get("pmid"))]
        addr_oa = [t for t in not_usable if is_oa(area, t["abstract"].get("pmid"))]
        # already-usable that also have full text (context)
        usable_ft = [t for t in usable if inepmc(area, t["abstract"].get("pmid"))]
        base = len(usable)
        out = {
            "n_denom": n,
            "usable_now": base,
            "pct_usable_now": round(100*base/n, 1) if n else None,
            "not_usable": len(not_usable),
            "addressable_inEPMC": len(addr_ft),
            "addressable_OA_subset": len(addr_oa),
            "usable_now_also_have_fulltext": len(usable_ft),
        }
        for conv in (0.70, 0.80, 0.90):
            proj = base + conv * len(addr_ft)
            out[f"proj_usable_conv{int(conv*100)}"] = round(proj, 1)
            out[f"proj_pct_conv{int(conv*100)}"] = round(100*proj/n, 1) if n else None
        return out
    return {
        "denomA_databank_confirmed": cell(lambda t: t["abstract"].get("databank_confirmed")),
        "denomB_any_index_abstract": cell(lambda t: t["abstract"].get("has_abstract") and t["abstract"].get("pmid")),
    }

def main():
    res = {a: analyze(a) for a in ("t2d", "onc")}
    json.dump(res, open(os.path.join(HERE, "out", "fulltext_lift.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    for area, d in res.items():
        print(f"\n=== {area.upper()} ===")
        for denom, c in d.items():
            print(f"  [{denom}] n={c['n_denom']}")
            print(f"    usable NOW (abstract)        : {c['usable_now']} ({c['pct_usable_now']}%)")
            print(f"    not usable                   : {c['not_usable']}")
            print(f"    addressable (has inEPMC FT)  : {c['addressable_inEPMC']}   (OA-subset only: {c['addressable_OA_subset']})")
            print(f"    already-usable & have FT     : {c['usable_now_also_have_fulltext']}")
            print(f"    PROJECTED usable @conv70/80/90: "
                  f"{c['proj_pct_conv70']}% / {c['proj_pct_conv80']}% / {c['proj_pct_conv90']}%  [ESTIMATE]")
    print("\nwrote", os.path.join(HERE, "out", "fulltext_lift.json"))

if __name__ == "__main__":
    main()
