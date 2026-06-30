# Independent re-derivation task (do NOT read any existing scorer code)

You are independently verifying a meta-analysis pilot's headline numbers.

Input file (same directory): `pilot_perrep.csv`
Columns: `target,regime,rep,method,true_mu,mu_hat,ci_low,ci_high,converged` (plus extras you can ignore).
Methods present: `nma`, `borrow`, `shrink_mean`. Regimes: `sparse`, `rich`.

Write your OWN short Python script (numpy/pandas) from the spec below — do not
look for or reuse any existing scoring code in the repo. Then RUN it and report.

## Metric definitions (implement exactly)
1. Per row: `err = abs(mu_hat - true_mu)`. Keep only rows where `converged` is
   true and `mu_hat`, `ci_low`, `ci_high` are finite.
2. MCIW0 (constant-width matched coverage), per `(target,regime,method)` group:
   - split reps: `calib = (rep % 2 == 0)`, `test = ~calib`.
   - `c_half = quantile(err[calib], 0.95)` (numpy default linear interpolation).
   - `MCIW0 = 2 * c_half`.
   - `mc0_test_cov = mean(err[test] <= c_half)`.
3. Paired bootstrap of MCIW0 advantage, per `(target,regime)`, contrast A_vs_B
   (e.g. borrow_vs_nma): pivot `err` to a reps x method table, drop rows with any
   NaN. With `rng = numpy default_rng(7)`, draw 2000 bootstrap resamples of the
   rep-rows (sample row indices with replacement, size = n_reps). For each
   resample: `dMCIW0 = 2*(quantile(errA_boot,0.95) - quantile(errB_boot,0.95))`.
   Report `ci_lo, ci_hi = percentile(dMCIW0, [2.5, 97.5])` and the point
   `2*(quantile(errA,0.95) - quantile(errB,0.95))`. `robust_win = ci_hi < 0`;
   `robust_harm = ci_lo > 0`.

## Report (JSON only, no prose)
For the TWO headline cells `(DPP4, sparse)` and `(GLP1, rich)`:
- For methods nma, borrow, shrink_mean: `MCIW0` and `mc0_test_cov`.
- Paired bootstrap for contrasts `borrow_vs_nma` and `shrink_mean_vs_nma`:
  `point, ci_lo, ci_hi, robust_win, robust_harm`.

Print the JSON to stdout. That is your entire answer.
