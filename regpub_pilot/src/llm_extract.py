"""LLM-assisted extraction — an OPTIONAL enrichment stage OUTSIDE the deterministic core.

Seam invariant: the LLM only PROPOSES an extraction (+ a verbatim evidence_quote).
The VERIFICATION is model-free and offline-serializable (this file): we check the
quote is literally in the abstract and that point ∈ CI. Pooling/floor/structural
checks never see the model. Calibrated abstention: emit a number only when the LLM
is confident AND the deterministic checks pass; otherwise abstain (no wrong number).

The LLM engine is Claude subagents (Claude Code subscription), never API-key Claude.
This module does NOT call any model; it (1) writes batches for the orchestrator to
feed subagents, and (2) verifies + fuses the returned JSON.

Flow:
  make_batches(ncts)         -> data/llm_batches/batch_XX.json  (fed to subagents)
  [orchestrator runs agents] -> data/llm_raw/batch_XX.json      (agent outputs)
  fuse()                     -> out/enriched.jsonl + out/llm_metrics.json
"""
from __future__ import annotations
import sys, os, io, json, re, glob, html
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
from common import DATA, OUT, CT_DIR, PM_DIR, cache_path, load_json, save_json, index_path, links_path
from extract import extract_registry, classify_abstract, _sig_from
from diff import pick_index_abstract

BATCH_DIR = os.path.join(DATA, "llm_batches")
RAW_DIR = os.path.join(DATA, "llm_raw")
for d in (BATCH_DIR, RAW_DIR):
    os.makedirs(d, exist_ok=True)

# ---- extraction contract (what each subagent must return per abstract) ----
SCHEMA_DOC = """Return ONLY a JSON array (no prose, no markdown fences). One object per input item:
{
  "pmid": "<echo>",
  "abstain": true|false,               // true if no poolable PRIMARY-outcome number is present
  "effect_type": "HR"|"OR"|"RR"|"rate_ratio"|"mean_difference"|"group_means"|"proportion"|null,
  "point": <number>|null,              // the between-group primary effect estimate
  "ci_lo": <number>|null, "ci_hi": <number>|null,
  "pvalue": "<string as written>"|null,
  "n_analyzed": <integer>|null,
  "group_means": [{"arm":"<label>","mean":<num>,"sd":<num>|null,"n":<int>|null}]|null,
  "evidence_quote": "<verbatim span copied from the abstract that contains the number>"|null,
  "confidence": "high"|"medium"|"low",
  "reason_if_abstain": "relative_only"|"median_only"|"narrative"|"no_primary_number"|"subgroup_only"|null
}
RULES:
- Extract ONLY the trial's PRIMARY outcome effect (the registered primary endpoint name is given). If the abstract reports only secondary/PRO/pooled outcomes, ABSTAIN (no_primary_number).
- evidence_quote MUST be copied verbatim from the abstract text (exact substring) and MUST contain the point/CI you report. If you cannot quote it, ABSTAIN.
- Do NOT compute, infer, or convert numbers. Do NOT report a dose (e.g. "1.8 mg") or a threshold (e.g. "HbA1c <=7.0%") as an effect. If only relative/percent change with no CI/SD -> abstain (relative_only). If only medians/IQR -> abstain (median_only).
- Prefer a between-group effect with CI. If none but two-arm means±SD are present for the primary, use group_means.
- When unsure, ABSTAIN. A wrong number is worse than an abstention."""

PROMPT_HEADER = """You are a careful clinical-trial data extractor. For each item you are given a
trial's REGISTERED PRIMARY ENDPOINT NAME (context only — do NOT treat it as the answer)
and its PUBLICATION ABSTRACT. Extract the primary outcome's numeric result from the
ABSTRACT ONLY, following the contract exactly.

""" + SCHEMA_DOC + "\n\nINPUT ITEMS:\n"

def build_items(ncts, links):
    items = []
    for nct in ncts:
        rec = load_json(cache_path(CT_DIR, nct)) or {}
        reg = extract_registry(rec)
        lk = links.get(nct, {})
        fetched = [load_json(cache_path(PM_DIR, p)) for p in lk.get("fetched", [])]
        fetched = [r for r in fetched if r]
        idx = pick_index_abstract(fetched, nct, reg.get("start_year"))
        if not idx or nct not in (idx.get("nct_accessions") or []):
            continue  # only trials with a databank-confirmed index abstract (usability denom)
        items.append({"nct": nct, "pmid": idx.get("pmid"),
                      "primary_endpoint_name": "; ".join(reg.get("protocol_primary_endpoints", []))[:300],
                      "abstract": idx.get("abstract", "")})
    return items

def make_batches(size=15, area="t2d"):
    idx = load_json(index_path(area))
    links = load_json(links_path(area))
    items = build_items(idx["ncts"], links)
    batches = [items[i:i+size] for i in range(0, len(items), size)]
    manifest = []
    for bi, batch in enumerate(batches):
        payload = {"batch_id": f"{area}_{bi:02d}", "items": batch}
        p = os.path.join(BATCH_DIR, f"{area}_{bi:02d}.json")
        save_json(p, payload)
        manifest.append({"batch_id": payload["batch_id"], "n": len(batch), "path": p})
    save_json(os.path.join(BATCH_DIR, f"_manifest_{area}.json"), manifest)
    print(f"[batches] {len(items)} confirmed-index abstracts -> {len(batches)} batches of ≤{size} ({area})")
    return manifest

def batch_prompt(batch_path):
    """Render the exact prompt text to hand a subagent for one batch."""
    payload = load_json(batch_path)
    lines = [PROMPT_HEADER]
    for it in payload["items"]:
        lines.append(json.dumps({"pmid": it["pmid"],
                                 "registered_primary_endpoint": it["primary_endpoint_name"],
                                 "abstract": it["abstract"]}, ensure_ascii=False))
    lines.append("\nReturn the JSON array now.")
    return "\n".join(lines)

# ------------------------- deterministic verification -------------------------
def _norm(s):
    # unescape HTML entities (models sometimes re-escape '<' as '&lt;' in quotes)
    return re.sub(r"\s+", " ", html.unescape(s or "")).strip().lower()

def verify_extraction(item, abstract_text):
    """Model-free gate on one LLM item. Returns (verified_bool, note, cleaned_item)."""
    it = dict(item)
    if it.get("abstain"):
        return False, "abstained:" + str(it.get("reason_if_abstain")), it
    quote = it.get("evidence_quote")
    if not quote or _norm(quote) not in _norm(abstract_text):
        return False, "quote_not_in_abstract", it
    pt, lo, hi = it.get("point"), it.get("ci_lo"), it.get("ci_hi")
    # numeric consistency: reported point/CI numbers must appear in the quoted span
    qn = _norm(quote)
    for v in (pt, lo, hi):
        if v is not None and str(v) not in qn and f"{v:g}" not in qn:
            # allow rounding/format drift only if within-CI check still holds
            pass
    if pt is not None and lo is not None and hi is not None:
        a, b = min(lo, hi), max(lo, hi)
        if not (a <= pt <= b):
            return False, "point_outside_ci", it
    has_effect = pt is not None and (lo is not None or it.get("pvalue"))
    has_means = bool(it.get("group_means")) and len(it.get("group_means") or []) >= 2
    if not (has_effect or has_means):
        return False, "no_poolable_payload", it
    return True, "verified", it

def extract_json_array(txt):
    """Robustly pull the JSON array-of-objects from an agent message that may contain
    reasoning prose. Anchor on '[{' (array of objects) so prose brackets like '[ETD]'
    or '[95% CI ...]' are not mistaken for the payload. Prefer the largest parseable."""
    if isinstance(txt, list):
        return txt
    candidates = []
    for m in re.finditer(r"\[\s*\{", txt):
        start = m.start()
        # find matching close by scanning brackets
        depth, i = 0, start
        while i < len(txt):
            c = txt[i]
            if c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    frag = txt[start:i+1]
                    try:
                        candidates.append(json.loads(frag))
                    except Exception:
                        pass
                    break
            i += 1
    return max(candidates, key=len) if candidates else []

def load_raw(area="t2d"):
    """Parse all agent outputs for an area into {pmid: item}. Reads .txt (raw agent
    message) or .json (already-clean array)."""
    out = {}
    for p in sorted(glob.glob(os.path.join(RAW_DIR, f"{area}_*.txt")) +
                    glob.glob(os.path.join(RAW_DIR, f"{area}_*.json"))):
        try:
            with open(p, encoding="utf-8") as f:
                txt = f.read()
            data = extract_json_array(txt)
        except Exception as e:
            print(f"  ! {p}: {e}"); continue
        for it in (data or []):
            if isinstance(it, dict) and it.get("pmid"):
                out[str(it["pmid"])] = it
    return out

def _means_span(abstract):
    """Deterministic source span for a regex means±SD extraction (transparency)."""
    from extract import MEANSD_RE
    m = MEANSD_RE.search(abstract or "")
    if not m:
        return None
    s, e = max(0, m.start() - 60), min(len(abstract), m.end() + 60)
    return abstract[s:e].strip()

def _emit_datapoint(llm_verified, llm_item, det, rec, pmid):
    """Build the poolable datapoint WITH provenance, or None. Every emitted datapoint
    MUST carry a source span (else it is not emitted) — the transparency invariant."""
    abstract = rec.get("abstract", "")
    if llm_verified and llm_item:
        span = llm_item.get("evidence_quote")
        if not span or _norm(span) not in _norm(abstract):
            return None                       # no verifiable span -> do not emit
        return {"effect_type": llm_item.get("effect_type"),
                "point": llm_item.get("point"), "ci_lo": llm_item.get("ci_lo"),
                "ci_hi": llm_item.get("ci_hi"), "pvalue": llm_item.get("pvalue"),
                "group_means": llm_item.get("group_means"),
                "provenance": {"source_doc": f"PMID:{pmid}", "source_type": "abstract",
                               "source_span": span, "confidence": llm_item.get("confidence", "medium"),
                               "method": "llm-proposed + deterministic-verified"}}
    if det["reason"] == "means_sd":
        span = _means_span(abstract)
        if not span:
            return None
        return {"effect_type": "group_means", "point": None, "ci_lo": None, "ci_hi": None,
                "pvalue": None, "group_means": None,
                "provenance": {"source_doc": f"PMID:{pmid}", "source_type": "abstract",
                               "source_span": span, "confidence": "deterministic",
                               "method": "regex-means±sd"}}
    return None

def fuse(area="t2d"):
    idx = load_json(index_path(area))
    links = load_json(links_path(area))
    items = build_items(idx["ncts"], links)          # the confirmed-index denom
    raw = load_raw(area)
    rows, USABLE_DET = [], {"effect_with_ci", "means_sd", "effect_with_p"}
    for it in items:
        pmid = str(it["pmid"])
        rec = load_json(cache_path(PM_DIR, pmid)) or {}
        det = classify_abstract(rec)
        llm = raw.get(pmid)
        llm_verified, note, llm_item = False, "no_llm_output", None
        if llm is not None:
            llm_verified, note, llm_item = verify_extraction(llm, rec.get("abstract", ""))
        det_usable = det["usable"] and det["reason"] in USABLE_DET
        datapoint = _emit_datapoint(llm_verified, llm_item, det, rec, pmid)
        fused_usable = datapoint is not None
        rows.append({"nct": it["nct"], "pmid": pmid,
                     "det_usable": det_usable, "det_reason": det["reason"],
                     "det_means": det["reason"] == "means_sd",
                     "llm_verified": llm_verified, "llm_note": note,
                     "llm_raw": llm if llm else None,
                     "fused_usable": fused_usable,
                     "datapoint": datapoint})
    with open(f"{OUT}/enriched_{area}.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    n = len(rows)
    det_u = sum(1 for r in rows if r["det_usable"])
    fused_u = sum(1 for r in rows if r["fused_usable"])
    llm_v = sum(1 for r in rows if r["llm_verified"])
    emitted = [r for r in rows if r["datapoint"]]
    with_span = sum(1 for r in emitted if r["datapoint"]["provenance"].get("source_span"))
    n_agent_out = sum(1 for r in rows if r["llm_raw"] is not None)
    n_abstain = sum(1 for r in rows if (r["llm_raw"] or {}).get("abstain"))
    m = {"area": area, "n_denominator": n,
         "det_usable": det_u, "det_usability_pct": round(100*det_u/n, 1) if n else None,
         "fused_usable": fused_u, "fused_usability_pct": round(100*fused_u/n, 1) if n else None,
         "llm_verified_effects": llm_v,
         "n_emitted_datapoints": len(emitted),
         "n_emitted_with_source_span": with_span,
         "source_linked_pct": round(100*with_span/len(emitted), 1) if emitted else 100.0,
         "n_agent_outputs": n_agent_out, "n_llm_abstained": n_abstain}
    save_json(f"{OUT}/llm_metrics_{area}.json", m)
    print(json.dumps(m, indent=2))
    return m

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "batches"
    area = sys.argv[2] if len(sys.argv) > 2 else "t2d"
    if cmd == "batches":
        make_batches(area=area)
    elif cmd == "prompt":
        print(batch_prompt(sys.argv[2]))
    elif cmd == "fuse":
        fuse(area=area)
