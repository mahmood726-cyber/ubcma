# Dose-Response Meta-Analysis (DRMA) thread

From-scratch aggregate-data dose-response meta-analysis, validated against R
`dosresmeta` 2.2.0 and disciplined with the AdaptShrink matched-coverage
truth-gate. Mirrors the structure of the `nma/` and `borrowing/` threads.

## Stage 1 -- two-stage & one-stage DRMA (`drma.py`)
- Greenland-Longnecker covariance reconstruction (`gl_reconstruct`, `gl_covariance`)
  -- port of `dosresmeta::grl` / `covar.logrr` (cc/ir/ci designs).
- Within-study GLS first stage (`first_stage`); linear and Harrell restricted-
  cubic-spline (`rcs_basis`, norm=2, matches `rms::rcs`) dose transforms.
- Multivariate random-effects pooling (`mvmeta`, REML/fixed); p=1 -> univariate REML.
- One-stage pooled GLS cross-check (`drma_one_stage`).

### Validation (alcohol_crc, 8 incidence-rate cohorts; see reference/, test_drma.py)
| quantity | max abs diff vs dosresmeta |
|---|---|
| GL within-study covariance (study 1) | 4.2e-16 |
| linear two-stage REML slope & SE | 2.6e-18 / 3.5e-18 |
| RCS spline two-stage FIXED coef | 7.4e-18 |
| RCS spline two-stage REML coef | 1.3e-09 |
| RCS spline two-stage REML between-study Psi | 1.1e-10 |

`PYTHONPATH=doseresponse python -m pytest doseresponse/test_drma.py -q`  -> 9 passed.

## Stage 2 -- model-based dose-response NMA (MBNMA)  [next]
## Stage 3 -- AdaptShrink matched-coverage bake-off on DR data  [next]
