# OJS republish handoff — UBCMA (Insight, sub 132 / pub 284)

Finalized 2026-06-20. Replaces the "preliminary version". **Do not publish until routed by the author.**
All "preliminary / not peer reviewed / provisional" notices and the `[preliminary version]`
title suffix are removed below. DOI is **not yet registered** (DOIs suppressed site-wide) — leave blank.

## Title (replace — drop the `[preliminary version]` suffix)

```
UBCMA: Unified Bias-Calibrated Meta-Analysis via Joint Heterogeneity-Selection Modeling
```

## Abstract (replace the whole field — remove the preliminary notice; this is the final 156-word E156 body)

Can a single meta-analytic model jointly correct heterogeneity, publication selection, and study-quality bias, rather than applying separate sequential corrections? We tested a unified mixture-normal selection likelihood against eight comparators on twelve simulated scenarios and a real six-trial aspirin secondary-prevention dataset. Estimation used multi-start L-BFGS-B optimisation with profile-likelihood confidence intervals and BCa bootstrap, optionally with Bayesian inference via PyMC. Across twelve scenarios (50 replicates, k=30) the unified model attained the highest coverage, 88.8% at RMSE 0.070, versus 59.7% (DerSimonian-Laird), 63.8% (REML-HKSJ), and 39.0% (trim-and-fill). With selection and quality bias combined, coverage held at 90.3% versus 31.3% for DerSimonian-Laird; on the aspirin data the model gave a pooled log-odds-ratio of +0.01 (95% CI -0.12 to 0.12), versus -0.07 uncorrected. Jointly modelling heterogeneity and selection bias yields less biased, better-calibrated pooled estimates than applying separate corrections sequentially. The parametric logistic selection function may not capture every publication-bias mechanism, and the model is unsuited to small reviews (k below five).

## Galley files to upload / replace

| Galley | File | Notes |
|--------|------|-------|
| PDF    | `e156-submission/ubcma_insight.pdf` | Insight identity, visual abstract + results table + refs |
| JATS   | `e156-submission/jats.xml` | JATS 1.3, with `<ref-list>` (5), `<table-wrap>` (Table 1), `<fig>` (visual abstract) |
| HTML   | `e156-submission/index.html` | interactive E156 galley; needs `assets/` (figures + dashboard) |

Figures (also embedded): `e156-submission/assets/visual_abstract.png`, `fig1_aspirin_forest.png`, `fig2_coverage.png`.

## DOI

Leave the DOI field empty. Not yet registered; the PDF/JATS/galley already state "not yet registered".

## Flags for the author

- **Affiliation discrepancy:** submission files use "Tahir Heart Institute"; the long-form
  `paper/manuscript.md` uses "Royal Free Hospital, London" with ORCID 0009-0003-7781-4478.
  Kept the submission's "Tahir Heart Institute" — confirm which is correct before publishing.
- **Media-violence illustration dropped** (was synthetic placeholder data — see
  `examples/DATA_PROVENANCE.md`). Only the real aspirin illustration remains.
