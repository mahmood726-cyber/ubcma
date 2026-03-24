from __future__ import annotations

import unittest

import pandas as pd

from ubcma.data import MetaAnalysisDataset
from ubcma.simulation import generate_synthetic_meta_analysis


class DataLoadingTests(unittest.TestCase):
    def test_quality_score_is_not_inferred_as_extra_domain(self) -> None:
        df = pd.DataFrame(
            {
                "yi": [0.2, 0.3, 0.1, 0.4],
                "sei": [0.1, 0.1, 0.12, 0.11],
                "rob_selection": [1, 0, 1, 0],
                "rob_reporting": [0, 1, 0, 1],
                "quality_score": [0.5, 0.5, 0.5, 0.5],
            }
        )
        data = MetaAnalysisDataset.from_dataframe(df)
        self.assertEqual(data.quality_names, ["rob_selection", "rob_reporting"])
        self.assertEqual(data.quality.shape[1], 2)

    def test_missing_explicit_design_column_raises(self) -> None:
        df = pd.DataFrame(
            {
                "yi": [0.2, 0.3, 0.1, 0.4],
                "sei": [0.1, 0.1, 0.12, 0.11],
            }
        )
        with self.assertRaisesRegex(ValueError, "Missing design column"):
            MetaAnalysisDataset.from_dataframe(df, design_col="design")

    def test_design_reference_controls_dummy_encoding(self) -> None:
        df = pd.DataFrame(
            {
                "yi": [0.2, 0.3, 0.1, 0.4],
                "sei": [0.1, 0.1, 0.12, 0.11],
                "design": ["RCT", "OBS", "RCT", "OBS"],
            }
        )
        data = MetaAnalysisDataset.from_dataframe(
            df,
            design_col="design",
            design_reference="RCT",
        )
        self.assertEqual(data.design_names, ["design_OBS"])

    def test_design_reference_is_required_for_multiple_design_levels(self) -> None:
        df = pd.DataFrame(
            {
                "yi": [0.2, 0.3, 0.1, 0.4],
                "sei": [0.1, 0.1, 0.12, 0.11],
                "design": ["RCT", "OBS", "RCT", "OBS"],
            }
        )
        with self.assertRaisesRegex(ValueError, "design_reference is required"):
            MetaAnalysisDataset.from_dataframe(df, design_col="design")

    def test_moderators_are_centered_and_reference_values_are_kept(self) -> None:
        df = pd.DataFrame(
            {
                "yi": [0.2, 0.3, 0.1, 0.4],
                "sei": [0.1, 0.1, 0.12, 0.11],
                "dose": [10.0, 20.0, 30.0, 40.0],
            }
        )
        data = MetaAnalysisDataset.from_dataframe(df, moderator_cols=["dose"])
        self.assertListEqual(data.moderator_reference_values.tolist(), [25.0])
        self.assertAlmostEqual(float(data.moderators.mean()), 0.0, places=8)

    def test_summary_quality_score_is_preserved_when_domains_are_absent(self) -> None:
        df = pd.DataFrame(
            {
                "yi": [0.2, 0.3, 0.1, 0.4],
                "sei": [0.1, 0.1, 0.12, 0.11],
                "quality_score": [0.2, 0.4, 0.6, 0.8],
            }
        )
        data = MetaAnalysisDataset.from_dataframe(df)
        self.assertEqual(data.quality.shape[1], 0)
        self.assertListEqual(data.quality_score.tolist(), [0.2, 0.4, 0.6, 0.8])


class SimulationTests(unittest.TestCase):
    def test_simulation_returns_observed_columns_only(self) -> None:
        published, full = generate_synthetic_meta_analysis(seed=42)
        self.assertIn("true_effect", full.columns)
        self.assertNotIn("true_effect", published.columns)
        self.assertNotIn("internal_bias", published.columns)
        self.assertNotIn("selection_probability", published.columns)
        self.assertNotIn("selected", published.columns)


if __name__ == "__main__":
    unittest.main()
