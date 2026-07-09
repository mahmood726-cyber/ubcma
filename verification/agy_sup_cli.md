# Independent Third-Vendor Correctness Bug-Review: CLI & Entry Wrappers

This verification report reviews the correctness of the Command Line Interface (CLI) implementation in [cli.py](file:///F:/ubcma/src/ubcma/cli.py) and the main script [__main__.py](file:///F:/ubcma/src/ubcma/__main__.py) for the `ubcma` repository on the `methods-borrowing` branch.

---

## 1. Executive Summary

The CLI wrapper [__main__.py](file:///F:/ubcma/src/ubcma/__main__.py) is a thin correct entry wrapper that forwards calls directly to [cli.py](file:///F:/ubcma/src/ubcma/cli.py). However, the CLI logic itself is **not** a thin correct wrapper; it implements routing, parameter defaults, and calls out to statistical utilities and loaders. 

We identified several correctness issues, including:
1. **Critical encoding issues** where CSV files with a UTF-8 BOM are misparsed, causing validation errors.
2. **Statistical violations** of the advanced stats rules, notably running DerSimonian-Laird (DL) on small sample sizes ($k < 10$) and running the Copas selection model on small sample sizes ($k < 15$).
3. **Hypothesis testing errors** in comparators where a normal distribution (Z-test) is incorrectly used in place of a $t$-distribution with $k-2$ degrees of freedom.
4. **NaN/Inf formatting propagation** where unhandled mathematical values are printed directly to the stdout.

---

## 2. Findings Log

Below is the detailed list of findings formatted as `file:line + severity + shipped-vs-internal`.

### Finding 1: Unhandled CSV UTF-8 BOM and Locale-Dependent Encoding
* **Location:** [data.py:L61](file:///F:/ubcma/src/ubcma/data.py#L61) (invoked via `fit`, `diagnose`, `fit-bayes` in [cli.py](file:///F:/ubcma/src/ubcma/cli.py))
* **Severity:** **High**
* **Shipped-vs-Internal:** Shipped
* **Description:** 
  The function `MetaAnalysisDataset.from_csv` loads data using `pd.read_csv(path)` without specifying an encoding (e.g. `encoding="utf-8-sig"` or `encoding="utf-8"`). 
  - On Windows systems, this defaults to the system locale-dependent encoding (e.g. `cp1252`), which fails on non-ASCII characters.
  - If a CSV is saved as UTF-8 with a Byte Order Mark (BOM), the BOM (`\ufeff`) is kept at the start of the first column header. If the first column is `yi`, pandas reads it as `\ufeffyi`. The check `effect_col not in df` in [data.py:L86](file:///F:/ubcma/src/ubcma/data.py#L86) then fails, raising a confusing `ValueError` saying the column is missing, even though the column is present.

---

### Finding 2: Statistical Default Contradicts DL Bias Rule (Simulation Study)
* **Location:** [cli.py:L75-84](file:///F:/ubcma/src/ubcma/cli.py#L75-L84) and [simulation_study.py:L107-117](file:///F:/ubcma/src/ubcma/simulation_study.py#L107-L117)
* **Severity:** **Medium**
* **Shipped-vs-Internal:** Internal (exposed via `--methods` CLI option)
* **Description:**
  The `study` command runs a factorial simulation study. The default value for `--methods` includes `"dl"` and `"dl_hksj"`. 
  - While the scenarios might start with $k \in \{10, 30, 80\}$, the publication selection mechanism in [simulation_study.py:L83](file:///F:/ubcma/src/ubcma/simulation_study.py#L83) filters out studies, only requiring a minimum of 4 selected studies (`selected.sum() < 4`).
  - As a result, the DerSimonian-Laird (DL) estimator is run on simulated datasets where the final count of published studies $k_{\text{published}}$ is routinely between 4 and 9. This violates the advanced-stats rule: **"Never use DL for k<10 - use REML or PM."**

---

### Finding 3: Unconditional Calculation of DL Baseline for Small k
* **Location:** [model.py:L575](file:///F:/ubcma/src/ubcma/model.py#L575) (invoked via `fit` in [cli.py](file:///F:/ubcma/src/ubcma/cli.py))
* **Severity:** **Medium**
* **Shipped-vs-Internal:** Shipped
* **Description:**
  The main fitting procedure `UBCMAFit.fit` accepts datasets with $k \ge 4$ studies. At the end of fitting, it unconditionally runs `dersimonian_laird(y, se)` to report baseline marginal statistics, which are then printed by the CLI via `result.to_text()`. This violates the rule against running DL when $k < 10$ and presents a biased marginal mean estimate as the reference point to the user.

---

### Finding 4: Running Copas Selection Model on Small k
* **Location:** [cli.py:L75-84](file:///F:/ubcma/src/ubcma/cli.py#L75-L84) and [simulation_study.py:L127-129](file:///F:/ubcma/src/ubcma/simulation_study.py#L127-L129)
* **Severity:** **Medium**
* **Shipped-vs-Internal:** Internal (exposed via `--methods` CLI option)
* **Description:**
  The `study` command runs the Copas selection model by default. The Copas model is run on all replicates, including those where $k_{\text{published}}$ drops down to 4. This directly violates the rule: **"Copas: Needs k>=15."** In small samples, the likelihood surface of the Copas model is flat or degenerate, leading to unstable optimization and numerical failures (which are caught and turned into `NaN` values).

---

### Finding 5: Z-Test Used Instead of t-Test in PET-PEESE
* **Location:** [comparators.py:L124-125](file:///F:/ubcma/src/ubcma/comparators.py#L124-L125) (invoked via `study` and `adaptshrink` in [cli.py](file:///F:/ubcma/src/ubcma/cli.py))
* **Severity:** **Medium**
* **Shipped-vs-Internal:** Shipped / Internal
* **Description:**
  In the implementation of `pet_peese`, the significance test of the intercept is calculated using:
  ```python
  z_test = beta_pet[0] / max(intercept_se, 1e-9)
  p_val = 2 * (1 - norm.cdf(abs(z_test)))
  ```
  This uses the normal distribution cumulative distribution function (Z-test) instead of the $t$-distribution with $k-2$ degrees of freedom. For small meta-analyses (especially where $k < 30$), the normal approximation severely underestimates the $p$-value, causing false rejections of the null and misrouting the estimator from PET to PEESE.

---

### Finding 6: NaN/Inf Format Flowing into Printed Results
* **Location:** [cli.py:L115-116](file:///F:/ubcma/src/ubcma/cli.py#L115-L116) and [cli.py:L119-120](file:///F:/ubcma/src/ubcma/cli.py#L119-L120)
* **Severity:** **Low**
* **Shipped-vs-Internal:** Shipped
* **Description:**
  - If a profile likelihood search fails to cross the threshold in one direction, `profile_likelihood_ci` returns `float("inf")` or `float("-inf")`. This is formatted with `:.4f` and printed as `[-inf, inf]`.
  - If more than 20% of bootstrap runs fail, `bootstrap_ci` returns `float("nan")` for CIs, which is formatted with `:.4f` and printed as `[nan, nan]`.
  - If the user runs `benchmark` with `--replicates 0` (or negative numbers), the resulting empty dataframe results in `NaN` statistics being printed directly to stdout via `to_string()`.

---

### Finding 7: Lack of User-Friendly Error Catching and Exit Code Customization
* **Location:** [__main__.py:L3-4](file:///F:/ubcma/src/ubcma/__main__.py#L3-L4) and [cli.py:L95-223](file:///F:/ubcma/src/ubcma/cli.py#L95-L223)
* **Severity:** **Low**
* **Shipped-vs-Internal:** Shipped
* **Description:**
  There is no high-level `try/except` block catching typical errors (such as `FileNotFoundError`, `ValueError` for missing columns, or optimization failures). If one of these occurs, the script crashes with a full Python traceback and standard exit code 1. A robust CLI should catch validation and file errors, log a user-friendly error to `sys.stderr`, and exit with `sys.exit(1)`.
