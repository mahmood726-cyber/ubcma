"""field_bakeoff.py -- does AdaptShrink beat the WHOLE modern field, per cell?

Expanded mandate: not just Henmi-Copas, but every serious modern meta-analysis
estimator, across a broad condition grid, judged per cell (never just on
averages). A real "beats the field" claim requires, in each cell: at matched
coverage AdaptShrink is narrower-than-or-tied-with every VALID comparator, AND
AdaptShrink keeps near-nominal DEPLOYABLE coverage. We report every cell where it
loses or ties -- brutally honest.

PANEL (12 estimators):
  classical/robust : dl_hksj, reml_hksj, trim_and_fill, pet_peese
  selection models : copas (Copas-Shi MLE), henmi_copas (real metafor::hc),
                     vevea_hedges (Vevea-Hedges 2-step weight function)
  significant-only : p_curve, p_uniform_star (van Aert p-uniform*)
  selection-aware  : ubcma
  AdaptShrink      : adaptshrink_ens  (robust avg of ubcma+pet+trim&fill)
                     adaptshrink_fast (robust avg of vevea+p_uniform*+pet; NO ubcma)
                     adaptshrink_solo (conformal-forward; parallel-session design)

GRID (strong selection): mu in {0,0.2,0.5} x tau in {0,0.1,0.3} x k in {10,40} x
  mechanism in {none,step,copas}. "none" = NO selection (negative control).

METRIC (identical to realhc_bakeoff/matched_coverage_bakeoff):
  mciw0 = 2 * (target-quantile of |mu_hat-mu_true| on a calib split); matched-
          coverage CONSTANT width, validated on a disjoint test split. Lower=better.
  raw_cov = deployable, out-of-the-box coverage (no oracle).
  Pairwise verdicts come from a paired bootstrap of mciw0 differences per cell.

Shardable for parallel compute:
  PYTHONPATH=src python truth-recovery/field_bakeoff.py --shard 0 --nshards 6 --reps 80 --tag v1
  ... (one process per shard) ...
  PYTHONPATH=src python truth-recovery/field_bakeoff.py --combine --tag v1
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import misspec_harness as H  # noqa: E402

from ubcma.data import MetaAnalysisDataset  # noqa: E402
from ubcma.simulation_study import _run_method  # noqa: E402

Z975 = 1.959963984540054
OUT = Path("truth-recovery")

# Methods computed directly via the dispatcher.
PANEL = ["dl_hksj", "reml_hksj", "trim_and_fill", "pet_peese", "copas",
         "henmi_copas", "vevea_hedges", "p_curve", "p_uniform_star",
         "ubcma", "adaptshrink_solo"]
# Derived ensembles (robust model average of precomputed members).
ENS_MEMBERS = ("ubcma", "pet_peese", "trim_and_fill")
FAST_MEMBERS = ("vevea_hedges", "p_uniform_star", "pet_peese")
SCORED = PANEL + ["adaptshrink_ens", "adaptshrink_fast"]
HEADLINES = ["adaptshrink_ens", "adaptshrink_fast", "adaptshrink_solo"]

MUS = [0.0, 0.2, 0.5]
TAUS = [0.0, 0.1, 0.3]
KS = [10, 40]
MECHS = ["none", "step", "copas"]
STRENGTH = "strong"


def build_grid():
    cells = []
    for mu, tau, k, mech in itertools.product(MUS, TAUS, KS, MECHS):
        cells.append({"mu": mu, "tau": tau, "k": k, "mechanism": mech,
                      "strength": STRENGTH})
    return cells


def _eff_se(lo, hi):
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return float("nan")
    return (hi - lo) / 2.0 / Z975


def _robust_avg(precomputed: dict, alpha: float = 0.05) -> dict:
    """Robust model average: w_j = 1/(se_j^2 + (mu_j-median)^2); model-avg variance."""
    from scipy.stats import t as t_dist
    eps = 1e-9
    panel = [(mu, se) for (mu, se) in precomputed.values()
             if np.isfinite(mu) and np.isfinite(se) and se > 0]
    if not panel:
        return {"mu": float("nan"), "ci_low": float("nan"),
                "ci_high": float("nan"), "converged": False}
    mus = np.array([p[0] for p in panel])
    s2 = np.square(np.array([p[1] for p in panel]))
    med = float(np.median(mus))
    w = 1.0 / (s2 + np.square(mus - med) + eps)
    ws = float(np.sum(w))
    mu = float(np.sum(w * mus) / ws)
    within = float(np.sum(np.square(w) * s2) / ws ** 2)
    between = float(np.sum(w * np.square(mus - mu)) / ws)
    tse = float(np.sqrt(max(within + between, eps)))
    n = len(panel)
    crit = float(t_dist.ppf(1 - alpha / 2, df=n - 1)) if n >= 2 else Z975
    half = crit * tse
    return {"mu": mu, "ci_low": mu - half, "ci_high": mu + half, "converged": True}


def run_cell(cell, reps, seed0):
    spec = H.Spec(mu=cell["mu"], tau=cell["tau"], k=cell["k"],
                  quality_bias="moderate")
    rows = []
    for r in range(reps):
        df, true_mu = H.generate(cell["mechanism"], cell["strength"], spec, seed0 + r)
        y = df["yi"].to_numpy(); se = df["sei"].to_numpy()
        qs = df["quality_score"].to_numpy()
        data = MetaAnalysisDataset.from_dataframe(
            df, effect_col="yi", se_col="sei", study_id_col="study_id",
            quality_cols=["rob_selection", "rob_measurement", "rob_reporting"])
        res = {m: _run_method(m, y, se, qs, data) for m in PANEL}
        # derived ensembles
        for tag, members in (("adaptshrink_ens", ENS_MEMBERS),
                             ("adaptshrink_fast", FAST_MEMBERS)):
            precomp = {}
            for name in members:
                rr = res.get(name)
                if rr and rr["converged"] and np.isfinite(rr["mu_hat"]):
                    sem = _eff_se(rr["ci_low"], rr["ci_high"])
                    if np.isfinite(sem) and sem > 0:
                        precomp[name] = (rr["mu_hat"], sem)
            ens = _robust_avg(precomp)
            res[tag] = {"mu_hat": ens["mu"], "ci_low": ens["ci_low"],
                        "ci_high": ens["ci_high"], "converged": ens["converged"]}
        for m in SCORED:
            rr = res[m]
            rows.append({**{k: cell[k] for k in ("mu", "tau", "k", "mechanism", "strength")},
                         "rep": r, "method": m, "true_mu": true_mu,
                         "mu_hat": rr["mu_hat"], "ci_low": rr["ci_low"],
                         "ci_high": rr["ci_high"], "converged": bool(rr["converged"])})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# scoring
# --------------------------------------------------------------------------
CELL_KEYS = ["mu", "tau", "k", "mechanism", "strength"]


def score_tables(df, target=0.95):
    out = []
    for keys, g in df.groupby(CELL_KEYS):
        cell = dict(zip(CELL_KEYS, keys))
        for method, gm in g.groupby("method"):
            gm = gm[gm["converged"] & np.isfinite(gm["mu_hat"])
                    & np.isfinite(gm["ci_low"]) & np.isfinite(gm["ci_high"])]
            n_tot = (g["method"] == method).sum()
            n = len(gm)
            if n < 8:
                out.append({**cell, "method": method, "n": n,
                            "conv_rate": round(n / max(n_tot, 1), 3),
                            "bias": np.nan, "rmse": np.nan, "raw_cov": np.nan,
                            "mciw0": np.nan, "mciw0_test_cov": np.nan})
                continue
            err = np.abs(gm["mu_hat"].to_numpy() - gm["true_mu"].to_numpy())
            hw = (gm["ci_high"].to_numpy() - gm["ci_low"].to_numpy()) / 2.0
            cov = ((gm["ci_low"].to_numpy() <= gm["true_mu"].to_numpy())
                   & (gm["true_mu"].to_numpy() <= gm["ci_high"].to_numpy()))
            reps = gm["rep"].to_numpy()
            calib, test = reps % 2 == 0, reps % 2 == 1
            if calib.sum() < 4 or test.sum() < 4:
                continue
            c_half = float(np.quantile(err[calib], target))
            out.append({**cell, "method": method, "n": n,
                        "conv_rate": round(n / max(n_tot, 1), 3),
                        "bias": round(float(np.mean(gm["mu_hat"] - gm["true_mu"])), 4),
                        "rmse": round(float(np.sqrt(np.mean((gm["mu_hat"] - gm["true_mu"]) ** 2))), 4),
                        "raw_cov": round(float(np.mean(cov)), 3),
                        "raw_width": round(float(np.mean(2 * hw)), 4),
                        "mciw0": round(float(2 * c_half), 4),
                        "mciw0_test_cov": round(float(np.mean(err[test] <= c_half)), 3)})
    return pd.DataFrame(out)


def bootstrap_pairwise(df, headline, target=0.95, n_boot=2000, seed=11,
                       min_conv=0.8, aggregation="pairwise"):
    """Per cell: paired-bootstrap mciw0(headline) - mciw0(comparator).

    Verdict: 'as_win' if 97.5% CI < 0; 'as_loss' if 2.5% CI > 0; else 'tie'.
    The valid-comparator filter (conv_rate>=min_conv) is applied downstream in
    ``field_domination``.

    ``aggregation`` controls how the paired rep set for each comparison is formed:

    "pairwise" (default, CORRECTED): each headline-vs-comparator paired bootstrap
        uses the reps on which BOTH the headline and THAT comparator converged. A
        comparator is judged if it shares >= 16 paired reps with the headline. No
        third method can delete a comparison, and low-convergence methods (which
        ``field_domination`` excludes anyway via ``min_conv``) cannot delete a whole
        cell from the denominator.

    "global" (LEGACY, retained for reproducibility): the paired rep set is the
        intersection over ALL methods (``pivot_table(...).dropna()``) -- a rep is
        used only if EVERY method converged on it, and the whole cell is skipped if
        that intersection has < 16 reps. This deletes reps, and can delete entire
        cells, because of low-convergence comparators (e.g. p_uniform_star / p_curve
        on null cells) that are later EXCLUDED by ``min_conv`` -- a selection
        artifact that biases the domination numerator/denominator. Selecting this
        mode reproduces the original v1/v2 headline (see
        test_field_bakeoff.py::test_dropna_selection_artifact).
    """
    if aggregation not in ("pairwise", "global"):
        raise ValueError(f"unknown aggregation {aggregation!r}")
    rng = np.random.default_rng(seed)

    def _emit(cell, headline, method, conv_rate, h, mv, common_n, bidx=None):
        # In "global" mode one bootstrap index is shared across all comparators in
        # a cell (drawn once, passed in) -- this exactly reproduces the legacy RNG
        # stream. In "pairwise" mode each comparator has its own common rep set, so
        # a fresh index is drawn per comparison.
        if bidx is None:
            bidx = rng.integers(0, common_n, size=(n_boot, common_n))
        h_q = np.quantile(h[bidx], target, axis=1)
        m_q = np.quantile(mv[bidx], target, axis=1)
        diff = 2.0 * (h_q - m_q)  # headline - comparator; negative = headline narrower
        lo, hi = np.quantile(diff, [0.025, 0.975])
        point = 2.0 * (np.quantile(h, target) - np.quantile(mv, target))
        verdict = "as_win" if hi < 0 else ("as_loss" if lo > 0 else "tie")
        return {**cell, "headline": headline, "comparator": method,
                "comp_conv": round(float(conv_rate.get(method, 0)), 3),
                "d_mciw0": round(float(point), 4),
                "ci_lo": round(float(lo), 4), "ci_hi": round(float(hi), 4),
                "verdict": verdict}

    out = []
    for keys, g in df.groupby(CELL_KEYS):
        cell = dict(zip(CELL_KEYS, keys))
        gg = g[g["converged"] & np.isfinite(g["mu_hat"])].copy()
        gg["abserr"] = np.abs(gg["mu_hat"] - gg["true_mu"])
        # conv rate per method in this cell (over all reps attempted)
        attempted = g.groupby("method")["rep"].nunique()
        conv = g[g["converged"] & np.isfinite(g["mu_hat"])
                 & np.isfinite(g["ci_low"]) & np.isfinite(g["ci_high"])]
        conv_rate = (conv.groupby("method")["rep"].nunique()
                     / attempted).to_dict()

        if aggregation == "global":
            wide = gg.pivot_table(index="rep", columns="method",
                                  values="abserr").dropna()
            if headline not in wide.columns or len(wide) < 16:
                continue
            h = wide[headline].to_numpy()
            bidx = rng.integers(0, len(wide), size=(n_boot, len(wide)))  # shared/cell
            for method in wide.columns:
                if method == headline:
                    continue
                out.append(_emit(cell, headline, method, conv_rate,
                                 h, wide[method].to_numpy(), len(wide), bidx=bidx))
        else:  # "pairwise" -- per-comparator common (both-converged) rep set
            hg = gg[gg["method"] == headline]
            if len(hg) < 16:
                continue
            h_series = hg.set_index("rep")["abserr"]
            h_reps = set(h_series.index)
            for method in gg["method"].unique():
                if method == headline:
                    continue
                m_series = gg[gg["method"] == method].set_index("rep")["abserr"]
                common = sorted(h_reps & set(m_series.index))
                if len(common) < 16:
                    continue
                out.append(_emit(cell, headline, method, conv_rate,
                                 h_series.loc[common].to_numpy(),
                                 m_series.loc[common].to_numpy(), len(common)))
    return pd.DataFrame(out)


def field_domination(score_df, pair_df, headline, cov_tol=0.07, target=0.95,
                     min_conv=0.8):
    """Per cell: does the headline dominate the VALID field + keep nominal cov?"""
    out = []
    sd = score_df.set_index(CELL_KEYS + ["method"])
    for keys, pr in pair_df[pair_df["headline"] == headline].groupby(CELL_KEYS):
        cell = dict(zip(CELL_KEYS, keys))
        try:
            hrow = sd.loc[tuple(keys) + (headline,)]
        except KeyError:
            continue
        valid = pr[pr["comp_conv"] >= min_conv]
        losses = valid[valid["verdict"] == "as_loss"]
        ties = valid[valid["verdict"] == "tie"]
        wins = valid[valid["verdict"] == "as_win"]
        cov_ok = bool(abs(float(hrow["raw_cov"]) - target) <= cov_tol
                      or float(hrow["raw_cov"]) >= target)
        dominates = bool(len(losses) == 0 and cov_ok)
        out.append({**cell, "headline": headline,
                    "raw_cov": float(hrow["raw_cov"]),
                    "deployable_cov_ok": cov_ok,
                    "n_valid_comp": int(len(valid)),
                    "n_win": int(len(wins)), "n_tie": int(len(ties)),
                    "n_loss": int(len(losses)),
                    "loses_to": ",".join(sorted(losses["comparator"])) or "-",
                    "dominates_field": dominates})
    return pd.DataFrame(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--reps", type=int, default=80)
    ap.add_argument("--tag", default="v1")
    ap.add_argument("--combine", action="store_true")
    ap.add_argument("--target", type=float, default=0.95)
    args = ap.parse_args()
    grid = build_grid()

    if not args.combine:
        assert args.shard is not None, "provide --shard or --combine"
        my = [(i, c) for i, c in enumerate(grid) if i % args.nshards == args.shard]
        frames = []
        t0 = time.time()
        for i, cell in my:
            tc = time.time()
            frames.append(run_cell(cell, args.reps, H.BASE_SEED + i * 100000))
            print(f"[field shard{args.shard}] cell {i} {cell} done ({time.time()-tc:.0f}s)",
                  flush=True)
        df = pd.concat(frames, ignore_index=True)
        path = OUT / f"field_{args.tag}_shard{args.shard}.csv"
        df.to_csv(path, index=False)
        print(f"[field shard{args.shard}] wrote {path}  total {time.time()-t0:.0f}s")
        return

    frames = []
    for p in sorted(OUT.glob(f"field_{args.tag}_shard*.csv")):
        frames.append(pd.read_csv(p))
    raw = pd.concat(frames, ignore_index=True)
    raw.to_csv(OUT / f"field_{args.tag}_perrep.csv", index=False)
    score = score_tables(raw, target=args.target)
    score.to_csv(OUT / f"field_{args.tag}_scores.csv", index=False)

    summary = {"tag": args.tag, "target": args.target,
               "n_cells": int(raw.groupby(CELL_KEYS).ngroups),
               "reps": int(raw["rep"].max()) + 1, "headlines": {}}
    all_pairs = []
    for headline in HEADLINES:
        pair = bootstrap_pairwise(raw, headline, target=args.target)
        all_pairs.append(pair)
        dom = field_domination(score, pair, headline, target=args.target)
        dom.to_csv(OUT / f"field_{args.tag}_domination_{headline}.csv", index=False)
        n_dom = int(dom["dominates_field"].sum()) if len(dom) else 0
        summary["headlines"][headline] = {
            "cells_dominated": n_dom, "cells_total": int(len(dom)),
            "cells_with_loss": int((dom["n_loss"] > 0).sum()) if len(dom) else 0,
        }
    pd.concat(all_pairs, ignore_index=True).to_csv(
        OUT / f"field_{args.tag}_pairwise.csv", index=False)
    with open(OUT / f"field_{args.tag}_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n# FIELD-WIDE bake-off  tag={args.tag}  cells={summary['n_cells']}  "
          f"reps={summary['reps']}  target={args.target}\n")
    for h, s in summary["headlines"].items():
        print(f"  {h:<18} dominates {s['cells_dominated']:>3}/{s['cells_total']:<3} cells"
              f"   ({s['cells_with_loss']} cells with >=1 loss)")
    print(f"\nWrote field_{args.tag}_perrep.csv / _scores.csv / _pairwise.csv / "
          f"_domination_*.csv / _summary.json")


if __name__ == "__main__":
    main()
