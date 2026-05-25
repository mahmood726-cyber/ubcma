# UBCMA: Unified Bias-Calibrated Meta-Analysis

[![ci](https://github.com/mahmood726-cyber/ubcma/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/mahmood726-cyber/ubcma/actions/workflows/ci.yml) [![codeql](https://github.com/mahmood726-cyber/ubcma/actions/workflows/codeql.yml/badge.svg?branch=master)](https://github.com/mahmood726-cyber/ubcma/actions/workflows/codeql.yml) [![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE) [![python: 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

A Python framework for meta-analysis that jointly models heterogeneity, publication selection bias, and study quality-dependent bias. UBCMA uses a mixture normal likelihood with a smooth selection function, optimized via multi-start L-BFGS-B with optional Bayesian (PyMC) inference.

## Install

```bash
pip install .               # frequentist only
pip install ".[bayes]"       # adds PyMC for Bayesian inference
```

## Quick Start

```python
from ubcma import MetaAnalysisDataset, UBCMAFit

data = MetaAnalysisDataset.from_csv("data.csv", study_id_col="study_id")
result = UBCMAFit(n_restarts=20).fit(data)
print(f"mu = {result.mu:.3f}, tau = {result.tau1:.3f}")
print(result.study_table())
```

## CLI

```bash
# Fit a model
ubcma fit data.csv --quality rob_selection,rob_measurement --profile-ci

# Run diagnostics (AIC/BIC, LOO influence, residuals)
ubcma diagnose data.csv

# Bayesian fit with prior sensitivity
ubcma fit-bayes data.csv --chains 4 --prior-sensitivity

# Simulation study (pilot tier, ~30 min)
ubcma study --tier pilot --replicates 50
```

## Key Features

- **Multi-start optimization** with Latin hypercube sampling
- **Profile likelihood CIs** (exact, no HKSJ correction needed)
- **BCa bootstrap CIs** with jackknife acceleration
- **Bayesian backend** via PyMC (NUTS, prior sensitivity analysis)
- **5 comparator methods**: REML, trim-and-fill, PET-PEESE, Copas, quality-effects
- **HKSJ correction** for DL and REML comparators
- **Diagnostics**: AIC/BIC for 5 model variants, LOO influence, Cook's D
- **Three-tier simulation study** framework (pilot/focused/full factorial)

## Model

For study *i*:

```
y_i ~ f_selected(y_i | theta_i, s_i, q_i, R_i = 1)

theta_i = mu + x_i' beta + z_i' delta + h_i
b_i = q_i' lambda
h_i ~ w N(0, tau_1^2) + (1 - w) N(0, tau_2^2)
y_i | theta_i, b_i ~ N(theta_i + b_i, s_i^2)

P(R_i = 1 | y_i, s_i, q_i) = logistic(g0 + g1 sig_i + g2 prec_i + g3 dir_i + g4 qbar_i)
```

Where `y_i` is the observed effect, `s_i` the standard error, `q_i` quality/bias indicators (0-1 scale), `x_i` moderators, `z_i` design indicators. The two-component mixture captures heterogeneity. The selection function models publication bias via significance, precision, and direction terms.

The target estimand `mu` is the expected effect for a future study at the reference design, mean moderator profile, and low quality-shift settings.

## Data Schema

Minimum CSV columns: `yi` (effect), `sei` (standard error).

Optional: `rob_*` / `bias_*` quality columns, `quality_score`, moderators (e.g. `dose`, `followup_months`), `design`, `study_id`.

## Files

- `src/ubcma/model.py` — core likelihood and optimizer
- `src/ubcma/data.py` — CSV ingestion and design matrix construction
- `src/ubcma/comparators.py` — REML, trim-and-fill, PET-PEESE, Copas, quality-effects, HKSJ
- `src/ubcma/inference.py` — bootstrap CIs, profile likelihood
- `src/ubcma/diagnostics.py` — AIC/BIC, LOO influence, Cook's D, residuals
- `src/ubcma/simulation.py` — synthetic data generation
- `src/ubcma/simulation_study.py` — tier-based simulation framework
- `src/ubcma/bayesian.py` — PyMC NUTS backend
- `src/ubcma/cli.py` — command-line entry point
- `examples/` — quickstart script and validation datasets

## Citation

```bibtex
@software{ubcma2026,
  title  = {UBCMA: Unified Bias-Calibrated Meta-Analysis},
  year   = {2026},
  url    = {https://github.com/TODO/ubcma}
}
```

## References

- Bohnning D. Meta-analysis: a unifying meta-likelihood approach. Methods Inf Med. 2005. PMID 15778804.
- Verde PE. A bias-corrected meta-analysis model. Biom J. 2021. PMID 32996196.
- Bartos F et al. Robust Bayesian meta-analysis. Psychol Methods. PMID 35588075.
- McShane BB et al. Adjusting for publication bias in meta-analysis. Perspect Psychol Sci. 2016. PMID 27694467.

## License

MIT
