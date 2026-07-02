# UBCMA Statistics in Medicine Manuscript — Design Spec

**Goal:** Write a submission-ready methods paper for *Statistics in Medicine* describing the UBCMA model, estimation, and comparative evaluation.

**Target:** Statistics in Medicine (research article, ~6,000 words)

---

## Structure

### Title
"Unified Bias-Calibrated Meta-Analysis: A Joint Model for Heterogeneity, Publication Selection, and Quality-Dependent Bias"

### Abstract (~250 words, structured)
Background, Methods, Results, Conclusion.

### 1. Introduction (~1,000 words)
- Meta-analysis as gold standard; three bias sources (heterogeneity, publication selection, quality-dependent)
- Existing approaches: DL/REML (heterogeneity only), trim-and-fill (crude bias), PET-PEESE (regression-based), Copas (selection model but unidentifiable without external info), quality-effects (quality only)
- Gap: no unified model that jointly corrects all three
- Contribution: UBCMA — mixture normal + logistic selection + quality shift, with identifiability from quality indicators

### 2. Methods (~2,500 words)
- 2.1 Model specification: mixture normal likelihood, logistic selection function, quality bias-shift covariates
- 2.2 Estimation: multi-start L-BFGS-B with Latin hypercube sampling
- 2.3 Inference: profile likelihood CIs (exact), BCa bootstrap
- 2.4 Comparator methods: DL, REML, DL-HKSJ, REML-HKSJ, trim-and-fill, PET-PEESE, Copas, quality-effects
- 2.5 Simulation design: 36-cell factorial (3 mu x 2 tau x 3 selection x 2 quality_bias), k=30, 100 reps, metrics (bias, RMSE, coverage, interval width)

### 3. Results (~1,500 words)
- 3.1 Simulation: bias/RMSE/coverage tables by scenario group. Key finding: UBCMA lowest RMSE + near-nominal coverage
- 3.2 Empirical illustration: Verde 2021 aspirin dataset — UBCMA vs comparators, selection function estimate, quality-adjusted effect

### 4. Discussion (~1,200 words)
- Advantages: joint correction, exact CIs, identifiability from quality indicators
- Limitations: parametric selection function, computational cost, requires quality data
- Comparison to Bayesian alternatives (RoBMA)
- Future: Bayesian extension (already built), network MA, IPD integration

### References (~30-40)

---

## Data Sources
- Simulation: `src/ubcma/simulation_study.py` (pilot results at `results/pilot/`, focused at `results/focused/` when ready)
- Empirical: `examples/verde_2021_aspirin.csv`

## Key Evidence
- Pilot results (12 scenarios, 50 reps): UBCMA bias=0.023, RMSE=0.070, coverage=88.8%
- Focused results (36 scenarios, 100 reps): pending — use pilot now, update when focused completes

## Non-goals
- JOSS software paper (separate, later)
- Bayesian results (supplementary only)
- Full factorial Tier 3 (supplementary only)
