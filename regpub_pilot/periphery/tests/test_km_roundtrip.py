"""KM->IPD reconstruction round-trip validation (the classic Guyot self-check).

Simulate a two-arm cohort with a KNOWN hazard ratio, build a data-driven KM curve
+ at-risk table from it, reconstruct pseudo-IPD via KMDigitizer, re-derive the HR,
and assert it matches the direct log-rank on the original IPD within tolerance AND
that the trust gate CONFIRMS it. Then perturb the digitization and assert the gate
FLAGS the now-inconsistent reconstruction.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from periphery import toolpaths

toolpaths.ensure_on_path()
from kmdigitizer import (IPDRecord, compute_logrank_hr, parse_coords,
                         parse_at_risk, reconstruct_two_arm)
from periphery.km_ipd import reconstruct_from_drop, trust_gate

GRID = [0, 1.5, 3, 4.5, 6, 8, 10, 12, 15, 18, 21, 24]


def _sim(lam, n, tmax=24.0, seed=0):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        t = rng.expovariate(lam)
        c = rng.uniform(6, tmax * 1.4)
        if t <= c and t <= tmax:
            out.append((round(t, 4), 1))
        else:
            out.append((round(min(c, tmax), 4), 0))
    return out


def _km(recs):
    rs = sorted(recs)
    ev = sorted({t for t, e in rs if e == 1})
    coords, atrisk = [], []
    for g in GRID:
        n = sum(1 for t, e in rs if t >= g)
        S = 1.0
        for et in ev:
            if et > g:
                break
            nat = sum(1 for t, e in rs if t >= et)
            d = sum(1 for t, e in rs if abs(t - et) < 1e-9 and e == 1)
            if nat > 0:
                S *= 1 - d / nat
        coords.append(f"{g},{round(S, 4)}")
        atrisk.append(f"{g},{n}")
    return "\n".join(coords), "\n".join(atrisk)


def test_roundtrip_recovers_hr_and_confirms():
    N, lam_c, HR = 600, 0.05, 0.65
    tx = _sim(lam_c * HR, N, seed=1)
    ct = _sim(lam_c, N, seed=2)
    direct = compute_logrank_hr(
        [IPDRecord(time=t, event=e, arm="t") for t, e in tx],
        [IPDRecord(time=t, event=e, arm="c") for t, e in ct])
    tc, ta = _km(tx)
    cc, ca = _km(ct)
    drop = {"pmid": "_rt", "tx": {"n0": N, "coords": tc, "at_risk": ta},
            "ctrl": {"n0": N, "coords": cc, "at_risk": ca},
            "reported": {"hr": direct.hr, "ci_lo": direct.ci[0], "ci_hi": direct.ci[1]}}
    r = reconstruct_from_drop(drop)
    # reconstructed HR within 20% of the direct-Cox HR on the source IPD
    assert abs(r["recon_hr"] - direct.hr) / direct.hr < 0.20
    # and consistent enough to CONFIRM + be poolable + flagged as reconstructed
    assert r["trust_gate"]["verdict"] == "CONFIRMED"
    assert r["poolable"] is True
    assert r["reconstructed_from_figure"] is True


def test_bad_digitization_is_flagged_not_pooled():
    # Reconstruct a real curve but claim a wildly different reported HR:
    N = 500
    tx = _sim(0.05 * 0.65, N, seed=3)
    ct = _sim(0.05, N, seed=4)
    tc, ta = _km(tx)
    cc, ca = _km(ct)
    drop = {"pmid": "_bad", "tx": {"n0": N, "coords": tc, "at_risk": ta},
            "ctrl": {"n0": N, "coords": cc, "at_risk": ca},
            "reported": {"hr": 0.30, "ci_lo": 0.20, "ci_hi": 0.45}}  # implausible vs curve
    r = reconstruct_from_drop(drop)
    assert r["trust_gate"]["verdict"] == "FLAGGED"
    assert r["poolable"] is False
