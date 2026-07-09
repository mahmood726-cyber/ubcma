# Independent Third-Vendor Witness Report: DTA Parity Verification

This document verifies the diagnostic test accuracy (DTA) bivariate model implementation against R's `mada::reitsma` reference package.

## 1. DTA Test Identification
* **Current Branch:** `methods-borrowing`
* **Test files found and executed:**
  * [validate_python.py](file:///F:/ubcma/truth-recovery-dta/validate_python.py)
* **Branch notes:**
  * `tests/test_dta.py` does not exist in the working directory of the `methods-borrowing` branch.
  * A compiled artifact `tests/__pycache__/test_dta.cpython-313-pytest-9.0.3.pyc` is present in the cache, suggesting that `tests/test_dta.py` exists on the alternative branch `methods-dta` (which is checked out in a separate worktree).

## 2. Test Execution & Results
Running the verification script [validate_python.py](file:///F:/ubcma/truth-recovery-dta/validate_python.py) directly with Python:
```
dataset        k               m1 py/R               m2 py/R              sens            spec  max|d|
AuditC        14  2.07626/2.07626  1.26245/1.26245  0.88857/0.88857 0.77945/0.77945  2.03e-08
smoking       51  2.44246/2.44246  2.40330/2.40330  0.92001/0.92001 0.91708/0.91708  2.52e-09
Dementia      33  1.31528/1.31528  2.04871/2.04871  0.78840/0.78840 0.88582/0.88582  9.02e-07
skin_tests    10  -1.05573/-1.05573  3.46994/3.46994  0.25813/0.25813 0.96982/0.96982  4.09e-09
SAQ           31  2.02965/2.02965  2.34549/2.34549  0.88388/0.88388 0.91258/0.91258  1.44e-09

worst abs disagreement vs mada::reitsma (ML): 9.02e-07
PASS (< 0.001)
```
* **Pass/Fail Counts:** **5/5 datasets passed** (0 failures).

## 3. Parity, Tolerance, and HSROC Validation
* **Asserted Parity Tolerance:**
  * The tolerance asserted in [validate_python.py](file:///F:/ubcma/truth-recovery-dta/validate_python.py#L43-L45) is `1e-3` (`tol = 1e-3`).
  * The actual maximum absolute disagreement observed is **$9.02 \times 10^{-7}$** (on the `Dementia` dataset), confirming the claimed ~9e-7 precision of the core estimator.
* **HSROC-vs-glmer Validation:**
  * **Not Present.** There is no HSROC-vs-glmer validation present in the codebase. (An unrelated one-stage binomial model vs `lme4::glmer` validation exists for dose-response meta-analysis under `doseresponse/`, but nothing for DTA/HSROC).

## 4. Formula Verification
* **Diagnostic Odds Ratio (DOR):**
  * We confirm that $\text{ln}(DOR) = \mu_1 + \mu_2$ (NOT $\mu_1 - \mu_2$).
  * In [src/ubcma/dta.py](file:///F:/ubcma/src/ubcma/dta.py#L484-L487), the SROC correction correctly models the summary Diagnostic Odds Ratio as:
    ```python
    lnDOR = M1 + M2
    ```
  * **Derivation:**
    $$\text{DOR} = \frac{\text{odds}(Se)}{\text{odds}(1 - Sp)} = \frac{Se / (1 - Se)}{(1 - Sp) / Sp} = \frac{Se}{1 - Se} \cdot \frac{Sp}{1 - Sp}$$
    Taking the natural logarithm:
    $$\ln(\text{DOR}) = \ln\left(\frac{Se}{1-Se}\right) + \ln\left(\frac{Sp}{1-Sp}\right) = \text{logit}(Se) + \text{logit}(Sp) = \mu_1 + \mu_2$$
    This is mathematically correct. A formula of $\mu_1 - \mu_2$ would represent the log odds-ratio of sensitivity to specificity, which is incorrect.
* **logit(Se) / logit(Sp) Transformations:**
  * In [src/ubcma/dta.py](file:///F:/ubcma/src/ubcma/dta.py#L130-L133), the logit transformations are:
    ```python
    se = tp / (tp + fn)
    sp = tn / (tn + fp)
    y1 = np.log(se / (1.0 - se))
    y2 = np.log(sp / (1.0 - sp))
    ```
    This correctly maps to $\text{logit}(Se)$ and $\text{logit}(Sp)$.
  * Back-transformation in [src/ubcma/dta.py](file:///F:/ubcma/src/ubcma/dta.py#L255-L256):
    ```python
    se_sum = float(1.0 / (1.0 + np.exp(-M[0])))
    sp_sum = float(1.0 / (1.0 + np.exp(-M[1])))
    ```
    This correctly computes the logistic sigmoid ($\text{logit}^{-1}$).

## Verdict
**CONFIRM** (All 5 datasets pass validation, with worst-case disagreement of 9.02e-07 confirming the ~9e-7 parity claim, and formula/transforms verified as correct).
