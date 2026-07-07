"""KM curve -> pseudo-IPD reconstruction periphery, wrapping Mahmood's KMDigitizer
(Guyot 2012). Offline, deterministic; no network, no model.

WHAT THIS DOES
--------------
Given a *figure drop* for a trial -- digitized ``time,survival`` coordinates for
two arms plus (ideally) an at-risk table and the arm sizes -- it:

  1. reconstructs pseudo-IPD via ``KMDigitizer.reconstruct_two_arm`` (Guyot),
  2. re-derives the log-rank hazard ratio from the reconstructed IPD,
  3. runs the TRUST GATE: compares the re-derived HR to the HR reported in the
     paper. Consistent -> the reconstructed survival effect is emitted as a
     poolable datapoint (flagged ``reconstructed_from_figure``). Inconsistent ->
     it is emitted as a DISCREPANCY and withheld from pooling (never silently
     pooled).

WHY A DROP, NOT A RASTER
------------------------
Automated tracing of a KM *curve* out of a raster figure is out of scope for the
deterministic core (it needs pixel work / a digitizer UI). So a curve is an
INPUT artifact here: produced once by WebPlotDigitizer (or KMDigitizer's own
browser tool) and dropped into ``periphery/figures/<pmid>/manifest.json``. Where
a paper clearly HAS a KM curve but no drop exists, the orchestrator records
``km_present_not_digitized`` -- an honest gap, mirroring Phase-1's
``pdf_unparseable`` bound, not a silent skip.

The numbers-at-risk row, by contrast, is often present as *text* in the JATS
table set, so ``numbers_at_risk_from_tables`` recovers it deterministically to
strengthen a drop that lacks one.
"""
from __future__ import annotations
import math
import re
from typing import Optional

from . import toolpaths

toolpaths.ensure_on_path()
# KMDigitizer is pure-stdlib; import after path is set.
from kmdigitizer import (  # noqa: E402
    Coord, AtRisk, parse_coords, parse_at_risk, reconstruct_two_arm,
)


# ---------------------------------------------------------------------------
# Trust gate
# ---------------------------------------------------------------------------
def trust_gate(recon_hr, recon_ci, reported_hr, reported_ci=None,
               *, pct_tol=0.20):
    """Decide whether a reconstructed HR is consistent with the reported HR.

    Two independent checks, BOTH required for CONFIRMED:
      (a) statistical containment: the reported HR lies inside the
          reconstructed 95% CI (a wide recon CI on a tiny trial is not, by
          itself, licence to trust a large point gap -- hence check b);
      (b) magnitude: the relative gap |recon-reported|/reported <= pct_tol.

    Returns a dict with verdict in {CONFIRMED, FLAGGED, UNGATED}. UNGATED means
    no reported HR was available to compare against (held out, not pooled)."""
    if reported_hr in (None, 0) or recon_hr in (None, 0):
        return {"verdict": "UNGATED", "reason": "no_reported_hr",
                "pct_gap": None, "reported_in_recon_ci": None}
    pct_gap = abs(recon_hr - reported_hr) / reported_hr
    in_ci = None
    if recon_ci and recon_ci[0] and recon_ci[1]:
        lo, hi = min(recon_ci), max(recon_ci)
        in_ci = lo <= reported_hr <= hi
    checks_ok = (in_ci is not False) and (pct_gap <= pct_tol)
    verdict = "CONFIRMED" if checks_ok else "FLAGGED"
    reason = None
    if verdict == "FLAGGED":
        bits = []
        if in_ci is False:
            bits.append("reported_hr_outside_recon_ci")
        if pct_gap > pct_tol:
            bits.append(f"pct_gap_{pct_gap:.0%}_gt_{pct_tol:.0%}")
        reason = "+".join(bits)
    return {"verdict": verdict, "reason": reason,
            "pct_gap": round(pct_gap, 4), "reported_in_recon_ci": in_ci,
            "pct_tol": pct_tol}


# ---------------------------------------------------------------------------
# Reconstruction from a figure drop
# ---------------------------------------------------------------------------
def _coords(obj):
    if isinstance(obj, str):
        return parse_coords(obj)
    return [Coord(t=float(t), s=float(s)) for t, s in obj]


def _atrisk(obj):
    if obj is None:
        return None
    if isinstance(obj, str):
        return parse_at_risk(obj)
    return [AtRisk(t=float(t), n=int(n)) for t, n in obj]


def reconstruct_from_drop(drop: dict, *, pct_tol=0.20) -> dict:
    """Reconstruct pseudo-IPD from one figure drop and apply the trust gate.

    ``drop`` schema (see periphery/figures/README):
        pmid, nct, endpoint, figure, digitization{method,quality},
        tx{label,n0,coords,at_risk?}, ctrl{label,n0,coords,at_risk?},
        reported{hr, ci_lo?, ci_hi?}
    Every field is local; nothing is fetched here.
    """
    tx, ctrl = drop["tx"], drop["ctrl"]
    rec = reconstruct_two_arm(
        _coords(tx["coords"]), _coords(ctrl["coords"]),
        int(tx["n0"]), int(ctrl["n0"]),
        _atrisk(tx.get("at_risk")), _atrisk(ctrl.get("at_risk")),
        tx.get("label", "Treatment"), ctrl.get("label", "Control"),
        validate=True,
    )
    lr = rec.logrank
    reported = drop.get("reported", {}) or {}
    rep_hr = reported.get("hr")
    rep_ci = ((reported.get("ci_lo"), reported.get("ci_hi"))
              if reported.get("ci_lo") and reported.get("ci_hi") else None)
    gate = trust_gate(lr.hr, lr.ci, rep_hr, rep_ci, pct_tol=pct_tol)

    dig = drop.get("digitization", {}) or {}
    return {
        "pmid": drop.get("pmid"), "nct": drop.get("nct"),
        "endpoint": drop.get("endpoint"),
        "measure": "HR", "family": "ratio",
        "reconstructed_from_figure": True,
        "recon_hr": lr.hr, "recon_ci": list(lr.ci) if lr.ci else None,
        "recon_p": lr.p,
        "recon_log_hr": lr.log_hr, "recon_se_log_hr": lr.se_log_hr,
        "recon_n": rec.total_n, "recon_events": rec.total_events,
        "median_tx": rec.median_tx, "median_ctrl": rec.median_ctrl,
        "reported_hr": rep_hr, "reported_ci": list(rep_ci) if rep_ci else None,
        "trust_gate": gate,
        # confidence tier folds the gate verdict + digitization quality
        "confidence_tier": _tier(gate, dig.get("quality")),
        "poolable": gate["verdict"] == "CONFIRMED",
        "provenance": {
            "source_doc": f"PMID:{drop.get('pmid')}" if drop.get("pmid") else None,
            "figure": drop.get("figure"),
            "digitization": dig,
            "at_risk_source": (
                "drop" if (tx.get("at_risk") or ctrl.get("at_risk")) else "none"),
            "tool": "KMDigitizer (Guyot 2012)",
        },
    }


def _tier(gate, dig_quality):
    v = gate["verdict"]
    if v == "CONFIRMED":
        return "reconstructed_verified" + (
            "_hi" if dig_quality in ("high", "pixel") else "")
    if v == "FLAGGED":
        return "reconstructed_discrepancy"
    return "reconstructed_ungated"


# ---------------------------------------------------------------------------
# Numbers-at-risk recovery from JATS table text (deterministic, offline)
# ---------------------------------------------------------------------------
_NAR_LABEL = re.compile(r"(number|no\.?|n)\s+at\s+risk", re.I)
_INT = re.compile(r"\b\d{1,6}\b")


def numbers_at_risk_from_tables(parsed_doc: dict):
    """Best-effort recovery of a numbers-at-risk row from the parsed JATS tables.

    Returns a list of candidate rows ``[{label, ints:[...]}]`` (caller matches to
    arms/time-grid). Deterministic string work over already-cached table text;
    no figure pixels involved. Empty list when no NAR row is present as text."""
    out = []
    for tb in parsed_doc.get("tables", []) or []:
        blob = " ".join(str(tb.get(k, "")) for k in ("label", "caption", "text"))
        if not _NAR_LABEL.search(blob):
            continue
        # take the integer run following the first NAR label occurrence
        m = _NAR_LABEL.search(blob)
        tail = blob[m.end(): m.end() + 400]
        ints = [int(x) for x in _INT.findall(tail)]
        if len(ints) >= 2:
            out.append({"label": (tb.get("label") or tb.get("caption") or "")[:80],
                        "ints": ints[:24]})
    return out


def km_curve_present(parsed_doc: dict) -> bool:
    """Heuristic: does this paper appear to contain a Kaplan-Meier survival
    figure? Used by the orchestrator to distinguish an honest
    ``km_present_not_digitized`` gap from a paper with no survival curve."""
    blob = ((parsed_doc.get("full_text") or "") + " "
            + " ".join(str(t.get("caption", "")) + " " + str(t.get("text", ""))
                       for t in (parsed_doc.get("tables", []) or []))).lower()
    return ("kaplan" in blob or "kaplan-meier" in blob
            or ("at risk" in blob and "survival" in blob))
