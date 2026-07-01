"""dump_grid_cells.py -- export per-replicate CSVs for selected tau x sel x n grid
cells so external vendors can re-derive MCIW0 + paired-bootstrap from scratch.

Uses the SAME BASE_SEED and reps as run_tausel_grid.py, so the per-rep rows are
byte-identical to what the grid map summarized (matched-seed reproducibility). The
vendor never imports ubcma code -- they get only these CSVs and grid_verify_spec.md.

Run: PYTHONPATH=nma python nma/verify/dump_grid_cells.py --reps 600 \
        --cells t05_strong_n8,t10_strong_n6,t10_strong_n10,t30_strong_n8,t10_none_n8
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))                      # nma/
sys.path.insert(0, str(ROOT / "truth-recovery"))   # nma/truth-recovery
import nma_bakeoff as BK  # noqa: E402
import run_tausel_grid as G  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=600)
    ap.add_argument("--cells", required=True, help="comma list of grid cell-ids")
    ap.add_argument("--outdir", default=str(HERE / "grid"))
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # map cell-id -> (tau, sel, n)
    index = {G.cell_id(tau, sel, n): (tau, sel, n)
             for tau in G.TAUS for sel in G.SELS for n in G.NS}

    for cid in args.cells.split(","):
        cid = cid.strip()
        if cid not in index:
            raise SystemExit(f"unknown cell-id {cid!r}; valid examples: "
                             f"{list(index)[:5]}")
        tau, sel, n = index[cid]
        spec = G.make_spec(tau, sel, n)
        perrep, _ = BK.run_replicates(spec, args.reps, BK.BASE_SEED, BK.NU_DEFAULT,
                                      small_values="undesirable")
        path = outdir / f"gridcell_{cid}_perrep.csv"
        perrep.to_csv(path, index=False)
        print(f"  {cid:18s} tau={tau} sel={sel} n={n}  "
              f"reps_scored={perrep['rep'].nunique():4d}  -> {path.name} "
              f"({len(perrep)} rows)")


if __name__ == "__main__":
    main()
