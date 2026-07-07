"""Combined full-text poolable lift: Europe PMC + OpenAlex/Unpaywall OA, over denomA."""
import json, os
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
cm=json.load(open(os.path.join(HERE,"out","combined_fulltext_map.json"),encoding="utf-8"))
for area in ("t2d","onc"):
    rows=[json.loads(l) for l in open(os.path.join(ROOT,"out",f"trials_{area}.jsonl"),encoding="utf-8")]
    rows=[t for t in rows if isinstance(t.get("abstract"),dict) and t["abstract"].get("databank_confirmed") and t["abstract"].get("pmid")]
    n=len(rows); m=cm[area]
    usable=[t for t in rows if t["abstract"].get("usable")]
    notus=[t for t in rows if not t["abstract"].get("usable")]
    def has_ft(t): return m.get(str(t["abstract"]["pmid"]),{}).get("any_fulltext")
    def has_epmc(t): return m.get(str(t["abstract"]["pmid"]),{}).get("inEPMC")
    addr_comb=[t for t in notus if has_ft(t)]
    addr_epmc=[t for t in notus if has_epmc(t)]
    base=len(usable)
    print(f"=== {area.upper()} denomA n={n} ===")
    print(f"  usable now {base} ({round(100*base/n,1)}%)")
    print(f"  addressable EPMC-only : {len(addr_epmc)}")
    print(f"  addressable COMBINED  : {len(addr_comb)}  (+{len(addr_comb)-len(addr_epmc)} from OpenAlex/Unpaywall)")
    for c in (0.7,0.8,0.9):
        proj=base+c*len(addr_comb)
        print(f"    COMBINED proj @conv{int(c*100)}: {round(100*proj/n,1)}%")
