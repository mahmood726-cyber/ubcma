# Independent Third-Vendor Bug-Review: Single-Arm Proportion Meta-Analysis Engines
**Repository:** [ubcma](file:///F:/ubcma)  
**Branch:** `methods-borrowing`  
**Date:** 2026-07-04  

This review investigates the presence and statistical safety of single-arm proportion meta-analysis engines within the [ubcma](file:///F:/ubcma) codebase, evaluating them against standard meta-analytic requirements (small-$k$ guards for between-study variance estimation, proper continuity corrections, back-transformation bias adjustments, and confidence interval properties on the proportion scale).

---

## 1. Presence / Absence Determination

> [!NOTE]
> A dedicated, general-purpose "single-arm proportion forest plot" or "single-arm proportion pooling engine" (such as the sister repository's JS implementation `vendor/single-arm-forest.js`) is **ABSENT** from the [ubcma](file:///F:/ubcma) repository.
> 
> However, proportion pooling and transformation logic is **PRESENT** across three locations in [ubcma](file:///F:/ubcma):
> 1. **Diagnostic Test Accuracy (DTA) Pooling:** Bivariate DTA models pool two sets of single-arm proportions (Sensitivity and Specificity). The module [dta.py](file:///F:/ubcma/src/ubcma/dta.py) includes a univariate pooling method [sep_univariate](file:///F:/ubcma/src/ubcma/dta.py#L348-L373) that performs independent logit-proportion pooling using the DerSimonian-Laird (DL) method.
> 2. **Replication Experiment Preprocessing:** The experiment module [multispecialty.py](file:///F:/ubcma/borrowing/replication/multispecialty.py) includes [build_ursino](file:///F:/ubcma/borrowing/replication/multispecialty.py#L65-L74), which applies an unconditional continuity correction to single-arm dose-toxicity proportions.
> 3. **Exact Binomial Dose-Response:** The module [drma_binomial.py](file:///F:/ubcma/doseresponse/drma_binomial.py) implements a one-stage exact binomial random-intercept logistic dose-response model, avoiding continuity corrections and log-scale transformation biases.

---

## 2. Review of Identified Proportion Logic

### A. $\tau^2$ Heterogeneity Method (Small-$k$ Guard)
In [sep_univariate](file:///F:/ubcma/src/ubcma/dta.py#L348-L373), the inner function `_dl` implements the DerSimonian-Laird (DL) random-effects estimator:
```python
    def _dl(y, s2):
        w = 1.0 / s2
        mu_fe = np.sum(w * y) / np.sum(w)
        Q = float(np.sum(w * (y - mu_fe) ** 2))
        k = len(y)
        c = np.sum(w) - np.sum(w ** 2) / np.sum(w)
        tau2 = max((Q - (k - 1)) / c, 0.0) if c > 0 else 0.0
        wr = 1.0 / (s2 + tau2)
        mu = np.sum(wr * y) / np.sum(wr)
        var = 1.0 / np.sum(wr)
        return mu, var, tau2
```
* **Review:** The DL $\tau^2$ calculation has **no small-$k$ guard**. It operates at any $k \geq 2$. When the number of studies $k$ is small, the DL estimator has high bias and underestimates the between-study variance, leading to overly narrow confidence intervals. This contrasts with other parts of the suite that use Paule-Mandel or REML, or enforce fixed-effect fallbacks for small $k$.

### B. Continuity Correction
* **In DTA Preprocessing (`from_counts`):**
  [from_counts](file:///F:/ubcma/src/ubcma/dta.py#L94-L137) defaults to `correction_control = "all"`:
  ```python
      any_zero = bool(np.any((tp == 0) | (fp == 0) | (fn == 0) | (tn == 0)))
      if correction_control == "all":
          need = np.ones(len(tp), bool) if any_zero else np.zeros(len(tp), bool)
  ```
  If *any* study contains a zero cell, a continuity correction of `0.5` is added to *every* cell of *every* study (including those without zeros). Even with `correction_control = "single"`, the correction is applied to all four cells of the affected study, which adjusts non-zero cells.
* **In Experiment Preprocessing (`build_ursino`):**
  [build_ursino](file:///F:/ubcma/borrowing/replication/multispecialty.py#L65-L74) applies:
  ```python
          ev, tot = float(r["events"]), float(r["total"])
          p = (ev + 0.5) / (tot + 1.0)
          y = float(np.log(p / (1 - p)))
          se = float(np.sqrt(1/(ev + 0.5) + 1/(tot - ev + 0.5)))
  ```
  This adds `0.5` to events and `0.5` to non-events unconditionally for every study in the dataset, regardless of whether any zero cells are present.
* **Review:** Both methods violate the best practice of applying a continuity correction **only when a cell is 0**. Unconditional corrections pull extreme proportions toward `0.5` and introduce unnecessary bias, particularly in small-sample trials.

### C. Back-Transform Bias
In [_summarize](file:///F:/ubcma/src/ubcma/dta.py#L252-L277) (called by [sep_univariate](file:///F:/ubcma/src/ubcma/dta.py#L348-L373)):
```python
    se_sum = float(1.0 / (1.0 + np.exp(-M[0])))
    sp_sum = float(1.0 / (1.0 + np.exp(-M[1])))
```
* **Review:** A simple logit back-transform (the logistic sigmoid) is applied directly to the pooled pooled mean logit. This ignores the back-transform bias introduced by Jensen's inequality in the presence of between-study random-effects variance $\tau^2$ (i.e., $E[\text{logit}^{-1}(X)] \neq \text{logit}^{-1}(E[X])$). No Freeman-Tukey double-arcsine transformation or harmonic-mean-N back-transform adjustments are present in this codebase.

### D. Confidence Intervals on the Proportion Scale
In [_summarize](file:///F:/ubcma/src/ubcma/dta.py#L252-L277):
```python
    se_lo = float(1.0 / (1.0 + np.exp(-(M[0] - z * np.sqrt(V[0, 0])))))
    se_hi = float(1.0 / (1.0 + np.exp(-(M[0] + z * np.sqrt(V[0, 0])))))
```
* **Review:** Confidence intervals are calculated as symmetric Wald intervals on the logit scale (`M - z * SE`) and then back-transformed. This method does not compute proper score-based intervals (such as Wilson score intervals) on the proportion scale and can exhibit poor coverage properties when proportions are close to `0` or `1`.

---

## 3. Detailed Findings List

| Finding ID | File & Lines | Severity | Shipped vs. Internal | Description |
|---|---|---|---|---|
| **FINDING-01** | [dta.py:356-366](file:///F:/ubcma/src/ubcma/dta.py#L356-L366) | **P1** | Shipped/Internal | `sep_univariate` pools logit-proportions using raw DerSimonian-Laird (DL) $\tau^2$ at any $k \geq 2$ with no small-$k$ guard. This can lead to underestimated heterogeneity and overly narrow CIs when $k$ is small. |
| **FINDING-02** | [dta.py:116-128](file:///F:/ubcma/src/ubcma/dta.py#L116-L128) | **P1** | Shipped/Internal | `from_counts` applies a continuity correction of `0.5` to every study in the meta-analysis if any single cell is zero (under the default `"all"` setting). Under the `"single"` setting, it corrects non-zero cells in zero-containing studies. |
| **FINDING-03** | [multispecialty.py:69-72](file:///F:/ubcma/borrowing/replication/multispecialty.py#L69-L72) | **P2** | Internal | `build_ursino` applies an unconditional `0.5` continuity correction to events and non-events for every study in the Ursino dataset, regardless of whether zero cells exist. |
| **FINDING-04** | [dta.py:255-262](file:///F:/ubcma/src/ubcma/dta.py#L255-L262) | **P1** | Shipped/Internal | `sep_univariate` back-transforms the logit pooled estimate and Wald intervals directly to the proportion scale via the logistic sigmoid. It does not correct for back-transformation bias or calculate score-based CIs on the proportion scale. |

> [!TIP]
> **Modern Alternative:** The module [drma_binomial.py](file:///F:/ubcma/doseresponse/drma_binomial.py) models study-level proportions natively using exact binomial likelihoods and adaptive Gauss-Hermite quadrature, which avoids continuity corrections, log-scale transformations, and back-transformation bias. However, this is a dose-response model rather than a general-purpose single-arm pooling engine.
