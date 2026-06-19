Mahmood Ahmad
Tahir Heart Institute
mahmood.ahmad2@nhs.net

UBCMA: Unified Bias-Calibrated Meta-Analysis via Joint Heterogeneity-Selection Modeling

Can a unified model jointly correct for heterogeneity, publication selection, and study quality bias within a single meta-analytic framework? We built a mixture normal likelihood with a logistic selection function and quality bias-shift covariates, compared against eight comparators on simulated and empirical data. Estimation used multi-start L-BFGS-B, profile likelihood confidence intervals, and BCa bootstrap, with optional Bayesian inference via PyMC. Across twelve simulation scenarios (50 replicates, k=30), the unified model attained the highest interval coverage (88.8%) at low RMSE (0.070), versus 59.7% for DerSimonian-Laird, 63.8% for REML-HKSJ, and 39.0% for trim-and-fill. When both selection and quality bias were present, coverage held at 90.3% versus 31.3% for DerSimonian-Laird, while AIC, BIC, and leave-one-out diagnostics confirmed stability. Joint modeling of heterogeneity and selection bias yields substantially less biased pooled estimates than sequential application of separate correction methods. However, the model is limited by its parametric selection function, which may not capture all publication bias mechanisms in complex reviews.

Outside Notes

Type: methods
Primary estimand: Pooled-effect RMSE and CI coverage
App: UBCMA v0.3.0
Data: Simulated and empirical meta-analysis datasets
Code: https://github.com/mahmood726-cyber/ubcma
Version: 0.3.0
Validation: DRAFT

References

1. Roever C. Bayesian random-effects meta-analysis using the bayesmeta R package. J Stat Softw. 2020;93(6):1-51.
2. Higgins JPT, Thompson SG, Spiegelhalter DJ. A re-evaluation of random-effects meta-analysis. J R Stat Soc Ser A. 2009;172(1):137-159.
3. Borenstein M, Hedges LV, Higgins JPT, Rothstein HR. Introduction to Meta-Analysis. 2nd ed. Wiley; 2021.
