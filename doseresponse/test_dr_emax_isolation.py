"""Regression test: per-estimator isolation in dr_emax_bakeoff.fit_all_emax (P1-7).

The old single try/except around all estimators marked EVERY method
non-converged for a replicate whenever any one raised, silently shrinking each
method's analyzed sample. Each estimator must be isolated.

Run: PYTHONPATH=doseresponse:src python -m pytest doseresponse/test_dr_emax_isolation.py -q
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "src"))

import dr_emax_bakeoff as B  # noqa: E402


class _FakeFit:
    pass


def test_one_estimator_failure_does_not_tank_the_others(monkeypatch):
    monkeypatch.setattr(B, "_predict_at_dstar", lambda fit: (0.5, 0.1))
    monkeypatch.setattr(B.drma, "drma_two_stage", lambda df, **k: _FakeFit())

    def boom(df, **k):
        raise RuntimeError("one_stage broke")
    monkeypatch.setattr(B.drma, "drma_one_stage", boom)

    out = B.fit_all_emax(df=None)
    # the two_stage methods still recorded real, converged results
    assert out["two_stage_reml"][3] is True, out["two_stage_reml"]
    assert out["two_stage_fixed"][3] is True, out["two_stage_fixed"]
    # the failing estimator is isolated -> non-converged, not crashing the rest
    assert out["one_stage"][3] is False, out["one_stage"]
    # adaptshrink still aggregates over the members that fit
    assert out["adaptshrink"][3] is True, out["adaptshrink"]


def test_all_estimators_failing_yields_all_nonconverged(monkeypatch):
    def boom(df, **k):
        raise RuntimeError("broke")
    monkeypatch.setattr(B.drma, "drma_two_stage", boom)
    monkeypatch.setattr(B.drma, "drma_one_stage", boom)
    out = B.fit_all_emax(df=None)
    for m in B.METHODS:
        assert out[m][3] is False, (m, out[m])
