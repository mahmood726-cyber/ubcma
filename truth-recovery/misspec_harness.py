"""
misspec_harness.py -- Selection-mechanism MISSPECIFICATION robustness for UBCMA.

UBCMA's built-in simulation study (`ubcma.simulation_study`) evaluates coverage
of the true mu under its OWN smooth logistic selection function -- i.e. the data
are generated from (essentially) the same selection family the model assumes.
That is a model-MATCHED evaluation: it tells you UBCMA works when its selection
model is correct.

The truth-recovery yardstick built for the allmeta portfolio (F:\\allmeta,
branch truth-recovery-unified-estimator) made a sharper point: the honest test
of a selection-aware estimator is whether it still recovers the truth when the
selection mechanism is DIFFERENT from the one it assumes -- because in the real
world the mechanism is unknown. Parametric selection models are excellent when
matched and can fail under misspecification.

This harness imports UBCMA's OWN method dispatcher (`_run_method`) and scores it,
unchanged, under three generators at the same true mu:

  smooth   : UBCMA's own logistic selection           (MATCHED -- baseline)
  step     : Vevea-Hedges one-sided p-value STEP weights (MISSPECIFIED)
  copas    : Copas latent-variable selection            (MISSPECIFIED)

Everything else (k, tau, quality bias, df schema) is held identical, so any
coverage drop from `smooth` to `step`/`copas` is attributable purely to
selection-mechanism misspecification.

Truth-first: every number is produced here from seeded simulation. Nothing is
hand-entered. Run: `PYTHONPATH=src python truth-recovery/misspec_harness.py --reps 150`
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.stats import norm

from ubcma.data import MetaAnalysisDataset
from ubcma.simulation_study import _run_method, ScenarioParams, _selection_gamma, _quality_lambda

BASE_SEED = 20260613

# Vevea step weights on the one-sided p-value (favouring large POSITIVE effects).
_STEP_CUTS = np.array([0.025, 0.05])
_STEP_WEIGHTS = {"moderate": np.array([1.0, 0.6, 0.4]),
                 "strong":   np.array([1.0, 0.35, 0.10])}
# Copas latent selection (bench parameterisation).
_COPAS = {"moderate": {"g0": -0.10, "g1": 0.12, "rho": 0.50},
          "strong":   {"g0": -0.20, "g1": 0.12, "rho": 0.90}}

METHODS = ["reml_hksj", "trim_and_fill", "pet_peese", "copas", "ubcma"]


@dataclass
class Spec:
    mu: float = 0.20
    tau: float = 0.10
    k: int = 40
    quality_bias: str = "moderate"


def _base_draw(rng, spec):
    """Common study-level draws (effects, SE, quality) shared by all mechanisms."""
    k = spec.k
    se = rng.uniform(0.05, 0.25, size=k)
    quality = rng.binomial(1, p=np.array([0.35, 0.28, 0.22]), size=(k, 3)).astype(float)
    quality_score = quality.mean(axis=1)
    heterogeneity = rng.normal(0, spec.tau, size=k) if spec.tau > 0 else np.zeros(k)
    bias_lambda = np.array(_quality_lambda(spec.quality_bias))
    internal_bias = quality @ bias_lambda
    true_effect = spec.mu + heterogeneity
    y = rng.normal(true_effect + internal_bias, se)
    return y, se, quality, quality_score


def _make_df(y, se, quality, quality_score, selected):
    k = len(y)
    df = pd.DataFrame({
        "study_id": [f"s{i}" for i in range(k)],
        "yi": y, "sei": se,
        "rob_selection": quality[:, 0],
        "rob_measurement": quality[:, 1],
        "rob_reporting": quality[:, 2],
        "quality_score": quality_score,
        "design": np.array(["RCT"] * k),
    })
    return df[selected].reset_index(drop=True)


def generate(mechanism, strength, spec, seed):
    """Return (df_selected, true_mu). Mechanisms differ ONLY in `selected`."""
    rng = np.random.default_rng(seed)
    for _ in range(50):
        y, se, quality, quality_score = _base_draw(rng, spec)
        z = y / se
        if mechanism == "smooth":
            gamma = np.array(_selection_gamma(strength))
            sig = expit(6.0 * (np.abs(z) - 1.96))
            direction = np.tanh(z / 1.5)
            prec = 1.0 / se
            prec_z = (prec - prec.mean()) / max(prec.std(ddof=0), 1e-9)
            sel_prob = expit(gamma[0] + gamma[1] * sig + gamma[2] * prec_z
                             + gamma[3] * direction + gamma[4] * quality_score)
            selected = rng.uniform(size=spec.k) < sel_prob
        elif mechanism == "step":
            w = _STEP_WEIGHTS[strength]
            p_one = norm.sf(z)                       # one-sided p (favours +)
            idx = np.searchsorted(_STEP_CUTS, p_one, side="right")
            weight = w[idx]
            selected = rng.uniform(size=spec.k) < weight
        elif mechanism == "copas":
            cp = _COPAS[strength]
            eps = (y - spec.mu) / se                 # ~ standardized residual proxy
            d = cp["rho"] * np.tanh(eps) + np.sqrt(1 - cp["rho"] ** 2) * rng.normal(0, 1, spec.k)
            sval = cp["g0"] + cp["g1"] / se + d
            selected = sval > 0
        else:
            raise ValueError(mechanism)
        if selected.sum() >= 6:
            return _make_df(y, se, quality, quality_score, selected), spec.mu
        seed += 1000
        rng = np.random.default_rng(seed)
    # fallback: keep all
    return _make_df(y, se, quality, quality_score, np.ones(spec.k, bool)), spec.mu


def run_cell(mechanism, strength, spec, reps, seed0):
    acc = {m: {"cov": 0, "n": 0, "bias": 0.0, "sq": 0.0, "width": 0.0, "fail": 0}
           for m in METHODS}
    for r in range(reps):
        df, true_mu = generate(mechanism, strength, spec, seed0 + r)
        y = df["yi"].to_numpy()
        se = df["sei"].to_numpy()
        qs = df["quality_score"].to_numpy()
        data = MetaAnalysisDataset.from_dataframe(
            df, effect_col="yi", se_col="sei", study_id_col="study_id",
            quality_cols=["rob_selection", "rob_measurement", "rob_reporting"],
        )
        for m in METHODS:
            res = _run_method(m, y, se, qs, data)
            a = acc[m]
            if not res["converged"] or not np.isfinite(res["mu_hat"]):
                a["fail"] += 1
                continue
            a["n"] += 1
            a["bias"] += res["mu_hat"] - true_mu
            a["sq"] += (res["mu_hat"] - true_mu) ** 2
            if np.isfinite(res["ci_low"]) and np.isfinite(res["ci_high"]):
                a["width"] += res["ci_high"] - res["ci_low"]
                if res["ci_low"] <= true_mu <= res["ci_high"]:
                    a["cov"] += 1
    out = {}
    for m, a in acc.items():
        n = a["n"]
        out[m] = {
            "coverage": round(a["cov"] / n, 3) if n else None,
            "bias": round(a["bias"] / n, 4) if n else None,
            "rmse": round((a["sq"] / n) ** 0.5, 4) if n else None,
            "mean_width": round(a["width"] / n, 4) if n else None,
            "n": n, "fail": a["fail"],
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=150)
    ap.add_argument("--strength", default="strong", choices=["moderate", "strong"])
    ap.add_argument("--out", default="truth-recovery/misspec_results.json")
    args = ap.parse_args()
    spec = Spec()
    t0 = time.time()
    grid = {}
    for mech in ["smooth", "step", "copas"]:
        print(f"[misspec] mechanism={mech} strength={args.strength} ...")
        grid[mech] = run_cell(mech, args.strength, spec, args.reps, BASE_SEED)
    result = {"spec": vars(spec), "strength": args.strength, "reps": args.reps,
              "seconds": round(time.time() - t0, 1), "seed": BASE_SEED,
              "grid": grid}
    with open(args.out, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n# UBCMA selection-misspecification robustness (mu={spec.mu}, tau={spec.tau}, "
          f"k={spec.k}, {args.strength}, reps={args.reps})\n")
    print("Coverage of the TRUE mu (target 0.95):\n")
    header = "mechanism   " + "".join(m.rjust(15) for m in METHODS)
    print(header)
    for mech in ["smooth", "step", "copas"]:
        row = mech.ljust(12) + "".join(
            str(grid[mech][m]["coverage"]).rjust(15) for m in METHODS)
        print(row)
    print("\n(smooth = MATCHED to UBCMA's model; step/copas = MISSPECIFIED)")
    print(f"\nWrote {args.out}  ({result['seconds']}s)")


if __name__ == "__main__":
    main()
