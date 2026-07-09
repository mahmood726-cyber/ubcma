# Independent Third-Vendor Correctness Bug-Review: `ubcma`

This document contains the raw correctness findings for the independent correctness bug-review of the `ubcma` repository (branch `methods-borrowing`) performed on 2026-07-04.

---

## 1. Robust and Heterogeneity Estimators

### Finding 1.1: Knapp-Hartung Adjustment division-by-zero for $k=1$
* **File:Line**: [src/ubcma/comparators.py:267](file:///F:/ubcma/src/ubcma/comparators.py#L267)
* **Severity**: Major
* **Concrete Failure**: The function `knapp_hartung_adjustment` lacks a small-sample guard for $k < 2$. When the number of studies $k = 1$, the degree of freedom `k - 1` becomes `0`. This causes:
  1. A division-by-zero when calculating the scaling factor:
     ```python
     q_hksj = float(np.sum(w * np.square(y - mu)) / (k - 1))
     ```
     yielding `nan` or `inf`.
  2. The degrees of freedom `df = 0` are passed to `t_dist.ppf`, which returns `nan` for the critical value `t_crit`.
  The function returns `nan` confidence intervals instead of throwing an informative error, falling back to a fixed-effect model, or returning appropriate boundaries.
* **Shipped vs. Internal**: Shipped (part of library).

### Finding 1.2: REML Estimator boundary clamping and $k \le 1$ convergence
* **File:Line**: [src/ubcma/comparators.py:35](file:///F:/ubcma/src/ubcma/comparators.py#L35)
* **Severity**: Major
* **Concrete Failure**: 
  1. The restricted maximum likelihood (REML) log-likelihood is minimized over `bounds=(-20, 5)` in `log_tau2`. This caps the estimated $\tau^2$ at $e^5 \approx 148.4$. In meta-analyses of binary outcomes or SMD with large effects, the true between-study variance $\tau^2$ can exceed this ceiling, leading to artificial truncation and underestimation of heterogeneity.
  2. If the number of studies $k \le 1$, the REML log-likelihood is mathematically constant at 0 for all values of $\tau^2$. The function `reml_estimator` does not check for $k < 2$, causing the optimizer to silently converge to an arbitrary boundary value (like $e^{-20}$) rather than failing or returning `NaN`.
* **Shipped vs. Internal**: Shipped (part of library).

---

## 2. Publication-Bias Diagnostics

### Finding 2.1: WLS Standard Error Underestimation in PET-PEESE
* **File:Line**: [src/ubcma/comparators.py:123](file:///F:/ubcma/src/ubcma/comparators.py#L123), [src/ubcma/comparators.py:137](file:///F:/ubcma/src/ubcma/comparators.py#L137)
* **Severity**: Critical
* **Concrete Failure**: The standard errors for the PET and PEESE intercepts are computed directly as the square roots of the diagonal elements of the unscaled covariance matrix `cov_pet = inv(X.T @ W @ X)`:
  ```python
  cov_pet = np.linalg.pinv(xtw @ x_pet)
  intercept_se = np.sqrt(max(cov_pet[0, 0], 0.0))
  ```
  This fails to multiply the covariance by the estimated residual dispersion parameter $\sigma^2 = \frac{1}{k - 2} \sum w_i e_i^2$ (multiplicative dispersion). It implicitly assumes $\sigma^2 \equiv 1$, ignoring any between-study heterogeneity. As a result, the standard errors are severely underestimated, producing artificially large $z$-statistics, leading to:
  1. Over-rejection of $H_0: \beta_0 = 0$ in the PET significance test, which incorrectly routes the model to PEESE instead of PET.
  2. Over-narrow confidence intervals for the final pooled estimate `mu`.
  *Note*: This is inconsistent with `pet_fit` in `robust_methods.py`, which correctly scales the covariance matrix by `sigma2`.
* **Shipped vs. Internal**: Shipped (part of library).

### Finding 2.2: Fixed-Effects SE/CI Force-Applied in Trim-and-Fill
* **File:Line**: [src/ubcma/comparators.py:101](file:///F:/ubcma/src/ubcma/comparators.py#L101)
* **Severity**: Major
* **Concrete Failure**: The `trim_and_fill` function computes its standard error and confidence interval using the fixed-effects formula:
  ```python
  se_adj = float(np.sqrt(1.0 / np.sum(1.0 / np.square(se_fill))))
  ```
  This is applied globally even if the user is running a random-effects meta-analysis. In the presence of heterogeneity ($\tau^2 > 0$), this ignores the between-study variance of the filled dataset, resulting in heavily underestimated standard errors and invalid coverage.
* **Shipped vs. Internal**: Shipped (part of library).

### Finding 2.3: Absence of Essential Publication-Bias Diagnostics
* **File:Line**: [src/ubcma/diagnostics.py:1](file:///F:/ubcma/src/ubcma/diagnostics.py#L1) (entire module)
* **Severity**: Major
* **Concrete Failure**: The diagnostics module is missing standard publication bias checks, specifically:
  - **Peters test for binary outcomes**: Regressing effect size against $1/N_i$ to avoid artifactual correlations between effect size and standard error.
  - **Egger radial test**: An alternative formulation of the Egger regression that is less prone to heteroscedasticity.
  *(Note: A simple Egger radial test is implemented internally in `transport_nma/aact_kappa_truthgate.py:58` for simulation gating, but is not exposed in the main diagnostics suite).*
* **Shipped vs. Internal**: Shipped (part of library).

---

## 3. Bayesian Pooling

### Finding 3.1: Non-Guarding Warnings for Sampler Diagnostics (Rhat/ESS)
* **File:Line**: [src/ubcma/bayesian.py:263-271](file:///F:/ubcma/src/ubcma/bayesian.py#L263)
* **Severity**: Medium
* **Concrete Failure**: When Bayesian sampler diagnostics fail (e.g. $R_{hat} > 1.01$, $\text{ESS} < 400$, or divergent transitions), the code only prints a warning (`warnings.warn`) but returns the result as if it succeeded. These are not hard guards: they do not throw errors or trigger automatic recovery/reparameterization. Furthermore, if $R_{hat}$ or $\text{ESS}$ evaluates to `NaN` (due to sampling failure or single-chain runs), the comparison `diagnostics["max_rhat"] > 1.01` evaluates to `False`, silently bypassing the warning.
* **Shipped vs. Internal**: Shipped (part of library).

### Finding 3.2: Numerical Instability in Gauss-Hermite Selection Normalizer
* **File:Line**: [src/ubcma/bayesian.py:210-231](file:///F:/ubcma/src/ubcma/bayesian.py#L210)
* **Severity**: Major
* **Concrete Failure**: The selection normalizer `e_sel` is computed on the probability scale by summing weighted quadrature nodes and is then clamped at `1e-9`:
  ```python
  e_sel = pt.maximum(e_sel, 1e-9)
  total_ll = pt.sum(log_density + pt.log(p_sel) - pt.log(e_sel))
  ```
  When the expected selection probability is extremely small, this clamping introduces flat gradients into PyMC's NUTS sampler. This flat gradient region prevents step-size optimization, leading to slow compilation/sampling, sampler struggles, and divergent transitions.
* **Shipped vs. Internal**: Shipped (part of library).

---

## 4. Fisher-z Variance & Clamping

### Finding 4.1: Erroneous Clamping of Fisher-z Variance Denominator for $N \le 3$
* **File:Line**: [borrowing/field_scale/corpus.py:66](file:///F:/ubcma/borrowing/field_scale/corpus.py#L66), [borrowing/field_scale/corpus.py:153](file:///F:/ubcma/borrowing/field_scale/corpus.py#L153)
* **Severity**: Major
* **Concrete Failure**: The sampling variance of the Fisher-z transformed correlation coefficient is calculated as:
  ```python
  vz = 1.0 / np.maximum(n - 3, 1.0)
  ```
  and for partial correlations:
  ```python
  vz = 1.0 / np.maximum(df.n - df.preds - 3, 1.0)
  ```
  Mathematically, the sampling variance for correlation $r$ is $v_z = \frac{1}{n-3}$. If $n \le 3$ (or $n - p \le 3$), the variance is infinite or undefined. By clamping the denominator to `1.0`, the code silently assigns a finite variance of `1.0` to these studies. This incorrect math assigns undue weight to extremely small studies during borrowing-field pooling.
* **Shipped vs. Internal**: Internal (borrowing field-scale pre-processing script).
