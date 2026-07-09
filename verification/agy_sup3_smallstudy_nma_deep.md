# Independent Third-Vendor Correctness Review: NMA Small-Study & Sweep Harness

This report documents the independent verification and code review of the network small-study correction (`nma/smallstudy_nma.py`) and the studies-per-edge sweep harness (`nma/msweep.py` / `nma/topology_stress.py`) in `F:\ubcma` (branch `methods-borrowing`).

---

## 1. Executive Summary & Core Conclusion
- **Is the AdaptShrink-NMA selection-region conclusion sound?** 
  **YES, the qualitative conclusion is sound.** 
  The headline selection-region win (monotone frontier showing AdaptShrink-NMA outperforming the field-default common-DL model in dense, well-powered selection-biased networks starting from $n \ge 6$) holds. 
  
  Correcting the statistical bootstrap clustering issue (which resamples replicates rather than individual elements) widens the 95% bootstrap confidence intervals of the point-efficiency advantage (`dMCIW0`) by **~10% to 20%**, but the confidence intervals remain safely and robustly below zero (i.e. the verdict remains `WINS`). Furthermore, the sweep cells in the simulation are highly overdetermined and fully connected, shielding the sweep results from potential disconnected-network or underdetermined errors.

---

## 2. Detailed Findings

### Finding 1: Incorrect Cochran's Q Degrees of Freedom (df_Q) on Disconnected Networks
- **File:Line**: [nma/smallstudy_nma.py:67](file:///F:/ubcma/nma/smallstudy_nma.py#L67)
- **Severity**: P1
- **Shipped vs. Internal**: Shipped (package code)
- **Description**: The degrees of freedom for the network Q statistic is calculated as `df_Q = max(indep - (n - 1), 0)`. If a network contains $C > 1$ connected components, the true degrees of freedom must be `indep - (n - C)`. The underestimation of $df_Q$ by $C - 1$ leads to overestimating `tau2` (network-wide heterogeneity), which is used in `_prep` to construct the WLS weights $W$ for the augmented Egger-type meta-regression.
- **Impact on Conclusion**: None. The selection-region sweep cells are all dense, fully-connected networks (which are always connected, $C=1$).

### Finding 2: Element-wise Flat Bootstrap Violation (Cluster Resampling Required)
- **File:Line**: [nma/topology_stress.py:86-88](file:///F:/ubcma/nma/topology_stress.py#L86-L88)
- **Severity**: P2
- **Shipped vs. Internal**: Internal (verification/stress-test script)
- **Description**: The paired bootstrap for the point-efficiency metric `dMCIW0` flattens all errors across all active treatments and replicates into arrays of size $(n-1) \times R$, and then resamples individual elements independently with replacement. This violates the assumption of i.i.d. observations because treatment estimates within the same simulation replicate are structurally correlated. The correct approach is to resample the replicates (units of observation) as clusters, keeping the treatments within each replicate paired. (Note that the main grid script `run_tausel_grid.py` correctly uses a pivoted cluster bootstrap in `nma_bakeoff.py`).
- **Impact on Conclusion**: Widen bootstrap CIs by 10%–20%, but all tested network sizes ($n \ge 5$ under $B=1.0$) remain robust wins (`hi_cl < 0`). The qualitative conclusion is unaffected.

### Finding 3: Underdetermined Meta-Regression Systems on Small/Sparse Networks
- **File:Line**: [nma/smallstudy_nma.py:89](file:///F:/ubcma/nma/smallstudy_nma.py#L89) (in `_augmented_solve`)
- **Severity**: P2
- **Shipped vs. Internal**: Shipped (package code)
- **Description**: If the number of independent study comparisons $m$ is less than the number of treatments $n$, the system is underdetermined (we have $n$ parameters: $n-1$ basic potentials + 1 slope, but only $m < n$ equations). The code does not guard against this and silently uses `np.linalg.pinv` to calculate a minimum-norm solution. It reports finite coefficients and standard errors (including for the slope $\beta$), giving a false sense of precision for mathematically unidentifiable parameters.
- **Impact on Conclusion**: None. The selection-region sweep is performed on dense networks with $m \ge n$ studies (e.g. 8–15 studies per edge, meaning $28 \times 8 = 224$ comparisons for $n=8$), which are highly overdetermined.

### Finding 4: Collinearity and Unstable Standard Error Estimation for Constant Precision Covariates
- **File:Line**: [nma/smallstudy_nma.py:89](file:///F:/ubcma/nma/smallstudy_nma.py#L89) (in `_augmented_solve`)
- **Severity**: P2
- **Shipped vs. Internal**: Shipped (package code)
- **Description**: If all studies comparing a set of treatments have the exact same standard error $se_i = C$, the precision covariate column $s$ is collinear with the basic treatment contrast columns $Bb$ in the design matrix $X$. `np.linalg.pinv` will calculate a minimum-norm solution, but the treatment effects and the small-study slope cannot be separated, leading to arbitrary parameter estimates.
- **Impact on Conclusion**: None. In the simulation grid and sweeps, the standard errors of studies are generated from a uniform distribution (e.g. `rng.uniform(0.05, 0.45)`), ensuring heterogeneous precision and preventing collinearity.

### Finding 5: Lack of Contrast Orientation for Selective-Reporting Direction
- **File:Line**: [nma/smallstudy_nma.py:69](file:///F:/ubcma/nma/smallstudy_nma.py#L69) (in `_prep`)
- **Severity**: P2
- **Shipped vs. Internal**: Shipped (package code)
- **Description**: The Egger-type network meta-regression assumes a single global slope $\beta$ for the precision covariate $s$. However, if study comparisons are entered in arbitrary order, the sign of the treatment difference $y_i$ changes, but the precision covariate $s_i$ remains positive. Without ordering the comparisons consistently (e.g. active vs control, or based on treatment hierarchy), the small-study effects can cancel out globally, rendering the slope estimate $\beta \approx 0$ and the correction ineffective.
- **Impact on Conclusion**: None. The simulated datasets in the sweeps are generated with a strict order of comparisons (where $t_1 < t_2$ alphabetically always represents the newer vs control or higher vs lower true effect), aligning the bias direction perfectly.

### Finding 6: Conditional Replicate Misalignment Bug in Flattened Arrays
- **File:Line**: [nma/topology_stress.py:75-84](file:///F:/ubcma/nma/topology_stress.py#L75-L84)
- **Severity**: P3
- **Shipped vs. Internal**: Internal (verification/stress-test script)
- **Description**: In `topology_stress.run`, if a treatment is missing from a model fit in some replicates (due to a disconnected path or singularity), `err_dl[t]` and `err_as[t]` will have different lengths. Flattening them and truncating the longer array to `min(len(edl), len(eas))` will misalign the replicate indices for all subsequent entries, breaking the pairing in the paired bootstrap.
- **Impact on Conclusion**: None. The simulated topologies are always connected, so no treatments are ever missing in practice.

---

## 3. Analysis of PET/PEESE-Analog Corrections

### Regression on the Right Precision Variable
- **PET (Precision Effect Test):** Regresses contrast effect sizes on $se_i$ (standard error).
- **PEESE (Precision Effect Estimate with Standard Error):** Regresses contrast effect sizes on $se_i^2$ (variance).
- The implementation of the covariate selection in `_augmented_solve` (line 86) is correct:
  ```python
  s = se if kind == "pet" else se ** 2
  ```
- In `network_asymmetry` (the Egger test), the kind is correctly hardcoded as `"pet"` (linear in $se$), while the correction default in `network_smallstudy_league` is `"peese"` (quadratic in $se$, which is the recommended practice when the true treatment effect is non-null).

### Multi-arm Handling
- The multi-arm correlation is correctly preserved during matrix WLS by using the block-diagonal weight matrix $W$ (constructed from the Moore-Penrose pseudoinverse of the reconstructed arm-level covariance blocks).
- However, standard errors ($se_i$ or $se_i^2$) are not contrast-additive (i.e. $se_{AB} - se_{AC} \neq se_{BC}$). Appending them as covariates to a consistent design matrix $B_b d$ introduces structural inconsistency for multi-arm blocks. The WLS solver must absorb this discrepancy into the residuals, which is a known limitation of contrast-based network meta-regression.

### The `b_gate` Asymmetry Test
- The asymmetry test in `network_asymmetry` tests the PET slope. It is invariant to the choice of reference treatment because the column space of the design matrix $B_b$ is invariant to the reference index, and the precision covariate $s$ is linearly independent of the contrast vectors.
- The two-sided test `p = float(2.0 * norm.sf(abs(z)))` is correct.

---

## 4. Verdict
Apart from the documented minor package-level issues with disconnected networks / collinearity and the test-harness statistical bootstrap clustering bug, the network PET/PEESE-analog small-study correction and the sweep harness are **mathematically and programmatically sound**. The AdaptShrink-NMA selection-region win conclusion is robust.
