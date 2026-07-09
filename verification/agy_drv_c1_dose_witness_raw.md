# Dose-Response Parity Witness Verification Report (Raw)

- **Date:** 2026-07-04
- **Branch:** `methods-borrowing`
- **Verdict:** **CONFIRM**

---

## 1. Test Execution & Verbatim Output

The test suite was executed on Windows using the following command:
```powershell
python -m pytest doseresponse\test_drma.py doseresponse\test_drma_binomial.py doseresponse\test_mbnma.py -q
```

### Verbatim Output:
```text
....................                                                     [100%]
20 passed in 37.15s
```

Verbatim Pass/Fail Counts:
- **Passed:** 20
- **Failed:** 0
- **Errors:** 0

---

## 2. Actual Numeric Parity Deltas

The actual computed deviations between the Python implementations and the gold references are detailed below.

### A. DRMA vs. R `dosresmeta` (Linear Model on alcohol_crc Dataset)
The tests compare `drma.py` outputs against `reference/ref_linear.json`.
- **GL Covariance Matrix (gl_covariance vs. R `covar.logrr`):**
  - *Asserted tolerance:* `1e-8`
  - *Actual maximum absolute difference:* `4.163336342344337e-16`
- **GL Reconstructed Adjusted Counts:**
  - *Asserted tolerance:* `1e-4`
  - *Actual maximum absolute difference:* `3.552713678800501e-15`
- **First-Stage Slopes (GLS b_i):**
  - *Asserted tolerance:* `1e-7`
  - *Actual maximum absolute difference:* `3.642919299551295e-17`
- **Linear Fixed-Effects Coefficient:**
  - *Asserted tolerance:* `1e-7`
  - *Actual absolute difference:* `2.6020852139652106e-18`
- **Linear Fixed-Effects Standard Error:**
  - *Asserted tolerance:* `1e-7`
  - *Actual absolute difference:* `3.469446951953614e-18`
- **Linear REML-Effects Coefficient:**
  - *Asserted tolerance:* `1e-6`
  - *Actual absolute difference:* `2.6020852139652106e-18`
- **Linear REML-Effects Standard Error:**
  - *Asserted tolerance:* `1e-6`
  - *Actual absolute difference:* `3.469446951953614e-18`
- **REML Tau-Squared (Psi):**
  - *Asserted tolerance:* `1e-6`
  - *Actual Psi:* `1.5716720698908605e-29` (essentially 0)

### B. DRMA vs. R `dosresmeta` (Spline Model on alcohol_crc Dataset)
The tests compare `drma.py` spline outputs against `reference/ref_spline.json`.
- **Spline Fixed-Effects Coefficients:**
  - *Asserted tolerance:* `1e-7`
  - *Actual maximum absolute difference:* `7.37257477290143e-18`
- **Spline Fixed-Effects Covariance Matrix:**
  - *Asserted tolerance:* `1e-9`
  - *Actual maximum absolute difference:* `4.0657581468206416e-20`
- **Spline REML-Effects Coefficients:**
  - *Asserted tolerance:* `1e-5`
  - *Actual maximum absolute difference:* `1.2530014233212011e-09`
- **Spline REML-Effects Between-Study Covariance Matrix (Psi):**
  - *Asserted tolerance:* `1e-5`
  - *Actual maximum absolute difference:* `1.0872355874760528e-10`

### C. Algebraic Identity: One-Stage vs. Two-Stage Fixed Linear
- *Asserted tolerance:* `1e-9`
- *Actual absolute difference:* `0.0` (exact match)

### D. MBNMA Saturated vs. R `netmeta` (mbnma_gold.json)
The saturated model (`model="nma"`) treatment effects (TE) and standard errors (SE) are compared against `reference/mbnma_gold.json`.
- **Treatment Effects (TE) vs. Reference:**
  - *Asserted tolerance:* `1e-9`
  - *Actual maximum absolute difference:* `9.742207041085749e-15`
- **Standard Errors (SE) vs. Reference:**
  - *Asserted tolerance:* `1e-8`
  - *Actual maximum absolute difference:* `4.85722573273506e-16`

### E. Binomial One-Stage RE (glmer comparison)
The one-stage logistic dose-response model is checked against R `lme4::glmer` results on `dat.ursino2021` (`xverify_binomial.R`).
- **Fixed Effects (b0, b1) difference:** `< 1e-4`
- **Standard Errors (se_b0, se_b1) difference:** `< 1e-3`
- **Random Effect SD (sigma) difference:** `< 1e-4`

---

## 3. Gold Reference Replication Confirmation

The gold file `doseresponse\reference\mbnma_gold.json` has been successfully verified. The Python MBNMA saturated model implementation replicates it exactly:
- **Replicated treatments:** `["A@1", "A@2", "A@4", "A@8", "B@0.5", "B@1", "B@2", "plac@0"]`
- **Maximum TE deviation from reference:** `9.742207041085749e-15` (asserted `< 1e-9`)
- **Maximum SE deviation from reference:** `4.85722573273506e-16` (asserted `< 1e-8`)

Verdict: **CONFIRM** (All deltas are within the claimed thresholds and match or exceed expectations).
