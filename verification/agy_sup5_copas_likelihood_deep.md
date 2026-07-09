# Copas Selection Model Likelihood Deep Analysis Report: First-Principles Derivation and Mis-specification Assessment

This report provides an independent third-vendor deep analysis of the likelihood formulation used in the Copas publication selection model within the Unified Bias-Calibrated Meta-Analysis (UBCMA) framework.

---

## Executive Summary

- **Verdict:** **MIS-SPECIFIED (Option C)**
- **Target File:** [comparators.py](file:///F:/ubcma/src/ubcma/comparators.py)
- **Target Function:** [copas_selection](file:///F:/ubcma/src/ubcma/comparators.py#L150-L237)
- **Primary Finding:** The likelihood optimization in `copas_selection` uses a hybrid formulation that models the observed effect sizes $y_i$ using selection-adjusted conditional moments (mean and variance) while adding a positive selection log-probability term `ll += np.sum(np.log(Phi_u))`. 
  - Under first principles, this hybrid form is **mis-specified (Option C)** because it inverts the sign of the selection probability term. 
  - In a proper conditional likelihood for observed studies (where the number of unselected studies is unknown), the selection probability term $\log \Phi(u_i)$ must enter with a **negative sign** (subtracted) to normalize the conditional density. 
  - Alternatively, if using the selection-adjusted moments approximation to the conditional density, no selection probability term should be added at all.
- **Direction of Bias:** The $+ \log \Phi(u_i)$ term acts as a heavy penalty that drives the optimizer toward the "no selection" limit ($\gamma_0 \to \infty$, where $\Phi(u_i) \to 1$). Consequently, under strong selection, the estimator **under-corrects** selection bias, yielding a pooled mean estimate $\hat{\mu}_{\text{code}}$ that is closer to the uncorrected naive pool (larger/more positive under positive publication selection) than the exact corrected estimate:
  $$ \hat{\mu}_{\text{exact}} < \hat{\mu}_{\text{code}} < \hat{\mu}_{\text{naive}} $$
- **Scope of Impact:** This issue only affects the standalone **Copas comparator** column in the diagnostic and comparison tables. It does **not** affect the default panel of **AdaptShrink**, which excludes the Copas estimator from its ensemble.

---

## 1. First-Principles Derivation of the Exact Copas-Shi (2000) Likelihood

Let study $i$ (for $i = 1, \dots, n$) have:
- An observed effect size $y_i$
- A known standard error $s_i$
- A between-study variance parameter $\tau^2$, defining the marginal variance $\sigma_i^2 = s_i^2 + \tau^2$

### The Probability Model
The Copas selection model consists of two equations:
1. **Outcome Equation:**
   $$ y_i = \mu + \eta_i, \quad \eta_i \sim N(0, \sigma_i^2) $$
2. **Selection Equation:**
   $$ z_i = u_i + \delta_i, \quad u_i = \gamma_0 + \frac{\gamma_1}{s_i}, \quad \delta_i \sim N(0, 1) $$
   where study $i$ is observed (selected) if and only if the latent variable $z_i > 0$.

The error terms $\eta_i$ and $\delta_i$ are assumed to follow a bivariate normal distribution:
$$ \begin{pmatrix} \eta_i \\ \delta_i \end{pmatrix} \sim N \left( \begin{pmatrix} 0 \\ 0 \end{pmatrix}, \begin{pmatrix} \sigma_i^2 & \rho \sigma_i \\ \rho \sigma_i & 1 \end{pmatrix} \right) $$
where $\rho \in [-1, 1]$ is the correlation between the outcome error and the selection error.

### Unconditional Probability of Selection
A study is selected if $z_i > 0$, which is equivalent to $\delta_i > -u_i$. Since $\delta_i \sim N(0, 1)$, the probability of selection is:
$$ P(z_i > 0) = P(\delta_i > -u_i) = \Phi(u_i) $$
where $\Phi(\cdot)$ is the cumulative distribution function (CDF) of the standard normal distribution.

### Conditional Probability of Selection Given the Outcome
Because we only observe the effect sizes $y_i$ of selected studies, we must find the joint distribution of $y_i$ and the selection event $z_i > 0$. By Bayes' theorem, the joint density is:
$$ f(y_i, z_i > 0) = f(y_i) P(z_i > 0 \mid y_i) $$
where $f(y_i)$ is the marginal (unadjusted) density of $y_i$:
$$ f(y_i) = \frac{1}{\sqrt{2\pi}\sigma_i} \exp\left( - \frac{(y_i - \mu)^2}{2\sigma_i^2} \right) $$

To evaluate $P(z_i > 0 \mid y_i)$, we compute the conditional distribution of $\delta_i$ given $y_i$ (or equivalently given $\eta_i = y_i - \mu$). From the properties of the bivariate normal distribution:
- **Conditional Mean:**
  $$ E[\delta_i \mid y_i] = E[\delta_i] + \frac{\text{Cov}(\eta_i, \delta_i)}{\text{Var}(\eta_i)}(y_i - \mu) = 0 + \frac{\rho \sigma_i}{\sigma_i^2}(y_i - \mu) = \frac{\rho(y_i - \mu)}{\sigma_i} $$
- **Conditional Variance:**
  $$ \text{Var}(\delta_i \mid y_i) = \text{Var}(\delta_i) - \frac{\text{Cov}(\eta_i, \delta_i)^2}{\text{Var}(\eta_i)} = 1 - \frac{\rho^2 \sigma_i^2}{\sigma_i^2} = 1 - \rho^2 $$

Thus:
$$ \delta_i \mid y_i \sim N\left( \frac{\rho(y_i - \mu)}{\sigma_i}, 1 - \rho^2 \right) $$

The conditional selection probability is:
$$ P(z_i > 0 \mid y_i) = P(\delta_i > -u_i \mid y_i) $$
Standardizing the variable $\delta_i$ under its conditional distribution:
$$ P(z_i > 0 \mid y_i) = P\left( \frac{\delta_i - E[\delta_i \mid y_i]}{\sqrt{1 - \rho^2}} > \frac{-u_i - \frac{\rho(y_i - \mu)}{\sigma_i}}{\sqrt{1 - \rho^2}} \;\middle|\; y_i \right) $$
Letting $W \sim N(0, 1)$ represent the standardized variable, and using the symmetry of the normal distribution ($P(W > -x) = \Phi(x)$):
$$ P(z_i > 0 \mid y_i) = \Phi\left( \frac{u_i + \rho \frac{y_i - \mu}{\sigma_i}}{\sqrt{1 - \rho^2}} \right) $$
Letting $v_i = \frac{u_i + \rho(y_i - \mu)/\sigma_i}{\sqrt{1 - \rho^2}}$, we obtain:
$$ P(z_i > 0 \mid y_i) = \Phi(v_i) $$

### The Exact Conditional Log-Likelihood
In a meta-analysis, the total pool of conducted but unpublished (unselected) studies is unknown. Therefore, the likelihood of the observed effect sizes must be conditioned on the event that they were selected:
$$ L_i = f(y_i \mid z_i > 0) = \frac{f(y_i, z_i > 0)}{P(z_i > 0)} = \frac{f(y_i) \Phi(v_i)}{\Phi(u_i)} $$

Taking the natural logarithm of $L_i$ yields the exact log-likelihood contribution for study $i$:
$$ \log L_i^{\text{exact}} = \log f(y_i) + \log \Phi(v_i) - \log \Phi(u_i) $$
Substituting the Gaussian density for $f(y_i)$:
$$ \log L_i^{\text{exact}} = -\frac{1}{2}\log(2\pi) - \frac{1}{2}\log(\sigma_i^2) - \frac{(y_i - \mu)^2}{2\sigma_i^2} + \log \Phi(v_i) - \log \Phi(u_i) $$

Summing over all observed studies, the exact Copas-Shi observed-data log-likelihood is:
$$ \log L_{\text{exact}} = \sum_{i=1}^n \left[ -\frac{1}{2}\log(2\pi) - \frac{1}{2}\log(\sigma_i^2) - \frac{(y_i - \mu)^2}{2\sigma_i^2} + \log \Phi(v_i) - \log \Phi(u_i) \right] $$

---

## 2. Mathematical Comparison and Characterization of the Code's Hybrid Form

The current implementation in `src/ubcma/comparators.py` computes the log-likelihood as:
```python
ll = -0.5 * np.sum(np.log(adj_var) + np.square(y - adj_mean) / adj_var)
ll += np.sum(np.log(Phi_u))
```
Expressing this mathematically (omitting the constant $-0.5 \log(2\pi)$):
$$ \log L_{\text{code}} = \sum_{i=1}^n \left[ -\frac{1}{2}\log(\text{adj\_var}_i) - \frac{(y_i - \text{adj\_mean}_i)^2}{2\,\text{adj\_var}_i} \right] + \sum_{i=1}^n \log \Phi(u_i) $$
where $\text{adj\_mean}_i$ and $\text{adj\_var}_i$ are the selection-adjusted conditional moments:
- $\text{adj\_mean}_i = \mu + \rho \sigma_i \lambda(u_i)$
- $\text{adj\_var}_i = \sigma_i^2 \left( 1 - \rho^2 u_i \lambda(u_i) - \rho^2 \lambda(u_i)^2 \right)$
with the inverse Mills ratio $\lambda(u_i) = \phi(u_i)/\Phi(u_i)$.

### Categorization: Mis-specified with the Wrong Sign (Option C)

The code's hybrid form is **mis-specified with the wrong sign on the $\log \Phi(u)$ term (Option C)**. 

To see why, let us evaluate the three possibilities:
- **(a) Equivalent:** No. The code's expression utilizes the conditional moments ($\text{adj\_mean}, \text{adj\_var}$) inside a Gaussian density, which is a normal approximation to the skewed truncated distribution of $y_i \mid z_i > 0$. However, even as an approximation, it adds $+\log \Phi(u_i)$ instead of subtracting it, which fundamentally alters the shape of the likelihood surface.
- **(b) Valid Alternative Parameterization:** No. A valid alternative parameterization would preserve the likelihood surface and the maximum likelihood estimates (MLEs) under a change of variables. The hybrid form does not correspond to the likelihood of any valid joint or conditional probability distribution. 
- **(c) Mis-specified with the Wrong Sign:** Yes. 
  1. If the code is attempting to approximate the **conditional** density $f(y_i \mid z_i > 0)$ using the selection-adjusted moments, the probability of selection has already been conditioned upon to derive $\text{adj\_mean}$ and $\text{adj\_var}$. Therefore, **no additional $\log \Phi(u_i)$ term** should be added.
  2. If the code is attempting to approximate the **joint** density $f(y_i, z_i > 0) = f(y_i \mid z_i > 0) \Phi(u_i)$, the log-joint likelihood would be:
     $$ \log L_{\text{joint}} \approx \sum_{i=1}^n \log N(y_i; \text{adj\_mean}_i, \text{adj\_var}_i) + \sum_{i=1}^n \log \Phi(u_i) $$
     This matches the code's sign ($+\sum \log \Phi(u_i)$). However, optimizing a joint likelihood of observed cases without normalizing for the unobserved cases is inappropriate for meta-analysis where $N - n$ is unknown.
  3. When conditioning on selection to obtain the correct conditional likelihood, the selection probability appears in the denominator, which translates to a **minus sign** ($-\log \Phi(u_i)$). By using $+\log \Phi(u_i)$, the code flips the sign of the selection correction term.

---

## 3. Analysis of the Mis-specification and Bias Direction

### Exact Corrected Objectives

To implement the Copas model correctly, two alternative paths are mathematically valid:

#### Path 1: The Exact Copas-Shi (2000) NLL (Recommended)
This path avoids the normal approximation of the conditional density and optimizes the exact likelihood. The negative log-likelihood (NLL) to be minimized for a given grid point $\rho$ is:
$$ NLL_{\text{exact}}(\mu, \tau^2, \gamma_0, \gamma_1) = \sum_{i=1}^n \left[ \frac{1}{2}\log(s_i^2 + \tau^2) + \frac{(y_i - \mu)^2}{2(s_i^2 + \tau^2)} - \log \Phi(v_i) + \log \Phi(u_i) \right] $$
where:
$$ u_i = \gamma_0 + \frac{\gamma_1}{s_i} $$
$$ v_i = \frac{u_i + \rho \frac{y_i - \mu}{\sqrt{s_i^2 + \tau^2}}}{\sqrt{1 - \rho^2}} $$

#### Path 2: Moment-Based Conditional NLL
If one wishes to use the selection-adjusted moments approximation to the conditional density, the correct NLL is:
$$ NLL_{\text{approx\_conditional}}(\mu, \tau^2, \gamma_0, \gamma_1) = \sum_{i=1}^n \left[ \frac{1}{2}\log(\text{adj\_var}_i) + \frac{(y_i - \text{adj\_mean}_i)^2}{2\,\text{adj\_var}_i} \right] $$
Note that **no $\log \Phi(u_i)$ term is present** because the selection event has already been conditioned upon to obtain the adjusted moments.

---

### Prediction of the Direction of $\hat{\mu}$ under Strong Selection

Under strong positive selection (where studies with larger positive effect sizes are more likely to be published, particularly when standard errors are large):
1. The naive REML estimate $\hat{\mu}_{\text{naive}}$ is biased upwards (too positive).
2. The exact selection-corrected estimator $\hat{\mu}_{\text{exact}}$ corrects this by shifting the pooled mean downwards (more negative / less positive):
   $$ \hat{\mu}_{\text{exact}} < \hat{\mu}_{\text{naive}} $$
3. In the code's hybrid likelihood, the selection probability term enters as $+ \sum \log \Phi(u_i)$. Since $\Phi(u_i) \le 1$, the term $\log \Phi(u_i) \le 0$ is always non-positive.
4. To maximize the hybrid log-likelihood, the optimizer is driven to make $+ \sum \log \Phi(u_i)$ as close to 0 as possible. This forces $u_i \to \infty$, which corresponds to $\gamma_0 \to \infty$ (i.e. the "selection probability is 1 / selection is off" limit).
5. As $\gamma_0 \to \infty$, the inverse Mills ratio $\lambda(u_i) \to 0$, causing the selection adjustment term $\rho \sigma_i \lambda(u_i) \to 0$. The adjusted mean collapses back to the unadjusted mean:
   $$ \text{adj\_mean}_i \to \mu $$
6. Thus, the $+ \log \Phi(u_i)$ term acts as a heavy penalty that discourages selection correction, biasing the model towards the uncorrected naive pool.
7. Consequently, under strong positive selection, the code's estimator will **under-correct**, leading to an estimate $\hat{\mu}_{\text{code}}$ that is larger (more positive / less negative) than the exact selection-corrected estimate $\hat{\mu}_{\text{exact}}$:
   $$ \hat{\mu}_{\text{exact}} < \hat{\mu}_{\text{code}} < \hat{\mu}_{\text{naive}} $$

---

## 4. Scope and Pipeline Impact

This mis-specification is isolated to the `copas_selection` comparator in [comparators.py](file:///F:/ubcma/src/ubcma/comparators.py).

- **AdaptShrink Panel Exclusion:** The default ensemble panel of **AdaptShrink** does **not** include the Copas comparator. AdaptShrink utilizes its own shrinkage estimators, PET-PEESE, and other robust estimators, but excludes the Copas selection model from its core model averaging/ensemble selection.
- **Comparator Tables Only:** The wrong sign on the $\log \Phi(u_i)$ term affects only the standalone "Copas" comparator column in simulation tables and diagnostic plots. It leads to reported Copas results that under-correct the publication bias compared to a correct implementation of the Copas-Shi (2000) model.
- **Verification Summary:**
  - Naive Pool: Biased by selection.
  - Current Code Copas: Partially corrected but biased towards the naive pool due to the $+ \log \Phi(u_i)$ penalty.
  - Exact Copas: Fully corrected.
