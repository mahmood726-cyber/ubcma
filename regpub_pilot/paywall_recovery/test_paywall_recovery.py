"""Regression guards for the open-supplement recovery probe.

These lock the honest headline numbers to the committed artifacts so a later refactor
cannot silently inflate the recovery rate. Run: python -m pytest test_paywall_recovery.py
"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); OUTD = os.path.join(HERE, "out")

def _load(name):
    return json.load(open(os.path.join(OUTD, name), encoding="utf-8"))

def test_denominator_is_108():
    rows = _load("paywalled_set.json")
    assert len(rows) == 108
    assert sum(1 for r in rows if r["area"] == "onc") == 38
    assert sum(1 for r in rows if r["area"] == "t2d") == 70

def test_epmc_and_ncbi_channels_recover_zero():
    """Both OA-subset APIs refuse every in-PMC paper (all isOpenAccess=N)."""
    supp = _load("supp_probe.json")
    assert len(supp) == 31
    assert all(x["isOpenAccess"] == "N" for x in supp)
    assert sum(1 for x in supp if x["epmc_supp"] == "OPEN") == 0
    assert sum(1 for x in supp if x["ncbi_oa"] == "OPEN_LINKS") == 0
    # 10 papers HOLD an EPMC bundle but none is served openly
    assert sum(1 for x in supp if x["hasSuppl"] == "Y") == 10

def test_worked_recovery_consensus_confirmed():
    v = _load("recovery_xcheck_verdict.json")
    assert v["pmid"] == "24552155"
    assert v["n_values"] == 18
    assert v["max_abs_dev"] == 0.0
    assert v["verdict"] == "CONFIRMED"

def test_no_km_and_no_pivotal_hr_recovered():
    cov = _load("coverage_summary.json")
    est = cov["recovery_rate_estimate"]
    assert est["pivotal_survival_HRs_newly_recovered"] == 0
    assert est["km_reconstruction_candidates_in_open_supplements"] == 0
    yld = cov["content_yield_of_retrieved"]["counts"]
    assert yld["km_plus_atrisk"] == 0
    assert yld["structured_tables"] == 2

def test_recovery_rate_is_low_and_honest():
    cov = _load("coverage_summary.json")
    est = cov["recovery_rate_estimate"]
    # genuine open-supplement recovery is a ~1% sliver of the 108-paper pocket
    assert est["genuine_open_supplement_recovery_of_poolable_data"]["n"] == 1
    assert est["genuine_open_supplement_recovery_of_poolable_data"]["rate_of_pocket_pct"] < 2.0

if __name__ == "__main__":
    import subprocess, sys
    sys.exit(subprocess.call([sys.executable, "-m", "pytest", __file__, "-q"]))
