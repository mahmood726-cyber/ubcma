"""field_rescore_interval.py -- (a) selection-strength-aware interval inflation.

adaptshrink_ens under-covers deployably in 10/54 cells (null+step where the centre
over-corrects; tau=0.3+small-k). Its model-averaging interval (within+between,
t_{m-1}) is too narrow exactly when the ensemble members DISAGREE -- which is the
signature of strong bias-correction / high uncertainty. So we widen the interval
by a global, data-driven amount proportional to member disagreement:

    hw' = hw_ens * (1 + a * D / hw_ens) = hw_ens + a * D
    where D = between-member SD (sqrt of the model-averaging between variance).

This is PURELY an interval change rescored from the saved per-rep member estimates
(ubcma, pet_peese, trim&fill). Therefore:
  * MCIW0 (matched-coverage CONSTANT width, point-error only) is UNCHANGED -> every
    pairwise verdict and the cells-dominated ranking are provably unaffected by the
    point estimator; only the deployable raw-coverage gate can change.
  * Because 5 non-dominated cells fail ONLY the coverage gate, fixing coverage can
    only INCREASE the dominated count, never decrease it.

The inflation constant `a` is GLOBAL (one value, not per-cell) and chosen to lift
the under-covering cells to ~nominal with minimal width growth on well-calibrated
cells. We report before/after coverage on the 10 cells + overall + width cost +
dominated count, and a flat-multiplier baseline for comparison.

Usage:
    PYTHONPATH=src python truth-recovery/field_rescore_interval.py --tag v1 --sweep
    PYTHONPATH=src python truth-recovery/field_rescore_interval.py --tag v1 --a 1.5 --write
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import field_bakeoff as F  # noqa: E402

Z975 = 1.959963984540054
OUT = Path("truth-recovery")
CELL_KEYS = F.CELL_KEYS
ENS_MEMBERS = ("ubcma", "pet_peese", "trim_and_fill")


def _member_spread(raw: pd.DataFrame) -> pd.DataFrame:
    """Per (cell,rep): between-member SD D of the ensemble members (saved mu's)."""
    key = CELL_KEYS + ["rep"]
    tabs = {m: raw[raw.method == m].set_index(key) for m in ENS_MEMBERS}
    idx = None
    for t in tabs.values():
        idx = t.index if idx is None else idx.intersection(t.index)
    mus = np.column_stack([tabs[m].loc[idx, "mu_hat"].to_numpy() for m in ENS_MEMBERS])
    ses = np.column_stack([
        ((tabs[m].loc[idx, "ci_high"].to_numpy() - tabs[m].loc[idx, "ci_low"].to_numpy())
         / 2.0 / Z975) for m in ENS_MEMBERS])
    # robust weights identical to F._robust_avg
    med = np.median(mus, axis=1, keepdims=True)
    w = 1.0 / (np.square(ses) + np.square(mus - med) + 1e-9)
    ws = w.sum(axis=1, keepdims=True)
    mu = (w * mus).sum(axis=1, keepdims=True) / ws
    between = (w * np.square(mus - mu)).sum(axis=1) / ws.ravel()
    D = np.sqrt(np.maximum(between, 0.0))
    out = pd.DataFrame(idx.tolist(), columns=key)
    out["D"] = D
    return out


def make_inflated(raw, a, mode="disagree", flat=1.0):
    """Return new adaptshrink_ens rows with inflated CI (center unchanged)."""
    ens = raw[raw.method == "adaptshrink_ens"].copy()
    key = CELL_KEYS + ["rep"]
    mu = ens["mu_hat"].to_numpy()
    hw = (ens["ci_high"].to_numpy() - ens["ci_low"].to_numpy()) / 2.0
    if mode == "flat":
        hw2 = hw * flat
    else:
        sp = _member_spread(raw).set_index(key)
        D = ens.set_index(key).index.map(lambda k: sp["D"].get(k, 0.0))
        D = np.asarray(D, dtype=float)
        hw2 = hw + a * D
    ens = ens.copy()
    ens["ci_low"] = mu - hw2
    ens["ci_high"] = mu + hw2
    ens["method"] = "adaptshrink_ens_infl"
    return ens


def evaluate(raw, ens_infl):
    aug = pd.concat([raw, ens_infl], ignore_index=True)
    score = F.score_tables(aug)
    pair = F.bootstrap_pairwise(aug, "adaptshrink_ens_infl")
    dom = F.field_domination(score, pair, "adaptshrink_ens_infl")
    sc = score[score.method == "adaptshrink_ens_infl"]
    return score, pair, dom, sc


UNDER_CELLS = [  # the 10 raw_cov<0.80 cells from v1 (for before/after)
    (0.0, 0.1, 10, "step"), (0.0, 0.1, 40, "step"), (0.0, 0.3, 10, "step"),
    (0.0, 0.3, 40, "step"), (0.2, 0.3, 10, "copas"), (0.2, 0.3, 10, "none"),
    (0.2, 0.3, 10, "step"), (0.5, 0.3, 10, "copas"), (0.5, 0.3, 10, "none"),
    (0.5, 0.3, 10, "step"),
]


def _cov_on_under(score, method):
    s = score[score.method == method]
    vals = []
    for mu, tau, k, mech in UNDER_CELLS:
        r = s[(s.mu == mu) & (s.tau == tau) & (s.k == k) & (s.mechanism == mech)]
        if len(r):
            vals.append(float(r.iloc[0]["raw_cov"]))
    return vals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="v1")
    ap.add_argument("--a", type=float, default=1.5)
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    raw = pd.read_csv(OUT / f"field_{args.tag}_perrep.csv")

    base_score = F.score_tables(raw)
    base_pair = F.bootstrap_pairwise(raw, "adaptshrink_ens")
    base_dom = F.field_domination(base_score, base_pair, "adaptshrink_ens")
    base_dom_n = int(base_dom["dominates_field"].sum())
    base_cov = _cov_on_under(base_score, "adaptshrink_ens")
    base_w = float(base_score[base_score.method == "adaptshrink_ens"]["raw_width"].mean())
    print(f"BASELINE adaptshrink_ens: dominates {base_dom_n}/54, "
          f"mean raw_cov(10 under-cells)={np.mean(base_cov):.3f}, mean raw_width={base_w:.4f}")

    if args.sweep:
        print("\n-- disagreement-scaled inflation hw' = hw + a*D --")
        for a in [0.5, 1.0, 1.5, 2.0, 3.0]:
            inf = make_inflated(raw, a, mode="disagree")
            sc, _, dom, scm = evaluate(raw, inf)
            cov10 = _cov_on_under(sc, "adaptshrink_ens_infl")
            print(f"  a={a:<4} dominates {int(dom.dominates_field.sum()):>2}/54  "
                  f"under-cells cov {np.mean(cov10):.3f} (min {np.min(cov10):.3f})  "
                  f"overall cov {scm.raw_cov.mean():.3f}  width {scm.raw_width.mean():.4f} "
                  f"(x{scm.raw_width.mean()/base_w:.2f})")
        print("\n-- flat inflation hw' = f*hw (baseline comparison) --")
        for f_ in [1.25, 1.5, 1.75, 2.0]:
            inf = make_inflated(raw, 0, mode="flat", flat=f_)
            sc, _, dom, scm = evaluate(raw, inf)
            cov10 = _cov_on_under(sc, "adaptshrink_ens_infl")
            print(f"  f={f_:<4} dominates {int(dom.dominates_field.sum()):>2}/54  "
                  f"under-cells cov {np.mean(cov10):.3f} (min {np.min(cov10):.3f})  "
                  f"overall cov {scm.raw_cov.mean():.3f}  width {scm.raw_width.mean():.4f} "
                  f"(x{scm.raw_width.mean()/base_w:.2f})")
        return

    inf = make_inflated(raw, args.a, mode="disagree")
    sc, pair, dom, scm = evaluate(raw, inf)
    cov10 = _cov_on_under(sc, "adaptshrink_ens_infl")
    print(f"\nINFLATED (a={args.a}): dominates {int(dom.dominates_field.sum())}/54, "
          f"under-cells cov {np.mean(cov10):.3f} (min {np.min(cov10):.3f}), "
          f"overall cov {scm.raw_cov.mean():.3f}, width {scm.raw_width.mean():.4f} "
          f"(x{scm.raw_width.mean()/base_w:.2f})")
    print("\nper under-cell coverage  base -> inflated:")
    for (mu, tau, k, mech), b in zip(UNDER_CELLS, base_cov):
        r = sc[(sc.method == "adaptshrink_ens_infl") & (sc.mu == mu) & (sc.tau == tau)
               & (sc.k == k) & (sc.mechanism == mech)]
        nc = float(r.iloc[0]["raw_cov"]) if len(r) else float("nan")
        print(f"  mu={mu} tau={tau} k={k:>2} {mech:<6}: {b:.3f} -> {nc:.3f}")
    if args.write:
        inf.to_csv(OUT / f"field_{args.tag}_ens_infl_perrep.csv", index=False)
        dom.to_csv(OUT / f"field_{args.tag}_domination_adaptshrink_ens_infl.csv", index=False)
        print("\nwrote inflated rows + domination CSV")


if __name__ == "__main__":
    main()
