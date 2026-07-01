"""dr_bakeoff.py -- AdaptShrink matched-coverage bake-off for dose-response MA.

Mirrors truth-recovery/matched_coverage_bakeoff.py, but the estimand is the
pooled linear dose-response SLOPE beta and the field-standard baseline to beat is
the two-stage REML DRMA (the dosresmeta workhorse). Under one-sided publication
selection (sim_doseresponse) the naive pooled slope is biased UP; we ask whether
an AdaptShrink aggregate of {two-stage REML, a PET-style trend correction,
one-stage GLS} is more EFFICIENT at matched coverage -- and gate every "win"
through the same MCIW0 + paired-bootstrap truth-gate used in the other threads.

Methods scored
--------------
  two_stage_reml : standard two-stage REML DRMA            (BASELINE, "the field")
  two_stage_fixed: two-stage fixed-effect DRMA
  one_stage      : pooled-GLS one-stage DRMA
  trend_pet      : PET/Egger-style small-study correction of the slope
                   (regress per-study slope on its SE; intercept = corrected)
  adaptshrink    : kernel aggregate of {two_stage_reml, trend_pet, one_stage}
                   via src/ubcma/adaptshrink.adaptshrink_estimator (same kernel)

Run:
  PYTHONPATH=doseresponse:src python doseresponse/dr_bakeoff.py --reps 300 --strength strong
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
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import drma  # noqa: E402
import sim_doseresponse as S  # noqa: E402
from ubcma.adaptshrink import adaptshrink_estimator  # noqa: E402

Z975 = 1.959963984540054
BASELINE = "two_stage_reml"
# AdaptShrink panel = the VALID (low-bias) estimators only. The regression-based
# small-study correctors trend_pet/trend_peese are STRUCTURALLY INVALID for the
# log-RR slope (the slope estimate and its SE share Poisson denominators -> a
# spurious slope-SE association, so they carry large POSITIVE bias even under NO
# selection; see the 'none' rows). They are reported as diagnostics but excluded
# from the panel -- there is no oracle-free bias-corrected member to draw on.
AS_MEMBERS = ("two_stage_reml", "two_stage_fixed", "one_stage")
ALL_METHODS = ["two_stage_reml", "two_stage_fixed", "one_stage",
               "trend_pet", "trend_peese", "adaptshrink"]


def _ci(mu, se):
    return mu - Z975 * se, mu + Z975 * se


def _trend_reg(bi, sei, moderator):
    """Regression-based small-study correction of the slope. moderator='se'
    (PET) or 'var' (PEESE): WLS of per-study slope b_i on the moderator with
    weights 1/s_i^2; the intercept (moderator=0) is the corrected slope.

    NOTE: structurally invalid for log-RR slopes (b_i and s_i share count
    denominators) -- biased even with no selection; kept only as a diagnostic.
    """
    bi = np.asarray(bi, float)
    sei = np.asarray(sei, float)
    ok = np.isfinite(bi) & np.isfinite(sei) & (sei > 0)
    bi, sei = bi[ok], sei[ok]
    if len(bi) < 3:
        return float("nan"), float("nan")
    mod = sei if moderator == "se" else sei ** 2
    w = 1.0 / sei ** 2
    X = np.column_stack([np.ones_like(sei), mod])
    WX = X * w[:, None]
    A = X.T @ WX
    beta = np.linalg.solve(A, WX.T @ bi)
    resid = bi - X @ beta
    dof = max(len(bi) - 2, 1)
    sigma2 = float(resid @ (w * resid) / dof)
    cov = np.linalg.inv(A) * sigma2
    return float(beta[0]), float(np.sqrt(max(cov[0, 0], 0.0)))


def fit_all(df, true_beta):
    """Return {method: (mu, ci_lo, ci_hi, converged)} for one dataset."""
    out = {}
    # two-stage (reml + fixed) share the first stage; reml gives per-study bi/Sigma
    f_reml = drma.drma_two_stage(df, n_col="peryears", transform="linear", method="reml")
    f_fix = drma.drma_two_stage(df, n_col="peryears", transform="linear", method="fixed")
    bi = f_reml.bi.ravel()
    sei = np.array([np.sqrt(S_[0, 0]) for S_ in f_reml.Sigma_list])

    mu_r = float(f_reml.coef[0]); se_r = float(np.sqrt(f_reml.vcov[0, 0]))
    lo, hi = _ci(mu_r, se_r)
    out["two_stage_reml"] = (mu_r, lo, hi, True)

    mu_f = float(f_fix.coef[0]); se_f = float(np.sqrt(f_fix.vcov[0, 0]))
    lo, hi = _ci(mu_f, se_f)
    out["two_stage_fixed"] = (mu_f, lo, hi, True)

    f_one = drma.drma_one_stage(df, n_col="peryears", transform="linear")
    mu_o = float(f_one.coef[0]); se_o = float(np.sqrt(f_one.vcov[0, 0]))
    lo, hi = _ci(mu_o, se_o)
    out["one_stage"] = (mu_o, lo, hi, True)

    for name, moderator in (("trend_pet", "se"), ("trend_peese", "var")):
        mu_x, se_x = _trend_reg(bi, sei, moderator)
        if np.isfinite(mu_x) and np.isfinite(se_x) and se_x > 0:
            lo, hi = _ci(mu_x, se_x)
            out[name] = (mu_x, lo, hi, True)
        else:
            out[name] = (float("nan"), float("nan"), float("nan"), False)

    precomputed = {"two_stage_reml": (mu_r, se_r), "two_stage_fixed": (mu_f, se_f),
                   "one_stage": (mu_o, se_o)}
    as_res = adaptshrink_estimator(
        np.zeros(1), np.ones(1), members=AS_MEMBERS, precomputed=precomputed, kappa=1.0)
    out["adaptshrink"] = (as_res["mu"], as_res["ci_low"], as_res["ci_high"],
                          bool(as_res["converged"]))
    return out


def run_replicates(strength, reps, seed0=12345, tau_slope=0.02):
    rows = []
    for r in range(reps):
        df, beta = S.gen_published(seed0 + r, strength, tau_slope=tau_slope)
        if df is None:
            continue
        res = fit_all(df, beta)
        for m in ALL_METHODS:
            mu, lo, hi, conv = res[m]
            rows.append({"strength": strength, "rep": r, "method": m,
                         "true_mu": beta, "mu_hat": mu, "ci_low": lo,
                         "ci_high": hi, "converged": conv})
    return pd.DataFrame(rows)


def matched_coverage_table(df, target=0.95):
    out = []
    for (strength, method), g in df.groupby(["strength", "method"]):
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
        calib = reps % 2 == 0
        test = ~calib
        if calib.sum() < 4 or test.sum() < 4:
            continue
        c_half = float(np.quantile(err[calib], target))
        mciw0 = 2.0 * c_half
        mciw0_test_cov = float(np.mean(err[test] <= c_half))
        valid = hw > 1e-12
        cm = calib & valid
        tm = test & valid
        if cm.sum() >= 4 and tm.sum() >= 4:
            ratio = err / np.where(valid, hw, np.nan)
            kappa = float(np.quantile(ratio[cm], target))
            test_cov = float(np.mean(ratio[tm] <= kappa))
            mciw = float(2.0 * kappa * np.mean(hw[tm]))
        else:
            kappa = test_cov = mciw = float("nan")
        out.append({
            "strength": strength, "method": method, "n": n,
            "bias": float(np.mean(g["mu_hat"] - g["true_mu"])),
            "rmse": float(np.sqrt(np.mean((g["mu_hat"] - g["true_mu"]) ** 2))),
            "raw_cov": round(float(np.mean(covered)), 3),
            "raw_width": round(float(np.mean(2 * hw)), 5),
            "mciw0": round(mciw0, 5), "mciw0_test_cov": round(mciw0_test_cov, 3),
            "mciw": round(mciw, 5), "test_cov": round(test_cov, 3),
        })
    return pd.DataFrame(out)


def _bootstrap_mciw0(df, target=0.95, n_boot=2000, seed=7):
    rng = np.random.default_rng(seed)
    out = []
    for strength, gm in df.groupby("strength"):
        gm = gm[gm["converged"] & np.isfinite(gm["mu_hat"])]
        gm = gm.assign(abserr=np.abs(gm["mu_hat"] - gm["true_mu"]))
        wide = gm.pivot_table(index="rep", columns="method", values="abserr").dropna()
        if BASELINE not in wide.columns or len(wide) < 16:
            continue
        reps = wide.index.to_numpy()
        base = wide[BASELINE].to_numpy()
        idx = rng.integers(0, len(reps), size=(n_boot, len(reps)))
        base_q = np.quantile(base[idx], target, axis=1)
        for method in wide.columns:
            if method == BASELINE:
                continue
            mv = wide[method].to_numpy()
            m_q = np.quantile(mv[idx], target, axis=1)
            diff = 2.0 * (m_q - base_q)
            lo, hi = np.quantile(diff, [0.025, 0.975])
            point = 2.0 * (np.quantile(mv, target) - np.quantile(base, target))
            out.append({"strength": strength, "method": method,
                        "mciw0_diff": round(float(point), 5),
                        "ci_lo": round(float(lo), 5), "ci_hi": round(float(hi), 5),
                        "robust_win": bool(hi < 0.0),
                        "frac_better": round(float(np.mean(diff < 0)), 3)})
    return out


def truth_gate(df, table, target=0.95, cov_tol=0.06):
    gate = {"target": target, "cov_tol": cov_tol, "baseline": BASELINE, "notes": []}
    scored = df[df["method"].isin(ALL_METHODS)]
    conv = scored[scored["converged"]]
    bad = conv[~np.isfinite(conv["mu_hat"])]
    gate["G1_finite_point_ok"] = bool(len(bad) == 0)
    wins = []
    for strength, g in table.groupby("strength"):
        g = g.set_index("method")
        if BASELINE not in g.index:
            continue
        base = g.loc[BASELINE]
        for method, row in g.iterrows():
            if method == BASELINE:
                continue
            cov_ok = abs(row["mciw0_test_cov"] - target) <= cov_tol
            beats = (row["mciw0"] < base["mciw0"] - 1e-9) and cov_ok
            if beats:
                wins.append({"strength": strength, "method": method,
                             "mciw0": float(row["mciw0"]),
                             "base_mciw0": float(base["mciw0"]),
                             "ratio": round(float(row["mciw0"] / base["mciw0"]), 3),
                             "test_cov": float(row["mciw0_test_cov"])})
    gate["verified_wins_vs_baseline"] = wins
    boot = _bootstrap_mciw0(df, target)
    gate["bootstrap_mciw0_vs_baseline"] = boot
    gate["robust_wins_vs_baseline"] = [b for b in boot if b["robust_win"]]
    return gate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=300)
    ap.add_argument("--strengths", default="none,moderate,strong")
    ap.add_argument("--tau-slope", type=float, default=0.02)
    ap.add_argument("--out-prefix", default="doseresponse/dr_bakeoff")
    ap.add_argument("--from-csv", default=None)
    args = ap.parse_args()

    t0 = time.time()
    if args.from_csv:
        raw = pd.read_csv(args.from_csv)
        raw_path = args.from_csv
    else:
        frames = []
        for st in args.strengths.split(","):
            print(f"[dr-bakeoff] strength={st} reps={args.reps} tau_slope={args.tau_slope} ...",
                  flush=True)
            frames.append(run_replicates(st, args.reps, tau_slope=args.tau_slope))
        raw = pd.concat(frames, ignore_index=True)
        raw_path = f"{args.out_prefix}_perrep.csv"
        raw.to_csv(raw_path, index=False)

    table = matched_coverage_table(raw)
    table_path = f"{args.out_prefix}_table.csv"
    table.to_csv(table_path, index=False)
    gate = truth_gate(raw, table)
    gate_path = f"{args.out_prefix}_truthgate.json"
    json.dump(gate, open(gate_path, "w"), indent=2)

    print(f"\n# Dose-response matched-coverage bake-off (baseline={BASELINE})")
    print("MCIW0 = matched-coverage constant width (PRIMARY, lower=better).\n")
    for st in args.strengths.split(","):
        sub = table[table["strength"] == st].sort_values("mciw0")
        if sub.empty:
            continue
        b0 = sub[sub["method"] == BASELINE]["mciw0"]
        b0 = float(b0.iloc[0]) if len(b0) else None
        print(f"-- selection = {st} --")
        print(f"{'method':<16}{'bias':>10}{'rmse':>9}{'raw_cov':>9}{'MCIW0':>9}{'mc0_cov':>9}")
        for _, r in sub.iterrows():
            star = "  <- narrower" if (b0 and r["method"] != BASELINE and r["mciw0"] < b0) else ""
            print(f"{r['method']:<16}{r['bias']:>10.4f}{r['rmse']:>9.4f}"
                  f"{r['raw_cov']:>9.3f}{r['mciw0']:>9.5f}{r['mciw0_test_cov']:>9.3f}{star}")
        print()
    print("# TRUTH-GATE")
    print(f"  G1 finite point estimates ok : {gate['G1_finite_point_ok']}")
    if gate["verified_wins_vs_baseline"]:
        print("  VERIFIED wins vs two-stage REML at matched coverage (MCIW0):")
        for w in gate["verified_wins_vs_baseline"]:
            print(f"    [{w['strength']}] {w['method']}: MCIW0={w['mciw0']:.5f} vs "
                  f"base {w['base_mciw0']:.5f} (ratio {w['ratio']}), test_cov={w['test_cov']:.3f}")
    else:
        print("  NO method verified to beat two-stage REML at matched coverage.")
    print("\n  Paired-bootstrap MCIW0 advantage vs baseline (robust win = 97.5% CI < 0):")
    for b in gate["bootstrap_mciw0_vs_baseline"]:
        flag = "  ROBUST WIN" if b["robust_win"] else ""
        print(f"    [{b['strength']:<8}] {b['method']:<16} dMCIW0={b['mciw0_diff']:+.5f}  "
              f"CI[{b['ci_lo']:+.5f},{b['ci_hi']:+.5f}]  P(better)={b['frac_better']:.3f}{flag}")
    print(f"\nWrote {raw_path}\n      {table_path}\n      {gate_path}  ({round(time.time()-t0,1)}s)")


if __name__ == "__main__":
    main()
