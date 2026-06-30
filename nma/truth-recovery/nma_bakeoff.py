"""nma_bakeoff.py -- matched-coverage NMA bake-off (MCIW0 + paired-bootstrap gate).

Generalizes truth-recovery/matched_coverage_bakeoff.py to a vector estimand: the
n-1 basic contrasts d_{ref,t} and the treatment ranking. Compares the modern
field default (common-tau^2 graph-theoretic NMA = netmeta) against the
comparison-specific heterogeneity model and AdaptShrink-NMA, all built on the
SAME verified engine so only the heterogeneity model differs.

Metrics (per DESIGN_BRIEF.md sec 3):
  MCIW0   (primary)   constant-width matched-coverage interval per contrast,
                      calibrated on a parity split; aggregated (mean) over the
                      n-1 contrasts. Isolates point-estimator efficiency.
  raw_cov (deployable) real per-replicate coverage of d_true, kappa=1, no oracle.
  ranking             Spearman rho + top-1 hit-rate of the P-score order vs truth.
  Truth-gate          paired bootstrap of MCIW0 advantage over the field default;
                      robust win = 97.5th percentile of the advantage < 0.

Run: PYTHONPATH=nma python nma/truth-recovery/nma_bakeoff.py --reps 300 --cell sparse_hetero
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # nma/
import nma_sim as S  # noqa: E402
from nma_core import fit_nma, p_score  # noqa: E402
from adaptshrink_nma import adaptshrink_nma, adaptshrink_nma_auto  # noqa: E402

BASE_SEED = 20260621
NU_DEFAULT = 4.0

# The field default (baseline to beat) is common-tau^2 DL = netmeta.
BASELINE = "common_DL"

CELLS = {
    "sparse_hetero": S.NetSpec(geom="loop", n=6, studies_per_comp=(1, 2),
                               hetero="heterogeneous", multiarm_frac=0.0,
                               selection="none"),
    "sparse_hetero_ma": S.NetSpec(geom="loop", n=6, studies_per_comp=(1, 2),
                                  hetero="heterogeneous", multiarm_frac=0.3,
                                  selection="none"),
    "moderate_hetero": S.NetSpec(geom="full", n=5, studies_per_comp=(3, 5),
                                 hetero="heterogeneous", multiarm_frac=0.0,
                                 selection="none"),
    # star: basic contrasts vs the hub ARE the direct edges -> exposes the
    # common-tau^2 mis-calibration (over-covers low-tau, under-covers high-tau).
    "star_hetero": S.NetSpec(geom="star", n=6, studies_per_comp=(3, 5),
                             hetero="heterogeneous", tau_low=0.05, tau_high=0.40,
                             multiarm_frac=0.0, selection="none"),
    "star_hetero_ma": S.NetSpec(geom="star", n=6, studies_per_comp=(3, 5),
                                hetero="heterogeneous", tau_low=0.05, tau_high=0.40,
                                multiarm_frac=0.3, selection="none"),
    "star_homog": S.NetSpec(geom="star", n=6, studies_per_comp=(3, 5),
                            hetero="homogeneous", tau_homog=0.20,
                            multiarm_frac=0.0, selection="none"),
    "sparse_homog": S.NetSpec(geom="loop", n=6, studies_per_comp=(1, 2),
                              hetero="homogeneous", multiarm_frac=0.0,
                              selection="none"),
    # --- selection axis (component B): dense, well-powered nets where the
    #     small-study bias dominates sampling variance -> point-estimate win. ---
    "select_strong_dense": S.NetSpec(geom="full", n=5, studies_per_comp=(8, 15),
                                     hetero="homogeneous", tau_homog=0.10,
                                     selection="strong"),
    # larger dense net: more contrasts -> lower-variance MCIW0 advantage, the
    # regime where B's point de-biasing is a bootstrap-robust efficiency win.
    "select_strong_dense_n6": S.NetSpec(geom="full", n=6, studies_per_comp=(8, 15),
                                        hetero="homogeneous", tau_homog=0.10,
                                        selection="strong"),
    # network-size sweep (Phase-3): identical to n6 headline except n. Tests the
    # falsifiable mechanism that the MCIW0 robust win STRENGTHENS with n, because
    # the mean-over-(n-1)-contrasts MCIW0 advantage has lower bootstrap variance.
    "select_strong_dense_n7": S.NetSpec(geom="full", n=7, studies_per_comp=(8, 15),
                                        hetero="homogeneous", tau_homog=0.10,
                                        selection="strong"),
    "select_strong_dense_n8": S.NetSpec(geom="full", n=8, studies_per_comp=(8, 15),
                                        hetero="homogeneous", tau_homog=0.10,
                                        selection="strong"),
    "select_moderate_dense": S.NetSpec(geom="full", n=5, studies_per_comp=(8, 15),
                                       hetero="homogeneous", tau_homog=0.10,
                                       selection="moderate"),
    "select_strong_sparse": S.NetSpec(geom="full", n=5, studies_per_comp=(3, 5),
                                      hetero="homogeneous", tau_homog=0.10,
                                      selection="strong"),
    # --- inconsistency axis (component C): loops where direct/indirect conflict.
    "incons_full": S.NetSpec(geom="full", n=5, studies_per_comp=(2, 4),
                             hetero="homogeneous", tau_homog=0.10,
                             inconsistency=0.30),
    "incons_loop": S.NetSpec(geom="loop", n=6, studies_per_comp=(2, 4),
                             hetero="homogeneous", tau_homog=0.10,
                             inconsistency=0.30),
    "consistent_full": S.NetSpec(geom="full", n=5, studies_per_comp=(2, 4),
                                 hetero="homogeneous", tau_homog=0.10,
                                 inconsistency=0.0),
}


def _fit_methods(comps, nu):
    out = {}
    out["common_DL"] = fit_nma(comps, random=True)
    out["comp_specific"] = adaptshrink_nma(comps, nu=0.0)
    out["adaptshrink"] = adaptshrink_nma(comps, nu=nu)
    out["adaptshrink_auto"] = adaptshrink_nma_auto(comps, nu=nu)
    return out


def run_replicates(spec, reps, seed0, nu, small_values="undesirable"):
    rows = []          # per (rep, method, contrast)
    rank_rows = []     # per (rep, method)
    for r in range(reps):
        comps, d_true, _ = S.generate(spec, seed0 + r)
        treats_present = sorted({c.t1 for c in comps} | {c.t2 for c in comps})
        # need the full treatment set connected to score all basic contrasts
        if len(treats_present) < spec.n:
            continue
        fits = _fit_methods(comps, nu)
        ref = "0"
        # true ranking by d_true (higher better if small_values='undesirable')
        order_true = np.argsort(-d_true if small_values == "undesirable" else d_true)
        rank_true = {str(t): int(np.where(order_true == t)[0][0]) for t in range(spec.n)}
        best_true = str(int(order_true[0]))
        for mname, fit in fits.items():
            tidx = fit.meta["tidx"]
            if ref not in tidx:
                continue
            for t in range(1, spec.n):
                tl = str(t)
                if tl not in tidx:
                    continue
                d_hat = fit.TE[tidx[tl], tidx[ref]]
                se = fit.seTE[tidx[tl], tidx[ref]]
                rows.append({
                    "rep": r, "method": mname, "contrast": tl,
                    "d_hat": float(d_hat),
                    "ci_low": float(d_hat - 1.959963984540054 * se),
                    "ci_high": float(d_hat + 1.959963984540054 * se),
                    "d_true": float(d_true[t]),
                })
            # ranking
            ps = p_score(fit, small_values=small_values)
            est_order = sorted(ps, key=lambda k: -ps[k])
            est_rank = {t: i for i, t in enumerate(est_order)}
            common = [t for t in rank_true if t in est_rank]
            rho = spearmanr([rank_true[t] for t in common],
                            [est_rank[t] for t in common]).correlation if len(common) > 2 else np.nan
            rank_rows.append({
                "rep": r, "method": mname,
                "spearman": float(rho) if rho == rho else np.nan,
                "top1_correct": int(est_order[0] == best_true),
            })
    return pd.DataFrame(rows), pd.DataFrame(rank_rows)


def matched_coverage(df, target=0.95):
    """Per (method, contrast): MCIW0 + raw coverage with parity calib/test split."""
    out = []
    for (method, contrast), g in df.groupby(["method", "contrast"]):
        g = g[np.isfinite(g["d_hat"]) & np.isfinite(g["ci_low"]) & np.isfinite(g["ci_high"])]
        if len(g) < 8:
            continue
        err = np.abs(g["d_hat"].to_numpy() - g["d_true"].to_numpy())
        reps = g["rep"].to_numpy()
        covered = (g["ci_low"].to_numpy() <= g["d_true"].to_numpy()) & \
                  (g["d_true"].to_numpy() <= g["ci_high"].to_numpy())
        raw_width = float(np.mean(g["ci_high"].to_numpy() - g["ci_low"].to_numpy()))
        calib = reps % 2 == 0
        test = ~calib
        if calib.sum() < 4 or test.sum() < 4:
            continue
        c_half = float(np.quantile(err[calib], target))
        mciw0 = 2.0 * c_half
        mciw0_test_cov = float(np.mean(err[test] <= c_half))

        # MCIW: scale the method's OWN per-rep half-width to hit target on calib
        # (rewards informative, difficulty-tracking uncertainty -- this is where
        # the heterogeneity model matters, since it sets the interval width).
        hw = (g["ci_high"].to_numpy() - g["ci_low"].to_numpy()) / 2.0
        valid_hw = hw > 1e-12
        c_mask = calib & valid_hw
        t_mask = test & valid_hw
        if c_mask.sum() >= 4 and t_mask.sum() >= 4:
            ratio = err / np.where(valid_hw, hw, np.nan)
            kappa = float(np.quantile(ratio[c_mask], target))
            mciw_test_cov = float(np.mean(ratio[t_mask] <= kappa))
            mciw = float(2.0 * kappa * np.mean(hw[t_mask]))
        else:
            kappa = mciw = mciw_test_cov = float("nan")

        out.append({
            "method": method, "contrast": contrast, "n": len(g),
            "bias": float(np.mean(g["d_hat"] - g["d_true"])),
            "rmse": float(np.sqrt(np.mean((g["d_hat"] - g["d_true"]) ** 2))),
            "raw_cov": float(np.mean(covered)), "raw_width": raw_width,
            "mciw0": mciw0, "mciw0_test_cov": mciw0_test_cov,
            "mciw": mciw, "mciw_test_cov": mciw_test_cov, "kappa": kappa,
        })
    return pd.DataFrame(out)


def aggregate_by_method(tab, target=0.95):
    """Mean over contrasts -> one row per method.

    cov_unif = mean |raw_cov_contrast - target| across contrasts: how UNEVEN the
    deployable coverage is across comparisons. Common-tau^2 should be uneven
    (over-covers low-tau, under-covers high-tau comparisons); a good heterogeneity
    model is uniform (small cov_unif).
    """
    rows = []
    for m, g in tab.groupby("method"):
        rows.append({
            "method": m,
            "bias": float(np.mean(np.abs(g["bias"]))),
            "rmse": float(np.mean(g["rmse"])),
            "raw_cov": float(np.mean(g["raw_cov"])),
            "cov_unif": float(np.mean(np.abs(g["raw_cov"] - target))),
            "raw_width": float(np.mean(g["raw_width"])),
            "mciw0": float(np.mean(g["mciw0"])),
            "mciw0_test_cov": float(np.mean(g["mciw0_test_cov"])),
            "mciw": float(np.nanmean(g["mciw"])),
            "mciw_test_cov": float(np.nanmean(g["mciw_test_cov"])),
        })
    return pd.DataFrame(rows)


def bootstrap_vs_baseline(df, target=0.95, n_boot=2000, seed=7):
    """Paired bootstrap of mean-over-contrasts MCIW0 advantage vs the field default.

    Pairs |error| across methods within (rep, contrast); resamples replicate
    indices; recomputes each method's mean-over-contrasts MCIW0; robust win if the
    97.5th percentile of (method - baseline) is < 0.
    """
    rng = np.random.default_rng(seed)
    df = df[np.isfinite(df["d_hat"])].copy()
    df["abserr"] = np.abs(df["d_hat"] - df["d_true"])
    contrasts = sorted(df["contrast"].unique())
    methods = [m for m in df["method"].unique() if m != BASELINE]
    reps = sorted(df["rep"].unique())
    reps = np.array(reps)

    # build per-method, per-contrast error vectors indexed by rep
    def err_matrix(method):
        sub = df[df["method"] == method]
        piv = sub.pivot_table(index="rep", columns="contrast", values="abserr")
        piv = piv.reindex(index=reps, columns=contrasts)
        return piv

    # also need own half-widths for the MCIW (own-width matched coverage) bootstrap
    df["hw"] = (df["ci_high"] - df["ci_low"]) / 2.0

    def hw_matrix(method):
        sub = df[df["method"] == method]
        piv = sub.pivot_table(index="rep", columns="contrast", values="hw")
        return piv.reindex(index=reps, columns=contrasts)

    base_m = err_matrix(BASELINE)
    base_hw = hw_matrix(BASELINE)
    out = []
    for method in methods:
        m_m = err_matrix(method)
        m_hw = hw_matrix(method)
        valid = (~base_m.isna().any(axis=1)) & (~m_m.isna().any(axis=1))
        bv, mv = base_m[valid].to_numpy(), m_m[valid].to_numpy()
        bhw, mhw = base_hw[valid].to_numpy(), m_hw[valid].to_numpy()
        if len(bv) < 16:
            continue
        bi = rng.integers(0, len(bv), size=(n_boot, len(bv)))
        d0 = np.empty(n_boot)   # MCIW0 (point efficiency) advantage
        dw = np.empty(n_boot)   # MCIW (own-width) advantage

        def own_mciw(err, hw, idx):
            # per contrast: kappa = target-quantile of err/hw, MCIW = 2*kappa*mean(hw)
            r = err[idx] / np.where(hw[idx] > 1e-12, hw[idx], np.nan)
            kap = np.nanquantile(r, target, axis=0)
            return 2.0 * np.nanmean(kap * np.nanmean(hw[idx], axis=0))

        for j in range(n_boot):
            idx = bi[j]
            d0[j] = (2.0 * np.mean(np.quantile(mv[idx], target, axis=0))
                     - 2.0 * np.mean(np.quantile(bv[idx], target, axis=0)))
            dw[j] = own_mciw(mv, mhw, idx) - own_mciw(bv, bhw, idx)
        lo0, hi0 = np.quantile(d0, [0.025, 0.975])
        low, hiw = np.quantile(dw, [0.025, 0.975])
        out.append({
            "method": method,
            "mciw0_diff": float(2.0 * np.mean(np.quantile(mv, target, axis=0))
                                - 2.0 * np.mean(np.quantile(bv, target, axis=0))),
            "mciw0_ci_lo": float(lo0), "mciw0_ci_hi": float(hi0),
            "mciw0_robust_win": bool(hi0 < 0.0),
            "mciw_diff": float(own_mciw(mv, mhw, np.arange(len(bv)))
                               - own_mciw(bv, bhw, np.arange(len(bv)))),
            "mciw_ci_lo": float(low), "mciw_ci_hi": float(hiw),
            "mciw_robust_win": bool(hiw < 0.0),
            "frac_better_mciw": float(np.mean(dw < 0.0)),
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=300)
    ap.add_argument("--cell", default="sparse_hetero", choices=list(CELLS.keys()))
    ap.add_argument("--nu", type=float, default=NU_DEFAULT)
    ap.add_argument("--target", type=float, default=0.95)
    ap.add_argument("--out-prefix", default="nma/truth-recovery/nma")
    args = ap.parse_args()

    spec = CELLS[args.cell]
    t0 = time.time()
    rows, rank_rows = run_replicates(spec, args.reps, BASE_SEED, args.nu)
    raw_path = f"{args.out_prefix}_{args.cell}_perrep.csv"
    rows.to_csv(raw_path, index=False)
    rank_path = f"{args.out_prefix}_{args.cell}_rank.csv"
    rank_rows.to_csv(rank_path, index=False)

    tab = matched_coverage(rows, target=args.target)
    tab.to_csv(f"{args.out_prefix}_{args.cell}_percontrast.csv", index=False)
    agg = aggregate_by_method(tab, target=args.target)
    boot = bootstrap_vs_baseline(rows, target=args.target)
    rank_summary = rank_rows.groupby("method").agg(
        spearman=("spearman", "mean"), top1=("top1_correct", "mean")).reset_index()

    agg_path = f"{args.out_prefix}_{args.cell}_summary.csv"
    agg.to_csv(agg_path, index=False)
    gate = {"cell": args.cell, "spec": vars(spec), "reps": args.reps, "nu": args.nu,
            "target": args.target, "baseline": BASELINE,
            "n_scored_reps": int(rows["rep"].nunique()),
            "bootstrap_vs_baseline": boot,
            "G1_all_finite": bool(np.isfinite(rows["d_hat"]).all())}
    gate_path = f"{args.out_prefix}_{args.cell}_gate.json"
    with open(gate_path, "w") as f:
        json.dump(gate, f, indent=2, default=str)

    secs = round(time.time() - t0, 1)
    agg = agg.sort_values("mciw")
    print(f"\n# NMA matched-coverage bake-off  cell={args.cell}  reps={args.reps}  "
          f"nu={args.nu}  (scored reps={gate['n_scored_reps']})")
    print(f"# spec: {vars(spec)}")
    print("# raw_cov/cov_unif = DEPLOYABLE (kappa=1); cov_unif = mean|cov-0.95| across")
    print("#   contrasts (lower=more uniform). MCIW = own-width matched coverage (PRIMARY")
    print("#   for a heterogeneity model: lower=narrower at nominal). MCIW0 = point eff.\n")
    print(f"{'method':<16}{'|bias|':>8}{'raw_cov':>9}{'cov_unif':>9}"
          f"{'MCIW':>9}{'mc_cov':>8}{'MCIW0':>9}{'spearmn':>9}{'top1':>7}")
    rs = rank_summary.set_index("method")
    base_mciw = float(agg[agg["method"] == BASELINE]["mciw"].iloc[0])
    for _, row in agg.iterrows():
        m = row["method"]
        ratio = row["mciw"] / base_mciw
        star = f"  {ratio:.3f}x" if m != BASELINE else "  (field)"
        sp = rs.loc[m, "spearman"] if m in rs.index else float("nan")
        t1 = rs.loc[m, "top1"] if m in rs.index else float("nan")
        print(f"{m:<16}{row['bias']:>8.4f}{row['raw_cov']:>9.3f}{row['cov_unif']:>9.3f}"
              f"{row['mciw']:>9.4f}{row['mciw_test_cov']:>8.3f}{row['mciw0']:>9.4f}"
              f"{sp:>9.3f}{t1:>7.2f}{star}")
    print("\n# Paired-bootstrap advantage vs field default (robust win = 97.5% CI < 0):")
    print(f"{'method':<16}{'dMCIW(own)':>14}{'  95% CI':>22}{'  robust':>9}{'dMCIW0':>10}")
    for b in boot:
        flag = "  WIN" if b["mciw_robust_win"] else ""
        print(f"  {b['method']:<14}{b['mciw_diff']:>+12.4f}  "
              f"[{b['mciw_ci_lo']:+.4f},{b['mciw_ci_hi']:+.4f}]{str(b['mciw_robust_win']):>8}"
              f"{b['mciw0_diff']:>+10.4f}{flag}")
    print(f"\nWrote {raw_path}\n      {agg_path}\n      {gate_path}  ({secs}s)")


if __name__ == "__main__":
    main()
