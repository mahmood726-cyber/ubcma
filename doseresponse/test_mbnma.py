"""test_mbnma.py -- validate the model-based dose-response NMA engine.

  * saturated reduction: fit_mbnma(model='nma') common-effect == R netmeta
    common-effect treatment effects vs reference (~1e-9). External anchor:
    reference/mbnma_gold.json (built by reference/mbnma_gold.R).
  * parameter recovery: linear & Emax truth recovered on simulated networks.

Run: PYTHONPATH=doseresponse python -m pytest doseresponse/test_mbnma.py -q
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

import mbnma
import sim_network as sn

REF = Path(__file__).resolve().parent / "reference"


def _load_contrasts(csv):
    import csv as _c
    rows = []
    with open(csv) as f:
        for r in _c.DictReader(f):
            rows.append((r["studlab"], r["treat1"], r["treat2"],
                         float(r["TE"]), float(r["seTE"])))
    return rows


def test_saturated_equals_netmeta():
    gold = json.load(open(REF / "mbnma_gold.json"))
    contrasts = _load_contrasts(REF / "mbnma_contrasts.csv")
    fit = mbnma.fit_mbnma(contrasts, ref="plac@0", parse=sn.parse_node,
                          model="nma", random=False)
    pos = {t: i for i, t in enumerate(fit.treatments)}
    diffs = []
    for t, te in zip(gold["treatments"], gold["te_vs_ref"]):
        diffs.append(abs(fit.delta[pos[t]] - te))
    assert max(diffs) < 1e-9, max(diffs)


def test_saturated_se_equals_netmeta():
    gold = json.load(open(REF / "mbnma_gold.json"))
    contrasts = _load_contrasts(REF / "mbnma_contrasts.csv")
    fit = mbnma.fit_mbnma(contrasts, ref="plac@0", parse=sn.parse_node,
                          model="nma", random=False)
    pos = {t: i for i, t in enumerate(fit.treatments)}
    diffs = []
    for t, se in zip(gold["treatments"], gold["se_vs_ref"]):
        if t == "plac@0":
            continue
        diffs.append(abs(fit.delta_se[pos[t]] - se))
    assert max(diffs) < 1e-8, max(diffs)


def test_linear_recovery():
    """Linear MBNMA recovers true per-agent slopes within MC error."""
    params = {"A": {"beta": 0.12}, "B": {"beta": 0.30}}
    ests = {"A": [], "B": []}
    for seed in range(40):
        contrasts, _ = sn.make_network(seed=seed, model="linear", params=params,
                                       n_studies=60, tau=0.0, arm_se=0.15)
        fit = mbnma.fit_mbnma(contrasts, ref="plac@0", parse=sn.parse_node,
                              model="linear")
        ests["A"].append(fit.psi["A"]["beta"])
        ests["B"].append(fit.psi["B"]["beta"])
    for a in ("A", "B"):
        m = float(np.mean(ests[a]))
        assert abs(m - params[a]["beta"]) < 0.02, (a, m)


def test_emax_recovery():
    """Emax MBNMA recovers Emax/ED50 reasonably on a well-identified network."""
    params = {"A": {"Emax": 0.9, "ED50": 2.0}, "B": {"Emax": 0.6, "ED50": 1.0}}
    emax_est, ed50_est = [], []
    n_conv = 0
    for seed in range(40):
        contrasts, _ = sn.make_network(seed=seed, model="emax", params=params,
                                       n_studies=80, tau=0.0, arm_se=0.12)
        fit = mbnma.fit_mbnma(contrasts, ref="plac@0", parse=sn.parse_node,
                              model="emax")
        if fit.converged:
            n_conv += 1
        emax_est.append(fit.psi["A"]["Emax"])
        ed50_est.append(fit.psi["A"]["ED50"])
    assert n_conv >= 30
    # Emax/ED50 are correlated & only weakly identified; check central tendency
    assert abs(np.median(emax_est) - 0.9) < 0.25, np.median(emax_est)
    assert abs(np.median(ed50_est) - 2.0) < 1.2, np.median(ed50_est)


def test_linear_beats_saturated_on_parameters():
    """Constrained linear model uses far fewer params than the saturated NMA."""
    params = {"A": {"beta": 0.12}, "B": {"beta": 0.30}}
    contrasts, _ = sn.make_network(seed=1, model="linear", params=params, n_studies=50)
    nma = mbnma.fit_mbnma(contrasts, ref="plac@0", parse=sn.parse_node, model="nma")
    lin = mbnma.fit_mbnma(contrasts, ref="plac@0", parse=sn.parse_node, model="linear")
    n_nma = len(nma.psi["delta_free"])
    n_lin = len(lin.agents)
    assert n_lin < n_nma  # 2 slopes vs 7 free node effects


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
