"""Regression: the real digitized OA drop (belotecan vs topotecan OS, PMC7884704)
reconstructs to an HR consistent with the reported 0.69 [0.48-0.99] and CONFIRMS.

This pins the one genuine reconstructed oncology survival datapoint recovered from
the 16 km_present_not_digitized OA papers. If a future edit to the reconstruction or
gate breaks it, this fails loudly.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from periphery.km_ipd import reconstruct_from_drop

DROP = os.path.join(os.path.dirname(HERE), "figures", "belotecan_topotecan_os", "manifest.json")


def test_belotecan_os_confirms():
    drop = json.load(open(DROP, encoding="utf-8"))
    r = reconstruct_from_drop(drop)
    assert r["reconstructed_from_figure"] is True
    assert r["synthetic"] is False
    assert r["trust_gate"]["verdict"] == "CONFIRMED"
    assert r["poolable"] is True
    # reported HR inside the reconstructed CI
    assert r["trust_gate"]["reported_in_recon_ci"] is True
    # reconstructed medians should be close to the reported 13.2 / 8.2 months
    assert abs(r["median_tx"] - 13.2) <= 2.0
    assert abs(r["median_ctrl"] - 8.2) <= 2.0
    assert r["provenance"]["figure"].startswith("PMC7884704")
