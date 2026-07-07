"""Unit tests for the open-data sufficiency analysis math.

Run: python -m pytest test_sufficiency.py -q   (from regpub_pilot/sufficiency/)
"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "src"))

import analysis as A
from analysis import _fe, _z_after_missing, breakdown_fraction, weight_coverage, \
    actual_missing_ratio, reproduce, verdict
from reviews import Trial, Review, conclusion_label, is_poolable, _fullset_benchmark

Z = 1.959963985


def _mk_review(effects, poolflags, favorable=-1, scale="log"):
    """Build a synthetic review from (yi, vi) pairs + poolable flags."""
    trials = [Trial(label=f"t{i}", year=None, n=None, yi=y, vi=v, poolable=p)
              for i, ((y, v), p) in enumerate(zip(effects, poolflags))]
    pub = _fullset_benchmark(trials, favorable, cite="synthetic")
    return Review("syn", "synthetic", "test", "OR", scale, favorable=favorable,
                  trials=trials, published=pub, tier="coverage")


# ---- weight coverage ------------------------------------------------------
def test_full_coverage_when_all_poolable():
    r = _mk_review([(0.0, 0.1), (0.0, 0.2)], [True, True])
    cov = weight_coverage(r)
    assert abs(cov["cov_fixed"] - 1.0) < 1e-12
    assert abs(cov["cov_re"] - 1.0) < 1e-12
    assert cov["wf_missing"] == 0.0


def test_fixed_coverage_matches_manual():
    # one big trial (v=0.01 -> w=100) poolable, one small (v=1 -> w=1) missing
    r = _mk_review([(0.0, 0.01), (0.0, 1.0)], [True, False])
    cov = weight_coverage(r)
    assert abs(cov["cov_fixed"] - (100.0 / 101.0)) < 1e-9  # big trial dominates fixed weight


def test_re_coverage_below_fixed_when_big_trial_poolable():
    # heterogeneous set: big trial poolable; RE flattens weights so RE coverage < fixed
    effects = [(-0.7, 0.001)] + [(0.0, 0.05)] * 10   # 1 big (poolable) + 10 small (missing)
    poolflags = [True] + [False] * 10
    r = _mk_review(effects, poolflags)
    cov = weight_coverage(r)
    assert cov["cov_fixed"] > cov["cov_re"]  # the ISIS-4 phenomenon
    assert cov["cov_fixed"] > 0.8            # big trial dominates fixed weight (1000/1200)


# ---- breakdown fraction algebra ------------------------------------------
def test_z_after_missing_identity_at_zero():
    assert abs(_z_after_missing(3.0, 0.1, 0.0, 0.0) - 3.0) < 1e-12


def test_z_after_missing_dilution_monotone_decrease():
    zs = [_z_after_missing(3.0, 0.1, rho, 0.0) for rho in (0, 0.5, 1, 2, 5)]
    assert all(zs[i] > zs[i + 1] for i in range(len(zs) - 1))


def test_dilution_closed_form():
    # a significant subset (all poolable) -> r_dilute should equal (|z|/1.96)^2 - 1
    effects = [(-0.5, 0.02), (-0.5, 0.02), (-0.5, 0.02)]
    r = _mk_review(effects, [True, True, True])
    rep = reproduce(r)
    bf = breakdown_fraction(r, rep)
    fe = _fe([t.yi for t in r.trials], [t.vi for t in r.trials])
    expected = (abs(fe["z"]) / Z) ** 2 - 1.0
    assert abs(bf["r_dilute"] - expected) < 1e-6
    assert bf["r_dilute"] > 0


def test_manufacture_effect_for_null_subset():
    # a null subset -> breakdown scenario is 'manufacture-effect', r_star finite & > 0
    effects = [(0.0, 0.02), (0.02, 0.02)]
    r = _mk_review(effects, [True, True])
    rep = reproduce(r)
    assert rep["conclusion"] == "null"
    bf = breakdown_fraction(r, rep)
    assert bf["scenario"] == "manufacture-effect"
    assert bf["r_star"] > 0


# ---- actual missing ratio -------------------------------------------------
def test_actual_missing_ratio_fixed():
    r = _mk_review([(0.0, 0.01), (0.0, 1.0)], [True, False])
    # W_pool = 100, W_miss = 1 -> rho = 0.01
    assert abs(actual_missing_ratio(r, "fixed") - 0.01) < 1e-9


def test_zero_coverage_is_insufficient():
    r = _mk_review([(0.0, 0.1), (0.0, 0.2)], [False, False])
    v = verdict(r)
    assert v["verdict"] == "INSUFFICIENT"


# ---- verdict integration on a fragile vs robust synthetic -----------------
def test_robust_when_missing_weight_tiny():
    # strong signal across several poolable trials, tiny missing weight -> ROBUST.
    # (use k>=4 so the full-set house HKSJ isn't degenerate at t_1.)
    effects = [(-0.8, 0.02), (-0.75, 0.02), (-0.82, 0.02), (-0.78, 0.02)] + [(0.0, 50.0)]
    r = _mk_review(effects, [True, True, True, True, False], favorable=-1)
    v = verdict(r)
    assert v["rep"]["reproduced"]
    assert v["verdict"] == "ROBUST"


def test_fragile_when_missing_weight_large():
    # marginal signal, large missing weight -> FRAGILE
    effects = [(-0.35, 0.03)] + [(0.0, 0.02)] * 3  # marginal poolable + heavy missing
    r = _mk_review(effects, [True, False, False, False], favorable=-1)
    v = verdict(r)
    if v["rep"]["reproduced"]:
        assert v["verdict"] in ("FRAGILE", "ROBUST")
        # with 3x the missing weight and a marginal finding, must be fragile
        assert v["rho_fixed"] > 0
        assert v["verdict"] == "FRAGILE"


# ---- poolability rule -----------------------------------------------------
def test_poolability_rule():
    assert is_poolable(2010, 100) is True       # P1 registry era
    assert is_poolable(1990, 60000) is True      # P2 mega-trial
    assert is_poolable(1990, 100) is False       # neither
    assert is_poolable(None, 100) is False       # unknown year, small


# ---- conclusion polarity --------------------------------------------------
def test_conclusion_polarity():
    # favorable=-1: negative est significant -> benefit
    assert conclusion_label(-0.5, True, -1) == "benefit"
    assert conclusion_label(0.5, True, -1) == "harm"
    # favorable=+1: positive est significant -> benefit (e.g. response OR>1)
    assert conclusion_label(0.5, True, +1) == "benefit"
    assert conclusion_label(-0.5, True, +1) == "harm"
    assert conclusion_label(0.5, False, -1) == "null"


if __name__ == "__main__":
    import subprocess
    sys.exit(subprocess.call([sys.executable, "-m", "pytest", __file__, "-q"]))
