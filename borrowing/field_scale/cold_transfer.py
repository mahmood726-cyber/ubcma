"""COLD out-of-corpus transfer test: does the learned-kernel borrowing field beat
within-MA borrowing on a FRESH registry `ma` it has NEVER trained on?

This runs the open probe designed in AACT_SLICE_NEXTSTEP.md. Unlike the corpus-EXPANSION
test (`aact_run_ext.py`), which adds AACT MAs to the corpus and scores by RANDOM k-fold --
so an AACT trial's own same-MA siblings sit in the training folds and the GP's `ma`-match
kernel term still fires -- here each target AACT `ma` is held out ENTIRELY (leave-one-MA-out).
On a held-out `ma` the GP cannot use its `ma`-kernel term, so it must generalise via
`specialty` + log-precision + year alone. That is the genuine external-validity question.

Comparators (all reuse the COMMITTED, unchanged machinery):
  - learned_cold   : field_learned GP trained on (corpus LOR + OTHER AACT MAs), target MA
                     fully held out, cross-predicted. Frozen feature transform on the full block.
  - learned_corpus : GP trained on the corpus LOR family ONLY (no AACT at all) -> predict every
                     AACT row. Purest transfer robustness variant.
  - learned_warm   : field_learned.predict_kfold_corpus on the expanded block (random k-fold,
                     ma-term fires) restricted to AACT rows -- the aact_run_ext regime, shown
                     here to DECOMPOSE how much the ma-term crutch was worth.
  - within_MA      : field.predict 'withinMA_rel' -- each AACT trial from its OWN same-MA
                     siblings (the exact headline within-MA comparator).
  - scrambled_cold : learned_cold with (ma,specialty) labels permuted within the LOR block
                     (negative control: real relevance structure must beat scrambled).

Truth-first: an honest null (cold kernel ties or loses to within-MA) is an ACCEPTABLE and
informative outcome -- it bounds the committed headline to in-corpus reconstruction.

Run:  python borrowing/field_scale/cold_transfer.py
"""
from __future__ import annotations
import sys, json, functools
from pathlib import Path
import numpy as np
import pandas as pd

# ASCII-only output; force per-line flush so a timeout/kill never loses the log.
print = functools.partial(print, flush=True)

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from corpus import load_corpus                      # noqa: E402  (committed, unchanged)
from field import prep, predict as field_predict    # noqa: E402  (committed, unchanged)
import field_learned as fl                           # noqa: E402  (committed, unchanged)

# Warm-decomposition seeds/folds kept modest: this is a SECONDARY sanity number (it
# reproduces the aact_run_ext.py ma-term-fires regime), not the headline, so it does not
# need the 5-seed/10-fold precision of the committed corpus benchmark.
SEEDS = (0, 1, 2)
WARM_FOLDS = 5
Z90 = 1.6448536269514722


def pboot(a, b, n=5000, seed=7):
    """paired bootstrap mean(a-b) with 95% CI; negative => a smaller error (a better)."""
    m = np.isfinite(a) & np.isfinite(b)
    d = (a - b)[m]
    if len(d) < 2:
        return np.nan, np.nan, np.nan, int(len(d))
    rng = np.random.default_rng(seed)
    bi = rng.integers(0, len(d), size=(n, len(d)))
    md = d[bi].mean(1)
    return float(d.mean()), float(np.quantile(md, 0.025)), float(np.quantile(md, 0.975)), int(len(d))


def gp_cross_predict(block, X, tr_idx, te_idx):
    """Train the committed grouped-ARD GP on block.iloc[tr_idx] (features X[tr_idx]) and
    cross-predict rows te_idx. Frozen transform X is shared so specialty/ma codes and the
    two standardised columns are IDENTICAL across train/test (same guarantee as
    field_learned.predict_kfold). Returns (mu, sd) for te_idx."""
    st = fl.gp_fit(block.iloc[tr_idx], X=X[tr_idx])
    theta, ymean = st["theta"], st["ymean"]
    Ks = fl._kmat(fl._dist_cross(st["X"], X[te_idx]), theta)     # (n_tr, n_te)
    a = st["Kinv"] @ st["yc"]
    mu = Ks.T @ a + ymean
    sf2 = np.exp(theta[0])
    v = st["Kinv"] @ Ks
    var = sf2 - np.einsum("ij,ij->j", Ks, v)
    return mu, np.sqrt(np.maximum(var, 1e-9))


def cold_lomo(block, aact_mas, X=None):
    """Leave-one-MA-out cold prediction of every AACT row. For each AACT ma m: train on
    all LOR rows with ma != m, cross-predict m's rows. block is a prepped LOR-only frame
    with a RangeIndex. Returns (mu, sd) aligned to block (NaN on non-AACT rows)."""
    if X is None:
        X = fl.build_features(block)
    n = len(block)
    mu = np.full(n, np.nan); sd = np.full(n, np.nan)
    ma = block["ma"].to_numpy()
    for m in aact_mas:
        te = np.where(ma == m)[0]
        tr = np.where(ma != m)[0]
        mm, ss = gp_cross_predict(block, X, tr, te)
        mu[te] = mm; sd[te] = ss
    return mu, sd


def within_ma_pred(df):
    out = np.full(len(df), np.nan)
    for i in range(len(df)):
        m, _ = field_predict(df, i, "withinMA_rel")
        out[i] = m
    return out


def report_delta(label, learned, within, y, mask, out=None):
    el = np.abs(learned - y); ew = np.abs(within - y)
    m = mask & np.isfinite(el) & np.isfinite(ew)
    d, lo, hi, npair = pboot(el[m], ew[m])
    tag = "LEARNED WINS" if hi < 0 else ("within better" if lo > 0 else "n.s. (tie)")
    print(f"  [{label:32}] learned MAE={np.nanmean(el[m]):.4f}  within MAE={np.nanmean(ew[m]):.4f}  "
          f"delta={d:+.4f} [{lo:+.4f},{hi:+.4f}] n={npair}  -> {tag}")
    if out is not None:
        out[label] = dict(learned_mae=float(np.nanmean(el[m])), within_mae=float(np.nanmean(ew[m])),
                          delta=d, lo=lo, hi=hi, n=npair, verdict=tag)


def main():
    results = {}
    # ---- build the combined LOR block: corpus LOR family + primary AACT cold slice ----
    corpus = load_corpus()
    corpus_lor = corpus[corpus.family == "LOR"][["ma", "family", "specialty", "yi", "se", "year"]]
    slice_df = pd.read_csv(HERE / "aact_coldslice_nodes.csv")
    aact = slice_df[slice_df.corpus_specialty == 1][["ma", "family", "specialty", "yi", "se", "year"]].copy()
    aact["year"] = pd.to_numeric(aact["year"], errors="coerce")
    block = prep(pd.concat([corpus_lor, aact], ignore_index=True))   # RangeIndex, yz+prec
    aact_mas = sorted(aact.ma.unique())
    aact_mask = block.ma.isin(aact_mas).to_numpy()
    y = block["yi"].to_numpy(float)
    print(f"combined LOR block: {len(block)} nodes / {block.ma.nunique()} MAs "
          f"(corpus LOR {len(corpus_lor)} / {corpus_lor.ma.nunique()} + AACT {int(aact_mask.sum())} / {len(aact_mas)})")
    print(f"AACT cold MAs: {aact_mas}")
    results["setup"] = dict(block_nodes=len(block), corpus_lor=len(corpus_lor),
                            aact_nodes=int(aact_mask.sum()), aact_mas=aact_mas)

    X = fl.build_features(block)                         # FROZEN transform on the full block

    # within-MA comparator on every AACT row (its own same-MA siblings)
    within = within_ma_pred(block)

    # ---- (1) COLD leave-one-MA-out: target AACT ma fully held out (the headline) ----
    print("\n" + "=" * 78)
    print("(1) COLD leave-one-MA-out: target AACT `ma` NEVER in training (ma-term cannot fire)")
    print("=" * 78)
    mu_cold, sd_cold = cold_lomo(block, aact_mas, X=X)
    report_delta("COLD LOMO (all AACT)", mu_cold, within, y, aact_mask, results)
    # per specialty
    for sp in sorted(aact.specialty.unique()):
        m = aact_mask & (block.specialty == sp).to_numpy()
        report_delta(f"COLD {sp}", mu_cold, within, y, m, results)

    # ---- (2) COLD corpus-only-trained (no AACT in training at all) robustness ----
    print("\n" + "=" * 78)
    print("(2) COLD corpus-only-trained: GP sees ONLY the corpus LOR family, predicts all AACT")
    print("=" * 78)
    corpus_idx = np.where(~aact_mask)[0]
    aact_idx = np.where(aact_mask)[0]
    mu_co, sd_co = gp_cross_predict(block, X, corpus_idx, aact_idx)
    mu_corpus = np.full(len(block), np.nan); sd_corpus = np.full(len(block), np.nan)
    mu_corpus[aact_idx] = mu_co; sd_corpus[aact_idx] = sd_co
    report_delta("COLD corpus-only (all AACT)", mu_corpus, within, y, aact_mask, results)

    # ---- (3) WARM expansion (random k-fold, ma-term fires) for decomposition ----
    print("\n" + "=" * 78)
    print("(3) WARM expansion (random k-fold, ma-term FIRES) -- decomposes the ma-crutch value")
    print("=" * 78)
    mu_warm, sd_warm = fl.predict_kfold_corpus(block, n_folds=WARM_FOLDS, seeds=SEEDS)
    report_delta("WARM kfold (all AACT)", mu_warm, within, y, aact_mask, results)

    # ---- (4) negative control: scrambled-label cold LOMO must lose to the real one ----
    print("\n" + "=" * 78)
    print("(4) NEGATIVE CONTROL: scrambled (ma,specialty) labels, same cold LOMO")
    print("=" * 78)
    scr = block.copy()
    rng = np.random.default_rng(101)
    idx = np.arange(len(block))
    p = rng.permutation(idx)
    scr["ma"] = block["ma"].to_numpy()[p]
    scr["specialty"] = block["specialty"].to_numpy()[p]
    scr = prep(scr)
    Xs = fl.build_features(scr)
    # hold out the SAME physical AACT rows (by position) under scrambled labels
    # Cold LOMO over the REAL AACT ma partition (same physical held-out rows), but with
    # scrambled feature labels -- so the target rows' true relevance structure is destroyed.
    mu_scr = np.full(len(block), np.nan); sd_scr = np.full(len(block), np.nan)
    ma_real = block["ma"].to_numpy()
    for m in aact_mas:
        te = np.where(ma_real == m)[0]
        tr = np.where(ma_real != m)[0]
        mm, ss = gp_cross_predict(scr, Xs, tr, te)
        mu_scr[te] = mm; sd_scr[te] = ss
    report_delta("SCRAMBLED cold (all AACT)", mu_scr, within, y, aact_mask, results)
    d, lo, hi, npair = pboot(np.abs(mu_cold - y)[aact_mask], np.abs(mu_scr - y)[aact_mask])
    tag = "real beats scrambled" if hi < 0 else ("real worse" if lo > 0 else "n.s.")
    print(f"  [real_cold - scrambled_cold           ] delta={d:+.4f} [{lo:+.4f},{hi:+.4f}] n={npair} -> {tag}")
    results["cold_vs_scrambled"] = dict(delta=d, lo=lo, hi=hi, n=npair, verdict=tag)

    # ---- (5) per-MA cold deltas ----
    print("\n" + "=" * 78)
    print("(5) per-MA COLD deltas (learned_cold - within_MA MAE; negative = cold kernel better)")
    print("=" * 78)
    permac = []
    for m in aact_mas:
        mm = (block.ma == m).to_numpy()
        el = np.abs(mu_cold - y)[mm]; ew = np.abs(within - y)[mm]
        sp = block.specialty[mm].iloc[0]
        permac.append(dict(ma=m, specialty=sp, k=int(mm.sum()),
                           learned=float(np.nanmean(el)), within=float(np.nanmean(ew)),
                           delta=float(np.nanmean(el) - np.nanmean(ew))))
        print(f"  {m:34} k={mm.sum():3} spec={sp:18} learned={np.nanmean(el):.3f} "
              f"within={np.nanmean(ew):.3f} delta={np.nanmean(el)-np.nanmean(ew):+.3f}")
    results["per_ma"] = permac
    won = sum(1 for r in permac if r["delta"] < 0)
    print(f"  MAs where cold kernel beat within-MA (point): {won}/{len(permac)}")

    # ---- (6) conformal coverage on cold AACT predictions ----
    print("\n" + "=" * 78)
    print("(6) COLD 90% coverage on AACT rows: model-PI (raw) vs split-conformal")
    print("=" * 78)
    se_t = block["se"].to_numpy(float)
    half_raw = Z90 * np.sqrt(sd_cold ** 2 + se_t ** 2)
    cov_raw = ((mu_cold - half_raw <= y) & (y <= mu_cold + half_raw)).astype(float)
    cov_raw[~np.isfinite(mu_cold)] = np.nan
    # split-conformal on the AACT rows: q = (1-alpha) quantile of the OTHER AACT rows'
    # cold |residual| (conformal calibrated within the held-out family, alpha=0.10)
    res = np.abs(mu_cold - y)[aact_mask]
    gi = np.where(aact_mask)[0]
    half_cf = np.full(len(block), np.nan); cov_cf = np.full(len(block), np.nan)
    for j in range(len(gi)):
        others = np.delete(res, j)
        others = others[np.isfinite(others)]
        if len(others) < 1:
            continue
        q = np.quantile(others, 0.90, method="higher")
        half_cf[gi[j]] = q
        cov_cf[gi[j]] = float(res[j] <= q)
    craw = float(np.nanmean(cov_raw[aact_mask])); wraw = float(np.nanmean((2 * half_raw)[aact_mask]))
    ccf = float(np.nanmean(cov_cf[aact_mask])); wcf = float(np.nanmean((2 * half_cf)[aact_mask]))
    print(f"  AACT cold rows (n={int(aact_mask.sum())}): raw cover={craw:.3f} (w={wraw:.3f}) -> "
          f"conformal cover={ccf:.3f} (w={wcf:.3f})  [nominal 0.90]")
    results["coverage"] = dict(raw_cover=craw, raw_width=wraw, conf_cover=ccf, conf_width=wcf,
                               n=int(aact_mask.sum()))

    json.dump(results, open(HERE / "cold_transfer_results.json", "w"), indent=2)
    print(f"\nwrote {HERE / 'cold_transfer_results.json'}")


if __name__ == "__main__":
    main()
