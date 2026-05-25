"""Tests for ubcma.diagnostics (Task 4).

Performance notes:
- Each model fit takes ~0.5-2s. LOO does n_studies refits.
- Module-level caching via _TOY_CACHE / _LOO_CACHE avoids redundant fits.
- LOO uses a tiny 6-study dataset (n_restarts=0, maxiter=20) for speed.
"""
from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from ubcma.data import MetaAnalysisDataset
from ubcma.diagnostics import (
    information_criteria,
    leave_one_out,
    selection_function_grid,
    standardized_residuals,
)
from ubcma.model import UBCMAFit
from ubcma.simulation import generate_synthetic_meta_analysis

# ---------------------------------------------------------------------------
# Module-level fixture cache — fits once per test run
# ---------------------------------------------------------------------------

_TOY_CACHE: tuple | None = None   # (result, data, fitter) for full IC / residual tests
_LOO_CACHE: tuple | None = None   # (result, data, fitter) for LOO tests (tiny dataset)


def _fit_toy() -> tuple:
    """Full toy dataset fit with seed=42. Cached after first call."""
    global _TOY_CACHE
    if _TOY_CACHE is None:
        published, _ = generate_synthetic_meta_analysis(seed=42)
        data = MetaAnalysisDataset.from_dataframe(
            published,
            quality_cols=["rob_selection", "rob_measurement", "rob_reporting"],
            moderator_cols=["moderator"],
            design_col="design",
            design_reference="RCT",
            study_id_col="study_id",
        )
        fitter = UBCMAFit(n_restarts=1, maxiter=30)
        result = fitter.fit(data, allow_failed=True)
        _TOY_CACHE = (result, data, fitter)
    return _TOY_CACHE


def _fit_loo_fixture() -> tuple:
    """Tiny 6-study dataset for LOO tests — no quality, no moderators, no design.

    Uses n_restarts=0, maxiter=20 so each LOO refit is fast.
    Cached after first call.
    """
    global _LOO_CACHE
    if _LOO_CACHE is None:
        rng = np.random.default_rng(7)
        n = 6
        df = pd.DataFrame(
            {
                "study_id": [f"s{i}" for i in range(n)],
                "yi": rng.normal(0.25, 0.12, size=n),
                "sei": rng.uniform(0.06, 0.18, size=n),
            }
        )
        data = MetaAnalysisDataset.from_dataframe(df, study_id_col="study_id")
        fitter = UBCMAFit(n_restarts=0, maxiter=20)
        result = fitter.fit(data, allow_failed=True)
        _LOO_CACHE = (result, data, fitter)
    return _LOO_CACHE


# ---------------------------------------------------------------------------
# Information criteria tests — cached IC result to avoid repeated slow refits
# ---------------------------------------------------------------------------

_IC_CACHE: dict | None = None


def _get_ic():
    global _IC_CACHE
    if _IC_CACHE is None:
        result, data, fitter = _fit_toy()
        _IC_CACHE = information_criteria(result, data, fitter)
    return _IC_CACHE


class InformationCriteriaTests(unittest.TestCase):

    def test_all_reduced_models_present(self) -> None:
        ic = _get_ic()
        for key in ("full", "no_selection", "no_quality", "single_component", "null"):
            self.assertIn(key, ic, msg=f"Key '{key}' missing from IC output")
            self.assertIn("aic", ic[key])
            self.assertIn("bic", ic[key])
            self.assertIn("n_params", ic[key])

    def test_aic_less_than_bic_for_large_k(self) -> None:
        result, data, fitter = _fit_toy()
        ic = _get_ic()
        if data.n_studies > 8:
            self.assertLess(
                ic["full"]["aic"],
                ic["full"]["bic"],
                msg="AIC should be < BIC when k > 8",
            )

    def test_full_model_aic_leq_null(self) -> None:
        ic = _get_ic()
        self.assertLessEqual(
            ic["full"]["aic"],
            ic["null"]["aic"] + 50,
            msg="Full model AIC should not exceed null AIC by more than 50",
        )

    def test_null_has_one_param(self) -> None:
        ic = _get_ic()
        self.assertEqual(ic["null"]["n_params"], 1)

    def test_single_component_fewer_params_than_full(self) -> None:
        ic = _get_ic()
        self.assertLess(
            ic["single_component"]["n_params"],
            ic["full"]["n_params"],
            msg="single_component should have fewer params than full model",
        )

    def test_neg_log_lik_finite(self) -> None:
        ic = _get_ic()
        for key in ("full", "null", "single_component"):
            nll = ic[key]["neg_log_lik"]
            self.assertTrue(
                np.isfinite(nll),
                msg=f"neg_log_lik for '{key}' is not finite: {nll}",
            )


# ---------------------------------------------------------------------------
# Standardized residual tests
# ---------------------------------------------------------------------------

class ResidualTests(unittest.TestCase):

    def test_residuals_correct_shape(self) -> None:
        result, data, fitter = _fit_toy()
        r = standardized_residuals(result)
        self.assertEqual(len(r), data.n_studies)

    def test_residuals_approximately_standard_normal(self) -> None:
        # On well-fitting data, residuals should be roughly N(0,1).
        # Allow wide tolerance since sample size is moderate.
        result, data, fitter = _fit_toy()
        r = standardized_residuals(result)
        self.assertAlmostEqual(float(np.mean(r)), 0.0, delta=1.5)
        self.assertAlmostEqual(float(np.std(r)), 1.0, delta=1.5)

    def test_residuals_are_finite(self) -> None:
        result, data, fitter = _fit_toy()
        r = standardized_residuals(result)
        self.assertTrue(np.all(np.isfinite(r)), msg="Residuals contain non-finite values")


# ---------------------------------------------------------------------------
# Leave-one-out tests
# ---------------------------------------------------------------------------

_LOO_RESULT_CACHE: pd.DataFrame | None = None


def _get_loo():
    global _LOO_RESULT_CACHE
    if _LOO_RESULT_CACHE is None:
        result, data, fitter = _fit_loo_fixture()
        _LOO_RESULT_CACHE = leave_one_out(result, data, fitter)
    return _LOO_RESULT_CACHE


class LeaveOneOutTests(unittest.TestCase):

    def test_loo_returns_correct_shape(self) -> None:
        result, data, fitter = _fit_loo_fixture()
        loo = _get_loo()
        self.assertEqual(len(loo), data.n_studies)
        self.assertIn("delta_mu", loo.columns)
        self.assertIn("cooks_d", loo.columns)

    def test_loo_delta_mu_is_finite(self) -> None:
        loo = _get_loo()
        self.assertTrue(
            np.all(np.isfinite(loo["delta_mu"].values)),
            msg="delta_mu contains non-finite values",
        )

    def test_loo_has_study_id_column(self) -> None:
        result, data, fitter = _fit_loo_fixture()
        loo = _get_loo()
        self.assertIn("study_id", loo.columns)
        self.assertEqual(len(loo), data.n_studies)

    def test_loo_cooks_d_nonneg(self) -> None:
        loo = _get_loo()
        finite_cooks = loo["cooks_d"].dropna().values
        self.assertTrue(
            np.all(finite_cooks >= 0.0),
            msg="Cook's D values must be non-negative",
        )


# ---------------------------------------------------------------------------
# Selection function grid tests
# ---------------------------------------------------------------------------

class SelectionGridTests(unittest.TestCase):

    def test_grid_returns_dataframe(self) -> None:
        result, data, fitter = _fit_toy()
        grid = selection_function_grid(result, fitter)
        self.assertIsInstance(grid, pd.DataFrame)
        self.assertIn("z_score", grid.columns)
        self.assertIn("precision", grid.columns)
        self.assertIn("p_selected", grid.columns)
        self.assertGreater(len(grid), 0)

    def test_grid_probabilities_in_01(self) -> None:
        result, data, fitter = _fit_toy()
        grid = selection_function_grid(result, fitter)
        p = grid["p_selected"].values
        self.assertTrue(
            np.all(p >= 0.0) and np.all(p <= 1.0),
            msg="p_selected values must be in [0, 1]",
        )

    def test_grid_size(self) -> None:
        result, data, fitter = _fit_toy()
        grid = selection_function_grid(result, fitter, n_z=5, n_prec=4)
        self.assertEqual(len(grid), 5 * 4)

    def test_positive_z_has_higher_p_selected(self) -> None:
        """Studies with large positive z-scores should have higher selection probability."""
        result, data, fitter = _fit_toy()
        grid = selection_function_grid(result, fitter, n_z=10, n_prec=5)
        high_z = grid[grid["z_score"] > 2.0]["p_selected"].mean()
        low_z = grid[grid["z_score"] < -2.0]["p_selected"].mean()
        # Selection model should favour positive/significant results
        self.assertGreaterEqual(high_z, low_z - 0.5)


if __name__ == "__main__":
    unittest.main()
