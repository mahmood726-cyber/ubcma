"""realhc_bakeoff.py -- settle the "beat Henmi-Copas" claim against the REAL HC.

The sibling harness ``matched_coverage_bakeoff.py`` (built in a parallel Codex
session) declared AdaptShrink/UBCMA winners "vs Henmi-Copas at matched
coverage". But its HC baseline is the in-repo ``copas`` comparator, which is the
Copas & Shi (2000) selection MLE -- NOT Henmi & Copas (2010). The named
adversary was therefore a mislabelled strawman.

This harness re-runs the SAME matched-coverage comparison with the genuine
Henmi-Copas CI (``ubcma.robust_methods.henmi_copas``, a faithful port of
``metafor::hc`` validated to 2e-8), added as a first-class method
``henmi_copas``. It also adds a standalone conformal AdaptShrink
(``adaptshrink_solo``) that needs no UBCMA fit, alongside the parallel session's
UBCMA-ensemble AdaptShrink (``adaptshrink_ens``, aggregation logic inlined here
so this script does not import churning concurrent files).

Metric (identical to the sibling harness):
    mciw0  = 2 * (target-quantile of |mu_hat - mu_true| on a calib split)
             -- the matched-coverage CONSTANT width; pure point-estimator
             efficiency (lower = better). The CI shape does not enter mciw0, so
             this isolates "is the CENTRE close enough to the truth that a
             95%-covering interval can be narrow?".
    raw_cov/raw_width = deployable (out-of-the-box, no oracle).

A win vs the REAL HC requires (G3) strictly smaller mciw0 with test-split
coverage within tolerance, AND (G4) a paired-bootstrap 97.5% CI of the mciw0
difference below 0. Truth-first: all numbers seeded; nothing hand-entered.

Run one mechanism (shardable for parallelism):
    PYTHONPATH=src python truth-recovery/realhc_bakeoff.py --mechanism step --reps 120
Combine shards + score + gate:
    PYTHONPATH=src python truth-recovery/realhc_bakeoff.py --combine --reps 120
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import misspec_harness as H  # noqa: E402  (committed, stable generators)

from ubcma.data import MetaAnalysisDataset  # noqa: E402
from ubcma.robust_methods import adaptshrink_conformal, henmi_copas, vevea_hedges  # noqa: E402
from ubcma.simulation_study import _run_method  # noqa: E402

Z975 = 1.959963984540054
HC_REF = "henmi_copas"  # the real adversary in this harness

# Base comparators via the committed dispatcher.
BASE_METHODS = ["reml_hksj", "trim_and_fill", "pet_peese", "copas", "ubcma"]
# Ensemble AdaptShrink panel (parallel session's design).
AS_ENS_MEMBERS = ("ubcma", "pet_peese", "trim_and_fill")
SCORED = BASE_METHODS + ["henmi_copas", "vevea_hedges", "adaptshrink_ens",
                         "adaptshrink_ens_vh", "adaptshrink_solo"]

OUT = Path("truth-recovery")


def _eff_se(lo: float, hi: float) -> float:
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return float("nan")
    return (hi - lo) / 2.0 / Z975


def _adaptshrink_ens(precomputed: dict[str, tuple[float, float]],
                     alpha: float = 0.05) -> dict:
    """Inlined copy of ubcma.adaptshrink.adaptshrink_estimator aggregation.

    Robust model-averaging of the panel: weight w_j = 1/(se_j^2 + (mu_j-median)^2)
    down-weights noisy AND outlying members; model-averaging variance =
    within + between spread. Kept here verbatim (reviewed) so this verification
    does not import the concurrently-edited adaptshrink.py.
    """
    from scipy.stats import t as t_dist
    eps = 1e-9
    panel = [(n, mu, se) for n, (mu, se) in precomputed.items()
             if np.isfinite(mu) and np.isfinite(se) and se > 0]
    if not panel:
        return {"mu": float("nan"), "ci_low": float("nan"),
                "ci_high": float("nan"), "converged": False}
    mus = np.array([p[1] for p in panel])
    s2 = np.square(np.array([p[2] for p in panel]))
    m_med = float(np.median(mus))
    w = 1.0 / (s2 + np.square(mus - m_med) + eps)
    w_sum = float(np.sum(w))
    mu_as = float(np.sum(w * mus) / w_sum)
    within = float(np.sum(np.square(w) * s2) / w_sum ** 2)
    between = float(np.sum(w * np.square(mus - mu_as)) / w_sum)
    total_se = float(np.sqrt(max(within + between, eps)))
    n = len(panel)
    crit = float(t_dist.ppf(1 - alpha / 2, df=n - 1)) if n >= 2 else Z975
    half = crit * total_se
    return {"mu": mu_as, "ci_low": mu_as - half, "ci_high": mu_as + half,
            "converged": True}


def run_replicates(mechanism: str, strength: str, spec, reps: int, seed0: int) -> pd.DataFrame:
    rows = []
    for r in range(reps):
        df, true_mu = H.generate(mechanism, strength, spec, seed0 + r)
        y = df["yi"].to_numpy()
        se = df["sei"].to_numpy()
        qs = df["quality_score"].to_numpy()
        data = MetaAnalysisDataset.from_dataframe(
            df, effect_col="yi", se_col="sei", study_id_col="study_id",
            quality_cols=["rob_selection", "rob_measurement", "rob_reporting"],
        )
        res = {m: _run_method(m, y, se, qs, data) for m in BASE_METHODS}

        # REAL Henmi-Copas (closed form, cheap).
        hc = henmi_copas(y, se)
        res["henmi_copas"] = {"mu_hat": hc["mu"], "ci_low": hc["ci_low"],
                              "ci_high": hc["ci_high"],
                              "converged": np.isfinite(hc["ci_low"])}

        # Standalone conformal AdaptShrink (no UBCMA needed).
        solo = adaptshrink_conformal(y, se)
        res["adaptshrink_solo"] = {"mu_hat": solo["mu"], "ci_low": solo["ci_low"],
                                   "ci_high": solo["ci_high"],
                                   "converged": np.isfinite(solo["ci_low"])}

        # Ensemble AdaptShrink (parallel session design) from precomputed members.
        precomp = {}
        for name in AS_ENS_MEMBERS:
            rr = res.get(name)
            if rr and rr["converged"] and np.isfinite(rr["mu_hat"]):
                sem = _eff_se(rr["ci_low"], rr["ci_high"])
                if np.isfinite(sem) and sem > 0:
                    precomp[name] = (rr["mu_hat"], sem)
        ens = _adaptshrink_ens(precomp)
        res["adaptshrink_ens"] = {"mu_hat": ens["mu"], "ci_low": ens["ci_low"],
                                  "ci_high": ens["ci_high"],
                                  "converged": ens["converged"]}

        # FIX1: Vevea-Hedges step weight-function member (built for STEP selection),
        # scored standalone AND added to the ensemble panel (adaptshrink_ens_vh).
        vh = vevea_hedges(y, se)
        vh_ok = np.isfinite(vh["mu"]) and np.isfinite(vh["se"]) and vh["se"] > 0
        res["vevea_hedges"] = {"mu_hat": vh["mu"], "ci_low": vh["mu"] - Z975 * vh["se"],
                               "ci_high": vh["mu"] + Z975 * vh["se"], "converged": vh_ok}
        precomp_vh = dict(precomp)
        if vh_ok:
            precomp_vh["vevea_hedges"] = (vh["mu"], vh["se"])
        ens_vh = _adaptshrink_ens(precomp_vh)
        res["adaptshrink_ens_vh"] = {"mu_hat": ens_vh["mu"], "ci_low": ens_vh["ci_low"],
                                     "ci_high": ens_vh["ci_high"],
                                     "converged": ens_vh["converged"]}

        for m in SCORED:
            rr = res[m]
            rows.append({"mechanism": mechanism, "strength": strength, "rep": r,
                         "method": m, "true_mu": true_mu, "mu_hat": rr["mu_hat"],
                         "ci_low": rr["ci_low"], "ci_high": rr["ci_high"],
                         "converged": bool(rr["converged"])})
    return pd.DataFrame(rows)


def matched_coverage_table(df: pd.DataFrame, target: float = 0.95) -> pd.DataFrame:
    """Per (mechanism, method): raw + matched-coverage metrics, calib/test split.

    Identical metric to matched_coverage_bakeoff.matched_coverage_table.
    """
    out = []
    for (mech, method), g in df.groupby(["mechanism", "method"]):
        g = g[g["converged"] & np.isfinite(g["mu_hat"])
              & np.isfinite(g["ci_low"]) & np.isfinite(g["ci_high"])].copy()
        n = len(g)
        if n < 8:
            continue
        err = np.abs(g["mu_hat"].to_numpy() - g["true_mu"].to_numpy())
        hw = (g["ci_high"].to_numpy() - g["ci_low"].to_numpy()) / 2.0
        covered = (g["ci_low"].to_numpy() <= g["true_mu"].to_numpy()) & \
                  (g["true_mu"].to_numpy() <= g["ci_high"].to_numpy())
        reps = g["rep"].to_numpy()
        calib = (reps % 2 == 0)
        test = ~calib
        if calib.sum() < 4 or test.sum() < 4:
            continue
        c_half = float(np.quantile(err[calib], target))
        mciw0 = float(2.0 * c_half)
        mciw0_test_cov = float(np.mean(err[test] <= c_half))
        valid = hw > 1e-12
        cm, tm = calib & valid, test & valid
        if cm.sum() >= 4 and tm.sum() >= 4:
            ratio = err / np.where(valid, hw, np.nan)
            kappa = float(np.quantile(ratio[cm], target))
            test_cov = float(np.mean(ratio[tm] <= kappa))
            mciw = float(2.0 * kappa * np.mean(hw[tm]))
        else:
            kappa = test_cov = mciw = float("nan")
        out.append({"mechanism": mech, "method": method, "n": n,
                    "bias": float(np.mean(g["mu_hat"] - g["true_mu"])),
                    "rmse": float(np.sqrt(np.mean((g["mu_hat"] - g["true_mu"]) ** 2))),
                    "raw_cov": round(float(np.mean(covered)), 3),
                    "raw_width": round(float(np.mean(2 * hw)), 4),
                    "mciw0": round(mciw0, 4), "mciw0_test_cov": round(mciw0_test_cov, 3),
                    "kappa": round(kappa, 3), "test_cov": round(test_cov, 3),
                    "mciw": round(mciw, 4)})
    return pd.DataFrame(out)


def bootstrap_vs_hc(df: pd.DataFrame, target: float, n_boot: int = 4000,
                    seed: int = 7) -> list[dict]:
    """Paired bootstrap of mciw0 difference (method - REAL HC) per mechanism."""
    rng = np.random.default_rng(seed)
    out = []
    for mech, gm in df.groupby("mechanism"):
        gm = gm[gm["converged"] & np.isfinite(gm["mu_hat"])].copy()
        gm["abserr"] = np.abs(gm["mu_hat"] - gm["true_mu"])
        wide = gm.pivot_table(index="rep", columns="method", values="abserr").dropna()
        if HC_REF not in wide.columns or len(wide) < 16:
            continue
        reps = wide.index.to_numpy()
        hc = wide[HC_REF].to_numpy()
        bidx = rng.integers(0, len(reps), size=(n_boot, len(reps)))
        hc_q = np.quantile(hc[bidx], target, axis=1)
        for method in wide.columns:
            if method == HC_REF:
                continue
            mv = wide[method].to_numpy()
            m_q = np.quantile(mv[bidx], target, axis=1)
            diff = 2.0 * (m_q - hc_q)
            lo, hi = np.quantile(diff, [0.025, 0.975])
            point = 2.0 * (np.quantile(mv, target) - np.quantile(hc, target))
            out.append({"mechanism": mech, "method": method,
                        "mciw0_diff": round(float(point), 4),
                        "ci_lo": round(float(lo), 4), "ci_hi": round(float(hi), 4),
                        "robust_win": bool(hi < 0.0),
                        "frac_better": round(float(np.mean(diff < 0.0)), 3)})
    return out


def truth_gate(df: pd.DataFrame, table: pd.DataFrame, target: float,
               cov_tol: float = 0.06) -> dict:
    gate = {"adversary": HC_REF, "target": target, "cov_tol": cov_tol,
            "pass": True, "notes": []}
    scored = df[df["method"].isin(SCORED) & df["converged"]]
    bad = scored[~(np.isfinite(scored["mu_hat"]) & np.isfinite(scored["ci_low"])
                   & np.isfinite(scored["ci_high"]))]
    gate["G1_finite_ok"] = bool(len(bad) == 0)
    if len(bad):
        gate["pass"] = False
        gate["notes"].append(f"G1 FAIL: {len(bad)} non-finite converged rows")

    wins = []
    for mech, g in table.groupby("mechanism"):
        g = g.set_index("method")
        if HC_REF not in g.index:
            gate["notes"].append(f"{mech}: no {HC_REF} row")
            continue
        hc = g.loc[HC_REF]
        for method, row in g.iterrows():
            if method == HC_REF:
                continue
            cov_ok = abs(row["mciw0_test_cov"] - target) <= cov_tol
            if (row["mciw0"] < hc["mciw0"] - 1e-6) and cov_ok:
                wins.append({"mechanism": mech, "method": method,
                             "mciw0": float(row["mciw0"]),
                             "hc_mciw0": float(hc["mciw0"]),
                             "ratio": round(float(row["mciw0"] / hc["mciw0"]), 3),
                             "test_cov": float(row["mciw0_test_cov"]),
                             "hc_test_cov": float(hc["mciw0_test_cov"])})
    gate["verified_wins_vs_real_hc"] = wins
    boot = bootstrap_vs_hc(df, target)
    gate["bootstrap_mciw0_vs_real_hc"] = boot
    gate["robust_wins_vs_real_hc"] = [b for b in boot if b["robust_win"]]
    return gate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mechanism", choices=["smooth", "step", "copas"])
    ap.add_argument("--reps", type=int, default=120)
    ap.add_argument("--strength", default="strong", choices=["moderate", "strong"])
    ap.add_argument("--target", type=float, default=0.95)
    ap.add_argument("--combine", action="store_true",
                    help="combine per-mechanism shards, score and gate")
    args = ap.parse_args()
    spec = H.Spec()
    prefix = f"realhc_{args.strength}"

    if not args.combine:
        mech = args.mechanism
        assert mech, "provide --mechanism or --combine"
        t0 = time.time()
        out = run_replicates(mech, args.strength, spec, args.reps, H.BASE_SEED)
        path = OUT / f"{prefix}_{mech}_perrep.csv"
        out.to_csv(path, index=False)
        print(f"[realhc] {mech} done: {len(out)} rows -> {path}  ({time.time()-t0:.1f}s)")
        return

    frames = []
    for mech in ["smooth", "step", "copas"]:
        p = OUT / f"{prefix}_{mech}_perrep.csv"
        if p.exists():
            frames.append(pd.read_csv(p))
    raw = pd.concat(frames, ignore_index=True)
    raw.to_csv(OUT / f"{prefix}_perrep.csv", index=False)
    table = matched_coverage_table(raw, target=args.target)
    table.to_csv(OUT / f"{prefix}_table.csv", index=False)
    gate = truth_gate(raw, table, target=args.target)
    with open(OUT / f"{prefix}_truthgate.json", "w") as f:
        json.dump(gate, f, indent=2)

    print(f"\n# REAL Henmi-Copas matched-coverage bake-off "
          f"(mu={spec.mu}, tau={spec.tau}, k={spec.k}, {args.strength}, "
          f"reps={int(raw['rep'].max())+1}, target={args.target})\n")
    for mech in ["smooth", "step", "copas"]:
        sub = table[table["mechanism"] == mech].sort_values("mciw0")
        if sub.empty:
            continue
        hc0 = sub[sub["method"] == HC_REF]["mciw0"]
        hc0 = float(hc0.iloc[0]) if len(hc0) else None
        print(f"-- {mech} --  (real HC mciw0 = {hc0})")
        print(f"{'method':<16}{'bias':>9}{'raw_cov':>9}{'raw_w':>9}{'MCIW0':>9}{'mc0_cov':>9}")
        for _, r in sub.iterrows():
            star = "  <-- < real HC" if (hc0 and r['method'] != HC_REF and r['mciw0'] < hc0) else ""
            mark = "  [REAL HC]" if r['method'] == HC_REF else ""
            print(f"{r['method']:<16}{r['bias']:>9.4f}{r['raw_cov']:>9.3f}"
                  f"{r['raw_width']:>9.4f}{r['mciw0']:>9.4f}{r['mciw0_test_cov']:>9.3f}{star}{mark}")
        print()
    print("# TRUTH-GATE vs REAL Henmi-Copas")
    if gate["verified_wins_vs_real_hc"]:
        print("  VERIFIED mciw0 wins vs REAL HC:")
        for w in gate["verified_wins_vs_real_hc"]:
            print(f"    [{w['mechanism']}] {w['method']}: mciw0={w['mciw0']:.4f} vs "
                  f"HC={w['hc_mciw0']:.4f} (ratio {w['ratio']}), test_cov={w['test_cov']:.3f}")
    else:
        print("  NO method beats the REAL Henmi-Copas at matched coverage.")
    print("\n  Paired-bootstrap mciw0 advantage vs REAL HC (robust = 97.5% CI<0):")
    for b in gate["bootstrap_mciw0_vs_real_hc"]:
        flag = "  ROBUST WIN" if b["robust_win"] else ""
        print(f"    [{b['mechanism']:<6}] {b['method']:<16} d={b['mciw0_diff']:+.4f} "
              f"CI[{b['ci_lo']:+.4f},{b['ci_hi']:+.4f}] P(better)={b['frac_better']:.3f}{flag}")


if __name__ == "__main__":
    main()
