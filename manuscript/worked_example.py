"""Worked example: run the committed estimator panel + adaptshrink_auto on the
REAL aspirin dataset (examples/verde_2021_aspirin.csv, k=6 log-OR).

Reproduces the EXACT adaptshrink_auto pipeline from
truth-recovery/field_bakeoff2.py (CGATE=4.0, CALIB_A=2.0, TAU0=0.2), using the
committed comparators/estimators. All numbers are computed by committed code on
committed data. Writes manuscript/worked_example.json.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "truth-recovery"))

import field_bakeoff as FB
import field_bakeoff2 as FB2
from ubcma.data import MetaAnalysisDataset
from ubcma.simulation_study import _run_method
from ubcma.robust_methods import pet_fit
from ubcma.model import dersimonian_laird

CGATE = 4.0
CALIB_A = 2.0
TAU0 = 0.2
Z975 = 1.959963984540054

df = pd.read_csv(ROOT / "examples" / "verde_2021_aspirin.csv")
y = df["yi"].to_numpy(); se = df["sei"].to_numpy()
qs = df["quality_score"].to_numpy()
data = MetaAnalysisDataset.from_dataframe(
    df, effect_col="yi", se_col="sei", study_id_col="study_id",
    quality_cols=["rob_selection", "rob_measurement", "rob_reporting"])

PANEL = FB.PANEL
res = {m: _run_method(m, y, se, qs, data) for m in PANEL}

# ensembles (adaptshrink_ens, adaptshrink_fast, adaptshrink_ens_calib)
ens_mu = ens_half = ens_D = np.nan
ens_ok = False
for tag, members in (("adaptshrink_ens", FB.ENS_MEMBERS),
                     ("adaptshrink_fast", FB.FAST_MEMBERS)):
    precomp = {}
    for name in members:
        rr = res.get(name)
        if rr and rr["converged"] and np.isfinite(rr["mu_hat"]):
            sem = FB._eff_se(rr["ci_low"], rr["ci_high"])
            if np.isfinite(sem) and sem > 0:
                precomp[name] = (rr["mu_hat"], sem)
    mu, half, D, ok = FB2._robust_avg_D(precomp)
    res[tag] = {"mu_hat": mu, "ci_low": mu - half, "ci_high": mu + half, "converged": ok}
    if tag == "adaptshrink_ens":
        ens_mu, ens_half, ens_D, ens_ok = mu, half, D, ok
        h2 = half + CALIB_A * D if ok else float("nan")
        res["adaptshrink_ens_calib"] = {"mu_hat": mu, "ci_low": mu - h2,
                                        "ci_high": mu + h2, "converged": ok}

# petgate
try:
    t1 = float(pet_fit(y, se)["t1"])
except Exception:
    t1 = float("nan")
re = res["reml_hksj"]; mu_re = re["mu_hat"]
hw_re = (re["ci_high"] - re["ci_low"]) / 2.0
if ens_ok and np.isfinite(t1) and np.isfinite(mu_re):
    g = t1 * t1 / (t1 * t1 + CGATE)
    mu_pg = (1 - g) * mu_re + g * ens_mu
    hw_pg = (1 - g) * hw_re + g * (ens_half + CALIB_A * ens_D)
    res["adaptshrink_petgate"] = {"mu_hat": mu_pg, "ci_low": mu_pg - hw_pg,
                                  "ci_high": mu_pg + hw_pg, "converged": True}
else:
    g = float("nan")
    res["adaptshrink_petgate"] = {"mu_hat": mu_re, "ci_low": re["ci_low"],
                                  "ci_high": re["ci_high"], "converged": True}

# auto (tau-aware selector)
try:
    tau_hat = float(dersimonian_laird(y, se)["tau"])
except Exception:
    tau_hat = float("nan")
pick = "adaptshrink_ens_calib" if (np.isfinite(tau_hat) and tau_hat < TAU0) else "adaptshrink_petgate"
src = res[pick]
res["adaptshrink_auto"] = {"mu_hat": src["mu_hat"], "ci_low": src["ci_low"],
                           "ci_high": src["ci_high"], "converged": True}

out = {
    "dataset": "verde_2021_aspirin.csv",
    "k": int(len(y)),
    "tau_hat_DL": tau_hat,
    "pet_t1": t1,
    "petgate_g": g,
    "auto_pick": pick,
    "studies": [{"id": r.study_id, "yi": float(r.yi), "sei": float(r.sei)}
                for r in df.itertuples()],
    "methods": {m: {"mu": float(res[m]["mu_hat"]),
                    "ci_low": float(res[m]["ci_low"]),
                    "ci_high": float(res[m]["ci_high"])}
                for m in res},
}
(Path(__file__).resolve().parent / "worked_example.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
