"""field_bakeoff2.py -- (b) broadened field-wide bake-off.

Extends field_bakeoff.py along three axes the mandate asked for:
  * more heterogeneity levels (tau up to 0.5),
  * binary / log-odds-ratio outcomes (a real 2x2-table DGP), and
  * small k = 5 (with the adaptive selection threshold in misspec_harness).

It also folds in avenue (a): a calibrated ensemble `adaptshrink_ens_calib` =
adaptshrink_ens centre + disagreement-inflated interval (hw + 2*D), the deployable
variant validated in field_rescore_interval.py.

Scoring (matched-coverage MCIW0 + paired bootstrap + deployable coverage +
field-domination) is reused verbatim from field_bakeoff so verdicts are identical
in definition to v1.

Continuous outcome reuses misspec_harness.generate; the log-OR outcome uses a
fresh 2x2 binomial DGP with the same three selection mechanisms applied to z=y/se.

Shardable:
  PYTHONPATH=src python truth-recovery/field_bakeoff2.py --shard 0 --nshards 4 --reps 60 --tag b1 --outcome continuous
  PYTHONPATH=src python truth-recovery/field_bakeoff2.py --shard 0 --nshards 4 --reps 60 --tag b2 --outcome logor
  PYTHONPATH=src python truth-recovery/field_bakeoff2.py --combine --tag b1
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import field_bakeoff as FB  # noqa: E402
import misspec_harness as H  # noqa: E402

from ubcma.data import MetaAnalysisDataset  # noqa: E402
from ubcma.simulation_study import _run_method  # noqa: E402

Z975 = 1.959963984540054
OUT = Path("truth-recovery")
CELL_KEYS = ["mu", "tau", "k", "mechanism", "strength", "outcome"]

PANEL = FB.PANEL
ENS_MEMBERS = FB.ENS_MEMBERS
FAST_MEMBERS = FB.FAST_MEMBERS
SCORED = PANEL + ["adaptshrink_ens", "adaptshrink_fast", "adaptshrink_ens_calib",
                  "adaptshrink_petgate", "adaptshrink_auto"]
HEADLINES = ["adaptshrink_ens", "adaptshrink_ens_calib", "adaptshrink_fast",
             "adaptshrink_petgate", "adaptshrink_auto"]
CALIB_A = 2.0   # interval-inflation constant from avenue (a)
CGATE = 4.0     # PET-asymmetry gate constant (avenue c); |t1|=2 -> g=0.5
TAU0 = 0.2      # adaptshrink_auto: use ens_calib when tau_hat<TAU0 else petgate


# --------------------------------------------------------------------------
# generators
# --------------------------------------------------------------------------

def _apply_selection(y, se, quality_score, mechanism, strength, spec, rng):
    """Replicate misspec_harness selection mechanisms on arbitrary (y, se)."""
    z = y / se
    k = len(y)
    if mechanism == "none":
        return np.ones(k, bool)
    if mechanism == "smooth":
        gamma = np.array(H._selection_gamma(strength))
        sig = expit(6.0 * (np.abs(z) - 1.96))
        direction = np.tanh(z / 1.5)
        prec = 1.0 / se
        prec_z = (prec - prec.mean()) / max(prec.std(ddof=0), 1e-9)
        sel = expit(gamma[0] + gamma[1] * sig + gamma[2] * prec_z
                    + gamma[3] * direction + gamma[4] * quality_score)
        return rng.uniform(size=k) < sel
    if mechanism == "step":
        w = H._STEP_WEIGHTS[strength]
        idx = np.searchsorted(H._STEP_CUTS, norm.sf(z), side="right")
        return rng.uniform(size=k) < w[idx]
    if mechanism == "copas":
        cp = H._COPAS[strength]
        eps = (y - spec.mu) / se
        d = cp["rho"] * np.tanh(eps) + np.sqrt(1 - cp["rho"] ** 2) * rng.normal(0, 1, k)
        return (cp["g0"] + cp["g1"] / se + d) > 0
    raise ValueError(mechanism)


def generate_logor(mechanism, strength, spec, seed):
    """2x2-table log-OR DGP with the same selection mechanisms. Returns (df, mu)."""
    rng = np.random.default_rng(seed)
    need = 6 if spec.k >= 8 else 4
    for _ in range(60):
        k = spec.k
        n_ctrl = rng.integers(20, 200, size=k)
        n_trt = rng.integers(20, 200, size=k)
        p_c = rng.uniform(0.1, 0.5, size=k)
        logit_c = np.log(p_c / (1 - p_c))
        quality = rng.binomial(1, p=np.array([0.35, 0.28, 0.22]), size=(k, 3)).astype(float)
        quality_score = quality.mean(axis=1)
        bias_lambda = np.array(H._quality_lambda(spec.quality_bias))
        internal_bias = quality @ bias_lambda
        theta = spec.mu + (rng.normal(0, spec.tau, size=k) if spec.tau > 0 else 0.0)
        p_t = expit(logit_c + theta + internal_bias)
        a = rng.binomial(n_trt, p_t); c = rng.binomial(n_ctrl, p_c)
        b = n_trt - a; d = n_ctrl - c
        # Haldane-Anscombe 0.5 correction
        y = np.log((a + 0.5) * (d + 0.5) / ((b + 0.5) * (c + 0.5)))
        se = np.sqrt(1/(a+0.5) + 1/(b+0.5) + 1/(c+0.5) + 1/(d+0.5))
        sel = _apply_selection(y, se, quality_score, mechanism, strength, spec, rng)
        if sel.sum() >= need:
            df = pd.DataFrame({
                "study_id": [f"s{i}" for i in range(k)], "yi": y, "sei": se,
                "rob_selection": quality[:, 0], "rob_measurement": quality[:, 1],
                "rob_reporting": quality[:, 2], "quality_score": quality_score,
                "design": np.array(["RCT"] * k)})
            return df[sel].reset_index(drop=True), spec.mu
        seed += 1000
        rng = np.random.default_rng(seed)
    return df.reset_index(drop=True), spec.mu


def _robust_avg_D(precomputed):
    """Robust model average returning (mu, half_width, D=between SD)."""
    from scipy.stats import t as t_dist
    eps = 1e-9
    panel = [(mu, se) for (mu, se) in precomputed.values()
             if np.isfinite(mu) and np.isfinite(se) and se > 0]
    if not panel:
        return float("nan"), float("nan"), float("nan"), False
    mus = np.array([p[0] for p in panel]); s2 = np.square(np.array([p[1] for p in panel]))
    med = float(np.median(mus))
    w = 1.0 / (s2 + np.square(mus - med) + eps); ws = float(np.sum(w))
    mu = float(np.sum(w * mus) / ws)
    within = float(np.sum(np.square(w) * s2) / ws ** 2)
    between = float(np.sum(w * np.square(mus - mu)) / ws)
    tse = float(np.sqrt(max(within + between, eps)))
    n = len(panel)
    crit = float(t_dist.ppf(0.975, df=n - 1)) if n >= 2 else Z975
    return mu, crit * tse, float(np.sqrt(max(between, 0.0))), True


def run_cell(cell, reps, seed0):
    spec = H.Spec(mu=cell["mu"], tau=cell["tau"], k=cell["k"], quality_bias="moderate")
    gen = generate_logor if cell["outcome"] == "logor" else \
        (lambda mech, st, sp, sd: H.generate(mech, st, sp, sd))
    rows = []
    for r in range(reps):
        df, true_mu = gen(cell["mechanism"], cell["strength"], spec, seed0 + r)
        y = df["yi"].to_numpy(); se = df["sei"].to_numpy()
        qs = df["quality_score"].to_numpy()
        data = MetaAnalysisDataset.from_dataframe(
            df, effect_col="yi", se_col="sei", study_id_col="study_id",
            quality_cols=["rob_selection", "rob_measurement", "rob_reporting"])
        res = {m: _run_method(m, y, se, qs, data) for m in PANEL}
        # ensembles
        ens_mu = ens_half = ens_D = np.nan
        ens_ok = False
        for tag, members in (("adaptshrink_ens", ENS_MEMBERS),
                             ("adaptshrink_fast", FAST_MEMBERS)):
            precomp = {}
            for name in members:
                rr = res.get(name)
                if rr and rr["converged"] and np.isfinite(rr["mu_hat"]):
                    sem = FB._eff_se(rr["ci_low"], rr["ci_high"])
                    if np.isfinite(sem) and sem > 0:
                        precomp[name] = (rr["mu_hat"], sem)
            mu, half, D, ok = _robust_avg_D(precomp)
            res[tag] = {"mu_hat": mu, "ci_low": mu - half, "ci_high": mu + half,
                        "converged": ok}
            if tag == "adaptshrink_ens":
                ens_mu, ens_half, ens_D, ens_ok = mu, half, D, ok
                h2 = half + CALIB_A * D if ok else float("nan")
                res["adaptshrink_ens_calib"] = {
                    "mu_hat": mu, "ci_low": mu - h2, "ci_high": mu + h2,
                    "converged": ok}

        # (c) PET-asymmetry-gated AdaptShrink: revert to efficient RE when funnel
        # asymmetry (a tau-robust selection signal) is weak; use the calibrated
        # ensemble when it is strong. g = t1^2/(t1^2 + CGATE).
        try:
            from ubcma.robust_methods import pet_fit
            t1 = float(pet_fit(y, se)["t1"])
        except Exception:
            t1 = float("nan")
        re = res["reml_hksj"]
        mu_re = re["mu_hat"]
        hw_re = (re["ci_high"] - re["ci_low"]) / 2.0
        if ens_ok and np.isfinite(t1) and np.isfinite(mu_re):
            g = t1 * t1 / (t1 * t1 + CGATE)
            mu_pg = (1 - g) * mu_re + g * ens_mu
            hw_pg = (1 - g) * hw_re + g * (ens_half + CALIB_A * ens_D)
            res["adaptshrink_petgate"] = {"mu_hat": mu_pg, "ci_low": mu_pg - hw_pg,
                                          "ci_high": mu_pg + hw_pg, "converged": True}
        else:
            res["adaptshrink_petgate"] = {"mu_hat": mu_re, "ci_low": re["ci_low"],
                                          "ci_high": re["ci_high"],
                                          "converged": bool(np.isfinite(mu_re))}

        # adaptshrink_auto: tau-aware selector. Use the calibrated ensemble when
        # heterogeneity is low (bias-correction pays off) and the PET-gated
        # estimator when tau_hat is high (revert toward efficient RE). tau_hat is
        # the observable DerSimonian-Laird estimate; saved for post-hoc sweeps.
        try:
            from ubcma.model import dersimonian_laird
            tau_hat = float(dersimonian_laird(y, se)["tau"])
        except Exception:
            tau_hat = float("nan")
        pick = "adaptshrink_ens_calib" if (np.isfinite(tau_hat) and tau_hat < TAU0) \
            else "adaptshrink_petgate"
        src = res[pick]
        res["adaptshrink_auto"] = {"mu_hat": src["mu_hat"], "ci_low": src["ci_low"],
                                   "ci_high": src["ci_high"],
                                   "converged": bool(src["converged"])}
        for m in SCORED:
            rr = res[m]
            rows.append({**{kk: cell[kk] for kk in CELL_KEYS}, "rep": r,
                         "method": m, "true_mu": true_mu, "mu_hat": rr["mu_hat"],
                         "ci_low": rr["ci_low"], "ci_high": rr["ci_high"],
                         "converged": bool(rr["converged"]), "pet_t1": t1,
                         "tau_hat": tau_hat})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# grid
# --------------------------------------------------------------------------

def build_grid(outcome):
    # Representative broadened grid (the new axes vs v1 are tau=0.5, k=5, logOR);
    # v1 already covered continuous tau in {0,0.1,0.3} at k in {10,40}.
    if outcome == "logor":
        mus, taus, ks = [0.0, 0.4, 0.8], [0.15, 0.4], [10, 40]      # 36 cells
    else:  # continuous: adds k=5 and tau=0.5
        mus, taus, ks = [0.0, 0.2, 0.5], [0.1, 0.3, 0.5], [5, 40]   # 54 cells
    cells = []
    for mu, tau, k, mech in itertools.product(mus, taus, ks, ["none", "step", "copas"]):
        cells.append({"mu": mu, "tau": tau, "k": k, "mechanism": mech,
                      "strength": "strong", "outcome": outcome})
    return cells


def _score_with_outcome(raw, target=0.95):
    """score_tables/bootstrap/domination keyed on CELL_KEYS (incl. outcome)."""
    orig = FB.CELL_KEYS
    FB.CELL_KEYS = CELL_KEYS
    try:
        score = FB.score_tables(raw, target=target)
        pairs, doms = {}, {}
        for h in HEADLINES:
            pairs[h] = FB.bootstrap_pairwise(raw, h, target=target)
            doms[h] = FB.field_domination(score, pairs[h], h, target=target)
    finally:
        FB.CELL_KEYS = orig
    return score, pairs, doms


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--reps", type=int, default=60)
    ap.add_argument("--tag", default="b1")
    ap.add_argument("--outcome", default="continuous", choices=["continuous", "logor"])
    ap.add_argument("--combine", action="store_true")
    ap.add_argument("--target", type=float, default=0.95)
    args = ap.parse_args()

    if not args.combine:
        grid = build_grid(args.outcome)
        my = [(i, c) for i, c in enumerate(grid) if i % args.nshards == args.shard]
        frames = []
        t0 = time.time()
        for i, cell in my:
            tc = time.time()
            frames.append(run_cell(cell, args.reps, H.BASE_SEED + i * 100000))
            print(f"[b shard{args.shard}] cell {i} {cell} ({time.time()-tc:.0f}s)", flush=True)
        pd.concat(frames, ignore_index=True).to_csv(
            OUT / f"field2_{args.tag}_shard{args.shard}.csv", index=False)
        print(f"[b shard{args.shard}] done total {time.time()-t0:.0f}s")
        return

    frames = [pd.read_csv(p) for p in sorted(OUT.glob(f"field2_{args.tag}_shard*.csv"))]
    raw = pd.concat(frames, ignore_index=True)
    raw.to_csv(OUT / f"field2_{args.tag}_perrep.csv", index=False)
    score, pairs, doms = _score_with_outcome(raw, target=args.target)
    score.to_csv(OUT / f"field2_{args.tag}_scores.csv", index=False)
    summary = {"tag": args.tag, "n_cells": int(raw.groupby(CELL_KEYS).ngroups),
               "reps": int(raw["rep"].max()) + 1, "headlines": {}}
    for h in HEADLINES:
        doms[h].to_csv(OUT / f"field2_{args.tag}_domination_{h}.csv", index=False)
        d = doms[h]
        summary["headlines"][h] = {"dominates": int(d["dominates_field"].sum()),
                                   "total": int(len(d)),
                                   "loss_cells": int((d["n_loss"] > 0).sum())}
    with open(OUT / f"field2_{args.tag}_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n# FIELD2 bake-off tag={args.tag} cells={summary['n_cells']} reps={summary['reps']}\n")
    for h, s in summary["headlines"].items():
        print(f"  {h:<22} dominates {s['dominates']:>3}/{s['total']:<3}  "
              f"({s['loss_cells']} loss-cells)")


if __name__ == "__main__":
    main()
