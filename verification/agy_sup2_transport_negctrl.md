# Independent Third-Vendor Witness Report: Negative Control (Honest-Negative Check) of Transport-NMA Registry-Severity Model

This report presents the third-vendor verification results of the fourth-domain external validation (antihypertensive SBP) to check if the registry severity correlation holds or fails in this domain, thereby validating the honest-negative claim.

---

## Part (a): Overview of the Fourth-Domain Validation
**Script run:** `python transport_nma/aact_kappa_bp.py`  
**JSON file read:** `transport_nma/aact_kappa_bp.json`  
**Underlying code:** [aact_kappa_bp.py](file:///F:/ubcma/transport_nma/aact_kappa_bp.py)  
**Report file:** [REPORT_TRANSPORT_NMA.md](file:///F:/ubcma/transport_nma/REPORT_TRANSPORT_NMA.md)

### Verification Context
The registry-severity model predicts that published trials show larger effects than registered-only trials, with the inflation gap growing as a function of the class-level selection severity (registry density $1-\lambda$).
- **Diabetes** (7 classes): Positive correlation $\text{corr}(\kappa, 1-\lambda) = +0.50$.
- **Antidepressants** (3 classes): Positive scale-invariant correlation $\text{corr}(\kappa_z, 1-\lambda) = +0.64$.
- **Lipids** (2 classes): Statin/ezetimibe gaps are robustly positive, but correlation is uninformative due to publication saturation.
- **Antihypertensive SBP** (Fourth domain): Tested as a negative control to establish whether the model's claims are domain-bounded.

---

## Part (b): Verification Findings & Numbers

### 1. Primary Endpoint Analysis: |MD| in mmHg
This analysis examines raw mean differences (MD) in mmHg for systolic blood pressure (SBP) change, filtering for trials on a continuous mmHg scale.
- **Total mmHg |MD| analyses kept:** 420

#### Class-Specific Details (MD)
| Class | Registry Density ($1-\lambda$) | $n_{\text{pub}}$ | $n_{\text{reg}}$ | Mean |MD| Pub ($m_{\text{pub}}$) | Mean |MD| Reg ($m_{\text{reg}}$) | Gap ($\kappa$) | 95% CI (trial bootstrap) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **ACEi** | 0.747 | 1 | 14 | 0.310 mmHg | 6.576 mmHg | -0.953 | - (Insufficient $n_{\text{pub}}$) |
| **ARB** | 0.758 | 172 | 218 | 8.106 mmHg | 9.289 mmHg | **-0.127** | `[-0.24, -0.00]` (Significant negative) |
| **CCB** | 0.744 | 34 | 78 | 13.016 mmHg | 11.091 mmHg | **+0.174** | `[-0.07, +0.48]` (Spans 0) |
| **beta_blocker** | 0.623 | 0 | 11 | - | 4.421 mmHg | - | - |
| **diuretic** | 0.711 | 72 | 43 | 10.971 mmHg | 15.035 mmHg | **-0.270** | `[-0.38, -0.14]` (Significant negative) |
| **alpha_blocker**| 0.857 | 0 | 0 | - | - | - | - |
| **central** | 0.828 | 0 | 0 | - | - | - | - |
| **renin_inhibitor**| 0.500 | 5 | 12 | 3.422 mmHg | 9.634 mmHg | -0.645 | - (Insufficient $n_{\text{pub}}$) |

#### MD Severity Correlation
- **Classes used (adequately powered $\min(n) \ge 8$):** 3 (ARB, CCB, diuretic)
- **Correlation $\text{corr}(\kappa, 1-\lambda)$:** `+0.523`
- **Bootstrap 95% CI:** `[-1.00, +1.00]`
- **Slope:** `-0.147`
- **Verdict:** `does NOT reproduce (per-class gaps mostly <=0)`

---

### 2. Robustness Endpoint Analysis: Scale-Invariant $z$-Gap
This analysis uses the scale-invariant standardized measure $z = |MD|/SE$ to control for potential scale heterogeneity.
- **Total z-analyses kept:** 424

#### Class-Specific Details (Z)
| Class | Registry Density ($1-\lambda$) | $n_{\text{pub}}$ | $n_{\text{reg}}$ | Mean $z$ Pub ($m_{\text{pub}}$) | Mean $z$ Reg ($m_{\text{reg}}$) | Gap ($\kappa_z$) | 95% CI (trial bootstrap) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **ACEi** | 0.747 | 0 | 14 | - | 3.912 | - | - |
| **ARB** | 0.758 | 170 | 216 | 7.511 | 6.418 | **+0.170** | `[-0.06, +0.45]` (Spans 0) |
| **CCB** | 0.744 | 32 | 85 | 16.530 | 10.460 | **+0.580** | `[+0.19, +1.15]*` (Significant positive) |
| **beta_blocker** | 0.623 | 1 | 11 | 0.302 | 1.569 | -0.807 | - |
| **diuretic** | 0.711 | 70 | 43 | 11.778 | 10.987 | **+0.072** | `[-0.17, +0.38]` (Spans 0) |
| **alpha_blocker**| 0.857 | 0 | 0 | - | - | - | - |
| **central** | 0.828 | 0 | 0 | - | - | - | - |
| **renin_inhibitor**| 0.500 | 4 | 12 | 2.080 | 6.672 | -0.688 | - |

#### Z Severity Correlation
- **Classes used (adequately powered $\min(n) \ge 8$):** 3 (ARB, CCB, diuretic)
- **Correlation $\text{corr}(\kappa_z, 1-\lambda)$:** `+0.402`
- **Bootstrap 95% CI:** `[-1.00, +1.00]`
- **Slope:** `+0.277`
- **Verdict:** `UNINFORMATIVE (corr CI spans 0; too few classes)`

---

## Part (c): Verification Verdict & Confirmation

> [!NOTE]
> **CONFIRM (Honest Negative Reproduces)**
>
> The third-vendor audit confirms that the registered-vs-published effect inflation **fails to hold** in the antihypertensive SBP domain:
> 1. **Per-Class Gaps are Mostly Non-Positive:** For the primary continuous mmHg measure, the gaps for the two largest classes are significantly negative (ARB: $\kappa = -0.127$, $95\%\text{ CI } [-0.24, -0.00]$; diuretic: $\kappa = -0.270$, $95\%\text{ CI } [-0.38, -0.14]$). This means that published trials in these classes actually showed *smaller* absolute treatment effects than registered-only trials, directly contradicting the positive publication bias/selection inflation model. Only CCB showed a non-significant positive gap ($\kappa = +0.174$, $95\%\text{ CI } [-0.07, +0.48]$).
> 2. **Correlation is Uninformative:** Although the correlation coefficient is descriptively positive ($+0.523$ for MD, $+0.402$ for Z), it is calculated over only 3 points (ARB, CCB, diuretic) whose registry densities ($1-\lambda$) are extremely compressed/near-tied (ranging narrowly from $0.711$ to $0.758$). The bootstrap confidence interval spans the entire mathematical limit `[-1.00, +1.00]`.
>
> Therefore, this domain represents a genuine **honest negative** rather than a hidden win. The validation of the registry-severity relationship is domain-dependent and bounded, which reproduces the team's documented negative control result.
