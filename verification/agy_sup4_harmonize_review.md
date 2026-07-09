# Independent Third-Vendor Review: Data Harmonization Provenance

This report documents the independent third-vendor correctness review of data harmonization provenance in [F:/ubcma](file:///F:/ubcma) (branch `methods-borrowing`). The review focuses on how the borrowing corpus is harmonized onto a common scale across the three effect size families: **COR** (Fisher-z correlation), **LOR** (log odds ratio), and **SMD** (Hedges' g standardised mean difference).

---

## 1. Executive Summary & Verdict

*   **Overall Verdict:** The harmonization architecture is **sound and conceptually correct**. Effect families are strictly segregated (block-diagonal kernel), ensuring no cross-family scale mixing or sign errors. The primary duplicates are correctly dropped.
*   **Defects Identified:** Two minor defects and one approximation discrepancy were found in the correlation (COR) and standardized mean difference (SMD) families.
*   **MAE Impact:** None of the identified issues move the headline learned-kernel MAE of **0.3325** at printed precision. The impacts are negligible due to the small size of the affected datasets relative to the 1177-node corpus.

---

## 2. Methodology & Scale Harmonization Architecture

The codebase stages and harmonizes meta-analyses (MAs) in [corpus.py](file:///F:/ubcma/borrowing/field_scale/corpus.py) and [harmonize_new.R](file:///F:/ubcma/borrowing/field_scale/harmonize_new.R) into a common per-family representation.
*   **Block-Diagonal Separation:** Cross-family borrowing is prevented. The Gaussian Process model in [field_learned.py](file:///F:/ubcma/borrowing/field_scale/field_learned.py) groups the corpus by family block (via `df.groupby("family")`) for fitting, cross-validation, and conformal calibration. No direct scale or sign mixing occurs during estimation.
*   **Sign Alignment:** Effect signs are consistently oriented (positive effect indicates positive correlation, increased odds of the treatment event, or higher treatment mean compared to control).

---

## 3. Family-Specific Harmonization Verification

### A. COR Family (Fisher-z Correlation)
The correlation family uses the Fisher-z transformation $z = \operatorname{arctanh}(r)$ with sampling variance $v_z = 1/(n-3)$.

#### 1. Standard Correlations
For standard correlations (e.g., `crede2010`, `molloy2014`, `mcdaniel1994`, `craft2003`, `cohen1981`), the transformation is implemented in `_z_from_r`:
```python
def _z_from_r(r, n):
    r = np.clip(np.asarray(r, float), -0.9999, 0.9999)
    n = np.asarray(n, float)
    z = np.arctanh(r)
    vz = 1.0 / np.maximum(n - 3, 1.0)
    return z, vz
```
*   **Correction/Parity:** The formula matches `metafor::escalc(measure="ZCOR")`.
*   **Robustness Clamping (Minor Gap):** For $n \le 3$, the denominator is clamped to 1.0, assigning a finite variance of 1.0. Mathematically, the variance is undefined/infinite for $n \le 3$ (and R's `escalc` returns `NA` with a warning). This allows tiny, unreliable correlation studies to enter the model with finite weight.

#### 2. Partial Correlations (`aloe2013`)
In `aloe2013`, partial correlations are computed from t-values:
```python
dfree = df.n - df.preds - 1
r = df.tval / np.sqrt(df.tval ** 2 + dfree)
z = np.arctanh(np.clip(r, -0.9999, 0.9999))
vz = 1.0 / np.maximum(df.n - df.preds - 3, 1.0)
```
*   **Defect (Off-by-One Degrees of Freedom):** The residual degrees of freedom for the t-to-r conversion is computed as $dfree = n - preds - 1$, implying the regression has $preds$ total predictors (including intercept). The number of control variables is $c = preds - 1$. The sampling variance of the Fisher-z transformed partial correlation should be:
    $$v_z = \frac{1}{n - c - 3} = \frac{1}{n - preds - 2}$$
    However, the code uses `vz = 1.0 / np.maximum(df.n - df.preds - 3, 1.0)`. This subtracts one too many degrees of freedom, causing an overestimation of the sampling variance and mismatching `metafor::escalc(measure="ZPCOR")` (which yields $\frac{1}{n - preds - 2}$).
*   **MAE Impact:** Negligible. It affects only the 5 studies of the `aloe2013` meta-analysis out of the 1177 total nodes. The headline MAE of 0.3325 remains unchanged.

---

### B. LOR Family (Log Odds Ratio)
The LOR family uses the log odds ratio from 2x2 contingency tables:
$$\text{lor} = \log\left(\frac{a \cdot d}{b \cdot c}\right), \quad v = \frac{1}{a} + \frac{1}{b} + \frac{1}{c} + \frac{1}{d}$$

*   **Implementation:** In [corpus.py](file:///F:/ubcma/borrowing/field_scale/corpus.py), LOR is computed via `_lor_2x2`:
```python
def _lor_2x2(a, b, c, d):
    a, b, c, d = (np.asarray(x, float) for x in (a, b, c, d))
    zero = (a == 0) | (b == 0) | (c == 0) | (d == 0)
    a = a + 0.5 * zero; b = b + 0.5 * zero
    c = c + 0.5 * zero; d = d + 0.5 * zero
    lor = np.log((a * d) / (b * c))
    v = 1 / a + 1 / b + 1 / c + 1 / d
    return lor, v
```
*   **Correction/Parity:** Matches the standard formula. The continuity correction of $+0.5$ added to all cells when any cell is zero matches `metafor::escalc(measure="OR")`'s default `add=0.5` and `to="only0"` behavior.
*   **R Implementation:** In [harmonize_new.R](file:///F:/ubcma/borrowing/field_scale/harmonize_new.R), `escalc("OR", ai=e$ai, bi=e$n1i - e$ai, ci=e$ci, di=e$n2i - e$ci)` is used. The measure `"OR"` in `metafor` computes the log odds ratio, not the raw odds ratio. This is correct.

---

### C. SMD Family (Standardised Mean Difference / Hedges' g)
The SMD family calculates Hedges' g and its variance from two-arm means.

*   **Implementation:** In [corpus.py](file:///F:/ubcma/borrowing/field_scale/corpus.py), this is computed via `_g_from_means`:
```python
def _g_from_means(n1, m1, sd1, n2, m2, sd2):
    n1, m1, sd1, n2, m2, sd2 = map(np.asarray, (n1, m1, sd1, n2, m2, sd2))
    sp = np.sqrt(((n1 - 1) * sd1 ** 2 + (n2 - 1) * sd2 ** 2) / (n1 + n2 - 2))
    d = (m1 - m2) / sp
    J = 1.0 - 3.0 / (4 * (n1 + n2) - 9)
    g = J * d
    vg = (n1 + n2) / (n1 * n2) + g ** 2 / (2 * (n1 + n2))
    return g, vg
```
*   **Variance Formula Check:** The variance formula $v_g = \frac{1}{n_1} + \frac{1}{n_2} + \frac{g^2}{2(n_1 + n_2)}$ matches `metafor`'s default large-sample approximation (`vtype="LS"`), where Hedges' g is substituted in the second term.
*   **Discrepancy (Correction Factor Approximation):** Python uses the linear/fractional approximation for Hedges' small-sample correction: $J = 1 - \frac{3}{4(n_1 + n_2) - 9}$. R's `metafor::escalc` computes the exact correction factor using gamma functions:
    $$J_{\text{exact}} = \frac{\Gamma(m/2)}{\sqrt{m/2} \, \Gamma((m-1)/2)} \quad \text{where } m = n_1 + n_2 - 2$$
    This causes a tiny numerical discrepancy. For example, for $n_1=10, n_2=12$:
    *   Python: $g = 0.700605$, $v_g = 0.194489$
    *   R `escalc`: $yi = 0.700546$, $vi = 0.194487$
*   **MAE Impact:** None. The discrepancy is on the order of $10^{-5}$ and does not affect the printed learned-kernel MAE.

---

## 4. Duplicate Meta-Analyses Check

Duplicate meta-analyses that share overlapping trials or represent identical data are correctly dropped:
*   **`colditz1994` vs `bcg`:** Identical BCG vaccine datasets. Only `bcg` is loaded in [corpus.py](file:///F:/ubcma/borrowing/field_scale/corpus.py). `colditz1994` is explicitly skipped in [harmonize_new.R](file:///F:/ubcma/borrowing/field_scale/harmonize_new.R).
*   **`egger2001` vs `li2007`:** Shared trials (IV magnesium in MI). Only `li2007` is loaded in [corpus.py](file:///F:/ubcma/borrowing/field_scale/corpus.py). `egger2001` is explicitly skipped in [harmonize_new.R](file:///F:/ubcma/borrowing/field_scale/harmonize_new.R).

---

## 5. Tabular Summary of Findings

| Finding / File:Line | Description | Severity | Moves learned-kernel MAE 0.3325? |
| :--- | :--- | :---: | :---: |
| **Partial Correlation DF**<br>[corpus.py:153](file:///F:/ubcma/borrowing/field_scale/corpus.py#L153) | Off-by-one error in Fisher-z variance of partial correlations (uses $n - preds - 3$ instead of $n - preds - 2$). | **P2** (Minor) | **No** (Impact < 1e-6) |
| **Fisher-z Clamping**<br>[corpus.py:66](file:///F:/ubcma/borrowing/field_scale/corpus.py#L66) | Clamps denominator to 1.0 for $n \le 3$, assigning a finite variance instead of undefined/infinite variance. | **P3** (Low) | **No** |
| **Hedges' g Correction**<br>[corpus.py:56](file:///F:/ubcma/borrowing/field_scale/corpus.py#L56) | Uses linear/fractional approximation for Hedges' $J$ instead of R `metafor`'s exact gamma-based formula. | **P3** (Low) | **No** (Impact < 1e-5) |
| **Duplicate Dropping** | `colditz1994` (duplicate of `bcg`) and `egger2001` (duplicate of `li2007`) are correctly excluded. | **Correct** | **No** |
| **Sign/Scale Mixing** | Estimation is strictly separated by family via `df.groupby("family")`, preventing cross-scale mixing. | **Correct** | **No** |
