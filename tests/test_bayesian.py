"""Tests for Bayesian UBCMA (Task 9). Skipped if PyMC is not installed.

Uses simplified=True (no quadrature normalizer) to avoid heavy computation
on systems without C compiler for PyTensor.
"""
from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from ubcma.data import MetaAnalysisDataset

try:
    from ubcma.bayesian import BayesianUBCMAFit
    HAS_PYMC = True
except ImportError:
    HAS_PYMC = False


# Minimal 8-study dataset (no quality/moderators/design) for fast MCMC
_MINI_DATA = None


def _make_mini_data():
    global _MINI_DATA
    if _MINI_DATA is None:
        rng = np.random.default_rng(7)
        n = 8
        df = pd.DataFrame({
            "study_id": [f"s{i}" for i in range(n)],
            "yi": rng.normal(0.3, 0.15, size=n),
            "sei": rng.uniform(0.05, 0.12, size=n),
        })
        _MINI_DATA = MetaAnalysisDataset.from_dataframe(df, study_id_col="study_id")
    return _MINI_DATA


# Cached fit result to avoid repeated MCMC
_FIT_RESULT = None


def _get_fit_result():
    global _FIT_RESULT
    if _FIT_RESULT is None:
        data = _make_mini_data()
        fitter = BayesianUBCMAFit()
        _FIT_RESULT = fitter.fit(
            data, chains=2, draws=100, tune=50, simplified=True
        )
    return _FIT_RESULT


@unittest.skipUnless(HAS_PYMC, "pymc not installed")
class BayesianModelBuildTests(unittest.TestCase):
    def test_model_builds(self) -> None:
        data = _make_mini_data()
        fitter = BayesianUBCMAFit()
        model = fitter.build_model(data, simplified=True)
        self.assertIsNotNone(model)

    def test_sampling_completes(self) -> None:
        result = _get_fit_result()
        self.assertIsNotNone(result.summary)

    def test_posterior_mu_reasonable(self) -> None:
        result = _get_fit_result()
        mu_mean = result.summary["mu"]["mean"]
        # Should be within 1.0 of 0.3 (generous for short chain on minimal data)
        self.assertAlmostEqual(mu_mean, 0.3, delta=1.0)

    def test_diagnostics_dict_keys(self) -> None:
        result = _get_fit_result()
        diag = result.diagnostics
        self.assertIn("max_rhat", diag)
        self.assertIn("min_ess_bulk", diag)
        self.assertIn("n_divergences", diag)

    def test_result_to_text(self) -> None:
        result = _get_fit_result()
        text = result.to_text()
        self.assertIn("mu", text)
        self.assertIn("tau", text)


@unittest.skipUnless(HAS_PYMC, "pymc not installed")
class PriorSensitivityTests(unittest.TestCase):
    def test_sensitivity_produces_three_results(self) -> None:
        data = _make_mini_data()
        fitter = BayesianUBCMAFit()
        results = fitter.prior_sensitivity(data, chains=2, draws=50, tune=25, simplified=True)
        self.assertEqual(len(results), 3)
        self.assertIn("informative", results)
        self.assertIn("weakly_informative", results)
        self.assertIn("diffuse", results)


if __name__ == "__main__":
    unittest.main()
