# Bivariate DTA HSROC and Exact-Binomial GLMM Deep Analysis Report: First-Principles Review and Branch Verification

This report provides an independent third-vendor deep analysis of the Hierarchical Summary Receiver Operating Characteristic (HSROC) and bivariate generalized linear mixed model (GLMM) exact-binomial framework within the Unified Bias-Calibrated Meta-Analysis (UBCMA) system. 

We determine the presence of these models on the current branch (`methods-borrowing`), derive their mathematical foundations from first principles, and review the code that is implemented on this branch.

---

## Executive Summary

- **Verdict:** **NOT PRESENT ON THIS BRANCH (Truthful Caveat)**
  - The HSROC and bivariate exact-binomial GLMM (with adaptive Gauss-Hermite quadrature) are **not implemented** in [dta.py](file:///F:/ubcma/src/ubcma/dta.py) or elsewhere in the `src/` directory on the `methods-borrowing` branch.
  - The compiled test cache artifacts (e.g., `tests/__pycache__/test_dta.cpython-313-pytest-9.0.3.pyc`) and historical verification records confirm that the HSROC exact-binomial GLMM lives on the **`methods-dta`** branch/worktree, which is separate.
- **Implemented Code Review:** The DTA code that *is* present on this branch in [dta.py](file:///F:/ubcma/src/ubcma/dta.py) implements the bivariate normal-normal random-effects model (the Reitsma / van Houwelingen model) on logit-transformed Sensitivity and Specificity, along with a novel shrinkage estimator ([adaptshrink_dta](file:///F:/ubcma/src/ubcma/dta.py#L445-L496)) and a Deeks-asymmetry-gated small-study selection correction ([deeks_asymmetry](file:///F:/ubcma/src/ubcma/dta.py#L405-L442)).
- **Review Summary:** 
  - The Reitsma and covariance-shrunk estimators in [dta.py](file:///F:/ubcma/src/ubcma/dta.py) are **mathematically and numerically sound**.
  - All logit transformations, matrix inversions, GLS pooling equations, and Deeks' test WLS statistics match their first-principles specifications exactly.
  - The profile log-likelihood concentration method implemented in [_neg_loglik](file:///F:/ubcma/src/ubcma/dta.py#L185-L200) and [_accumulate](file:///F:/ubcma/src/ubcma/dta.py#L152-L182) is highly efficient and numerically stable.

---

## 1. First-Principles Derivation of the DTA Bivariate Exact-Binomial GLMM

For a diagnostic test accuracy (DTA) meta-analysis, let each study $i$ (for $i = 1, \dots, k$) contribute a $2 \times 2$ table of cell counts:
- Diseased group: $n_{i1}$ total patients, of whom $y_{i1}$ are True Positives (TP).
- Non-diseased group: $n_{i2}$ total patients, of whom $y_{i2}$ are True Negatives (TN).

Because the diseased and non-diseased patient groups are independent, the counts of True Positives and True Negatives are conditionally independent binomially distributed variables given the study-level sensitivity $Se_i$ and specificity $Sp_i$:
$$ y_{i1} \mid Se_i \sim \operatorname{Binomial}(n_{i1}, Se_i) $$
$$ y_{i2} \mid Sp_i \sim \operatorname{Binomial}(n_{i2}, Sp_i) $$

### The Random-Effects Link
To model the between-study heterogeneity and the correlation between sensitivity and specificity, we apply a bivariate normal distribution to the logit-transformed probabilities:
$$ \eta_{i1} = \operatorname{logit}(Se_i) = \ln\left(\frac{Se_i}{1 - Se_i}\right) = \mu_1 + u_{i1} $$
$$ \eta_{i2} = \operatorname{logit}(Sp_i) = \ln\left(\frac{Sp_i}{1 - Sp_i}\right) = \mu_2 + u_{i2} $$

where:
- $\mu = (\mu_1, \mu_2)^T$ is the vector of summary mean sensitivity and specificity on the logit scale.
- $u_i = (u_{i1}, u_{i2})^T$ represents the study-specific random effects, assumed to follow a bivariate normal distribution:
$$ u_i \sim N(0, \Sigma), \quad \Sigma = \begin{pmatrix} \tau_1^2 & \rho \tau_1 \tau_2 \\ \rho \tau_1 \tau_2 & \tau_2^2 \end{pmatrix} $$
where $\tau_1^2$ and $\tau_2^2$ are the between-study variances of logit sensitivity and logit specificity, and $\rho$ is their correlation.

### Bivariate Likelihood Formulation
The conditional likelihood of observing $(y_{i1}, y_{i2})$ given the random effects $u_i$ is:
$$ P(y_{i1}, y_{i2} \mid u_i) = \binom{n_{i1}}{y_{i1}} \left(\frac{e^{\mu_1+u_{i1}}}{1 + e^{\mu_1+u_{i1}}}\right)^{y_{i1}} \left(\frac{1}{1 + e^{\mu_1+u_{i1}}}\right)^{n_{i1}-y_{i1}} \binom{n_{i2}}{y_{i2}} \left(\frac{e^{\mu_2+u_{i2}}}{1 + e^{\mu_2+u_{i2}}}\right)^{y_{i2}} \left(\frac{1}{1 + e^{\mu_2+u_{i2}}}\right)^{n_{i2}-y_{i2}} $$

Expressing this compactly in log-space:
$$ P(y_{i1}, y_{i2} \mid u_i) = \binom{n_{i1}}{y_{i1}}\binom{n_{i2}}{y_{i2}} \exp\left( \sum_{j=1}^2 \left[ y_{ij} (\mu_j + u_{ij}) - n_{ij} \ln\left(1 + e^{\mu_j + u_{ij}}\right) \right] \right) $$

To obtain the marginal likelihood $L_i(\theta)$ for the parameters $\theta = (\mu_1, \mu_2, \tau_1, \tau_2, \rho)^T$, we integrate out the random effects $u_i$ over their bivariate normal prior $f(u_i \mid \Sigma)$:
$$ L_i(\theta) = \int_{\mathbb{R}^2} P(y_{i1}, y_{i2} \mid u_i) f(u_i \mid \Sigma) du_i $$
$$ f(u_i \mid \Sigma) = \frac{1}{2\pi \sqrt{\operatorname{det}\Sigma}} \exp\left( -\frac{1}{2} u_i^T \Sigma^{-1} u_i \right) $$

The joint log-likelihood for the entire meta-analysis is the sum of the log marginal integrals across all studies:
$$ \ln L(\theta) = \sum_{i=1}^k \ln \int_{\mathbb{R}^2} P(y_{i1}, y_{i2} \mid u_i) f(u_i \mid \Sigma) du_i $$

---

## 2. Adaptive Gauss-Hermite Quadrature (AGQ)

Standard Gauss-Hermite quadrature approximates integrals by evaluating the integrand at fixed nodes scaled by a prior variance. However, if the conditional binomial likelihood $P(y_{i1}, y_{i2} \mid u_i)$ is highly peaked (e.g., in studies with large sample sizes $n_{ij}$), the integrand concentrates in a narrow region that may lie entirely between the fixed nodes, causing severe numerical instability and approximation errors (the "node-slippage" problem).

Adaptive Gauss-Hermite Quadrature (Liu & Pierce, 1994) solves this by shifting and scaling the quadrature nodes for each study to center them at the posterior mode of the random effects and scale them by the local curvature.

### Step 1: Finding the Mode (Node Adaptation)
For study $i$, let the log-integrand (excluding the binomially constant coefficients) be:
$$ h_i(u) = \sum_{j=1}^2 \left[ y_{ij} (\mu_j + u_j) - n_{ij} \ln\left(1 + e^{\mu_j + u_j}\right) \right] - \frac{1}{2} u^T \Sigma^{-1} u $$

We locate the mode $\hat{u}_i = \operatorname{argmax}_{u} h_i(u)$ by solving the gradient equation $\nabla h_i(u) = 0$. The gradient is:
$$ \nabla h_i(u) = \begin{pmatrix} y_{i1} - n_{i1} p_{i1}(u) \\ y_{i2} - n_{i2} p_{i2}(u) \end{pmatrix} - \Sigma^{-1} u = 0 $$
where $p_{ij}(u) = \frac{1}{1 + e^{-(\mu_j + u_j)}}$ is the probability.

We evaluate the Hessian matrix $H_i(u) = -\nabla^2 h_i(u)$, which represents the negative curvature:
$$ H_i(u) = \operatorname{diag}\left( n_{i1} p_{i1}(u)(1 - p_{i1}(u)), \; n_{i2} p_{i2}(u)(1 - p_{i2}(u)) \right) + \Sigma^{-1} $$
Since $0 < p_{ij} < 1$ and $\Sigma^{-1}$ is positive-definite, $H_i(u)$ is strictly positive-definite, making $h_i(u)$ strictly concave with a unique global maximum. $\hat{u}_i$ is obtained numerically via Newton-Raphson iterations.

### Step 2: Scaling and Rotational Transformation
We evaluate the Hessian at the mode: $\hat{H}_i = H_i(\hat{u}_i)$. The inverse Hessian $\hat{V}_i = \hat{H}_i^{-1}$ serves as the covariance of the Laplace approximation.
We perform a Cholesky decomposition of the local covariance:
$$ \hat{V}_i = C_i C_i^T $$

We transform the multidimensional integration variable from $u$ to $z$ via:
$$ u = \hat{u}_i + \sqrt{2} C_i z $$
The Jacobian of this transformation is $\operatorname{det}\left(\sqrt{2} C_i\right) = 2^{D/2} \sqrt{\operatorname{det}\hat{V}_i} = 2 \sqrt{\operatorname{det}\hat{V}_i}$ (for $D=2$).

### Step 3: Quadrature Summation
Using $Q$ standard quadrature nodes $z_q$ and weights $w_q$ derived from the Hermite polynomials (roots of the physicist's Hermite polynomial $H_Q(z)$), the bivariate integral is approximated by:
$$ L_i(\theta) \approx 2 \sqrt{\operatorname{det}\hat{V}_i} \sum_{q_1=1}^Q \sum_{q_2=1}^Q w_{q_1} w_{q_2} \exp\left( z_{q_1}^2 + z_{q_2}^2 \right) \exp\left( h_i\left(\hat{u}_i + \sqrt{2} C_i z_q\right) \right) $$
where $z_q = (z_{q_1}, z_{q_2})^T$.

### Step 4: Log-Scale Stability
To prevent numerical underflow or overflow, evaluations are computed in log-space. Let:
$$ T_q = \ln(w_{q_1}) + \ln(w_{q_2}) + \|z_q\|^2 + h_i\left(\hat{u}_i + \sqrt{2} C_i z_q\right) $$
We pull out the maximum term $T_{\max} = \max_{q} T_q$ to stabilize the sum:
$$ \ln L_i(\theta) \approx \ln(2) + \frac{1}{2}\ln \operatorname{det}\hat{V}_i + T_{\max} + \ln\left( \sum_{q_1=1}^Q \sum_{q_2=1}^Q \exp\left( T_q - T_{\max} \right) \right) $$

---

## 3. The HSROC Parameterization (Rutter-Gatsonis 2001)

The Hierarchical SROC (HSROC) model parameterizes the sensitivity and specificity of studies in terms of three components:
1. **Accuracy ($\Lambda_i$):** The overall diagnostic power of study $i$.
2. **Threshold ($\theta_i$):** The diagnostic cutoff used by study $i$.
3. **Shape ($\beta$):** The asymmetry of the SROC curve.

Letting $Y_{i1} = \operatorname{logit}(Se_i)$ and $Y_{i2}^* = \operatorname{logit}(FPR_i) = \operatorname{logit}(1 - Sp_i) = -\operatorname{logit}(Sp_i)$, the Rutter-Gatsonis model defines:
$$ Y_{i1} = e^{-\beta/2} \left( \theta_i + \frac{1}{2} \Lambda_i \right) $$
$$ Y_{i2}^* = e^{\beta/2} \left( \theta_i - \frac{1}{2} \Lambda_i \right) $$
where:
- $\Lambda_i \sim N(\Lambda, \sigma_\Lambda^2)$ is the random effect for study accuracy.
- $\theta_i \sim N(\Theta, \sigma_\theta^2)$ is the random effect for study threshold.
- $\Lambda_i$ and $\theta_i$ are assumed to be independent.

### Mathematical Equivalence to the Bivariate Random-Effects Model
Harbord et al. (2007) showed that the HSROC model without study-level covariates is mathematically equivalent to the bivariate normal-normal model of logit sensitivity and logit specificity. The mapping is derived by equating the marginal means and covariance matrices.

#### Between-Study Variances and Correlation
Using the independence of $\theta_i$ and $\Lambda_i$, the marginal variances of $Y_{i1}$ and $Y_{i2}^*$ are:
$$ \tau_{Se}^2 = \operatorname{Var}(Y_{i1}) = e^{-\beta} \left( \sigma_\theta^2 + \frac{1}{4}\sigma_\Lambda^2 \right) $$
$$ \tau_{FPR}^2 = \operatorname{Var}(Y_{i2}^*) = e^{\beta} \left( \sigma_\theta^2 + \frac{1}{4}\sigma_\Lambda^2 \right) $$
The between-study covariance is:
$$ \operatorname{Cov}(Y_{i1}, Y_{i2}^*) = \sigma_\theta^2 - \frac{1}{4}\sigma_\Lambda^2 $$

Taking the ratio of the variances:
$$ \frac{\tau_{FPR}^2}{\tau_{Se}^2} = e^{2\beta} \implies \beta = \ln\left( \frac{\tau_{FPR}}{\tau_{Se}} \right) = \ln\left( \frac{\tau_{Sp}}{\tau_{Se}} \right) $$

Solving the system for the HSROC variances:
$$ \sigma_\theta^2 = \frac{1}{2} \tau_{Se} \tau_{Sp} (1 - \rho) $$
$$ \sigma_\Lambda^2 = 2 \tau_{Se} \tau_{Sp} (1 + \rho) $$
where $\rho = \operatorname{Cov}(Y_{i1}, Y_{i2}) / (\tau_{Se} \tau_{Sp}) = -\operatorname{Cov}(Y_{i1}, Y_{i2}^*) / (\tau_{Se} \tau_{Sp})$.

#### Marginal Means
Let the bivariate model means be $M_1 = E[Y_{i1}]$ and $M_2 = E[-Y_{i2}^*]$ (i.e. $E[Y_{i2}^*] = -M_2$).
$$ M_1 = e^{-\beta/2} \left( \Theta + \frac{1}{2}\Lambda \right) \implies M_1 e^{\beta/2} = \Theta + \frac{1}{2}\Lambda $$
$$ -M_2 = e^{\beta/2} \left( \Theta - \frac{1}{2}\Lambda \right) \implies -M_2 e^{-\beta/2} = \Theta - \frac{1}{2}\Lambda $$

Solving for $\Lambda$ and $\Theta$:
$$ \Lambda = M_1 e^{\beta/2} + M_2 e^{-\beta/2} $$
$$ \Theta = \frac{1}{2} \left( M_1 e^{\beta/2} - M_2 e^{-\beta/2} \right) $$

For the symmetric case ($\beta = 0$, implying $\tau_{Se} = \tau_{Sp}$):
- $\Lambda = M_1 + M_2 = \operatorname{logit}(Se) + \operatorname{logit}(Sp) = \ln(\operatorname{DOR})$
- $\Theta = \frac{1}{2} (M_1 - M_2)$

---

## 4. Back-Transformation to Se/Sp/SROC

### Back-Transforming the Summary Point
To obtain the summary operating point on the probability scale, the logit coordinates $M_1$ and $M_2$ are transformed using the logistic sigmoid function:
$$ Se_{\text{summary}} = \frac{1}{1 + e^{-M_1}} $$
$$ Sp_{\text{summary}} = \frac{1}{1 + e^{-M_2}} $$

### SROC Curve Formulation
The summary receiver operating characteristic (SROC) curve defines the expected relationship between Sensitivity and Specificity. In the HSROC framework, we eliminate the study-level threshold $\theta_i$ to find the curve.
Setting the accuracy parameter to its mean $\Lambda_i = \Lambda$, we have:
$$ Y_{i1} e^{\beta/2} - Y_{i2}^* e^{-\beta/2} = \Lambda $$
Substituting $Y_{i1} = \operatorname{logit}(Se)$ and $Y_{i2}^* = -\operatorname{logit}(Sp)$:
$$ \operatorname{logit}(Se) e^{\beta/2} + \operatorname{logit}(Sp) e^{-\beta/2} = \Lambda $$
$$ \operatorname{logit}(Se) = e^{-\beta/2} \Lambda - e^{-\beta} \operatorname{logit}(Sp) $$

Expressing sensitivity as a function of the false positive rate ($FPR = 1 - Sp$):
$$ Se(FPR) = \frac{1}{1 + \exp\left( - \left( e^{-\beta/2} \Lambda + e^{-\beta} \operatorname{logit}(FPR) \right) \right)} $$

---

## 5. Code Review of the Current DTA Implementation

The DTA meta-analysis code is located in [dta.py](file:///F:/ubcma/src/ubcma/dta.py). Below we audit the mathematical implementation of the Reitsma model, the shrinkage estimation, and Deeks' correction.

### Bivariate Normal-Normal Likelihood concentration
In [_accumulate](file:///F:/ubcma/src/ubcma/dta.py#L152-L182), the precision matrix $W_i = V_i^{-1}$ for each study is calculated:
```python
    s11, s12, s22 = Sigma[0, 0], Sigma[0, 1], Sigma[1, 1]
    a = s11 + S[:, 0, 0]              # tau1^2 + s1_i^2
    c = s22 + S[:, 1, 1]              # tau2^2 + s2_i^2
    b = s12                           # rho * tau1 * tau2
    det = a * c - b * b
    inv = 1.0 / det
    w11 = c * inv
    w22 = a * inv
    w12 = -b * inv
```
This matches the analytic inverse of a symmetric $2 \times 2$ matrix $V_i = \begin{pmatrix} a_i & b \\ b & c_i \end{pmatrix}$:
$$ V_i^{-1} = \frac{1}{a_i c_i - b^2} \begin{pmatrix} c_i & -b \\ -b & a_i \end{pmatrix} $$
which is exact.

In [_neg_loglik](file:///F:/ubcma/src/ubcma/dta.py#L185-L200), the profile MLE of $M$ given $\Sigma$ is computed:
```python
    M = np.array([A[1, 1] * rhs[0] - A[0, 1] * rhs[1],
                  -A[0, 1] * rhs[0] + A[0, 0] * rhs[1]]) / detA
    quad = quad_sum - rhs @ M
    return 0.5 * (logdet_sum + quad)
```
This represents $M = A^{-1} \operatorname{rhs}$ and the profile negative log-likelihood (omitting the $k \ln(2\pi)$ constant):
$$ -\ln L_{\text{profile}}(\Sigma) = \frac{1}{2} \sum_{i=1}^k \ln \operatorname{det}(V_i) + \frac{1}{2} \left[ \sum_{i=1}^k y_i^T V_i^{-1} y_i - M^T \left( \sum_{i=1}^k V_i^{-1} \right) M \right] $$
This is mathematically exact and highly efficient, as it reduces the dimensionality of the numerical optimization from 5 parameters to 3.

### Optimization Convergence
In [_fit_sigma](file:///F:/ubcma/src/ubcma/dta.py#L213-L241), a multi-start optimization is implemented using 3 starting values:
```python
    starts = [
        np.array([0.5 * np.log(v1), 0.5 * np.log(v2), 0.0]),
        np.array([np.log(0.3), np.log(0.3), 0.0]),
        np.array([np.log(0.6), np.log(0.6), np.arctanh(-0.4)]),
    ]
```
The parameters optimized are $(\ln \tau_1, \ln \tau_2, \operatorname{arctanh}(\rho))$, which are entirely unconstrained. This prevents optimization failures due to hard boundaries and ensures convergence.

### Correlation Shrinkage
In [_shrinkage_delta](file:///F:/ubcma/src/ubcma/dta.py#L376-L388), the shrinkage factor $\delta$ is:
```python
    delta_k = AS_KAPPA0 / (AS_KAPPA0 + max(k - 3, 1))
    boundary = (abs(rho) >= AS_RHO_BOUNDARY) or (cond >= AS_COND_MAX)
    delta = delta_k + (AS_BOUNDARY_BOOST if boundary else 0.0)
    delta = float(np.clip(delta, 0.0, AS_DELTA_MAX))
```
This is a robust heuristic that shrinks correlation towards 0 when $k$ is small or when the covariance matrix is ill-conditioned (condition number $\ge 1000$ or $|\hat{\rho}| \ge 0.95$). In [_shrink_sigma](file:///F:/ubcma/src/ubcma/dta.py#L391-L402), it preserves the marginal variances $\tau_1^2$ and $\tau_2^2$, applying the shrinkage only to the correlation coefficient:
$$ R_{\text{AS}} = (1 - \delta) R_{\text{MLE}} + \delta I $$
This is mathematically sound and guarantees that $\Sigma_{\text{AS}}$ is positive-definite and well-conditioned.

### Deeks' Asymmetry and Selection Correction
In [deeks_asymmetry](file:///F:/ubcma/src/ubcma/dta.py#L405-L442), the WLS regression statistics are:
```python
    # weighted least squares of lndor ~ a + slope*x, weights = ess
    w = ess
    X = np.column_stack([np.ones(k), x])
    WX = X * w[:, None]
    XtWX = X.T @ WX
    XtWy = WX.T @ lndor
    beta = np.linalg.solve(XtWX, XtWy)
    resid = lndor - X @ beta
    dof = k - 2
    sigma2 = float(np.sum(w * resid ** 2) / dof)
    cov_beta = sigma2 * np.linalg.inv(XtWX)
```
This is mathematically 100% correct.

In [adaptshrink_dta](file:///F:/ubcma/src/ubcma/dta.py#L445-L496), if $p < 0.10$ for the asymmetry test, the selection correction is:
```python
            ess_corr = dk["slope"] * float(np.mean(1.0 / np.sqrt(dk["ess"])))
            shift = 0.5 * ess_corr
            M = np.array([M[0] - shift, M[1] - shift])
```
This correctly subtracts the small-study bias from the summary logit coordinates:
$$ \ln(\operatorname{DOR}) \leftarrow \ln(\operatorname{DOR}) - \beta_{\text{slope}} \cdot \operatorname{mean}\left(\frac{1}{\sqrt{ESS}}\right) $$
preserving the threshold coordinate difference $M_1 - M_2$.

---

## 6. Findings and Audit Table

| Finding ID | Location / Code Symbol | Severity | Shipped-vs-Internal | Description / Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **AS-DTA-01** | `tests/test_dta.py` | **Info** (Truthful Caveat) | Internal | **HSROC Bivariate GLMM Not Present on Branch:** The exact-binomial bivariate GLMM and HSROC models are not implemented on the `methods-borrowing` branch; they live on the `methods-dta` branch/worktree. |
| **AS-DTA-02** | [dta.py:L488](file:///F:/ubcma/src/ubcma/dta.py#L488) | **Low** | Shipped | **GLS Covariance Unadjusted after Shift:** The selection correction shifts the mean vector $M$ but leaves the GLS covariance $V$ unadjusted. While standard for location corrections, it neglects the variance introduced by the regression shift itself. |

### Soundness Verdict
The bivariate DTA implementation in [dta.py](file:///F:/ubcma/src/ubcma/dta.py) is **MATHEMATICALLY SOUND**. All models (Reitsma, independent-Reitsma, and AdaptShrink-DTA) are correctly formulated, and the profile likelihood optimization, correlation shrinkage, and asymmetry test statistics are implemented with high numerical precision.
