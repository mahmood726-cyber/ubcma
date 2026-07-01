"""Regression truth-gate for the real-Henmi-Copas bake-off.

Re-derives the headline result from the committed per-rep CSV (no re-simulation)
and asserts the verified, bootstrap-robust wins vs the REAL Henmi-Copas hold --
and, equally important, that the honest NEGATIVES hold (the standalone conformal
AdaptShrink does NOT beat HC; HC genuinely under-covers). If a future change to
the estimators or metric breaks these, this test fails loudly.

Run: PYTHONPATH=src python -m pytest truth-recovery/test_realhc.py -q
"""
import os
import sys

import pandas as pd
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, HERE)

import realhc_bakeoff as R  # noqa: E402

CSV = os.path.join(HERE, "realhc_strong_perrep.csv")
CSV_MOD = os.path.join(HERE, "realhc_moderate_perrep.csv")


def _score(path):
    raw = pd.read_csv(path)
    table = R.matched_coverage_table(raw, target=0.95)
    boot = {(b["mechanism"], b["method"]): b for b in R.bootstrap_vs_hc(raw, 0.95)}
    tbl = {(r["mechanism"], r["method"]): r for _, r in table.iterrows()}
    return raw, tbl, boot


@pytest.fixture(scope="module")
def scored():
    if not os.path.exists(CSV):
        pytest.skip("realhc_strong_perrep.csv not present")
    return _score(CSV)


@pytest.fixture(scope="module")
def scored_mod():
    if not os.path.exists(CSV_MOD):
        pytest.skip("realhc_moderate_perrep.csv not present")
    return _score(CSV_MOD)


def test_real_hc_undercovers(scored):
    _, tbl, _ = scored
    # The genuine Henmi-Copas badly under-covers the true mu under selection.
    for mech in ("smooth", "step", "copas"):
        assert tbl[(mech, "henmi_copas")]["raw_cov"] < 0.5


def test_adaptshrink_ensemble_robustly_beats_real_hc(scored):
    _, tbl, boot = scored
    # Robust (bootstrap 97.5% CI < 0) win on smooth AND step.
    for mech in ("smooth", "step"):
        b = boot[(mech, "adaptshrink_ens")]
        assert b["robust_win"], f"ens not robust on {mech}: {b}"
        assert tbl[(mech, "adaptshrink_ens")]["mciw0"] < tbl[(mech, "henmi_copas")]["mciw0"]


def test_adaptshrink_ensemble_covers_out_of_the_box(scored):
    _, tbl, _ = scored
    # Near-nominal DEPLOYABLE coverage where HC collapses (the Pareto win).
    for mech in ("smooth", "step", "copas"):
        assert tbl[(mech, "adaptshrink_ens")]["raw_cov"] >= 0.90


def test_ubcma_robustly_beats_real_hc_on_selection(scored):
    _, _, boot = scored
    for mech in ("step", "copas"):
        assert boot[(mech, "ubcma")]["robust_win"], f"ubcma not robust on {mech}"


def test_standalone_conformal_does_not_beat_hc(scored):
    # HONEST NEGATIVE: the standalone conformal AdaptShrink is NOT a robust
    # winner on any mechanism. If this ever flips, revisit the claims.
    _, _, boot = scored
    for mech in ("smooth", "step", "copas"):
        assert not boot[(mech, "adaptshrink_solo")]["robust_win"]


# --- Moderate-selection generalization + its honest boundary ---

def test_ensemble_win_generalizes_to_moderate(scored_mod):
    # The smooth/step robust win holds under moderate selection too.
    _, _, boot = scored_mod
    for mech in ("smooth", "step"):
        assert boot[(mech, "adaptshrink_ens")]["robust_win"], f"ens not robust on moderate {mech}"


def test_no_robust_win_on_copas_under_moderate(scored_mod):
    # HONEST BOUNDARY: under MILD (moderate) selection on the copas mechanism,
    # real HC's centre is only slightly biased and NO method robustly beats it.
    _, _, boot = scored_mod
    for method in ("adaptshrink_ens", "adaptshrink_solo", "ubcma"):
        assert not boot[("copas", method)]["robust_win"]
