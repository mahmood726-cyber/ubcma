"""Regression tests for the harms-omission class (guards the discipline fixes)."""
import sys; sys.path.insert(0, ".")
from harms import extract_registry_harms, classify_abstract_harms, harms_verdict

def _rec(groups, serious_events=None):
    return {"resultsSection": {"adverseEventsModule": {
        "eventGroups": groups, "seriousEvents": serious_events or []}}}

def test_zero_event_not_sae_data():
    # table present but all-zero serious -> nothing to omit
    r = extract_registry_harms(_rec([{"title": "A", "seriousNumAffected": 0, "seriousNumAtRisk": 100}]))
    assert r["has_sae_table"] is True and r["has_sae_data"] is False

def test_real_events_is_sae_data():
    r = extract_registry_harms(_rec([{"title": "A", "seriousNumAffected": 12, "seriousNumAtRisk": 100},
                                     {"title": "B", "seriousNumAffected": 5, "seriousNumAtRisk": 100}]))
    assert r["has_sae_data"] and r["total_serious_affected"] == 17 and r["total_at_risk"] == 200

def test_abstract_safety_is_mention():
    a = classify_abstract_harms({"abstract": "The vaccine was safe and reduced malaria.", "pubtypes": ["Randomized Controlled Trial"]})
    assert a["harms_mention"] and not a["harms_quantified"]

def test_omission_vs_mention():
    reg = extract_registry_harms(_rec([{"title": "A", "seriousNumAffected": 12, "seriousNumAtRisk": 100}]))
    silent = classify_abstract_harms({"abstract": "Efficacy was 95% against clinical malaria.", "pubtypes": ["Randomized Controlled Trial"]})
    assert harms_verdict(reg, silent)["status"] == "harms_omitted"
    quant = classify_abstract_harms({"abstract": "Serious adverse events occurred in 12% vs 8%.", "pubtypes": ["Randomized Controlled Trial"]})
    assert harms_verdict(reg, quant)["status"] == "harms_concordant"

def test_review_abstract_excluded():
    reg = extract_registry_harms(_rec([{"title": "A", "seriousNumAffected": 12, "seriousNumAtRisk": 100}]))
    rev = classify_abstract_harms({"abstract": "We review malaria vaccines.", "pubtypes": ["Review"]})
    assert harms_verdict(reg, rev)["status"] == "na_nontrial_abstract"

if __name__ == "__main__":
    for fn in (test_zero_event_not_sae_data, test_real_events_is_sae_data, test_abstract_safety_is_mention,
               test_omission_vs_mention, test_review_abstract_excluded):
        fn(); print("  [ok]", fn.__name__)
    print("ALL HARMS TESTS PASSED")
