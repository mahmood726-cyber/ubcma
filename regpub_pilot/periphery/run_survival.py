"""Orchestrate the periphery extraction over a Phase-1 area corpus.

For each parsed OA full-text doc in the area:
  1. run the RCT extractor (rct_fulltext) -> structured effect datapoints;
  2. if a digitized KM figure drop exists for that PMID, reconstruct pseudo-IPD
     (km_ipd), re-derive the HR, and apply the trust gate;
  3. CROSS-CHECK: when the full text also reports an HR for the same trial and a
     reconstruction exists, compare them (a second, independent consistency lens);
  4. classify each survival datapoint: CONFIRMED (poolable) / FLAGGED discrepancy
     (withheld) / UNGATED (held out);
  5. optionally pool the CONFIRMED reconstructed HRs with the pilot's own REML+HKSJ
     stack (src/pool.py) so the survival lift is quantified, not just asserted.

Writes ``out/survival_extraction_<area>.json``. Pure offline over cached inputs;
the ONLY networked step in the whole survival path remains Phase-1 acquisition.

Run (from regpub_pilot/):
    REGPUB_FT_PARSED=<parsed dir> PILOT_AREA=onc python -m periphery.run_survival
"""
from __future__ import annotations
import glob
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from . import toolpaths
from . import rct_fulltext
from . import km_ipd

HERE = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(HERE, "figures")
ROOT = os.path.dirname(HERE)               # regpub_pilot/
OUT = os.path.join(ROOT, "out")
os.makedirs(OUT, exist_ok=True)


def _load_drops():
    """Load every figure drop manifest: {pmid: drop}. A drop dir is any
    subdir of periphery/figures/ (except those prefixed '_' for internal use is
    still loaded, but flagged synthetic) holding a manifest.json."""
    drops = {}
    for mf in glob.glob(os.path.join(FIG_DIR, "*", "manifest.json")):
        try:
            d = json.load(open(mf, encoding="utf-8"))
        except Exception as e:
            print(f"[warn] bad drop manifest {mf}: {e}")
            continue
        pmid = str(d.get("pmid") or os.path.basename(os.path.dirname(mf)))
        d.setdefault("pmid", pmid)
        drops[pmid] = d
    return drops


def _area_pmids(area):
    """PMIDs belonging to ``area``, from that area's Phase-1 fetch summary.

    The summary sits in the ``out/`` dir that is a sibling of the parsed cache
    (which may be the concurrent Phase-1 lane's tree, not this worktree). We look
    there first, then this worktree's out/. Returns None if no summary is found
    (caller then processes the whole shared cache)."""
    parsed_dir = toolpaths.parsed_fulltext_dir()
    cache_out = os.path.join(os.path.dirname(os.path.dirname(parsed_dir)), "out")
    for base in (cache_out, OUT):
        summ = os.path.join(base, f"fulltext_fetch_{area}.json")
        if os.path.exists(summ):
            d = json.load(open(summ, encoding="utf-8"))
            return {str(r["pmid"]) for r in d.get("results", [])}
    return None


def _parsed_docs(area):
    """Yield ``(pmid, doc)`` parsed full-text docs for an area (or all, if the
    area's PMID set can't be resolved)."""
    parsed_dir = toolpaths.parsed_fulltext_dir()
    area_pmids = _area_pmids(area)
    for fp in glob.glob(os.path.join(parsed_dir, "*.json")):
        pmid = os.path.splitext(os.path.basename(fp))[0]
        if area_pmids is not None and pmid not in area_pmids:
            continue
        try:
            doc = json.load(open(fp, encoding="utf-8"))
        except Exception:
            continue
        doc.setdefault("_pmid", pmid)
        yield pmid, doc


def run(area):
    drops = _load_drops()
    rct_records, recon_records, discrepancies = [], [], []
    gaps = {"km_present_not_digitized": [], "no_survival_signal": 0}
    n_docs = 0
    corpus_ft_hr = {}  # pmid -> first full-text HR (for KM cross-check)

    # -- Pass 1: RCT extraction over the parsed corpus ---------------------------
    for pmid, doc in _parsed_docs(area):
        # only parsed docs carry usable text; stubs are honest Phase-1 misses
        if doc.get("_status") not in (None, "parsed"):
            continue
        n_docs += 1
        ext = rct_fulltext.extract_fulltext(doc)
        if ext["datapoints"]:
            rct_records.append(ext)
        ft_surv = [d for d in ext["datapoints"] if d.get("is_survival") and d.get("point")]
        if ft_surv:
            corpus_ft_hr[pmid] = ft_surv[0]["point"]
        # honest-gap accounting for the survival/KM opportunity
        if pmid not in drops:
            if km_ipd.km_curve_present(doc):
                gaps["km_present_not_digitized"].append(pmid)
            elif not ft_surv:
                gaps["no_survival_signal"] += 1

    # -- Pass 2: KM->IPD reconstruction for EVERY figure drop --------------------
    # A drop is an explicit digitization artifact; it is reconstructed whether or
    # not its paper is in the OA parsed corpus. When it IS in the corpus and the
    # full text also reports an HR, we add an independent cross-check.
    for pmid, drop in drops.items():
        recon = km_ipd.reconstruct_from_drop(drop)
        ft_hr = corpus_ft_hr.get(pmid)
        recon["cross_check"] = (
            {"fulltext_reported_hr": ft_hr,
             **km_ipd.trust_gate(recon["recon_hr"], recon.get("recon_ci"), ft_hr)}
            if ft_hr is not None else None)
        recon["in_oa_corpus"] = pmid in corpus_ft_hr or any(
            r["pmid"] == pmid for r in rct_records)
        recon_records.append(recon)
        if recon["trust_gate"]["verdict"] == "FLAGGED":
            discrepancies.append({
                "pmid": pmid, "nct": recon.get("nct"),
                "type": "reconstructed_vs_reported_hr_mismatch",
                "recon_hr": recon["recon_hr"], "reported_hr": recon["reported_hr"],
                "detail": recon["trust_gate"]})

    # Pool the CONFIRMED reconstructed survival HRs (quantify the lift). REAL and
    # SYNTHETIC drops are pooled SEPARATELY: the real pool is the clinical number;
    # the synthetic pool only demonstrates the REML+HKSJ engine end-to-end and must
    # never contaminate a clinical estimate.
    real = [r for r in recon_records if not r.get("synthetic")]
    synth = [r for r in recon_records if r.get("synthetic")]
    pooled_real = _pool_confirmed(real)
    pooled_synth = _pool_confirmed(synth)

    result = {
        "area": area,
        "n_docs_processed": n_docs,
        "rct_extractor": {
            "tool": "rct-extractor-v2",
            "docs_with_effects": len(rct_records),
            "total_effect_datapoints": sum(len(r["datapoints"]) for r in rct_records),
            "survival_datapoints": sum(
                sum(1 for d in r["datapoints"] if d["is_survival"]) for r in rct_records),
            "by_tier": _tier_counts(rct_records),
        },
        "km_reconstruction": {
            "tool": "KMDigitizer (Guyot 2012)",
            "drops_loaded": len(drops),
            "reconstructions": len(recon_records),
            "confirmed": sum(1 for r in recon_records
                             if r["trust_gate"]["verdict"] == "CONFIRMED"),
            "flagged": sum(1 for r in recon_records
                           if r["trust_gate"]["verdict"] == "FLAGGED"),
            "ungated": sum(1 for r in recon_records
                           if r["trust_gate"]["verdict"] == "UNGATED"),
            "real_confirmed": sum(1 for r in real
                                  if r["trust_gate"]["verdict"] == "CONFIRMED"),
            "real_confirmed_datapoints": [
                {"pmid": r["pmid"], "trial": r.get("trial"), "endpoint": r.get("endpoint"),
                 "recon_hr": r["recon_hr"], "recon_ci": r["recon_ci"],
                 "reported_hr": r["reported_hr"], "reported_ci": r.get("reported_ci"),
                 "pct_gap": r["trust_gate"]["pct_gap"], "tier": r["confidence_tier"]}
                for r in real if r["trust_gate"]["verdict"] == "CONFIRMED"],
            "pooled_real_confirmed": pooled_real,
            "pooled_synthetic_confirmed_ENGINE_CHECK_ONLY": pooled_synth,
        },
        "gaps": {"km_present_not_digitized": gaps["km_present_not_digitized"],
                 "km_present_not_digitized_n": len(gaps["km_present_not_digitized"]),
                 "no_survival_signal_n": gaps["no_survival_signal"]},
        "discrepancies": discrepancies,
        "reconstructions": recon_records,
        "rct_records": rct_records,
    }
    outp = os.path.join(OUT, f"survival_extraction_{area}.json")
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    _print_summary(result, outp)
    return result


def _tier_counts(rct_records):
    c = {"A": 0, "B": 0, "C": 0}
    for r in rct_records:
        for d in r["datapoints"]:
            c[d["confidence_tier"]] = c.get(d["confidence_tier"], 0) + 1
    return c


def _pool_confirmed(recon_records):
    """Pool CONFIRMED reconstructed log-HRs with the pilot's REML+HKSJ engine."""
    conf = [r for r in recon_records
            if r["trust_gate"]["verdict"] == "CONFIRMED"
            and r.get("recon_log_hr") is not None and r.get("recon_se_log_hr")]
    if len(conf) < 2:
        return {"k": len(conf), "note": "need >=2 confirmed HRs to pool"}
    try:
        sys.path.insert(0, os.path.join(ROOT, "src"))
        from pool import pool as _pool  # pilot's REML+HKSJ+PI engine
        import math
        yi = [r["recon_log_hr"] for r in conf]
        vi = [r["recon_se_log_hr"] ** 2 for r in conf]
        p = _pool(yi, vi, method="REML", hksj=True)
        return {"k": len(conf),
                "hr": round(math.exp(p["est"]), 3),
                "ci": [round(math.exp(p["ci_lo"]), 3), round(math.exp(p["ci_hi"]), 3)],
                "tau2": round(p["tau2"], 4), "I2": p["I2"]}
    except Exception as e:
        return {"k": len(conf), "error": f"pool_failed:{e}"}


def _print_summary(r, outp):
    print("=" * 74)
    print(f"SURVIVAL EXTRACTION — area={r['area']}  ({r['n_docs_processed']} parsed docs)")
    x = r["rct_extractor"]
    print(f"  RCT extractor  : {x['total_effect_datapoints']} effects "
          f"({x['survival_datapoints']} survival) in {x['docs_with_effects']} docs "
          f"| tiers {x['by_tier']}")
    k = r["km_reconstruction"]
    print(f"  KM->IPD (Guyot): {k['reconstructions']} reconstructions from "
          f"{k['drops_loaded']} drops — CONFIRMED {k['confirmed']} / "
          f"FLAGGED {k['flagged']} / UNGATED {k['ungated']}  "
          f"(REAL confirmed: {k['real_confirmed']})")
    for dp in k["real_confirmed_datapoints"]:
        print(f"     REAL  {dp['pmid']} {dp['trial'] or ''} [{dp['endpoint']}]: "
              f"recon HR {dp['recon_hr']} {dp['recon_ci']} vs reported {dp['reported_hr']} "
              f"(gap {dp['pct_gap']:.0%}) tier={dp['tier']}")
    print(f"  pooled REAL confirmed survival: {k['pooled_real_confirmed']}")
    print(f"  pooled SYNTHETIC (engine check only): {k['pooled_synthetic_confirmed_ENGINE_CHECK_ONLY']}")
    g = r["gaps"]
    print(f"  honest gaps    : KM-present-not-digitized {g['km_present_not_digitized_n']} "
          f"| no-survival-signal {g['no_survival_signal_n']}")
    print(f"  discrepancies flagged (not pooled): {len(r['discrepancies'])}")
    print(f"[survival] -> {outp}")


if __name__ == "__main__":
    area = os.environ.get("PILOT_AREA", "onc")
    run(area)
