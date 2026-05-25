"""Tests for simulation study runner (Task 13)."""
from __future__ import annotations

import os
import tempfile
import unittest

import pandas as pd

from ubcma.simulation_study import ScenarioParams, compute_metrics, run_scenario


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


class TierTests(unittest.TestCase):
    def test_pilot_has_12_scenarios(self) -> None:
        from ubcma.simulation_study import pilot_scenarios
        self.assertEqual(len(pilot_scenarios()), 12)

    def test_focused_has_36_scenarios(self) -> None:
        from ubcma.simulation_study import focused_scenarios
        self.assertEqual(len(focused_scenarios()), 36)

    def test_full_has_324_scenarios(self) -> None:
        from ubcma.simulation_study import full_scenarios
        self.assertEqual(len(full_scenarios()), 324)

    def test_pilot_scenarios_are_scenarioparams(self) -> None:
        from ubcma.simulation_study import pilot_scenarios
        for s in pilot_scenarios():
            self.assertIsInstance(s, ScenarioParams)


class FormatTableTests(unittest.TestCase):
    def test_markdown_has_header_separator(self) -> None:
        from ubcma.simulation_study import format_table
        df = pd.DataFrame({
            "method": ["dl", "reml"],
            "bias": [0.01, 0.02],
            "rmse": [0.10, 0.11],
            "coverage": [0.95, 0.94],
            "interval_width": [0.40, 0.42],
            "convergence_rate": [1.0, 1.0],
        })
        md = format_table(df, fmt="markdown")
        self.assertIn("|", md)
        self.assertIn("---", md)

    def test_latex_has_tabular(self) -> None:
        from ubcma.simulation_study import format_table
        df = pd.DataFrame({
            "method": ["dl", "reml"],
            "bias": [0.01, 0.02],
            "rmse": [0.10, 0.11],
            "coverage": [0.95, 0.94],
            "interval_width": [0.40, 0.42],
            "convergence_rate": [1.0, 1.0],
        })
        tex = format_table(df, fmt="latex")
        self.assertIn("\\begin{tabular}", tex)
        self.assertIn("\\end{tabular}", tex)


if __name__ == "__main__":
    unittest.main()
