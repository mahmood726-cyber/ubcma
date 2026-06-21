"""Tests for AdaptShrink-NMA components B (small-study) and C (inconsistency).

Deterministic parity / reduction checks are exact (1e-10); Monte-Carlo behaviour
checks use relaxed tolerances and fixed seeds (stochastic-test rule).
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "truth-recovery"))

from nma_core import fit_nma  # noqa: E402
from smallstudy_nma import network_smallstudy_league, network_asymmetry  # noqa: E402
import nma_sim as S  # noqa: E402


# ---------------------------------------------------------------- Component B

def test_smallstudy_no_covariate_reproduces_engine():
    """kind=None must reproduce the verified engine league exactly."""
    spec = S.NetSpec(geom="full", n=5, studies_per_comp=(3, 5),
                     hetero="heterogeneous", selection="none")
    comps, _, _ = S.generate(spec, seed=1)
    eng = fit_nma(comps, random=True)
    ss = network_smallstudy_league(comps, kind=None)
    assert np.max(np.abs(eng.TE - ss.TE)) < 1e-10
    assert np.max(np.abs(eng.seTE - ss.seTE)) < 1e-10


def test_smallstudy_league_reference_invariant():
    spec = S.NetSpec(geom="loop", n=6, studies_per_comp=(2, 4), selection="moderate")
    comps, _, _ = S.generate(spec, seed=3)
    l0 = network_smallstudy_league(comps, reference="0", kind="peese")
    l3 = network_smallstudy_league(comps, reference="3", kind="peese")
    assert np.max(np.abs(l0.TE - l3.TE)) < 1e-9


def test_asymmetry_null_calibration():
    """Under NO selection the Egger-type test should not over-fire (~nominal)."""
    spec = S.NetSpec(geom="full", n=5, studies_per_comp=(8, 15),
                     hetero="homogeneous", tau_homog=0.1, selection="none")
    ps = []
    for r in range(200):
        comps, _, _ = S.generate(spec, seed=6000 + r)
        if len({c.t1 for c in comps} | {c.t2 for c in comps}) < 5:
            continue
        ps.append(network_asymmetry(comps)["p"])
    # nominal 5% +/- Monte-Carlo slack
    assert np.mean(np.array(ps) < 0.05) < 0.12


def test_asymmetry_fires_and_peese_debiases_under_strong_selection():
    """Dense well-powered net + strong selection: test fires positive and PEESE
    reduces the common-DL downward bias on the basic contrasts."""
    spec = S.NetSpec(geom="full", n=5, studies_per_comp=(8, 15),
                     hetero="homogeneous", tau_homog=0.1, selection="strong")
    betas, bias_dl, bias_pe = [], [], []
    for r in range(250):
        comps, d_true, _ = S.generate(spec, seed=7000 + r)
        treats = sorted({c.t1 for c in comps} | {c.t2 for c in comps})
        if len(treats) < 5:
            continue
        a = network_asymmetry(comps)
        betas.append(a["beta"])
        dl = fit_nma(comps, random=True)
        pe = network_smallstudy_league(comps, kind="peese")
        tidx = dl.meta["tidx"]
        for t in range(1, 5):
            tl = str(t)
            bias_dl.append(dl.TE[tidx[tl], tidx["0"]] - d_true[t])
            bias_pe.append(pe.TE[tidx[tl], tidx["0"]] - d_true[t])
    assert np.mean(betas) > 0.1                     # positive small-study slope
    # PEESE materially reduces the magnitude of the (downward) bias
    assert abs(np.mean(bias_pe)) < abs(np.mean(bias_dl)) * 0.6
