"""Full-text extraction layer — the poolable-ceiling lever (Phase 1).

Runs the SAME calibrated-abstention extraction the abstract layer uses, but over the
retrieved OA full text (Results + Methods + result tables) instead of the abstract.
This is where the pilot's stated hard gap closes: the abstract often reports only a
relative %, a median, or narrative, while the full-text Results / tables carry the
between-group primary effect with a CI.

SEAM (unchanged): the model only PROPOSES an extraction + a verbatim evidence_quote.
Verification is model-free (this file): the quote must be a literal substring of the
exact text we handed the model, and point must lie inside its CI. Nothing poolable is
emitted without a source span. Calibrated abstention: a wrong number is worse than an
abstention.

To keep the model's job bounded AND the seam clean, a deterministic PRE-FILTER shrinks
each article to compact verbatim "candidate windows" around statistics + primary-endpoint
terms. The model selects the primary among candidates; the windows are all literal
substrings, so evidence-quote verification stays exact.

Flow (mirrors llm_extract):
  make_ft_batches(area) -> data/ft_batches/{area}_NN.json   (fed to subagents)
  [orchestrator runs agents] -> data/ft_raw/{area}_NN.txt   (agent outputs)
  fuse_ft(area) -> out/fulltext_enriched_{area}.jsonl + out/fulltext_metrics_{area}.json
"""
from __future__ import annotations
import sys, os, io, json, re, glob
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
from common import DATA, OUT, CT_DIR, PM_DIR, cache_path, load_json, save_json, index_path, links_path
from extract import extract_registry, CI_RE, EFFECT_RE, MEANSD_RE, PVAL_RE
from diff import key_terms
from llm_extract import build_items, verify_extraction, extract_json_array, _norm

FT_PARSED = os.path.join(DATA, "fulltext_parsed")
FT_BATCH = os.path.join(DATA, "ft_batches")
FT_RAW = os.path.join(DATA, "ft_raw")
for d in (FT_BATCH, FT_RAW):
    os.makedirs(d, exist_ok=True)

# ---------------------------------------------------------------------------
# deterministic candidate-window pre-filter
# ---------------------------------------------------------------------------
NUM_NEAR = re.compile(r"\d")

def _windows(text, spans, pad=260):
    """Merge ±pad char windows around (start,end) spans into non-overlapping slices."""
    if not spans:
        return []
    ivs = sorted(((max(0, s - pad), min(len(text), e + pad)) for s, e in spans))
    merged = [list(ivs[0])]
    for a, b in ivs[1:]:
        if a <= merged[-1][1] + 40:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return [text[a:b].strip() for a, b in merged]

def candidate_text(parsed, primary_names, cap=9000):
    """Compact set of verbatim excerpts most likely to hold the primary effect.

    Windows around: effect words, 95% CIs, means±SD, p-values, and primary-endpoint
    key terms that sit near a number. All excerpts are literal substrings of the body,
    so an evidence_quote drawn from them verifies exactly."""
    body = " ".join(filter(None, [parsed.get("results", ""), parsed.get("methods", "")]))
    tables = " ".join(t.get("text", "") for t in (parsed.get("tables") or []))
    full = (body + "  " + tables).strip()
    if not full:
        return "", {}
    spans = []
    for rgx in (EFFECT_RE, CI_RE, MEANSD_RE, PVAL_RE):
        for m in rgx.finditer(full):
            spans.append((m.start(), m.end()))
    # primary-endpoint term windows (only where a digit sits within ~120 chars)
    terms = set()
    for nm in primary_names:
        terms |= key_terms(nm)
    low = full.lower()
    for t in terms:
        if len(t) < 4:
            continue
        for m in re.finditer(re.escape(t), low):
            s, e = m.start(), m.end()
            around = full[max(0, s - 120):min(len(full), e + 120)]
            if NUM_NEAR.search(around):
                spans.append((s, e))
    wins = _windows(full, spans)
    stats = {"n_stat_spans": len(spans), "n_windows": len(wins), "body_chars": len(full)}
    # assemble, capped; prefer windows containing a CI (most poolable) first
    wins.sort(key=lambda w: (0 if CI_RE.search(w) else 1, -len(w)))
    out, total = [], 0
    for w in wins:
        if total + len(w) > cap:
            continue
        out.append(w); total += len(w)
    excerpt = "  ///  ".join(out)
    stats["excerpt_chars"] = len(excerpt)
    return excerpt, stats

# ---------------------------------------------------------------------------
# batch construction  (only the GAP set: trials not already poolable)
# ---------------------------------------------------------------------------
def _load_fused_rows(area):
    """The baseline is TRIAL-denominated (one row per trial). A few trials share an
    index PMID (one paper reports >1 NCT), so we must count trials (rows), never
    collapse by pmid. Returns the list of enriched rows."""
    ep = os.path.join(OUT, f"enriched_{area}.jsonl")
    return [json.loads(l) for l in open(ep, encoding="utf-8")] if os.path.exists(ep) else []

def _fused_by_pmid(area):
    """pmid -> fused_usable (True if ANY trial on that pmid is already poolable)."""
    m = {}
    for r in _load_fused_rows(area):
        p = str(r["pmid"]); m[p] = m.get(p, False) or r["fused_usable"]
    return m

def build_ft_items(area, gap_only=True):
    idx = load_json(index_path(area)); links = load_json(links_path(area))
    items = build_items(idx["ncts"], links)
    fused = _fused_by_pmid(area)
    out = []
    for it in items:
        pmid = str(it["pmid"])
        if gap_only and fused.get(pmid):
            continue
        parsed_p = os.path.join(FT_PARSED, f"{pmid}.json")
        parsed = load_json(parsed_p)
        if not parsed or parsed.get("_status") != "parsed":
            continue                       # no usable full text for this trial
        rec = load_json(cache_path(CT_DIR, pmid))  # (not needed but keep symmetry)
        reg_rec = load_json(cache_path(CT_DIR, it["nct"])) or {}
        reg = extract_registry(reg_rec)
        primary = reg.get("protocol_primary_endpoints", [])
        excerpt, stats = candidate_text(parsed, primary)
        if not excerpt.strip():
            continue
        out.append({"nct": it["nct"], "pmid": pmid,
                    "primary_endpoint_name": "; ".join(primary)[:300],
                    "source_doc": _source_doc(parsed, pmid),
                    "channel": parsed.get("_channel"),
                    "extraction_text": excerpt, "stats": stats})
    return out

def _source_doc(parsed, pmid):
    ch = parsed.get("_channel", "")
    if ch == "epmc_jats":
        # pmcid recorded in the raw path; recover from fetch record if present
        return f"PMID:{pmid}(fulltext:EuropePMC-JATS)"
    return f"PMID:{pmid}(fulltext:{ch})"

SCHEMA_DOC = """Return ONLY a JSON array (no prose, no markdown fences). One object per input item:
{
  "pmid": "<echo>",
  "abstain": true|false,
  "effect_type": "HR"|"OR"|"RR"|"rate_ratio"|"mean_difference"|"group_means"|"proportion"|null,
  "point": <number>|null,
  "ci_lo": <number>|null, "ci_hi": <number>|null,
  "pvalue": "<string as written>"|null,
  "n_analyzed": <integer>|null,
  "group_means": [{"arm":"<label>","mean":<num>,"sd":<num>|null,"n":<int>|null}]|null,
  "evidence_quote": "<verbatim span copied from the PROVIDED EXCERPTS containing the number>"|null,
  "confidence": "high"|"medium"|"low",
  "reason_if_abstain": "relative_only"|"median_only"|"narrative"|"no_primary_number"|"subgroup_only"|null
}
RULES:
- You are given VERBATIM EXCERPTS from a trial's OPEN-ACCESS FULL TEXT (Results + tables), separated by "///", plus the trial's REGISTERED PRIMARY ENDPOINT NAME (context — NOT the answer).
- Extract ONLY the registered PRIMARY outcome's between-group effect. The excerpts contain many numbers (secondary outcomes, subgroups, baseline characteristics) — pick the one matching the PRIMARY endpoint. If the primary outcome's number is not present in the excerpts, ABSTAIN (no_primary_number).
- evidence_quote MUST be copied verbatim from the PROVIDED EXCERPTS (exact substring) and MUST contain the point/CI you report. If you cannot quote it from the excerpts, ABSTAIN.
- Do NOT compute, infer, or convert. Do NOT report a dose or a threshold as an effect. Only relative/percent change with no CI/SD -> abstain (relative_only). Only medians/IQR -> abstain (median_only).
- Prefer a between-group effect with 95% CI. If none but two-arm means±SD for the primary are present, use group_means.
- When unsure, ABSTAIN. A wrong number is worse than an abstention."""

PROMPT_HEADER = ("You are a careful clinical-trial data extractor working from OPEN-ACCESS FULL TEXT.\n"
                 + SCHEMA_DOC + "\n\nINPUT ITEMS:\n")

def make_ft_batches(area, size=8):
    items = build_ft_items(area, gap_only=True)
    batches = [items[i:i+size] for i in range(0, len(items), size)]
    manifest = []
    for bi, batch in enumerate(batches):
        payload = {"batch_id": f"{area}_{bi:02d}", "items": batch}
        p = os.path.join(FT_BATCH, f"{area}_{bi:02d}.json")
        save_json(p, payload)
        manifest.append({"batch_id": payload["batch_id"], "n": len(batch), "path": p})
    save_json(os.path.join(FT_BATCH, f"_manifest_{area}.json"), manifest)
    print(f"[ft-batches] {len(items)} gap trials with full text -> {len(batches)} batches of <={size} ({area})")
    return manifest

def ft_batch_prompt(batch_path):
    payload = load_json(batch_path)
    lines = [PROMPT_HEADER]
    for it in payload["items"]:
        lines.append(json.dumps({"pmid": it["pmid"],
                                 "registered_primary_endpoint": it["primary_endpoint_name"],
                                 "full_text_excerpts": it["extraction_text"]}, ensure_ascii=False))
    lines.append("\nReturn the JSON array now.")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# fuse: verify LLM items against the EXACT excerpt text, emit poolable datapoints
# ---------------------------------------------------------------------------
def load_ft_raw(area):
    out = {}
    for p in sorted(glob.glob(os.path.join(FT_RAW, f"{area}_*.txt")) +
                    glob.glob(os.path.join(FT_RAW, f"{area}_*.json"))):
        try:
            with open(p, encoding="utf-8") as f:
                data = extract_json_array(f.read())
        except Exception as e:
            print(f"  ! {p}: {e}"); continue
        for it in (data or []):
            if isinstance(it, dict) and it.get("pmid"):
                out[str(it["pmid"])] = it
    return out

def _emit_ft_datapoint(llm_item, excerpt, source_doc, pmid):
    """Poolable datapoint WITH source span, or None. Span MUST be verbatim in excerpt."""
    span = llm_item.get("evidence_quote")
    if not span or _norm(span) not in _norm(excerpt):
        return None
    return {"effect_type": llm_item.get("effect_type"),
            "point": llm_item.get("point"), "ci_lo": llm_item.get("ci_lo"),
            "ci_hi": llm_item.get("ci_hi"), "pvalue": llm_item.get("pvalue"),
            "group_means": llm_item.get("group_means"),
            "provenance": {"source_doc": source_doc, "source_type": "fulltext_results",
                           "source_span": span, "confidence": llm_item.get("confidence", "medium"),
                           "method": "llm-proposed + deterministic-verified (fulltext)"}}

def fuse_ft(area):
    # TRIAL-denominated: one row per gap trial (keyed by nct), even when two trials
    # share an index PMID (one paper, two NCTs) — both become poolable from that doc.
    items = build_ft_items(area, gap_only=True)
    raw = load_ft_raw(area)
    rows = []
    for it in items:
        pmid = it["pmid"]
        llm = raw.get(pmid)
        verified, note, datapoint = False, "no_llm_output", None
        if llm is not None:
            verified, note, clean = verify_extraction(llm, it["extraction_text"])
            if verified:
                datapoint = _emit_ft_datapoint(clean, it["extraction_text"], it["source_doc"], pmid)
                if datapoint is None:
                    verified, note = False, "span_not_in_excerpt"
        rows.append({"nct": it["nct"], "pmid": pmid, "channel": it["channel"],
                     "source_doc": it["source_doc"],
                     "ft_verified": verified, "ft_note": note,
                     "llm_raw": llm, "ft_usable": datapoint is not None,
                     "datapoint": datapoint})
    with open(os.path.join(OUT, f"fulltext_enriched_{area}.jsonl"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    # metrics (trial-denominated, matches the abstract-layer baseline denominator)
    base_rows = _load_fused_rows(area)
    denom = len(base_rows)
    base_usable = sum(1 for r in base_rows if r["fused_usable"])
    ft_recovered = [r for r in rows if r["ft_usable"]]
    new_poolable = base_usable + len(ft_recovered)
    emitted = [r for r in rows if r["datapoint"]]
    with_span = sum(1 for r in emitted if r["datapoint"]["provenance"].get("source_span"))
    from collections import Counter
    by_ch = Counter(r["channel"] for r in ft_recovered)
    n_agent = sum(1 for r in rows if r["llm_raw"] is not None)
    n_abstain = sum(1 for r in rows if (r["llm_raw"] or {}).get("abstain"))
    m = {"area": area, "n_denominator": denom,
         "baseline_fused_usable": base_usable,
         "baseline_fused_pct": round(100*base_usable/denom, 1) if denom else None,
         "ft_gap_trials_with_fulltext_examined": len(rows),
         "ft_recovered": len(ft_recovered),
         "ft_recovered_by_channel": dict(by_ch),
         "new_poolable": new_poolable,
         "new_poolable_pct": round(100*new_poolable/denom, 1) if denom else None,
         "lift_pts": round(100*(new_poolable-base_usable)/denom, 1) if denom else None,
         "n_emitted_datapoints": len(emitted),
         "n_emitted_with_source_span": with_span,
         "source_linked_pct": round(100*with_span/len(emitted), 1) if emitted else 100.0,
         "n_agent_outputs": n_agent, "n_llm_abstained": n_abstain}
    save_json(os.path.join(OUT, f"fulltext_metrics_{area}.json"), m)
    print(json.dumps(m, indent=2))
    return m

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "batches"
    area = os.environ.get("PILOT_AREA", sys.argv[2] if len(sys.argv) > 2 else "t2d")
    if cmd == "batches":
        make_ft_batches(area)
    elif cmd == "prompt":
        print(ft_batch_prompt(sys.argv[2]))
    elif cmd == "fuse":
        fuse_ft(area)
