"""Regression guard: AdaptShrink-NMA selection-robustness win holds across topologies (low-rep)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import topology_stress as ts


def test_win_holds_across_topologies_under_strong_selection():
    for topo in ("dense", "ladder", "star"):
        r = ts.run(topology=topo, B=1.0, reps=150, seed=7, boot=1500)
        assert r["dmciw0"] < 0, (topo, r["dmciw0"])          # AdaptShrink-NMA improves matched-coverage
        assert r["ci"][1] < 0, (topo, r["ci"])               # robust (97.5% CI upper < 0)


def test_inert_under_negligible_selection_dense():
    # safety property: near-zero small-study effect -> no manufactured win (tie, not a strong win)
    r = ts.run(topology="dense", B=0.02, reps=150, seed=7, boot=1500)
    assert r["dmciw0"] > -0.05, r["dmciw0"]
