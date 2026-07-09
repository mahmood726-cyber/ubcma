# NMA Engine Independent Third-Vendor Correctness Review Report

This report documents real correctness defects verified from first principles in the NMA engine of `F:\ubcma` (branch `methods-borrowing`).

## Methodology
- Evaluation of aggregate weight/precision matrix assembly and its (pseudo)inverse.
- Verification of multi-arm shared-control covariance formulation.
- Examination of consistency / design-by-treatment decomposition.
- Review of node-splitting, SUCRA computation, and degenerate network guards.
- Analysis of singular-matrix/NaN paths and fixed vs random effects labelling.

---

## Findings

### Finding 1: Disconnected Network standard error artifact (No disconnected-network guard)
- **File:Line**: [nma/nma_core.py:274](file:///F:/ubcma/nma/nma_core.py#L274) and [nma/nma_core.py:188](file:///F:/ubcma/nma/nma_core.py#L188) (in `fit_nma` / `_league`)
- **Severity**: P0
- **Concrete Failure**: The NMA engine has no guard against disconnected network structures. When the network is disconnected (e.g. contains two or more independent connected components of treatments), `np.linalg.pinv(L)` computes a finite pseudoinverse for the Laplacian. The `_league` function then calculates finite standard errors (`seTE`) and treatment differences (`TE`) between treatments in disconnected components, despite them sharing no common studies or paths. The true standard error between disconnected treatments should be infinite (or undefined).
- **Breaks netmeta-parity**: Yes. R's `netmeta` detects disconnected networks and splits them or returns NA/error. The Python engine erroneously reports finite numbers (e.g. `seTE = 0.35` for completely disconnected arms).

### Finding 2: Cochran's Q Degrees of Freedom (df_Q) Underestimation on Disconnected Networks
- **File:Line**: [nma/nma_core.py:258](file:///F:/ubcma/nma/nma_core.py#L258) and [nma/inconsistency_nma.py:68](file:///F:/ubcma/nma/inconsistency_nma.py#L68)
- **Severity**: P1
- **Concrete Failure**: The degrees of freedom for the network Q statistic is computed as `df_Q = max(indep - (n - 1), 0)`. If a network contains $C$ connected components, the number of estimated parameters is $n - C$ rather than $n - 1$. The true degrees of freedom must be `indep - (n - C)`. The current formula underestimates the degrees of freedom by $C - 1$ for disconnected networks. This underestimation propagates to overestimate `tau2` and `I2`.
- **Breaks netmeta-parity**: Yes. Parity will fail for any disconnected network since R's `netmeta` computes degrees of freedom per component or handles the components correctly, whereas this engine loses degrees of freedom.

### Finding 3: Point-Estimate/Potential Vector Inconsistency in Gated Small-Study Correction
- **File:Line**: [nma/adaptshrink_nma.py:238-243](file:///F:/ubcma/nma/adaptshrink_nma.py#L238-L243)
- **Severity**: P2
- **Concrete Failure**: In `adaptshrink_nma_auto`, if the small-study asymmetry gate `b_gate` fires, `TE` and `seTE` are updated with the PET/PEESE-adjusted values from `fitB`. However, `fit.theta` (potentials) and `fit.Lplus` (covariance matrix) are kept as the unadjusted `fitA.theta` and `fitA.Lplus`. This leads to a representation inconsistency inside the returned `NMAFit` object: `fit.TE` and `fit.seTE` are PEESE-adjusted, but `fit.theta` and `fit.Lplus` are not.
- **Breaks netmeta-parity**: No (internal path / representation inconsistency).

### Finding 4: Unconstrained Least-Squares Arm-Variance Reconstruction (Potential Negative Variances)
- **File:Line**: [nma/nma_core.py:115](file:///F:/ubcma/nma/nma_core.py#L115)
- **Severity**: P2
- **Concrete Failure**: In `_arm_variances`, the system $v = |A| \sigma^2$ is solved via unconstrained least-squares `np.linalg.lstsq`. For underdetermined or noisy systems, this can yield negative values for some elements of `sig2`. When `sig2` is negative, the resulting block covariance `V` may not be positive semi-definite (PSD), which can cause incorrect/unstable pseudoinverse weights.
- **Breaks netmeta-parity**: No (internal path, though could cause instability for noisy/underdetermined multi-arm blocks).

---

parity claims safe? no
