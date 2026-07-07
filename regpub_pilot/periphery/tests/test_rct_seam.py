"""RCT extractor seam: parsed full-text doc -> provenance/tier-tagged datapoints.

Also guards the no-hallucination contract: a PROTOCOL-style sentence ("HRs will be
derived from a Cox model") must yield no effect datapoint.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from periphery.rct_fulltext import extract_fulltext


def _doc(results, pmid="123", channel="epmc_jats"):
    return {"_pmid": pmid, "_channel": channel, "_status": "parsed",
            "results": results, "full_text": results, "tables": []}


def test_extracts_hr_with_provenance_and_tier():
    doc = _doc("In the intention-to-treat population, overall survival favoured the "
               "drug (hazard ratio 0.68; 95% CI 0.56 to 0.83; p=0.002).")
    out = extract_fulltext(doc)
    hrs = [d for d in out["datapoints"] if d["measure"] == "HR"]
    assert hrs, "expected an HR datapoint"
    d = hrs[0]
    assert abs(d["point"] - 0.68) < 1e-6
    assert d["ci_lo"] == 0.56 and d["ci_hi"] == 0.83
    assert d["family"] == "ratio" and d["is_survival"] is True
    assert d["confidence_tier"] in ("A", "B")
    assert d["provenance"]["source_doc"] == "PMID:123"
    assert d["provenance"]["source_span"]          # verbatim span present
    assert d["reconstructed_from_figure"] is False


def test_protocol_text_yields_no_effect():
    doc = _doc("Hazard ratios and 95% confidence intervals will be derived from a "
               "Cox proportional-hazards model as the primary analysis.")
    out = extract_fulltext(doc)
    assert not out["datapoints"], "protocol text must not produce an effect (no hallucination)"


def test_empty_doc_is_safe():
    out = extract_fulltext({"_pmid": "9", "results": "", "full_text": ""})
    assert out["datapoints"] == []
    assert out["meta"]["status"] == "no_text"
