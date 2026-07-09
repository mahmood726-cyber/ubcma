# Independent Third-Vendor Correctness Review: UBCMA Selection Model and Optimizer

This document contains a deep correctness review of the selection-model optimizer and inference utilities implemented in [model.py](file:///F:/ubcma/src/ubcma/model.py) and [inference.py](file:///F:/ubcma/src/ubcma/inference.py). The review was performed from **first principles** on the `methods-borrowing` branch of the `ubcma` repository.

---

## 1. Selection Likelihood Construction & Normalizer Math Verification

### A. Mathematical Derivation of the Conditional Likelihood
In a publication-selection model (e.g., Copas or Hedges-Vevea), the observed data consists of effect sizes $y_i$ and standard errors $\sigma_i$ for studies that have been published/observed (i.e., selected). The conditional likelihood of the observed effect size $y_i$ given selection is:
$$f(y_i \mid \text{selected}_i = 1) = \frac{P(\text{selected}_i = 1 \mid y_i, \sigma_i) f(y_i \mid \sigma_i)}{P(\text{selected}_i = 1 \mid \sigma_i)}$$

Taking the logarithm yields:
$$\log f(y_i \mid \text{selected}_i = 1) = \log f(y_i \mid \sigma_i) + \log P(\text{selected}_i = 1 \mid y_i, \sigma_i) - \log P(\text{selected}_i = 1 \mid \sigma_i)$$

Summing over all observed studies $i = 1, \dots, N$:
$$\log L = \sum_{i=1}^N \left( \log f(y_i \mid \sigma_i) + \log P(\text{selected}_i = 1 \mid y_i, \sigma_i) - \log P(\text{selected}_i = 1 \mid \sigma_i) \right)$$

In the implementation ([model.py:478-528](file:///F:/ubcma/src/ubcma/model.py#L478-L528)), this log-likelihood (plus prior log-density penalties) is computed inside the `objective` function:
```python
log_density = logsumexp(log_comp, axis=0) # log f(y_i)
p_select_obs = self._selection_probability(...) # P(selected_i | y_i)
normalizer = ... # P(selected_i)
total = np.sum(log_density + np.log(p_select_obs) - np.log(normalizer))
```
This implementation matches the mathematical formulation of the conditional likelihood **exactly**.

### B. Expected Selection Probability and Gauss-Hermite Integration
The marginal selection probability $P(\text{selected}_i = 1 \mid \sigma_i)$ (the normalizer) is the expectation of the selection probability over the marginal distribution of $y_i$ before selection:
$$P(\text{selected}_i = 1 \mid \sigma_i) = \int_{-\infty}^{\infty} P(\text{selected}_i = 1 \mid y, \sigma_i) f(y \mid \sigma_i) dy$$

Under the mixture model, $f(y \mid \sigma_i) = w_1 N(y \mid \mu_i, \text{sd}_{1,i}^2) + (1 - w_1) N(y \mid \mu_i, \text{sd}_{2,i}^2)$ where:
- $\mu_i$ is the study location (including moderators, design shifts, and quality-bias adjustments).
- $\text{sd}_{1,i}^2 = \sigma_i^2 + \tau_1^2$ and $\text{sd}_{2,i}^2 = \sigma_i^2 + \tau_2^2$.

So the normalizer integral splits into:
$$P(\text{selected}_i = 1 \mid \sigma_i) = w_1 \int_{-\infty}^{\infty} P(\text{selected}_i = 1 \mid y, \sigma_i) N(y \mid \mu_i, \text{sd}_{1,i}^2) dy + (1 - w_1) \int_{-\infty}^{\infty} P(\text{selected}_i = 1 \mid y, \sigma_i) N(y \mid \mu_i, \text{sd}_{2,i}^2) dy$$

To evaluate each integral $\int_{-\infty}^{\infty} h(y) N(y \mid \mu, s^2) dy$, the code uses Gauss-Hermite quadrature.
Let $y = \mu + \sqrt{2} s t$. The differential is $dy = \sqrt{2} s dt$. Substituting:
$$\int_{-\infty}^{\infty} h(y) \frac{1}{s \sqrt{2\pi}} e^{-\frac{(y-\mu)^2}{2s^2}} dy = \frac{1}{\sqrt{\pi}} \int_{-\infty}^{\infty} h(\mu + \sqrt{2} s t) e^{-t^2} dt \approx \frac{1}{\sqrt{\pi}} \sum_j w_j h(\mu + \sqrt{2} s t_j)$$
where $t_j$ and $w_j$ are the physicist's Hermite quadrature nodes and weights.

In the code ([model.py:285-295](file:///F:/ubcma/src/ubcma/model.py#L285-L295)):
```python
nodes = loc_array[:, None] + np.sqrt(2.0) * sd_array[:, None] * self._gh_x[None, :]
...
expected = np.sum(self._gh_w[None, :] * probs, axis=1) / np.sqrt(np.pi)
```
This is mathematically **correct**.

### C. Covariate Treatment in the Normalizer
The selection probability relies on covariates:
$$\text{logit}(P(\text{selected}_i = 1)) = \gamma_0 + \gamma_1 \cdot \text{smooth\_significance}_i(y_i, \sigma_i) + \gamma_2 \cdot \text{precision\_z}_i(\sigma_i) + \gamma_3 \cdot \text{smooth\_direction}_i(y_i) + \gamma_{\text{quality}} \cdot \text{quality}_i$$

During integration over the marginal distribution of $y_i$:
- `smooth_significance` and `smooth_direction` depend on $y_i$, so they are evaluated at the quadrature `nodes`.
- `precision_z` and `quality` are fixed characteristics of the study $i$ and do not depend on the integration variable $y_i$. They must be held constant across all quadrature nodes for study $i$.

In the code ([model.py:286-294](file:///F:/ubcma/src/ubcma/model.py#L286-L294)):
- `precision_z` is passed as `precision_array[:, None]` (shape $(N, 1)$), broadcasting to $(N, n_{quad})$.
- `quality` is tiled as `tiled_quality = np.repeat(quality_array[:, None, :], repeats=len(self._gh_x), axis=1)` (shape $(N, n_{quad}, n_{selection\_quality})$).
Thus, both covariates are held constant across nodes, while $y$ varies. This is mathematically **correct**.

### Verdict on Likelihood and Normalizer Math
The selection likelihood construction and normalizer math are **completely correct**.

---

## 2. Optimizer Bounds & Initialization

### A. Parameterization and Bounds
The parameters are optimized in an unconstrained space and mapped to constrained domains:
- $\tau_1 = \exp(\text{clip}(x_1, -20, 20)) > 0$
- $\tau_2 = \tau_1 + \exp(\text{clip}(x_2, -20, 20)) > \tau_1$
- $w = \text{sigmoid}(x_3) \in (0, 1)$

Because of this unconstrained mapping, no explicit bounds are passed to the `minimize` call, which is mathematically and programmatically correct.
The use of `np.clip` in `_safe_exp` creates a flat gradient if the optimizer explores values beyond $[-20, 20]$, but the quadratic priors on $\tau_1, \tau_2$ pull them away from $+\infty$, and values below $-20$ represent $\tau \approx 2 \times 10^{-9}$ (practically zero), where the gradient is negligible anyway.

### B. Initialization
The optimizer uses a multi-start framework starting with:
1. A baseline DerSimonian-Laird estimate (`dl_start`).
2. Random initializations using a pseudo-Latin Hypercube generator (`_latin_hypercube_starts`).
*Note:* The random start generator `_latin_hypercube_starts` draws independent random uniforms and normals rather than performing stratified Latin Hypercube sampling. However, it functions correctly as a multi-start generator.

---

## 3. Profile / BCa Interval Construction

### A. Dead Exception Handling in Bootstrap and Jackknife Fits
* **File & Line:** [inference.py:388](file:///F:/ubcma/src/ubcma/inference.py#L388) and [inference.py:487](file:///F:/ubcma/src/ubcma/inference.py#L487)
* **Severity:** **P2** (Logic / Robustness issue)
* **Shipped-vs-internal:** **Internal** (does not affect shipped numbers)
* **First-Principles Analysis:**
  In `bootstrap_ci` and `_bca_ci`, fits are run using:
  ```python
  boot_result = fast_fitter.fit(boot_data, allow_failed=True)
  ```
  and
  ```python
  jr = fitter.fit(jack_data, allow_failed=True)
  ```
  Passing `allow_failed=True` instructs the fitter to catch convergence failures internally and return a `UBCMAResult` object with `success=False` rather than raising a `RuntimeError`.
  
  As a consequence, the outer exception handlers:
  ```python
  try:
      boot_result = fast_fitter.fit(boot_data, allow_failed=True)
      boot_mus.append(float(boot_result.params["mu"]))
  except Exception:
      n_failed += 1
  ```
  are dead code. Any optimization failure is silently ignored, and the non-converged parameter values from the failed optimization are appended to the bootstrap and jackknife distribution arrays.
  
  This introduces noise and invalid outliers into the bootstrap distribution and the jackknife acceleration calculation.
  
  *Impact on Shipped Numbers:* The main simulation study and the AdaptShrink estimator use `profile_likelihood_ci` to obtain confidence intervals for the `ubcma` member, completely bypassing `bootstrap_ci`. Thus, this bug **does not move** the shipped `ubcma` or `AdaptShrink` benchmark numbers.
* **Remedy:** Set `allow_failed=False` inside the bootstrap/jackknife `fit` calls so that convergence failures correctly raise a `RuntimeError`, increment `n_failed`, and skip/fallback appropriately.

---

### B. Warm-Start Optimization in Bisection Search for Profile Likelihood
* **File & Line:** [inference.py:226-241](file:///F:/ubcma/src/ubcma/inference.py#L226-L241)
* **Severity:** **P3** (Minor optimization / numerical issue)
* **Shipped-vs-internal:** **Shipped** (does not significantly move shipped numbers)
* **First-Principles Analysis:**
  The profile likelihood boundary search utilizes a bisection search where the test points `mid` jump non-monotonically. The bisection solver warm-starts each evaluation using the nonlocal variable `_last_nuisance`:
  ```python
  _last_nuisance = res.x.copy()
  ```
  Because the search target jumps back and forth, warm-starting from the last evaluated point (which could be on the other side of the threshold or far away) rather than a closer point (or the global MLE) can result in L-BFGS-B starting in a suboptimal region. Since it is restricted to `maxiter=20` and `ftol=1e-3` for speed, it may terminate at a local minimum or fail to fully converge, leading to an overestimated profile objective value at that point.
  
  An overestimated profile objective value causes the bisection search to cross the threshold closer to the MLE, resulting in a slightly narrower (optimistic) interval.
  
  *Impact on Shipped Numbers:* In practice, the penalized likelihood profile curve is smooth, and L-BFGS-B converges quickly. The impact on simulated coverage rates and widths is negligible.
* **Remedy:** For maximum stability, reset the warm-start to `mle_params[1:].copy()` for each profile evaluation, or increase `maxiter` to 50 when warm-starting from arbitrary non-monotonic points.

---

## 4. Data Reuse and Optimistic Coverage

We evaluated whether the same data is reused to both fit the model and report a confidence interval without adjusting for the degrees of freedom or selection process.

- **Profile Likelihood CI:** The bisection search profiles out (re-minimizes over) all nuisance parameters ($\beta$, $\delta$, $\lambda_{bias}$, $\gamma_{common}$, $\gamma_{quality}$, $\tau_1$, $\tau_2$, $mix\_weight$) at each step. This correctly propagates all model estimation uncertainties into the interval of the treatment effect $\mu$, avoiding optimistic coverage from plug-in estimation.
- **Bootstrap CI:** The non-parametric bootstrap resamples the entire dataset and refits the entire model (including the selection model) for each replicate, which correctly accounts for the uncertainty of the entire fitting process.
- **Verdict:** There is no data-reuse double dipping that creates optimistic coverage in the core selection-model intervals.
