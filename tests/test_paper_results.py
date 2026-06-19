"""Regression guard: the committed canonical results must match the manuscript.

These tests read the version-controlled tables in ``paper/results/`` (produced by
``scripts/reproduce_paper_results.py`` at seed 42) and assert that the headline
numbers reported in the published manuscript (Tables 1 and 3) are reproducible
from committed files. This is the contract that closes the "headline numbers are
not reproducible from the repo" integrity gap: if anyone regenerates the tables
and the numbers drift past Monte-Carlo tolerance, this test fails.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

RESULTS = Path(__file__).resolve().parents[1] / "paper" / "results"
SUMMARY = RESULTS / "pilot_summary.csv"
BY_BIAS = RESULTS / "pilot_by_quality_bias.csv"

# Published manuscript values (Tables 1 and 3) and the tolerance we accept.
# 50 reps per scenario => coverage SE ~ sqrt(.5*.5/600) ~ 0.02 overall; we use a
# generous absolute tolerance that still catches a real regression.
TOL = 0.02

pytestmark = pytest.mark.skipif(
    not SUMMARY.exists() or not BY_BIAS.exists(),
    reason="canonical paper/results tables not present; run scripts/reproduce_paper_results.py",
)


def _val(df: pd.DataFrame, method: str, col: str) -> float:
    return float(df.loc[df["method"] == method, col].iloc[0])


def test_overall_headline_matches_manuscript():
    s = pd.read_csv(SUMMARY)
    # Table 1
    assert _val(s, "ubcma", "rmse") == pytest.approx(0.070, abs=TOL)
    assert _val(s, "ubcma", "coverage") == pytest.approx(0.888, abs=TOL)
    assert _val(s, "dl", "coverage") == pytest.approx(0.597, abs=TOL)
    assert _val(s, "reml_hksj", "coverage") == pytest.approx(0.638, abs=TOL)
    assert _val(s, "trim_and_fill", "coverage") == pytest.approx(0.390, abs=TOL)
    # UBCMA's unambiguous advantage is COVERAGE: it has the highest of all methods.
    assert _val(s, "ubcma", "coverage") == s["coverage"].max()
    # NOTE: UBCMA does not have the strictly lowest RMSE -- quality_effects edges it
    # out (~0.067 vs ~0.070) at the cost of badly undercovered intervals (~62%).
    # This matches manuscript Table 1; the repo wording leads with the coverage win.
    assert _val(s, "quality_effects", "rmse") == pytest.approx(0.067, abs=TOL)
    assert _val(s, "quality_effects", "rmse") < _val(s, "ubcma", "rmse")


def test_worst_case_quality_bias_matches_manuscript():
    b = pd.read_csv(BY_BIAS)
    mod = b[b["quality_bias"] == "moderate"]
    # Table 3: under moderate quality bias UBCMA holds coverage while DL collapses.
    assert _val(mod, "ubcma", "coverage") == pytest.approx(0.903, abs=TOL)
    assert _val(mod, "dl", "coverage") == pytest.approx(0.313, abs=TOL)


def test_eight_comparators_present():
    s = pd.read_csv(SUMMARY)
    comparators = {
        "dl", "dl_hksj", "reml", "reml_hksj",
        "trim_and_fill", "pet_peese", "copas", "quality_effects",
    }
    methods = set(s["method"])
    assert comparators.issubset(methods)
    assert "ubcma" in methods
    assert len(comparators) == 8
