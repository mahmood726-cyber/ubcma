# Independent Third-Vendor Witness Report: Lipids/LDL Transport Severity Result Verification

This report presents the independent third-vendor witness verification results of the third-domain (lipids/LDL-C reduction) publication-bias analysis.

---

## Part (a): Overview of the Lipids/LDL Replication
- **Analysis Script:** [aact_kappa_lipid.py](file:///F:/ubcma/transport_nma/aact_kappa_lipid.py)  
- **Output Data:** [aact_kappa_lipid.json](file:///F:/ubcma/transport_nma/aact_kappa_lipid.json)  
- **Related Report Document:** [REPORT_TRANSPORT_NMA.md](file:///F:/ubcma/transport_nma/REPORT_TRANSPORT_NMA.md)

### Verification Context
The registry-severity model posits that treatment efficacy inflation in published trials (compared to registered-only trials) tracks selection severity (measured by registry density $1-\lambda$).
- **The Team's Claim:** They assert that in the lipid domain (LDL change), the published-vs-registered effect inflation reproduces robustly at the trial level for the two adequately-powered classes (statin and ezetimibe). However, the severity-tracking correlation $\text{corr}(\kappa, 1-\lambda)$ is uninformative (not testable / insufficient classes) because lipid trials are largely *publication-saturated*, meaning very few trials remain unregistered-only (PCSK9 has only 3/6, and others have zero), leaving only statin and ezetimibe with adequate power ($\ge 8$ trials in both arms).
- **The Auditor's Goal:** Independently execute the script, verify the exact numbers from `aact_kappa_lipid.json` (marking them as `COMMITTED`), check if the gaps are robustly positive, verify the publication saturation caveat, and issue a final verdict of **CONFIRM** or **DIVERGE**.

---

## Part (b): Verification Findings & Detailed Numbers

The script `transport_nma/aact_kappa_lipid.py` was executed successfully on Windows. 

### 1. Percent-Change LDL Mean Difference Analysis (`pct_md`)
From the generated [aact_kappa_lipid.json](file:///F:/ubcma/transport_nma/aact_kappa_lipid.json), the exact class-specific metrics for the percent-change LDL MD gaps are:

- **Statin:**
  - $n_{\text{pub}}$ = `131` [COMMITTED]
  - $n_{\text{reg}}$ = `60` [COMMITTED]
  - $m_{\text{pub}}$ = `33.13709923664122` [COMMITTED]
  - $m_{\text{reg}}$ = `22.07131666666667` [COMMITTED]
  - $\kappa_{MD}$ (gap) = `0.501364859065554` (approx. `50.14%`) [COMMITTED]
  - $\lambda$ (posted ratio) = `0.2706645056726094` ($1-\lambda \approx 0.729$) [COMMITTED]
  - 95% CI (trial bootstrap) = `[0.22040746006126014, 0.8538675193040941]` [COMMITTED]
  - **Verdict:** Robustly positive (the 95% CI lower bound `+22.04%` is strictly greater than 0).

- **Ezetimibe:**
  - $n_{\text{pub}}$ = `111` [COMMITTED]
  - $n_{\text{reg}}$ = `52` [COMMITTED]
  - $m_{\text{pub}}$ = `29.61410810810811` [COMMITTED]
  - $m_{\text{reg}}$ = `20.45221153846154` [COMMITTED]
  - $\kappa_{MD}$ (gap) = `0.4479660574807327` (approx. `44.80%`) [COMMITTED]
  - $\lambda$ (posted ratio) = `0.3813559322033898` ($1-\lambda \approx 0.619$) [COMMITTED]
  - 95% CI (trial bootstrap) = `[0.194532334760601, 0.7508837711111518]` [COMMITTED]
  - **Verdict:** Robustly positive (the 95% CI lower bound `+19.45%` is strictly greater than 0).

- **Summary Statistics:**
  - Number of classes with $\ge 8$ trials in both arms: `2` (Statin, Ezetimibe)
  - Correlation $\text{corr}(\kappa, 1-\lambda)$ = `null` [COMMITTED]
  - Script Verdict = `insufficient` [COMMITTED]

---

### 2. Scale-Invariant Significance Gap Analysis (`z`)
For completeness, the scale-invariant significance gap ($z = |MD|/SE$) metrics from the JSON file are:

- **Statin:**
  - $n_{\text{pub}}$ = `132` [COMMITTED]
  - $n_{\text{reg}}$ = `68` [COMMITTED]
  - $m_{\text{pub}}$ = `9.503992618956586` [COMMITTED]
  - $m_{\text{reg}}$ = `4.270019467846031` [COMMITTED]
  - $\kappa_{z}$ (gap) = `1.2257492478718794` (approx. `122.57%` gap in significance) [COMMITTED]
  - 95% CI (trial bootstrap) = `[0.8138672143183903, 1.7341789671924102]` [COMMITTED]
  - **Verdict:** Robustly positive.

- **Ezetimibe:**
  - $n_{\text{pub}}$ = `139` [COMMITTED]
  - $n_{\text{reg}}$ = `54` [COMMITTED]
  - $m_{\text{pub}}$ = `8.051018523746531` [COMMITTED]
  - $m_{\text{reg}}$ = `3.4520847715279763` [COMMITTED]
  - $\kappa_{z}$ (gap) = `1.3322192404281417` (approx. `133.22%` gap in significance) [COMMITTED]
  - 95% CI (trial bootstrap) = `[0.8764948311781215, 1.8986643601809852]` [COMMITTED]
  - **Verdict:** Robustly positive.

- **Summary Statistics:**
  - Number of classes with $\ge 8$ trials in both arms: `2` (Statin, Ezetimibe)
  - Correlation $\text{corr}(\kappa, 1-\lambda)$ = `null` [COMMITTED]
  - Script Verdict = `insufficient` [COMMITTED]

---

## Part (c): Verification Verdict & Confirmation

> [!NOTE]
> **VERDICT: CONFIRM (Statin/Ezetimibe gaps robustly positive; correlation uninformative due to publication saturation, honestly disclosed)**
> 
> The independent third-vendor witness audit confirms the findings:
> 
> 1. **Gaps are Robustly Positive:** On the percent-change LDL MD scale, the published-vs-registered inflation gaps are **50.14%** (95% CI: `[+22.04%, +85.39%]`) for statin and **44.80%** (95% CI: `[+19.45%, +75.09%]`) for ezetimibe. Both of these trial-level bootstrap intervals exclude zero, indicating that published trials report significantly larger treatment effects than unregistered-only trials.
> 
> 2. **Correlation is Uninformative due to Publication Saturation:** The lipid-lowering domain is highly publication-saturated. Out of 6 classes, 3 (fibrate, bile_acid, niacin) have exactly 0 registered-only trials with LDL outcomes, and PCSK9 has only 3 registered-only trials (well below the power limit of $\ge 8$ trials). Only statin and ezetimibe have enough trials to calculate stable gaps. Since only 2 classes are adequately powered, a class-level correlation cannot be computed (it returns `null` with verdict `insufficient`). This represents a real data limitation resulting from publication saturation, which the team has honestly disclosed in [REPORT_TRANSPORT_NMA.md](file:///F:/ubcma/transport_nma/REPORT_TRANSPORT_NMA.md#L236-L259).
