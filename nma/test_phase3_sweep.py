"""Phase-3 regression: the selection-regime MCIW0 win is a monotone network-size
effect. Locks in the committed sweep gate JSONs so the headline cannot silently
regress. See nma/REPORT_NMA_PHASE3.md.
"""
import json
from pathlib import Path

import pytest

SWEEP = Path(__file__).resolve().parent / "truth-recovery" / "sweep"
CELLS = [
    ("swp_select_strong_dense_gate.json", 5),
    ("swp_select_strong_dense_n6_gate.json", 6),
    ("swp_select_strong_dense_n7_gate.json", 7),
    ("swp_select_strong_dense_n8_gate.json", 8),
]


def _auto(cell_file):
    g = json.load(open(SWEEP / cell_file))
    for b in g["bootstrap_vs_baseline"]:
        if b["method"] == "adaptshrink_auto":
            return b
    raise AssertionError("adaptshrink_auto not in gate")


@pytest.fixture(scope="module")
def autos():
    return [(_auto(f), n) for f, n in CELLS]


def test_n5_is_not_a_robust_win(autos):
    """Honest negative: the smallest dense net has no efficiency win."""
    b5 = autos[0][0]
    assert b5["mciw0_robust_win"] is False
    assert b5["mciw0_diff"] > 0  # point estimate is the wrong sign at n=5


def test_robust_win_emerges_at_n6_and_holds(autos):
    for b, n in autos:
        if n >= 6:
            assert b["mciw0_robust_win"] is True, f"n={n} lost the robust win"
            assert b["mciw0_ci_hi"] < 0.0, f"n={n} CI upper not < 0"


def test_point_advantage_strengthens_monotonically(autos):
    diffs = [b["mciw0_diff"] for b, _ in autos]
    assert diffs == sorted(diffs, reverse=True), f"dMCIW0 not monotone ↓: {diffs}"
    assert diffs[-1] < diffs[0] - 0.04  # n8 at least 0.04 below n5


def test_ci_upper_bound_moves_monotonically_below_zero(autos):
    his = [b["mciw0_ci_hi"] for b, _ in autos]
    assert his == sorted(his, reverse=True), f"CI uppers not monotone ↓: {his}"


def _auto_for(cell_file):
    return _auto(cell_file)


def test_control_no_selection_is_not_a_win():
    """KEY falsification: with no selection the win must vanish (not an
    under-coverage artifact). dMCIW0 wrong-sign / CI above 0, coverage unharmed."""
    b = _auto_for("swp_select_none_dense_n8_gate.json")
    assert b["mciw0_robust_win"] is False
    assert b["mciw0_ci_lo"] > 0.0  # entire CI above zero: not narrower at all


def test_moderate_selection_not_robust_even_at_n8():
    """The efficiency win needs STRONG selection; large n does not rescue weak."""
    b = _auto_for("swp_select_moderate_dense_n8_gate.json")
    assert b["mciw0_robust_win"] is False


def test_win_strengthens_through_n10():
    b8 = _auto_for("swp_select_strong_dense_n8_gate.json")
    b10 = _auto_for("swp_select_strong_dense_n10_gate.json")
    assert b10["mciw0_robust_win"] is True
    assert b10["mciw0_diff"] < b8["mciw0_diff"]  # still strengthening, no plateau


def test_high_tau_amplifies_point_efficiency_win():
    b = _auto_for("swp_select_strong_dense_n8_hitau_gate.json")
    assert b["mciw0_robust_win"] is True
    assert b["mciw0_diff"] < -0.05  # larger than the low-tau n8 win


def test_ranking_preserved_no_degradation(autos):
    """P-score Spearman must not be degraded by the estimator (read from summary)."""
    import pandas as pd
    for f, n in CELLS:
        cell = f.replace("_gate.json", "")
        rk = pd.read_csv(SWEEP / f"{cell}_rank.csv").groupby("method").spearman.mean()
        assert rk["adaptshrink_auto"] >= rk["common_DL"] - 0.01, \
            f"n={n}: ranking degraded {rk['adaptshrink_auto']:.3f} vs {rk['common_DL']:.3f}"
