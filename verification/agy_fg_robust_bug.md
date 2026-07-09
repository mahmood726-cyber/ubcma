# Robust Methods Engine Independent Third-Vendor Correctness Review Report

This report documents correctness defects verified from first principles in the robust estimation, diagnostics, Bayesian, and Fisher-z components of `F:\ubcma` (branch `methods-borrowing`).

## Methodology
- Evaluation of heterogeneity estimators (DerSimonian-Laird, REML, and Knapp-Hartung/HKSJ adjustment).
- Verification of publication bias diagnostics (Egger, Peters, PET-PEESE, and Trim-and-fill usage).
- Examination of Bayesian MCMC sampler diagnostic handling (Rhat, ESS, divergences, log-scale pooling).
- Mathematical verification of Fisher-z transformations and logit clamping.

---

## Findings

### Finding 1: Unconditional use of DerSimonian-Laird for small samples ($k < 10$) in robust estimators
- **File:Line**: [src/ubcma/robust_methods.py:74](file:///F:/ubcma/src/ubcma/robust_methods.py#L74)
- **Severity**: P1
- **Concrete Failure**: The function `random_effects` computes $\tau^2$ using `dl_tau2` (DerSimonian-Laird) unconditionally. Under the rule "DL must NOT be used for k<10 (REML/PM instead)", the estimator violates this constraint when $k < 10$. This affects `adaptshrink` and `adaptshrink_conformal` because they rely on `random_effects(y, se)` for the naive RE mean and heterogeneity scale.
- **Shipped-vs-internal**: Shipped (library model).

### Finding 2: Unconditional use of DerSimonian-Laird for small samples ($k < 10$) in leave-one-out diagnostics
- **File:Line**: [src/ubcma/diagnostics.py:166](file:///F:/ubcma/src/ubcma/diagnostics.py#L166)
- **Severity**: P1
- **Concrete Failure**: In the leave-one-out diagnostic `leave_one_out`, the code computes the baseline variance of the pooled mean `var_mu` using `dersimonian_laird(data.y, data.se)`:
  ```python
  dl = dersimonian_laird(data.y, data.se)
  var_mu = max(dl["se"] ** 2, 1e-12)
  ```
  This value is used as the scaling denominator for Cook's distance. Since many meta-analyses have $k < 10$ (the framework permits $k \ge 4$), this uses DL instead of REML or PM, violating the rule.
- **Shipped-vs-internal**: Shipped (library model).

### Finding 3: Unconditional use of DerSimonian-Laird for starting values in selection models
- **File:Line**: [src/ubcma/modern_comparators.py:136](file:///F:/ubcma/src/ubcma/modern_comparators.py#L136) and [src/ubcma/modern_comparators.py:226](file:///F:/ubcma/src/ubcma/modern_comparators.py#L226)
- **Severity**: P2
- **Concrete Failure**: The estimators `p_uniform_star` and `vevea_hedges_step` initialize their optimizations using the DerSimonian-Laird estimate `base = dersimonian_laird(y, se)` as starting coordinates. If $k < 10$, this utilizes DL instead of REML or PM.
- **Shipped-vs-internal**: Shipped (library model).

### Finding 4: Inadequate enforcement and interpretation of Bayesian sampler diagnostics
- **File:Line**: [src/ubcma/bayesian.py:263-271](file:///F:/ubcma/src/ubcma/bayesian.py#L263)
- **Severity**: P1
- **Concrete Failure**: If MCMC diagnostics fail (e.g. $R_{\text{hat}} > 1.01$, $\text{ESS} < 400$, or divergent transitions are detected), `BayesianUBCMAFit` prints warning messages via `warnings.warn` but still returns a normal results object and permits interpretation of the estimates. Under the rules:
  1. $R_{\text{hat}} > 1.01$ must *not* be interpreted (the function should block access, return NaN, or raise an error).
  2. $\text{ESS} < 400$ should be explicitly flagged as unreliable.
  3. Divergent transitions are not handled (they should trigger re-parameterization or adaptively increase `target_accept`).
- **Shipped-vs-internal**: Shipped (library model).

### Finding 5: Sigmoid probability clamping uses $1\times 10^{-9}$ instead of $1\times 10^{-10}$
- **File:Line**: [src/ubcma/bayesian.py:202](file:///F:/ubcma/src/ubcma/bayesian.py#L202) and [src/ubcma/bayesian.py:223](file:///F:/ubcma/src/ubcma/bayesian.py#L223)
- **Severity**: P2
- **Concrete Failure**: The selection probability and quadrature nodes are clamped to `[1e-9, 1.0 - 1e-9]`:
  ```python
  p_sel = pt.clip(pm.math.sigmoid(sel_linear), 1e-9, 1.0 - 1e-9)
  ```
  This restricts the probability space further than the rule-mandated `[1e-10, 1 - 1e-10]`. *(Note: The optimization model in `model.py:260` also utilizes `1e-9` clamping).*
- **Shipped-vs-internal**: Shipped (library model).

### Finding 6: Non-exact Fisher-z variance calculation for small samples
- **File:Line**: [borrowing/field_scale/corpus.py:66](file:///F:/ubcma/borrowing/field_scale/corpus.py#L66) and [borrowing/field_scale/corpus.py:153](file:///F:/ubcma/borrowing/field_scale/corpus.py#L153)
- **Severity**: P1
- **Concrete Failure**: The sampling variance of the Fisher-z transformed correlation coefficient is calculated as:
  ```python
  vz = 1.0 / np.maximum(n - 3, 1.0)
  ```
  and for partial correlations:
  ```python
  vz = 1.0 / np.maximum(df.n - df.preds - 3, 1.0)
  ```
  The exact mathematical sampling variance is $\frac{1}{n-3}$. If $n \le 3$ (or $n - p \le 3$), the variance is infinite/undefined. By clamping the denominator to `1.0`, the code silently assigns a finite variance of `1.0` to these studies, giving them disproportionate weight during borrowing-field pooling.
- **Shipped-vs-internal**: Internal (borrowing preprocessing script).

### Finding 7: Knapp-Hartung Adjustment uses incorrect floor logic and lacks $k=1$ guard
- **File:Line**: [src/ubcma/comparators.py:281](file:///F:/ubcma/src/ubcma/comparators.py#L281)
- **Severity**: P1
- **Concrete Failure**:
  1. The Knapp-Hartung scaling factor `q_hksj` is calculated using random-effects weights and is capped as `q_hksj = max(q_hksj, 1.0)`. Under the rule, the floor must be `max(1, Q/(k-1))` where $Q$ is Cochran's $Q$ statistic (calculated using fixed-effects weights), i.e., $Q = \sum w_{\text{FE}} (y_i - \hat{\mu}_{\text{FE}})^2$.
  2. If the number of studies $k = 1$, the function divides by `k-1 = 0`, causing a division-by-zero that yields `NaN` or `inf` without a guard.
- **Shipped-vs-internal**: Shipped (library model).

### Finding 8: Trim-and-Fill is incorrectly included in the primary point estimation panel
- **File:Line**: [src/ubcma/adaptshrink.py:58](file:///F:/ubcma/src/ubcma/adaptshrink.py#L58)
- **Severity**: P1
- **Concrete Failure**: In the model-averaging estimator `adaptshrink_estimator`, the default member list includes `trim_and_fill`:
  ```python
  DEFAULT_MEMBERS = ("ubcma", "pet_peese", "trim_and_fill")
  ```
  This uses `trim_and_fill` as a core point estimator for calculating the primary pooled estimate `mu_as`. Under the rule, the trim-and-fill method is for "sensitivity only" and must not be used as a primary point estimator or component in the main aggregation model.
- **Shipped-vs-internal**: Shipped (library model).

### Finding 9: Absence of Peters Test and Egger Radial Version in Diagnostics
- **File:Line**: [src/ubcma/diagnostics.py:1](file:///F:/ubcma/src/ubcma/diagnostics.py#L1) (entire module)
- **Severity**: P1
- **Concrete Failure**: The diagnostics module lacks the Peters test for binary outcomes and the Egger radial test formulation. Under the rule, these publication bias tests must be present in the suite.
- **Shipped-vs-internal**: Shipped (library model).
