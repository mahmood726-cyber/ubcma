"""Harms-omission discrepancy class (deterministic, model-free, offline).

The registry results section carries a STRUCTURED serious-adverse-event table
(adverseEventsModule.eventGroups[].seriousNumAffected/AtRisk). The abstract frequently
omits harms entirely (the journal-abstract layer subtracts harms — Boutron spin). This
module measures that asymmetry with provenance, per the pre-registration.

Reporting-asymmetry, NOT misconduct: an abstract is space-limited. The honest claim is
"the registry harms table is machine-readable; the abstract usually is not" -> route to
the registry table.
"""
from __future__ import annotations
import re

# ---- registry side ---------------------------------------------------------
def extract_registry_harms(rec):
    rs = rec.get("resultsSection", {})
    ae = rs.get("adverseEventsModule", {})
    out = {"has_sae_data": False, "n_serious_terms": 0, "groups": [],
           "total_serious_affected": None, "total_at_risk": None,
           "has_deaths_data": False, "total_deaths": None}
    if not ae:
        return out
    groups = ae.get("eventGroups", []) or []
    ser_aff = ser_risk = deaths = 0
    any_ser = any_death = False
    gsum = []
    for g in groups:
        sa, sr = g.get("seriousNumAffected"), g.get("seriousNumAtRisk")
        da = g.get("deathsNumAffected")
        if sa is not None and sr is not None:
            any_ser = True
            ser_aff += sa; ser_risk += sr
            gsum.append({"group": g.get("title", "")[:40], "serious": sa, "at_risk": sr})
        if da is not None:
            any_death = True; deaths += da
    # A serious-AE TABLE can be present with all-zero counts (no serious events actually
    # occurred). There is nothing to "omit" in that case, so has_sae_data requires that at
    # least one serious event was reported (ser_aff > 0). Honest denominator.
    out["has_sae_table"] = any_ser
    out["has_sae_data"] = any_ser and ser_aff > 0
    out["n_serious_terms"] = len(ae.get("seriousEvents", []) or [])
    out["groups"] = gsum
    if any_ser:
        out["total_serious_affected"] = ser_aff
        out["total_at_risk"] = ser_risk
    out["has_deaths_data"] = any_death
    if any_death:
        out["total_deaths"] = deaths
    return out

# ---- abstract side ---------------------------------------------------------
HARMS_TERMS = re.compile(
    r"\b(adverse event|adverse effect|adverse reaction|side[- ]effect|serious adverse|"
    r"\bsae\b|\baes?\b|toxicit|tolerab|well[- ]tolerated|safe(?:ty)?\b|unsafe|"
    r"grade [3-5]|grade 3|discontinu\w*|withdraw\w* (?:due to|because of)|"
    r"treatment[- ]related|drug[- ]related|hepatotox|nephrotox|cardiotox|reactogenic|"
    r"\bharm\b|\bharms\b)", re.I)
# bare "safe"/"safety" now counts as a (weak) harms mention -> conservative against
# over-calling omission (an abstract that says "safe and well tolerated" is NOT an omission).
HARMS_QUANT = re.compile(
    r"(grade [3-5][^.]{0,40}\d|(\d+\.?\d*\s*%[^.]{0,40}(adverse|event|toxicit|discontinu|grade))|"
    r"((adverse|serious|toxicit|discontinu|grade)[^.]{0,40}\d+\.?\d*\s*%)|"
    r"(\bsae\b[^.]{0,30}\d)|(\d+[^.]{0,20}serious adverse))", re.I)

def classify_abstract_harms(abstract_rec):
    text = (abstract_rec or {}).get("abstract", "") or ""
    pubtypes = [(p or "").lower() for p in (abstract_rec or {}).get("pubtypes", [])]
    # is this a RESULTS publication (vs review/comment/protocol)?
    is_review = any("review" in p or "comment" in p or "editorial" in p or "meta-analysis" in p
                    for p in pubtypes)
    mention = bool(HARMS_TERMS.search(text))
    quant = bool(HARMS_QUANT.search(text))
    m = HARMS_TERMS.search(text)
    return {"has_abstract": bool(text.strip()),
            "harms_mention": mention, "harms_quantified": quant,
            "is_review_or_nontrial": is_review,
            "evidence_term": (m.group(0) if m else None)}

def harms_verdict(reg_h, abs_h):
    """Only trials where the REGISTRY has serious-AE data are in the denominator."""
    if not reg_h.get("has_sae_data"):
        return {"status": "na_no_registry_harms"}
    if not abs_h.get("has_abstract"):
        return {"status": "na_no_abstract"}
    if abs_h.get("is_review_or_nontrial"):
        return {"status": "na_nontrial_abstract"}
    if not abs_h.get("harms_mention"):
        return {"status": "harms_omitted",
                "detail": f"registry serious-AE {reg_h.get('total_serious_affected')}/"
                          f"{reg_h.get('total_at_risk')} across {len(reg_h.get('groups',[]))} arms; "
                          "abstract SILENT on harms"}
    if not abs_h.get("harms_quantified"):
        return {"status": "harms_underreported",
                "detail": f"abstract mentions harms ('{abs_h.get('evidence_term')}') but does not quantify"}
    return {"status": "harms_concordant",
            "detail": f"both report harms (abstract quantifies)"}
