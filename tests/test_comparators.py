"""Tests for comparator methods (Tasks 11-12)."""
from __future__ import annotations

import unittest

import numpy as np

from ubcma.comparators import (
    reml_estimator,
    trim_and_fill,
    pet_peese,
    copas_selection,
    quality_effects,
)


# Homogeneous dataset (tau~0)
Y_HOMO = np.array([0.20, 0.22, 0.18, 0.21, 0.19, 0.23, 0.20, 0.17, 0.24, 0.21])
SE_HOMO = np.array([0.05, 0.06, 0.04, 0.05, 0.07, 0.05, 0.06, 0.04, 0.05, 0.06])

# Heterogeneous dataset
Y_HET = np.array([0.10, 0.30, 0.50, -0.10, 0.25, 0.40, 0.05, 0.35, 0.60, 0.15])
SE_HET = np.array([0.10, 0.08, 0.12, 0.15, 0.09, 0.11, 0.10, 0.07, 0.13, 0.10])


class REMLTests(unittest.TestCase):
    def test_returns_required_keys(self) -> None:
        r = reml_estimator(Y_HOMO, SE_HOMO)
        for key in ("mu", "se", "tau", "ci_low", "ci_high"):
            self.assertIn(key, r)

    def test_agrees_with_dl_on_homogeneous(self) -> None:
        from ubcma.model import dersimonian_laird
        dl = dersimonian_laird(Y_HOMO, SE_HOMO)
        reml = reml_estimator(Y_HOMO, SE_HOMO)
        self.assertAlmostEqual(dl["mu"], reml["mu"], delta=0.02)

    def test_tau_nonnegative(self) -> None:
        r = reml_estimator(Y_HOMO, SE_HOMO)
        self.assertGreaterEqual(r["tau"], 0.0)

    def test_ci_contains_mu(self) -> None:
        r = reml_estimator(Y_HET, SE_HET)
        self.assertLess(r["ci_low"], r["mu"])
        self.assertGreater(r["ci_high"], r["mu"])


class TrimAndFillTests(unittest.TestCase):
    def test_returns_required_keys(self) -> None:
        r = trim_and_fill(Y_HET, SE_HET)
        for key in ("mu", "se", "ci_low", "ci_high", "k_imputed", "k_total"):
            self.assertIn(key, r)

    def test_k_total_geq_k_original(self) -> None:
        r = trim_and_fill(Y_HET, SE_HET)
        self.assertGreaterEqual(r["k_total"], len(Y_HET))


class PETPEESETests(unittest.TestCase):
    def test_returns_required_keys(self) -> None:
        r = pet_peese(Y_HET, SE_HET)
        for key in ("mu", "se", "ci_low", "ci_high", "pet_p_value", "method_used"):
            self.assertIn(key, r)

    def test_method_is_pet_or_peese(self) -> None:
        r = pet_peese(Y_HET, SE_HET)
        self.assertIn(r["method_used"], ("PET", "PEESE"))


class CopasTests(unittest.TestCase):
    def test_returns_required_keys(self) -> None:
        r = copas_selection(Y_HET, SE_HET)
        for key in ("mu", "se", "ci_low", "ci_high", "sensitivity_range"):
            self.assertIn(key, r)

    def test_sensitivity_range_has_two_values(self) -> None:
        r = copas_selection(Y_HET, SE_HET)
        self.assertEqual(len(r["sensitivity_range"]), 2)


class QualityEffectsTests(unittest.TestCase):
    def test_returns_required_keys(self) -> None:
        q = np.array([0.2, 0.1, 0.4, 0.0, 0.3, 0.1, 0.2, 0.5, 0.0, 0.3])
        r = quality_effects(Y_HET, SE_HET, q)
        for key in ("mu", "se", "ci_low", "ci_high"):
            self.assertIn(key, r)

    def test_no_quality_falls_back_to_ivhet(self) -> None:
        r = quality_effects(Y_HET, SE_HET)
        self.assertIn("mu", r)


if __name__ == "__main__":
    unittest.main()
