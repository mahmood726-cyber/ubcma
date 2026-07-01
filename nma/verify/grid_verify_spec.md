# Phase-4 NMA τ×selection×n grid — independent cross-vendor verification spec

You are an **INDEPENDENT verifier**. Do NOT import or read any `ubcma` / `nma`
source code. Work ONLY from this spec and the per-replicate CSV files named below.
Re-implement the matched-coverage **MCIW0** metric and the **paired-bootstrap
robust-win** test FROM SCRATCH (your own Python, in this working directory), and
report the numbers requested. The goal is to independently confirm — or refute —
the headline boundary-map cells. Use `python` (not `python3`).

## Input

One CSV per grid cell, named `gridcell_<cellid>_perrep.csv`, one row per
(replicate, method, contrast):

    rep,method,contrast,d_hat,ci_low,ci_high,d_true

- `method` ∈ {`common_DL` (field-default baseline), `comp_specific`,
  `adaptshrink`, `adaptshrink_auto` (the proposed estimator)}.
- `contrast` indexes the n−1 basic contrasts (treatment t vs reference 0).
- `d_hat` = point estimate; `d_true` = the true value; `ci_low/ci_high` = the
  method's nominal 95% CI for that contrast.
- A cell-id encodes the regime, e.g. `t10_strong_n8` = homogeneous τ=0.10, strong
  small-study selection, n=8 treatments (full network, 8–15 studies/edge).

## Metric: MCIW0 (matched-coverage interval width at nominal — point efficiency)

For each (method, contrast):
1. error `e = |d_hat - d_true|` per rep.
2. Split reps by parity: `calib = (rep % 2 == 0)`, `test = (rep % 2 == 1)`.
3. `c_half =` the 0.95-quantile of `e` over the CALIB reps (numpy default linear
   interpolation, `np.quantile(..., 0.95)`).
4. `MCIW0(method, contrast) = 2 * c_half`.
5. (sanity) test-split coverage `mean(e[test] <= c_half)` should be ≈ 0.95.

Aggregate: `MCIW0(method) = mean over the n−1 contrasts`.
`dMCIW0(method) = MCIW0(method) − MCIW0(common_DL)`. Negative ⇒ narrower at nominal.

## Truth-gate: paired-bootstrap robust-win test

- For each method build an `(R × (n−1))` matrix of per-rep, per-contrast `|error|`
  indexed by rep (rows) × contrast (cols). Keep only reps where BOTH the baseline
  and the method have all contrasts non-NaN (paired).
- Resample rep-row indices with replacement, `B = 2000` times, RNG seed `= 7`
  (`numpy.random.default_rng(7)`), `rng.integers(0, R, size=(B, R))`.
- For each bootstrap sample recompute, for the method and for `common_DL`,
  `2 * mean_over_contrasts( quantile_0.95( |error|[resampled rows], axis=rows ) )`,
  and take the difference `d0 = MCIW0(method) − MCIW0(common_DL)`.
- Report the 2.5th and 97.5th percentile of the `B` differences.
- **ROBUST WIN** iff the 97.5th percentile of `d0 < 0` (the whole 95% bootstrap CI
  of the advantage lies below zero).

## What to report — for EACH gridcell CSV you are given

For `adaptshrink_auto` relative to `common_DL` (and `adaptshrink` if you wish):
`cellid, n_paired_reps, MCIW0_method, MCIW0_baseline, dMCIW0,
bootstrap CI [2.5%, 97.5%], robust_win (true/false)`.

Write your answer as JSON to `result_<yourname>_grid.json` in this directory, shaped:

    {"cells": {"t10_strong_n8": {"n_paired_reps": ..., "mciw0_method": ...,
       "mciw0_baseline": ..., "dMCIW0": ..., "ci_low": ..., "ci_high": ...,
       "robust_win": true}, ...}, "verifier": "<yourname>"}

## Headline claims under test (confirm or refute, per cell)

1. With **strong** small-study selection and **n ≥ 6**, `adaptshrink_auto` is a
   bootstrap-robust MCIW0 win over the field default, and the win **strengthens
   monotonically with n**.
2. With **no selection** (e.g. `t10_none_n8`, the CONTROL), there is **no** robust
   win — `dMCIW0` should be ≈ 0 or positive, CI not entirely below 0. (If the
   "win" appeared here it would be an under-coverage artifact, not real de-biasing.)
3. Higher **τ** amplifies, not erases, the strong-selection point-efficiency win.

Report each cell's `robust_win` and the dMCIW0 magnitudes to ~3–4 decimal places.
