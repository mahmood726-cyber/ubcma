# UBCMA Three-Phase Development Design

**Date**: 2026-03-24
**Status**: Approved (spec review passed 2026-03-24)
**Scope**: Harden frequentist prototype, add Bayesian inference, run simulation study

## Context

UBCMA v0.1.0 is a working Python prototype for unified bias-calibrated meta-analysis. It fits a joint penalized likelihood for pooling, mixture heterogeneity, quality-associated shift, and publication selection. The codebase has 4 source modules, 7 passing tests, and a CLI with `fit`, `simulate`, and `benchmark` commands.

The model produces point estimates only. There are no confidence intervals, no multi-start optimization, no diagnostics, and no real-data validation. The test suite covers data loading and simulation but not model fitting.

This spec defines three sequential phases to bring UBCMA from prototype to publication-ready.

## Phase 1: Publication-Ready Frequentist Prototype

### 1.1 Confidence Intervals

**Profile likelihood CIs for `mu_target`**. Walk the negative log-likelihood surface along `mu` while re-optimizing all other parameters at each step. Find where the profile objective increases by `chi2(1, alpha)/2` above the MLE. Use bisection search on each side of the MLE.

- Default: 95% CI (alpha = 0.05)
- Initial search bracket: MLE +/- 5 × SE_DL (the DerSimonian-Laird standard error). If the profile curve does not cross the chi-squared threshold within this bracket, double the bracket and retry once. If still no crossing, return +/-inf for that bound with a warning.
- Maximum bisection iterations: 50. Convergence tolerance (`resolution`): 1e-4 on the mu scale.
- At each profile step, re-optimize nuisance parameters using L-BFGS-B with the same bounds as the full fit, warm-started from the MLE solution. If re-optimization fails at an extreme mu value, exclude that point from the profile curve and issue a warning.
- `n_points`: number of evenly-spaced mu values stored on the profile curve for diagnostic plotting (default 40, 20 per side of MLE).
- Store profile curve data for diagnostic plotting
- Expose via `UBCMAResult.mu_ci` as a `(low, high)` tuple

**Nonparametric bootstrap CIs** as secondary method. Resample studies with replacement, refit the model B times, extract percentile and BCa intervals.

- Default B = 2000
- BCa requires jackknife acceleration — compute via leave-one-out refits (already needed for influence diagnostics)
- If a bootstrap refit fails to converge, record it as missing. Require at least 80% successful refits (1600/2000) for valid bootstrap CIs. Report `n_failed` in the result. If <80% succeed, return NaN CIs with a warning.
- Expose via `UBCMAResult.mu_bootstrap_ci`
- Store full bootstrap distribution for downstream use

**Implementation**: New module `src/ubcma/inference.py` with:
- `profile_likelihood_ci(result, alpha, n_points, resolution)` — `n_points` is the number of profile curve points for plotting; `resolution` is the bisection convergence tolerance on the mu scale
- `bootstrap_ci(data, fitter, n_boot, alpha, method, seed)`

### 1.2 Multi-Start Optimization

Current: single L-BFGS-B run from DerSimonian-Laird starting values.

Change: 20 random restarts using Latin hypercube sampling over the parameter space, plus the current DL-based start. Keep the solution with the lowest objective.

- Sample mu from U(-1, 1), log-tau from U(-3, 0.5), mixture weight logit from U(-2, 2), gamma from N(0, 1), lambda from N(0, 0.5)
- Report: number of converged restarts, objective spread, whether the best solution came from DL start or a random start
- Add `n_restarts` parameter to `UBCMAFit.__init__` (default 20, set to 0 for single-start behavior for backward compat)
- Implementation: retain `_build_start()` for the DL-based start. Add `_latin_hypercube_starts(n, rng)` method to generate random starts. `fit()` orchestrates running all starts (DL + LHS), collects converged solutions, and keeps the one with the lowest objective.

### 1.3 Diagnostics Module

New module `src/ubcma/diagnostics.py`:

**Information criteria**:
- AIC and BIC for the full model
- Reduced models: (a) no selection — `gamma_common = [c, 0, 0, 0]` where `c` is freely estimated (intercept-only, flat selection), `gamma_quality` = 0; (b) no quality shift — `lambda_bias` = 0; (c) single-component heterogeneity — `mix_weight` fixed at 1.0; (d) null model — mu only + homogeneous (tau=0, no moderators/design/quality/selection)
- Each reduced model is a constrained refit, not just a parameter count change. Start from the full model MLE with constrained parameters set to their null values. Use single-start for reduced models (no multi-start).

**Influence diagnostics**:
- Leave-one-out: refit dropping each study, report delta-mu, delta-tau, delta-objective
- Cook's distance analog: `D_i = (mu_full - mu_{-i})^2 / Var(mu_full)`, where `Var(mu_full)` is estimated from the inverse observed information (Hessian approximation from L-BFGS-B at the MLE)
- Externally studentized residuals: `r_i = (y_i - theta_i_hat) / sqrt(s_i^2 + tau^2_hat)`

**Selection function visualization data**:
- Grid of (z-score, precision) -> estimated P(selected)
- Observed studies overlaid with their estimated selection probabilities
- Export as a DataFrame for plotting

**Goodness of fit**:
- Observed vs expected distribution of p-values (selection model predicts a p-value distribution)
- Q-Q plot data: standardized residuals vs normal quantiles

### 1.4 Real-Data Validation

Reproduce published results from reference papers:

**Verde (2021)**: Bias-corrected meta-analysis. Extract the example dataset(s) from the paper or its R package (`baminger` or via Table data). Run UBCMA and compare mu, tau, quality-shift estimates against published Table values.

**Bartos et al. (2022)**: RoBMA paper. Use their example datasets. Compare UBCMA frequentist estimates against their reported posterior means (acknowledging the Bayesian/frequentist distinction — focus on direction and magnitude agreement).

**Fallback**: If datasets are not directly extractable from papers or R packages, simulate synthetic datasets matching the published summary statistics (k, mean effect, tau, proportion of high-RoB studies) as a secondary validation target.

Store datasets as `examples/verde_2021_*.csv` and `examples/bartos_2022_*.csv`. Store expected values as test fixtures in `tests/fixtures/`.

### 1.5 Test Expansion

Target: ~30+ tests total. New test categories:

**Model fitting tests** (`tests/test_model.py`):
- Convergence on toy data with all features (quality, moderators, design)
- Convergence on minimal data (no quality, no moderators, no design)
- CI coverage: simulate 500 datasets from known truth, check that 95% profile CIs contain true mu at ~90-99% rate (SE at 500 reps ~ 0.97%, so this band has <5% false failure rate)
- Edge cases: k=4 (minimum), k=200 (large), all-RCT, homogeneous (tau=0 DGP), no quality columns
- Multi-start: verify best-of-20 objective <= single-start objective

**Diagnostics tests** (`tests/test_diagnostics.py`):
- LOO influence returns correct shape
- AIC < BIC (always true for k > e^2 ~ 7.4)
- Reduced models have higher AIC than full model (on data generated with all components active)
- Residuals are approximately standard normal on homogeneous data

**Inference tests** (`tests/test_inference.py`):
- Profile CI contains point estimate
- Profile CI is narrower than bootstrap CI (typical, not guaranteed)
- Bootstrap distribution has correct length
- BCa adjustment shifts interval in correct direction for skewed data

**Validation tests** (`tests/test_validation.py`):
- Verde dataset: UBCMA mu within tolerance of published value
- Bartos dataset: same check
- Exact tolerance TBD after extracting published values

### 1.6 Files Changed/Created

| File | Action |
|------|--------|
| `src/ubcma/model.py` | Add multi-start to `UBCMAFit.fit()`, expand `UBCMAResult` with CI fields |
| `src/ubcma/inference.py` | NEW — profile likelihood, bootstrap |
| `src/ubcma/diagnostics.py` | NEW — AIC/BIC, LOO, influence, selection plot, GOF |
| `src/ubcma/cli.py` | Add `--n-restarts`, `--bootstrap`, `--profile-ci` flags to `fit` command; add `diagnose` subcommand |
| `tests/test_model.py` | NEW — fitting tests |
| `tests/test_diagnostics.py` | NEW — diagnostics tests |
| `tests/test_inference.py` | NEW — CI tests |
| `tests/test_validation.py` | NEW — real-data validation tests |
| `tests/fixtures/` | NEW — expected values for validation |
| `examples/verde_2021_*.csv` | NEW — reference datasets |
| `examples/bartos_2022_*.csv` | NEW — reference datasets |

---

## Phase 2: Bayesian Rewrite (PyMC)

### 2.1 Architecture

New module `src/ubcma/bayesian.py` alongside existing frequentist `model.py`. Both share `data.py` for data ingestion. A `BayesianUBCMAFit` class mirrors the `UBCMAFit` API.

Dependency: `pymc >= 5.10` added to `pyproject.toml` as an optional dependency (`pip install ubcma[bayes]`).

### 2.2 PyMC Model Specification

Same likelihood structure as the frequentist model:

```
mu ~ Normal(0, 2.5)
beta ~ Normal(0, 1.5)            # moderator coefficients, shape (n_moderators,)
delta ~ Normal(0, 1.5)           # design shift coefficients, shape (n_design,)
lambda_bias ~ Normal(0, 0.75)    # quality-shift coefficients, shape (n_quality,)
log_tau1 ~ Normal(-1, 1)
log_tau2_gap ~ Normal(-1, 1)     # tau2 = tau1 + exp(log_tau2_gap)
mix_logit ~ Normal(1.4, 1)       # logit(0.8) ~ 1.4
gamma_common ~ Normal(0, 1)      # shape (4,): intercept, significance, precision, direction
gamma_quality ~ Normal(0, 0.75)  # shape (n_selection_quality,)

# Heterogeneity: marginalized mixture (NOT discrete latent)
# Analytically marginalize over the two-component assignment using logsumexp,
# matching the frequentist implementation (model.py lines 364-370).
# log p(y_i | ...) = logsumexp(log(w) + logN(y_i; loc, sd1), log(1-w) + logN(y_i; loc, sd2))

# Observation model
theta_i = mu + X_i @ beta + Z_i @ delta
b_i = Q_i @ lambda_bias
# Mixture marginal density per study, not a per-study discrete assignment

# In PyMC code, use sigma=se_i (standard deviation), NOT se_i^2.
# PyMC's Normal is parameterized as Normal(mu, sigma), not Normal(mu, variance).

# Selection likelihood (custom Potential)
log P(R_i=1 | y_i, se_i, Q_i; gamma) - log E[P(R=1 | ...)]
```

The selection normalizer uses the same Gauss-Hermite quadrature as the frequentist model, wrapped in a `pm.Potential`. The entire observation likelihood (mixture marginal + selection) is implemented as a single `pm.Potential` since the built-in distributions cannot express the selection-weighted mixture directly.

### 2.3 Prior Sensitivity

Run with three prior scales:
- **Informative**: sd multiplied by 0.5 (strong regularization)
- **Weakly informative**: default priors (as above)
- **Diffuse**: sd multiplied by 3 (minimal regularization)

Report how `mu_target` posterior shifts across scales. Store as a comparison DataFrame.

### 2.4 Outputs

`BayesianUBCMAResult` contains:
- Posterior summary: mean, median, sd, 95% CrI for all parameters
- Posterior predictive check data
- Study-level shrinkage estimates (posterior mean of theta_i vs observed y_i)
- MCMC diagnostics: Rhat, ESS (bulk + tail), divergence count
- ArviZ InferenceData object for downstream analysis
- Prior sensitivity comparison table

### 2.5 MCMC Diagnostics

Auto-check after sampling:
- Rhat > 1.01 for any parameter → warning
- ESS (bulk) < 400 for any parameter → warning
- Any divergences → warning with suggested remedies (increase target_accept, reparameterize)
- These are reported in `BayesianUBCMAResult.diagnostics` dict and printed by CLI

### 2.6 CLI Extension

New subcommand: `python -m ubcma fit-bayes <csv> [options]`

Additional flags:
- `--chains` (default 4)
- `--draws` (default 2000)
- `--tune` (default 1000)
- `--target-accept` (default 0.9)
- `--prior-scale` (default "weakly_informative", options: "informative", "weakly_informative", "diffuse")
- `--prior-sensitivity` flag: run all three scales and report comparison
- Same `--quality`, `--moderators`, `--design`, `--design-reference`, `--study-id` flags as `fit`

### 2.7 Tests

**`tests/test_bayesian.py`** (~10 tests):
- Model builds without error on toy data
- Sampling completes with 2 chains × 200 draws (smoke test, not convergence)
- Posterior mean of mu is within 0.3 of frequentist MLE on toy data
- Rhat < 1.05 on well-behaved synthetic data (relaxed threshold for test speed)
- Prior sensitivity produces 3 results with different CrI widths
- Diagnostics dict contains expected keys
- Result serializes to text correctly

### 2.8 Files Changed/Created

| File | Action |
|------|--------|
| `src/ubcma/bayesian.py` | NEW — PyMC model, sampler, result class |
| `src/ubcma/cli.py` | Add `fit-bayes` subcommand |
| `pyproject.toml` | Add `[project.optional-dependencies] bayes = ["pymc>=5.10", "arviz>=0.17"]` |
| `tests/test_bayesian.py` | NEW |

---

## Phase 3: Simulation Study

### 3.1 Comparators

| Method | Implementation |
|--------|---------------|
| DerSimonian-Laird | Already in `model.py` |
| REML | scipy optimize (add to `model.py`) |
| UBCMA frequentist | Existing `UBCMAFit` |
| UBCMA Bayesian | Phase 2 `BayesianUBCMAFit` |
| Trim-and-fill | Implement in Python (Duval & Tweedie) |
| PET-PEESE | Implement in Python (weighted regression on SE/SE^2) |
| Copas selection model | Implement in Python (Copas & Shi 2000). Probit selection function with correlation parameter rho and threshold gamma. Profile likelihood over rho grid (0.0 to 0.99 in 20 steps), maximize over remaining parameters at each rho, report sensitivity range. |
| Quality-effects model | Implement in Python (Doi et al. 2015, IVhet-based QE model as in metafor `method="IVhet"` with quality weights replacing inverse-variance weights). |
| RoBMA | Optional R bridge via `rpy2` if available, otherwise skip with note |

New module: `src/ubcma/comparators.py` for non-UBCMA methods.

### 3.2 Data-Generating Scenarios

Factorial design:

| Factor | Levels |
|--------|--------|
| True mu | 0, 0.2, 0.5 |
| Tau | 0, 0.1, 0.3 |
| Selection strength | none (flat), moderate (g1=1.0), strong (g1=2.5) |
| Quality bias | none (lambda=0), moderate (lambda=0.1) |
| Number of studies k | 10, 30, 80 |
| Design mix | all-RCT, 70/30 RCT/OBS |

Total cells: 3 × 3 × 3 × 2 × 3 × 2 = 324

Replicates per cell: 1000

Total simulation runs: 324,000 (frequentist methods are fast; Bayesian UBCMA runs on a subset of ~30 representative cells × 200 reps due to MCMC cost).

**Wall-clock estimates**: Each UBCMA frequentist fit with 20 restarts takes ~0.5-2s. At 324K runs, that is ~45-180 hours single-threaded. With 4-core parallelization, ~12-45 hours. To reduce cost, the simulation study uses `n_restarts=5` (not 20) for UBCMA. Simpler methods (DL, REML, trim-and-fill, PET-PEESE) are ~1ms each. Bayesian subset (6,000 fits × 4 chains × 3K samples) requires ~4-20 days single-threaded; a multi-core machine or cloud resource is assumed.

### 3.3 Performance Metrics

For each method × scenario:
- **Bias**: mean(mu_hat - mu_true)
- **RMSE**: sqrt(mean((mu_hat - mu_true)^2))
- **Coverage**: proportion of 95% CIs/CrIs containing mu_true
- **Interval width**: mean CI/CrI width
- **Convergence rate**: proportion of runs that converged without error

Primary estimand: mu at the reference design (RCT), at low quality-shift settings, at centered moderators.

### 3.4 Execution

New module: `src/ubcma/simulation_study.py`

- `run_scenario(scenario_params, methods, n_reps, seed)` → DataFrame of results
- `run_full_study(n_reps, seed, methods, n_jobs)` → writes results to `results/simulation_study.csv`
- Parallelization via `concurrent.futures.ProcessPoolExecutor`
- Progress bar via tqdm (optional dependency)
- Checkpointing: save completed scenarios incrementally so crashes don't lose work

CLI: `python -m ubcma study --replicates 1000 --seed 42 --jobs 4 --output results/`

### 3.5 Output

- `results/simulation_study.csv`: one row per method × scenario × replicate
- `results/simulation_summary.csv`: aggregated metrics per method × scenario
- `results/simulation_tables.txt`: formatted tables for manuscript supplementary

### 3.6 Tests

**`tests/test_comparators.py`** (~8 tests):
- Each comparator returns expected keys (mu, ci_low, ci_high)
- DL and REML agree closely on homogeneous data
- Trim-and-fill returns at least as many studies as input
- PET-PEESE intercept matches DL when no selection (SE coefficient ~ 0)

**`tests/test_simulation_study.py`** (~5 tests):
- Single scenario × 2 reps runs without error
- Output DataFrame has expected columns
- Metrics computation is correct on hand-crafted data
- Checkpointing saves and resumes correctly

### 3.7 Files Changed/Created

| File | Action |
|------|--------|
| `src/ubcma/comparators.py` | NEW — REML, trim-and-fill, PET-PEESE, Copas, quality-effects |
| `src/ubcma/simulation_study.py` | NEW — scenario runner, aggregation, checkpointing |
| `src/ubcma/cli.py` | Add `study` subcommand |
| `tests/test_comparators.py` | NEW |
| `tests/test_simulation_study.py` | NEW |
| `results/` | NEW directory for study outputs |

---

## Success Criteria

### Phase 1
- All existing tests pass (no regressions)
- 30+ tests total, all green
- Profile likelihood CI coverage 90-99% on 500-rep simulation with known mu
- Multi-start finds equal or better objective than single-start on 95%+ of runs
- Verde and Bartos dataset estimates within stated tolerances

### Phase 2
- Bayesian posterior mean within 0.1 of frequentist MLE on toy data
- Rhat < 1.01 on toy data with 4 chains × 2000 draws
- Prior sensitivity shows narrower CrI with informative priors
- 10+ Bayesian-specific tests pass

### Phase 3
- All 7+ comparators run without error on all 324 scenarios
- UBCMA has lower bias than DL/REML under moderate-to-strong selection
- UBCMA has valid coverage (>90%) under its assumed DGP
- Results CSV is complete and reproducible from seed

## Dependencies

| Package | Phase | Required |
|---------|-------|----------|
| numpy >= 1.26 | All | Yes |
| scipy >= 1.12 | All | Yes |
| pandas >= 2.2 | All | Yes |
| pymc >= 5.10 | 2, 3 | Optional (bayes extra) |
| arviz >= 0.17 | 2, 3 | Optional (bayes extra) |
| tqdm | 3 | Optional |
