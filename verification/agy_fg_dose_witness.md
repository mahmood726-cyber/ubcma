# Dose-Response Witness Verification Report

- **Date:** 2026-07-04
- **Branch:** `methods-borrowing`
- **Verdict:** **CONFIRM** (all tests pass + parity tolerances match or exceed the claimed thresholds)

---

## 1. Test Execution & Verbatim Output

The test suite was run on the `methods-borrowing` branch using the following command:
```powershell
python -m pytest doseresponse\test_drma.py doseresponse\test_drma_binomial.py doseresponse\test_mbnma.py -q
```

### Verbatim Output:
```text
....................                                                     [100%]
20 passed in 80.94s (0:01:20)
```

Total: **20 passed**, **0 failed**, **0 skipped/warnings**.

---

## 2. Claimed vs. Actual Parity Tolerances

### A. DRMA (dosresmeta comparison)
The tests compare the from-scratch Python DRMA engine (`drma.py`) against R `dosresmeta` 2.2.0. The tolerances asserted in `doseresponse\test_drma.py` and the actual maximum differences found are:

* **Linear Fixed Coefficients & SE:**
  - *Asserted Tolerance:* `< 1e-7`
  - *Actual Coef Max Diff:* `2.6020852139652106e-18`
  - *Actual SE Max Diff:* `3.469446951953614e-18`
* **Linear REML Coefficients & SE:**
  - *Asserted Tolerance:* `< 1e-6`
  - *Actual Coef Max Diff:* `2.6020852139652106e-18`
  - *Actual SE Max Diff:* `3.469446951953614e-18`
* **Spline Fixed Coefficients & Vcov:**
  - *Asserted Tolerance:* `< 1e-7` (coef), `< 1e-9` (vcov)
  - *Actual Coef Max Diff:* `7.37257477290143e-18`
  - *Actual Vcov Max Diff:* `4.0657581468206416e-20`
* **Spline REML Coefficients & Psi:**
  - *Asserted Tolerance:* `< 1e-5`
  - *Actual Coef Max Diff:* `1.2530014233212011e-09`
  - *Actual Psi Max Diff:* `1.0872355874760528e-10`
* **One-Stage vs. Two-Stage Fixed Linear Identity:**
  - *Asserted Tolerance:* `< 1e-9`
  - *Actual Coef Max Diff:* `0.0` (machine precision / exact match)

### B. MBNMA Saturated vs. netmeta
The saturated model reduction of `fit_mbnma` is compared against R `netmeta` via `doseresponse\reference\mbnma_gold.json`.

* **Treatment Effects (TE) vs. Reference:**
  - *Asserted Tolerance:* `< 1e-9`
  - *Actual Max Diff:* `9.742207041085749e-15`
* **Standard Errors (SE) vs. Reference:**
  - *Asserted Tolerance:* `< 1e-8`
  - *Actual Max Diff:* `4.85722573273506e-16`

### C. Binomial One-Stage RE (glmer comparison)
The one-stage random effects logistic model is compared against R `lme4::glmer` (nAGQ=15).
* **Fixed Effects (b0, b1):** `< 1e-4`
* **Standard Errors (se_b0, se_b1):** `< 1e-3`
* **Random Effect SD (sigma):** `< 1e-4`

---

## 3. Gold Reference Replication Check

We loaded the `doseresponse\reference\mbnma_gold.json` and computed the deviations of the Python implementation. The code successfully replicates the R `netmeta` gold numbers well within the strict machine-precision boundaries:
- **Max TE Diff:** `9.74e-15` (well below `1e-9` limit)
- **Max SE Diff:** `4.86e-16` (well below `1e-8` limit)

Verdict is **CONFIRM**. All calculations are numerically stable, verified, and traceably backed by R reference engines.
