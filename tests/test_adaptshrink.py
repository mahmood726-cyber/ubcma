"""Tests for the AdaptShrink robust-aggregation estimator.

Run: PYTHONPATH=src python -m pytest tests/test_adaptshrink.py -q
"""
import numpy as np
import pytest

from ubcma.adaptshrink import DEFAULT_MEMBERS, adaptshrink_estimator


def test_deterministic():
    pc = {"ubcma": (0.22, 0.035), "pet_peese": (0.26, 0.045),
          "trim_and_fill": (0.13, 0.03)}
    r1 = adaptshrink_estimator(np.array([0.2]), np.array([0.1]),
                               members=DEFAULT_MEMBERS, precomputed=pc)
    r2 = adaptshrink_estimator(np.array([0.2]), np.array([0.1]),
                               members=DEFAULT_MEMBERS, precomputed=pc)
    assert r1["mu"] == r2["mu"]
    assert r1["ci_low"] == r2["ci_low"] and r1["ci_high"] == r2["ci_high"]


def test_ci_ordering_and_weights():
    pc = {"ubcma": (0.22, 0.035), "pet_peese": (0.26, 0.045),
          "trim_and_fill": (0.13, 0.03)}
    r = adaptshrink_estimator(np.array([0.2]), np.array([0.1]),
                              members=DEFAULT_MEMBERS, precomputed=pc)
    assert r["converged"] and r["n_members"] == 3
    assert r["ci_low"] < r["mu"] < r["ci_high"]
    assert abs(sum(r["weights"].values()) - 1.0) < 1e-9
    # aggregate stays within the convex hull of the members
    assert min(m["mu"] for m in r["members"].values()) <= r["mu"]
    assert r["mu"] <= max(m["mu"] for m in r["members"].values())


def test_precomputed_zero_se_member_dominates_not_dropped():
    """Regression (P0-3): a precomputed member with se=0 (a claimed-exact
    estimate) must NOT be silently dropped. Inverse-variance logic says a more
    precise member gets MORE weight, so a near-exact member should DOMINATE the
    aggregate — not vanish, leaving only the noisy member (mu=0.0). The old code
    filtered `sem > 0`, discarding it and reporting converged with n_members=1.
    """
    r = adaptshrink_estimator(
        np.array([0.2, 0.3]), np.array([0.1, 0.1]),
        members=("exact", "noisy"),
        precomputed={"exact": (1.0, 0.0), "noisy": (0.0, 1.0)})
    assert r["converged"], r
    assert r["n_members"] == 2, r          # both members participate
    # The (near-)exact member dominates -> aggregate pulled strongly toward its
    # value (~0.83 for this 2-member panel), NOT the buggy 0.0 (noisy-only).
    assert r["mu"] > 0.75, r
    assert r["weights"]["exact"] > r["weights"]["noisy"], r["weights"]


def test_k1_computed_members_do_not_fabricate_a_panel():
    """Regression (P1-4): with a single study and no precomputed members, the
    pub-bias corrections (PET-PEESE, trim-and-fill) are NOT estimable, so the
    panel must be empty (fail closed) — not a fabricated converged panel. The
    >=2-valid-studies compute gate enforces this."""
    r = adaptshrink_estimator(np.array([1.0]), np.array([0.1]))
    assert r["converged"] is False, r
    assert r["n_members"] == 0, r


def test_degenerate_input_se_fails_closed_not_crash(recwarn):
    """Regression (P0-2): a study with se=0 in the input data must not crash the
    computed-member path (PET-PEESE weighted regression -> LinAlgError 'SVD did
    not converge'). The estimator must fail closed (NaN result) or drop the
    degenerate member, never raise."""
    # No precomputed members -> members are computed from (y, se); se has a zero.
    r = adaptshrink_estimator(np.array([0.2, 0.3]), np.array([0.0, 0.1]))
    # Must return a dict, not raise. Either a fail-closed NaN result, or a valid
    # aggregate from whatever members survived the degenerate input.
    assert isinstance(r, dict) and "mu" in r and "converged" in r, r


def test_disagreement_downweights_outlier():
    # An outlying member with the same SE must receive less weight than a member
    # that agrees with the consensus.
    pc = {"ubcma": (0.20, 0.04), "pet_peese": (0.21, 0.04),
          "trim_and_fill": (0.60, 0.04)}  # outlier
    r = adaptshrink_estimator(np.array([0.2]), np.array([0.1]),
                              members=DEFAULT_MEMBERS, precomputed=pc)
    assert r["weights"]["trim_and_fill"] < r["weights"]["ubcma"]
    assert r["weights"]["trim_and_fill"] < r["weights"]["pet_peese"]


def test_between_model_spread_widens_interval():
    # More member disagreement -> wider interval (model-uncertainty inflation).
    tight = {"ubcma": (0.20, 0.03), "pet_peese": (0.205, 0.03),
             "trim_and_fill": (0.195, 0.03)}
    wide = {"ubcma": (0.05, 0.03), "pet_peese": (0.20, 0.03),
            "trim_and_fill": (0.35, 0.03)}
    rt = adaptshrink_estimator(np.array([0.2]), np.array([0.1]),
                               members=DEFAULT_MEMBERS, precomputed=tight)
    rw = adaptshrink_estimator(np.array([0.2]), np.array([0.1]),
                               members=DEFAULT_MEMBERS, precomputed=wide)
    assert (rw["ci_high"] - rw["ci_low"]) > (rt["ci_high"] - rt["ci_low"])
    assert rw["between_var"] > rt["between_var"]


def test_kappa_scales_width_linearly():
    pc = {"ubcma": (0.22, 0.035), "pet_peese": (0.26, 0.045),
          "trim_and_fill": (0.13, 0.03)}
    r1 = adaptshrink_estimator(np.array([0.2]), np.array([0.1]),
                               members=DEFAULT_MEMBERS, precomputed=pc, kappa=1.0)
    r2 = adaptshrink_estimator(np.array([0.2]), np.array([0.1]),
                               members=DEFAULT_MEMBERS, precomputed=pc, kappa=2.0)
    w1 = r1["ci_high"] - r1["ci_low"]
    w2 = r2["ci_high"] - r2["ci_low"]
    assert abs(w2 - 2.0 * w1) < 1e-9
    assert r2["mu"] == r1["mu"]  # point estimate unchanged by kappa


def test_degenerate_inputs():
    # No usable members -> not converged, NaN estimates (never fabricated zeros).
    r = adaptshrink_estimator(np.array([]), np.array([]),
                              members=("ubcma",), precomputed={})
    assert r["converged"] is False
    assert np.isnan(r["mu"]) and np.isnan(r["ci_low"])
    # Single member -> normal critical value, finite CI.
    r1 = adaptshrink_estimator(np.array([0.2]), np.array([0.1]),
                               members=("pet_peese",),
                               precomputed={"pet_peese": (0.2, 0.05)})
    assert r1["converged"] and r1["n_members"] == 1
    assert np.isfinite(r1["ci_low"]) and np.isfinite(r1["ci_high"])


def test_computes_members_from_data_when_not_precomputed():
    # With no precomputed members, the cheap closed-form members are computed
    # from (y, se) directly.
    rng = np.random.default_rng(0)
    se = rng.uniform(0.05, 0.2, size=20)
    y = rng.normal(0.3, se)
    r = adaptshrink_estimator(y, se, members=("pet_peese", "trim_and_fill"))
    assert r["converged"] and r["n_members"] == 2
    assert np.isfinite(r["mu"])


def test_dispatcher_integration():
    # AdaptShrink is reachable as a first-class method via the simulation
    # dispatcher and reuses the (expensive) UBCMA member.
    import pandas as pd

    from ubcma.data import MetaAnalysisDataset
    from ubcma.simulation_study import _run_method

    rng = np.random.default_rng(1)
    k = 14
    se = rng.uniform(0.05, 0.2, size=k)
    y = rng.normal(0.25, se)
    df = pd.DataFrame({
        "study_id": [f"s{i}" for i in range(k)], "yi": y, "sei": se,
        "rob_selection": rng.integers(0, 2, k).astype(float),
        "rob_measurement": rng.integers(0, 2, k).astype(float),
        "rob_reporting": rng.integers(0, 2, k).astype(float),
    })
    df["quality_score"] = df[["rob_selection", "rob_measurement",
                              "rob_reporting"]].mean(axis=1)
    data = MetaAnalysisDataset.from_dataframe(
        df, effect_col="yi", se_col="sei", study_id_col="study_id",
        quality_cols=["rob_selection", "rob_measurement", "rob_reporting"])
    r = _run_method("adaptshrink", y, se, df["quality_score"].to_numpy(), data)
    assert r["converged"]
    assert np.isfinite(r["mu_hat"])
    assert r["ci_low"] < r["mu_hat"] < r["ci_high"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
