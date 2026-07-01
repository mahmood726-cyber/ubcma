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
