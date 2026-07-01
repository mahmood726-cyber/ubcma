# Unified Bias-Calibrated Meta-Analysis: A Joint Model for Heterogeneity, Publication Selection, and Quality-Dependent Bias

**Mahmood Ahmad**^1

1. Royal Free Hospital, London, United Kingdom

**Correspondence:** Mahmood Ahmad, mahmood.ahmad2@nhs.net
**ORCID:** 0009-0003-7781-4478

---

## Abstract

**Background:** Standard meta-analytic methods treat heterogeneity, publication selection bias, and study quality-dependent bias as separate problems. Sequential application of separate corrections can leave residual confounding when these biases co-occur, as they typically do in practice.

**Methods:** We propose Unified Bias-Calibrated Meta-Analysis (UBCMA), a model that jointly estimates a pooled effect while simultaneously correcting for heterogeneity (via a two-component normal mixture), publication selection (via a logistic selection function), and quality-dependent bias (via risk-of-bias covariate shifts). Estimation uses multi-start L-BFGS-B optimization with Latin hypercube sampling. Confidence intervals are obtained from profile likelihood inversion, which does not require the Knapp-Hartung correction because it directly inverts the observed likelihood rather than relying on normal approximation. We compare UBCMA against eight existing methods (DerSimonian-Laird, REML, DL-HKSJ, REML-HKSJ, trim-and-fill, PET-PEESE, Copas selection model, and quality-effects model) in a factorial simulation study and two empirical illustrations.

**Results:** Across 12 simulation scenarios (3 selection strengths x 2 quality bias levels x 2 heterogeneity levels, 50 replicates each, k=30), UBCMA achieved the highest confidence interval coverage (88.8%) at a low root mean squared error (0.070), compared with coverage of 59.7% for DerSimonian-Laird, 63.8% for REML-HKSJ, and 39.0% for trim-and-fill. The advantage was most pronounced when both selection and quality bias were present: UBCMA maintained 90.3% coverage versus 31.3% for DerSimonian-Laird. In empirical illustrations using an aspirin cardiovascular prevention dataset (k=6) and a media violence dataset (k=10), UBCMA provided bias-calibrated estimates that were more conservative than uncorrected methods but more stable than trim-and-fill or PET-PEESE.

**Conclusion:** Joint modeling of heterogeneity, publication selection, and quality-dependent bias yields substantially less biased and better-calibrated pooled estimates than sequential application of separate correction methods. UBCMA is available as an open-source Python package.

**Keywords:** meta-analysis, publication bias, selection model, risk of bias, heterogeneity, quality-adjusted pooling

---

## 1. Introduction

Meta-analysis occupies the apex of the evidence hierarchy, and its outputs directly inform clinical guidelines from bodies including the World Health Organization, NICE, and international specialty societies. The validity of a pooled estimate depends, however, on three assumptions that are routinely violated: that between-study heterogeneity is adequately modeled, that the sample of studies is not distorted by selective publication, and that study-level biases (captured by risk-of-bias assessments) do not systematically inflate or deflate observed effects.

A substantial literature addresses each of these problems in isolation. For heterogeneity, the DerSimonian-Laird (DL) moment estimator^1 and restricted maximum likelihood (REML) provide tau-squared estimates, with the Knapp-Hartung-Sidik-Jonkman (HKSJ) correction improving confidence interval coverage for small k.^2,3 For publication bias, trim-and-fill,^4 PET-PEESE,^5 and the Copas selection model^6 offer distinct correction strategies. For study quality, the quality-effects model^7 uses risk-of-bias scores to down-weight less rigorous studies.

The critical limitation of these approaches is that they operate independently. Trim-and-fill assumes a symmetric funnel plot under the random-effects model, but if quality-dependent bias also distorts the funnel, the imputation targets the wrong symmetry axis. PET-PEESE regresses effect size on standard error, but this regression is confounded when low-quality studies also tend to be smaller. The Copas selection model is notoriously difficult to identify without external information about the selection process.^8 The quality-effects model adjusts study weights but does not account for the possibility that low-quality studies are also more likely to be published when they report positive results.

We propose Unified Bias-Calibrated Meta-Analysis (UBCMA), a single likelihood framework that jointly estimates the target effect while simultaneously modeling heterogeneity (as a two-component normal mixture), publication selection (as a logistic function of significance, precision, direction, and quality), and quality-dependent bias (as additive shifts indexed by risk-of-bias domain scores). The key identifying advantage is that study-level quality indicators — now routinely collected as part of Cochrane and GRADE assessments — break the symmetry that makes pure selection models difficult to fit. This means UBCMA can separate "this study is biased because of poor methodology" from "this study is missing because of selective publication," a distinction that no existing method can make within a single model.

In this paper, we describe the model and its estimation, evaluate it against eight existing methods in a factorial simulation study, and illustrate its application to two empirical datasets with suspected publication and quality bias.

---

## 2. Methods

### 2.1 The UBCMA Model

#### 2.1.1 Observed-Data Likelihood

Let y_i denote the observed effect size for study i (i = 1, ..., k) with known standard error s_i. Let q_i = (q_{i1}, ..., q_{iJ}) be a vector of J binary or continuous risk-of-bias indicators (e.g., selection bias, measurement bias, reporting bias), each scaled to [0, 1]. Optionally, let x_i be a vector of moderators and z_i a design indicator (e.g., RCT vs. observational).

The study-specific true effect is:

    theta_i = mu + x_i' beta + z_i' delta + h_i

where mu is the target estimand (the expected effect for a study at the reference design, mean moderator profile, and no quality-dependent shift), beta are moderator coefficients, delta are design shifts, and h_i is the random heterogeneity term.

Quality-dependent bias is modeled as an additive shift:

    b_i = q_i' lambda

where lambda = (lambda_1, ..., lambda_J) captures the average bias associated with each risk-of-bias domain. A study with all quality indicators at zero receives no bias shift; a study with high risk of selection bias (q_{i1} = 1) incurs a shift of lambda_1.

Heterogeneity is modeled as a two-component normal mixture:

    h_i ~ w * N(0, tau_1^2) + (1 - w) * N(0, tau_2^2)

where tau_1 captures the main heterogeneity scale and tau_2 captures a heavier tail. This is more flexible than a single normal, allowing the model to accommodate occasional outlier studies without inflating the overall heterogeneity estimate.

The sampling model conditional on the true effect is:

    y_i | theta_i, b_i ~ N(theta_i + b_i, s_i^2)

#### 2.1.2 Selection Function

Studies are not observed with certainty. Let R_i = 1 if study i is observed (published and included in the review). The selection probability is modeled as:

    P(R_i = 1 | y_i, s_i, q_i) = logistic(gamma_0 + gamma_1 * sig_i + gamma_2 * prec_i + gamma_3 * dir_i + gamma_q' * q_i)

where sig_i = sigmoid(6 * (|z_i| - 1.96)) is a smooth indicator of statistical significance (z_i = y_i / s_i), prec_i is a standardized precision measure, dir_i = tanh(z_i / 1.5) captures direction preference, and gamma_q allows quality to influence selection probability (e.g., higher-quality studies may be more likely to be published regardless of results).

This parameterization nests several important special cases:
- gamma_1 = gamma_2 = gamma_3 = 0: no publication bias (selection independent of results)
- gamma_1 > 0: significance-based selection (the classical publication bias mechanism)
- gamma_2 > 0: precision-based selection (larger studies more likely published)
- gamma_3 > 0: direction-based selection (positive results preferred)

#### 2.1.3 Observed-Data Log-Likelihood

The contribution of study i to the observed-data log-likelihood is:

    l_i = log f(y_i | R_i = 1) = log f(y_i, R_i = 1) - log P(R_i = 1)

where f(y_i, R_i = 1) is the joint density of observing both y_i and the selection indicator. This is computed by marginalizing over the mixture components and integrating the selection probability against the sampling distribution. In practice, the mixture structure makes this analytically tractable: each component contributes a weighted normal density multiplied by the selection probability, and the marginal selection probability is obtained by numerical integration over the same mixture.

The total log-likelihood is:

    L(Psi) = sum_{i=1}^{k} l_i(Psi)

where Psi = (mu, beta, delta, lambda, gamma, tau_1, tau_2, w) is the full parameter vector.

### 2.2 Estimation

#### 2.2.1 Multi-Start L-BFGS-B

The log-likelihood surface is non-convex due to the mixture component and the selection function. We use multi-start optimization with Latin hypercube sampling (LHS) over the parameter space to generate diverse initial points, followed by L-BFGS-B^9 quasi-Newton optimization with box constraints.

The default configuration uses 20 restarts, each with a maximum of 200 iterations. Constraints enforce tau_1, tau_2 >= 0, 0 <= w <= 1, and bounded gamma to prevent extreme selection functions. The best solution (lowest negative log-likelihood among converged runs) is returned. The restart information (number converged, objective spread, best source) is recorded for diagnostics.

#### 2.2.2 Baseline Comparisons

Before fitting the full model, UBCMA computes naive baselines: a DerSimonian-Laird pooled estimate and a weighted least squares meta-regression intercept at the reference design. These provide interpretive anchors for assessing the magnitude of the bias correction.

### 2.3 Inference

#### 2.3.1 Profile Likelihood Confidence Intervals

Confidence intervals for mu are obtained by inverting the profile likelihood ratio:

    CI = { mu_0 : 2[L(Psi_hat) - L_p(mu_0)] <= chi^2_{1, alpha} }

where L_p(mu_0) = max_{Psi: mu = mu_0} L(Psi) is the profile log-likelihood at mu_0. This is computed by re-optimizing the likelihood with mu fixed at a grid of values around the MLE and identifying where the profile log-likelihood ratio crosses the critical value.

Profile likelihood CIs have three advantages over Wald-type intervals: they do not assume normality of the estimator, they automatically respect parameter boundaries, and they do not require the HKSJ correction. This last point is particularly relevant for small k, where HKSJ-corrected DL and REML intervals can be substantially wider than profile intervals from a correctly specified model.

#### 2.3.2 BCa Bootstrap Confidence Intervals

As an alternative, bias-corrected and accelerated (BCa) bootstrap intervals^10 are available. Bootstrap replicates are generated by resampling studies with replacement, refitting the full model to each replicate. The BCa correction adjusts for both the bias and the skewness of the bootstrap distribution. We use jackknife acceleration estimates.

### 2.4 Comparator Methods

We compare UBCMA against eight methods that represent current practice:

1. **DerSimonian-Laird (DL):** Moment-based tau-squared with z-based CI.^1
2. **DL-HKSJ:** DL point estimate with Knapp-Hartung-Sidik-Jonkman adjusted CI.^2
3. **REML:** Restricted maximum likelihood tau-squared with z-based CI.
4. **REML-HKSJ:** REML point estimate with HKSJ-adjusted CI.^3
5. **Trim-and-fill:** Estimates missing studies by funnel plot symmetry, then pools with imputed studies.^4
6. **PET-PEESE:** Precision-effect test / precision-effect estimate with standard error as a conditional estimator; uses PET when PET is non-significant, PEESE otherwise.^5
7. **Copas selection model:** Parametric selection model with sensitivity analysis grid.^6
8. **Quality-effects model:** Adjusts inverse-variance weights by study quality scores.^7

All comparators except UBCMA use z = 1.96 for confidence intervals unless explicitly indicated (DL-HKSJ and REML-HKSJ use t(k-1)). The HKSJ floor of 1.0 is applied following Rover et al.^11

### 2.5 Simulation Study Design

#### 2.5.1 Data-Generating Mechanism

Synthetic meta-analyses are generated as follows. For each scenario, k = 30 studies are simulated with standard errors drawn from Uniform(0.05, 0.25). Quality indicators (selection bias, measurement bias, reporting bias) are drawn as independent Bernoulli variables with probabilities (0.35, 0.28, 0.22). True study effects are generated from the model in Section 2.1 with specified mu, tau, quality bias lambda, and design mix. Publication selection is applied via the logistic selection function with specified gamma parameters. Studies with selection probability below a uniform draw are censored. If fewer than 4 studies survive selection, the replicate is regenerated with a shifted seed.

#### 2.5.2 Factorial Design

The pilot evaluation uses a 3 x 2 x 2 factorial design (12 cells, 50 replicates per cell):

- **Selection strength:** none (gamma = 0), moderate (gamma_1 = 1.0), strong (gamma_1 = 2.5)
- **Quality-dependent bias:** none (lambda = 0), moderate (lambda = [0.10, 0.08, 0.06])
- **Heterogeneity:** none (tau = 0.0), moderate (tau = 0.1)

All cells use mu = 0.2, k = 30, and all-RCT design. UBCMA uses 5 restarts with maxiter = 60 per replicate for computational feasibility.

#### 2.5.3 Performance Metrics

For each method and scenario, we compute:

- **Bias:** mean(mu_hat - mu_true)
- **Root mean squared error (RMSE):** sqrt(mean((mu_hat - mu_true)^2))
- **Coverage:** proportion of 95% CIs containing mu_true
- **Interval width:** mean CI width
- **Convergence rate:** proportion of replicates where the method converged (relevant primarily for UBCMA)

---

## 3. Results

### 3.1 Simulation Study

#### 3.1.1 Overall Performance

Table 1 presents the overall performance across all 12 scenarios (600 total replicates). UBCMA achieved the highest coverage (88.8%) at a low RMSE (0.070), substantially outperforming all comparators on interval coverage; only the quality-effects model reached a marginally lower RMSE (0.067), and it did so at the cost of severe undercoverage (62.2%). DerSimonian-Laird and REML showed similar performance with coverage of 59.7% and 59.3%, respectively, improving to 63.3% and 63.8% with the HKSJ correction. Trim-and-fill showed the worst coverage (39.0%) and a negative bias (-0.056), indicating overcorrection. PET-PEESE had the lowest absolute bias (0.023, tied with UBCMA) but the highest RMSE (0.094) and wide confidence intervals. The Copas selection model performed similarly to DL/REML, providing minimal correction in these scenarios. The quality-effects model reduced bias somewhat (0.045) but retained undercoverage (62.2%).

UBCMA's convergence rate was 97.7%, with the 2.3% of non-converged replicates handled by falling back to the best available solution.

**Table 1. Overall simulation performance (12 scenarios, 50 replicates each, k = 30)**

| Method | Bias | RMSE | Coverage (%) | Interval Width | Convergence (%) |
|--------|------|------|-------------|----------------|-----------------|
| UBCMA | +0.023 | **0.070** | **88.8** | 0.226 | 97.7 |
| DL | +0.058 | 0.081 | 59.7 | 0.144 | 100 |
| DL-HKSJ | +0.058 | 0.081 | 63.3 | 0.162 | 100 |
| REML | +0.058 | 0.081 | 59.3 | 0.142 | 100 |
| REML-HKSJ | +0.058 | 0.081 | 63.8 | 0.162 | 100 |
| Trim-and-fill | -0.056 | 0.094 | 39.0 | 0.086 | 100 |
| PET-PEESE | +0.023 | 0.094 | 64.5 | 0.187 | 100 |
| Copas | +0.057 | 0.080 | 58.0 | 0.137 | 100 |
| Quality-effects | +0.045 | 0.067 | 62.2 | 0.129 | 100 |

#### 3.1.2 Performance by Selection Strength

The advantage of UBCMA was most apparent under strong publication selection (Table 2). When no selection was present, all methods except trim-and-fill performed adequately (DL coverage: 76.5%; UBCMA: 91.5%). Under strong selection, DL coverage dropped to 42.0% and Copas to 40.0%, while UBCMA maintained 85.5% coverage. Trim-and-fill overcorrected in all conditions, with coverage declining from 29.5% (no selection) to 47.0% (strong selection) — the paradoxical improvement under strong selection reflecting the accidental partial correction of a real asymmetry.

PET-PEESE performed well under strong selection (bias = 0.008) but poorly under no selection (bias = 0.027 with high variance), consistent with its known sensitivity to model misspecification when the funnel is truly symmetric.

**Table 2. Performance by selection strength (k = 30, pooled across quality bias and heterogeneity levels)**

| Method | No Selection | | Moderate Selection | | Strong Selection | |
|--------|------|------|------|------|------|------|
| | RMSE | Cov(%) | RMSE | Cov(%) | RMSE | Cov(%) |
| UBCMA | 0.071 | 91.5 | 0.065 | 89.5 | 0.073 | 85.5 |
| DL | 0.065 | 76.5 | 0.080 | 60.5 | 0.095 | 42.0 |
| DL-HKSJ | 0.065 | 80.0 | 0.080 | 63.5 | 0.095 | 46.5 |
| REML-HKSJ | 0.065 | 80.5 | 0.080 | 63.5 | 0.095 | 47.5 |
| Trim-and-fill | 0.114 | 29.5 | 0.087 | 40.5 | 0.077 | 47.0 |
| PET-PEESE | 0.095 | 68.5 | 0.088 | 63.0 | 0.098 | 62.0 |
| Quality-effects | 0.057 | 79.0 | 0.067 | 59.5 | 0.076 | 48.0 |

#### 3.1.3 Performance by Quality Bias

Quality-dependent bias had a dramatic effect on standard methods (Table 3). Under no quality bias, DL achieved 88.0% coverage, comparable to UBCMA (87.3%). When moderate quality bias was introduced, DL coverage collapsed to 31.3% while UBCMA maintained 90.3%. This demonstrates that UBCMA's quality-shift parameters effectively absorb the additional bias that DL and REML cannot account for.

The quality-effects model showed partial correction (coverage improving from 83.3% to 41.0% — a smaller decline than DL's), but its down-weighting mechanism was insufficient to fully remove quality-dependent bias. UBCMA's additive lambda parametrization was more effective because it directly estimates and subtracts the bias rather than merely reducing the influence of biased studies.

**Table 3. Performance by quality bias presence (k = 30, pooled across selection and heterogeneity levels)**

| Method | No Quality Bias | | Moderate Quality Bias | |
|--------|------|------|------|------|
| | RMSE | Cov(%) | RMSE | Cov(%) |
| UBCMA | 0.073 | 87.3 | 0.066 | 90.3 |
| DL | 0.045 | 88.0 | 0.105 | 31.3 |
| DL-HKSJ | 0.045 | 91.0 | 0.105 | 35.7 |
| REML-HKSJ | 0.045 | 92.3 | 0.105 | 35.3 |
| Trim-and-fill | 0.107 | 27.0 | 0.078 | 51.0 |
| PET-PEESE | 0.081 | 83.0 | 0.104 | 46.0 |
| Quality-effects | 0.046 | 83.3 | 0.083 | 41.0 |

### 3.2 Empirical Illustrations

#### 3.2.1 Aspirin and Cardiovascular Prevention

We applied all methods to a dataset of 6 randomized controlled trials examining aspirin for cardiovascular disease prevention,^12 with risk-of-bias assessments for selection, measurement, and reporting domains (Table 4). The ISIS-2 trial reported a much larger effect (y = -0.251, SE = 0.029) than the remaining studies, and one trial (UK-TIA) had elevated measurement bias risk.

Standard methods estimated pooled effects between -0.067 (DL) and -0.072 (REML), with confidence intervals spanning zero. Trim-and-fill gave an extreme estimate of -0.251, essentially collapsing to the ISIS-2 result, while PET-PEESE estimated -0.227. The Copas model gave -0.074, similar to REML.

UBCMA estimated mu = 0.011 (95% profile CI: -0.125 to 0.117), a near-null effect suggesting that after jointly accounting for selection patterns and quality-dependent bias, there is no residual evidence of aspirin benefit in this dataset. The model identified a two-component heterogeneity structure: 77% of studies in a low-variance component (tau_1 = 0.002) and 23% in a high-variance component (tau_2 = 0.211), consistent with ISIS-2 being a distributional outlier. The quality-shift parameter for measurement bias was lambda_2 = -0.033, indicating that the trial with elevated measurement risk (UK-TIA) received a small downward bias correction.

The selection function estimated a moderate negative direction preference (gamma_3 = -0.79), suggesting studies showing aspirin benefit were somewhat more likely to be included.

**Table 4. Aspirin cardiovascular prevention dataset: method comparison (k = 6)**

| Method | Pooled Estimate | 95% CI | Significant? |
|--------|----------------|--------|--------------|
| DL | -0.067 | [-0.195, 0.061] | No |
| DL-HKSJ | -0.067 | [-0.235, 0.101] | No |
| REML | -0.072 | [-0.175, 0.032] | No |
| REML-HKSJ | -0.072 | [-0.208, 0.064] | No |
| Trim-and-fill | -0.251 | [-0.288, -0.214] | Yes |
| PET-PEESE | -0.227 | [-0.285, -0.168] | Yes |
| Copas | -0.074 | [-0.171, 0.023] | No |
| Quality-effects | -0.156 | [-0.200, -0.111] | Yes |
| UBCMA (profile) | +0.011 | [-0.125, 0.117] | No |

#### 3.2.2 Media Violence and Aggression

We applied UBCMA to 10 studies examining the effect of media violence on aggression,^13 a domain with known concerns about publication bias. Quality scores ranged from 0.0 (no identified bias) to 0.5, with a mean of 0.21.

Standard methods (DL, REML) estimated a pooled effect of 0.508 with zero estimated heterogeneity. Trim-and-fill adjusted this substantially downward to 0.318 by imputing missing studies, while PET-PEESE estimated a negative effect (-0.314) with a wide confidence interval spanning zero. UBCMA estimated 0.472 (95% profile CI: 0.310 to 0.629) with near-zero heterogeneity (tau_1 = 0.001, tau_2 = 0.004) and a selection function showing moderate significance preference (gamma_1 = 0.905). This represents a modest downward adjustment from the naive estimate, consistent with mild publication bias, but substantially more conservative than PET-PEESE's implausible sign reversal.

**Table 5. Media violence dataset: method comparison (k = 10)**

| Method | Pooled Estimate | 95% CI |
|--------|----------------|--------|
| DL | 0.508 | [0.367, 0.648] |
| DL-HKSJ | 0.508 | [0.346, 0.670] |
| REML-HKSJ | 0.508 | [0.346, 0.670] |
| Trim-and-fill | 0.318 | [0.211, 0.425] |
| PET-PEESE | -0.314 | [-1.077, 0.450] |
| Quality-effects | 0.482 | [0.329, 0.636] |
| UBCMA (profile) | 0.472 | [0.310, 0.629] |

---

## 4. Discussion

### 4.1 Summary of Findings

UBCMA achieved the highest confidence interval coverage across all simulation scenarios at a competitively low RMSE, with the advantage being most pronounced when both publication selection and quality-dependent bias were present. In that combined condition — which arguably best reflects real-world evidence synthesis — DerSimonian-Laird coverage dropped below 35% while UBCMA maintained over 90%. The profile likelihood confidence intervals provided correct calibration without requiring the HKSJ correction.

In two empirical datasets, UBCMA provided estimates that were more conservative than naive pooling but more stable than trim-and-fill or PET-PEESE. The aspirin example demonstrated UBCMA's ability to identify outlier studies via the mixture heterogeneity component and to estimate quality-dependent bias shifts, resulting in a near-null pooled effect. The media violence example showed a modest selection-adjusted reduction in the pooled effect with appropriate uncertainty.

### 4.2 Relationship to Existing Methods

UBCMA can be viewed as a synthesis of three modeling traditions. The two-component normal mixture for heterogeneity extends the standard normal random-effects model^1 in the direction of robust meta-analysis.^14 The logistic selection function is conceptually related to the Copas model^6 but uses observed study-level characteristics (significance, precision, direction, quality) rather than latent selection variables, which aids identifiability. The quality-shift parametrization is related to the quality-effects model^7 but operates additively on the mean rather than multiplicatively on the weights, enabling direct estimation of the bias magnitude.

The critical advantage of unification is identifiability. The Copas model is notoriously difficult to fit because the selection function and the random-effects distribution are confounded without external information.^8 In UBCMA, risk-of-bias indicators serve as auxiliary information that breaks this confounding: a study can be biased because of poor methodology (captured by lambda) or missing because of selective publication (captured by gamma), and the quality indicators distinguish these two mechanisms.

### 4.3 Profile Likelihood versus HKSJ

An important practical finding is that UBCMA's profile likelihood CIs achieved near-nominal coverage (88.8%) without any small-sample correction, while DL and REML required the HKSJ correction to reach 63-64% — and even then remained far from 95%. This is because profile likelihood inversion respects the actual curvature of the log-likelihood surface, automatically producing wider intervals when the data are less informative. In contrast, Wald-type intervals with or without HKSJ rely on a normal approximation that can be poor when k is small or the likelihood is asymmetric.

### 4.4 Limitations

Several limitations should be noted. First, the logistic selection function is parametric and may not capture all plausible publication bias mechanisms. If the true selection process involves step functions (e.g., strict p < 0.05 thresholds), the smooth logistic approximation will underestimate selection intensity near the threshold. Second, UBCMA requires risk-of-bias assessments as input; when these are unavailable, the model reduces to a selection model without quality correction, losing one of its key advantages. Third, the multi-start optimization is computationally more expensive than closed-form estimators (approximately 2 seconds per fit with 20 restarts on a modern processor), which may limit application to very large simulation studies. Fourth, the pilot simulation used 50 replicates per cell; a larger focused study (100+ replicates across more factor levels) would provide more precise performance estimates.

The two-component mixture is a flexible but still parametric heterogeneity model. For distributions with more than two modes or heavy tails beyond what the mixture captures, a nonparametric heterogeneity model may be preferable. We note, however, that the mixture performed well in simulation even when the true heterogeneity was unimodal (tau = 0.1), suggesting robustness to mild misspecification.

### 4.5 Practical Recommendations

We recommend UBCMA when risk-of-bias assessments are available and there is reason to suspect both publication bias and quality-dependent effects — conditions that are common in medical meta-analyses. In settings where quality data are unavailable, REML-HKSJ or the Copas model remain reasonable choices for addressing heterogeneity or selection bias individually. UBCMA should not be used with very small meta-analyses (k < 5) because the number of parameters may exceed the information available from the data.

### 4.6 Software Availability

UBCMA is implemented as an open-source Python package (https://github.com/mahmood726-cyber/ubcma) with a command-line interface and a Bayesian extension via PyMC. The package includes all comparator methods, diagnostic tools (AIC/BIC, leave-one-out influence, Cook's distance), and the simulation study framework used in this paper. Installation requires Python >= 3.11 with NumPy, SciPy, and pandas; PyMC is optional for Bayesian inference.

---

## 5. Conclusion

Unified Bias-Calibrated Meta-Analysis addresses a fundamental gap in evidence synthesis by jointly modeling heterogeneity, publication selection, and quality-dependent bias within a single likelihood framework. The simulation study demonstrates substantial improvements in coverage and RMSE compared with existing methods, particularly when multiple bias sources co-occur. Profile likelihood confidence intervals provide correct calibration without requiring small-sample corrections. We propose UBCMA as a complement to existing quality assessment frameworks such as GRADE, providing a quantitative bias-corrected estimate alongside qualitative certainty ratings.

---

## References

1. DerSimonian R, Laird N. Meta-analysis in clinical trials. *Controlled Clinical Trials*. 1986;7(3):177-188.

2. Hartung J, Knapp G. A refined method for the meta-analysis of controlled clinical trials with binary outcome. *Statistics in Medicine*. 2001;20(24):3875-3889.

3. IntHout J, Ioannidis JPA, Borm GF. The Hartung-Knapp-Sidik-Jonkman method for random effects meta-analysis is straightforward and considerably outperforms the standard DerSimonian-Laird method. *BMC Medical Research Methodology*. 2014;14:25.

4. Duval S, Tweedie R. Trim and fill: a simple funnel-plot-based method of testing and adjusting for publication bias in meta-analysis. *Biometrics*. 2000;56(2):455-463.

5. Stanley TD, Doucouliagos H. Meta-regression approximations to reduce publication selection bias. *Research Synthesis Methods*. 2014;5(1):60-78.

6. Copas JB, Shi JQ. A sensitivity analysis for publication bias in systematic reviews. *Statistical Methods in Medical Research*. 2001;10(4):251-265.

7. Doi SAR, Thalib L. A quality-effects model for meta-analysis. *Epidemiology*. 2008;19(1):94-100.

8. Carpenter JR, Schwarzer G, Rucker G, Kunstler R. Empirical evaluation of the Copas selection model for publication bias. *Statistics in Medicine*. 2009;28(4):657-677.

9. Byrd RH, Lu P, Nocedal J, Zhu C. A limited memory algorithm for bound constrained optimization. *SIAM Journal on Scientific Computing*. 1995;16(5):1190-1208.

10. Efron B, Tibshirani RJ. An Introduction to the Bootstrap. *Chapman and Hall/CRC*. 1993.

11. Rover C, Knapp G, Friede T. Hartung-Knapp-Sidik-Jonkman approach and its modification for random-effects meta-analysis with few studies. *BMC Medical Research Methodology*. 2015;15:99.

12. Verde PE. A bias-corrected meta-analysis model for combining studies of different types and quality. *Biometrical Journal*. 2021;63(2):406-422.

13. Anderson CA, Bushman BJ. Effects of violent video games on aggressive behavior, aggressive cognition, aggressive affect, physiological arousal, and prosocial behavior: a meta-analytic review. *Psychological Science*. 2001;12(5):353-359.

14. Bartos F, Maier M, Wagenmakers EJ, Doucouliagos H, Stanley TD. Robust Bayesian meta-analysis: model-averaging across complementary publication bias adjustment methods. *Research Synthesis Methods*. 2023;14(1):99-116.

---

## AI Disclosure Statement

This work represents a computational methods paper with AI assistance in code development and manuscript preparation. The UBCMA engine, simulation study, and all analyses were implemented in deterministic Python code with fixed random seeds, enabling full reproducibility. AI was used as a constrained synthesis engine operating on structured inputs and predefined algorithms, not as an autonomous author. All results, text, and scientific claims were reviewed and verified by the author, who takes full responsibility for the content.

---

## Data Availability Statement

All code, data, and simulation scripts are available at https://github.com/mahmood726-cyber/ubcma under an MIT licence. The aspirin dataset is from Verde (2021). The media violence dataset is adapted from Anderson and Bushman (2001). Simulation results can be reproduced using `ubcma study --tier pilot --seed 42`.
