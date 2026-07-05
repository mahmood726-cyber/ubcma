"""INDEPENDENT witness for cold_transfer.py -- a from-scratch reimplementation that
does NOT import field_learned or field. It reads the SAME node CSVs, rebuilds the
combined LOR block, and recomputes the two load-bearing numbers:

  (i)  the pooled COLD leave-one-MA-out delta  MAE(learned_cold) - MAE(within_MA)  on the
       AACT rows, and its paired-bootstrap CI; and
  (ii) the within-MA baseline.

Independent choices (deliberately different implementation, same math contract):
  - GP: zero-mean GP with an ARD-RBF over [std year, std log-precision] PLUS a
    Hamming match kernel over (specialty, ma), heteroscedastic noise se^2. Hyper-params
    fit by a coarse-to-fine grid on the negative log marginal likelihood (NOT L-BFGS),
    so the optimiser is independent of the primary engine.
  - within-MA: inverse-variance (precision) weighted mean of the target's same-MA
    siblings, year-Gaussian down-weighted (bw=1 SD), leave-one-out -- recomputed here.

If this witness agrees with cold_transfer_results.json in SIGN and rough magnitude of the
pooled cold delta, the headline is cross-engine confirmed. Emits cold_transfer_witness.json.
"""
from __future__ import annotations
import sys, json, functools
from pathlib import Path
import numpy as np
import pandas as pd

print = functools.partial(print, flush=True)   # ASCII-only; flush so a kill never loses output
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from corpus import load_corpus   # only used to read the SAME corpus LOR nodes; no field/field_learned

Z90 = 1.6448536269514722


def stdz(x):
    x = np.asarray(x, float)
    m = np.isfinite(x)
    o = np.zeros_like(x)
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
    """Independent optimiser: coarse-to-fine random+grid search on the NLML."""
    ymean = ytr.mean(); yc = ytr - ymean
    sf2_0 = max(np.var(yc), 1e-3)
    grid_l = [0.5, 1.5, 4.0]
    best = (None, np.inf)
    for lyr in grid_l:
        for llp in grid_l:
            for lsp in [0.7, 2.0, 5.0]:
                for lma in [0.5, 1.5, 5.0]:
                    hp = (sf2_0, lyr, llp, lsp, lma, 1e-2)
                    f = nlml(Xtr, yc, alpha, hp)
                    if f < best[1]:
                        best = (hp, f)
    # refine sf2 + nugget around the winner
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
    mu = Ks.T @ (Kinv @ (ytr - ymean)) + ymean
    return mu


def within_ma(df, i, yz):
    """Leave-one-out precision-weighted mean of target i's same-MA siblings, with a
    year-Gaussian (bw=1 SD) down-weight relative to the target (neutral when year missing).
    df has a RangeIndex so global index == positional index. yz = std year over the block."""
    t = df.iloc[i]
    same = (df.ma.to_numpy() == t.ma) & (np.arange(len(df)) != i)
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
    m = np.isfinite(a) & np.isfinite(b)
    d = (a - b)[m]
    rng = np.random.default_rng(seed)
    bi = rng.integers(0, len(d), size=(n, len(d)))
    md = d[bi].mean(1)
    return float(d.mean()), float(np.quantile(md, 0.025)), float(np.quantile(md, 0.975)), int(len(d))


def main():
    corpus = load_corpus()
    clor = corpus[corpus.family == "LOR"][["ma", "specialty", "yi", "se", "year"]]
    sl = pd.read_csv(HERE / "aact_coldslice_nodes.csv")
    aact = sl[sl.corpus_specialty == 1][["ma", "specialty", "yi", "se", "year"]].copy()
    aact["year"] = pd.to_numeric(aact["year"], errors="coerce")
    df = pd.concat([clor, aact], ignore_index=True).reset_index(drop=True)
    aact_mas = sorted(aact.ma.unique())
    ama = df.ma.isin(aact_mas).to_numpy()
    y = df["yi"].to_numpy(float)
    X = features(df)
    alpha = df["se"].to_numpy(float) ** 2
    print(f"[witness] combined LOR: {len(df)} nodes / {df.ma.nunique()} MAs; AACT {ama.sum()} / {len(aact_mas)}")

    # cold LOMO learned
    mu_cold = np.full(len(df), np.nan)
    ma = df.ma.to_numpy()
    for m in aact_mas:
        te = np.where(ma == m)[0]; tr = np.where(ma != m)[0]
        hp, ym = fit_grid(X[tr], y[tr], alpha[tr])
        mu_cold[te] = gp_predict(X[tr], y[tr], alpha[tr], X[te], hp, ym)

    # within-MA
    yz = stdz(df["year"].to_numpy(float))
    win = np.full(len(df), np.nan)
    for i in np.where(ama)[0]:
        win[i] = within_ma(df, i, yz)

    el = np.abs(mu_cold - y); ew = np.abs(win - y)
    d, lo, hi, npair = pboot(el[ama], ew[ama])
    tag = "LEARNED WINS" if hi < 0 else ("within better" if lo > 0 else "n.s. (tie)")
    print(f"[witness] COLD LOMO pooled: learned MAE={np.nanmean(el[ama]):.4f} "
          f"within MAE={np.nanmean(ew[ama]):.4f} delta={d:+.4f} [{lo:+.4f},{hi:+.4f}] n={npair} -> {tag}")
    out = dict(n=npair, learned_mae=float(np.nanmean(el[ama])), within_mae=float(np.nanmean(ew[ama])),
               delta=d, lo=lo, hi=hi, verdict=tag)
    json.dump(out, open(HERE / "cold_transfer_witness.json", "w"), indent=2)
    print("wrote cold_transfer_witness.json")


if __name__ == "__main__":
    main()
