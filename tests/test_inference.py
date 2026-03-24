"""Tests for inference.py — profile likelihood and bootstrap CIs."""
from __future__ import annotations

import unittest
import warnings

import numpy as np
import pandas as pd

from ubcma.inference import bootstrap_ci, profile_likelihood_ci
from ubcma.data import MetaAnalysisDataset
from ubcma.model import UBCMAFit
from ubcma.simulation import generate_synthetic_meta_analysis


# ---------------------------------------------------------------------------
# Shared fixtures — cached at module level for speed
# ---------------------------------------------------------------------------
_TOY_RESULT = None
_TOY_DATA = None
_TOY_FITTER = None


def _fit_toy():
    """Full toy fixture with quality/moderators/design (slower, for profile tests)."""
    global _TOY_RESULT, _TOY_DATA, _TOY_FITTER
    if _TOY_RESULT is None:
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
        _TOY_RESULT, _TOY_DATA, _TOY_FITTER = result, data, fitter
    return _TOY_RESULT, _TOY_DATA, _TOY_FITTER


_MINI_RESULT = None
_MINI_DATA = None
_MINI_FITTER = None


def _fit_mini():
    """Minimal 8-study fixture with no extras (fast, for bootstrap tests)."""
    global _MINI_RESULT, _MINI_DATA, _MINI_FITTER
    if _MINI_RESULT is None:
        rng = np.random.default_rng(7)
        n = 8
        df = pd.DataFrame({
            "study_id": [f"s{i}" for i in range(n)],
            "yi": rng.normal(0.3, 0.15, size=n),
            "sei": rng.uniform(0.05, 0.12, size=n),
        })
        data = MetaAnalysisDataset.from_dataframe(df, study_id_col="study_id")
        fitter = UBCMAFit(n_restarts=0, maxiter=20)
        result = fitter.fit(data, allow_failed=True)
        _MINI_RESULT, _MINI_DATA, _MINI_FITTER = result, data, fitter
    return _MINI_RESULT, _MINI_DATA, _MINI_FITTER


# ---------------------------------------------------------------------------
# Profile likelihood tests — cached CI result to avoid repeated expensive calls
# ---------------------------------------------------------------------------
_PROFILE_CI_95 = None
_PROFILE_CI_80 = None


def _get_profile_ci_95():
    global _PROFILE_CI_95
    if _PROFILE_CI_95 is None:
        result, data, fitter = _fit_toy()
        _PROFILE_CI_95 = profile_likelihood_ci(result, data, fitter, alpha=0.05, n_points=5)
    return _PROFILE_CI_95


def _get_profile_ci_80():
    global _PROFILE_CI_80
    if _PROFILE_CI_80 is None:
        result, data, fitter = _fit_toy()
        _PROFILE_CI_80 = profile_likelihood_ci(result, data, fitter, alpha=0.20, n_points=0)
    return _PROFILE_CI_80


class ProfileLikelihoodTests(unittest.TestCase):

    def test_ci_contains_point_estimate(self):
        """CI must bracket the MLE mu estimate."""
        out = _get_profile_ci_95()
        self.assertLessEqual(out["ci_low"], out["mle_mu"] + 1e-9)
        self.assertGreaterEqual(out["ci_high"], out["mle_mu"] - 1e-9)

    def test_ci_finite_on_toy_data(self):
        """Both CI bounds must be finite floats (not NaN or ±inf)."""
        out = _get_profile_ci_95()
        self.assertTrue(np.isfinite(out["ci_low"]), f"ci_low not finite: {out['ci_low']}")
        self.assertTrue(np.isfinite(out["ci_high"]), f"ci_high not finite: {out['ci_high']}")

    def test_profile_curve_has_points(self):
        """profile_curve must have n_points entries with mu and objective keys."""
        out = _get_profile_ci_95()
        curve = out["profile_curve"]
        self.assertEqual(len(curve), 5)
        for entry in curve:
            self.assertIn("mu", entry)
            self.assertIn("objective", entry)

    def test_narrower_ci_with_lower_alpha(self):
        """A smaller alpha (larger confidence level) must yield a wider CI."""
        out_95 = _get_profile_ci_95()
        out_80 = _get_profile_ci_80()
        width_95 = out_95["ci_high"] - out_95["ci_low"]
        width_80 = out_80["ci_high"] - out_80["ci_low"]
        self.assertGreater(width_95, width_80,
                           f"95% CI ({width_95:.4f}) should be wider than 80% CI ({width_80:.4f})")

    def test_return_dict_has_required_keys(self):
        """Output dict must contain all documented keys."""
        out = _get_profile_ci_95()
        required = {"ci_low", "ci_high", "alpha", "mle_mu", "mle_objective", "threshold", "profile_curve"}
        for key in required:
            self.assertIn(key, out, f"Missing key: {key}")

    def test_mle_objective_matches_result_objective(self):
        """mle_objective should equal result.objective (to within tolerance)."""
        result, data, fitter = _fit_toy()
        out = _get_profile_ci_95()
        self.assertAlmostEqual(out["mle_objective"], result.objective, places=2)


# ---------------------------------------------------------------------------
# Bootstrap CI tests
# ---------------------------------------------------------------------------
class BootstrapCITests(unittest.TestCase):

    def test_percentile_ci_is_finite(self):
        """Percentile bootstrap CI bounds must be finite."""
        result, data, fitter = _fit_mini()
        out = bootstrap_ci(data, fitter, n_boot=20, alpha=0.05, method="percentile", seed=42)
        self.assertTrue(np.isfinite(out["ci_low"]), f"ci_low not finite: {out['ci_low']}")
        self.assertTrue(np.isfinite(out["ci_high"]), f"ci_high not finite: {out['ci_high']}")

    def test_percentile_ci_is_ordered(self):
        """ci_low <= ci_high always."""
        result, data, fitter = _fit_mini()
        out = bootstrap_ci(data, fitter, n_boot=20, alpha=0.05, method="percentile", seed=0)
        self.assertLessEqual(out["ci_low"], out["ci_high"])

    def test_bca_ci_is_ordered(self):
        """BCa ci_low <= ci_high always."""
        result, data, fitter = _fit_mini()
        out = bootstrap_ci(data, fitter, n_boot=20, alpha=0.05, method="bca", seed=7)
        self.assertLessEqual(out["ci_low"], out["ci_high"])

    def test_return_dict_has_required_keys(self):
        """Output dict must contain all documented keys."""
        result, data, fitter = _fit_mini()
        out = bootstrap_ci(data, fitter, n_boot=15, alpha=0.05, method="percentile", seed=1)
        required = {"ci_low", "ci_high", "alpha", "method", "n_boot", "n_failed", "n_succeeded", "distribution"}
        for key in required:
            self.assertIn(key, out, f"Missing key: {key}")

    def test_distribution_length(self):
        """distribution must have length == n_succeeded."""
        result, data, fitter = _fit_mini()
        out = bootstrap_ci(data, fitter, n_boot=15, alpha=0.05, method="percentile", seed=2)
        self.assertEqual(len(out["distribution"]), out["n_succeeded"])

    def test_method_stored(self):
        """Returned method must match the input method string."""
        result, data, fitter = _fit_mini()
        out = bootstrap_ci(data, fitter, n_boot=15, alpha=0.05, method="percentile", seed=3)
        self.assertEqual(out["method"], "percentile")

    def test_seed_reproducibility(self):
        """Same seed must yield identical CIs."""
        result, data, fitter = _fit_mini()
        out1 = bootstrap_ci(data, fitter, n_boot=15, alpha=0.05, method="percentile", seed=99)
        out2 = bootstrap_ci(data, fitter, n_boot=15, alpha=0.05, method="percentile", seed=99)
        self.assertAlmostEqual(out1["ci_low"], out2["ci_low"], places=10)
        self.assertAlmostEqual(out1["ci_high"], out2["ci_high"], places=10)

    def test_n_boot_stored(self):
        """n_boot in output must match input."""
        result, data, fitter = _fit_mini()
        out = bootstrap_ci(data, fitter, n_boot=10, alpha=0.05, method="percentile", seed=4)
        self.assertEqual(out["n_boot"], 10)

    def test_n_failed_plus_succeeded_equals_n_boot(self):
        """n_failed + n_succeeded == n_boot."""
        result, data, fitter = _fit_mini()
        out = bootstrap_ci(data, fitter, n_boot=15, alpha=0.05, method="percentile", seed=6)
        self.assertEqual(out["n_failed"] + out["n_succeeded"], out["n_boot"])


if __name__ == "__main__":
    unittest.main()
