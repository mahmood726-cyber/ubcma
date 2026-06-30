"""Borrowing-field pilot harness + matched-coverage truth gate.

Held-out-effect design on the real T2DM HbA1c field (active-class vs placebo):
  * target class c in {GLP1, DPP4, SGLT2} (the well-populated classes)
  * truth mu*_c = REML pool over ALL of c's trials (data-rich gold standard)
  * regimes: SPARSE (k=2 sampled c-trials) and RICH (k=8 sampled c-trials)
  * methods (PAIRED within a replicate's sampled subset):
      - nma    : standard NMA (netmeta-parity engine) on full field + sampled c
                 -> TE[c, placebo]  (the no-borrowing comparator)
      - borrow : AdaptShrink borrowing field (own sampled c  (+)  cross-class
                 relevance x lambda x precision prior, with stand-down)
  * scoring: MCIW0 matched-coverage (constant-width, point-estimator efficiency)
    + paired bootstrap of the MCIW0 advantage vs nma -- the SAME gate logic as
    truth-recovery/matched_coverage_bakeoff.py, baseline = nma.

Negative control: relevance scrambled (mechanism map permuted across classes)
-> borrowing must NOT manufacture a win and must stand down (delta small).
"""
from __future__ import annotations

import sys, json, argparse
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "nma"))

import borrowing_field as BF
from ubcma.comparators import reml_estimator
from nma_core import fit_nma, Comparison

Z975 = 1.959963984540054
TARGETS = ["GLP1", "DPP4", "SGLT2"]
REGIMES = {"sparse": 2, "rich": 8}


def reml_truth(trials):
    y = np.array([t["y"] for t in trials], float)
    se = np.array([t["se"] for t in trials], float)
    r = reml_estimator(y, se)
    return float(r["mu"])


def nma_estimate(sampled, others_all, target):
    """Standard NMA TE[target, placebo] on full field (others) + sampled target."""
    comps = []
    for i, t in enumerate(sampled):
        comps.append(Comparison(f"S_{target}_{i}", target, "placebo", t["y"], t["se"]))
    for j, t in enumerate(others_all):
        comps.append(Comparison(f"O_{t['active']}_{j}", t["active"], "placebo", t["y"], t["se"]))
    fit = fit_nma(comps, reference="placebo", random=True)
    tidx = fit.meta["tidx"]
    ti, pi = tidx[target], tidx["placebo"]
    te = float(fit.TE[ti, pi]); se = float(fit.seTE[ti, pi])
    return te, se


def run(trials, lam, scramble=False, reps=300, seed0=20260630):
    # optional negative control: permute the mechanism map across the classes
    # present so "relevance" no longer tracks real mechanism similarity.
    if scramble:
        present = sorted({t["active"] for t in trials})
        groups = [BF.MECHANISM[c] for c in present]
        rng = np.random.default_rng(12345)
        perm = rng.permutation(groups)
        BF.MECHANISM.update({c: g for c, g in zip(present, perm)})

    by_class = {c: [t for t in trials if t["active"] == c] for c in set(t["active"] for t in trials)}
    truths = {c: reml_truth(v) for c, v in by_class.items() if len(v) >= 2}
    rows = []
    for c in TARGETS:
        pool = by_class[c]
        nc = len(pool)
        mu_star = truths[c]
        target_baseline = float(np.nanmean([t["baseline"] for t in pool
                                            if t["baseline"] is not None]))
        # sources = ALL trials of OTHER classes (the borrowing field)
        sources = [BF.Source(t["active"], t["y"], t["se"],
                             t["baseline"], lam.get(t["active"], 0.3))
                   for t in trials if t["active"] != c]
        for regime, k in REGIMES.items():
            kk = min(k, nc - 1)
            if kk < 1:
                continue
            rng = np.random.default_rng(seed0 + hash((c, regime)) % 99999)
            for rep in range(reps):
                idx = rng.choice(nc, size=kk, replace=False)
                sampled = [pool[i] for i in idx]
                others_field = [t for t in trials if t["active"] != c]
                # --- standard NMA ---
                te, se = nma_estimate(sampled, others_field, c)
                rows.append(dict(target=c, regime=regime, rep=rep, method="nma",
                                 true_mu=mu_star, mu_hat=te,
                                 ci_low=te - Z975 * se, ci_high=te + Z975 * se,
                                 converged=np.isfinite(te) and np.isfinite(se)))
                # --- borrowing field ---
                oy = np.array([t["y"] for t in sampled]); ose = np.array([t["se"] for t in sampled])
                b = BF.borrow_estimate(oy, ose, c, target_baseline, sources)
                rows.append(dict(target=c, regime=regime, rep=rep, method="borrow",
                                 true_mu=mu_star, mu_hat=b["mu"],
                                 ci_low=b["ci_low"], ci_high=b["ci_high"],
                                 converged=bool(b["converged"]) if "converged" in b else np.isfinite(b["mu"]),
                                 delta=b.get("delta"), Q=b.get("Q_conflict")))
                # --- null diagnostic: plain field-mean shrinkage (no relevance/lambda) ---
                sm = BF.borrow_estimate(oy, ose, c, target_baseline, sources, uniform_prior=True)
                rows.append(dict(target=c, regime=regime, rep=rep, method="shrink_mean",
                                 true_mu=mu_star, mu_hat=sm["mu"],
                                 ci_low=sm["ci_low"], ci_high=sm["ci_high"],
                                 converged=np.isfinite(sm["mu"]),
                                 delta=sm.get("delta"), Q=sm.get("Q_conflict")))
    return pd.DataFrame(rows)


# ---- matched-coverage scoring (baseline = nma); mirrors matched_coverage_bakeoff ----
def mc_table(df, target=0.95):
    out = []
    for (tg, rg, method), g in df.groupby(["target", "regime", "method"]):
        g = g[g["converged"] & np.isfinite(g["mu_hat"]) & np.isfinite(g["ci_low"]) & np.isfinite(g["ci_high"])]
        if len(g) < 8:
            continue
        err = np.abs(g["mu_hat"].to_numpy() - g["true_mu"].to_numpy())
        lo = g["ci_low"].to_numpy(); hi = g["ci_high"].to_numpy(); tm = g["true_mu"].to_numpy()
        covered = (lo <= tm) & (tm <= hi)
        reps = g["rep"].to_numpy()
        calib = reps % 2 == 0; test = ~calib
        if calib.sum() < 4 or test.sum() < 4:
            continue
        c_half = float(np.quantile(err[calib], target))
        mciw0 = 2.0 * c_half
        mciw0_test_cov = float(np.mean(err[test] <= c_half))
        out.append(dict(target=tg, regime=rg, method=method, n=len(g),
                        bias=float(np.mean(g["mu_hat"] - g["true_mu"])),
                        rmse=float(np.sqrt(np.mean((g["mu_hat"] - g["true_mu"]) ** 2))),
                        raw_cov=round(float(np.mean(covered)), 3),
                        raw_width=round(float(np.mean(hi - lo)), 4),
                        mciw0=round(mciw0, 4), mciw0_test_cov=round(mciw0_test_cov, 3)))
    return pd.DataFrame(out)


def _paired_boot(base, meth, rng, n_boot, target):
    bi = rng.integers(0, len(base), size=(n_boot, len(base)))
    diff = 2.0 * (np.quantile(meth[bi], target, axis=1) - np.quantile(base[bi], target, axis=1))
    loq, hiq = np.quantile(diff, [0.025, 0.975])
    point = 2.0 * (np.quantile(meth, target) - np.quantile(base, target))
    return dict(mciw0_diff=round(float(point), 4), ci_lo=round(float(loq), 4),
                ci_hi=round(float(hiq), 4), robust_win=bool(hiq < 0.0),
                robust_harm=bool(loq > 0.0), frac_better=round(float(np.mean(diff < 0.0)), 3))


def bootstrap_mciw0(df, target=0.95, n_boot=2000, seed=7):
    """Paired bootstrap of MCIW0 advantage. contrasts: borrow-vs-nma (primary),
    shrink_mean-vs-nma, and borrow-vs-shrink_mean (does relevance/lambda add?)."""
    rng = np.random.default_rng(seed); out = []
    CONTRASTS = [("borrow", "nma"), ("shrink_mean", "nma"), ("borrow", "shrink_mean")]
    for (tg, rg), gm in df.groupby(["target", "regime"]):
        gm = gm[gm["converged"] & np.isfinite(gm["mu_hat"])]
        gm = gm.assign(abserr=np.abs(gm["mu_hat"] - gm["true_mu"]))
        wide = gm.pivot_table(index="rep", columns="method", values="abserr").dropna()
        if len(wide) < 16:
            continue
        for meth_name, base_name in CONTRASTS:
            if meth_name not in wide.columns or base_name not in wide.columns:
                continue
            r = _paired_boot(wide[base_name].to_numpy(), wide[meth_name].to_numpy(),
                             rng, n_boot, target)
            out.append(dict(target=tg, regime=rg, contrast=f"{meth_name}_vs_{base_name}", **r))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=300)
    ap.add_argument("--scramble", action="store_true")
    ap.add_argument("--prefix", default="pilot")
    args = ap.parse_args()
    trials = json.load(open(HERE / "trials.json"))
    lam = json.load(open(HERE / "class_lambda.json"))
    df = run(trials, lam, scramble=args.scramble, reps=args.reps)
    tag = "_scramble" if args.scramble else ""
    df.to_csv(HERE / f"{args.prefix}{tag}_perrep.csv", index=False)
    tbl = mc_table(df)
    tbl.to_csv(HERE / f"{args.prefix}{tag}_table.csv", index=False)
    boot = bootstrap_mciw0(df)
    json.dump(boot, open(HERE / f"{args.prefix}{tag}_bootstrap.json", "w"), indent=2)

    print(f"\n# Borrowing-field pilot  (scramble={args.scramble}, reps={args.reps})")
    print(f"  field: {len(trials)} trials; targets={TARGETS}")
    for rg in ["sparse", "rich"]:
        print(f"\n-- regime = {rg} --")
        print(f"{'target':7}{'method':8}{'bias':>9}{'rmse':>8}{'raw_cov':>9}{'MCIW0':>9}{'mc0_cov':>9}")
        sub = tbl[tbl["regime"] == rg]
        for tg in TARGETS:
            for _, r in sub[sub["target"] == tg].sort_values("method").iterrows():
                print(f"{r['target']:7}{r['method']:8}{r['bias']:>9.4f}{r['rmse']:>8.4f}"
                      f"{r['raw_cov']:>9.3f}{r['mciw0']:>9.4f}{r['mciw0_test_cov']:>9.3f}")
    print("\n# PAIRED-BOOTSTRAP MCIW0 advantage; win=97.5% CI<0, harm=2.5% CI>0")
    for contrast in ["borrow_vs_nma", "shrink_mean_vs_nma", "borrow_vs_shrink_mean"]:
        print(f"  contrast: {contrast}")
        for b in [x for x in boot if x["contrast"] == contrast]:
            flag = "  ROBUST WIN" if b["robust_win"] else ("  ROBUST HARM" if b["robust_harm"] else "")
            print(f"    [{b['target']:6} {b['regime']:6}] dMCIW0={b['mciw0_diff']:+.4f} "
                  f"CI[{b['ci_lo']:+.4f},{b['ci_hi']:+.4f}] P(better)={b['frac_better']:.2f}{flag}")
    # stand-down diagnostics
    bdf = df[(df.method == "borrow")]
    if "delta" in bdf.columns:
        print("\n# STAND-DOWN (mean delta; 1=full borrow, 0=full stand-down)")
        for rg in ["sparse", "rich"]:
            for tg in TARGETS:
                d = bdf[(bdf.regime == rg) & (bdf.target == tg)]["delta"].dropna()
                if len(d):
                    print(f"  [{tg:6} {rg:6}] mean delta={d.mean():.3f}  mean Q={bdf[(bdf.regime==rg)&(bdf.target==tg)]['Q'].dropna().mean():.2f}")


if __name__ == "__main__":
    main()
