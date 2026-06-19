#!/usr/bin/env python
"""Run the focused (Tier 2) simulation study: 36 scenarios × 100 reps × 9 methods.
Expected runtime: 2-4 hours. Run with:
    python scripts/run_focused_simulation.py
"""
import sys
import time
from pathlib import Path

# Allow running from a source checkout without installation.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.exists() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ubcma.simulation_study import compute_metrics, format_table, run_tier

METHODS = [
    "dl", "dl_hksj", "reml", "reml_hksj",
    "trim_and_fill", "pet_peese", "copas",
    "quality_effects", "ubcma",
]

OUTPUT_DIR = str(ROOT / "results" / "focused")

if __name__ == "__main__":
    print("Starting Tier 2 (focused) simulation: 36 scenarios × 100 reps × 9 methods")
    print(f"Output: {OUTPUT_DIR}/")
    t0 = time.time()

    full_df = run_tier(
        tier="focused",
        methods=METHODS,
        n_reps=100,
        seed=42,
        output_dir=OUTPUT_DIR,
    )

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed/3600:.1f} hours ({elapsed:.0f}s)")

    # Overall summary
    summary = compute_metrics(full_df)
    print("\n=== Overall Summary ===")
    print(format_table(summary))

    # Per-scenario summaries
    for (sel, bias), group in full_df.groupby(["selection", "quality_bias"]):
        metrics = compute_metrics(group)
        print(f"\n=== selection={sel}, quality_bias={bias} ===")
        print(format_table(metrics))

    # Save formatted tables
    summary.to_csv(f"{OUTPUT_DIR}/simulation_summary.csv", index=False)
    print(f"\nSummary written to {OUTPUT_DIR}/simulation_summary.csv")
    print(format_table(summary, fmt="latex"))
