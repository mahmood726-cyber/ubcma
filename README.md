# UBCMA

UBCMA stands for Unified Bias-Calibrated Meta-Analysis. This project is a new prototype model for meta-analysis that estimates a pooled effect while jointly accounting for:

- between-study heterogeneity
- quality-associated shift terms
- publication selection and small-study effects
- study-level moderators and mixed designs

This directory contains a working Python prototype, a benchmark script, and a toy dataset.

## Why this exists

Current methods usually handle only part of the problem well. Random-effects pooling captures heterogeneity but not publication bias. Selection models address publication bias but usually do not model internal bias explicitly. Quality-adjusted models often do not separate bias from heterogeneity. UBCMA is designed to put those pieces into one coherent likelihood.

The target estimand is not just the mean of the observed studies. Under the model's zero-mean heterogeneity assumption, `mu` is the expected effect for a future study at:

- low quality-shift settings
- the sample-mean moderator profile after automatic centering
- the chosen reference design

## Prototype model

For study `i`:

`y_i ~ f_selected(y_i | theta_i, s_i, q_i, R_i = 1)`

`theta_i = mu + x_i' beta + z_i' delta + h_i`

`b_i = q_i' lambda`

`h_i ~ w N(0, tau_1^2) + (1 - w) N(0, tau_2^2)`

`y_i | theta_i, b_i ~ N(theta_i + b_i, s_i^2)`

`P(R_i = 1 | y_i, s_i, q_i) = logistic(g0 + g1 sig_i + g2 prec_i + g3 dir_i + g4 qbar_i)`

Where:

- `y_i` is the observed study effect
- `s_i` is the reported standard error
- `q_i` is a vector of bias or quality indicators, ideally scaled 0 to 1
- `x_i` are moderators
- `z_i` are non-reference design indicators
- `h_i` captures heterogeneity with a two-component mixture
- `sig_i` is a smooth significance term based on `|y_i / s_i|`
- `prec_i` is study precision
- `dir_i` is a smooth direction term from the observed z-score

The implementation uses a penalized likelihood or MAP-style fit with `scipy.optimize`, plus Gauss-Hermite quadrature for the publication-selection normalizing constant.

The quality terms should be read as quality-associated shifts, not as fully identified causal bias corrections. When domain-level quality columns are supplied, the selection model now uses domain-level quality terms too instead of a forced equal-weight summary score.

## What this prototype does and does not claim

It does:

- fit a joint model for pooling, heterogeneity, quality bias, and publication selection
- produce a reference-design effect estimate under explicit modeling assumptions
- estimate quality-associated shift coefficients
- run an aligned synthetic benchmark against a naive weighted meta-regression intercept

It does not:

- prove superiority to all existing methods
- replace a full validated Bayesian implementation in Stan or PyMC
- handle multivariate correlated outcomes yet
- identify internal bias separately from true effect modification without stronger assumptions

The benchmark is an aligned synthetic check under data generated from mechanisms close to the fitted model. It is useful as a smoke test, not as broad comparative evidence.

## Data schema

Minimum CSV columns:

- `yi`: observed effect estimate
- `sei`: standard error

Optional columns:

- quality or bias columns such as `rob_selection`, `rob_measurement`, `rob_reporting`
- a summary quality column such as `quality_score`
- moderator columns such as `dose`, `followup_months`
- a design column such as `design`
- `study_id`

Quality columns should be numeric and preferably coded from `0` for low risk to `1` for high risk.
If `--quality` is omitted, UBCMA infers only `rob_*` and `bias_*` domain columns. A standalone `quality_score` is treated as a summary score, not as an extra bias domain.
Moderator columns are automatically centered so `mu_target` is anchored at the observed mean moderator profile.
If `--design` has more than one level, `--design-reference` is required so the reference design is explicit.

## Quick start

Run directly from the source tree:

```powershell
$env:PYTHONPATH='src'
```

Optional editable install, if your environment allows it:

```powershell
python -m pip install -e . --user
```

Fit the bundled toy dataset:

```powershell
python -m ubcma fit examples\toy_studies.csv --quality rob_selection,rob_measurement,rob_reporting --moderators moderator --design design --design-reference RCT --study-id study_id
```

Run a one-replicate synthetic smoke benchmark:

```powershell
python -m ubcma benchmark --replicates 1 --seed 42
```

Generate a synthetic observed dataset:

```powershell
python -m ubcma simulate --output examples\simulated.csv --seed 42
```

If you want the latent development dataset too:

```powershell
python -m ubcma simulate --output examples\simulated.csv --seed 42 --include-latent
```

Run the smoke tests:

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests
```

## Files

- `src/ubcma/model.py`: core likelihood and optimizer
- `src/ubcma/data.py`: CSV ingestion and design matrix construction
- `src/ubcma/simulation.py`: synthetic data and benchmark harness
- `src/ubcma/cli.py`: command-line entry point
- `tests/test_smoke.py`: basic input and simulation checks

## References

These papers informed the design rationale and are worth keeping with the project:

- Bohnning D. Meta-analysis: a unifying meta-likelihood approach framing unobserved heterogeneity, study covariates, publication bias, and study quality. Methods Inf Med. 2005. PMID 15778804. https://pubmed.ncbi.nlm.nih.gov/15778804/
- Verde PE. A bias-corrected meta-analysis model for combining studies of different types and quality. Biom J. 2021. PMID 32996196. https://pubmed.ncbi.nlm.nih.gov/32996196/
- Bartoš F et al. Robust Bayesian meta-analysis and its extension with regression. Psychol Methods and Research Synthesis Methods. PMID 35588075 and 39964496. https://pubmed.ncbi.nlm.nih.gov/35588075/ and https://pubmed.ncbi.nlm.nih.gov/39964496/
- McShane BB et al. Adjusting for publication bias in meta-analysis: an evaluation of selection methods and some cautionary notes. Perspect Psychol Sci. 2016. PMID 27694467. https://pubmed.ncbi.nlm.nih.gov/27694467/

## Suggested next step

If this prototype looks promising, the right next move is a fully Bayesian implementation with:

- multivariate outcomes
- explicit missing-evidence process
- prior sensitivity analysis
- simulations against RoBMA, Copas-type models, BC/BC-BNP, and quality-effects models
