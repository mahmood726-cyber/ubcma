"""Tests for ubcma.robust_methods: Henmi-Copas, AdaptShrink, conformal CI.

The Henmi-Copas test validates the Python port against reference CIs produced
by metafor::hc (truth-recovery/hc_reference.json). If that file is absent
(metafor / R not available in CI), the validation case is skipped but the
self-consistency and behavioural tests still run.
"""
import json
import os

import numpy as np
import pytest

from ubcma.robust_methods import (
    adaptshrink,
    adaptshrink_conformal,
    conformal_ci,
    fixed_effect,
    henmi_copas,
    random_effects,
)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HC_REF = os.path.join(ROOT, "truth-recovery", "hc_reference.json")


# ---------------------------------------------------------------------------
# Henmi-Copas
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not os.path.exists(HC_REF), reason="no metafor reference json")
def test_henmi_copas_matches_metafor():
    ds = json.load(open(HC_REF))
    max_err = 0.0
    for d in ds:
        yi = np.atleast_1d(np.asarray(d["yi"], float))
        se = np.sqrt(np.atleast_1d(np.asarray(d["vi"], float)))
        r = henmi_copas(yi, se, alpha=0.05)
        lb = float(np.atleast_1d(d["ci_lb"])[0])
        ub = float(np.atleast_1d(d["ci_ub"])[0])
        beta = float(np.atleast_1d(d["beta"])[0])
        max_err = max(max_err, abs(r["ci_low"] - lb), abs(r["ci_high"] - ub),
                      abs(r["mu"] - beta))
    assert max_err < 1e-6, f"HC port deviates from metafor::hc by {max_err:.2e}"


def test_henmi_copas_center_is_fixed_effect():
    rng = np.random.default_rng(0)
    se = rng.uniform(0.05, 0.3, 20)
    y = rng.normal(0.2, se)
    mu_fe, _ = fixed_effect(y, se)
    r = henmi_copas(y, se)
    assert abs(r["mu"] - mu_fe) < 1e-12
    assert r["ci_low"] < r["mu"] < r["ci_high"]


# ---------------------------------------------------------------------------
# AdaptShrink
# ---------------------------------------------------------------------------

def test_adaptshrink_no_asymmetry_reduces_to_re():
    # Symmetric, no selection: funnel asymmetry ~ 0 -> omega ~ 0 -> AS ~ RE.
    rng = np.random.default_rng(3)
    se = rng.uniform(0.05, 0.25, 40)
    y = rng.normal(0.2, se)
    a = adaptshrink(y, se)
    re = random_effects(y, se)
    assert a["omega"] < 0.25
    assert abs(a["mu"] - re["mu"]) < 0.05


def test_adaptshrink_pulls_toward_corrected_under_selection():
    # Construct upward small-study bias: omega should rise and AS should sit
    # between the (biased) RE mean and the (corrected) PET intercept.
    rng = np.random.default_rng(7)
    se = rng.uniform(0.05, 0.3, 50)
    y = rng.normal(0.2, se) + 0.8 * se  # small studies inflated => asymmetry
    a = adaptshrink(y, se)
    re = random_effects(y, se)
    assert a["omega"] > 0.3
    lo, hi = sorted([re["mu"], a["b0_pet"]])
    assert lo - 1e-9 <= a["mu"] <= hi + 1e-9
    assert a["b0_pet"] < re["mu"]  # correction is downward


def test_adaptshrink_deterministic():
    rng = np.random.default_rng(11)
    se = rng.uniform(0.05, 0.3, 25)
    y = rng.normal(0.2, se)
    assert adaptshrink(y, se)["mu"] == adaptshrink(y, se)["mu"]


# ---------------------------------------------------------------------------
# Conformal CI
# ---------------------------------------------------------------------------

def test_conformal_ci_ordered_and_finite():
    rng = np.random.default_rng(5)
    se = rng.uniform(0.05, 0.3, 20)
    y = rng.normal(0.2, se)
    c = adaptshrink_conformal(y, se)
    assert np.isfinite(c["ci_low"]) and np.isfinite(c["ci_high"])
    assert c["ci_low"] < c["mu"] < c["ci_high"]


def test_conformal_scale_widens_linearly():
    rng = np.random.default_rng(9)
    se = rng.uniform(0.05, 0.3, 18)
    y = rng.normal(0.2, se)
    point_fn = lambda yy, ss: random_effects(yy, ss)["mu"]
    c1 = conformal_ci(y, se, point_fn, scale=1.0)
    c2 = conformal_ci(y, se, point_fn, scale=2.0)
    w1 = c1["ci_high"] - c1["ci_low"]
    w2 = c2["ci_high"] - c2["ci_low"]
    assert abs(w2 - 2.0 * w1) < 1e-9
