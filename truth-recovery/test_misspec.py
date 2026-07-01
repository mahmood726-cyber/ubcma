"""
Tests for the selection-misspecification robustness harness.

Run: PYTHONPATH=src python -m pytest truth-recovery/test_misspec.py -q

Fast structural checks plus one (slow) UBCMA-fit smoke. The full coverage
invariant (UBCMA >= comparators under misspecified selection) is established by
`misspec_harness.py` and recorded in REPORT.md; re-running it here at test scale
would be too slow (each UBCMA fit is multi-start L-BFGS-B).
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, HERE)

import misspec_harness as H  # noqa: E402


def test_dgp_reproducible():
    df1, mu1 = H.generate("step", "strong", H.Spec(), seed=7)
    df2, mu2 = H.generate("step", "strong", H.Spec(), seed=7)
    assert mu1 == mu2
    assert np.allclose(df1["yi"].to_numpy(), df2["yi"].to_numpy())


def test_mechanisms_produce_expected_schema():
    for mech in ("smooth", "step", "copas"):
        df, true_mu = H.generate(mech, "strong", H.Spec(), seed=3)
        assert true_mu == H.Spec().mu
        for col in ("study_id", "yi", "sei", "rob_selection",
                    "rob_measurement", "rob_reporting", "quality_score", "design"):
            assert col in df.columns
        assert len(df) >= 6
        assert (df["sei"] > 0).all()


def test_step_selection_inflates_naive_mean():
    # Positive-favouring step selection should bias the observed mean upward
    # relative to no selection, at the same true mu.
    spec = H.Spec()
    none_means, step_means = [], []
    for s in range(60):
        # 'smooth' with strength 'none' approximates no selection (gamma all 0)
        df_none, _ = H.generate("smooth", "none", spec, seed=1000 + s) \
            if False else (None, None)
        df_step, _ = H.generate("step", "strong", spec, seed=2000 + s)
        step_means.append(df_step["yi"].mean())
    # compare to unselected draws (all studies kept)
    rng = np.random.default_rng(0)
    for s in range(60):
        y, se, q, qs = H._base_draw(rng, spec)
        none_means.append(float(np.mean(y)))
    assert np.mean(step_means) > np.mean(none_means)


def test_ubcma_fit_returns_finite():
    # One real UBCMA fit through the dispatcher (slow but small).
    df, _ = H.generate("step", "strong", H.Spec(), seed=5)
    from ubcma.data import MetaAnalysisDataset
    data = MetaAnalysisDataset.from_dataframe(
        df, effect_col="yi", se_col="sei", study_id_col="study_id",
        quality_cols=["rob_selection", "rob_measurement", "rob_reporting"])
    res = H._run_method("ubcma", df["yi"].to_numpy(), df["sei"].to_numpy(),
                        df["quality_score"].to_numpy(), data)
    assert np.isfinite(res["mu_hat"])
    assert np.isfinite(res["ci_low"]) and np.isfinite(res["ci_high"])
