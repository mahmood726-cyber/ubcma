# Independent Third-Vendor Correctness Bug-Review: AdaptShrink Core Estimator

This document presents the first-principles review of the core proposed AdaptShrink estimator package in the `methods-borrowing` branch of `F:\ubcma`.

## Core Files Reviewed
1. `src\ubcma\adaptshrink.py`
2. `src\ubcma\inference.py`
3. `src\ubcma\model.py`

---

## 1. Summary of Major and Minor Defects

### Defect 1: Severe Underestimation of Within-Member Variance (AdaptShrink Analytical Interval)
* **File & Line:** `src\ubcma\adaptshrink.py:147`
* **Severity:** High
* **Concrete Failure:** 
  In calculating the model-averaging variance, the code computes the within-member sampling variance of the weighted mean as:
  ```python
  within_var = float(np.sum(np.square(w) * s2) / (w_sum ** 2))
  ```
  which corresponds to the formula $\mathrm{Var}(\sum \bar{w}_j \mu_j) = \sum \bar{w}_j^2 s_j^2$. This formula assumes that the individual estimator errors ($\mu_j - E[\mu_j]$) are **independent**.
  However, all members of the panel (`ubcma`, `pet_peese`, `trim_and_fill`) are fitted on the *exact same dataset* $(y, se)$. Their sampling errors are highly correlated (correlation $\approx 1.0$).
  Under perfect correlation, the variance of the weighted average is $(\sum \bar{w}_j s_j)^2$, not $\sum \bar{w}_j^2 s_j^2$.
  For $N$ identical models with equal weights, the formula used in the code reduces within-member variance to $s^2 / N$ rather than $s^2$. For the default $N=3$ panel, this underestimates the within-member variance component by a factor of 3 (and underestimates the corresponding standard error by $\sqrt{3} \approx 1.732$). This results in overly narrow confidence intervals and sub-nominal coverage.
* **Affects Shipped Headline:** Yes, it directly affects the **shipped AdaptShrink headline** (calibrated deployable win vs DL/HKSJ/HC/Copas/PET). While matched-coverage scoring adjusts the calibration multiplier $\kappa$ to compensate for this during bake-offs, the "deployable raw coverage" (where $\kappa = 1.0$) is severely compromised, and the required calibration multiplier $\kappa$ will be artificially inflated (e.g. $\kappa \approx \sqrt{N}$ even in the absence of other bias/selection issues) to achieve nominal coverage.

---

### Defect 2: Unprotected BCa Quantiles Denominator in Bootstrap CI (Zero Division / Sign Flips)
* **File & Line:** `src\ubcma\inference.py:504`
* **Severity:** Medium
* **Concrete Failure:** 
  In the BCa bootstrap adjusted quantile calculation, the code implements:
  ```python
  adj = z0 + num / (1.0 - a_hat * num)
  ```
  where `num = z0 + z_alpha`. The term `1.0 - a_hat * num` is not guarded against zero or negative values. If `a_hat * num >= 1.0` (which is common when the acceleration parameter $a$ is positive and $z_0$ or the quantile $z_{\alpha}$ is large), the denominator can become zero (causing a `ZeroDivisionError`) or negative. 
  A negative denominator flips the sign of the adjustment term, pushing the quantile to the opposite extreme before it is passed to `_norm.cdf(adj)`. Although the output is subsequently clipped using `np.clip(..., 0.001, 0.999)`, the computed quantile is corrupted and mathematically incorrect.
* **Affects Shipped Headline:** Internal path. The AdaptShrink headline uses analytical intervals and is unaffected, but any user requesting BCa bootstrap intervals via `inference.py` is exposed to this stability and correctness issue.

---

### Defect 3: Path-Dependency and Local Minima in Profile Likelihood Bisection
* **File & Line:** `src\ubcma\inference.py:223-241`
* **Severity:** Medium
* **Concrete Failure:** 
  The warm-start vector `_last_nuisance` is modified in-place and shared nonlocally inside `profile_at`. During bisection, the target parameter `mu_val` jumps back and forth. Because the penalized log-likelihood of selection models with mixture heterogeneity is highly non-convex and multi-modal, warm-starting from the previous evaluation point causes the optimizer to get stuck in different local minima depending on the bisection search path. This introduces path-dependency, making the profile likelihood curve and the resulting CI bounds unstable and dependent on the initial bracket size.
* **Affects Shipped Headline:** Internal path. This affects only the profile likelihood confidence intervals in `inference.py`, which is an alternative inference option.

---

### Defect 4: Ineffective BCa Jackknife Acceleration for $k=4$ Studies
* **File & Line:** `src\ubcma\inference.py:487`
* **Severity:** Low / Boundary Case
* **Concrete Failure:** 
  When the dataset has $n=4$ studies (the minimum required for a stable fit under `model.py:389`), the jackknife leave-one-out datasets have size $n-1 = 3$. 
  Inside `_bca_ci`, fitting the jackknife datasets via `fitter.fit(jack_data)` will always raise `ValueError: UBCMA needs at least 4 studies for a stable fit.`. 
  The code catches this exception and falls back to:
  ```python
  except Exception:
      jack_mus.append(mle_mu)
  ```
  Since all jackknife estimates fall back to `mle_mu`, the difference `diff = jack_mean - jack_mus` is exactly zero, making the acceleration parameter $a = 0.0$. The BCa interval falls back to a simple bias-corrected (BC) interval.
* **Affects Shipped Headline:** Internal path. It degrades BCa to BC when $n=4$ but does not crash, showing acceptable fail-closed behavior.
