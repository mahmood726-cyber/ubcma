#!/usr/bin/env python
"""Reproduce the headline simulation results reported in the UBCMA manuscript.

This regenerates the pilot tier (the tier the paper's Tables 1-3 are built from):

    12 scenarios = 3 selection strengths x 2 quality-bias levels x 2 heterogeneity
    50 replicates per scenario, k=30, mu=0.2, all-RCT designs
    9 methods = UBCMA + 8 comparators
    (dl, dl_hksj, reml, reml_hksj, trim_and_fill, pet_peese, copas, quality_effects)

Random seed is FIXED at 42 (the value documented in the manuscript:
"Simulation results can be reproduced using `ubcma study --tier pilot --seed 42`").
Data generation is seeded per replicate; UBCMA's multi-start optimiser uses a
fixed restart_seed (12345), so the run is deterministic.

Canonical, version-controlled outputs are written to ``paper/results/``:

    pilot_summary.csv            -- overall per-method table (source of Table 1)
    pilot_by_quality_bias.csv    -- per-method metrics split by quality-bias level
                                    (source of Table 3 worst-case coverage figures)
    pilot_simulation_study.csv   -- the full per-replicate record (audit trail)

The script also prints the reproduced headline numbers next to the published
values so any reader can confirm the paper stands (or see the deltas if it does
not).

Usage:
    python scripts/reproduce_paper_results.py            # reuse results/pilot if present
    python scripts/reproduce_paper_results.py --force    # always re-run the simulation
    python scripts/reproduce_paper_results.py --seed 42  # override the seed
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Allow running from a source checkout without installation.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.exists() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ubcma.simulation_study import compute_metrics, run_tier  # noqa: E402

METHODS = [
    "dl", "dl_hksj", "reml", "reml_hksj",
    "trim_and_fill", "pet_peese", "copas", "quality_effects", "ubcma",
]

SCRATCH_DIR = ROOT / "results"          # gitignored working area / checkpoints
CANONICAL_DIR = ROOT / "paper" / "results"  # version-controlled artifacts

# Published values (manuscript Tables 1 and 3) for the reproduction check.
PUBLISHED = {
    "ubcma_rmse": 0.070,
    "ubcma_coverage": 0.888,
    "dl_coverage": 0.597,
    "reml_hksj_coverage": 0.638,
    "trim_and_fill_coverage": 0.390,
    "ubcma_worstcase_coverage": 0.903,   # selection+quality bias present
    "dl_worstcase_coverage": 0.313,
}


def _load_or_run(force: bool, seed: int) -> pd.DataFrame:
    study_csv = SCRATCH_DIR / "pilot" / "simulation_study.csv"
    if study_csv.exists() and not force:
        print(f"Reusing existing run: {study_csv}")
        return pd.read_csv(study_csv)
    print(f"Running pilot tier (seed={seed}); this takes roughly 30-60 minutes...")
    return run_tier("pilot", methods=METHODS, n_reps=50, seed=seed,
                    output_dir=str(SCRATCH_DIR / "pilot"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true",
                    help="Re-run the simulation even if a cached run exists.")
    ap.add_argument("--seed", type=int, default=42,
                    help="Random seed (default 42, the manuscript value).")
    args = ap.parse_args()

    full = _load_or_run(args.force, args.seed)

    CANONICAL_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Overall per-method table (Table 1 source).
    overall = compute_metrics(full).sort_values("method").reset_index(drop=True)
    overall.to_csv(CANONICAL_DIR / "pilot_summary.csv", index=False)

    # 2. Per-method metrics split by quality-bias level (Table 3 source).
    by_bias = (
        full.groupby("quality_bias", group_keys=True)
        .apply(lambda g: compute_metrics(g), include_groups=False)
        .reset_index(level=0)
        .reset_index(drop=True)
    )
    by_bias.to_csv(CANONICAL_DIR / "pilot_by_quality_bias.csv", index=False)

    # 3. Full per-replicate audit trail.
    full.to_csv(CANONICAL_DIR / "pilot_simulation_study.csv", index=False)

    # ----- Reproduction check -----
    def cov(method: str) -> float:
        return float(overall.loc[overall.method == method, "coverage"].iloc[0])

    def rmse(method: str) -> float:
        return float(overall.loc[overall.method == method, "rmse"].iloc[0])

    worst = by_bias[by_bias.quality_bias == "moderate"]

    def worst_cov(method: str) -> float:
        return float(worst.loc[worst.method == method, "coverage"].iloc[0])

    repro = {
        "ubcma_rmse": rmse("ubcma"),
        "ubcma_coverage": cov("ubcma"),
        "dl_coverage": cov("dl"),
        "reml_hksj_coverage": cov("reml_hksj"),
        "trim_and_fill_coverage": cov("trim_and_fill"),
        "ubcma_worstcase_coverage": worst_cov("ubcma"),
        "dl_worstcase_coverage": worst_cov("dl"),
    }

    print("\nseed =", args.seed)
    print(f"replicates per scenario = 50, scenarios = 12, "
          f"total replicates = {len(full) // len(METHODS)}")
    print("\n=== Reproduced vs published ===")
    print(f"{'quantity':<28}{'reproduced':>12}{'published':>12}{'delta':>10}")
    max_abs_delta = 0.0
    for key, pub in PUBLISHED.items():
        got = repro[key]
        delta = got - pub
        max_abs_delta = max(max_abs_delta, abs(delta))
        print(f"{key:<28}{got:>12.4f}{pub:>12.4f}{delta:>+10.4f}")

    print(f"\nlargest absolute delta: {max_abs_delta:.4f}")
    tol = 0.02  # Monte-Carlo tolerance for coverage/RMSE at 50 reps
    verdict = "MATCH (paper stands)" if max_abs_delta <= tol else "DIFFERS (paper needs correction)"
    print(f"verdict @ tol {tol}: {verdict}")

    print("\nCanonical artifacts written to:")
    for name in ("pilot_summary.csv", "pilot_by_quality_bias.csv",
                 "pilot_simulation_study.csv"):
        print(f"  {CANONICAL_DIR / name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
