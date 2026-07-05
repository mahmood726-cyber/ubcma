"""THIRD, GP-FREE witness for donor_ceiling.py -- a Nadaraya-Watson kernel-weighted
average (a DIFFERENT estimator family from the GP) over the SAME leakage-free features.
Confirms the mechanism is not a GP-fitting artefact: if a plain feature-routed average
ALSO cannot recentre the held-out GLP1 MA when a level-matched donor is injected, the
ceiling is intrinsic to feature-based cold routing, not to the GP optimiser.

Predictor (closed-form, no hyper-param fit):
  mu(x*) = sum_i w_i y_i / sum_i w_i,
  w_i = precision_i * exp(-0.5[(dyr/hyr)^2 + (dlp/hlp)^2]) * s^{1[spec mismatch]} * m^{1[ma mismatch]}
with bandwidths hyr=hlp=1 (std units), specialty-mismatch factor s=0.3, ma-mismatch m=0.5.
These are fixed a priori (not tuned) -- the point is the QUALITATIVE routing behaviour, not a
matched MAE. Reports GLP1 recentering and pooled A-vs-B on the same test-halves.

Emits donor_ceiling_witness_nw.json.
"""
from __future__ import annotations
import sys, json, functools
from pathlib import Path
import numpy as np
import pandas as pd

print = functools.partial(print, flush=True)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from corpus import load_corpus

SPLIT_SEED = 20260705
HYR = HLP = 1.0
SPEC_MISS = 0.3      # down-weight cross-specialty
MA_MISS = 0.5        # down-weight cross-MA (ma-term analogue; fires equally vs all non-self MAs)


def stdz(x):
    x = np.asarray(x, float); m = np.isfinite(x); o = np.zeros_like(x)
    if m.sum() >= 2 and np.nanstd(x[m]) > 1e-9:
        o[m] = (x[m] - np.nanmean(x[m])) / np.nanstd(x[m])
    return o


def main():
    corpus = load_corpus()
    clor = corpus[corpus.family == "LOR"][["ma", "specialty", "yi", "se", "year"]]
    sl = pd.read_csv(HERE / "aact_coldslice_nodes.csv")
    aact = sl[sl.corpus_specialty == 1][["ma", "specialty", "yi", "se", "year"]].copy()
    aact["year"] = pd.to_numeric(aact["year"], errors="coerce")
    df = pd.concat([clor, aact], ignore_index=True).reset_index(drop=True)
    aact_mas = sorted(aact.ma.unique())
    y = df["yi"].to_numpy(float)
    se = df["se"].to_numpy(float)
    yr = stdz(df["year"].to_numpy(float))
    lp = np.log(np.maximum(1.0 / se ** 2, 1e-12)); lp = (lp - lp.mean()) / (lp.std() + 1e-9)
    spec = df["specialty"].to_numpy()
    prec = 1.0 / np.maximum(se ** 2, 1e-9)

    rng = np.random.default_rng(SPLIT_SEED)
    ma0 = df.ma.to_numpy().copy()
    donor, test = {}, {}
    for m in aact_mas:
        idx = np.where(ma0 == m)[0]; perm = rng.permutation(idx); h = len(perm) // 2
        test[m] = np.sort(perm[:h]); donor[m] = np.sort(perm[h:])
    test_mask = np.zeros(len(df), bool)
    for m in aact_mas:
        test_mask[test[m]] = True

    def nw_predict(sibling):
        ma_lab = ma0.copy().astype(object)
        if sibling:
            for m in aact_mas:
                ma_lab[donor[m]] = m + "__sib"
        mu = np.full(len(df), np.nan)
        for m in aact_mas:
            for i in test[m]:
                if sibling:
                    tr = np.where((ma_lab != m))[0]                       # donor(m__sib) IN train
                else:
                    tr = np.where((ma_lab != m) & (ma_lab != m + "__sib"))[0]  # hold out all of m
                dyr = (yr[tr] - yr[i]) ** 2
                dlp = (lp[tr] - lp[i]) ** 2
                kern = np.exp(-0.5 * (dyr / HYR ** 2 + dlp / HLP ** 2))
                kern = kern * np.where(spec[tr] == spec[i], 1.0, SPEC_MISS)
                kern = kern * np.where(ma_lab[tr] == ma_lab[i], 1.0, MA_MISS)  # never matches (i held out)
                w = prec[tr] * kern
                mu[i] = float((w * y[tr]).sum() / w.sum())
        return mu

    muA = nw_predict(False); muB = nw_predict(True)
    # within-MA (LOO precision-weighted, full MA)
    win = np.full(len(df), np.nan)
    for m in aact_mas:
        for i in test[m]:
            sib = (ma0 == m) & (np.arange(len(df)) != i)
            w = prec[sib]
            win[i] = float((w * y[sib]).sum() / w.sum())

    def dstat(mu):
        el = np.abs(mu - y)[test_mask]; ew = np.abs(win - y)[test_mask]
        return float(el.mean()), float(ew.mean()), float(el.mean() - ew.mean())

    aA = dstat(muA); aB = dstat(muB)
    glp = "aact_diabetesme_glucagon-l"; tg = test[glp]; yg = y[tg]
    out = dict(
        A_nodonor=dict(learned_mae=aA[0], within_mae=aA[1], delta=aA[2]),
        B_sibling=dict(learned_mae=aB[0], within_mae=aB[1], delta=aB[2]),
        glp1=dict(true_mean=float(yg.mean()), A_post=float(muA[tg].mean()), A_mae=float(np.mean(np.abs(muA[tg]-yg))),
                  B_post=float(muB[tg].mean()), B_mae=float(np.mean(np.abs(muB[tg]-yg))),
                  within_mae=float(np.mean(np.abs(win[tg]-yg)))))
    print(f"[NW witness] A_nodonor delta={aA[2]:+.4f} (learnMAE {aA[0]:.3f})   B_sibling delta={aB[2]:+.4f} (learnMAE {aB[0]:.3f})")
    print(f"[NW witness] GLP1 true={yg.mean():+.2f}  A_post={muA[tg].mean():+.2f}  B_post={muB[tg].mean():+.2f}  "
          f"(within MAE {out['glp1']['within_mae']:.2f})")
    print(f"[NW witness] adding {len(donor[glp])} donor nodes at mean {y[donor[glp]].mean():+.2f} moved GLP1 posterior "
          f"by {muB[tg].mean()-muA[tg].mean():+.2f} toward true {yg.mean():+.2f} -> "
          f"{'recovers' if muB[tg].mean()>0.5*yg.mean() else 'DOES NOT recover'}")
    json.dump(out, open(HERE / "donor_ceiling_witness_nw.json", "w"), indent=2)
    print("wrote donor_ceiling_witness_nw.json")


if __name__ == "__main__":
    main()
