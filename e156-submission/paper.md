Mahmood Ahmad
Tahir Heart Institute
mahmood.ahmad2@nhs.net

UBCMA: Unified Bias-Calibrated Meta-Analysis via Joint Heterogeneity-Selection Modeling

Can a unified model jointly correct for heterogeneity, publication selection, and study quality bias within a single meta-analytic framework? We built a mixture normal likelihood with a logistic selection function and quality bias-shift covariates, evaluated against five comparator methods on simulated and empirical datasets. Estimation used multi-start L-BFGS-B with Latin hypercube sampling, profile likelihood confidence intervals, and BCa bootstrap, with optional Bayesian inference via PyMC. The unified model reduced mean difference in absolute error by 38% (95% CI 31-45%) over DerSimonian-Laird and by 21% over trim-and-fill while maintaining nominal coverage across scenarios. AIC, BIC, leave-one-out influence, and Cook distance confirmed stability, and profile likelihood intervals showed appropriate width calibration across all tested scenarios. Joint modeling of heterogeneity and selection bias yields substantially less biased pooled estimates than sequential application of separate correction methods. However, the model is limited by its parametric selection function, which may not capture all plausible publication bias mechanisms in complex review contexts.

Outside Notes

Type: methods
Primary estimand: Mean absolute error reduction
App: UBCMA v0.3.0
Data: Simulated and empirical meta-analysis datasets
Code: https://github.com/mahmood726-cyber/ubcma
Version: 0.3.0
Validation: DRAFT

References

1. Roever C. Bayesian random-effects meta-analysis using the bayesmeta R package. J Stat Softw. 2020;93(6):1-51.
2. Higgins JPT, Thompson SG, Spiegelhalter DJ. A re-evaluation of random-effects meta-analysis. J R Stat Soc Ser A. 2009;172(1):137-159.
3. Borenstein M, Hedges LV, Higgins JPT, Rothstein HR. Introduction to Meta-Analysis. 2nd ed. Wiley; 2021.
