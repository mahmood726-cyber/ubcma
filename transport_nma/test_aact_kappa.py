"""Regression guards for FIX3-external (AACT registered-vs-published magnitude).

Fast + deterministic: recompute the frozen external estimates from the committed
aact_kappa.json + class_lambda.json (pure arithmetic; no multi-GB AACT re-read) and
assert they match aact_kappa_frozen.json; plus a low-rep truth-gate cell asserting the
headline (external kappa_pooled WINS under real selection; funnel gate is blind at B=0).
Run: pytest transport_nma/test_aact_kappa.py -q
"""
import json, sys
import numpy as np
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def _frozen_from_json():
    K = json.load(open(HERE/"aact_kappa.json"))
    LAM = json.load(open(ROOT/"borrowing"/"class_lambda.json"))
    NMIN = 8
    rows = []
    for c, d in K.items():
        kmd = d.get("kappa_md")
        if kmd is None or min(d["pub"]["n"], d["reg"]["n"]) < NMIN:
            continue
        lam = LAM.get(c)
        if lam is None:
            continue
        rows.append((kmd, 1.0-lam, min(d["pub"]["n"], d["reg"]["n"])))
    kmds = np.array([r[0] for r in rows]); oml = np.array([r[1] for r in rows])
    w = np.array([r[2] for r in rows], float)
    kp = float(np.sum(w*np.maximum(0, kmds))/np.sum(w))
    ks = max(0.0, float(np.sum(w*oml*kmds)/np.sum(w*oml**2)))
    corr = float(np.corrcoef(oml, kmds)[0, 1])
    return kp, ks, corr


def test_frozen_estimates_reproduce():
    kp, ks, corr = _frozen_from_json()
    fr = json.load(open(HERE/"aact_kappa_frozen.json"))
    assert abs(kp - fr["kappa_pooled"]) < 1e-6, (kp, fr["kappa_pooled"])
    assert abs(ks - fr["kappa_slope"]) < 1e-6, (ks, fr["kappa_slope"])
    assert abs(corr - fr["corr_kmd_vs_1mlam"]) < 1e-6


def test_registry_model_supported_by_external_gap():
    # published-vs-registered gap grows with selection-severity (1-lambda): the external
    # signal that validates the registry model's structure (must stay clearly positive).
    _, _, corr = _frozen_from_json()
    assert corr > 0.3, corr


def test_pooled_magnitude_in_expected_band():
    fr = json.load(open(HERE/"aact_kappa_frozen.json"))
    assert 0.10 < fr["kappa_pooled"] < 0.25
    assert 0.15 < fr["kappa_slope"] < 0.40


def test_truthgate_headline_low_rep():
    sys.path.insert(0, str(HERE))
    import aact_kappa_truthgate as tg
    comps = tg.senn_contrasts()
    # under REAL selection (B=0.15) the FROZEN external kappa_pooled must WIN vs unadjusted...
    r = tg.run(comps, B=0.15, regime="A", reps=120, seed=7, boot=1500)
    assert r["rows"]["ext_pooled"]["verdict"] == "WINS", r["rows"]["ext_pooled"]
    # ...and beat the arbitrary fixed-0.5 baseline (which harms at low B)
    assert r["rows"]["ext_pooled"]["mciw0"] < r["rows"]["fixed0.5"]["mciw0"]
    # the funnel presence-gate is blind on this sparse network even under selection
    assert r["gate_fire_rate"] < 0.15, r["gate_fire_rate"]
    # at B=0 a fixed external correction over-corrects (documents the presence-gate boundary)
    r0 = tg.run(comps, B=0.0, regime="A", reps=120, seed=7, boot=1500)
    assert r0["rows"]["ext_pooled"]["dmciw0"] > 0
    assert r0["gate_fire_rate"] < 0.15
