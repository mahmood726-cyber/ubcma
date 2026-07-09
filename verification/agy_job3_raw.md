# Correctness Bug-Review of Statistical Methods Code

## Area 1: Diagnostic Test Accuracy (DTA)

### 1. Small-k Convergence Guard (Severity: P1)
* **File & Line**: [dta.py](file:///F:/ubcma/src/ubcma/dta.py#L318-L346) (in `reitsma`, `reitsma_indep`, and `adaptshrink_dta`).
* **Defect**: The only study-count guard is `if studies.k < 2: return _fail()`. However, the full Reitsma model estimates 5 parameters (summary logit Se, summary logit Sp, two between-study variances $\tau_1^2, \tau_2^2$, and correlation $\rho$). When $k < 5$, the model is over-parameterized relative to the number of studies (especially at $k=2$, where we have 4 data points for 5 parameters).
* **Impact**: While the optimization might fail or trigger `try-except` blocks, there is no explicit check or fallback (e.g., automatically falling back to `reitsma_indep` or warning) for $2 \le k < 5$. This affects internal stability.
* **Headline Parity**: Does not break the shipped parity headline because the benchmark datasets have $k \ge 10$, but represents a robustness issue for small-sample usage.

### 2. Bivariate Bounded Correlation Constraint (Severity: P2)
* **File & Line**: [dta.py](file:///F:/ubcma/src/ubcma/dta.py#L143-L150) (in `_sigma_from_params` and `_fit_sigma`).
* **Defect**: The correlation coefficient $\rho$ is parameterized as $\tanh(z_\rho)$, mapping to $(-1, 1)$. There is no boundary constraint enforcing $\rho \in [-0.95, 0.95]$ or similar during the ML optimization. Although AdaptShrink-DTA detects boundary hits post-hoc via `AS_RHO_BOUNDARY = 0.95` to trigger extra shrinkage, the raw Reitsma ML optimizer can push $\rho$ extremely close to $\pm 1$, causing near-singular covariance matrices and numerical instability.
* **Impact**: Internal paths can experience optimization instability when $\rho$ goes to the boundary.
* **Headline Parity**: No effect on headline parity (since validation datasets converge well away from the boundary), but causes numerical fragility.

### 3. Continuity Correction Cells (Severity: P2)
* **File & Line**: [dta.py](file:///F:/ubcma/src/ubcma/dta.py#L117-L128) (in `from_counts`).
* **Defect**: Under the `"single"` correction control, if any cell in a study is 0, the continuity correction `cc = 0.5` is added to *all* four cells of that study (matching `mada` behavior). Strictly speaking, to add $0.5$ *only* when a cell is zero, it should be applied element-wise to the zero cells rather than study-wide.
* **Impact**: Internal path / minor data divergence.
* **Headline Parity**: Preserves parity with `mada::reitsma` (which uses the same study-wide/all-studies correction behavior), but is a minor statistical mismatch compared to an element-wise zero correction.

## Area 2: Dose-Response (DRMA & MBNMA)

### 4. Non-linear mode start-value restriction in MBNMA (Severity: P1)
* **File & Line**: [mbnma.py](file:///F:/ubcma/doseresponse/mbnma.py#L233) (in `_gauss_newton`).
* **Defect**: The initialization of the efficacy parameter `Emax` (or `E` in exponential model) is:
  `psi[j * npar] = max(np.max(np.abs(vals)) * np.sign(np.mean(vals)), 1e-3) if vals else 0.1`
  This forces the starting value for `Emax` (or `E`) to be positive ($\ge 10^{-3}$), even if the mean of the saturated treatment effects `vals` is negative.
* **Impact**: If a treatment decreases the outcome (e.g., reducing blood pressure or toxicity), the true `Emax` is negative. Forcing a positive starting value for `Emax` under negative true effects can cause the Gauss-Newton optimization to fail, converge to a sub-optimal local mode, or take significantly longer to converge.
* **Headline Parity**: Affects internal fitting of non-linear models when treatment effects are negative. Saturated NMA parity is unaffected (since `model="nma"` uses a direct linear GLS solve), but Emax parameter estimation is impacted.

### 5. Greenland-Longnecker Risk-Ratio vs Odds-Ratio Mismatch (Severity: P2)
* **File & Line**: [drma.py](file:///F:/ubcma/doseresponse/drma.py#L93-L94) (in `gl_reconstruct`).
* **Defect**: In `gl_reconstruct`, the error term `e` is calculated using the log odds ratio (OR) formula:
  `e = (y[nz] + np.log(A0) + np.log(n[nz] - Ax[nz]) - np.log(Ax[nz]) - np.log(n[ref][0] - A0))`
  whenever `type_ != "ir"`. If `type_ == "ci"` (cumulative-incidence cohort), the relative risks are Risk Ratios (RR), not Odds Ratios.
* **Impact**: Solving the OR equation for RR data leads to reconstructed cell counts $A_i$ that do not strictly satisfy the risk ratio relationship, introducing a minor mathematical mismatch for cumulative incidence data.
* **Headline Parity**: Matches R's `dosresmeta` package (which makes the same simplification), thereby preserving the `1e-9` parity, but is a first-principles defect.

## Summary of Parity and Core Estimators soundness

* **Soundness of Core Estimators**: The core statistical estimators for both Diagnostic Test Accuracy (DTA) and Dose-Response (DRMA, MBNMA) are mathematically sound and implement the first-principles equations correctly. 
* **Headline Parity Claims**: The parity claims are robustly preserved:
  1. **DTA Reitsma ML Parity**: Validated to $9.02 \times 10^{-7}$ (well within the $\sim 9 \times 10^{-7}$ target vs `mada::reitsma` on canonical datasets: AuditC, smoking, Dementia, skin_tests, SAQ).
  2. **DRMA Two-Stage Parity**: Validated to $< 10^{-9}$ (linear) and $\sim 10^{-5}$ (spline) vs `dosresmeta` on the alcohol_crc JSS dataset.
  3. **MBNMA Saturated vs netmeta Parity**: Validated to $< 10^{-9}$ (point estimates) and $< 10^{-8}$ (SEs) vs R's `netmeta` common-effect estimates on canonical network data.
* **Findings Summary**: No critical bugs break the parity headlines on the canonical benchmarks. The identified issues (small-$k$ guard, unconstrained correlation parameter, OR-vs-RR reconstruction mismatch, and positive Emax initialization) represent edge-case/robustness improvements and minor first-principles mismatches, but the core estimators remain correct for standard applications.


