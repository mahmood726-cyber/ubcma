"""Tests for API ergonomics — property access, ci(), to_dict, to_json."""
from __future__ import annotations

import json
import unittest

import numpy as np
import pandas as pd

from ubcma.data import MetaAnalysisDataset
from ubcma.model import UBCMAFit

# Minimal cached fixture
_RESULT = None
_DATA = None
_FITTER = None


def _get_result():
    global _RESULT, _DATA, _FITTER
    if _RESULT is None:
        rng = np.random.default_rng(7)
        n = 8
        df = pd.DataFrame({
            "study_id": [f"s{i}" for i in range(n)],
            "yi": rng.normal(0.3, 0.15, size=n),
            "sei": rng.uniform(0.05, 0.12, size=n),
        })
        _DATA = MetaAnalysisDataset.from_dataframe(df, study_id_col="study_id")
        _FITTER = UBCMAFit(n_restarts=0, maxiter=20)
        _RESULT = _FITTER.fit(_DATA, allow_failed=True)
    return _RESULT, _DATA, _FITTER


class PropertyTests(unittest.TestCase):
    def test_mu_property(self) -> None:
        result, _, _ = _get_result()
        self.assertEqual(result.mu, result.params["mu"])

    def test_tau1_property(self) -> None:
        result, _, _ = _get_result()
        self.assertEqual(result.tau1, result.params["tau1"])

    def test_tau2_property(self) -> None:
        result, _, _ = _get_result()
        self.assertEqual(result.tau2, result.params["tau2"])

    def test_mix_weight_property(self) -> None:
        result, _, _ = _get_result()
        self.assertEqual(result.mix_weight, result.params["mix_weight"])

    def test_fitter_stored(self) -> None:
        result, _, fitter = _get_result()
        self.assertIs(result.fitter, fitter)


class ToDictTests(unittest.TestCase):
    def test_to_dict_has_mu(self) -> None:
        result, _, _ = _get_result()
        d = result.to_dict()
        self.assertIn("mu", d)
        self.assertEqual(d["mu"], result.mu)

    def test_to_dict_has_tau(self) -> None:
        result, _, _ = _get_result()
        d = result.to_dict()
        self.assertIn("tau1", d)
        self.assertIn("tau2", d)

    def test_to_dict_serializable(self) -> None:
        result, _, _ = _get_result()
        d = result.to_dict()
        # Must be JSON-serializable (no numpy arrays)
        json_str = json.dumps(d)
        self.assertIsInstance(json_str, str)


class ToJsonTests(unittest.TestCase):
    def test_to_json_roundtrip(self) -> None:
        result, _, _ = _get_result()
        json_str = result.to_json()
        d = json.loads(json_str)
        self.assertAlmostEqual(d["mu"], result.mu, places=6)

    def test_to_json_to_file(self) -> None:
        import os
        import tempfile
        result, _, _ = _get_result()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "result.json")
            result.to_json(path=path)
            self.assertTrue(os.path.exists(path))
            with open(path) as f:
                d = json.load(f)
            self.assertIn("mu", d)


if __name__ == "__main__":
    unittest.main()
