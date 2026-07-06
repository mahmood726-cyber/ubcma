"""Regression test for prep_transport covariate-join validation (P1-9).

The prep script used to write trials_transport.json BEFORE checking the
covariate join; a wholesale WB-obesity join failure left every pop_ob None, the
all-null file was persisted, and the summary then crashed on the empty list.
Downstream consumers (sim_transport / truthgate) filter `pop_ob is not None` and
crash on the empty result. Validation must happen before the write.

Run: PYTHONPATH=borrowing python -m pytest borrowing/test_prep_transport.py -q
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import prep_transport as P  # noqa: E402


def test_require_covariate_join_fails_closed_on_all_null():
    with pytest.raises(ValueError):
        P.require_covariate_join([{"pop_ob": None}, {"pop_ob": None}])


def test_require_covariate_join_passes_with_any_covariate():
    P.require_covariate_join([{"pop_ob": None}, {"pop_ob": 30.0}])  # no raise


def test_build_records_joins_covariates():
    trials = {"NCT1": {"active": "GLP1", "y": -1.0, "se": 0.1, "baseline": 7.5}}
    tc = {"NCT1": ["United States"]}
    recs = P._build_records(trials, tc, {"United States": 36.0},
                            {"United States": 10.0})
    assert recs[0]["pop_ob"] == 36.0
    assert recs[0]["single_country"] is True
    # and a build that joins nothing is caught by the guard
    empty = P._build_records(trials, {"NCT1": ["Nowhere"]}, {}, {})
    with pytest.raises(ValueError):
        P.require_covariate_join(empty)
