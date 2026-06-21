# Independent verification task: bivariate DTA (Reitsma) ML estimator

You are an INDEPENDENT re-implementer. **Do NOT read or import
`src/ubcma/dta.py`** — implement the estimator yourself from the math spec below,
then check your implementation against the reference-software fits in
`truth-recovery-dta/reference_fits.json` (produced by R `mada::reitsma`, ML).

## Math spec
A diagnostic test accuracy meta-analysis has per-study 2×2 counts (TP, FP, FN,
TN). With continuity correction matching `mada` (`correction=0.5`,
`correction.control="all"`: if ANY study has a zero cell, add 0.5 to EVERY cell
of EVERY study), define per study:

```
Se = TP/(TP+FN),  Sp = TN/(TN+FP)
y1 = logit(Se),   y2 = logit(Sp)
s1^2 = 1/TP + 1/FN   (within-study var of y1)
s2^2 = 1/TN + 1/FP   (within-study var of y2)
S_i  = diag(s1_i^2, s2_i^2)   (zero within-study covariance)
```

Bivariate normal-normal random-effects model: the marginal of study i is
`(y1_i, y2_i) ~ N( M, Sigma + S_i )` with `M = (M1, M2)` and between-study
covariance `Sigma = [[t1^2, rho t1 t2],[rho t1 t2, t2^2]]`. Fit `Sigma` by
**maximum likelihood** (concentrate `M` out via GLS:
`M = (sum_i Wi)^{-1} sum_i Wi y_i`, `Wi = (Sigma + S_i)^{-1}`). The summary
sensitivity = `expit(M1)`, summary specificity = `expit(M2)`.

NOTE: `mada` parameterizes the second coordinate as logit(FPR) = -logit(Sp). The
ML fit is invariant to that sign flip, so your `M2 = logit(Sp)` must equal
`-(mada logit FPR)` = the `m2_logit_spec` field in the JSON.

## What to do
1. Write your own standalone implementation to
   `truth-recovery-dta/verify_<seat>.py` (replace `<seat>` with your identifier,
   e.g. `verify_codex_main`, `verify_codex_noreen`, `verify_agy`). Use only
   numpy/scipy. Do NOT import the project's `ubcma` package.
2. For each dataset in `reference_fits.json` (`counts.TP/FP/FN/TN`), fit your
   estimator and compute the absolute differences of your `(M1, M2,
   sens_summary, spec_summary)` versus the JSON reference fields
   (`m1_logit_sens`, `m2_logit_spec`, `sens_summary`, `spec_summary`).
3. Print a per-dataset table and the worst-case absolute difference. State
   clearly whether the worst-case is below 1e-6 (PASS) or not (FAIL), and write
   the same verdict to `truth-recovery-dta/verify_<seat>_result.json` as
   `{"worst_abs_diff": <float>, "pass": <bool>, "per_dataset": {...}}`.

Report only: your worst-case agreement vs `mada::reitsma`, and PASS/FAIL at 1e-6.
This is a math cross-check; no fabricated numbers — every figure must come from
running your code.
