# Independent Third-Vendor Witness Report: Full Repository Regression Verification

* **Witness ID:** Antigravity (Independent Third-Vendor Witness)
* **Date:** 2026-07-05
* **Repository:** [ubcma](file:///F:/ubcma)
* **Branch:** `methods-borrowing`
* **OS Environment:** Windows (using `python`)

---

## 1. Overview & Verification Scope

This report provides independent witness verification of the full repository test suite for the Unified Bias-Calibrated Meta-Analysis (`ubcma`) prototype. The test suite was executed repo-wide to establish a regression baseline. 

Verification was conducted by:
1. Executing the entire pytest test suite from the repository root directory.
2. Explicitly running the pytest suite on each subdirectory group to ensure full test coverage and check for any discrepancy.
3. Executing scripts containing validation/parity tests that run directly with Python rather than through pytest auto-collection.

---

## 2. Test Execution Group Metrics

We discovered and ran all pytest tests across the repository. The verbatim outcomes are reported below by group:

### Group 1: Repo-Wide Run (All pytest tests)
* **Command:** `python -m pytest -q` from root [ubcma/](file:///F:/ubcma/)
* **Outcomes:** 
  * **Passed:** 215
  * **Failed:** 0
  * **Errored:** 0
  * **Skipped:** 6
  * **Total Collected:** 221
  * **Verbatim Output:** `215 passed, 6 skipped in 398.92s (0:06:38)`

### Group 2: Subdirectory pytest Runs
We ran pytest on each subdirectory separately. The verbatim counts for each are:

* **[tests/](file:///F:/ubcma/tests/)**
  * **Command:** `python -m pytest -q tests`
  * **Passed:** 118
  * **Failed:** 0
  * **Errored:** 0
  * **Skipped:** 6
  * **Total Collected:** 124
  * **Verbatim Output:** `118 passed, 6 skipped in 61.66s (0:01:01)`
  * *Note:* The 6 skipped tests are in [test_bayesian.py](file:///F:/ubcma/tests/test_bayesian.py) due to PyMC not being installed.

* **[nma/](file:///F:/ubcma/nma/)**
  * **Command:** `python -m pytest -q nma`
  * **Passed:** 35
  * **Failed:** 0
  * **Errored:** 0
  * **Skipped:** 0
  * **Total Collected:** 35
  * **Verbatim Output:** `35 passed in 52.69s`

* **[doseresponse/](file:///F:/ubcma/doseresponse/)**
  * **Command:** `python -m pytest -q doseresponse`
  * **Passed:** 23
  * **Failed:** 0
  * **Errored:** 0
  * **Skipped:** 0
  * **Total Collected:** 23
  * **Verbatim Output:** `23 passed in 40.86s`

* **[borrowing/](file:///F:/ubcma/borrowing/)**
  * **Command:** `python -m pytest -q borrowing`
  * **Passed:** 10
  * **Failed:** 0
  * **Errored:** 0
  * **Skipped:** 0
  * **Total Collected:** 10
  * **Verbatim Output:** `10 passed in 242.84s (0:04:02)`

* **[transport_nma/](file:///F:/ubcma/transport_nma/)**
  * **Command:** `python -m pytest -q transport_nma`
  * **Passed:** 6
  * **Failed:** 0
  * **Errored:** 0
  * **Skipped:** 0
  * **Total Collected:** 6
  * **Verbatim Output:** `6 passed in 9.77s`

* **[truth-recovery/](file:///F:/ubcma/truth-recovery/)**
  * **Command:** `python -m pytest -q truth-recovery`
  * **Passed:** 23
  * **Failed:** 0
  * **Errored:** 0
  * **Skipped:** 0
  * **Total Collected:** 23
  * **Verbatim Output:** `23 passed in 6.58s`

* **[truth-recovery-dta/](file:///F:/ubcma/truth-recovery-dta/)**
  * **Command:** `python -m pytest -q truth-recovery-dta`
  * **Passed:** 0
  * **Failed:** 0
  * **Errored:** 0
  * **Skipped:** 0
  * **Total Collected:** 0
  * **Verbatim Output:** `no tests ran`
  * *Note:* No standard pytest tests exist in this directory. The validation checks are run via direct Python scripts.

* **[consensus/](file:///F:/ubcma/consensus/)**
  * **Command:** `python -m pytest -q consensus`
  * **Passed:** 0
  * **Failed:** 0
  * **Errored:** 0
  * **Skipped:** 0
  * **Total Collected:** 0
  * **Verbatim Output:** `no tests ran`
  * *Note:* No standard pytest tests exist in this directory. The verification check is run via direct Python scripts.

---

## 3. Direct Python Verification Scripts

In addition to the pytest suite, we executed the validation/benchmark scripts in the subdirectories that do not contain standard `test_*.py` pytest entries but verify code correctness and parity:

1. **[test_netmeta_parity.py](file:///F:/ubcma/nma/reference/test_netmeta_parity.py)**
   * **Command:** `python nma/reference/test_netmeta_parity.py`
   * **Outcome:** `ALL PASS <1e-6` (League-table parity against R `netmeta` 3.6-1 and scalar/estimator parity on DL tau2, Q, df, and P-score).
2. **[test_bootstrap_compare.py](file:///F:/ubcma/nma/verify/test_bootstrap_compare.py)**
   * **Command:** `python nma/verify/test_bootstrap_compare.py`
   * **Outcome:** Runs successfully and prints bootstrap comparison metrics (Element vs Cluster Bootstrap) for $n \in \{5, 6, 7, 8\}$ on dense topologies, showing a consistent AdaptShrink-NMA win.
3. **[validate_python.py](file:///F:/ubcma/truth-recovery-dta/validate_python.py)**
   * **Command:** `python truth-recovery-dta/validate_python.py`
   * **Outcome:** `PASS (< 0.001)` (Validation of Reitsma bivariate estimator against R `mada::reitsma` reference fits; maximum absolute disagreement is `9.02e-07`).
4. **[consensus_or_flag.py](file:///F:/ubcma/consensus/consensus_or_flag.py)**
   * **Command:** `python consensus/consensus_or_flag.py`
   * **Outcome:** Runs successfully, completing the matched-false-flag comparison benchmark and paired-bootstrap analysis, confirming a consistent win for the heterogeneous bank over the homogeneous bank.

---

## 4. Static-vs-Dynamic Hardcode-Disclosure Table

| Category | Sourced Item | Classification | Verification / Evidence |
| :--- | :--- | :--- | :--- |
| **Static Configuration** | Test Selection / Exclusions | Pytest configuration | `pymc` dependency skip decorators on Bayesian tests in [test_bayesian.py](file:///F:/ubcma/tests/test_bayesian.py#L54-L86). |
| **Static Configuration** | Reference Values | Statically set in JSON/CSV | Reference files for parity comparisons (e.g. [reference_fits.json](file:///F:/ubcma/truth-recovery-dta/reference_fits.json) and `nma/reference/*.csv`). |
| **Dynamic Results** | Pytest Counts | Dynamically run per group | Recorded directly from the `stdout` of each execution. |
| **Dynamic Results** | Parity Disagreements | Dynamically calculated | Exact max absolute error outputs printed by verification scripts (e.g. `9.02e-07` in Reitsma DTA validation). |

---

## 5. Failures and Tracebacks

* **Errors/Failures:** None.
* Verdict: **GREEN** (All tests successfully passed or were cleanly skipped).

---

## 6. Summary Declaration & Authenticity Certification

This report represents a truth-first regression baseline. The test suite execution results are verified verbatim from direct runs on the `methods-borrowing` branch in a Windows Python environment.

*Witness Signature:* Antigravity  
*Signature Timestamp:* 2026-07-05T00:23:00+01:00
