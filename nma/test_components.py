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

from nma_core import fit_nma, p_score  # noqa: E402
from smallstudy_nma import network_smallstudy_league, network_asymmetry  # noqa: E402
from inconsistency_nma import q_decomposition, inconsistency_factor  # noqa: E402
from adaptshrink_nma import adaptshrink_nma_auto  # noqa: E402
import nma_sim as S  # noqa: E402

Z975 = 1.959963984540054


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


# ---------------------------------------------------------------- Component C

@pytest.mark.parametrize("geom,n,expected_loops", [
    ("star", 6, 0), ("line", 6, 0), ("loop", 6, 1), ("full", 5, 6)])
def test_df_inc_equals_independent_loops(geom, n, expected_loops):
    spec = S.NetSpec(geom=geom, n=n, studies_per_comp=(3, 4),
                     hetero="homogeneous", inconsistency=0.0)
    comps, _, _ = S.generate(spec, seed=1)
    d = q_decomposition(comps)
    assert d["df_inc"] == expected_loops
    assert abs(d["Q_total"] - (d["Q_het"] + d["Q_inc"])) < 1e-9 or d["Q_inc"] == 0.0


def test_inconsistency_null_calibration_no_overfire():
    """Consistent network with real heterogeneity must NOT be flagged inconsistent
    (RE-weighted decomposition: heterogeneity is not mistaken for inconsistency)."""
    spec = S.NetSpec(geom="full", n=5, studies_per_comp=(2, 4),
                     hetero="homogeneous", tau_homog=0.1, inconsistency=0.0)
    fired = []
    for r in range(300):
        comps, _, _ = S.generate(spec, seed=9000 + r)
        if len({c.t1 for c in comps} | {c.t2 for c in comps}) < 5:
            continue
        fired.append(inconsistency_factor(comps)["fired"])
    assert np.mean(fired) < 0.12          # ~nominal 0.10 gate, no over-firing


def test_inconsistency_inflation_restores_coverage():
    """Under design inconsistency, gated phi inflation improves deployable
    coverage of the basic contrasts over the un-inflated consistency model."""
    spec = S.NetSpec(geom="full", n=5, studies_per_comp=(2, 4),
                     hetero="homogeneous", tau_homog=0.1, inconsistency=0.30)
    cov_dl, cov_phi, phis = [], [], []
    for r in range(300):
        comps, d_true, _ = S.generate(spec, seed=9000 + r)
        if len({c.t1 for c in comps} | {c.t2 for c in comps}) < 5:
            continue
        phi = inconsistency_factor(comps)["phi"]
        phis.append(phi)
        fit = fit_nma(comps, random=True)
        tidx = fit.meta["tidx"]
        for t in range(1, 5):
            se = fit.seTE[tidx[str(t)], tidx["0"]]
            err = abs(d_true[t] - fit.TE[tidx[str(t)], tidx["0"]])
            cov_dl.append(err <= Z975 * se)
            cov_phi.append(err <= Z975 * phi * se)
    assert np.mean(phis) > 1.2                       # fires and inflates
    assert np.mean(cov_phi) > np.mean(cov_dl) + 0.05  # materially better coverage


# -------------------------------------------------------- Integrated A+B+C

def test_auto_does_no_harm_on_clean_network():
    """Clean, consistent, symmetric network: gates rarely fire and the auto
    estimator stays near the field default's deployable coverage."""
    spec = S.NetSpec(geom="full", n=5, studies_per_comp=(3, 5),
                     hetero="homogeneous", tau_homog=0.1,
                     selection="none", inconsistency=0.0)
    b_fire = c_fire = 0
    cov = []
    tot = 0
    for r in range(200):
        comps, d_true, _ = S.generate(spec, seed=100 + r)
        if len({c.t1 for c in comps} | {c.t2 for c in comps}) < 5:
            continue
        tot += 1
        au = adaptshrink_nma_auto(comps)
        b_fire += au.meta["b_fired"]
        c_fire += au.meta["c_fired"]
        tidx = au.meta["tidx"]
        for t in range(1, 5):
            se = au.seTE[tidx[str(t)], tidx["0"]]
            cov.append(abs(d_true[t] - au.TE[tidx[str(t)], tidx["0"]]) <= Z975 * se)
    assert b_fire / tot < 0.12 and c_fire / tot < 0.12      # ~nominal false fires
    assert np.mean(cov) > 0.90                              # no coverage damage
    # P-score still produces a valid ranking on the integrated league
    ps = p_score(au)
    assert len(ps) == 5 and all(0.0 <= v <= 1.0 for v in ps.values())


def test_auto_debiases_under_dense_strong_selection():
    """Integrated estimator reduces bias and improves coverage vs the field
    default in a dense well-powered net under strong selection (B's regime)."""
    spec = S.NetSpec(geom="full", n=6, studies_per_comp=(8, 15),
                     hetero="homogeneous", tau_homog=0.1, selection="strong")
    bias_dl, bias_au, cov_dl, cov_au = [], [], [], []
    for r in range(200):
        comps, d_true, _ = S.generate(spec, seed=10000 + r)
        if len({c.t1 for c in comps} | {c.t2 for c in comps}) < 6:
            continue
        dl = fit_nma(comps, random=True)
        au = adaptshrink_nma_auto(comps)
        td, ta = dl.meta["tidx"], au.meta["tidx"]
        for t in range(1, 6):
            tl = str(t)
            bias_dl.append(dl.TE[td[tl], td["0"]] - d_true[t])
            bias_au.append(au.TE[ta[tl], ta["0"]] - d_true[t])
            cov_dl.append(abs(dl.TE[td[tl], td["0"]] - d_true[t]) <= Z975 * dl.seTE[td[tl], td["0"]])
            cov_au.append(abs(au.TE[ta[tl], ta["0"]] - d_true[t]) <= Z975 * au.seTE[ta[tl], ta["0"]])
    assert abs(np.mean(bias_au)) < abs(np.mean(bias_dl)) * 0.75   # bias reduced
    assert np.mean(cov_au) > np.mean(cov_dl) + 0.03              # coverage improved
