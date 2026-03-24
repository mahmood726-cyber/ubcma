"""Tests for simulation study runner (Task 13)."""
from __future__ import annotations

import os
import tempfile
import unittest

import pandas as pd

from ubcma.simulation_study import ScenarioParams, run_scenario, compute_metrics


class ScenarioRunnerTests(unittest.TestCase):
    def test_single_scenario_runs(self) -> None:
        params = ScenarioParams(
            mu=0.2, tau=0.1, selection_strength="none",
            quality_bias="none", k=10, design_mix="all_rct",
        )
        df = run_scenario(params, methods=["dl", "reml"], n_reps=2, seed=42)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)

    def test_output_has_required_columns(self) -> None:
        params = ScenarioParams(
            mu=0.2, tau=0.1, selection_strength="none",
            quality_bias="none", k=10, design_mix="all_rct",
        )
        df = run_scenario(params, methods=["dl"], n_reps=2, seed=42)
        for col in ("method", "mu_hat", "ci_low", "ci_high", "true_mu", "replicate"):
            self.assertIn(col, df.columns)

    def test_metrics_computation(self) -> None:
        df = pd.DataFrame({
            "method": ["dl", "dl", "dl"],
            "mu_hat": [0.22, 0.18, 0.25],
            "ci_low": [0.10, 0.06, 0.13],
            "ci_high": [0.34, 0.30, 0.37],
            "true_mu": [0.20, 0.20, 0.20],
            "converged": [True, True, True],
        })
        m = compute_metrics(df)
        self.assertIn("bias", m.columns)
        self.assertIn("rmse", m.columns)
        self.assertIn("coverage", m.columns)

    def test_checkpointing(self) -> None:
        params = ScenarioParams(
            mu=0.0, tau=0.0, selection_strength="none",
            quality_bias="none", k=10, design_mix="all_rct",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "checkpoint.csv")
            df = run_scenario(params, methods=["dl"], n_reps=3, seed=42, checkpoint_path=path)
            self.assertTrue(os.path.exists(path))
            df2 = pd.read_csv(path)
            self.assertEqual(len(df), len(df2))


if __name__ == "__main__":
    unittest.main()
