# Independent Third-Vendor Witness Report: DRMA Spline Parity & Stage Identity

**Task Identification:** Verification of from-scratch Dose-Response Meta-Analysis (DRMA) Engine against R `dosresmeta` 2.2.0 on the `methods-borrowing` branch.  
**Files under Review:**
- [doseresponse/test_drma.py](file:///F:/ubcma/doseresponse/test_drma.py) (Parity tests and assertions)
- [doseresponse/drma.py](file:///F:/ubcma/doseresponse/drma.py) (The from-scratch DRMA engine)
- [doseresponse/reference/ref_spline.json](file:///F:/ubcma/doseresponse/reference/ref_spline.json) (Spline reference data from R `dosresmeta`)
- [doseresponse/reference/ref_linear.json](file:///F:/ubcma/doseresponse/reference/ref_linear.json) (Linear reference data from R `dosresmeta`)

**Witness Date:** 2026-07-04  
**OS Platform:** Windows  
**Verdict:** **CONFIRM** (The from-scratch DRMA spline REML fit matches R `dosresmeta` to high precision: coefficient max difference is $\approx 1.25 \times 10^{-9}$ and random-effects variance matrix $\Psi$ max difference is $\approx 1.09 \times 10^{-10}$—both well within the asserted tolerances. Additionally, the one-stage vs. two-stage fixed linear algebraic identity holds with exactly $0.0$ max difference).

---

## 1. Executive Summary & Core Conclusion

We have independently executed the test suites and computed the exact numerical discrepancies for the **Dose-Response Meta-Analysis (DRMA) spline and identity claims**.

The primary claims under verification are:
1. **Spline REML Parity (vs R `dosresmeta`):** The spline REML coefficients and variance-covariance matrix of random effects ($\Psi$) from our Python-based implementation match those produced by R's `dosresmeta` package (v2.2.0) on the canonical alcohol-CRC JSS dataset to high numerical precision, with coefficients differing by $\approx 1.25 \times 10^{-9}$ and $\Psi$ by $\approx 1.09 \times 10^{-10}$.
2. **One-Stage vs. Two-Stage Fixed Linear Identity:** The algebraic identity between the pooled one-stage GLS model and the fixed-effects two-stage linear model holds exactly, with a maximum difference of exactly $0.0$.

All tests in [doseresponse/test_drma.py](file:///F:/ubcma/doseresponse/test_drma.py) passed successfully on the `methods-borrowing` branch of `F:\ubcma`.

---

## 2. Spline REML Coefficient and Psi Parity (vs R `dosresmeta`)

The restricted maximum likelihood (REML) spline model is fitted to the alcohol-CRC dataset using three knots ($0$, $14.25$, $57.18$). We compared the parameters computed by our Python engine against the gold-standard reference values stored in `ref_spline.json`.

### A. Spline REML Coefficients ($\beta$)
* **Python Got**:
  ```python
  [-0.0013658921958630966, 0.02097456992424861]
  ```
* **R Reference (`ref_spline.json`)**:
  ```json
  [-0.00136589344886452, 0.0209745709202553]
  ```
* **Observed Max Difference:** `1.2530014233212011e-09` (matches claim $\approx 1.25 \times 10^{-9}$)
* **Asserted Tolerance in Test:** `atol=1e-5, rtol=0` (Passes)

### B. Spline REML Between-Study Variance-Covariance Matrix ($\Psi$)
* **Python Got**:
  ```python
  [[3.693261703102134e-05, -8.798235608608976e-05],
   [-8.798235608608976e-05, 0.00020959508436560535]]
  ```
* **R Reference (`ref_spline.json`)**:
  ```json
  [[3.69327042204903e-05, -8.79824648096485e-05],
   [-8.79824648096485e-05, 0.000209595107571204]]
  ```
* **Observed Max Difference:** `1.0872355874760528e-10` (matches claim $\approx 1.09 \times 10^{-10}$)
* **Asserted Tolerance in Test:** `atol=1e-5, rtol=0` (Passes)

---

## 3. One-Stage vs. Two-Stage Fixed Linear Identity

The algebraic equivalence of the one-stage pooled GLS and two-stage fixed-effects linear models dictates that their coefficients must be identical. We evaluated the coefficient outputs for the linear models on the alcohol-CRC dataset:

* **Python One-Stage Coef:** `[0.006437537802609003]`
* **Python Two-Stage Fixed Linear Coef:** `[0.006437537802609003]`
* **Observed Max Difference:** `0.0` (exactly identical, matches claim `0.0 exact`)
* **Asserted Tolerance in Test:** `< 1e-9` (Passes)

---

## 4. Test Suite Run & Verbatim Logs

### A. Pytest Output
We executed `python -m pytest doseresponse/test_drma.py -vv` from the workspace root. All 9 tests passed.

```
============================= test session starts =============================
platform win32 -- Python 3.13.13, pytest-9.0.3, pluggy-1.6.0 -- ~\AppData\Local\Programs\Python\Python313\python.exe
cachedir: .pytest_cache
hypothesis profile 'default'
rootdir: F:\ubcma
configfile: pyproject.toml
plugins: anyio-4.13.0, hypothesis-6.155.6, base-url-2.1.0, playwright-0.8.0, timeout-2.4.0
collecting ... collected 9 items

doseresponse/test_drma.py::test_gl_covariance_study1 PASSED              [ 11%]
doseresponse/test_drma.py::test_gl_adjusted_counts_study1 PASSED         [ 22%]
doseresponse/test_drma.py::test_first_stage_slopes PASSED                [ 33%]
doseresponse/test_drma.py::test_linear_fixed PASSED                      [ 44%]
doseresponse/test_drma.py::test_linear_reml PASSED                       [ 55%]
doseresponse/test_drma.py::test_rcs_basis_value PASSED                   [ 66%]
doseresponse/test_drma.py::test_spline_fixed PASSED                      [ 77%]
doseresponse/test_drma.py::test_spline_reml PASSED                       [ 88%]
doseresponse/test_drma.py::test_one_stage_vs_two_stage_fixed_linear PASSED [100%]

============================== 9 passed in 3.01s ==============================
```

### B. Summary of All Asserted Tolerances and Observed Max-Differences Verbatim

Below is a detailed breakdown of all assertions present in [doseresponse/test_drma.py](file:///F:/ubcma/doseresponse/test_drma.py):

| Test Name | Parameter Checked | Asserted Tolerance | Observed Max Difference | Status |
| :--- | :--- | :--- | :--- | :--- |
| `test_gl_covariance_study1` | Covariance matrix $S$ vs. $S_{\text{ref}}$ | `atol=1e-8, rtol=0` | `4.163336342344337e-16` | PASSED |
| `test_gl_adjusted_counts_study1` | Reconstructed counts $A$ vs. $A_{\text{ref}}$ | `atol=1e-4, rtol=0` | `3.552713678800501e-15` | PASSED |
| `test_first_stage_slopes` | First-stage slopes $b_i$ vs. $b_{i,\text{ref}}$ | `atol=1e-7, rtol=0` | `3.642919299551295e-17` | PASSED |
| `test_linear_fixed` | Linear fixed-effects `coef` and `se` | `< 1e-7` | `2.6020852139652106e-18` (coef)<br>`3.469446951953614e-18` (se) | PASSED |
| `test_linear_reml` | Linear REML `coef`, `se`, and `Psi` | `< 1e-6` | `2.6020852139652106e-18` (coef)<br>`3.469446951953614e-18` (se)<br>`1.5716720698908605e-29` (Psi value) | PASSED |
| `test_rcs_basis_value` | RCS basis evaluated at dose 25 | `atol=1e-8` | `0.0` | PASSED |
| `test_spline_fixed` | Spline fixed-effects `coef` and `vcov` | `atol=1e-7` (coef)<br>`atol=1e-9` (vcov) | `7.37257477290143e-18` (coef)<br>`4.0657581468206416e-20` (vcov) | PASSED |
| `test_spline_reml` | Spline REML `coef` and `Psi` | `atol=1e-5` (coef)<br>`atol=1e-5` (Psi) | `1.2530014233212011e-09` (coef)<br>`1.0872355874760528e-10` (Psi) | PASSED |
| `test_one_stage_vs_two_stage_fixed_linear` | Coefficient identity | `< 1e-9` | `0.0` | PASSED |

---

## 5. Hardcode-Disclosure Table

Per the verification contract, we list the source and nature of all quantitative fields reported in this review:

| Quantitative Field | Value / Range | Type | Source |
| :--- | :--- | :---: | :--- |
| `test_gl_covariance_study1` diff | `4.163336342344337e-16` | Dynamic | Live check via Python / `drma.py` |
| `test_gl_adjusted_counts_study1` diff | `3.552713678800501e-15` | Dynamic | Live check via Python / `drma.py` |
| `test_first_stage_slopes` diff | `3.642919299551295e-17` | Dynamic | Live check via Python / `drma.py` |
| `test_linear_fixed` coef/se diff | `2.60e-18` / `3.47e-18` | Dynamic | Live check via Python / `drma.py` |
| `test_linear_reml` coef/se/Psi | `2.60e-18` / `3.47e-18` / `1.57e-29` | Dynamic | Live check via Python / `drma.py` |
| `test_rcs_basis_value` diff | `0.0` | Dynamic | Live check via Python / `drma.py` |
| `test_spline_fixed` coef/vcov diff | `7.37e-18` / `4.07e-20` | Dynamic | Live check via Python / `drma.py` |
| `test_spline_reml` coef/Psi diff | `1.2530014233212011e-09` / `1.0872355874760528e-10` | Dynamic | Live check via Python / `drma.py` |
| `test_one_stage_vs_two_stage_fixed_linear` diff | `0.0` | Dynamic | Live check via Python / `drma.py` |
| Reference spline values | `ref_spline.json` fields | Static | Loaded from [ref_spline.json](file:///F:/ubcma/doseresponse/reference/ref_spline.json) |
| Reference linear values | `ref_linear.json` fields | Static | Loaded from [ref_linear.json](file:///F:/ubcma/doseresponse/reference/ref_linear.json) |

---

## 6. Verdict

We **CONFIRM** that:
- The spline REML coefficients and variance-covariance matrix of random effects ($\Psi$) from our Python-based implementation match those produced by R's `dosresmeta` package (v2.2.0) on the canonical alcohol-CRC JSS dataset to within $\approx 1.25 \times 10^{-9}$ and $\approx 1.09 \times 10^{-10}$ respectively.
- The one-stage vs. two-stage fixed linear algebraic identity holds with exactly `0.0` max difference.
- All 9 tests in [doseresponse/test_drma.py](file:///F:/ubcma/doseresponse/test_drma.py) pass on the `methods-borrowing` branch of `F:\ubcma`.
