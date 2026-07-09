# Independent Third-Vendor Witness Report: Multi-Domain Generalization of Transport-NMA

This report presents the third-vendor verification results for the transport-NMA multi-domain generalization claims on the antidepressant (depression) network under the branch `methods-borrowing`.

---

## Part (a): Scale-Invariant Z-Gap Correlation (Antidepressants)
**Script run:** `python transport_nma\aact_kappa_depression_std.py`

### Findings & Numbers
- **z-analyses kept:** 262
- **logOR-analyses kept:** 226
- **Scale-invariant z-gap correlation $\text{corr}(\kappa_z, 1-\lambda)$:** `+0.641` (POSITIVE)
- **Slope:** `+1.124`
- **Class-specific details (Z-analysis):**
  - **SSRI:** $1-\lambda = 0.679$, $n_{\text{pub}} = 30$, $n_{\text{reg}} = 32$, $\kappa_z = 0.690$, $95\%\text{ CI} = [+0.22, +1.28]$ (significant)
  - **SNRI:** $1-\lambda = 0.565$, $n_{\text{pub}} = 130$, $n_{\text{reg}} = 12$, $\kappa_z = -0.331$, $95\%\text{ CI} = [-0.55, +0.27]$
  - **atypical:** $1-\lambda = 0.619$, $n_{\text{pub}} = 118$, $n_{\text{reg}} = 27$, $\kappa_z = 1.177$, $95\%\text{ CI} = [+0.72, +1.86]$ (significant)

### Verification Verdict
**CONFIRM**  
The observed scale-invariant z-gap correlation is **`+0.641`**, which is positive and aligns perfectly with the claim of `~+0.64`.

### Raw-Scale (HAM-D) Version Failure Analysis
A raw-scale (HAM-D) version is expected to fail because of a **scale version artefact**. HAM-D exists in multiple scale lengths (e.g., 17-item, 21-item, and 24-item HAM-D versions) and is mixed with MADRS. These scales have different maximum values and variance ranges, making raw mean differences across trials heterogeneous and mathematically incomparable without standardization. Standardized scale-invariant measures (such as the signal-to-noise ratio $z = |MD|/SE$) are necessary for valid comparisons.

---

## Part (b): Second Real Network Truth-Gate Validation (Linde 2015)
**Script run:** `python transport_nma\linde_nma.py`  
**JSON file read:** `transport_nma\linde_nma_result.json`

### Verification Questions & Findings
1. **Does the registry-lambda correction beat internal funnel models?**
   **Yes.** Across all bias levels ($B=0.00, 0.15, 0.30$), the registry-lambda correction methods (`registry_extdiab0.158`, `registry_oracle`, and `registry_fix0.5`) achieve **WINS** or **ties** against unadjusted NMA, whereas the internal funnel models (PET and TF) achieve **HARMS** (increasing the mean credible interval width $MCIW_0$).
2. **Is PET catastrophic?**
   **Yes.** PET performs catastrophically. It results in a massive increase in estimation error ($MCIW_0$ is $\sim 1.86$--$1.87$ compared to the baseline unadjusted $MCIW_0$ of $\sim 0.64$--$0.69$, corresponding to a $dMCIW_0$ of $+1.17$ to $+1.22$ and a clear **HARMS** verdict).
3. **Does the diabetes-derived kappa transfer?**
   **Yes.** The model `registry_extdiab0.158` (which applies the frozen diabetes-derived $\kappa_{\text{pooled}} = 0.158$ to the depression network) successfully transfers. It achieves a **WINS** verdict at all bias levels:
   - **$B=0.00$:** $dMCIW_0 = -0.0418$, $95\%\text{ CI} = [-0.0656, -0.0230]$ (**WINS**)
   - **$B=0.15$:** $dMCIW_0 = -0.0652$, $95\%\text{ CI} = [-0.0846, -0.0461]$ (**WINS**)
   - **$B=0.30$:** $dMCIW_0 = -0.0835$, $95\%\text{ CI} = [-0.1103, -0.0667]$ (**WINS**)

### Verification Verdict
**CONFIRM**  
The registry-lambda correction consistently outperforms internal funnel models, PET is catastrophic, and the diabetes-derived $\kappa$ transfers successfully.

---

### Exact Simulation Sweep Output (from `linde_nma_result.json`)

| Bias Level ($B$) | Method | $MCIW_0$ | $dMCIW_0$ | $95\%$ CI | Verdict |
|---|---|---|---|---|---|
| **$B=0.00$** | unadjusted | 0.6463 | +0.0000 | `[+0.0000, +0.0000]` | - |
| | registry_oracle | 0.6463 | +0.0000 | `[+0.0000, +0.0000]` | tie |
| | registry_extdiab0.158 | 0.6044 | -0.0418 | `[-0.0656, -0.0230]` | **WINS** |
| | registry_fix0.5 | 0.6218 | -0.0245 | `[-0.0589, +0.0028]` | tie |
| | PET | 1.8705 | +1.2242 | `[+1.0866, +1.3379]` | **HARMS** |
| | TF | 0.6903 | +0.0440 | `[+0.0177, +0.0586]` | **HARMS** |
| | HC | 0.6463 | +0.0000 | `[+0.0000, +0.0000]` | tie |
|---|---|---|---|---|---|
| **$B=0.15$** | unadjusted | 0.6677 | +0.0000 | `[+0.0000, +0.0000]` | - |
| | registry_oracle | 0.6060 | -0.0617 | `[-0.0827, -0.0437]` | **WINS** |
| | registry_extdiab0.158 | 0.6025 | -0.0652 | `[-0.0846, -0.0461]` | **WINS** |
| | registry_fix0.5 | 0.5796 | -0.0880 | `[-0.1141, -0.0541]` | **WINS** |
| | PET | 1.8625 | +1.1948 | `[+1.0760, +1.3130]` | **HARMS** |
| | TF | 0.6914 | +0.0238 | `[+0.0131, +0.0458]` | **HARMS** |
| | HC | 0.6677 | +0.0000 | `[+0.0000, +0.0000]` | tie |
|---|---|---|---|---|---|
| **$B=0.30$** | unadjusted | 0.6915 | +0.0000 | `[+0.0000, +0.0000]` | - |
| | registry_oracle | 0.5588 | -0.1327 | `[-0.1644, -0.1103]` | **WINS** |
| | registry_extdiab0.158 | 0.6080 | -0.0835 | `[-0.1103, -0.0667]` | **WINS** |
| | registry_fix0.5 | 0.5452 | -0.1463 | `[-0.1842, -0.1151]` | **WINS** |
| | PET | 1.8651 | +1.1736 | `[+1.0657, +1.3044]` | **HARMS** |
| | TF | 0.7377 | +0.0462 | `[+0.0268, +0.0667]` | **HARMS** |
| | HC | 0.6915 | +0.0000 | `[-0.0069, +0.0047]` | tie |
