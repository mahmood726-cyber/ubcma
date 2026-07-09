# Independent Third-Vendor Witness Report: Conformal Calibration Repair

**Task Identification:** Verification of Conformal Calibration Coverage Repair across Borrowing-Field Methods on the Expanded Corpus (`methods-borrowing` branch).  
**File under Review:** [benchmark_learned_results.json](file:///F:/ubcma/borrowing/field_scale/benchmark_learned_results.json) / [benchmark_learned.py](file:///F:/ubcma/borrowing/field_scale/benchmark_learned.py)  
**Witness Date:** 2026-07-04  
**OS Platform:** Windows  
**Verdict:** **CONFIRM** (Conformal calibration repairs the coverage of every borrowing-field method to exactly 0.8988954970263382 (~0.90), and the learned-kernel GP estimator achieves the tightest conformal prediction interval width of 1.556568624354025 (~1.56).)

---

## 1. Summary of Claims & Background

The primary claim under verification is that:
1. **Conformal Calibration Repair:** Conformal calibration (using leave-one-out cross-conformal prediction within each effect-size family block) corrects the empirical coverage of all candidate borrowing-field methods to approximately $0.90$.
2. **Learned Kernel Superiority:** The [learned_kernel](file:///F:/ubcma/borrowing/field_scale/field_learned.py) method, which suffers from under-coverage under standard model-based intervals (achieving only $0.806$ coverage), is successfully corrected to $0.899$ coverage, while maintaining the **tightest conformal interval width** ($\approx 1.55$) among all compared methods.

We confirm these claims by inspecting the committed execution results in [benchmark_learned_results.json](file:///F:/ubcma/borrowing/field_scale/benchmark_learned_results.json) (labeled **COMMITTED**).

---

## 2. Table of Conformal Performance (COMMITTED)

Below are the exact values read directly from the committed [benchmark_learned_results.json](file:///F:/ubcma/borrowing/field_scale/benchmark_learned_results.json):

| Method Name | Model Coverage (`model_cover`) | Model PI Average Width (`model_width`) | Conformal Coverage (`conf_cover`) [COMMITTED] | Conformal Width (`conf_width`) [COMMITTED] |
| :--- | :---: | :---: | :---: | :---: |
| `no_borrow` | 0.9039932030586236 | 1.9041228319099395 | 0.8988954970263382 | 1.9590344530272246 |
| `within_MA` | 0.9430756159728122 | 1.8259707250575050 | 0.8988954970263382 | 1.6969019836521755 |
| `hand_field` | 0.9456244689889550 | 1.8367796592646970 | 0.8988954970263382 | 1.7735666795159800 |
| `robust_map` | 0.9991503823279524 | 7.0058626270799760 | 0.8988954970263382 | 1.6343944451170915 |
| `hier_bayes` | 0.7765505522514868 | 1.2982685271919765 | 0.8988954970263382 | 1.6118387672543590 |
| `g_model` | 0.9337298215802888 | 2.2967430179192174 | 0.8988954970263382 | 1.9872176669695790 |
| **`learned_kernel`** | **0.8062871707731520** | **1.3024211909187777** | **0.8988954970263382** | **1.5565686243540250** |
| `learned_scrambled` | 0.8079864061172473 | 1.4353094427154183 | 0.8988954970263382 | 1.7683841556448632 |

---

## 3. Mathematical Analysis & Insights

### A. Mathematical Identity of Conformal Coverage

A notable observation is that `conf_cover` is exactly equal to `0.8988954970263382` (which is $89.89\%$) for **every single method** (except in potential cases with infinite/non-finite values or ties, of which there are none here).

This is not a numerical coincidence, but rather a direct consequence of the leave-one-out conformal prediction algorithm implemented in [conformal_intervals](file:///F:/ubcma/borrowing/field_scale/field_learned.py#L271-L293).

Under the hood:
1. The 1177 studies are partitioned into three effect-size family blocks:
   - **SMD (Standardised Mean Difference):** $N_{\text{SMD}} = 445$ studies
   - **LOR (Log Odds Ratio):** $N_{\text{LOR}} = 380$ studies
   - **COR (Correlation / Fisher-z):** $N_{\text{COR}} = 352$ studies
2. For each study $j$ within a family block of size $M$, its conformal interval is constructed using the residual quantile of the other $M - 1$ studies:
   $$q_j = \text{quantile}(\{|e_i|\}_{i \neq j}, 1 - \alpha, \text{method="higher"})$$
   with $\alpha = 0.10$.
3. When `method="higher"` is used in NumPy, the $(1-\alpha)$ quantile of $M-1$ values selects the $\lceil(M-1)(1-\alpha)\rceil$-th smallest residual. 
4. If the residuals are distinct, then for any study $j$, its residual $|e_j|$ is $\le q_j$ if and only if $|e_j|$ ranks within the first $k_M = \lceil(M-1)(1-\alpha)\rceil$ smallest residuals in the combined set of all $M$ residuals.
5. Consequently, the number of covered studies in each family block is mathematically guaranteed to be exactly $k_M$:
   - For SMD: $k_{445} = \lceil 444 \times 0.90 \rceil = 400$
   - For LOR: $k_{380} = \lceil 379 \times 0.90 \rceil = 342$
   - For COR: $k_{352} = \lceil 351 \times 0.90 \rceil = 316$
6. The total number of covered studies across the corpus is exactly:
   $$\text{Total Covered} = 400 + 342 + 316 = 1058$$
7. Thus, the empirical coverage is:
   $$\text{Coverage} = \frac{1058}{1177} \approx 0.8988954970263382$$

This mathematically guarantees that conformal calibration maps the empirical coverage of *any* method to exactly $89.89\%$ (i.e., $\sim 0.90$) given the sample sizes of the three family blocks, completely fixing the coverage regardless of the original model's calibration quality.

### B. Verification of Conformal Prediction Widths

While conformal prediction guarantees uniform coverage ($89.89\%$), the efficiency of each method is reflected in the average width of its conformal intervals. A smaller average width indicates a more precise and informative prediction.

Sorting the methods by their average conformal interval width (`conf_width`) reveals:
1. **`learned_kernel`**: **1.5565686243540250** (Tightest)
2. `hier_bayes` (Hierarchical Bayes): 1.6118387672543590 (+3.5%)
3. `robust_map` (Robust MAP): 1.6343944451170915 (+5.0%)
4. `within_MA` (Within-MA borrowing): 1.6969019836521755 (+9.0%)
5. `learned_scrambled` (Negative Control): 1.7683841556448632 (+13.6%)
6. `hand_field` (AdaptShrink): 1.7735666795159800 (+14.0%)
7. `no_borrow` (No borrowing): 1.9590344530272246 (+25.9%)
8. `g_model` (G-modeling): 1.9872176669695790 (+27.7%)

The GP-based `learned_kernel` achieves the tightest width (~1.557), which represents a **$9.0\%$ reduction** in prediction interval width relative to standard `within_MA` borrowing, and a **$25.9\%$ reduction** compared to `no_borrow`.

---

## 4. Witness Verdict

We **CONFIRM** the claims under review:
- Conformal calibration successfully repairs the empirical coverage of all methods to exactly $0.8988954970263382$ ($\sim 0.90$), fixing the under-coverage of methods like `learned_kernel` (which increases from $0.806287170773152$ to $0.8988954970263382$).
- The GP-based `learned_kernel` method produces the tightest average conformal interval width of **$1.556568624354025$** across all candidate methods, verifying that it is the most efficient predictive model on the expanded corpus.
