"""RCT full-text extraction periphery, wrapping Mahmood's rct-extractor-v2.

Phase-1 already turns an OA paper (Europe PMC JATS / bronze-green HTML) into a
parsed section object ``{abstract, methods, results, discussion, tables[],
full_text, source_kind}`` (see src/jats.py). THIS module takes that object and
runs the deterministic RCT extractor over its text to recover structured effect
estimates (HR/OR/RR/MD + CI + p + SE) and arm-level data (poolable 2x2 /
continuous), each carrying:

  * PROVENANCE  -- source_doc (PMID), channel, section, and the verbatim
                   ``source_text`` span (+ char offsets) the value came from;
  * CONFIDENCE TIER -- folded from the extractor's own calibrated confidence /
                   plausibility / needs-review flags into A/B/C.

DETERMINISTIC-CORE SEAM: the extractor is rule/regex based (rapidfuzz + pydantic,
no ML model, no network). Same parsed doc -> same datapoints. It slots into the
pilot's model-free classification path; it does not call out to any service.
"""
from __future__ import annotations
from typing import Optional

from . import toolpaths

toolpaths.ensure_on_path()
import rct_extractor as rx  # noqa: E402

_RATIO = {"HR", "OR", "RR", "RATERATIO", "RATE_RATIO", "IRR", "HAZARD RATIO",
          "ODDS RATIO", "RISK RATIO", "RELATIVE RISK"}
_DIFF = {"MD", "SMD", "WMD", "MEAN DIFFERENCE", "DIFFERENCE"}


def _family(effect_type):
    t = (effect_type or "").upper().replace(" ", "")
    if t in {x.replace(" ", "") for x in _RATIO}:
        return "ratio"
    if t in {x.replace(" ", "") for x in _DIFF}:
        return "diff"
    return "other"


def _tier(e):
    """Fold the extractor's native quality signals into the pilot A/B/C tiers.

    A (high):   plausible ratio/diff with BOTH CI bounds, full-auto, no review flag.
    B (medium): point + (CI or p or SE) but flagged for review or p-only.
    C (low):    point only / needs_review / implausible.
    """
    has_ci = e.get("ci_lower") is not None and e.get("ci_upper") is not None
    has_p = e.get("p_value") is not None
    has_se = e.get("standard_error") is not None
    plausible = e.get("is_plausible", True)
    review = e.get("needs_review", False)
    conf = e.get("calibrated_confidence")
    if has_ci and plausible and not review and (conf is None or conf >= 0.8):
        return "A"
    if (has_ci or has_p or has_se) and plausible:
        return "B"
    return "C"


def _sections(parsed_doc):
    """Return (text, section_label) pairs to feed the extractor, richest first.

    We prefer the results section (where effects live) then fall back to the
    full text; we tag which section a run came from for provenance."""
    pairs = []
    for key in ("results", "full_text"):
        txt = parsed_doc.get(key) or ""
        if txt.strip():
            pairs.append((txt, key))
    return pairs


def extract_fulltext(parsed_doc: dict, *, specialty="auto", max_chars=40000) -> dict:
    """Extract structured RCT datapoints from ONE parsed full-text doc.

    Returns ``{pmid, specialty, subspecialty, datapoints:[...], arm_level, meta}``
    where each datapoint is provenance- and confidence-tagged and de-duplicated
    on (type, effect_size, ci). ``survival`` datapoints (type == HR) are marked so
    the orchestrator can cross-check them against a KM reconstruction."""
    pmid = str(parsed_doc.get("_pmid") or parsed_doc.get("pmid") or "")
    channel = parsed_doc.get("_channel")
    text, section = "", None
    for t, s in _sections(parsed_doc):
        text, section = t[:max_chars], s
        break
    if not text.strip():
        return {"pmid": pmid, "specialty": None, "datapoints": [],
                "arm_level": None, "meta": {"status": "no_text"}}

    res = rx.extract(text, specialty=specialty)
    dps = []
    seen = set()
    for e in res.get("effects", []) or []:
        fam = _family(e.get("type"))
        pt = e.get("effect_size")
        key = (e.get("type"), pt, e.get("ci_lower"), e.get("ci_upper"))
        if key in seen:
            continue
        seen.add(key)
        span = e.get("source_text")
        dps.append({
            "measure": e.get("type"), "family": fam,
            "point": pt, "ci_lo": e.get("ci_lower"), "ci_hi": e.get("ci_upper"),
            "p_value": e.get("p_value"),
            "se": e.get("standard_error"), "se_method": e.get("se_method"),
            "endpoint": e.get("endpoint"),
            "is_survival": (e.get("type") or "").upper() == "HR",
            "confidence_tier": _tier(e),
            "extractor_confidence": e.get("calibrated_confidence"),
            "needs_review": e.get("needs_review", False),
            "reconstructed_from_figure": False,
            "provenance": {
                "source_doc": f"PMID:{pmid}" if pmid else None,
                "channel": channel, "section": section,
                "source_span": span,
                "char_start": e.get("char_start"), "char_end": e.get("char_end"),
                "tool": "rct-extractor-v2",
            },
        })
    return {
        "pmid": pmid,
        "specialty": res.get("specialty"),
        "subspecialty": res.get("subspecialty"),
        "datapoints": dps,
        "arm_level": res.get("arm_level"),
        "meta": {"status": "ok", "section_used": section,
                 "n_effects": len(dps),
                 "n_survival": sum(1 for d in dps if d["is_survival"])},
    }
