"""Trust-gate logic: CONFIRMED requires reported HR in recon CI AND small gap."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from periphery.km_ipd import trust_gate


def test_confirmed_when_in_ci_and_small_gap():
    g = trust_gate(0.72, (0.60, 0.86), reported_hr=0.70)
    assert g["verdict"] == "CONFIRMED"
    assert g["reported_in_recon_ci"] is True
    assert g["pct_gap"] < 0.05


def test_flagged_when_reported_outside_recon_ci():
    # DAPA-HF-like: reported 0.74 above recon CI upper 0.732
    g = trust_gate(0.649, (0.576, 0.732), reported_hr=0.74)
    assert g["verdict"] == "FLAGGED"
    assert "outside_recon_ci" in g["reason"]


def test_flagged_when_gap_exceeds_tol_even_if_in_ci():
    # KEYNOTE-024-like: wide recon CI contains reported, but 22% point gap
    g = trust_gate(0.609, (0.444, 0.834), reported_hr=0.50, pct_tol=0.20)
    assert g["reported_in_recon_ci"] is True
    assert g["verdict"] == "FLAGGED"
    assert "pct_gap" in g["reason"]


def test_ungated_without_reported_hr():
    g = trust_gate(0.7, (0.6, 0.8), reported_hr=None)
    assert g["verdict"] == "UNGATED"
    assert g["pct_gap"] is None
