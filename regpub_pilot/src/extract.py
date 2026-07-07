"""Deterministic (model-free, offline-serializable) extractors.

Two independent readings of each trial's 'truth':
  extract_registry(ctgov_record) -> structured facts from the CT.gov results section
  classify_abstract(pubmed_record) -> usability verdict + reason + any effect fact

DETERMINISTIC-CORE INVARIANT: pure functions over cached JSON. No network, no model.
Same input -> same output. This is the poolable feedstock and the diff substrate.
"""
from __future__ import annotations
import re

# ---------------------------------------------------------------------------
# REGISTRY SIDE
# ---------------------------------------------------------------------------
RATIO_MEASURES = ("hazard ratio", "odds ratio", "risk ratio", "relative risk",
                  "rate ratio", "incidence rate ratio", "hr", "or", "rr")
DIFF_MEASURES = ("mean difference", "least squares mean difference", "difference in means",
                 "median difference", "difference", "md", "change")

def _measure_family(param_type):
    if not param_type:
        return None
    p = param_type.lower()
    if any(m in p for m in ("hazard", "odds", "risk ratio", "relative risk",
                            "rate ratio")) or p in ("hr", "or", "rr"):
        return "ratio"
    if any(m in p for m in ("mean difference", "difference in means",
                            "median difference")) or "difference" in p:
        return "diff"
    return "other"

def _pval_to_float(pv):
    if pv is None:
        return None
    s = str(pv).strip().replace(" ", "")
    m = re.match(r"^[<>]?=?(-?\d*\.?\d+)(e-?\d+)?$", s, re.I)
    if m:
        try:
            return float(m.group(0).lstrip("<>="))
        except ValueError:
            return None
    return None

def _sig_from(pval, lo, hi, family):
    """Significant at 0.05 iff p<0.05 OR CI excludes the null (1 ratio / 0 diff)."""
    p = _pval_to_float(pval)
    if p is not None:
        return p < 0.05
    if lo is not None and hi is not None:
        null = 1.0 if family == "ratio" else 0.0
        return not (lo <= null <= hi)
    return None

def extract_registry(rec):
    ps = rec.get("protocolSection", {})
    ident = ps.get("identificationModule", {})
    nct = ident.get("nctId")
    status = ps.get("statusModule", {})
    enroll = ps.get("designModule", {}).get("enrollmentInfo", {})
    enroll_actual = enroll.get("count") if enroll.get("type") == "ACTUAL" else None
    proto_primary = [o.get("measure", "").strip()
                     for o in (ps.get("outcomesModule", {}).get("primaryOutcomes", []) or [])
                     if o.get("measure")]
    start_date = (status.get("startDateStruct") or {}).get("date")
    start_year = None
    if start_date:
        m = re.match(r"(\d{4})", start_date)
        if m:
            start_year = int(m.group(1))
    out = {
        "nct": nct,
        "overall_status": status.get("overallStatus"),
        "start_date": start_date,
        "start_year": start_year,
        "completion_date": (status.get("completionDateStruct") or {}).get("date"),
        "enrollment_actual": enroll_actual,
        "protocol_primary_endpoints": proto_primary,
        "has_results": "resultsSection" in rec,
        "registry_primary": None,
        "usable_registry": False,
    }
    rs = rec.get("resultsSection", {})
    oms = rs.get("outcomeMeasuresModule", {}).get("outcomeMeasures", []) or []
    primaries = [o for o in oms if (o.get("type") == "PRIMARY")]
    if not primaries:
        return out
    o = primaries[0]
    fam = _measure_family(o.get("paramType"))
    est = {"measure_title": o.get("title", "").strip(),
           "param_type": o.get("paramType"), "unit": o.get("unitOfMeasure"),
           "family": fam, "point": None, "ci_lo": None, "ci_hi": None,
           "pvalue": None, "n_groups": len(o.get("groups", []) or []),
           "group_values": [], "has_analysis": False}
    # analyses (preferred: gives between-group effect + CI + p)
    analyses = o.get("analyses", []) or []
    if analyses:
        a = analyses[0]
        est["has_analysis"] = True
        try:
            est["point"] = float(a["paramValue"]) if a.get("paramValue") not in (None, "") else None
        except (ValueError, TypeError):
            est["point"] = None
        for k, dst in (("ciLowerLimit", "ci_lo"), ("ciUpperLimit", "ci_hi")):
            try:
                est[dst] = float(a[k]) if a.get(k) not in (None, "") else None
            except (ValueError, TypeError):
                est[dst] = None
        est["pvalue"] = a.get("pValue")
        est["analysis_param_type"] = a.get("paramType")
        # The between-group effect family comes from the ANALYSIS param type
        # (e.g. "Hazard Ratio (HR)"), which is more specific than the outcome-level
        # paramType (often "NUMBER"/"MEAN"). Prefer it whenever it resolves.
        afam = _measure_family(a.get("paramType"))
        if afam in ("ratio", "diff"):
            est["family"] = afam
    # group values (means per arm) from classes
    for cls in o.get("classes", []) or []:
        for cat in cls.get("categories", []) or []:
            for m in cat.get("measurements", []) or []:
                try:
                    est["group_values"].append({"group": m.get("groupId"),
                                                 "value": float(m.get("value"))})
                except (ValueError, TypeError):
                    pass
    est["significant"] = _sig_from(est["pvalue"], est["ci_lo"], est["ci_hi"], est["family"])
    out["registry_primary"] = est
    # usable iff we have an analysis with a point/p, OR >=2 group values
    out["usable_registry"] = bool(
        (est["has_analysis"] and (est["point"] is not None or _pval_to_float(est["pvalue"]) is not None))
        or len(est["group_values"]) >= 2)
    return out

# ---------------------------------------------------------------------------
# ABSTRACT SIDE
# ---------------------------------------------------------------------------
CI_RE = re.compile(
    r"95(?:\.\d+)?\s*%?\s*(?:ci|confidence interval)[\s:,]*[\[\(]?\s*"
    r"(-?\d+\.?\d*)\s*(?:to|,|–|—|-|\bto\b)\s*(-?\d+\.?\d*)", re.I)
# measure word ... up to 40 non-digit chars ... the point estimate. The 'reduction'
# exclusion prevents "38% relative risk reduction" being read as an effect estimate.
EFFECT_RE = re.compile(
    r"\b(hazard ratio|odds ratio|risk ratio|relative risk|rate ratio|mean difference|"
    r"hr|or|rr|md)\b(?!\s*reduction)[^.\dxX]{0,40}?(-?\d+\.\d+)", re.I)
MEANSD_RE = re.compile(r"(-?\d+\.?\d*)\s*(?:±|\+/-|\+/−|\bSD\b)\s*(\d+\.?\d*)", re.I)
PVAL_RE = re.compile(r"\bp\s*[<>=]\s*0?\.\d+", re.I)
MEDIAN_RE = re.compile(r"\bmedian\b", re.I)
IQR_RE = re.compile(r"\b(iqr|interquartile)\b", re.I)
PERCENT_RE = re.compile(r"\d+\.?\d*\s*%")
SUBGROUP_RE = re.compile(r"\bsubgroup", re.I)
NUM_RE = re.compile(r"-?\d+\.?\d*")
N_RE = re.compile(r"\b(?:n\s*=\s*|randomi[sz]ed\s+|assigned\s+(?:to\s+)?|enrolled\s+)(\d[\d,]{1,6})", re.I)

def _results_text(rec):
    """Prefer the RESULTS section of a structured abstract; fall back to full."""
    secs = rec.get("abstract_sections", []) or []
    res = " ".join(s["text"] for s in secs
                   if s.get("label") and "RESULT" in s["label"].upper())
    return res if res.strip() else rec.get("abstract", "")

def _abstract_direction(measure_word, point, ci_lo, ci_hi):
    fam = "ratio" if measure_word.lower() in ("hr", "or", "rr", "hazard ratio",
        "odds ratio", "risk ratio", "relative risk", "rate ratio") else "diff"
    return fam

def classify_abstract(rec):
    """Return usability verdict + reason + best-effort effect fact."""
    text = _results_text(rec)
    full = rec.get("abstract", "")
    out = {"pmid": rec.get("pmid"), "usable": False, "reason": None,
           "effect": None, "abstract_n": None, "has_abstract": bool(full.strip())}
    if not full.strip():
        out["reason"] = "no_abstract"
        return out
    # abstract total-N (best-effort; largest match near enrollment keyword)
    ns = [int(m.replace(",", "")) for m in N_RE.findall(full)]
    out["abstract_n"] = max(ns) if ns else None

    ci = CI_RE.search(text) or CI_RE.search(full)
    eff = EFFECT_RE.search(text) or EFFECT_RE.search(full)
    meansd = MEANSD_RE.findall(text)
    pval = PVAL_RE.search(text) or PVAL_RE.search(full)

    # Build the effect fact if we found a point estimate
    if eff:
        try:
            point = float(eff.group(2))
        except ValueError:
            point = None
        fam = _abstract_direction(eff.group(1), point, None, None)
        ci_lo = ci_hi = None
        if ci:
            try:
                ci_lo, ci_hi = float(ci.group(1)), float(ci.group(2))
            except ValueError:
                pass
        pv = None
        if pval:
            pv = pval.group(0)
        # Self-consistency guard: CI_RE and EFFECT_RE match independently and can pick a
        # point from one sentence and a CI from another (or grab a dose / an "HbA1c<=7.0%"
        # threshold as the point). If the point falls OUTSIDE the CI, the point grab is
        # spurious -> replace it with the CI midpoint (geo-mean for ratios) and flag.
        point_corrected = False
        if point is not None and ci_lo is not None and ci_hi is not None:
            lo, hi = min(ci_lo, ci_hi), max(ci_lo, ci_hi)
            if not (lo <= point <= hi):
                if fam == "ratio" and lo > 0 and hi > 0:
                    point = round((lo * hi) ** 0.5, 4)
                else:
                    point = round((lo + hi) / 2.0, 4)
                point_corrected = True
        sig = _sig_from(pv, ci_lo, ci_hi, fam)
        out["effect"] = {"measure": eff.group(1).lower(), "family": fam,
                         "point": point, "ci_lo": ci_lo, "ci_hi": ci_hi,
                         "pvalue": pv, "significant": sig,
                         "point_corrected": point_corrected}

    # ---- usability classification (priority order) ----
    if eff and ci:
        out["usable"], out["reason"] = True, "effect_with_ci"
    elif len(meansd) >= 2:
        out["usable"], out["reason"] = True, "means_sd"
    elif eff and pval:
        out["usable"], out["reason"] = True, "effect_with_p"   # marginal: SE recoverable from p+n
    else:
        # unusable — assign the dominant reason
        if MEDIAN_RE.search(text) and not MEANSD_RE.search(text):
            out["reason"] = "median_no_dispersion"
        elif PERCENT_RE.search(text) and not eff:
            out["reason"] = "relative_only"
        elif pval and not eff:
            out["reason"] = "pvalue_only"
        elif SUBGROUP_RE.search(text) and not eff:
            out["reason"] = "subgroup_only"
        elif NUM_RE.search(text):
            out["reason"] = "numbers_no_estimate"
        else:
            out["reason"] = "narrative_only"
    return out
