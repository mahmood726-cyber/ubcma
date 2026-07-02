# E156 Protocol: UBCMA: Unified Bias-Calibrated Meta-Analysis via Joint Heterogeneity-Selection Modeling

**Project**: ubcma
**E156 Entry**: #163
**Type**: methods
**Primary Estimand**: Pooled-effect RMSE and CI coverage
**Data**: 12 simulated scenarios (k=30) + real 6-trial aspirin dataset (Verde 2021)

**Date Created**: 2026-04-07
**Date Last Updated**: 2026-06-20
**Status**: FINAL

**Dashboard**: [https://mahmood726-cyber.github.io/ubcma/](https://mahmood726-cyber.github.io/ubcma/)

## E156 Abstract (CURRENT BODY)

Can a single meta-analytic model jointly correct heterogeneity, publication selection, and study-quality bias, rather than applying separate sequential corrections? We tested a unified mixture-normal selection likelihood against eight comparators on twelve simulated scenarios and a real six-trial aspirin secondary-prevention dataset. Estimation used multi-start L-BFGS-B optimisation with profile-likelihood confidence intervals and BCa bootstrap, optionally with Bayesian inference via PyMC. Across twelve scenarios (50 replicates, k=30) the unified model attained the highest coverage, 88.8% at RMSE 0.070, versus 59.7% (DerSimonian-Laird), 63.8% (REML-HKSJ), and 39.0% (trim-and-fill). With selection and quality bias combined, coverage held at 90.3% versus 31.3% for DerSimonian-Laird; on the aspirin data the model gave a pooled log-odds-ratio of +0.01 (95% CI -0.12 to 0.12), versus -0.07 uncorrected. Jointly modelling heterogeneity and selection bias yields less biased, better-calibrated pooled estimates than applying separate corrections sequentially. The parametric logistic selection function may not capture every publication-bias mechanism, and the model is unsuited to small reviews (k below five).

---
*Finalized 2026-06-20 (empirical result added, simulation numbers verified, preliminary markers removed).*
