"""Regression tests for the diff-engine refinements (false-positive suppression)."""
import sys; sys.path.insert(0, ".")
from diff import _direction, endpoint_in_abstract, pick_index_abstract

def test_direction_helper():
    assert _direction("ratio", 0.86) == "reduction"
    assert _direction("ratio", 1.10) == "increase"
    assert _direction("ratio", 1.0) == "null"
    assert _direction("diff", -0.5) == "decrease"
    assert _direction("diff", 0.3) == "increase"

def test_databank_confirmed_index_preferred():
    recs = [
        {"pmid": "1", "abstract": "bg", "year": 2001, "pubtypes": ["Review"], "nct_accessions": []},
        {"pmid": "2", "abstract": "results", "year": 2015, "pubtypes": ["Randomized Controlled Trial"],
         "nct_accessions": ["NCT9"]},
    ]
    idx = pick_index_abstract(recs, nct="NCT9", start_year=2012)
    assert idx["pmid"] == "2", "should pick databank-confirmed RCT over background review"

def test_predate_filter():
    recs = [
        {"pmid": "1", "abstract": "bg", "year": 2006, "pubtypes": ["Randomized Controlled Trial"], "nct_accessions": []},
        {"pmid": "2", "abstract": "res", "year": 2013, "pubtypes": ["Journal Article"], "nct_accessions": []},
    ]
    # no databank-confirmed; start 2010 -> the 2006 paper is dropped as pre-trial
    idx = pick_index_abstract(recs, nct="NCTx", start_year=2010)
    assert idx["pmid"] == "2"

def test_endpoint_overlap():
    score, terms, hits = endpoint_in_abstract(
        ["Change in Glycated Hemoglobin A1c (HbA1c) From Baseline to Week 26"],
        "hba1c fell significantly from baseline")
    assert score is not None and score > 0  # 'hba1c' term hits

if __name__ == "__main__":
    for fn in (test_direction_helper, test_databank_confirmed_index_preferred,
               test_predate_filter, test_endpoint_overlap):
        fn(); print("  [ok]", fn.__name__)
    print("ALL DIFF TESTS PASSED")
