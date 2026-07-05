"""INDEPENDENT witness for conflict_discount.py -- from-scratch reimplementation that
does NOT import field_learned, field, or cold_transfer. It reads the SAME node CSVs and
independently re-derives the load-bearing NEW number:

  the pooled DEPLOYABLE conflict-aware fused delta  MAE(fuse_discount) - MAE(within_MA)
  on the cold AACT rows, and its paired-bootstrap CI.

Everything is reimplemented with independent choices (same math contract):
  - GP cold LOMO: ARD-RBF over [std year, std log-prec] + Hamming (specialty, ma),
    heteroscedastic se^2 noise, coarse-to-fine GRID NLML optimiser (not L-BFGS).
    Also returns the GP predictive sd (se_p) for the fusion.
  - within-MA: precision-weighted year-Gaussian pool of the target's same-MA siblings;
    se0 = sqrt(1/sum precision-weights) (independent SE choice, not the primary's within+between).
  - power prior: a0 = exp(-Q/2), Q = (within-cold)^2/(se0^2+se_p^2); precision fusion
    mu = (p_own*within + a0/se_p^2 * cold)/(p_own + a0/se_p^2), p_own = 1/se0^2.

Agreement in SIGN + rough magnitude with conflict_discount_results.json => the deployable
conflict-aware headline is cross-engine confirmed. Emits conflict_discount_witness.json.
"""
from __future__ import annotations
import sys, json, functools
from pathlib import Path
import numpy as np
import pandas as pd

print = functools.partial(print, flush=True)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from corpus import load_corpus   # only to read the SAME corpus LOR nodes


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
    gl = [0.5, 1.5, 4.0]
    best = (None, np.inf)
    for lyr in gl:
        for llp in gl:
            for lsp in [0.7, 2.0, 5.0]:
                for lma in [0.5, 1.5, 5.0]:
                    hp = (sf2_0, lyr, llp, lsp, lma, 1e-2)
                    f = nlml(Xtr, yc, alpha, hp)
                    if f < best[1]:
                        best = (hp, f)
    hp0 = best[0]
    for sf2 in [0.3 * hp0[0], hp0[0], 3 * hp0[0]]:
        for nug in [1e-3, 1e-2, 1e-1]:
            hp = (sf2, hp0[1], hp0[2], hp0[3], hp0[4], nug)
            f = nlml(Xtr, yc, alpha, hp)
            if f < best[1]:
                best = (hp, f)
    return best[0], ymean


def gp_predict(Xtr, ytr, alpha, Xte, hp, ymean):
    """returns (mu, sd) -- predictive mean AND sd (sd needed for fusion)."""
    sf2, lyr, llp, lsp, lma, nug = hp
    K = kernel(Xtr, Xtr, sf2, lyr, llp, lsp, lma) + np.diag(alpha + nug)
    Ks = kernel(Xtr, Xte, sf2, lyr, llp, lsp, lma)
    Kinv = np.linalg.inv(K)
    mu = Ks.T @ (Kinv @ (ytr - ymean)) + ymean
    var = sf2 - np.einsum("ij,ij->j", Ks, Kinv @ Ks)
    return mu, np.sqrt(np.maximum(var, 1e-9))


def within_ma(df, i, yz):
    """LOO precision+year-Gaussian pool; returns (mean, se0=sqrt(1/sum w))."""
    t = df.iloc[i]
    same = (df.ma.to_numpy() == t.ma) & (np.arange(len(df)) != i)
    if same.sum() == 0:
        return np.nan, np.nan
    y = df["yi"].to_numpy(float)[same]; se = df["se"].to_numpy(float)[same]
    w = 1.0 / np.maximum(se ** 2, 1e-9)
    tyz = yz[i]
    if np.isfinite(tyz):
        yzs = yz[same]
        w = w * np.where(np.isfinite(yzs), np.exp(-0.5 * (yzs - tyz) ** 2), 1.0)
    mu = float((w * y).sum() / w.sum())
    se0 = float(np.sqrt(1.0 / w.sum()))
    return mu, se0


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
    X = features(df); alpha = df["se"].to_numpy(float) ** 2
    ma = df.ma.to_numpy()
    print(f"[witness] LOR block {len(df)} nodes; AACT {ama.sum()}/{len(aact_mas)}")

    mu_cold = np.full(len(df), np.nan); sd_cold = np.full(len(df), np.nan)
    for m in aact_mas:
        te = np.where(ma == m)[0]; tr = np.where(ma != m)[0]
        hp, ym = fit_grid(X[tr], y[tr], alpha[tr])
        mm, ss = gp_predict(X[tr], y[tr], alpha[tr], X[te], hp, ym)
        mu_cold[te] = mm; sd_cold[te] = ss

    yz = stdz(df["year"].to_numpy(float))
    win = np.full(len(df), np.nan); win_sd = np.full(len(df), np.nan)
    for i in np.where(ama)[0]:
        win[i], win_sd[i] = within_ma(df, i, yz)

    # independent power-prior fusion
    fused = np.full(len(df), np.nan)
    for i in np.where(ama)[0]:
        y0, se0, mp, sp = win[i], win_sd[i], mu_cold[i], sd_cold[i]
        if not (np.isfinite(mp) and np.isfinite(sp) and sp > 0 and np.isfinite(y0) and se0 > 0):
            fused[i] = y0; continue
        Q = (y0 - mp) ** 2 / (se0 ** 2 + sp ** 2)
        a0 = float(np.clip(np.exp(-0.5 * Q), 0.0, 1.0))
        p_own = 1.0 / se0 ** 2; p_pri = a0 / sp ** 2
        fused[i] = (p_own * y0 + p_pri * mp) / (p_own + p_pri)

    ef = np.abs(fused - y); ew = np.abs(win - y); ec = np.abs(mu_cold - y)
    dcold, lcold, hcold, _ = pboot(ec[ama], ew[ama])
    d, lo, hi, npair = pboot(ef[ama], ew[ama])
    tag = "BEATS within" if hi < 0 else ("worse than within" if lo > 0 else "TIE (safe)")
    print(f"[witness] raw_cold  delta={dcold:+.4f} [{lcold:+.4f},{hcold:+.4f}]")
    print(f"[witness] fuse_disc MAE={np.nanmean(ef[ama]):.4f} within={np.nanmean(ew[ama]):.4f} "
          f"delta={d:+.4f} [{lo:+.4f},{hi:+.4f}] n={npair} -> {tag}")
    out = dict(n=npair, raw_cold_delta=dcold, raw_cold_lo=lcold, raw_cold_hi=hcold,
               fused_mae=float(np.nanmean(ef[ama])), within_mae=float(np.nanmean(ew[ama])),
               fused_delta=d, fused_lo=lo, fused_hi=hi, verdict=tag)
    json.dump(out, open(HERE / "conflict_discount_witness.json", "w"), indent=2)
    print("wrote conflict_discount_witness.json")


if __name__ == "__main__":
    main()
