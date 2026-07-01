"""Strengthened benchmark for the PROMOTED estimator: the learned-kernel + conformal
registry field vs the modern borrowing frontier, on the EXPANDED corpus
(1177 nodes / 28 MAs; LOR grown 3 -> 12 MAs).

Truth-gated, held-out reconstruction. Reports:
  (1) MAE table: learned-kernel (honest k-fold, multi-seed) vs
      {within-MA, robust-MAP, hierarchical cross-MA Bayes, g-modeling, no-borrow,
       hand-field (AdaptShrink)}, each with paired-bootstrap CI vs within-MA.
  (2) Per-regime: home-MA sibling count sparse (<=8) / mid (9-40) / rich (>40) --
      is the learned-kernel win uniform or regime-specific?
  (3) Negative controls: SCRAMBLED learned kernel must lose; g-modeling inert.
  (4) Conformal coverage (target 90%) for every method: model PI vs conformal.

This is the reproduce script for the primary-method evidence.
Run:  python borrowing/field_scale/benchmark_learned.py
"""
from __future__ import annotations
import json
import sys
import warnings
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # for borrowing_transport
sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")
from corpus import load_corpus
from field import prep, predict as field_predict
import field_learned as fl
from field_modern import dl_tau2, robust_map, npmle_g, hier_crossMA_predict

SEEDS = (0, 1, 2, 3, 4)


def pboot(a, b, n=5000, seed=7):
    """paired bootstrap mean(a-b) with 95% CI; negative => a smaller error."""
    m = np.isfinite(a) & np.isfinite(b)
    d = (a - b)[m]
    if len(d) < 2:
        return np.nan, np.nan, np.nan, 0
    rng = np.random.default_rng(seed)
    bi = rng.integers(0, len(d), size=(n, len(d)))
    md = d[bi].mean(1)
    return float(d.mean()), float(np.quantile(md, 0.025)), float(np.quantile(md, 0.975)), int(len(d))


def build_predictions(df):
    n = len(df)
    P = {k: np.full(n, np.nan) for k in
         ["no_borrow", "within_MA", "hand_field", "robust_map",
          "hier_bayes", "g_model", "learned_kernel", "learned_scrambled"]}
    S = {k: np.full(n, np.nan) for k in P}

    # --- field.py closed-form baselines ---
    for i in range(n):
        for key, mode in [("no_borrow", "global"), ("within_MA", "withinMA_rel"),
                          ("hand_field", "field_adapt")]:
            mu, se = field_predict(df, i, mode)
            P[key][i] = mu
            S[key][i] = se

    # --- per-target robust-MAP mean + hierarchical cross-MA ---
    for i in range(n):
        t = df.iloc[i]
        sib = df[(df.ma == t.ma) & (df.index != i)]
        if len(sib) >= 1:
            _, mu, se = dl_tau2(sib["yi"].values, sib["se"].values)
            P["robust_map"][i] = mu
            m_, s_, w_ = robust_map(sib["yi"].values, sib["se"].values)
            S["robust_map"][i] = float(np.sqrt((w_ * (s_ ** 2 + m_ ** 2)).sum() - (w_ * m_).sum() ** 2))
        try:
            mu_h, se_h = hier_crossMA_predict(df, i)
            P["hier_bayes"][i] = mu_h
            S["hier_bayes"][i] = se_h
        except Exception:
            pass

    # --- per-family g-modeling prior mean ---
    for _, sub in df.groupby("family"):
        idx = sub.index.values
        grid, pi = npmle_g(sub["yi"].values, sub["se"].values)
        P["g_model"][idx] = float((grid * pi).sum())
        S["g_model"][idx] = np.sqrt(((grid ** 2) * pi).sum() - (grid * pi).sum() ** 2)

    # --- learned kernel (honest k-fold, multi-seed) ---
    mu, sd = fl.predict_kfold_corpus(df, seeds=SEEDS)
    P["learned_kernel"] = mu
    S["learned_kernel"] = sd

    # --- learned kernel with SCRAMBLED labels (negative control) ---
    scr = df.copy()
    rng = np.random.default_rng(101)
    for _, g in df.groupby("family"):
        idx = g.index.to_numpy()
        p = rng.permutation(idx)
        scr.loc[idx, "ma"] = df["ma"].to_numpy()[p]
        scr.loc[idx, "specialty"] = df["specialty"].to_numpy()[p]
    mu_s, sd_s = fl.predict_kfold_corpus(prep(scr), seeds=SEEDS)
    P["learned_scrambled"] = mu_s
    S["learned_scrambled"] = sd_s
    return P, S


def mae_table(df, P):
    y = df["yi"].to_numpy(float)
    order = ["learned_kernel", "robust_map", "hier_bayes", "within_MA",
             "hand_field", "g_model", "no_borrow", "learned_scrambled"]
    rows = []
    for k in order:
        err = np.abs(P[k] - y)
        d, lo, hi, npair = pboot(err, np.abs(P["within_MA"] - y))
        rows.append(dict(method=k, n=int(np.isfinite(err).sum()),
                         MAE=float(np.nanmean(err)),
                         vs_within=d, lo=lo, hi=hi))
    return pd.DataFrame(rows)


def per_regime(df, P):
    y = df["yi"].to_numpy(float)
    ksib = df.groupby("ma")["yi"].transform("size").to_numpy() - 1
    regimes = [("sparse k<=8", ksib <= 8), ("mid 9-40", (ksib > 8) & (ksib <= 40)),
               ("rich k>40", ksib > 40)]
    out = []
    el = np.abs(P["learned_kernel"] - y)
    ew = np.abs(P["within_MA"] - y)
    for name, mask in regimes:
        d, lo, hi, npair = pboot(el[mask], ew[mask])
        out.append(dict(regime=name, n=npair,
                        learned=float(np.nanmean(el[mask])),
                        within=float(np.nanmean(ew[mask])),
                        delta=d, lo=lo, hi=hi))
    return pd.DataFrame(out)


def conformal_table(df, P, S):
    y = df["yi"].to_numpy(float)
    se_t = df["se"].to_numpy(float)
    rows = []
    for k, pred in P.items():
        half = fl.Z975 * np.sqrt(S[k] ** 2 + se_t ** 2)
        cov = ((pred - half <= y) & (y <= pred + half)).astype(float)
        cov[~np.isfinite(pred)] = np.nan
        # rescale model PI to 90% nominal for a fair width comparison
        cf = fl.conformal_intervals(df, pred, alpha=0.10)
        rows.append(dict(method=k, model_cover=float(np.nanmean(cov)),
                         model_width=float(np.nanmean(2 * half)),
                         conf_cover=cf["cover"], conf_width=cf["width"]))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = prep(load_corpus())
    print(f"corpus: {len(df)} nodes | {df.ma.nunique()} MAs | families {sorted(df.family.unique())}")
    print("building predictions (learned kernel = honest 10-fold, 5-seed avg)...")
    P, S = build_predictions(df)

    print("\n" + "=" * 72)
    print("(1) MAE vs modern baselines  (paired bootstrap vs within-MA)")
    print("=" * 72)
    mt = mae_table(df, P)
    for _, r in mt.iterrows():
        tag = "" if r.method == "within_MA" else \
              (" WINS vs within" if r.hi < 0 else (" worse" if r.lo > 0 else " n.s."))
        print(f"  {r.method:18} MAE={r.MAE:.4f}  vs_within={r.vs_within:+.4f} "
              f"[{r.lo:+.4f},{r.hi:+.4f}]{tag}")

    print("\n" + "=" * 72)
    print("(2) Per-regime: learned_kernel - within_MA (negative = learned better)")
    print("=" * 72)
    pr = per_regime(df, P)
    for _, r in pr.iterrows():
        tag = " learned WINS" if r.hi < 0 else (" within better" if r.lo > 0 else " n.s.")
        print(f"  {r.regime:14} n={r.n:5d}  learned={r.learned:.4f} within={r.within:.4f}  "
              f"delta={r.delta:+.4f} [{r.lo:+.4f},{r.hi:+.4f}]{tag}")

    print("\n" + "=" * 72)
    print("(3) Negative controls")
    print("=" * 72)
    y = df["yi"].to_numpy()
    d, lo, hi, _ = pboot(np.abs(P["learned_kernel"] - y), np.abs(P["learned_scrambled"] - y))
    print(f"  learned_kernel - learned_SCRAMBLED = {d:+.4f} [{lo:+.4f},{hi:+.4f}]"
          f"{'  structure REAL (true beats scrambled)' if hi < 0 else '  FAIL'}")
    d, lo, hi, _ = pboot(np.abs(P["within_MA"] - y), np.abs(P["no_borrow"] - y))
    print(f"  within_MA - no_borrow             = {d:+.4f} [{lo:+.4f},{hi:+.4f}]"
          f"{'  within-MA borrowing REAL' if hi < 0 else ''}")

    print("\n" + "=" * 72)
    print("(4) Conformal calibration (target 90%)")
    print("=" * 72)
    ct = conformal_table(df, P, S)
    print(f"  {'method':18}{'modelCov':>9}{'modelW':>9}{'confCov':>9}{'confW':>9}")
    for _, r in ct.iterrows():
        print(f"  {r.method:18}{r.model_cover:>9.3f}{r.model_width:>9.3f}"
              f"{r.conf_cover:>9.3f}{r.conf_width:>9.3f}")

    out = dict(corpus=dict(nodes=len(df), MAs=int(df.ma.nunique()),
                           families={k: int(v) for k, v in df.family.value_counts().items()}),
               mae=mt.to_dict("records"), per_regime=pr.to_dict("records"),
               conformal=ct.to_dict("records"))
    json.dump(out, open(Path(__file__).resolve().parent / "benchmark_learned_results.json", "w"), indent=2)
    print("\nwrote benchmark_learned_results.json")
