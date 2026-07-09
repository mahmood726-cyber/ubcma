# PET-PEESE Standard Error Scaling Verification & Fix Proposal

This report documents the independent verification of a discrepancy between the comparator and robust implementation of the PET-PEESE bias-correction estimators.

---

## Executive Summary

- **Verdict:** **CONFIRMED**
- **Target File:** [comparators.py](file:///F:/ubcma/src/ubcma/comparators.py)
- **Target Lines:** 
  - [comparators.py:123](file:///F:/ubcma/src/ubcma/comparators.py#L123) (`intercept_se` for PET)
  - [comparators.py:137](file:///F:/ubcma/src/ubcma/comparators.py#L137) (`se_mu` for PEESE)
- **Defect:** Omission of the multiplicative residual-dispersion scaling factor ($\sigma^2$) in the comparator's weighted least squares (WLS) covariance estimation.
- **Inconsistency:** [robust_methods.py:100-104](file:///F:/ubcma/src/ubcma/robust_methods.py#L100) correctly estimates $\sigma^2 = \sum w_i e_i^2 / \max(k-2, 1)$ and scales `covb = cov * sigma2`. The comparator implementation in `comparators.py` implicitly assumes $\sigma^2 \equiv 1$, underestimating standard errors under heterogeneity.

---

## 1. Mathematical Verification from First Principles

In a WLS regression model for publication bias (e.g., PET: $y_i = \beta_0 + \beta_1 \text{se}_i + \epsilon_i$), the studies are weighted by $w_i = 1/\text{se}_i^2$. 

The model assumes:
$$\text{Var}(\epsilon_i) = \sigma^2 \text{se}_i^2$$

where $\sigma^2$ is the residual-dispersion parameter reflecting between-study heterogeneity not captured by the within-study variances. 

The parameter estimator is:
$$\hat{\beta} = (X^T W X)^{-1} X^T W Y$$

Using the covariance propagation rule, the variance-covariance matrix of $\hat{\beta}$ is:
$$\text{Cov}(\hat{\beta}) = (X^T W X)^{-1} X^T W \text{Cov}(Y) W X (X^T W X)^{-1}$$

Substituting the model assumption $\text{Cov}(Y) = \sigma^2 W^{-1}$:
$$\text{Cov}(\hat{\beta}) = (X^T W X)^{-1} X^T W (\sigma^2 W^{-1}) W X (X^T W X)^{-1} = \sigma^2 (X^T W X)^{-1}$$

In standard meta-regression practice (e.g., Stanley & Doucouliagos 2012; R's `metafor` package), $\sigma^2$ is estimated from the weighted residuals to account for extra-dispersion:
$$\sigma^2 = \frac{\sum_{i=1}^k w_i (y_i - x_i \hat{\beta})^2}{k - 2}$$

Omitting $\sigma^2$ (i.e. assuming $\sigma^2 \equiv 1$) is valid only when there is no residual heterogeneity. In the presence of heterogeneity (typical in real-world meta-analyses), $\sigma^2 > 1$. Omitting it under-scales the standard error of the intercept ($\beta_0$) by a factor of $\sqrt{\sigma^2}$.

### Code Inconsistency
In [comparators.py](file:///F:/ubcma/src/ubcma/comparators.py#L122-L123):
```python
cov_pet = np.linalg.pinv(xtw @ x_pet)
intercept_se = np.sqrt(max(cov_pet[0, 0], 0.0))
```
This assumes $\sigma^2 = 1.0$.

In [robust_methods.py](file:///F:/ubcma/src/ubcma/robust_methods.py#L97-L104):
```python
cov = np.linalg.pinv(xtwx)
...
resid = y - X @ beta
dof = max(k - 2, 1)
sigma2 = float(np.sum(w * np.square(resid)) / dof)
covb = cov * sigma2
```
This correctly scales the covariance by $\sigma^2$.

---

## 2. Impact Analysis on Shipped Artifacts

### A. Manuscript Worked Example (Table 3)
The worked example uses the aspirin dataset [verde_2021_aspirin.csv](file:///F:/ubcma/examples/verde_2021_aspirin.csv) ($k = 6$, high heterogeneity). Running a sensitivity verification confirms the following:

#### 1. PET-PEESE (Standalone)
Under PEESE (which is selected by the PET test), the residual dispersion is $\sigma^2 = 3.778$. Omitting it under-scales the SE of $\hat{\mu}$ by a factor of $\sqrt{3.778} \approx 1.944$.
* **As-shipped (Unscaled):** 
  - $\hat{\mu} = -0.226719$
  - $\text{SE} = 0.029929$
  - $95\%\text{ CI} = [-0.285379, -0.168060]$ (Width: $0.1173$)
* **Corrected (Scaled):**
  - $\hat{\mu} = -0.226719$
  - $\text{SE} = 0.058175$
  - $95\%\text{ CI} = [-0.340739, -0.112699]$ (Width: $0.2280$)
  - **Change:** Standalone PET-PEESE CI width **increases by 94.4%**.

#### 2. AdaptShrink Ensemble (`adaptshrink_auto`)
Because PET-PEESE is a member of the AdaptShrink panel, its artificially low SE gives it excessive weight in the ensemble model-averaging formula $w_j = 1 / (se_j^2 + \text{disagreement}_j)$:
* **As-shipped Weighting:**
  - `pet_peese` weight: **51.0%** (SE = $0.0299$)
  - `trim_and_fill` weight: **48.3%**
  - `ubcma` weight: **0.7%**
  - Pooled $\hat{\mu}_{\text{AS}} = -0.236643$
  - Calibrated $95\%\text{ CI} = [-0.417408, -0.055878]$ (reported as `[-0.417, -0.056]`)
* **Corrected Weighting:**
  - `pet_peese` weight: **21.6%** (SE = $0.0582$)
  - `trim_and_fill` weight: **77.2%**
  - `ubcma` weight: **1.2%**
  - Pooled $\hat{\mu}_{\text{AS}} = -0.242594$
  - Calibrated $95\%\text{ CI} = [-0.454810, -0.030378]$
  - **Change:** Pooled point estimate shifts slightly protective; AdaptShrink interval width **increases by 17.4%** (from $0.3615$ to $0.4244$).

### B. Shipped Simulation Results (`pilot_summary.csv`)
- **PET-PEESE coverage:** Shipped as `0.645`. Correcting the SE to include $\sigma^2 > 1$ under heterogeneity will widen the confidence intervals and **increase the empirical coverage** of PET-PEESE closer to nominal $95\%$. The under-scaled SE made PET-PEESE's coverage look artificially worse.
- **Headline Conclusions:** The core conclusion of the paper (AdaptShrink outperforms DL, REML, and selection correctors under publication bias and heterogeneity) is unaffected. Even with corrected SEs, PET-PEESE still suffers from high variance and bias under selection, while AdaptShrink continues to maintain superior nominal coverage.

---

## 3. Proposed Fix

We propose replacing the SE calculation lines in [comparators.py](file:///F:/ubcma/src/ubcma/comparators.py) with one-line expressions that compute and multiply the WLS residual variance $\sigma^2$.

### Fix 1: PET Intercept SE
**File & Line:** [comparators.py:123](file:///F:/ubcma/src/ubcma/comparators.py#L123)
```diff
-    intercept_se = np.sqrt(max(cov_pet[0, 0], 0.0))
+    intercept_se = np.sqrt(max(cov_pet[0, 0] * np.sum(w * np.square(y - x_pet @ beta_pet)) / max(k - 2, 1), 0.0))
```

### Fix 2: PEESE Intercept SE
**File & Line:** [comparators.py:137](file:///F:/ubcma/src/ubcma/comparators.py#L137)
```diff
-        se_mu = float(np.sqrt(max(cov_peese[0, 0], 0.0)))
+        se_mu = float(np.sqrt(max(cov_peese[0, 0] * np.sum(w * np.square(y - x_peese @ beta_peese)) / max(k - 2, 1), 0.0)))
```

### Expected Numeric Effect Direction
1. **Confidence Interval Widths:** Widens PET-PEESE intervals under heterogeneity ($\sigma^2 > 1$).
2. **Decision Logic Routing:** Increases the PET p-value (reducing false positives/over-rejections of $H_0: \beta_0 = 0$, routing less aggressively to PEESE).
3. **AdaptShrink Weights:** Correctly down-weights PET-PEESE's contribution under high heterogeneity.
