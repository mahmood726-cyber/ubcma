# Independent Third-Vendor Correctness Review: GP Internals & Conformal Calibration

This document contains a deep correctness review of the Gaussian Process (GP) internals and conformal calibration implemented in [field_learned.py](file:///F:/ubcma/borrowing/field_scale/field_learned.py). The review was performed from **first principles** on the `methods-borrowing` branch.

---

## 1. Grouped-ARD Kernel PSD Verification
* **Routine:** `_dist_components` (lines 85-91) & `_kmat` (lines 102-106)
* **Verdict:** **VERIFIED CORRECT** (Mathematically and numerically sound)
* **Mathematical Proof of Positive Semi-Definiteness (PSD):**
  The grouped-ARD covariance kernel is formulated as:
  $$K(x_s, x_t) = \sigma_f^2 \exp\left( -0.5 \left[ \frac{(yr_s - yr_t)^2}{l_{yr}^2} + \frac{(lp_s - lp_t)^2}{l_{lp}^2} + \frac{\mathbb{1}[spec_s \ne spec_t]}{l_{sp}^2} + \frac{\mathbb{1}[ma_s \ne ma_t]}{l_{ma}^2} \right] \right)$$
  We verify that each component is a valid PSD kernel:
  1. The continuous components (year $yr$ and log-precision $lp$) enter via the standard Squared Exponential (RBF) kernel, which is a known PSD kernel.
  2. For the categorical components (specialty $spec$ and meta-analysis $ma$), we define the mismatch kernel:
     $$K_c(c_s, c_t) = \exp\left( - \gamma \mathbb{1}[c_s \ne c_t] \right)$$
     where $\gamma = \frac{0.5}{l_c^2} \ge 0$. This can be rewritten as:
     $$K_c = e^{-\gamma} J + (1 - e^{-\gamma}) I$$
     where $J$ is the all-ones matrix and $I$ is the identity matrix. Since $\gamma \ge 0$, we have $e^{-\gamma} \in (0, 1]$, and thus $1 - e^{-\gamma} \ge 0$. Both $J$ and $I$ are PSD matrices, and since PSD matrices are closed under non-negative linear combinations, $K_c$ is guaranteed to be PSD for any $\gamma \ge 0$.
  3. The final kernel $K$ is the element-wise (Schur) product of these individual components:
     $$K = K_{yr} \odot K_{lp} \odot K_{sp} \odot K_{ma}$$
     By the Schur Product Theorem, the element-wise product of PSD matrices is PSD. Thus, the kernel is guaranteed to be PSD.
* **Implementation Note:** Integer-coding in `build_features` (lines 54-71) uses a "frozen" mapping during k-fold evaluation, preventing code-drift or mismatch between splits.

---

## 2. Rasmussen & Williams Marginal-Likelihood Gradient Verification
* **Routine:** `_obj` (lines 109-134)
* **Verdict:** **VERIFIED CORRECT** (Verified via first-principles derivation and numerical finite differences)
* **Mathematical Derivation:**
  The negative log marginal likelihood (NLML) to minimize is:
  $$\text{NLML}(\theta) = \frac{1}{2} y^T K_y^{-1} y + \frac{1}{2} \log |K_y| + \frac{n}{2} \log (2\pi)$$
  where $K_y = K_f + \text{diag}(\alpha + \text{nugget})$.
  Let $\alpha_{\text{coeff}} = K_y^{-1} y$ (represented as `a` in code).
  Taking the derivative with respect to log-hyperparameters $\theta_j$:
  $$\frac{\partial \text{NLML}}{\partial \theta_j} = - \frac{1}{2} y^T K_y^{-1} \frac{\partial K_y}{\partial \theta_j} K_y^{-1} y + \frac{1}{2} \text{Tr}\left( K_y^{-1} \frac{\partial K_y}{\partial \theta_j} \right)$$
  $$\frac{\partial \text{NLML}}{\partial \theta_j} = - \frac{1}{2} \text{Tr}\left( \alpha_{\text{coeff}} \alpha_{\text{coeff}}^T \frac{\partial K_y}{\partial \theta_j} \right) + \frac{1}{2} \text{Tr}\left( K_y^{-1} \frac{\partial K_y}{\partial \theta_j} \right)$$
  $$\frac{\partial \text{NLML}}{\partial \theta_j} = - \frac{1}{2} \text{Tr}\left( \left( \alpha_{\text{coeff}} \alpha_{\text{coeff}}^T - K_y^{-1} \right) \frac{\partial K_y}{\partial \theta_j} \right)$$
  Let $W = \alpha_{\text{coeff}} \alpha_{\text{coeff}}^T - K_y^{-1}$ (represented as `W` in code).
  Because both $W$ and $\frac{\partial K_y}{\partial \theta_j}$ are symmetric, the trace product is computed as the sum of element-wise products:
  $$\text{Tr}\left( W \frac{\partial K_y}{\partial \theta_j} \right) = \sum_{i,k} W_{ik} \left[\frac{\partial K_y}{\partial \theta_j}\right]_{ik}$$
  This is implemented in Python as:
  ```python
  def tr(dK):
      return -0.5 * float(np.sum(W * dK))
  ```
  This is mathematically correct.
* **Hyperparameter Derivative Terms:**
  Since the parameters are optimized in log-space ($\theta_j = \log \phi_j$), the chain rule gives:
  $$\frac{\partial K_f}{\partial \theta_j} = \frac{\partial K_f}{\partial \phi_j} \frac{\partial \phi_j}{\partial \theta_j} = \phi_j \frac{\partial K_f}{\partial \phi_j}$$
  - **Signal variance ($\sigma_f^2 = e^{\theta_0}$):** $\frac{\partial K_f}{\partial \theta_0} = K_f$ $\rightarrow$ `tr(Kf)` (Correct).
  - **Length scales ($l_d = e^{\theta_d}$ for $d \in \{yr, lp, sp, ma\}$):**
    $$q = \sum_d \frac{D_d}{l_d^2} \implies \frac{\partial K_f}{\partial l_d} = K_f \left( \frac{D_d}{l_d^3} \right) \implies \frac{\partial K_f}{\partial \theta_d} = K_f \left( \frac{D_d}{l_d^2} \right)$$
    This matches the code: `tr(Kf * (D_d / l_d**2))` (Correct).
  - **Nugget ($\text{nugget} = e^{\theta_5}$):**
    $K_y = K_f + \text{diag}(\alpha) + \text{nugget} I \implies \frac{\partial K_y}{\partial \theta_5} = \text{nugget} I$.
    The gradient is:
    $$-0.5 \text{Tr}\left( W \cdot \text{nugget} I \right) = -0.5 \cdot \text{nugget} \cdot \text{Tr}(W)$$
    This matches the code: `-0.5 * nugget * float(np.trace(W))` (Correct).
* **Numerical Validation:**
  An independent finite-difference check of `_obj` gradients against numerical derivatives evaluated on random configurations yielded a maximum absolute difference of $\le 1.06 \times 10^{-9}$, confirming exact analytic matches.

---

## 3. Conflict-Aware Precision Fusion Analysis
* **Routine:** `conflict_aware_fuse` (lines 254-265)
* **Verdict:** **ROBUST baseline (P2 Edge Case Bug Present)**
* **Mathematical Correctness:**
  Under normal-normal conjugacy, prior $N(\mu_p, se_p^2)$ downweighted by power prior $a_0$ has precision $p_{pri} = a_0 / se_p^2$. The data precision is $p_{own} = 1/se_0^2$. The fused mean and standard deviation are:
  $$\mu_{fused} = \frac{p_{own} y_0 + p_{pri} \mu_p}{p_{own} + p_{pri}}, \quad se_{fused} = \sqrt{\frac{1}{p_{own} + p_{pri}}}$$
  This is mathematically correct.
* **Finding 1 (P2 Edge Case Bug):**
  - **File & Line:** `borrowing\field_scale\field_learned.py:262`
  - **Concrete Failure:** The function does not validate the target study's own standard error `se0`. If `se0 == 0`, evaluating `p_own = 1.0 / se0 ** 2` results in a `ZeroDivisionError` crash. If `se0 < 0`, it is silently squared and treated as positive precision, which is physically nonsensical.
  - **Shipped-vs-Internal (Headline Impact):** **NO IMPACT**. All real studies in the metadat corpus have strictly positive standard errors ($se_0 > 0$). Furthermore, `conflict_aware_fuse` is not used in the primary GP execution path (`predict_kfold_corpus` or `predict_loo_corpus`); it is only called in option-level benchmarks. Thus, this does not move the headline MAE 0.3325 / conformal 0.899 numbers.

---

## 4. Conformal Quantile Calibration & Finite-Sample Correction
* **Routine:** `conformal_intervals` (lines 271-294)
* **Verdict:** **CONFINED UNDERCOVERAGE BUG (P1 Bug Confirmed)**
* **Finding 2 (P1 Mathematical Bug):**
  - **File & Line:** `borrowing\field_scale\field_learned.py:289`
  - **Concrete Failure:** The code uses standard numpy quantile interpolation to compute the conformal threshold:
    ```python
    q = np.quantile(others, 1 - alpha, method="higher")
    ```
    For a calibration set of size $M$ (where $M = n - 1$ other studies in the same family block), standard conformal prediction theory requires taking the $k$-th sorted residual, where:
    $$k = \lceil (M+1)(1-\alpha) \rceil$$
    0-indexed, this corresponds to index:
    $$idx_{correct} = \lceil (M+1)(1-\alpha) \rceil - 1$$
    However, `np.quantile(..., method="higher")` computes the virtual index using the interpolation formula $i = p(M-1)$, which rounds up to:
    $$idx_{np} = \lceil (M-1)(1-\alpha) \rceil$$
    This causes an off-by-one undercoverage bug. For example, with $M = 11$ calibration residuals and $\alpha = 0.10$:
    - The correct index is $\lceil 12 \times 0.90 \rceil - 1 = 11 - 1 = 10$ (the maximum residual value).
    - Numpy's `method="higher"` picks $\lceil 10 \times 0.90 \rceil = 9$ (the second-largest residual value).
    - For small $M$ (e.g., $M < 1/\alpha - 1$), the conformal interval should be infinite ($k > M$). Numpy's implementation instead produces a finite interval, undercovering the target.
  - **Shipped-vs-Internal (Headline Impact):** **MOVES THE CONFORMAL HEADLINE**.
    An independent evaluation on the 1177-node corpus (1-seed, 10-fold CV predictions) shows the following difference:
    - **Original:** Coverage = **0.898895** ($\approx 0.899$ headline), Average Width = **1.541944**
    - **Corrected:** Coverage = **0.900595** ($\approx 0.901$), Average Width = **1.556394**
    - **Delta:** Coverage = **+0.17%** (achieving the nominal $\ge 90\%$ guarantee), Width = **+0.9%** (+0.0144).
  - **Exchangeability / Methodological Note:**
    Because `pred` is computed from k-fold cross-validation predictions, the residuals are not strictly exchangeable due to overlapping training sets. While Barber et al. (2021) CV+/Jackknife+ bounds handle this overlap, they require evaluating *all* fold models at the test point. The implemented symmetric formulation is a simplified cross-conformal heuristic, but with the correct index calculation, it achieves the nominal 90% coverage rate in practice ($90.06\%$).
