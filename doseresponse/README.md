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

## Stage 2 -- model-based dose-response NMA (`mbnma.py`)
Frequentist analogue of Bayesian `MBNMAdose`. Treatments are (agent, dose)
nodes; each agent's nodes are constrained to a dose-response curve f_a(dose).
Built on the verified `nma_core` contrast machinery (multi-arm shared-arm
correlation preserved). Models: `nma` (saturated), `linear`, `exponential`,
`emax` (Gauss-Newton GLS). Placebo = network reference, f_a(0)=0.

### Validation (synthetic dose network, 45-80 studies; test_mbnma.py)
| check | result |
|---|---|
| saturated MBNMA common-effect vs R `netmeta` -- TE | max abs diff 9.7e-15 |
| saturated MBNMA common-effect vs R `netmeta` -- SE | max abs diff 4.9e-16 |
| linear slope recovery (truth 0.12 / 0.30) | mean 0.119 / 0.301 |
| Emax recovery (truth Emax 0.9, ED50 2.0) | median 0.915 / 2.033 |

`PYTHONPATH=doseresponse python -m pytest doseresponse/test_mbnma.py -q` -> 5 passed.

JAGS / `MBNMAdose` is not installed in this environment (no JAGS binary), so an
exact match to the Bayesian package is not attempted; the netmeta common-effect
reduction is the external anchor. Bayesian cross-validation is a documented
next step.

## Stage 3 -- AdaptShrink matched-coverage bake-off (`dr_bakeoff.py`)
Estimand = pooled linear dose-response slope; baseline = two-stage REML DRMA;
data = ir studies with known truth + one-sided publication selection
(`sim_doseresponse.py`). **Result: HONEST NULL** -- no estimator robustly beats
two-stage REML at matched coverage (paired-bootstrap MCIW0 CI includes/exceeds 0
in every cell). Mechanism: regression correctors (PET/PEESE) are structurally
invalid for log-RR slopes (biased even with NO selection), so there is no valid
oracle-free bias-corrected member; the kernel collapses onto the field standard.
Confirmed 4 independent internal ways + a from-scratch re-derivation
(`selfverify_dr.py`) because external vendors were unreachable. Full write-up:
`../REPORT_DOSERESPONSE.md`.

`PYTHONPATH=doseresponse:src python -m pytest doseresponse/test_dr_bakeoff.py -q` -> 3 passed.

## Stage 4 -- borrowing connection (`BORROWING_CONNECTION.md`)
Design note: dose is a within-class relevance covariate; MBNMA already *is*
dose-borrowing (precision fusion with a dose-proximity kernel). Proposed forward
test reuses `borrowing/` pilot-2 machinery on the real GLP1-dose slice.
