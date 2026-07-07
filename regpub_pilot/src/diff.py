"""Diff engine: three-state poolability model + discrepancy classifiers.

Per trial we hold two independent readings (registry facts, index-abstract facts)
and emit:
  poolability state  : BOTH / ONE / NEITHER usable
  discrepancy flags  : each a DIFFABLE FACT, with a 'contradicts' vs 'silent_on'
                       distinction (abstract OMISSION is never a discrepancy).

Classes: non_publication, enrollment_mismatch, direction_flip, significance_flip,
primary_endpoint (concordance / switch-candidate), ma_omission (GAP).

Pure/offline. Reads only cached JSON + extractor outputs.
"""
from __future__ import annotations
import re, json, os
from common import CT_DIR, PM_DIR, DATA, OUT, cache_path, load_json, save_json
from extract import extract_registry, classify_abstract

RCT_TYPES = {"randomized controlled trial", "clinical trial", "clinical trial, phase iii",
             "clinical trial, phase ii", "clinical trial, phase iv", "controlled clinical trial",
             "multicenter study", "comparative study", "pragmatic clinical trial"}

STOP = set("""time first occurrence any of the following adjudicated components composite
endpoint change from baseline to at week weeks month months day days year years number
participants percentage proportion rate mean median score index level total incidence
with without study period end point outcome measure value achieving who had over during
after within between per and or in on for a an the by is was were as compared versus vs
than least squares ls""".split())

TERM_RE = re.compile(r"[a-z][a-z0-9\-]{2,}")

def key_terms(name):
    return {t for t in TERM_RE.findall((name or "").lower()) if t not in STOP}

def endpoint_in_abstract(primary_names, abstract_text):
    """Concordance score in [0,1]: fraction of the registry primary endpoint's
    salient terms that appear in the abstract. Returns (score, terms, hit_terms)."""
    terms = set()
    for nm in primary_names:
        terms |= key_terms(nm)
    if not terms:
        return None, set(), set()
    at = (abstract_text or "").lower()
    hits = {t for t in terms if t in at}
    return len(hits) / len(terms), terms, hits

def pick_index_abstract(fetched_recs, nct=None, start_year=None):
    """Deterministic index-publication proxy.

    Reliability seam: a paper that lists THIS NCT in its PubMed databank field
    (nct_accessions) is genuinely reporting this trial; background/protocol citations
    manually attached as DERIVED refs do NOT (they predate registration). So we
    RESTRICT to databank-confirmed abstracts when any exist. As a secondary guard we
    drop abstracts published before the trial started. Then prefer RCT/trial pubtype,
    then earliest remaining year, then lowest PMID.
    NOT selected on endpoint-term match (would bias the endpoint-switch analysis)."""
    recs = [r for r in fetched_recs if r.get("abstract", "").strip()] or list(fetched_recs)
    if not recs:
        return None
    if nct:
        confirmed = [r for r in recs if nct in (r.get("nct_accessions") or [])]
        if confirmed:                  # trust the databank link over heuristics
            recs = confirmed
    if start_year:
        after = [r for r in recs if (r.get("year") or 9999) >= start_year - 1]
        if after:                      # don't empty the pool if all predate (rare)
            recs = after
    def rank(r):
        is_rct = any((pt or "").lower() in RCT_TYPES for pt in r.get("pubtypes", []))
        yr = r.get("year") or 9999
        try:
            pmid = int(r.get("pmid"))
        except (TypeError, ValueError):
            pmid = 10**12
        return (0 if is_rct else 1, yr, pmid)
    return sorted(recs, key=rank)[0]

def _direction(family, point):
    if point is None:
        return None
    if family == "ratio":
        if abs(point - 1.0) < 1e-9:
            return "null"
        return "reduction" if point < 1.0 else "increase"
    if family == "diff":
        if abs(point) < 1e-9:
            return "null"
        return "decrease" if point < 0 else "increase"
    return None

def diff_trial(nct, links):
    rec = load_json(cache_path(CT_DIR, nct)) or {}
    reg = extract_registry(rec)
    fetched = [load_json(cache_path(PM_DIR, p)) for p in links.get("fetched", [])]
    fetched = [r for r in fetched if r]
    n_linked = len(links.get("union", []))
    # 'reporting' publications = sponsor RESULT refs + reverse-databank [si] hits.
    # (Generic DERIVED refs are often pre-registration background citations, so they
    # do NOT count as a publication *of* this trial.)
    reporting = set(links.get("pmids_ctgov_result", [])) | set(links.get("pmids_si", []))
    n_reporting = len(reporting)
    idx = pick_index_abstract(fetched, nct, reg.get("start_year"))
    abs_cls = classify_abstract(idx) if idx else None
    idx_confirmed = bool(idx and nct in (idx.get("nct_accessions") or []))
    if abs_cls is not None:
        abs_cls["databank_confirmed"] = idx_confirmed

    reg_usable = reg["usable_registry"]
    # only a databank-confirmed abstract counts as a usable source FOR THIS TRIAL
    abs_usable = bool(abs_cls and abs_cls["usable"] and idx_confirmed)
    if reg_usable and abs_usable:
        state = "BOTH"
    elif reg_usable or abs_usable:
        state = "ONE"
    else:
        state = "NEITHER"

    flags = {}   # class -> {status: contradicts|silent_on|concordant|na, detail}

    # --- non_publication (trial level; whole sample) ---
    completed = reg["overall_status"] == "COMPLETED"
    if completed and n_reporting == 0:
        flags["non_publication"] = {"status": "contradicts",
            "detail": f"completed, results_posted={reg['has_results']}, 0 reporting "
                      f"publications ({n_linked} background-only refs)"}
    else:
        flags["non_publication"] = {"status": "concordant" if n_reporting else "na",
            "detail": f"{n_reporting} reporting pubs ({n_linked} total linked)"}

    # Abstract-dependent classes require an index abstract that GENUINELY reports this
    # trial (databank-confirmed). Without one, we cannot compare -> 'no_confirmed_pub'.
    if idx is None or not idx_confirmed:
        for c in ("enrollment_mismatch", "direction_flip", "significance_flip", "primary_endpoint"):
            flags[c] = {"status": "no_confirmed_pub",
                        "detail": "no databank-confirmed index publication in fetched set"}
        return {"nct": nct, "state": state, "reg": reg,
                "index_pmid": (idx.get("pmid") if idx else None),
                "index_confirmed": idx_confirmed, "abstract": abs_cls,
                "n_linked": n_linked, "n_reporting": n_reporting, "flags": flags}

    # --- enrollment mismatch ---
    ea, an = reg["enrollment_actual"], abs_cls["abstract_n"]
    if ea and an:
        rel = abs(ea - an) / max(ea, an)
        if an > ea * 1.10:
            # a LARGER published N than registered is a different/pooled population
            # (pooled PK, program-wide safety analysis), not a shrinkage discrepancy.
            flags["enrollment_mismatch"] = {"status": "silent_on",
                "detail": f"registry={ea} < abstract_n={an}: abstract N is a different/"
                          "pooled population, not this trial's enrolled set"}
        elif rel > 0.15:
            flags["enrollment_mismatch"] = {"status": "contradicts",
                "detail": f"registry={ea} vs abstract_n={an} (rel {rel:.2f}); "
                          "CAUTION: often analyzed/substudy vs randomized set (see report)",
                          "rel": round(rel, 3)}
        else:
            flags["enrollment_mismatch"] = {"status": "concordant",
                "detail": f"registry={ea} vs abstract_n={an} (rel {rel:.2f})"}
    else:
        flags["enrollment_mismatch"] = {"status": "silent_on",
            "detail": f"registry={ea} abstract_n={an}"}

    # --- direction / significance flip (need effects of same family) ---
    reg_eff = reg.get("registry_primary") or {}
    abs_eff = abs_cls.get("effect") or {}
    rfam, afam = reg_eff.get("family"), abs_eff.get("family")
    # Only compare directions/significance when the abstract effect is anchored by a CI
    # (a bare point with no interval is fragile — often a mis-extracted number).
    abs_effect_trusted = abs_eff.get("point") is not None and abs_eff.get("ci_lo") is not None
    if reg_eff.get("point") is not None and abs_effect_trusted and rfam == afam and rfam in ("ratio", "diff"):
        rd, ad = _direction(rfam, reg_eff["point"]), _direction(afam, abs_eff["point"])
        opposite = {("reduction", "increase"), ("increase", "reduction"),
                    ("decrease", "increase"), ("increase", "decrease")}
        reg_sig, abs_sig = reg_eff.get("significant"), abs_eff.get("significant")
        both_null = (reg_sig is False) and (abs_sig is False)
        if (rd, ad) in opposite and not both_null:
            # a sign change is only a real discrepancy if at least one side is
            # significant; when BOTH CIs include the null, opposite signs are noise
            # and the trial-level conclusion ("no effect") actually agrees.
            flags["direction_flip"] = {"status": "contradicts",
                "detail": f"registry {rd} (point {reg_eff['point']}, sig={reg_sig}) vs "
                          f"abstract {ad} (point {abs_eff['point']}, sig={abs_sig})"}
        elif (rd, ad) in opposite and both_null:
            flags["direction_flip"] = {"status": "concordant",
                "detail": f"opposite signs but both null (reg {reg_eff['point']} / abs {abs_eff['point']}) — agree on no effect"}
        else:
            flags["direction_flip"] = {"status": "concordant",
                "detail": f"registry {rd} vs abstract {ad}"}
    else:
        flags["direction_flip"] = {"status": "silent_on",
            "detail": f"reg_family={rfam} abs_family={afam}"}

    rs, as_ = reg_eff.get("significant"), abs_eff.get("significant")
    # only meaningful when the two effects plausibly describe the SAME endpoint family
    # (else we compare a registry HbA1c mean against an abstract responder odds ratio).
    same_family = rfam == afam and rfam in ("ratio", "diff")
    if rs is not None and as_ is not None and abs_effect_trusted and same_family:
        flags["significance_flip"] = {"status": "contradicts" if rs != as_ else "concordant",
            "detail": f"registry_sig={rs} abstract_sig={as_} (family {rfam})"}
    else:
        flags["significance_flip"] = {"status": "silent_on",
            "detail": f"registry_sig={rs} abstract_sig={as_} trusted={abs_effect_trusted} "
                      f"same_family={same_family}"}

    # --- primary endpoint concordance / switch-candidate ---
    score, terms, hits = endpoint_in_abstract(reg["protocol_primary_endpoints"], idx.get("abstract", ""))
    if score is None:
        flags["primary_endpoint"] = {"status": "na", "detail": "no registry primary name"}
    elif score >= 0.5:
        flags["primary_endpoint"] = {"status": "concordant",
            "detail": f"term overlap {score:.2f} ({len(hits)}/{len(terms)})", "score": round(score, 2)}
    elif score == 0.0:
        # registry primary completely absent from abstract: SILENT-ON, not a switch.
        flags["primary_endpoint"] = {"status": "silent_on",
            "detail": f"registry primary terms absent from abstract (score 0); "
                      "omission != switch — needs adjudication", "score": 0.0}
    else:
        flags["primary_endpoint"] = {"status": "switch_candidate",
            "detail": f"low term overlap {score:.2f} ({len(hits)}/{len(terms)}); adjudicate",
            "score": round(score, 2)}

    return {"nct": nct, "state": state, "reg": reg, "index_pmid": idx.get("pmid"),
            "index_confirmed": idx_confirmed, "abstract": abs_cls,
            "n_linked": n_linked, "n_reporting": n_reporting, "flags": flags}

def main():
    from common import index_path, links_path, trials_out
    idx = load_json(index_path())
    links = load_json(links_path())
    if links is None:
        raise SystemExit("links file missing — run link_pubmed.py first")
    rows = []
    for nct in idx["ncts"]:
        rows.append(diff_trial(nct, links.get(nct, {})))
    with open(trials_out(), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[diff] wrote {len(rows)} trial diffs -> {trials_out()}")

if __name__ == "__main__":
    main()
