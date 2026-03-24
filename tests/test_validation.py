"""Validation tests against real-data examples (Task 6)."""
from __future__ import annotations

import unittest
from pathlib import Path

from ubcma.data import MetaAnalysisDataset
from ubcma.model import UBCMAFit, dersimonian_laird


EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


class VerdeValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        path = EXAMPLES / "verde_2021_aspirin.csv"
        if not path.exists():
            self.skipTest(f"Dataset not found: {path}")
        self.data = MetaAnalysisDataset.from_csv(
            path,
            quality_cols="rob_selection,rob_measurement,rob_reporting",
            study_id_col="study_id",
        )

    def test_dataset_loads(self) -> None:
        self.assertGreaterEqual(self.data.n_studies, 4)

    def test_dl_estimate_reasonable(self) -> None:
        dl = dersimonian_laird(self.data.y, self.data.se)
        # Aspirin reduces MI risk — pooled effect should be negative
        self.assertLess(dl["mu"], 0.1)

    def test_ubcma_converges(self) -> None:
        fitter = UBCMAFit(n_restarts=2, maxiter=30)
        result = fitter.fit(self.data, allow_failed=True)
        self.assertIsNotNone(result.params["mu"])


class BartosValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        path = EXAMPLES / "bartos_2022_anderson.csv"
        if not path.exists():
            self.skipTest(f"Dataset not found: {path}")
        self.data = MetaAnalysisDataset.from_csv(path, study_id_col="study_id")

    def test_dataset_loads(self) -> None:
        self.assertGreaterEqual(self.data.n_studies, 4)

    def test_ubcma_converges(self) -> None:
        fitter = UBCMAFit(n_restarts=2, maxiter=30)
        result = fitter.fit(self.data, allow_failed=True)
        self.assertIsNotNone(result.params["mu"])

    def test_ubcma_mu_positive(self) -> None:
        # Psychotherapy has positive effect
        fitter = UBCMAFit(n_restarts=2, maxiter=30)
        result = fitter.fit(self.data, allow_failed=True)
        self.assertGreater(result.params["mu"], 0.0)


if __name__ == "__main__":
    unittest.main()
