#!/usr/bin/env python3
"""run_agy_grid.py -- have agy (Antigravity/Gemini) independently re-derive the
Phase-4 grid MCIW0 + paired-bootstrap robust-win test FROM SCRATCH.

Mirrors run_agy_phase2.py: agy returns a standalone Python script (no ubcma
import); we extract it, run it against the gridcell_*_perrep.csv files in
nma/verify/grid/, and it writes result_agy_grid.json. agy never reads ubcma
source -- it only gets the metric spec (below) and the per-rep CSVs.
"""
import re
import subprocess
import sys
from pathlib import Path

DRIVER = Path.home() / "agy-driver" / "agy_driver.py"
VERIFY_DIR = Path("F:/ubcma/nma/verify")
GRID_DIR = VERIFY_DIR / "grid"
OUTPUT_PY = VERIFY_DIR / "agy_grid_nma.py"

cells = sorted(p.name for p in GRID_DIR.glob("gridcell_*_perrep.csv"))
cell_list = "\n".join(f"  - {c}" for c in cells)

PROMPT = r"""You are an INDEPENDENT verifier cross-checking another team's network
meta-analysis result. Do NOT read or import any `ubcma` / `nma` source code.
Implement the metric and the bootstrap FROM SCRATCH from this spec. Output ONLY a
single Python code block (```python ... ```), nothing else.

INPUT: per-replicate CSVs in the directory F:/ubcma/nma/verify/grid/, one per grid
cell, named gridcell_<cellid>_perrep.csv, columns:
    rep,method,contrast,d_hat,ci_low,ci_high,d_true
method in {common_DL (baseline), comp_specific, adaptshrink, adaptshrink_auto}.
contrast indexes the n-1 basic contrasts. The cells to process:
""" + cell_list + r"""

METRIC MCIW0 (matched-coverage interval width at nominal): for each
(method, contrast): e = |d_hat - d_true| per rep; split reps by parity
calib=(rep%2==0), test=(rep%2==1); c_half = np.quantile(e[calib], 0.95) (default
linear interpolation); MCIW0(method,contrast) = 2*c_half. Aggregate MCIW0(method)
= mean over the n-1 contrasts. dMCIW0 = MCIW0(method) - MCIW0(common_DL).

PAIRED-BOOTSTRAP robust-win: build per-method (R x (n-1)) |error| matrix indexed
by rep x contrast; keep only reps where BOTH baseline and method have all contrasts
non-NaN. Resample rep rows with replacement B=2000 times with
rng = numpy.random.default_rng(7), idx = rng.integers(0, R, size=(B, R)). For each
sample recompute 2*mean_over_contrasts(quantile_0.95(|err|[rows], axis=rows)) for
method and baseline; d0 = method - baseline. Report 2.5th and 97.5th percentiles.
ROBUST WIN iff 97.5th percentile < 0.

DELIVERABLE: a standalone Python script (numpy + pandas only; no ubcma import) that,
run with cwd = F:/ubcma/nma/verify/grid, processes every listed gridcell CSV and for
adaptshrink_auto (vs common_DL) computes n_paired_reps, mciw0_method,
mciw0_baseline, dMCIW0, ci_low (2.5%), ci_high (97.5%), robust_win. It must write
F:/ubcma/nma/verify/result_agy_grid.json shaped:
  {"cells": {"<cellid>": {"n_paired_reps":..., "mciw0_method":...,
     "mciw0_baseline":..., "dMCIW0":..., "ci_low":..., "ci_high":...,
     "robust_win": true/false}, ...}, "verifier": "agy"}
and also print each cell's cellid, dMCIW0, [ci_low, ci_high], robust_win.
Output ONLY the Python code block."""


def main():
    if not cells:
        sys.exit("no gridcell_*_perrep.csv in nma/verify/grid/ -- run dump_grid_cells.py first")
    print(f"[run_agy_grid] {len(cells)} cells; calling agy (model=pro)...")
    sys.stdout.flush()
    result = subprocess.run(
        ["python", str(DRIVER), "--json", "--model", "pro",
         "--response-timeout", "360", PROMPT],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=420)
    print(f"[run_agy_grid] exit={result.returncode}")
    if result.returncode != 0:
        print("[run_agy_grid] stderr:", result.stderr[:600])
        sys.exit(1)
    try:
        import json
        text = json.loads(result.stdout).get("text", result.stdout)
    except Exception:
        text = result.stdout
    (VERIFY_DIR / "agy_grid_raw_response.txt").write_text(text, encoding="utf-8")
    m = re.search(r"```python\s*(.*?)```", text, re.DOTALL)
    code = m.group(1) if m else text
    OUTPUT_PY.write_text(code, encoding="utf-8")
    print(f"[run_agy_grid] wrote {len(code)} chars -> {OUTPUT_PY}")
    print("[run_agy_grid] now run: cd nma/verify/grid && python ../agy_grid_nma.py")


if __name__ == "__main__":
    main()
