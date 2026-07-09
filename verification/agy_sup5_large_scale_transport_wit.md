# Independent Third-Vendor Witness Report: Large-Scale Transport Verification (k=42)

* **Witness ID:** Antigravity (Independent Third-Vendor Witness)
* **Date:** 2026-07-05
* **Repository:** [ubcma](file:///F:/ubcma)
* **Branch:** `methods-borrowing`
* **OS Environment:** Windows (using `python`)

---

## 1. Overview & Verification Scope

This report provides independent third-vendor witness verification of the large-scale borrowing/transport program headlines. The scope includes:
1. Verifying the individual Rotavirus vaccine efficacy slice (U5MR moderator, $k=29$ trials) extracted from Clark 2019 (*Lancet Infect Dis* 19:717–727).
2. Verifying the combined pooled results across the two strong-modifier slices: BCG (latitude, $k=13$ trials) + Rotavirus (U5MR, $k=29$ trials), yielding $k=42$ real held-out trials.
3. Checking three comparison metrics across three bandwidth/kernel configurations:
   - **`transport - NMA`** (full method vs. textbook NMA)
   - **`relevance - uniform`** (kernel weighting vs. no relevance weighting)
   - **`transport - relevance`** (incremental gain of standardization/g-computation over relevance-only)
4. Confirming exact numerical estimates, bootstrap confidence intervals, and heterogeneity statistics ($I^2$).
5. Explicitly distinguishing between results that are **SETTLED** (robustly significant across all bandwidths/kernels with $I^2 \approx 0\%$) and those that are **ON-THRESHOLD** (borderline significant/null at primary bandwidths).

### Verified Code and Data Artifacts
* **Data extraction and prep:** [prep_rota.py](file:///F:/ubcma/borrowing/rota/prep_rota.py) [COMMITTED]
* **LOO Cross-validation engine:** [run_rota.py](file:///F:/ubcma/borrowing/rota/run_rota.py) [COMMITTED]
* **From-scratch independent verification:** [selfverify_rota.py](file:///F:/ubcma/borrowing/rota/selfverify_rota.py) [COMMITTED]
* **Multi-slice pooling script:** [aggregate_transport.py](file:///F:/ubcma/borrowing/agg/aggregate_transport.py) [COMMITTED]
* **Aggregated outcomes data:** [aggregate_results.json](file:///F:/ubcma/borrowing/agg/aggregate_results.json) [COMMITTED]
* **Summary report:** [REPORT_BORROWING_EXPANSION.md](file:///F:/ubcma/REPORT_BORROWING_EXPANSION.md) [COMMITTED]

---

## 2. Verification Findings: Settled vs. On-Threshold Results

The scripts were executed directly in the environment. Below we document the exact results and their settled vs. on-threshold status.

### A. SETTLED: Transport Beats Textbook NMA
The full bias-calibrated transportability model consistently and robustly outperforms textbook NMA across all three kernel/bandwidth choices, with minimal cross-slice heterogeneity ($I^2 \approx 0\%$):

1. **Primary Central Bandwidth (SD) — Gaussian Kernel:**
   - Pooled Inv-Var Delta (logRR MAE): **`-0.138`** [COMMITTED]
   - Bootstrap 95% CI: **`[-0.240, -0.028]`** [COMMITTED]
   - Analytical SE: **`0.056`** [COMMITTED]
   - Heterogeneity: $Q = 1.04$ (df = 1), $I^2 = 3.91\%$ (reported as $I^2 \approx 0\%$) [COMMITTED]
   - Verdict: **SETTLED WIN** (CI strictly below 0)

2. **Secondary Narrow Bandwidth (SD/2) — Gaussian Kernel:**
   - Pooled Inv-Var Delta (logRR MAE): **`-0.189`** [COMMITTED]
   - Bootstrap 95% CI: **`[-0.290, -0.085]`** [COMMITTED]
   - Analytical SE: **`0.054`** [COMMITTED]
   - Heterogeneity: $Q = 0.06$ (df = 1), $I^2 = 0.0\%$ [COMMITTED]
   - Verdict: **SETTLED WIN**

3. **Epanechnikov Kernel (Central Bandwidth):**
   - Pooled Inv-Var Delta (logRR MAE): **`-0.203`** [COMMITTED]
   - Bootstrap 95% CI: **`[-0.305, -0.095]`** [COMMITTED]
   - Analytical SE: **`0.055`** [COMMITTED]
   - Heterogeneity: $Q = 0.01$ (df = 1), $I^2 = 0.0\%$ [COMMITTED]
   - Verdict: **SETTLED WIN**

### B. SETTLED: Relevance Beats No-Relevance (Uniform)
Relevance down-weighting consistently outperforms the uniform (no-relevance) null model across all specifications, verifying the value of the similarity kernel:

1. **Primary Central Bandwidth (SD) — Gaussian Kernel:**
   - Pooled Inv-Var Delta (logRR MAE): **`-0.104`** [COMMITTED]
   - Bootstrap 95% CI: **`[-0.146, -0.054]`** [COMMITTED]
   - Analytical SE: **`0.024`** [COMMITTED]
   - Heterogeneity: $Q = 1.07$ (df = 1), $I^2 = 6.78\%$ (reported as $I^2 \approx 0\%$) [COMMITTED]
   - Verdict: **SETTLED WIN**

2. **Secondary Narrow Bandwidth (SD/2) — Gaussian Kernel:**
   - Pooled Inv-Var Delta (logRR MAE): **`-0.212`** [COMMITTED]
   - Bootstrap 95% CI: **`[-0.319, -0.098]`** [COMMITTED]
   - Analytical SE: **`0.057`** [COMMITTED]
   - Heterogeneity: $Q = 0.65$ (df = 1), $I^2 = 0.0\%$ [COMMITTED]
   - Verdict: **SETTLED WIN**

3. **Epanechnikov Kernel (Central Bandwidth):**
   - Pooled Inv-Var Delta (logRR MAE): **`-0.222`** [COMMITTED]
   - Bootstrap 95% CI: **`[-0.337, -0.101]`** [COMMITTED]
   - Analytical SE: **`0.062`** [COMMITTED]
   - Heterogeneity: $Q = 1.19$ (df = 1), $I^2 = 16.22\%$ [COMMITTED]
   - Verdict: **SETTLED WIN**

---

### C. ON-THRESHOLD: Transport Beats Relevance (Incremental Gain)
Unlike the comparisons above, the incremental gain from standardisation/transport over relevance-only is **not settled**. While pointing in the correct direction, the primary pre-registered central bandwidth crosses zero. A significant benefit is observed only at narrower or bounded kernels:

1. **Primary Central Bandwidth (SD) — Gaussian Kernel (Primary Pre-registered):**
   - Pooled Inv-Var Delta (logRR MAE): **`-0.069`** (precisely `-0.0688`) [COMMITTED]
   - Bootstrap 95% CI: **`[-0.134, +0.004]`** (precisely `[-0.1339, +0.0043]`) [COMMITTED]
   - Analytical SE: **`0.036`** [COMMITTED]
   - Heterogeneity: $Q = 0.63$ (df = 1), $I^2 = 0.0\%$ [COMMITTED]
   - Verdict: **ON-THRESHOLD / JUST MISSES** (the upper bootstrap CI bound is positive at `+0.004`, failing conservative significance).

2. **Secondary Narrow Bandwidth (SD/2) — Gaussian Kernel:**
   - Pooled Inv-Var Delta (logRR MAE): **`-0.066`** (precisely `-0.0660`) [COMMITTED]
   - Bootstrap 95% CI: **`[-0.097, -0.034]`** [COMMITTED]
   - Analytical SE: **`0.016`** [COMMITTED]
   - Heterogeneity: $Q = 0.71$ (df = 1), $I^2 = 0.0\%$ [COMMITTED]
   - Verdict: **WIN** (reaches significance due to less kernel-broadening noise at the narrow limit).

3. **Epanechnikov Kernel (Central Bandwidth):**
   - Pooled Inv-Var Delta (logRR MAE): **`-0.061`** (precisely `-0.0608`) [COMMITTED]
   - Bootstrap 95% CI: **`[-0.090, -0.030]`** [COMMITTED]
   - Analytical SE: **`0.016`** [COMMITTED]
   - Heterogeneity: $Q = 2.38$ (df = 1), $I^2 = 57.96\%$ (reported as $I^2 \approx 58\%$) [COMMITTED]
   - Verdict: **WIN** (wins but with moderate heterogeneity).

---

### D. Single-Country Sensitivity Analysis (Rotavirus-Only, k=20)
To ensure the Rotavirus modifier is not an artifact of assigning region-level child mortality values to pooled regions (e.g., WHO regional anchors), a sensitivity analysis dropping the 9 pooled-region trials was performed via [selfverify_rota.py](file:///F:/ubcma/borrowing/rota/selfverify_rota.py):

* **Full Rotavirus-Only LOO ($k=29$):**
  - `transport - relevance` delta: **`-0.110`** (95% CI: `[-0.212, +0.032]`) [COMMITTED]
* **Single-Country Rotavirus-Only ($k=20$):**
  - `transport - relevance` delta: **`-0.069`** (95% CI: `[-0.186, +0.101]`) [COMMITTED]
* **Verdict:** **ON-THRESHOLD / WEAKENS**. Dropping regional anchors reduces the sample and mortality gradient span, causing the transport benefit to weaken and cross zero more widely. This indicates the transport effect relies on the full gradient of child mortality, which is honestly disclosed.

---

## 3. Independent Witness Verdict

> [!NOTE]
> **VERDICT: CONFIRM**
> 
> The independent third-vendor witness verification confirms all reported numbers in [REPORT_BORROWING_EXPANSION.md](file:///F:/ubcma/REPORT_BORROWING_EXPANSION.md):
> 1. **Parity Check:** All values from the JSON output database [aggregate_results.json](file:///F:/ubcma/borrowing/agg/aggregate_results.json) match the reported figures to three decimal places.
> 2. **Correct Categorization:** The distinction between settled wins and on-threshold findings is highly accurate and is stated without inflation or fabrication. Specifically, the pooled incremental gain of `transport - relevance` is `-0.069 [-0.134, +0.004]` (just missing significance) at the primary bandwidth, but shows a robust win at narrow bandwidth and Epanechnikov kernel.
> 3. **Methodological Control Checks:** Re-running the standalone verification script [selfverify_rota.py](file:///F:/ubcma/borrowing/rota/selfverify_rota.py) replicated the Rotavirus-specific deltas (`tran-rel` of `-0.110` for full $k=29$ and `-0.069` for single-country $k=20$) and confirmed that disabling the modifier ($\beta=0$) collapses transport error onto relevance (delta of `+0.0000`), validating the g-computation process.
