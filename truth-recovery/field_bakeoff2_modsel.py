"""Moderate-selection extension of the field2 domination bake-off.

The committed field2 grid (field_bakeoff2.py) fixes strength="strong" on every
selection cell. The single most central open question for a *bias-corrector* is
whether its domination survives *weaker* selection: under moderate selection the
induced bias is smaller (less for the corrector to recover) while the corrector's
efficiency cost is unchanged, so domination could plausibly erode.

This sibling reuses run_cell / scoring from field_bakeoff2 verbatim (the legacy
generator is left bit-faithful for provenance) and only swaps the grid to
strength="moderate" on the two *strength-dependent* mechanisms {step, copas}.
The "none" mechanism is strength-invariant (identical DGP), so it is excluded --
the honest comparison is against the strong grid restricted to the SAME step+copas
selection cells (continuous 20/36, log-OR 17/24 for adaptshrink_auto).

Tags: "cm" (continuous moderate), "lm" (log-OR moderate). Distinct artifact set;
never overwrites field2_c2 / field2_l2.

  PYTHONPATH=src python truth-recovery/field_bakeoff2_modsel.py --shard 0 --nshards 4 --reps 40 --tag cm --outcome continuous
  PYTHONPATH=src python truth-recovery/field_bakeoff2_modsel.py --combine --tag cm --outcome continuous
"""
import argparse
import itertools
import json
import time

import pandas as pd

import misspec_harness as H
import field_bakeoff2 as FB2

OUT = FB2.OUT
CELL_KEYS = FB2.CELL_KEYS
HEADLINES = FB2.HEADLINES


def build_grid_moderate(outcome):
    """Mirror the field2 grid axes but strength='moderate', selection mechs only."""
    if outcome == "logor":
        mus, taus, ks = [0.0, 0.4, 0.8], [0.15, 0.4], [10, 40]      # 24 cells
    else:  # continuous
        mus, taus, ks = [0.0, 0.2, 0.5], [0.1, 0.3, 0.5], [5, 40]   # 36 cells
    cells = []
    for mu, tau, k, mech in itertools.product(mus, taus, ks, ["step", "copas"]):
        cells.append({"mu": mu, "tau": tau, "k": k, "mechanism": mech,
                      "strength": "moderate", "outcome": outcome})
    return cells


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--reps", type=int, default=40)
    ap.add_argument("--tag", default="cm")
    ap.add_argument("--outcome", default="continuous", choices=["continuous", "logor"])
    ap.add_argument("--combine", action="store_true")
    ap.add_argument("--target", type=float, default=0.95)
    args = ap.parse_args()

    if not args.combine:
        grid = build_grid_moderate(args.outcome)
        my = [(i, c) for i, c in enumerate(grid) if i % args.nshards == args.shard]
        frames = []
        t0 = time.time()
        for i, cell in my:
            tc = time.time()
            # same seed scheme as parent; independent moderate grid
            frames.append(FB2.run_cell(cell, args.reps, H.BASE_SEED + i * 100000))
            print(f"[m shard{args.shard}] cell {i} {cell} ({time.time()-tc:.0f}s)", flush=True)
        pd.concat(frames, ignore_index=True).to_csv(
            OUT / f"field2_{args.tag}_shard{args.shard}.csv", index=False)
        print(f"[m shard{args.shard}] done total {time.time()-t0:.0f}s")
        return

    frames = [pd.read_csv(p) for p in sorted(OUT.glob(f"field2_{args.tag}_shard*.csv"))]
    raw = pd.concat(frames, ignore_index=True)
    raw.to_csv(OUT / f"field2_{args.tag}_perrep.csv", index=False)
    score, pairs, doms = FB2._score_with_outcome(raw, target=args.target)
    score.to_csv(OUT / f"field2_{args.tag}_scores.csv", index=False)
    summary = {"tag": args.tag, "strength": "moderate",
               "n_cells": int(raw.groupby(CELL_KEYS).ngroups),
               "reps": int(raw["rep"].max()) + 1, "headlines": {}}
    for h in HEADLINES:
        doms[h].to_csv(OUT / f"field2_{args.tag}_domination_{h}.csv", index=False)
        d = doms[h]
        summary["headlines"][h] = {"dominates": int(d["dominates_field"].sum()),
                                   "total": int(len(d)),
                                   "loss_cells": int((d["n_loss"] > 0).sum())}
    with open(OUT / f"field2_{args.tag}_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n# FIELD2 MODERATE-selection bake-off tag={args.tag} "
          f"cells={summary['n_cells']} reps={summary['reps']}\n")
    for h, s in summary["headlines"].items():
        print(f"  {h:<22} dominates {s['dominates']:>3}/{s['total']:<3}  "
              f"({s['loss_cells']} loss-cells)")


if __name__ == "__main__":
    main()
