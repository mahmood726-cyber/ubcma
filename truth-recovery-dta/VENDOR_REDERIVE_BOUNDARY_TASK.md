# Cross-vendor re-derivation — AdaptShrink-DTA BOUNDARY-MAP strong column

Same protocol as `VENDOR_REDERIVE_TASK.md` (read it for the exact MCIW0-2D area
formula + paired-bootstrap definition), but applied to a **new input** and a
**new cell list**. Do NOT import `ubcma` or read any project source — use only
numpy/pandas/scipy and the CSV.

## Input
`dta_boundary_perrep.csv` (same columns as the focus CSV:
`cell,strength,rep,method,true_m1,true_m2,m1,m2,converged,area_raw,v00,v01,v11,k_eff`).

## What to compute
For the win-frontier **strong-selection column**, cells:
`k6_thr, k8_thr, k10_thr, k12_thr, k16_thr, k20_thr` (all at `strength=strong`).

For each cell: pair `reitsma` and `adaptshrink_dta` on reps where both are
converged & finite; compute
`AREA = pi * quantile(d2,0.95) * sqrt(det W)` with `W=cov(E,rowvar=False)`,
`d2 = e' W^-1 e`; `darea = AREA(adaptshrink_dta) - AREA(reitsma)` (deterministic,
must reproduce to >=4 dp); then a 2000-resample paired bootstrap (your own seed)
for `ci_lo,ci_hi,frac_better,robust_win=(ci_hi<0)`.

## Output
Write JSON `verify_boundary_<seat>_result.json`:
`{ "seat":"<agy|codex_pc2>", "input":"dta_boundary_perrep.csv",
   "cells":[ {"cell":...,"strength":"strong","area_reitsma":...,
   "area_adaptshrink":...,"darea":...,"ci_lo":...,"ci_hi":...,
   "frac_better":...,"robust_win":...,"n_reps":...}, ... ],
   "imported_ubcma": false }`
Print a short table. The deterministic `darea` is the headline cross-check.
