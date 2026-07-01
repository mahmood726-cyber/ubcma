"""pytest suite for the NMA engine + AdaptShrink-NMA.

Run: PYTHONPATH=nma python -m pytest nma/test_nma.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nma_core import Comparison, fit_nma, p_score  # noqa: E402
from adaptshrink_nma import adaptshrink_nma, compute_shrunk_tau2  # noqa: E402

REF = Path(__file__).resolve().parent / "reference"
TOL = 1e-6


def _comps(tag):
    df = pd.read_csv(REF / f"{tag}_input.csv")
    return [Comparison(str(r.studlab), str(r.treat1), str(r.treat2),
                       float(r.TE), float(r.seTE)) for r in df.itertuples()]


def _league(path):
    return pd.read_csv(path, index_col=0)


@pytest.mark.parametrize("tag", ["senn2013", "smoking"])
def test_engine_matches_netmeta_random(tag):
    scal = pd.read_csv(REF / f"{tag}_scalars.csv").iloc[0]
    comps = _comps(tag)
    fit = fit_nma(comps, random=True, tau2=float(scal.tau2))
    te_ref = _league(REF / f"{tag}_TE_random.csv")
    se_ref = _league(REF / f"{tag}_seTE_random.csv")
    tidx = fit.meta["tidx"]
    order = [tidx[t] for t in te_ref.columns]
    TE = fit.TE[np.ix_(order, order)]
    seTE = fit.seTE[np.ix_(order, order)]
    assert np.max(np.abs(TE - te_ref.to_numpy())) < TOL
    assert np.max(np.abs(seTE - se_ref.to_numpy())) < TOL


@pytest.mark.parametrize("tag", ["senn2013", "smoking"])
def test_dl_tau2_matches_netmeta(tag):
    scal = pd.read_csv(REF / f"{tag}_scalars.csv").iloc[0]
    fit = fit_nma(_comps(tag), random=True)
    assert abs(fit.tau2 - float(scal.tau2)) < 1e-6
    assert abs(fit.Q - float(scal.Q)) < 1e-5
    assert fit.df_Q == int(scal["df.Q"])


@pytest.mark.parametrize("tag", ["senn2013", "smoking"])
def test_pscore_matches_netmeta(tag):
    small = "desirable" if tag == "senn2013" else "undesirable"
    ps_ref = pd.read_csv(REF / f"{tag}_pscore.csv")
    ps = p_score(fit_nma(_comps(tag), random=True), small_values=small)
    ref = dict(zip(ps_ref["treat"].astype(str), ps_ref["Pscore.random"].astype(float)))
    assert max(abs(ps[t] - ref[t]) for t in ref) < 1e-6


def test_adaptshrink_limits():
    """nu->inf recovers common-tau^2; nu=0 recovers comparison-specific."""
    comps = _comps("smoking")
    common = fit_nma(comps, random=True)
    # large nu -> all lambda ~ 1 -> tau2_map ~ common everywhere -> league ~ common
    big = adaptshrink_nma(comps, nu=1e6)
    assert np.max(np.abs(big.TE - common.TE)) < 1e-3
    # nu=0 -> comparison-specific (differs from common when heterogeneity varies)
    cs = adaptshrink_nma(comps, nu=0.0)
    assert np.max(np.abs(cs.TE - common.TE)) > 1e-3


def test_adaptshrink_stabilizes_unstable_edge():
    """A 2-study edge with a wild direct tau^2 is shrunk toward common."""
    tmap, tcommon, detail = compute_shrunk_tau2(_comps("smoking"), nu=4.0,
                                                return_detail=True)
    ad = detail[frozenset(("A", "D"))]  # n=2, direct tau^2 ~ 4.5 (unstable)
    assert ad["n_c"] == 2
    assert ad["tau2_direct"] > 2.0
    assert ad["tau2_shrunk"] < ad["tau2_direct"]  # pulled in
    assert ad["lambda"] > 0.5                       # heavy shrink toward common


def test_multiarm_consistency_round_trip():
    """A clean 3-arm study with consistent contrasts reproduces its inputs."""
    # arm effects 0, 1, 2.5; equal SE; build the 3 consistent contrasts
    se = 0.2
    comps = [
        Comparison("s1", "A", "B", -1.0, np.sqrt(2) * se),
        Comparison("s1", "A", "C", -2.5, np.sqrt(2) * se),
        Comparison("s1", "B", "C", -1.5, np.sqrt(2) * se),
    ]
    fit = fit_nma(comps, random=False)
    tidx = fit.meta["tidx"]
    # single consistent study -> league reproduces the contrasts exactly
    assert abs(fit.TE[tidx["A"], tidx["B"]] - (-1.0)) < 1e-9
    assert abs(fit.TE[tidx["A"], tidx["C"]] - (-2.5)) < 1e-9
    assert abs(fit.TE[tidx["B"], tidx["C"]] - (-1.5)) < 1e-9
