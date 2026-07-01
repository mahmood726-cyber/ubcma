"""field_rescore_petgate.py -- sweep the (c) PET-gate constant without re-sim.

adaptshrink_petgate = (1-g)*RE + g*calibrated-ensemble, with
g = t1^2/(t1^2 + c), t1 = funnel-asymmetry t-statistic (saved per replicate as
`pet_t1`). Everything needed to recompute it at an arbitrary gate constant c is
already in field2_<tag>_perrep.csv:

  mu_re, hw_re        <- reml_hksj rows
  mu_ens, half_ens    <- adaptshrink_ens rows
  D (between SD)       <- (ens_calib half - ens half) / CALIB_A   (CALIB_A=2)
  t1                   <- pet_t1 column

So we can sweep c, recompute the gated centre + interval, and re-run the exact
field-domination truth-gate. Truth-first: this is a transparent post-hoc sweep on
a single grid -- reported as a curve, not cherry-picked.

Usage:
    PYTHONPATH=src python truth-recovery/field_rescore_petgate.py --tag b1 --sweep
    PYTHONPATH=src python truth-recovery/field_rescore_petgate.py --tag b1 --c 4 --write
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import field_bakeoff as FB  # noqa: E402
import field_bakeoff2 as F2  # noqa: E402

OUT = Path("truth-recovery")
CELL_KEYS = F2.CELL_KEYS
CALIB_A = 2.0


def rebuild(raw, c, name="adaptshrink_petgate_c"):
    key = CELL_KEYS + ["rep"]
    re = raw[raw.method == "reml_hksj"].set_index(key)
    en = raw[raw.method == "adaptshrink_ens"].set_index(key)
    ca = raw[raw.method == "adaptshrink_ens_calib"].set_index(key)
    pg = raw[raw.method == "adaptshrink_petgate"].set_index(key)
    idx = re.index.intersection(en.index).intersection(ca.index).intersection(pg.index)
    re, en, ca, pg = re.loc[idx], en.loc[idx], ca.loc[idx], pg.loc[idx]
    mu_re = re["mu_hat"].to_numpy(); hw_re = (re["ci_high"] - re["ci_low"]).to_numpy() / 2
    mu_en = en["mu_hat"].to_numpy(); hw_en = (en["ci_high"] - en["ci_low"]).to_numpy() / 2
    hw_ca = (ca["ci_high"] - ca["ci_low"]).to_numpy() / 2
    D = np.maximum((hw_ca - hw_en) / CALIB_A, 0.0)
    t1 = pg["pet_t1"].to_numpy()
    ok = en["converged"].to_numpy() & np.isfinite(mu_re) & np.isfinite(t1)
    g = np.where(ok, t1 * t1 / (t1 * t1 + c), 0.0)
    mu = np.where(ok, (1 - g) * mu_re + g * mu_en, mu_re)
    hw = np.where(ok, (1 - g) * hw_re + g * (hw_en + CALIB_A * D), hw_re)
    out = pd.DataFrame(idx.tolist(), columns=key)
    out["method"] = name
    out["true_mu"] = re["true_mu"].to_numpy()
    out["mu_hat"] = mu; out["ci_low"] = mu - hw; out["ci_high"] = mu + hw
    out["converged"] = ok | np.isfinite(mu_re)
    return out


def evaluate(raw, gated, name):
    aug = pd.concat([raw.drop(columns=[c for c in ["pet_t1"] if c in raw.columns]),
                     gated], ignore_index=True)
    orig = FB.CELL_KEYS
    FB.CELL_KEYS = CELL_KEYS
    try:
        score = FB.score_tables(aug)
        pair = FB.bootstrap_pairwise(aug, name)
        dom = FB.field_domination(score, pair, name)
    finally:
        FB.CELL_KEYS = orig
    sc = score[score.method == name]
    return dom, sc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="b1")
    ap.add_argument("--c", type=float, default=4.0)
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    raw = pd.read_csv(OUT / f"field2_{args.tag}_perrep.csv")

    # reference: ens and ens_calib domination on this grid
    orig = FB.CELL_KEYS; FB.CELL_KEYS = CELL_KEYS
    try:
        sc0 = FB.score_tables(raw)
        for ref in ("adaptshrink_ens", "adaptshrink_ens_calib"):
            d = FB.field_domination(sc0, FB.bootstrap_pairwise(raw, ref), ref)
            print(f"  REF {ref:<22} dominates {int(d.dominates_field.sum())}/{len(d)}"
                  f"  tau=.3/.5 high: {int(d[d.tau>=0.3].dominates_field.sum())}/{len(d[d.tau>=0.3])}")
    finally:
        FB.CELL_KEYS = orig

    cs = [1, 2, 4, 9, 16, 36] if args.sweep else [args.c]
    for c in cs:
        gated = rebuild(raw, c)
        dom, sc = evaluate(raw, gated, "adaptshrink_petgate_c")
        nd = int(dom.dominates_field.sum())
        hi = dom[dom.tau >= 0.3]
        print(f"c={c:<4} petgate dominates {nd:>3}/{len(dom)}  "
              f"high-tau(>=.3) {int(hi.dominates_field.sum())}/{len(hi)}  "
              f"mean cov {sc.raw_cov.mean():.3f}")
        if args.write and not args.sweep:
            gated.to_csv(OUT / f"field2_{args.tag}_petgate_c{int(c)}_perrep.csv", index=False)
            dom.to_csv(OUT / f"field2_{args.tag}_domination_petgate_c{int(c)}.csv", index=False)
            print("  wrote rebuilt petgate + domination CSV")


if __name__ == "__main__":
    main()
