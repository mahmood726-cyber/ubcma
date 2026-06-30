# Cross-vendor re-derivation task — AdaptShrink-DTA headline bake-off numbers

You are an INDEPENDENT verifier. Re-derive the headline matched-coverage
bake-off numbers **from the raw per-replicate CSV only**. Do **NOT** import or
read the `ubcma` package, `dta_bakeoff.py`, or any project source. Use only
`numpy`/`pandas`/`scipy` and the CSV.

## Input
`dta_focus_perrep.csv` (and, when present, `dta_boundary_perrep.csv`).
Columns: `cell,strength,rep,method,true_m1,true_m2,m1,m2,converged,area_raw,v00,v01,v11,k_eff`.
`(m1,m2)` = a method's summary operating point (logit Se, logit Sp);
`(true_m1,true_m2)` = the data-generating truth for that replicate.

## The metric: MCIW0-2D constant-region AREA
For one `(cell, strength, method)` group, over the set of paired replicates R:

```
e_i  = (m1_i - true_m1_i,  m2_i - true_m2_i)        # 2-vector per rep i in R
E    = stack of e_i                                  # |R| x 2
W    = numpy.cov(E, rowvar=False)                    # 2x2, ddof=1 (numpy default)
detW = det(W)   (require detW > 0)
d2_i = e_i^T  W^{-1}  e_i
q    = numpy.quantile(d2, 0.95)                      # method='linear' (numpy default)
AREA = pi * q * sqrt(detW)
```

## Paired comparison
Reference method = `reitsma` (the Henmi–Copas analogue). Method under test =
`adaptshrink_dta`. The paired rep set R = replicates where **both** `reitsma`
and `adaptshrink_dta` have `converged==True` and finite `m1,m2` (in these focus
cells all methods converge on all 800 reps, so R = all reps).

```
dArea = AREA(adaptshrink_dta) - AREA(reitsma)      # negative => ours smaller (better)
```

This point `dArea` is **deterministic** (no seed) — it must reproduce to ≥4 dp.

## Bootstrap (your own seed — agreement on sign/robustness, not exact CI)
Paired bootstrap over R: draw `n_boot=2000` resamples of the rep indices (with
replacement, same indices applied to both methods), recompute `AREA` for each
method on the resample, form `diff_b = AREA(ours)_b - AREA(reitsma)_b`. Report:
- `ci_lo, ci_hi` = 2.5th / 97.5th percentile of `diff_b`
- `frac_better` = mean(diff_b < 0)
- `robust_win`  = (ci_hi < 0)

## Target cells (from `dta_focus_perrep.csv`)
| cell | strength | ubcma reference dArea | ubcma robust? |
|---|---|---|---|
| k10_hi | strong | -0.2244 | True |
| k6_thr | strong | -0.1333 | True |
| k10_thr | strong | -0.1264 | False (near-miss) |
| k20_thr | strong | -0.0293 | False |

## Output (write JSON to `verify_rederive_<seat>_result.json`)
```json
{ "seat": "<agy|codex_pc2>",
  "cells": [
    {"cell":"k10_hi","strength":"strong",
     "area_reitsma":..., "area_adaptshrink":..., "darea":...,
     "ci_lo":..., "ci_hi":..., "frac_better":..., "robust_win":...,
     "n_reps":...}, ... ],
  "imported_ubcma": false }
```
Print a short table too. The deterministic `darea` is the headline cross-check.
