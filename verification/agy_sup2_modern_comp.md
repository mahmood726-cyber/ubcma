# Independent Third-Vendor Correctness Bug-Review: `ubcma` (Modern Comparators)

This document contains the independent correctness bug-review of the selection-model estimators in `src/ubcma/modern_comparators.py` (branch `methods-borrowing`) performed on 2026-07-04.

---

## 1. Summary of Estimators Reviewed

We reviewed the following selection-model estimators in `src/ubcma/modern_comparators.py`:
* `p_curve`: Simonsohn et al. (2014) p-curve effect estimator (significant studies only).
* `p_uniform_star`: van Aert & van Assen (2016) random-effects conditional estimator (all studies).
* `vevea_hedges_step`: Vevea & Hedges (1995) 2-step weight-function selection model.

---

## 2. Specific Checks & Verdicts

* **Log-scale stability**: **Fail.** Estimators perform likelihood computations on the standard probability scale before taking logs, causing numerical underflow and completely flat likelihood/objective surfaces for negative effect sizes or small study standard errors.
* **Division-by-zero when all/none significant**: **Fail.** `vevea_hedges_step` does not guard against cases where all or none of the studies are significant, leading to unidentifiable selection weights and runaway optimizer parameters. `p_uniform_star` does not check for zero significant studies.
* **Optimizer bounds**: **Fail.** No explicit bounds are placed on the optimizer search space, and the heuristic span for profile likelihood confidence intervals fails to scale with study/estimate standard errors.
* **Silently-wrong sentinels**: **Fail.** `vevea_hedges_step` returns `converged: True` with extreme boundary weight values (e.g., $e^{-30}$ or $e^{20}$) when the weights are completely unidentified.

---

## 3. Detailed Findings and Correctness Reports

### Finding 3.1: Numerical Underflow and Flat Likelihood Surface in `p_uniform_star`
* **File:Line**: [src/ubcma/modern_comparators.py:128-132](file:///F:/ubcma/src/ubcma/modern_comparators.py#L128-L132)
* **Severity**: Major
* **Concrete Failure**:
  The random-effects conditional negative log-likelihood (`negll`) in `p_uniform_star` is computed on the standard probability scale before taking the log:
  ```python
  p_sig = np.clip(norm.sf((C * se - mu) / sd), 1e-300, 1.0)
  p_nsig = np.clip(1.0 - p_sig, 1e-300, 1.0)
  dens = norm.pdf(y, loc=mu, scale=sd)
  cond = np.where(m, dens / p_sig, dens / p_nsig)
  val = -np.sum(np.log(np.maximum(cond, 1e-300)))
  ```
  When the optimizer steps into negative values of $\mu$ (e.g., $\mu \le -5.0$ for a study standard error $se = 0.1$), the argument `(C * se - mu) / sd` becomes large and positive, causing the true `norm.sf` to underflow.
  While `p_sig` is clipped to `1e-300`, `dens = norm.pdf(y, loc=mu, scale=sd)` also underflows to `0.0` (since `norm.pdf` underflows for values $> 38$ standard deviations from the mean).
  Consequently, `dens / p_sig` evaluates to `0.0 / 1e-300 = 0.0`.
  The conditional likelihood contribution per significant study is then clipped to `1e-300`, yielding a constant log-likelihood contribution of $-\log(1e-300) = 690.77$.
  This creates a completely flat likelihood surface (exactly zero gradient) for all $\mu \le -5.0$, preventing the unconstrained Nelder-Mead optimizer (or Brentq profile searches) from finding the true minimum or converging correctly.
  *Verification*: Direct evaluation of `negll` for $\mu$ at `[-5.0, -10.0, -20.0]` shows identical values of `2763.1021115928547` for a 4-study sample.
* **Shipped vs. Internal**: Shipped (part of library).

### Finding 3.2: Underflow / Lack of Log-Scale Stability in `_cond_pp`
* **File:Line**: [src/ubcma/modern_comparators.py:63-66](file:///F:/ubcma/src/ubcma/modern_comparators.py#L63-L66)
* **Severity**: Major
* **Concrete Failure**:
  In `_cond_pp` (called by `p_curve` and the fixed-effect fallback `_puni_fixed`), the conditional p-values of significant studies are computed as:
  ```python
  num = norm.sf(y / se - ncp)
  den = norm.sf(C - ncp)
  den = np.maximum(den, 1e-300)
  return np.clip(num / den, 0.0, 1.0)
  ```
  If $\mu$ is negative (or $se$ is small), `C - ncp = C - mu / se` becomes large.
  For values $\ge 38$, `norm.sf` underflows to `0.0`.
  Although `den` is clipped to `1e-300`, `num` also underflows to `0.0`, resulting in a return value of exactly `0.0`.
  This creates a flat objective function value of `-0.5` for `g(mu) = np.mean(pp) - 0.5`.
  If the root-finding search interval `[mu_lo, mu_hi]` contains a flat region (which it will if `mu_lo = -2.0` and standard errors are small), the Brentq optimizer (`_safe_brentq`) will fail to find a root or cross 0, returning `nan` and setting `converged = False`.
  This can be computed stably on the log scale as:
  ```python
  log_num = norm.logsf(y / se - mu / se)
  log_den = norm.logsf(C - mu / se)
  return np.clip(np.exp(log_num - log_den), 0.0, 1.0)
  ```
* **Shipped vs. Internal**: Shipped (part of library).

### Finding 3.3: Severe Underflow Clipping Bias in `vevea_hedges_step`
* **File:Line**: [src/ubcma/modern_comparators.py:218](file:///F:/ubcma/src/ubcma/modern_comparators.py#L218)
* **Severity**: Major
* **Concrete Failure**:
  In `vevea_hedges_step`, the probability of significance `p_sig` is clipped to `1e-12`:
  ```python
  p_sig = np.clip(norm.cdf(thr), 1e-12, 1.0)
  ```
  Clipping `norm.cdf(thr)` (which corresponds to the probability of a study being significant-positive) to `1e-12` introduces a massive artificial floor.
  If the true probability `p_sig` is below `1e-12` (which occurs when `thr < -7.03`), the likelihood term `log(A)` becomes completely flat in $\mu$ for those studies.
  This disables the selection correction for trials with low likelihood of significance, biasing the estimate toward the naive uncorrected mean and degrading the optimizer's search performance.
  This can be computed stably without clipping using `np.logaddexp`:
  ```python
  log_A = np.logaddexp(norm.logcdf(thr), log_w + norm.logsf(thr))
  ```
  which represents `log(A)` stably.
* **Shipped vs. Internal**: Shipped (part of library).

### Finding 3.4: Non-Identification and Runaway Parameters when All/None Studies are Significant
* **File:Line**: [src/ubcma/modern_comparators.py:193](file:///F:/ubcma/src/ubcma/modern_comparators.py#L193) (for `vevea_hedges_step`), [src/ubcma/modern_comparators.py:104](file:///F:/ubcma/src/ubcma/modern_comparators.py#L104) (for `p_uniform_star`)
* **Severity**: Major
* **Concrete Failure**:
  In `vevea_hedges_step`, there is no check for whether any studies are significant or non-significant before running the joint estimation:
  1. If ALL studies are significant (`k_sig = k`), there are no studies in the non-significant interval. The weight parameter `log_w` for non-significant studies is completely unidentified. The optimizer will drive `log_w -> -inf` (running off to the clip boundary `-30`).
  2. If NONE of the studies are significant (`k_sig = 0`), the weight parameter is again unidentified, and the optimizer will drive `log_w -> +inf` (running off to the clip boundary `20`).
  In either case, the optimizer (Nelder-Mead) will wander along the runaway direction of `log_w`, which is unconstrained, leading to slow convergence, optimization failure, or returning an arbitrary point on the boundary as "converged".
  The function does not guard against `k_sig == 0` or `k_sig == k`, returning a dict with `converged: True` containing a boundary weight (e.g., `weight = e^{-30}` or `weight = 2.27e9`) and an unstable/biased estimate of $\mu$.
  Similarly, `p_uniform_star` does not check for `k_sig == 0`, and will run the RE likelihood estimation on studies where none are significant, which is highly unstable.
* **Shipped vs. Internal**: Shipped (part of library).

### Finding 3.5: Heuristic Profile CI Search Range Failure
* **File:Line**: [src/ubcma/modern_comparators.py:154](file:///F:/ubcma/src/ubcma/modern_comparators.py#L154), [src/ubcma/modern_comparators.py:245](file:///F:/ubcma/src/ubcma/modern_comparators.py#L245)
* **Severity**: Medium
* **Concrete Failure**:
  When the Wald confidence interval fails (e.g. because of flat likelihood/Hessian issues), the functions fall back to a profile likelihood search using `_safe_brentq` over the range `[mu_hat - span, mu_hat + span]`, where:
  - `span = max(1.0, 8.0 * abs(mu_hat) + 1.0)` (in `p_uniform_star`)
  - `span = max(1.0, 10.0 * abs(mu_hat) + 1.0)` (in `vevea_hedges_step`)
  This heuristic span does not scale with the actual standard errors of the studies or the estimator's uncertainty.
  If the study standard errors are large (e.g. $se_i \ge 1.0$), the true confidence interval can easily exceed `span`.
  In such cases, the Brentq root-finder will find that the endpoints have the same sign (since they both fall on one side of the crossing point), returning `nan` and causing the function to report `converged = False` and `ci_low/ci_high = nan`.
  A more robust approach would dynamically expand the search span or base it on a multiple of the estimated standard error from a fixed-effect/naive random-effects model.
* **Shipped vs. Internal**: Shipped (part of library).

### Finding 3.6: Erroneous "Decreasing in mu" Documentation Comment
* **File:Line**: [src/ubcma/modern_comparators.py:85](file:///F:/ubcma/src/ubcma/modern_comparators.py#L85)
* **Severity**: Low
* **Concrete Failure**:
  The comment in `p_curve` for function `g(mu)` states:
  ```python
  def g(mu: float) -> float:  # mean pp - 0.5 ; decreasing in mu
  ```
  However, the conditional probability `pp_i` of a study being at least as extreme as $z_i$ given that it is significant increases as the true effect size $\mu$ increases (since a larger true effect shifts the conditional distribution upward, making any observed positive effect size less extreme relative to the new mean).
  Mathematically, $pp_i(\mu) = sf(z_i - \mu/se_i) / sf(c - \mu/se_i)$ is strictly *increasing* in $\mu$.
  Therefore, the comment is incorrect (it should say `increasing in mu`). While this does not affect the correctness of `_safe_brentq` (which is sign-based and does not assume directionality), it is a documentation defect.
* **Shipped vs. Internal**: Shipped (part of library).

---

## 4. Verification of Specific Inquiries

* **Does `p_curve` guard against no-significant-studies -> NaN?** 
  Yes. In `p_curve` (lines 80-83), the function explicitly checks if $k < 1$ (where $k$ is the number of significant studies) and immediately returns NaN sentinels:
  ```python
  if k < 1:
      return {"mu": float("nan"), "se": float("nan"), "ci_low": float("nan"),
              "ci_high": float("nan"), "converged": False, "k_sig": 0}
  ```
  This is a correct guard that prevents division-by-zero or Brentq exceptions in `p_curve` itself.
* **Identification of cutpoints/weights with small $k$ in `vevea_hedges_step`**:
  No, weights are not identified if $k$ is small and all studies fall on one side of the cutpoint, or if there is insufficient information to distinguish study-level heterogeneity from selection bias. Nelder-Mead will drive the parameter to the bounds ($e^{-30}$ or $e^{20}$) without throwing an error or reporting non-convergence.
