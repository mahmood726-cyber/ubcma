Mahmood Ahmad
Tahir Heart Institute
mahmood.ahmad2@nhs.net

UBCMA: Unified Bias-Calibrated Meta-Analysis via Joint Heterogeneity-Selection Modeling

Can a single meta-analytic model jointly correct heterogeneity, publication selection, and study-quality bias, rather than applying separate sequential corrections? We tested a unified mixture-normal selection likelihood against eight comparators on twelve simulated scenarios and a real six-trial aspirin secondary-prevention dataset. Estimation used multi-start L-BFGS-B optimisation with profile-likelihood confidence intervals and BCa bootstrap, optionally with Bayesian inference via PyMC. Across twelve scenarios (50 replicates, k=30) the unified model attained the highest coverage, 88.8% at RMSE 0.070, versus 59.7% (DerSimonian-Laird), 63.8% (REML-HKSJ), and 39.0% (trim-and-fill). With selection and quality bias combined, coverage held at 90.3% versus 31.3% for DerSimonian-Laird; on the aspirin data the model gave a pooled log-odds-ratio of +0.01 (95% CI -0.12 to 0.12), versus -0.07 uncorrected. Jointly modelling heterogeneity and selection bias yields less biased, better-calibrated pooled estimates than applying separate corrections sequentially. The parametric logistic selection function may not capture every publication-bias mechanism, and the model is unsuited to small reviews (k below five).

Outside Notes

Type: methods
Primary estimand: Pooled-effect RMSE and CI coverage
App: UBCMA v0.3.0
Data: 12 simulated scenarios (k=30) + real 6-trial aspirin dataset (Verde 2021)
Code: https://github.com/mahmood726-cyber/ubcma
Version: 0.3.0
Validation: FINAL

References

1. DerSimonian R, Laird N. Meta-analysis in clinical trials. Control Clin Trials. 1986;7(3):177-188.
2. Verde PE. A bias-corrected meta-analysis model for combining studies of different types and quality. Biom J. 2021;63(2):406-422.
3. Copas JB, Shi JQ. A sensitivity analysis for publication bias in systematic reviews. Stat Methods Med Res. 2001;10(4):251-265.
4. Doi SAR, Thalib L. A quality-effects model for meta-analysis. Epidemiology. 2008;19(1):94-100.
5. Rover C, Knapp G, Friede T. Hartung-Knapp-Sidik-Jonkman approach and its modification for random-effects meta-analysis with few studies. BMC Med Res Methodol. 2015;15:99.
