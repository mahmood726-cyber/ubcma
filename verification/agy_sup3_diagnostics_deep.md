# Independent Third-Vendor Correctness Review: UBCMA Diagnostics Module

This document contains a deep correctness review of the diagnostics module implemented in [diagnostics.py](file:///F:/ubcma/src/ubcma/diagnostics.py). The review was performed from **first principles** on the `methods-borrowing` branch of the `ubcma` repository.

---

## 1. Leave-One-Out Influence and Cook's Distance Analysis

### A. Model Specification Mismatch (Dropped Design Covariates)
* **File & Line:** [diagnostics.py:187](file:///F:/ubcma/src/ubcma/diagnostics.py#L187)
* **Severity:** **P1** (Mathematical / Model Specification Bug)
* **Shipped-vs-Internal:** **Shipped / User-Facing**
* **First-Principles Derivation:**
  Let the full model be defined with parameters:
  $$\theta = \{\mu, \beta, \delta, \lambda_{\text{bias}}, \gamma_{\text{common}}, \gamma_{\text{quality}}, \tau_1, \tau_2, \text{mix}\}$$
  where:
  - $\mu$ is the treatment effect.
  - $\delta$ represents the coefficients for study design covariates (e.g., RCT vs. Observational).
  
  When design columns are present in the dataset, the full model estimates a non-empty vector $\delta$ of size $n_{design}$. The overall location for study $i$ is:
  $$\text{loc}_i = \mu + \mathbf{X}_{mod, i} \beta + \mathbf{X}_{design, i} \delta + \mathbf{Z}_{quality, i} \lambda_{\text{bias}}$$
  
  In the leave-one-out refitting loop, `drop_data` is constructed by setting `design_col=None`:
  ```python
  drop_data = MetaAnalysisDataset.from_dataframe(
      drop_df,
      quality_cols=quality_cols_arg,
      moderator_cols=moderator_cols_arg,
      design_col=None,  # skip design to avoid reference-level issues
      study_id_col="study_id" if has_study_id else None,
  )
  ```
  Consequently, the LOO fitter fits a **reduced model specification** where $n_{design} = 0$ (omitting $\delta$ entirely).
  
  The resulting LOO parameter estimate $\hat{\mu}_{-i}$ is calculated under a model that does *not* control for design characteristics, whereas the full estimate $\hat{\mu}_{\text{full}}$ did control for them. The difference:
  $$\Delta \mu_i = \hat{\mu}_{\text{full}} - \hat{\mu}_{-i}$$
  is therefore confounded by the omission of the design covariates. A study's computed influence (and its Cook's distance) will reflect both the omission of the study and the complete change in model specification, rendering the diagnostics mathematically incorrect.
* **Remedy:** Ensure the design column and reference level are preserved in the LOO fits, or raise an error/warning if LOO is run on a model with design covariates.

---

### B. Quality Column Autodetection Bug
* **File & Line:** [diagnostics.py:173](file:///F:/ubcma/src/ubcma/diagnostics.py#L173) and [diagnostics.py:185](file:///F:/ubcma/src/ubcma/diagnostics.py#L185)
* **Severity:** **P1** (Logic / Model Specification Bug)
* **Shipped-vs-Internal:** **Shipped / User-Facing**
* **First-Principles Analysis:**
  The full dataset may be initialized with `quality_cols=[]` to explicitly disable quality-bias adjustments. Under this setup, `data.quality_names` is empty (`[]`).
  
  In `leave_one_out`, the argument for the LOO dataset is prepared as:
  ```python
  quality_cols_arg: list[str] | None = data.quality_names if data.quality_names else None
  ```
  If `data.quality_names` is empty, `quality_cols_arg` evaluates to `None`.
  
  Inside `MetaAnalysisDataset.from_dataframe(drop_df, quality_cols=quality_cols_arg, ...)`:
  ```python
  if quality_cols is not None:
      quality_names = _split_csv_arg(quality_cols)
  else:
      quality_names = [col for col in df.columns if col.lower().startswith("rob_") or col.lower().startswith("bias_")]
  ```
  Since `quality_cols_arg` is `None`, the function falls back to **autodetecting** columns starting with `rob_` or `bias_` from the dataframe. If such columns exist in the raw dataframe, they will be autodetected and included in the LOO fits, even though they were excluded from the full model fit. This changes the model specification, causing incorrect parameter comparisons.
* **Remedy:** Pass `data.quality_names` directly without converting empty lists to `None`:
  ```python
  quality_cols_arg: list[str] | None = data.quality_names
  ```

---

### C. Missing $k < 5$ Guards (Silent LOO Failure)
* **File & Line:** [diagnostics.py:182-205](file:///F:/ubcma/src/ubcma/diagnostics.py#L182-L205)
* **Severity:** **P1** (Robustness / Usability Bug)
* **Shipped-vs-Internal:** **Shipped / User-Facing**
* **First-Principles Analysis:**
  The model fitter (`UBCMAFit.fit`) has a hard guard enforcing a minimum of 4 studies for fitting:
  ```python
  if data.n_studies < 4:
      raise ValueError("UBCMA needs at least 4 studies for a stable fit.")
  ```
  If `leave_one_out` is called on a dataset with $k = 4$ studies (which is a valid fit size), the full fit succeeds. However, each LOO iteration drops one study, leaving $k-1 = 3$ studies.
  
  The call `drop_fitter.fit(drop_data, allow_failed=True)` will raise a `ValueError` during the fit because $3 < 4$. The exception is caught by the broad `try...except Exception` block in `leave_one_out`, which silently sets all influence metrics (`delta_mu`, `delta_tau`, `delta_objective`, `cooks_d`) to `NaN`.
  
  Consequently, running LOO on 4 studies silently returns a DataFrame of `NaN`s without any warnings or errors explaining why.
* **Remedy:** Implement an explicit guard at the beginning of `leave_one_out`:
  ```python
  if data.n_studies < 5:
      raise ValueError("Leave-one-out influence analysis requires at least 5 studies (so that leave-one-out fits have at least 4 studies).")
  ```

---

### D. Invalid Likelihood / Objective Comparison
* **File & Line:** [diagnostics.py:199](file:///F:/ubcma/src/ubcma/diagnostics.py#L199)
* **Severity:** **P2** (Mathematical / Statistical Definition Issue)
* **Shipped-vs-Internal:** **Shipped / User-Facing**
* **First-Principles Derivation:**
  The function computes `delta_objective` as:
  $$\Delta \text{Objective} = \text{Objective}_{\text{full}}(\hat{\theta}) - \text{Objective}_{\text{LOO}}(\hat{\theta}_{-i})$$
  
  The objective function represents the negative log-likelihood (plus priors) over the given dataset. Let $D$ be the full dataset of $k$ studies and $D_{-i}$ be the dataset of $k-1$ studies omitting study $i$:
  $$\text{Objective}_{\text{full}}(\hat{\theta}) = -\sum_{j=1}^k \log \mathcal{L}(y_j \mid \hat{\theta}) - \log \text{Prior}(\hat{\theta})$$
  $$\text{Objective}_{\text{LOO}}(\hat{\theta}_{-i}) = -\sum_{j \neq i} \log \mathcal{L}(y_j \mid \hat{\theta}_{-i}) - \log \text{Prior}(\hat{\theta}_{-i})$$
  
  Subtracting these two values:
  $$\Delta \text{Objective} = -\log \mathcal{L}(y_i \mid \hat{\theta}) + \sum_{j \neq i} \left( \log \mathcal{L}(y_j \mid \hat{\theta}_{-i}) - \log \mathcal{L}(y_j \mid \hat{\theta}) \right) + \left( \log \text{Prior}(\hat{\theta}_{-i}) - \log \text{Prior}(\hat{\theta}) \right)$$
  
  This subtraction compares objectives evaluated on two different datasets of different sizes ($k$ vs $k-1$ observations). The term $-\log \mathcal{L}(y_i \mid \hat{\theta})$ dominates the subtraction simply because it is the omitted likelihood contribution of study $i$. This does not isolate the influence of study $i$ on the parameter estimates.
  
  To measure parameter-shift influence on the likelihood (known as **likelihood displacement**), both objectives must be evaluated on the *same* dataset (the full dataset):
  $$LD_i = 2 \times \left( \text{Objective}_{\text{full}}(\hat{\theta}_{-i}) - \text{Objective}_{\text{full}}(\hat{\theta}) \right)$$
* **Remedy:** Document `delta_objective` as a naive difference in dataset sizes, or compute the true likelihood displacement by evaluating the full objective function at the leave-one-out parameter estimates $\hat{\theta}_{-i}$.

---

### E. Cook's Distance Variance Denominator Approximation
* **File & Line:** [diagnostics.py:166-167](file:///F:/ubcma/src/ubcma/diagnostics.py#L166-L167)
* **Verdict:** **MATHEMATICALLY DEFENDED APPROXIMATION**
* **First-Principles Analysis:**
  Cook's distance for a parameter estimate $\mu$ is defined as:
  $$D_i = \frac{(\hat{\mu} - \hat{\mu}_{-i})^2}{\text{Var}(\hat{\mu})}$$
  
  In the code, $\text{Var}(\hat{\mu})$ is estimated using the standard DerSimonian-Laird (DL) random-effects model variance:
  ```python
  dl = dersimonian_laird(data.y, data.se)
  var_mu = max(dl["se"] ** 2, 1e-12)
  ```
  
  **Verification:**
  The full UBCMA model is fitted via maximum a posteriori (MAP) optimization (using L-BFGS-B on a penalized likelihood). It incorporates selection probabilities and quality-bias adjustments. A formal Hessian-based variance estimate of $\hat{\mu}$ is not computed during the fit.
  
  Using the DL standard error of the mean as a plug-in variance $\text{Var}(\hat{\mu})$ is a standard and robust approximation. It provides a consistent, scale-free scaling factor for the numerator $(\Delta \mu_i)^2$. The relative magnitude of $D_i$ across studies remains preserved, allowing correct identification of influential studies. Thus, the formula is mathematically defensible given the optimization constraints.

---

## 2. Standardized Residuals

### A. Misnomer in Studentization Definition
* **File & Line:** [diagnostics.py:23](file:///F:/ubcma/src/ubcma/diagnostics.py#L23)
* **Severity:** **P2** (Documentation / Terminology Issue)
* **Shipped-vs-Internal:** **Shipped / User-Facing**
* **First-Principles Derivation:**
  The docstring defines `standardized_residuals` as "Externally studentized Pearson residuals."
  However, the implementation computes:
  $$r_i = \frac{y_i - \text{loc}_i}{\sqrt{s_i^2 + \tau_1^2}}$$
  where $\text{loc}_i$ is the fitted study location and $\tau_1$ is the overall between-study standard deviation from the full model fit.
  
  This formula computes standard **Pearson residuals**, not studentized residuals.
  - **Internally studentized residuals** adjust for the leverage $h_i$ of study $i$:
    $$\text{SE}(y_i - \hat{y}_i) = \sqrt{(s_i^2 + \tau^2)(1 - h_i)}$$
    $$r_{i,\text{int}} = \frac{y_i - \hat{y}_i}{\sqrt{(s_i^2 + \tau^2)(1 - h_i)}}$$
  - **Externally studentized residuals** utilize the leave-one-out parameter estimates $\text{loc}_{i,-i}$ and $\tau_{-i}$ to isolate the study's influence:
    $$r_{i,\text{ext}} = \frac{y_i - \text{loc}_{i,-i}}{\sqrt{s_i^2 + \tau_{-i}^2 + \text{Var}(\text{loc}_{i,-i})}}$$
  
  The current code does not adjust for leverage or use LOO parameters. It simply divides by the marginal standard deviation under the full model.
* **Remedy:** Rename the docstring description to "Standardized Pearson residuals" to reflect the actual implementation.

---

### B. Lack of Empty / Small $k$ Guards
* **File & Line:** [diagnostics.py:22-35](file:///F:/ubcma/src/ubcma/diagnostics.py#L22-L35)
* **Severity:** **P2** (Robustness Issue)
* **Shipped-vs-Internal:** **Shipped / User-Facing**
* **First-Principles Analysis:**
  There are no guards against empty datasets (`len(y) == 0`).
  If the dataset is empty, `denom` is empty, and it returns an empty numpy array without raising an error. While this does not cause a crash immediately, it propagates empty arrays to downstream methods like `qq_plot_data` and `pvalue_distribution`, which could fail or produce misleading empty charts.
* **Remedy:** Add an empty check at the start of the function.

---

## 3. Information Criteria

### A. Parameter Count Mismatch in Reduced Models
* **File & Line:** [diagnostics.py:104](file:///F:/ubcma/src/ubcma/diagnostics.py#L104) and [diagnostics.py:126](file:///F:/ubcma/src/ubcma/diagnostics.py#L126)
* **Severity:** **P1** (Logic / Mismatch Bug)
* **Shipped-vs-Internal:** **Shipped / User-Facing**
* **First-Principles Analysis:**
  In `information_criteria`, the parameter counts for the refitted reduced models `no_selection` and `no_quality` are hardcoded as:
  $$n_{\text{no\_sel}} = 1 + n_{mod} + 0 + 0 + 4 + 0 + 3 = 8 + n_{mod}$$
  $$n_{\text{no\_qual}} = 1 + n_{mod} + 0 + 0 + 4 + 0 + 3 = 8 + n_{mod}$$
  
  However, the refitted models are obtained by calling `fitter.fit(no_sel_data)` and `fitter.fit(no_qual_data)`.
  If the raw dataset `data.raw` contains a column named `quality_score`, `no_sel_data` and `no_qual_data` will autodetect it (as a summary quality score) during construction because `quality_cols=[]` is passed.
  
  In `UBCMAFit.fit`, if `quality_score` is present and not all zero, `n_selection_quality` is set to `1` and the model is fitted with a non-empty `gamma_quality` vector (size 1).
  
  The actual fit estimates $9 + n_{mod}$ parameters, but the AIC/BIC calculation penalizes only $8 + n_{mod}$ parameters. This mismatch under-penalizes the reduced models, corrupting the AIC and BIC comparisons:
  $$\text{AIC} = 2 \cdot \text{NLL} + 2 \cdot n_{params}$$
  $$\text{BIC} = 2 \cdot \text{NLL} + n_{params} \cdot \log(k)$$
* **Remedy:** Dynamically compute parameter counts from the fitted result objects rather than hardcoding them:
  ```python
  def _get_param_count(res: UBCMAResult) -> int:
      return (
          1  # mu
          + len(res.params.get("beta", []))
          + len(res.params.get("delta", []))
          + len(res.params.get("lambda_bias", []))
          + len(res.params.get("gamma_common", []))
          + len(res.params.get("gamma_quality", []))
          + 3  # log_tau1, log_tau2_inc, logit_mix
      )
  ```

---

### B. Single-Component Likelihood Approximation
* **File & Line:** [diagnostics.py:131-134](file:///F:/ubcma/src/ubcma/diagnostics.py#L131-L134)
* **Severity:** **P2** (Statistical / Design Issue)
* **Shipped-vs-Internal:** **Shipped / User-Facing**
* **First-Principles Analysis:**
  The `single_component` reduced model uses the negative log-likelihood of the full two-component mixture model (`nll_full`) but subtracts 2 from the parameter count:
  ```python
  n_single = max(n_full - 2, 1)
  out["single_component"] = _aic_bic(nll_full, n_single)
  ```
  
  This is a crude approximation that does not refit a true single-component model. Since the two-component model has more flexibility, its NLL will always be lower than or equal to a true single-component model. Evaluating AIC/BIC using the lower NLL of the two-component model with the parameter penalty of the single-component model artificially favors the `single_component` model, yielding incorrect model comparison results.
* **Remedy:** Refit a true single-component model (setting the mixture weight to 1 or omitting the second component parameters) to obtain its true NLL, or document this as a simplified upper-bound approximation.

---

### C. Null Model Fixed-Effect Likelihood
* **File & Line:** [diagnostics.py:136-145](file:///F:/ubcma/src/ubcma/diagnostics.py#L136-L145)
* **Verdict:** **CORRECT**
* **First-Principles Verification:**
  The likelihood of a fixed-effect meta-analysis model $y_i \sim N(\mu, s_i^2)$ is:
  $$\mathcal{L}(\mu) = \prod_{i=1}^k \frac{1}{\sqrt{2\pi s_i^2}} \exp\left( -\frac{(y_i - \mu)^2}{2s_i^2} \right)$$
  
  The negative log-likelihood is:
  $$-\log \mathcal{L}(\mu) = 0.5 \sum_{i=1}^k \left( \log(2\pi s_i^2) + \frac{(y_i - \mu)^2}{s_i^2} \right)$$
  
  This matches the implementation in the code:
  ```python
  nll_null = float(
      0.5 * np.sum(
          np.log(2.0 * np.pi * np.square(data.se))
          + np.square(data.y - mu_fe) / np.square(data.se)
      )
  )
  ```
  where `mu_fe` is the fixed-effect weighted mean $\frac{\sum w_i y_i}{\sum w_i}$ with $w_i = 1/s_i^2$. The derivation is mathematically correct.

---

## 4. Selection Function Grid

* **File & Line:** [diagnostics.py:220-265](file:///F:/ubcma/src/ubcma/diagnostics.py#L220-L265)
* **Verdict:** **CORRECT**
* **First-Principles Verification:**
  The selection function grid maps z-scores and precisions to the estimated selection probability $P(\text{selected})$.
  - It correctly evaluates the selection probability on centered precision `precision_z = 0.0` (corresponding to the population average precision).
  - It correctly handles quality features by evaluating them at zero (`qual_feat = np.zeros(...)`), representing the reference level of study quality (no quality-based selection shift).
  - The grid spacing and mapping of $y = z \cdot \text{se}$ matches the model's formulation of the selection function. The routine is correct.

---

## 5. Q-Q Plot and Observed P-Value Distribution

### A. Q-Q Plot Quantiles
* **File & Line:** [diagnostics.py:268-277](file:///F:/ubcma/src/ubcma/diagnostics.py#L268-L277)
* **Verdict:** **CORRECT**
* **First-Principles Verification:**
  Theoretical quantiles are obtained using Hazen's plotting positions:
  $$q_i = \Phi^{-1}\left(\frac{i - 0.5}{n}\right)$$
  where $\Phi^{-1}$ is the percent point function (`norm.ppf`) of the standard normal distribution. This is a standard formulation for plotting sample quantiles against theoretical normal quantiles. The math is correct.

---

### B. Observed P-Value Distribution
* **File & Line:** [diagnostics.py:279-294](file:///F:/ubcma/src/ubcma/diagnostics.py#L279-L294)
* **Verdict:** **CORRECT**
* **First-Principles Verification:**
  The two-sided p-value for the standardized residual $r_i$ under $N(0,1)$ is:
  $$p_i = 2 \times \left(1 - \Phi(|r_i|)\right)$$
  This matches:
  ```python
  pvalues = 2.0 * (1.0 - _norm.cdf(np.abs(r)))
  ```
  Binned uniformly into 10 bins over $[0,1]$, the expected count under the null hypothesis (uniform distribution of p-values) is $N / 10$, where $N = \text{len}(r)$. This matches `expected = float(len(r)) / 10.0`. The implementation is correct.

---

## 6. Omitted Diagnostic Routines

### A. Baujat Coordinates (Missing Diagnostic)
* **Severity:** **P2** (Completeness / Missing Feature)
* **Shipped-vs-Internal:** **Missing**
* **First-Principles Definition:**
  Baujat coordinates identify studies that contribute excessively to heterogeneity and/or the overall treatment effect.
  For each study $i$:
  - **X-axis (heterogeneity contribution):** The squared standardized residual of the study from the fixed-effect model (or the contribution to Cochrane's Q):
    $$X_i = \frac{(y_i - \hat{\mu}_{-i})^2}{s_i^2}$$
  - **Y-axis (pooled effect influence):** The squared difference between the overall effect and the LOO effect, standardized by the variance of the LOO estimate:
    $$Y_i = \frac{(\hat{\mu} - \hat{\mu}_{-i})^2}{\text{Var}(\hat{\mu}_{-i})}$$
  Neither this plotting data nor the corresponding coordinate calculation is implemented in `diagnostics.py`.

---

### B. GOSH / Subset Resampling (Missing Diagnostic)
* **Severity:** **P2** (Completeness / Missing Feature)
* **Shipped-vs-Internal:** **Missing**
* **First-Principles Definition:**
  Graphical Display of Study Heterogeneity (GOSH) plots are generated by fitting the meta-analysis model on a large number of subsets of the studies (e.g., $M \approx 10^3$ random combinations).
  Plotting the pooled effect size $\hat{\mu}$ against heterogeneity ($\tau^2$ or $I^2$) for each subset highlights distinct clusters, indicating outlying studies or multiple treatment effects.
  This resampling and subset diagnostic capability is entirely missing from the codebase.
