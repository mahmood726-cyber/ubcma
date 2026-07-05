"""INDEPENDENT witness for donor_ceiling.py -- from-scratch GP (grid-NLML, no import of
field_learned / field / cold_transfer). Recomputes the load-bearing decomposition numbers:

  A_nodonor  : cold LOMO, target MA fully held out, predict its TEST half.
  B_sibling  : donor half relabelled `m__sib` (distinct ma-code) kept in training; predict
               the test half (label m) -- level-matched donor routed via spec+prec+year only.

and the GLP1 recentering (field posterior mean A vs B on the GLP1 test half). If this
independent engine agrees in SIGN that B reduces the cold loss and recentres GLP1, the
donor-ceiling headline is cross-engine confirmed. Emits donor_ceiling_witness.json.

Deliberately independent choices (same math contract, different code path):
  - GP hyper-params by coarse-to-fine GRID on the NLML (not L-BFGS).
  - within-MA: LOO precision-weighted mean of same-MA siblings, year-Gaussian downweight.
  - own feature builder (pd.factorize codes), own kernel, own split RNG stream.
"""
from __future__ import annotations
import sys, json, functools
from pathlib import Path
import numpy as np
import pandas as pd

print = functools.partial(print, flush=True)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from corpus import load_corpus   # only reads the SAME corpus LOR nodes; no field/field_learned/cold_transfer

SPLIT_SEED = 20260705


def stdz(x):
    x = np.asarray(x, float); m = np.isfinite(x); o = np.zeros_like(x)
    if m.sum() >= 2 and np.nanstd(x[m]) > 1e-9:
        o[m] = (x[m] - np.nanmean(x[m])) / np.nanstd(x[m])
    return o


def features(df):
    yr = stdz(df["year"].to_numpy(float))
    lp = np.log(np.maximum(1.0 / df["se"].to_numpy(float) ** 2, 1e-12))
    lp = (lp - lp.mean()) / (lp.std() + 1e-9)
    spec = pd.factorize(df["specialty"])[0].astype(float)
    ma = pd.factorize(df["ma"])[0].astype(float)
    return np.column_stack([yr, lp, spec, ma])


def kernel(Xa, Xb, sf2, lyr, llp, lsp, lma):
    dyr = (Xa[:, 0][:, None] - Xb[:, 0][None, :]) ** 2
    dlp = (Xa[:, 1][:, None] - Xb[:, 1][None, :]) ** 2
    msp = (Xa[:, 2][:, None] != Xb[:, 2][None, :]).astype(float)
    mma = (Xa[:, 3][:, None] != Xb[:, 3][None, :]).astype(float)
    q = dyr / lyr ** 2 + dlp / llp ** 2 + msp / lsp ** 2 + mma / lma ** 2
    return sf2 * np.exp(-0.5 * q)


def nlml(Xtr, ytr, alpha, hp):
    sf2, lyr, llp, lsp, lma, nug = hp
    K = kernel(Xtr, Xtr, sf2, lyr, llp, lsp, lma) + np.diag(alpha + nug)
    try:
        L = np.linalg.cholesky(K)
    except np.linalg.LinAlgError:
        return 1e18
    a = np.linalg.solve(L.T, np.linalg.solve(L, ytr))
    return float(0.5 * ytr @ a + np.log(np.diag(L)).sum() + 0.5 * len(ytr) * np.log(2 * np.pi))


def fit_grid(Xtr, ytr, alpha):
    ymean = ytr.mean(); yc = ytr - ymean
    sf2_0 = max(np.var(yc), 1e-3)
    grid_l = [0.5, 1.5, 4.0]
    best = (None, np.inf)
    for lyr in grid_l:
        for llp in grid_l:
            for lsp in [0.7, 2.0, 5.0]:
                for lma in [0.5, 1.5, 5.0]:
                    f = nlml(Xtr, yc, alpha, (sf2_0, lyr, llp, lsp, lma, 1e-2))
                    if f < best[1]:
                        best = ((sf2_0, lyr, llp, lsp, lma, 1e-2), f)
    hp0 = best[0]
    for sf2 in [0.3 * hp0[0], hp0[0], 3 * hp0[0]]:
        for nug in [1e-3, 1e-2, 1e-1]:
            hp = (sf2, hp0[1], hp0[2], hp0[3], hp0[4], nug)
            f = nlml(Xtr, yc, alpha, hp)
            if f < best[1]:
                best = (hp, f)
    return best[0], ymean


def gp_predict(Xtr, ytr, alpha, Xte, hp, ymean):
    sf2, lyr, llp, lsp, lma, nug = hp
    K = kernel(Xtr, Xtr, sf2, lyr, llp, lsp, lma) + np.diag(alpha + nug)
    Ks = kernel(Xtr, Xte, sf2, lyr, llp, lsp, lma)
    Kinv = np.linalg.inv(K)
    return Ks.T @ (Kinv @ (ytr - ymean)) + ymean


def within_ma(df, i, yz):
    same = (df.ma.to_numpy() == df.iloc[i].ma) & (np.arange(len(df)) != i)
    if same.sum() == 0:
        return np.nan
    y = df["yi"].to_numpy(float)[same]; se = df["se"].to_numpy(float)[same]
    w = 1.0 / np.maximum(se ** 2, 1e-9)
    tyz = yz[i]
    if np.isfinite(tyz):
        yzs = yz[same]
        w = w * np.where(np.isfinite(yzs), np.exp(-0.5 * (yzs - tyz) ** 2), 1.0)
    return float((w * y).sum() / w.sum())


def pboot(a, b, n=5000, seed=7):
    m = np.isfinite(a) & np.isfinite(b); d = (a - b)[m]
    rng = np.random.default_rng(seed)
    bi = rng.integers(0, len(d), size=(n, len(d)))
    return float(d.mean()), float(np.quantile(d[bi].mean(1), 0.025)), float(np.quantile(d[bi].mean(1), 0.975)), int(len(d))


def main():
    corpus = load_corpus()
    clor = corpus[corpus.family == "LOR"][["ma", "specialty", "yi", "se", "year"]]
    sl = pd.read_csv(HERE / "aact_coldslice_nodes.csv")
    aact = sl[sl.corpus_specialty == 1][["ma", "specialty", "yi", "se", "year"]].copy()
    aact["year"] = pd.to_numeric(aact["year"], errors="coerce")
    df = pd.concat([clor, aact], ignore_index=True).reset_index(drop=True)
    aact_mas = sorted(aact.ma.unique())
    y = df["yi"].to_numpy(float)
    print(f"[witness] combined LOR: {len(df)} nodes / {df.ma.nunique()} MAs; AACT {len(aact_mas)} MAs")

    # deterministic disjoint donor/test split (own RNG stream, same seed as primary)
    rng = np.random.default_rng(SPLIT_SEED)
    ma0 = df.ma.to_numpy().copy()
    donor, test = {}, {}
    for m in aact_mas:
        idx = np.where(ma0 == m)[0]; perm = rng.permutation(idx); h = len(perm) // 2
        test[m] = np.sort(perm[:h]); donor[m] = np.sort(perm[h:])
    test_mask = np.zeros(len(df), bool)
    for m in aact_mas:
        test_mask[test[m]] = True

    yz = stdz(df["year"].to_numpy(float))
    win = np.full(len(df), np.nan)
    for i in np.where(test_mask)[0]:
        win[i] = within_ma(df, i, yz)

    def predict(mode):
        dfx = df.copy()
        if mode == "B":
            for m in aact_mas:
                dfx.loc[donor[m], "ma"] = m + "__sib"
        X = features(dfx); alpha = dfx["se"].to_numpy(float) ** 2
        ma_now = dfx.ma.to_numpy()
        mu = np.full(len(dfx), np.nan)
        for m in aact_mas:
            te = test[m]
            if mode == "A":
                tr = np.where((ma_now != m) & (ma_now != m + "__sib"))[0]
            else:
                tr = np.where(ma_now != m)[0]
            hp, ym = fit_grid(X[tr], y[tr], alpha[tr])
            mu[te] = gp_predict(X[tr], y[tr], alpha[tr], X[te], hp, ym)
        return mu

    muA = predict("A"); muB = predict("B")
    out = {}
    for name, mu in [("A_nodonor", muA), ("B_sibling", muB)]:
        el = np.abs(mu - y); ew = np.abs(win - y)
        d, lo, hi, n = pboot(el[test_mask], ew[test_mask])
        tag = "LEARNED WINS" if hi < 0 else ("within better" if lo > 0 else "n.s. (tie)")
        print(f"[witness] {name:11} learnMAE={np.nanmean(el[test_mask]):.3f} withinMAE={np.nanmean(ew[test_mask]):.3f} "
              f"delta={d:+.4f} [{lo:+.4f},{hi:+.4f}] -> {tag}")
        out[name] = dict(delta=d, lo=lo, hi=hi, n=n, learned_mae=float(np.nanmean(el[test_mask])),
                         within_mae=float(np.nanmean(ew[test_mask])), verdict=tag)
    # sibling helps? (B_err - A_err) < 0
    d, lo, hi, n = pboot(np.abs(muB - y)[test_mask], np.abs(muA - y)[test_mask])
    print(f"[witness] sibling_vs_nodonor (B_err-A_err) mean={d:+.4f} [{lo:+.4f},{hi:+.4f}] "
          f"-> {'B beats A' if hi<0 else ('B worse' if lo>0 else 'n.s.')}")
    out["sibling_vs_nodonor"] = dict(delta=d, lo=lo, hi=hi, n=n)
    # GLP1 recentering
    glp = "aact_diabetesme_glucagon-l"; tg = test[glp]; yg = y[tg]
    out["glp1"] = dict(true_mean=float(yg.mean()),
                       A_post=float(muA[tg].mean()), A_mae=float(np.mean(np.abs(muA[tg] - yg))),
                       B_post=float(muB[tg].mean()), B_mae=float(np.mean(np.abs(muB[tg] - yg))),
                       within_mae=float(np.mean(np.abs(win[tg] - yg))))
    print(f"[witness] GLP1 true={yg.mean():+.2f}  A_post={muA[tg].mean():+.2f}(MAE {out['glp1']['A_mae']:.2f})  "
          f"B_post={muB[tg].mean():+.2f}(MAE {out['glp1']['B_mae']:.2f})  within MAE={out['glp1']['within_mae']:.2f}")
    json.dump(out, open(HERE / "donor_ceiling_witness.json", "w"), indent=2)
    print("wrote donor_ceiling_witness.json")


if __name__ == "__main__":
    main()
