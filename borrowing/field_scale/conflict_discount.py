"""CONFLICT-AWARE DISCOUNT on the COLD out-of-corpus transfer regime.

Follow-up to cold_transfer.py (committed 9b52b86). The cold LOMO test found an honest
negative: on a genuinely fresh registry `ma` the RAW cross-MA field loses to within-MA
pooling (Delta=+0.152 [+0.050,+0.263]), and the pooled loss is DOMINATED by one
extreme-level MA (aact_diabetesme_glucagon-l / GLP1: cold MAE 2.48 vs within 0.86,
Delta=+1.62) that cross-MA borrowing cannot recentre.

But cold_transfer.py compared the raw cold GP and within-MA as two SEPARATE predictors.
It never exercised the DEPLOYABLE estimator the method already ships: the adaptive
power-prior fusion `field_learned.conflict_aware_fuse` (Ibrahim-Chen 2000; a0=exp(-Q/2),
Q the standardised prior-data conflict). That fusion combines the target MA's OWN
within-MA evidence (y0,se0) with the cold cross-MA field prior (mu_p,se_p), discounting
the borrowed mass when the field CONFLICTS with local data. Under conflict a0 -> 0 and the
estimator collapses to within-MA -- i.e. it should be STRUCTURALLY SAFE cold: never
materially worse than within-MA, while still borrowing where the field agrees.

This script asks the deployment question the capstone item-4 "Fix" names:
  does the SHIPPED conflict-aware discount make the borrowing field SAFE (tie) or
  BENEFICIAL (win) when deployed on a cold, out-of-corpus MA?

Estimators (all reuse COMMITTED, unchanged machinery -- no new estimator, no tuned param):
  within        : within-MA_rel pool (target MA's own siblings)      = the headline baseline
  raw_cold      : field_learned cold LOMO GP (cross-MA only)          = the honest-negative
  fuse_naive    : precision fusion within (+) cold, a0=1 FIXED         = fusion WITHOUT discount
  fuse_discount : conflict_aware_fuse(within, cold), a0 ADAPTIVE       = the SHIPPED estimator
  fuse_scramco  : conflict_aware_fuse(within, SCRAMBLED cold)          = falsification control

Pre-declared verdicts (truth-first):
  - fuse_discount removes the honest negative  <=> its Delta vs within has CI upper bound <= ~0.
  - STRICT win                                 <=> Delta vs within CI < 0.
  - the discount (not mere fusion) is what protects <=> fuse_naive is HARMED (dragged by GLP1)
    while fuse_discount is not.
  - the field carries real agreement signal <=> fuse_discount(real cold) beats fuse_discount(scrambled).

Run:  python borrowing/field_scale/conflict_discount.py
"""
from __future__ import annotations
import sys, json, functools
from pathlib import Path
import numpy as np
import pandas as pd

print = functools.partial(print, flush=True)

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from corpus import load_corpus                       # noqa: E402 committed, unchanged
from field import prep, predict as field_predict     # noqa: E402 committed, unchanged
import field_learned as fl                            # noqa: E402 committed, unchanged
from cold_transfer import cold_lomo, pboot            # noqa: E402 committed, unchanged

Z90 = 1.6448536269514722
CHI2_95_1 = 3.841458820694124   # (1.96)^2, hard test-then-pool threshold on Q


def within_pred_sd(df):
    """within-MA_rel prediction (mean, predictive sd) for every row -- the exact
    headline within-MA comparator, now KEEPING the sd that cold_transfer discarded."""
    mu = np.full(len(df), np.nan); sd = np.full(len(df), np.nan)
    for i in range(len(df)):
        m, s = field_predict(df, i, "withinMA_rel")
        mu[i] = m; sd[i] = s
    return mu, sd


def fuse(y0, se0, mu_p, se_p, a0_mode="adaptive"):
    """Power-prior fusion of own (y0,se0) with borrowed prior (mu_p,se_p).
    a0_mode: 'adaptive' -> shipped conflict_aware_fuse (a0=exp(-Q/2));
             'naive'    -> a0=1 (no discount); 'hard' -> a0=1[Q<3.84]; 'inv' -> a0=1/(1+Q)."""
    n = len(y0)
    mu = np.full(n, np.nan); a0v = np.full(n, np.nan)
    for i in range(n):
        if not (np.isfinite(mu_p[i]) and np.isfinite(se_p[i]) and se_p[i] > 0
                and np.isfinite(y0[i]) and np.isfinite(se0[i]) and se0[i] > 0):
            mu[i] = y0[i]; a0v[i] = 0.0
            continue
        Q = (y0[i] - mu_p[i]) ** 2 / (se0[i] ** 2 + se_p[i] ** 2)
        if a0_mode == "adaptive":
            # SHIPPED path -- byte-identical result to fl.conflict_aware_fuse(a0=None)
            m, _ = fl.conflict_aware_fuse(y0[i], se0[i], mu_p[i], se_p[i])
            mu[i] = m; a0v[i] = float(np.clip(np.exp(-0.5 * Q), 0.0, 1.0))
            continue
        if a0_mode == "naive":
            a0 = 1.0
        elif a0_mode == "hard":
            a0 = 1.0 if Q < CHI2_95_1 else 0.0
        elif a0_mode == "inv":
            a0 = 1.0 / (1.0 + Q)
        else:
            raise ValueError(a0_mode)
        p_own = 1.0 / se0[i] ** 2
        p_pri = a0 / se_p[i] ** 2
        mu[i] = (p_own * y0[i] + p_pri * mu_p[i]) / (p_own + p_pri)
        a0v[i] = a0
    return mu, a0v


def dvs(label, pred, within, y, mask, out=None, base="within"):
    """paired-bootstrap Delta(|pred-y| - |within-y|); negative => pred beats within."""
    ep = np.abs(pred - y); ew = np.abs(within - y)
    m = mask & np.isfinite(ep) & np.isfinite(ew)
    d, lo, hi, npair = pboot(ep[m], ew[m])
    tag = "BEATS within" if hi < 0 else ("worse than within" if lo > 0 else "TIE (safe)")
    print(f"  [{label:26}] MAE={np.nanmean(ep[m]):.4f}  vs within {np.nanmean(ew[m]):.4f}  "
          f"Delta={d:+.4f} [{lo:+.4f},{hi:+.4f}] n={npair}  -> {tag}")
    if out is not None:
        out[label] = dict(mae=float(np.nanmean(ep[m])), within_mae=float(np.nanmean(ew[m])),
                          delta=d, lo=lo, hi=hi, n=npair, verdict=tag)
    return d, lo, hi


def main():
    R = {}
    # ---- rebuild the EXACT cold-transfer block (identical to cold_transfer.py) ----
    corpus = load_corpus()
    corpus_lor = corpus[corpus.family == "LOR"][["ma", "family", "specialty", "yi", "se", "year"]]
    slice_df = pd.read_csv(HERE / "aact_coldslice_nodes.csv")
    aact = slice_df[slice_df.corpus_specialty == 1][["ma", "family", "specialty", "yi", "se", "year"]].copy()
    aact["year"] = pd.to_numeric(aact["year"], errors="coerce")
    block = prep(pd.concat([corpus_lor, aact], ignore_index=True))
    aact_mas = sorted(aact.ma.unique())
    aact_mask = block.ma.isin(aact_mas).to_numpy()
    y = block["yi"].to_numpy(float)
    print(f"block: {len(block)} nodes, AACT cold {int(aact_mask.sum())}/{len(aact_mas)} MAs")

    X = fl.build_features(block)                          # frozen transform (committed)
    within, within_sd = within_pred_sd(block)             # own siblings (mean+sd)
    mu_cold, sd_cold = cold_lomo(block, aact_mas, X=X)     # cross-MA cold LOMO (committed)

    # scrambled cold for the falsification control (same as cold_transfer step 4)
    scr = block.copy()
    rng = np.random.default_rng(101)
    p = rng.permutation(np.arange(len(block)))
    scr["ma"] = block["ma"].to_numpy()[p]; scr["specialty"] = block["specialty"].to_numpy()[p]
    scr = prep(scr); Xs = fl.build_features(scr)
    mu_scr = np.full(len(block), np.nan); sd_scr = np.full(len(block), np.nan)
    ma_real = block["ma"].to_numpy()
    from cold_transfer import gp_cross_predict
    for m in aact_mas:
        te = np.where(ma_real == m)[0]; tr = np.where(ma_real != m)[0]
        mm, ss = gp_cross_predict(scr, Xs, tr, te); mu_scr[te] = mm; sd_scr[te] = ss

    # ---- fused estimators ----
    fuse_naive, a0_naive = fuse(within, within_sd, mu_cold, sd_cold, "naive")
    fuse_disc,  a0_disc  = fuse(within, within_sd, mu_cold, sd_cold, "adaptive")
    fuse_hard,  a0_hard  = fuse(within, within_sd, mu_cold, sd_cold, "hard")
    fuse_inv,   a0_inv   = fuse(within, within_sd, mu_cold, sd_cold, "inv")
    fuse_scr,   _        = fuse(within, within_sd, mu_scr,  sd_scr,  "adaptive")

    # dump per-row predictions so an EXTERNAL vendor can independently re-derive the
    # power-prior fusion arithmetic (the genuinely new step) from already-verified inputs.
    dump = pd.DataFrame(dict(ma=block.ma.to_numpy(), specialty=block.specialty.to_numpy(),
                             y=y, within=within, within_sd=within_sd, mu_cold=mu_cold,
                             sd_cold=sd_cold, aact=aact_mask))[aact_mask]
    dump.to_csv(HERE / "conflict_discount_rows.csv", index=False)
    print(f"dumped {len(dump)} AACT rows -> conflict_discount_rows.csv")

    print("\n" + "=" * 82)
    print("(1) DEPLOYMENT QUESTION: does the discount make the cold field SAFE / beneficial?")
    print("=" * 82)
    dvs("raw_cold",       mu_cold,    within, y, aact_mask, R)   # the honest negative
    dvs("fuse_naive(a0=1)", fuse_naive, within, y, aact_mask, R) # fusion, no discount
    dvs("fuse_discount",  fuse_disc,  within, y, aact_mask, R)   # SHIPPED estimator
    print("  -- discount-family robustness (pooled Delta vs within must stay <= ~0) --")
    dvs("fuse_hard(Q<3.84)", fuse_hard, within, y, aact_mask, R)
    dvs("fuse_inv(1/(1+Q))", fuse_inv,  within, y, aact_mask, R)

    print("\n" + "=" * 82)
    print("(2) FALSIFICATION: real-cold discount must beat scrambled-cold discount")
    print("=" * 82)
    dvs("fuse_scrambled",  fuse_scr,   within, y, aact_mask, R)
    d, lo, hi, npair = pboot(np.abs(fuse_disc - y)[aact_mask], np.abs(fuse_scr - y)[aact_mask])
    tag = "real beats scrambled" if hi < 0 else ("real worse" if lo > 0 else "n.s.")
    print(f"  [fuse_discount(real) - fuse_discount(scrambled)] Delta={d:+.4f} [{lo:+.4f},{hi:+.4f}]"
          f" n={npair} -> {tag}")
    R["disc_real_vs_scrambled"] = dict(delta=d, lo=lo, hi=hi, n=npair, verdict=tag)

    print("\n" + "=" * 82)
    print("(3) PER-MA: mean a0 (discount fires?), fused vs within (mechanism on GLP1)")
    print("=" * 82)
    perma = []
    for m in aact_mas:
        mm = (block.ma == m).to_numpy()
        ef = np.abs(fuse_disc - y)[mm]; ew = np.abs(within - y)[mm]; ec = np.abs(mu_cold - y)[mm]
        rec = dict(ma=m, specialty=block.specialty[mm].iloc[0], k=int(mm.sum()),
                   a0=float(np.nanmean(a0_disc[mm])), cold_mae=float(np.nanmean(ec)),
                   within_mae=float(np.nanmean(ew)), fused_mae=float(np.nanmean(ef)),
                   fused_minus_within=float(np.nanmean(ef) - np.nanmean(ew)))
        perma.append(rec)
        print(f"  {m:34} k={mm.sum():3} a0={rec['a0']:.3f}  cold={rec['cold_mae']:.3f} "
              f"within={rec['within_mae']:.3f} fused={rec['fused_mae']:.3f} "
              f"(fused-within={rec['fused_minus_within']:+.3f})")
    R["per_ma"] = perma
    print(f"  GLP1 check: cold-catastrophe recentred? "
          f"{[r for r in perma if 'glucagon' in r['ma']]}")

    # ---- conformal coverage of the shipped fused estimator on cold rows ----
    se_t = block["se"].to_numpy(float)
    res = np.abs(fuse_disc - y)[aact_mask]; gi = np.where(aact_mask)[0]
    cov_cf = np.full(len(block), np.nan)
    for j in range(len(gi)):
        others = res[np.isfinite(res)]; others = np.delete(others, j) if len(others) > 1 else others
        if len(others) < 1:
            continue
        q = np.quantile(others, 0.90, method="higher"); cov_cf[gi[j]] = float(res[j] <= q)
    R["conformal_cover_fused"] = float(np.nanmean(cov_cf[aact_mask]))
    print(f"\n  fused split-conformal cold coverage @0.90 = {R['conformal_cover_fused']:.3f}")

    json.dump(R, open(HERE / "conflict_discount_results.json", "w"), indent=2)
    print(f"\nwrote {HERE / 'conflict_discount_results.json'}")


if __name__ == "__main__":
    main()
