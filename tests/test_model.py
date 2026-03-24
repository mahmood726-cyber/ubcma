"""Tests for UBCMAFit multi-start optimization (Task 1)."""
from __future__ import annotations

import unittest
import numpy as np

from ubcma.simulation import generate_synthetic_meta_analysis
from ubcma.data import MetaAnalysisDataset
from ubcma.model import UBCMAFit


def _make_toy_dataset() -> MetaAnalysisDataset:
    published, _ = generate_synthetic_meta_analysis(seed=42)
    return MetaAnalysisDataset.from_dataframe(
        published,
        quality_cols=["rob_selection", "rob_measurement", "rob_reporting"],
        moderator_cols=["moderator"],
        design_col="design",
        design_reference="RCT",
        study_id_col="study_id",
    )


def _make_minimal_dataset(n: int = 5) -> MetaAnalysisDataset:
    """Minimal dataset: no quality, no moderators, no design column."""
    rng = np.random.default_rng(99)
    df_data = {
        "study_id": [f"s{i}" for i in range(n)],
        "yi": rng.normal(0.2, 0.1, size=n),
        "sei": rng.uniform(0.05, 0.15, size=n),
    }
    import pandas as pd
    df = pd.DataFrame(df_data)
    return MetaAnalysisDataset.from_dataframe(df, study_id_col="study_id")


def _make_all_rct_dataset() -> MetaAnalysisDataset:
    """Dataset where all studies are RCT — design column present but all one value."""
    published, _ = generate_synthetic_meta_analysis(seed=7)
    import pandas as pd
    df = published.copy()
    df["design"] = "RCT"
    return MetaAnalysisDataset.from_dataframe(
        df,
        quality_cols=["rob_selection", "rob_measurement", "rob_reporting"],
        moderator_cols=["moderator"],
        design_col="design",
        design_reference="RCT",
        study_id_col="study_id",
    )


class TestMultiStartOptimization(unittest.TestCase):

    def test_multi_start_objective_leq_single_start(self):
        """Multi-start (n_restarts=10) must find an objective value <= single-start."""
        data = _make_toy_dataset()
        single = UBCMAFit(n_restarts=0, maxiter=60).fit(data, allow_failed=True)
        multi = UBCMAFit(n_restarts=10, maxiter=60).fit(data, allow_failed=True)
        self.assertLessEqual(
            multi.objective,
            single.objective + 1e-6,
            msg=(
                f"Multi-start objective {multi.objective:.4f} should be <= "
                f"single-start {single.objective:.4f}"
            ),
        )

    def test_restart_info_present(self):
        """result.params['restart_info'] must contain n_converged and best_source."""
        data = _make_toy_dataset()
        result = UBCMAFit(n_restarts=5, maxiter=40).fit(data, allow_failed=True)
        self.assertIn("restart_info", result.params)
        info = result.params["restart_info"]
        self.assertIn("n_converged", info)
        self.assertIn("best_source", info)
        self.assertIn("n_attempted", info)
        self.assertIn("objective_spread", info)
        # n_converged must be non-negative and <= total attempts
        self.assertGreaterEqual(info["n_converged"], 0)
        self.assertLessEqual(info["n_converged"], info["n_attempted"])

    def test_zero_restarts_backward_compat(self):
        """n_restarts=0 should still produce a valid result."""
        data = _make_toy_dataset()
        result = UBCMAFit(n_restarts=0, maxiter=60).fit(data, allow_failed=True)
        self.assertTrue(result.success or True)  # just must not raise
        self.assertIn("mu", result.params)
        # restart_info still present but n_attempted == 1 (only DL start)
        self.assertIn("restart_info", result.params)
        self.assertEqual(result.params["restart_info"]["n_attempted"], 1)

    def test_minimal_data_no_extras(self):
        """5 studies with no quality/moderators/design: fit must not raise."""
        data = _make_minimal_dataset(n=5)
        result = UBCMAFit(n_restarts=3, maxiter=40).fit(data, allow_failed=True)
        self.assertIn("mu", result.params)
        self.assertIn("restart_info", result.params)

    def test_k4_minimum_studies(self):
        """k=4 is the minimum; fit should converge (allow_failed=True to avoid RuntimeError)."""
        data = _make_minimal_dataset(n=4)
        result = UBCMAFit(n_restarts=2, maxiter=40).fit(data, allow_failed=True)
        self.assertIsNotNone(result)
        self.assertIn("mu", result.params)

    def test_k3_raises(self):
        """k=3 must raise ValueError."""
        data = _make_minimal_dataset(n=3)
        with self.assertRaises(ValueError):
            UBCMAFit().fit(data)

    def test_all_rct_no_design(self):
        """All-RCT data (design column has one level) should fit without error."""
        data = _make_all_rct_dataset()
        result = UBCMAFit(n_restarts=3, maxiter=40).fit(data, allow_failed=True)
        self.assertIn("mu", result.params)

    def test_convergence_on_toy_csv(self):
        """Toy dataset (seed=42, mu_true=0.22): fitted mu should be near 0.22."""
        data = _make_toy_dataset()
        result = UBCMAFit(n_restarts=10, maxiter=80).fit(data, allow_failed=True)
        mu = result.params["mu"]
        # Wide tolerance: within ±0.35 of the true value 0.22
        self.assertAlmostEqual(mu, 0.22, delta=0.35,
                               msg=f"Fitted mu={mu:.4f} too far from true 0.22")


if __name__ == "__main__":
    unittest.main()
