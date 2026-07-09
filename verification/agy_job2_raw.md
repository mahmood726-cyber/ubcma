# Correctness Bug-Review: Statistical Methods (branch methods-borrowing)

This report presents the findings of an independent third-vendor correctness bug-review of the statistical methods code in the `F:\ubcma` repository (branch `methods-borrowing`).

---

## 1. Summary of New Correctness Defects

| # | File:Line | Severity | Defect Type | Concrete Failure & Why It Is Wrong | Scope Affected |
|---|---|---|---|---|---|
| **1** | `src/ubcma/comparators.py:240` | **P0** | Wrong estimator & variance / silent naive pool | The `quality_effects` model (Doi et al. 2015, IVhet-based) is implemented with the standard weighted fixed-effect variance `se_mu = float(np.sqrt(1.0 / np.sum(w)))`. It completely fails to perform the quasi-likelihood overdispersion expansion or $\tau^2$-based variance inflation that defines Doi's QE/IVhet model. When `quality_scores` is None, it silently returns the naive, uncorrected fixed-effect pool standard error. This severely underestimates standard errors and produces too-narrow confidence intervals when heterogeneity is present. | Internal comparator column |
| **2** | `src/ubcma/comparators.py:280` | **P1** | NaN/edge-case path | `knapp_hartung_adjustment` lacks a guard for small sample sizes. If `k = 1`, the division by `k - 1` triggers a `ZeroDivisionError`. Additionally, the degrees of freedom `df = k - 1 = 0` is passed to `t_dist.ppf`, which is invalid and returns `NaN`. | Internal comparator column (REML/HKSJ) |
| **3** | `src/ubcma/comparators.py:101` | **P1** | Wrong variance/pooling | In `trim_and_fill`, the standard error `se_adj` is calculated using the fixed-effect formula `se_adj = float(np.sqrt(1.0 / np.sum(1.0 / np.square(se_fill))))`. Under the random-effects assumption, this completely ignores the between-study variance $\tau^2$ of the filled dataset, leading to severely underestimated standard errors under heterogeneity. | Internal comparator column |
| **4** | `transport_nma/aact_kappa.py:127`, `129` | **P1** | Truthiness guard dropping valid 0.0 | The conditions `if sp['mean_amd'] and sr['mean_amd']:` and `if sp['mean_z'] and sr['mean_z']:` check the truthiness of float values. If either mean is exactly `0.0` (a legitimate value indicating zero selection bias), the guard evaluates to `False`. This prevents the calculation of `kmd` or `kz` (leaving them as `None`), which propagates to `aact_kappa_freeze.py` and causes that drug class to be silently skipped. | External selection strength (kappa values) |
| **5** | `transport_nma/aact_kappa.py:110` | **P1** | Non-comparable subset mixing | In `summ(lst)`, `mean_amd` is computed over all trials in the drug class, while `mean_z` is computed only over the subset of trials that have a valid standard error (where `z is not None`). Because these two metrics are computed on different subsets of trials, `kappa_md` and `kappa_z` are computed on different populations and are not comparable. | External selection strength (kappa values) |
| **6** | `borrowing/field_scale/field_learned.py:181` | **P2** | Wrong variance (double-counting) | In `predict_loo`, `sd` is returned as `np.sqrt(1.0 / np.diag(Kinv))`, which is the standard deviation of the predictive distribution of the *observed* study value (already including the study's own sampling variance $se_i^2$). In `score`, the half-width is calculated as `hw = z * np.sqrt(sd ** 2 + se_t ** 2)`, which adds the sampling variance `se_t ** 2` a second time, leading to overly wide confidence intervals. | Reference LOO GP predictions |

---

## 2. Review of Previously Reported Defects

### Defect A: `copas_selection` returning the `rho=0` uncorrected pool because the grid loop stored no likelihood.
* **Status**: **STILL BUGGY** (and a **NEW related issue**).
* **Detailed Analysis**: 
  * The current code attempts to resolve the issue by saving `"nll": nll_adj` inside the results of the grid loop and selecting `best = min(scored, key=lambda r: r["nll"])`. 
  * However, there is a fundamental mathematical error in the objective function `_copas_nll`. The line `ll += np.sum(np.log(Phi_u))` adds the log selection probability to the log-likelihood (which translates to subtracting it in the NLL). This acts as a heavy penalty that drives the probit selection probability $\Phi(u_i)$ to 1 ($\gamma_0 \to \infty$). Consequently, the optimization at each `rho` collapses back to the unselected state (no selection correction), and the returned estimate `mu` remains biased toward the naive uncorrected pool.
  * In addition, the standard error `se_adj` is calculated using the naive random-effects formula `sqrt(1.0 / sum(w_adj))` instead of using the Hessian from the joint selection model, which underestimates the standard error of the selection-corrected estimate by ignoring parameter estimation uncertainty.

### Defect B: `field_learned` k-fold building test features on a different block than it trained on so category codes / standardization diverged.
* **Status**: **CORRECT** (fix present and sound for category code alignment), but with a **NEW related issue** (covariate leakage).
* **Detailed Analysis**: 
  * The code now builds the feature embedding once on the full block `sub` before the fold loop (`X = build_features(sub)`) and slices it inside the fold loop (`X[tr]`, `X[te]`). This successfully prevents category code and standardization divergence.
  * However, this implementation introduces **covariate leakage** from the test fold into the training features. The standardization statistics (mean and standard deviation) and categorical integer mapping are fit on the full block (including the held-out test data) rather than on the training subset only. While this is covariate-only leakage (no target `yi` values enter `build_features`), it is a departure from strict machine learning validation hygiene.

---

## 3. Detailed Verification & Mathematical Rationale

### Quality-Effects Variance
In Doi's Quality-Effects model, the weights are adjusted by quality scores:
$$ w_i = w_{iv, i} \cdot q_{weights, i} $$
However, the variance of the pooled estimate is not the standard fixed-effect variance $\frac{1}{\sum w_i}$. The QE and IVhet models adjust the standard error to account for heterogeneity using a scale parameter (or overdispersion factor):
$$ \text{Var}(\hat{\mu}) = \sum \left( \frac{w_i}{\sum w_i} \right)^2 (\text{se}_i^2 + \tau^2) $$
The current code in `quality_effects` uses `se_mu = float(np.sqrt(1.0 / np.sum(w)))`, which completely omits this adjustment, leading to severe underestimation of the variance under heterogeneity.

### Copas Likelihood Objective Function
For the observed studies, the likelihood is conditional on selection:
$$ L_c = \prod_{i=1}^k f(y_i \mid \text{selected}_i) = \prod_{i=1}^k \frac{f(y_i) P(\text{selected}_i \mid y_i)}{P(\text{selected}_i)} $$
Thus, the log-likelihood is:
$$ \log L_c = \sum_{i=1}^k \log f(y_i) + \sum_{i=1}^k \log P(\text{selected}_i \mid y_i) - \sum_{i=1}^k \log P(\text{selected}_i) $$
In the code, `Phi_u` is $P(\text{selected}_i) = \Phi(u_i)$. The code does:
`ll += np.sum(np.log(Phi_u))` (where `ll` is the log-likelihood).
Since `ll` is returned as `-ll` (the NLL), this term is added to the NLL, which acts as a penalty that tries to maximize $\Phi(u_i)$ by driving it to 1 ($\gamma_0 \to \infty$), rendering the selection correction ineffective.

### GP LOO Variance Double-counting
In `predict_loo`, `sd` is computed as $\sqrt{1 / K^{-1}_{ii}}$. Since $K = K_f + \text{diag}(\alpha + \text{nugget})$ contains the study-specific noise variance $\alpha_i = \text{se}_i^2$, the term $1 / K^{-1}_{ii}$ is the predictive variance of the *observed* study value $y_i$, which already includes $\text{se}_i^2$.
When the performance is scored in `score`:
`hw = z * np.sqrt(sd ** 2 + se_t ** 2)`
the study noise `se_t ** 2` is added again, double-counting the sampling variance and resulting in artificially wide confidence intervals.
