# Phase-3 NMA network-size sweep — independent cross-vendor verification spec

You are an INDEPENDENT verifier. Do NOT import or read any `ubcma` / `nma`
source code. Work ONLY from this spec and the per-replicate CSV named below.
Re-implement the matched-coverage MCIW0 metric and the paired-bootstrap robust-
win test FROM SCRATCH, and report the numbers requested. The goal is to confirm
(or refute) the headline claim with a fully independent implementation.

## Input

A CSV `swp_<cell>_perrep.csv` with one row per (replicate, method, contrast):

    rep,method,contrast,d_hat,ci_low,ci_high,d_true

- `method` is one of: `common_DL` (the field-default baseline), `comp_specific`,
  `adaptshrink`, `adaptshrink_auto` (the proposed estimator).
- `contrast` indexes the n-1 basic contrasts (treatment t vs reference 0).
- `d_hat` = point estimate of that basic contrast; `d_true` = the true value;
  `ci_low/ci_high` = the method's nominal 95% CI for that contrast.

## Metric: MCIW0 (matched-coverage interval width at nominal, point-efficiency)

For each (method, contrast):
1. error e = |d_hat - d_true| per rep.
2. Split reps by parity: calib = (rep % 2 == 0), test = (rep % 2 == 1).
3. c_half = the `target`-quantile (target = 0.95) of e over the CALIB reps
   (numpy default linear interpolation, `np.quantile`).
4. MCIW0(method, contrast) = 2 * c_half.
5. (Sanity) test-split coverage = mean(e[test] <= c_half) should be ~0.95.

Aggregate: MCIW0(method) = mean of MCIW0(method, contrast) over the n-1 contrasts.

dMCIW0(method) = MCIW0(method) - MCIW0(common_DL).  Negative = narrower at nominal.

## Truth-gate: paired bootstrap robust-win test

- Build, for each method, an (R x (n-1)) matrix of per-rep, per-contrast |error|,
  indexed by rep (rows) and contrast (cols). Keep only reps where BOTH the
  baseline and the method have all contrasts non-NaN (paired).
- Resample rep-row indices with replacement, B = 2000 times (seed your RNG = 7).
- For each bootstrap sample: recompute MCIW0(method) and MCIW0(common_DL) as
  `2 * mean_over_contrasts( quantile_0.95( |error|[resampled rows], axis=rows ) )`,
  and take the difference d0 = MCIW0(method) - MCIW0(common_DL).
- Report the 2.5th and 97.5th percentile of the B differences.
- ROBUST WIN for a method iff the 97.5th percentile of d0 < 0 (the whole 95%
  bootstrap CI of the advantage lies below zero).

## What to report (for EACH cell CSV you are given)

For `adaptshrink_auto` and `adaptshrink`, relative to `common_DL`:
- n_paired_reps
- MCIW0(method), MCIW0(common_DL)
- dMCIW0 (point)
- bootstrap 95% CI [2.5%, 97.5%] of dMCIW0
- robust_win (true/false)

## Headline claim under test

Across the network-size sweep (n = 5, 6, 7, 8 treatments; full geometry; 8–15
studies/edge; homogeneous tau = 0.10; strong small-study selection), the claim is
that `adaptshrink_auto` achieves a **bootstrap-robust** MCIW0 win over the field
default, and that the win **strengthens monotonically with n** (the 97.5%
bootstrap CI upper bound of dMCIW0 moves further below 0 as n grows), because the
mean-over-(n-1)-contrasts advantage has lower bootstrap variance for larger
networks. Confirm the per-cell robust_win flags and the monotone trend, or refute.
