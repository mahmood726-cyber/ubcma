"""OUTCOME-SWITCHING at scale from open sources — the landmark measurement.

The registry records the PRE-SPECIFIED primary outcome (declared before data). The paper
reports whatever it reports as primary. How often do they differ, and how?

Comparator: registry primary (protocolSection.outcomesModule.primaryOutcomes, name+timeFrame)
vs the paper's DECLARED primary, extracted by an LLM from the OPEN-ACCESS FULL-TEXT METHODS
section (where the primary is declared) with a VERBATIM span. Deterministic layer verifies
the span exists and classifies on OUTCOME CONCEPT + TIMEPOINT — never numeric proximity.

Every asserted switch is individually checkable: registry locator (NCT/primaryOutcomes) +
registry value, and paper locator (methods span) + paper value.

CAVEAT (lower bound): CT.gov v2 public API does not expose per-field registration-time
history, so we compare the CURRENT registry primary. Trials whose registry primary was
retro-edited to match the paper are counted concordant -> this UNDERSTATES switching.

The LLM proposes; the deterministic core disposes (span-verify + classify). Subscription
Claude subagents only.
"""
from __future__ import annotations
import sys, os, io, json, re, glob
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
sys.path.insert(0, ".")
from common import OUT, CT_DIR, PM_DIR, index_path, links_path, cache_path, load_json, save_json
from llm_extract import build_items, extract_json_array, _norm

FT_PARSED = os.path.join(os.path.dirname(OUT), "data", "fulltext_parsed")
SW_BATCH = os.path.join(os.path.dirname(OUT), "data", "sw_batches")
SW_RAW = os.path.join(os.path.dirname(OUT), "data", "sw_raw")
for d in (SW_BATCH, SW_RAW):
    os.makedirs(d, exist_ok=True)

def registry_primaries(rec):
    ps = rec.get("protocolSection", {})
    om = ps.get("outcomesModule", {})
    prim = [{"measure": (o.get("measure") or "").strip(), "timeframe": (o.get("timeFrame") or "").strip()}
            for o in (om.get("primaryOutcomes") or [])]
    sec = [(o.get("measure") or "").strip() for o in (om.get("secondaryOutcomes") or [])]
    status = ps.get("statusModule", {})
    return prim, sec, {
        "start": (status.get("startDateStruct") or {}).get("date"),
        "study_first_post": (status.get("studyFirstPostDateStruct") or {}).get("date"),
        "primary_completion": (status.get("primaryCompletionDateStruct") or {}).get("date"),
    }

SCHEMA = """Return ONLY a JSON array (no prose/fences). One object per input item:
{
 "pmid":"<echo>",
 "abstain": true|false,                       // true only if the METHODS text does not state any primary outcome
 "paper_primary":[{"outcome":"<short name>","timepoint":"<as stated or null>"}],
 "paper_primary_span":"<verbatim sentence from the METHODS that declares the primary outcome>",
 "registry_primary_disposition":[            // one entry PER registered primary given to you, in order
   {"registered":"<echo the registered primary name>",
    "status":"reported_as_primary_same|reported_primary_different_timepoint|demoted_to_secondary|not_reported",
    "note":"<short reason / where it appears>"}],
 "new_primary_promoted": true|false,          // paper declares a primary NOT among the registered primaries
 "confidence":"high|medium|low"
}
RULES:
- The excerpt is the METHODS section plus windows around every "primary" mention (separated by "///"). Find where the PAPER declares its primary ("primary outcome/endpoint was ...", "primary efficacy endpoint ...").
- paper_primary_span MUST be copied verbatim from the provided excerpt (exact substring).
- MATCH ON THE OUTCOME CONCEPT, not exact wording. "Change in A1C at end of study", "HbA1c change from baseline", and registered "Change in Glycated Hemoglobin (HbA1c) at Week 26" are the SAME CONCEPT (HbA1c change) -> reported_as_primary_same. Do NOT call a wording/label difference a switch.
- CO-PRIMARIES: if several primaries are registered and the paper reports ANY of them as its primary, mark that one "reported_as_primary_same".
- reported_primary_different_timepoint ONLY when the paper's primary is the same outcome but at a genuinely DIFFERENT analysis timepoint than registered (e.g., registered week 52, paper primary week 24).
- demoted_to_secondary: the registered primary appears in the paper but explicitly as a secondary/other outcome. not_reported: the outcome concept is absent as any endpoint.
- If NO primary is stated anywhere in the excerpt, abstain=true.
- When unsure between statuses, pick the LESS severe one and explain in note. DO NOT invent switching — a rate built on false positives is worthless."""

PROMPT_HEADER = ("You audit clinical-trial OUTCOME SWITCHING. For each item you get the trial's "
                 "REGISTERED primary outcome(s) (name + timeframe) and VERBATIM METHODS text from the "
                 "open-access paper. Determine what the PAPER declares as its primary outcome and how it "
                 "disposes of each registered primary.\n\n" + SCHEMA + "\n\nINPUT ITEMS:\n")

def build_switch_items(area):
    idx = load_json(index_path(area)); links = load_json(links_path(area))
    items = build_items(idx["ncts"], links)   # confirmed-index trials
    out = []
    for it in items:
        pj = load_json(os.path.join(FT_PARSED, f"{it['pmid']}.json"))
        if not pj or pj.get("_status") != "parsed":
            continue
        methods = (pj.get("methods") or "").strip()
        if not methods:
            continue
        rec = load_json(cache_path(CT_DIR, it["nct"])) or {}
        prim, sec, dates = registry_primaries(rec)
        if not prim:
            continue
        out.append({"nct": it["nct"], "pmid": it["pmid"],
                    "registry_primaries": prim, "registry_secondaries": sec[:20],
                    "dates": dates,
                    "methods": primary_excerpt(pj), "abstract": pj.get("abstract", "")[:1500]})
    return out

_PRIMARY_RE = re.compile(r"primary\s+(?:outcome|end[- ]?point|efficacy|analysis)", re.I)
def primary_excerpt(parsed, cap=7500):
    """The primary is DECLARED in methods, but JATS section classification sometimes
    files that sentence under results/unclassified. Feed the methods section PLUS a
    window around every 'primary outcome/endpoint' mention anywhere in the full text."""
    meth = (parsed.get("methods") or "").strip()
    full = (parsed.get("full_text") or "").strip()
    wins = []
    for m in _PRIMARY_RE.finditer(full):
        s = max(0, m.start() - 220); e = min(len(full), m.start() + 320)
        wins.append(full[s:e])
    seen, uniq = set(), []
    for w in wins:
        k = w[:60]
        if k not in seen:
            seen.add(k); uniq.append(w)
    text = meth + ("\n///\n" + "\n///\n".join(uniq) if uniq else "")
    return text[:cap] if text.strip() else (full[:cap])

def make_batches(area, size=6):
    items = build_switch_items(area)
    batches = [items[i:i+size] for i in range(0, len(items), size)]
    man = []
    for bi, b in enumerate(batches):
        p = os.path.join(SW_BATCH, f"{area}_{bi:02d}.json")
        save_json(p, {"batch_id": f"{area}_{bi:02d}", "items": b}); man.append(p)
    save_json(os.path.join(SW_BATCH, f"_manifest_{area}.json"), man)
    print(f"[sw-batches] {len(items)} trials with FT methods + registry primary -> {len(batches)} batches ({area})")
    return man

def batch_prompt(path):
    pl = load_json(path); lines = [PROMPT_HEADER]
    for it in pl["items"]:
        lines.append(json.dumps({"pmid": it["pmid"],
            "registered_primaries": it["registry_primaries"],
            "methods": it["methods"]}, ensure_ascii=False))
    lines.append("\nReturn the JSON array now.")
    return "\n".join(lines)

def _methods_of(pmid):
    # superset the LLM could have quoted from: methods section + full body text
    pj = load_json(os.path.join(FT_PARSED, f"{pmid}.json")) or {}
    return (pj.get("methods", "") or "") + "\n" + (pj.get("full_text", "") or "")

def classify(item, methods_text):
    """Deterministic trial-level switch class from a verified LLM item."""
    if item.get("abstain"):
        return {"status": "abstain_no_primary_in_methods"}
    span = item.get("paper_primary_span")
    if not span or _norm(span) not in _norm(methods_text):
        return {"status": "unverified_span", "span": span}
    disp = item.get("registry_primary_disposition") or []
    sts = [d.get("status") for d in disp]
    # COMPare logic: a trial is CONCORDANT if the paper reports ANY registered primary AS
    # its primary — even when other co-primaries (e.g. a later timepoint) appear only in a
    # separate publication. Switching = the paper's declared primary is NOT a registered one.
    if not sts:
        cls = "indeterminate"
    elif "reported_as_primary_same" in sts:
        cls = "concordant"
    elif "reported_primary_different_timepoint" in sts:
        cls = "switch_timepoint"        # registered outcome, but a different timepoint is the paper's primary
    elif item.get("new_primary_promoted") and "demoted_to_secondary" in sts:
        cls = "switch_demotion"         # registered primary demoted, a new one promoted
    elif "demoted_to_secondary" in sts:
        cls = "switch_demotion"
    elif all(s == "not_reported" for s in sts):
        cls = "switch_silent"           # NO registered primary is the paper's primary
    else:
        cls = "indeterminate"
    return {"status": cls, "disposition": disp,
            "paper_primary": item.get("paper_primary"),
            "new_primary_promoted": item.get("new_primary_promoted"),
            "confidence": item.get("confidence")}

def load_raw(area):
    out = {}
    for p in sorted(glob.glob(os.path.join(SW_RAW, f"{area}_*.txt")) + glob.glob(os.path.join(SW_RAW, f"{area}_*.json"))):
        try:
            arr = extract_json_array(open(p, encoding="utf-8").read())
        except Exception as e:
            print("  !", p, e); continue
        for it in arr:
            if isinstance(it, dict) and it.get("pmid"):
                out[str(it["pmid"])] = it
    return out

def fuse(area):
    items = {it["pmid"]: it for it in build_switch_items(area)}
    raw = load_raw(area)
    rows = []
    for pmid, it in items.items():
        llm = raw.get(str(pmid))
        if not llm:
            continue
        c = classify(llm, _methods_of(pmid))
        rows.append({"nct": it["nct"], "pmid": pmid,
                     "registry_primaries": it["registry_primaries"],
                     "switch": c,
                     # checkable locators
                     "registry_locator": f"CTGOV:{it['nct']}#outcomesModule.primaryOutcomes",
                     "paper_locator": f"PMID:{pmid}#methods",
                     "paper_primary_span": llm.get("paper_primary_span")})
    with open(f"{OUT}/switch_{area}.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    import collections
    cc = collections.Counter(r["switch"]["status"] for r in rows)
    scored = [r for r in rows if r["switch"]["status"] not in
              ("abstain_no_primary_in_methods", "unverified_span", "indeterminate")]
    nsw = sum(1 for r in scored if r["switch"]["status"].startswith("switch_"))
    summary = {"area": area, "n_with_ft_methods": len(items), "n_llm": len(raw),
               "n_scored": len(scored), "counts": dict(cc),
               "switch_any": nsw,
               "switch_rate_pct": round(100 * nsw / len(scored), 1) if scored else None,
               "by_type": {k: v for k, v in cc.items() if k.startswith("switch_")}}
    save_json(f"{OUT}/switch_summary_{area}.json", summary)
    print(json.dumps(summary, indent=1))
    return summary

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "batches"
    area = sys.argv[2] if len(sys.argv) > 2 else "t2d"
    if cmd == "batches": make_batches(area)
    elif cmd == "prompt": print(batch_prompt(sys.argv[2]))
    elif cmd == "fuse": fuse(area)
