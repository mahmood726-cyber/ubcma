# Independent Third-Vendor Witness: AdaptShrink Univariate Boundary & Win-Region Mapping

**Verdict:** CONFIRM (with key caveats on the no-selection boundary)  
**Status:** COMMITTED (read from committed sweep results in `truth-recovery/realhc_*`, `truth-recovery/mc_*`, and `truth-recovery/field_v1_*` files)  
**OS/Shell:** Windows/PowerShell + Python 3.13  

---

## 1. Context and Executive Summary
This witness report evaluates the univariate boundary and win-region claims for **AdaptShrink** (`adaptshrink_ens`), a selection-robust random-effects meta-analysis ensemble. We verify where AdaptShrink robustly outperforms classical random-effects models (DerSimonian–Laird / REML + HKSJ), selection-aware estimators (Henmi–Copas, Copas–Shi selection MLE), and other adjustment methods (PET-PEESE, trim-and-fill) on the matched-coverage interval width (**MCIW0**) metric, versus where it merely ties or loses.

To ensure a fair comparison among models with wildly different raw coverages under publication selection, the codebase employs a **matched-coverage protocol**:
1. Replicates are split into calibration and test halves.
2. A constant half-width multiplier ($\kappa$) is calibrated on the calibration half to force exactly $95\%$ coverage.
3. The resulting matched width (**MCIW0 = $2c$**) is evaluated on the held-out test half.
4. An advantage is declared **robust** (a win) if and only if the $97.5\%$ percentile of the paired-bootstrap difference versus a comparator is strictly below $0$ (G4 gate).

We inspected the committed sweep data from the following files:
* [realhc_strong_truthgate.json](file:///F:/ubcma/truth-recovery/realhc_strong_truthgate.json) & [realhc_strong_table.csv](file:///F:/ubcma/truth-recovery/realhc_strong_table.csv) ($k=40$, strong selection vs real Henmi–Copas)
* [realhc_moderate_truthgate.json](file:///F:/ubcma/truth-recovery/realhc_moderate_truthgate.json) & [realhc_moderate_table.csv](file:///F:/ubcma/truth-recovery/realhc_moderate_table.csv) ($k=40$, moderate selection vs real Henmi–Copas)
* [mc_strong_truthgate.json](file:///F:/ubcma/truth-recovery/mc_strong_truthgate.json) & [mc_strong_table.csv](file:///F:/ubcma/truth-recovery/mc_strong_table.csv) ($k=40$, strong selection vs in-repo proxy Copas)
* [mc_moderate_truthgate.json](file:///F:/ubcma/truth-recovery/mc_moderate_truthgate.json) & [mc_moderate_table.csv](file:///F:/ubcma/truth-recovery/mc_moderate_table.csv) ($k=40$, moderate selection vs in-repo proxy Copas)
* [field_v1_scores.csv](file:///F:/ubcma/truth-recovery/field_v1_scores.csv) & [field_v1_pairwise.csv](file:///F:/ubcma/truth-recovery/field_v1_pairwise.csv) ($k \in \{10, 40\}$, selection strengths `strong` and `none`)

---

## 2. Head-to-Head Focused Slice Verification ($k=40$, $\mu=0.2$, $\tau=0.1$, target = $95\%$)
We compare AdaptShrink Ensemble (`adaptshrink_ens`) against the faithful port of the **Henmi–Copas** estimator (`henmi_copas`) and the in-repo proxy reference (`copas`):

### A. Strong Selection Strength (150 replicates)
* **Smooth Mechanism:** **WIN**
  - AdaptShrink `mciw0`: **0.2524** (vs Henmi–Copas `mciw0` **0.3267**, ratio: **0.773**)
  - Mean difference (`dMCIW0`): **-0.0813** ($95\%$ bootstrap CI: `[-0.1403, -0.0454]`, `robust_win`: **True**)
* **Step Mechanism:** **WIN**
  - AdaptShrink `mciw0`: **0.2204** (vs Henmi–Copas `mciw0` **0.3807**, ratio: **0.579**)
  - Mean difference (`dMCIW0`): **-0.1325** ($95\%$ bootstrap CI: `[-0.1604, -0.1085]`, `robust_win`: **True**)
* **Copas Mechanism:** **WIN**
  - AdaptShrink `mciw0`: **0.2047** (vs Henmi–Copas `mciw0` **0.2638**, ratio: **0.776**)
  - Mean difference (`dMCIW0`): **-0.0496** ($95\%$ bootstrap CI: `[-0.0769, -0.0141]`, `robust_win`: **True**)

### B. Moderate Selection Strength (150 replicates)
* **Smooth Mechanism:** **WIN**
  - AdaptShrink `mciw0`: **0.2474** (vs Henmi–Copas `mciw0` **0.2944**, ratio: **0.840**)
  - Mean difference (`dMCIW0`): **-0.0423** ($95\%$ bootstrap CI: `[-0.1095, -0.0032]`, `robust_win`: **True**)
* **Step Mechanism:** **WIN**
  - AdaptShrink `mciw0`: **0.1994** (vs Henmi–Copas `mciw0` **0.2935**, ratio: **0.679**)
  - Mean difference (`dMCIW0`): **-0.0846** ($95\%$ bootstrap CI: `[-0.1440, -0.0457]`, `robust_win`: **True**)
* **Copas Mechanism:** **TIE**
  - AdaptShrink `mciw0`: **0.2161** (vs Henmi–Copas `mciw0` **0.2637**, ratio: **0.819**)
  - Mean difference (`dMCIW0`): **-0.0222** ($95\%$ bootstrap CI: `[-0.0541, +0.0225]`, `robust_win`: **False**)
  - *Observation:* The true Henmi–Copas R port is slightly harder to beat under moderate Copas selection, resulting in a confidence interval crossing zero. Under the same setting vs the in-repo proxy reference (`copas`), AdaptShrink still achieves a robust win (CI `[-0.0651, -0.0130]`).

---

## 3. Grid Sweep and Win-Region Boundary ($k \in \{10, 40\}$, heterogeneous $\tau \in \{0.0, 0.1, 0.3\}$)
The field-wide `field_v1` sweep evaluates a grid of 54 cells. Grouping and averaging the MCIW0 values across $\mu \in \{0, 0.2, 0.5\}$ reveals the structural boundary of the win region:

### A. Grouped MCIW0 Values (Averaged over $\mu$)
| $k$ | Selection Mechanism | Heterogeneity $\tau$ | AdaptShrink (`ens`) | REML+HKSJ | Henmi–Copas | Trim-and-Fill | PET-PEESE |
|---|---|---|:---:|:---:|:---:|:---:|:---:|
| **10** | **none** | **0.0** | **0.2456** | 0.2580 | 0.2406 | 0.3126 | 0.3479 |
| | | **0.1** | **0.3555** | 0.2790 | 0.3323 | 0.4118 | 0.5584 |
| | | **0.3** | **0.8721** | 0.4742 | 0.6249 | 1.2050 | 0.9575 |
| | **step** | **0.0** | **0.2775** | 0.3582 | 0.3492 | 0.2945 | 0.4266 |
| | | **0.1** | **0.3895** | 0.4564 | 0.4628 | 0.3964 | 0.5864 |
| | | **0.3** | **0.8320** | 0.9019 | 0.8257 | 0.7768 | 1.0888 |
| | **copas** | **0.0** | **0.2163** | 0.3060 | 0.2970 | 0.2675 | 0.3697 |
| | | **0.1** | **0.3578** | 0.3419 | 0.3257 | 0.3870 | 0.5160 |
| | | **0.3** | **0.9288** | 0.7126 | 0.7685 | 0.9558 | 1.0593 |
| **40** | **none** | **0.0** | **0.1151** | 0.2081 | 0.2059 | 0.2019 | 0.2252 |
| | | **0.1** | **0.1749** | 0.2312 | 0.2357 | 0.3410 | 0.2888 |
| | | **0.3** | **0.4096** | 0.2908 | 0.2985 | 0.8904 | 0.4511 |
| | **step** | **0.0** | **0.2215** | 0.3734 | 0.3582 | 0.2432 | 0.3799 |
| | | **0.1** | **0.3190** | 0.4157 | 0.4043 | 0.3119 | 0.4023 |
| | | **0.3** | **0.6458** | 0.7290 | 0.7152 | 0.5052 | 0.7535 |
| | **copas** | **0.0** | **0.1009** | 0.2339 | 0.2344 | 0.1550 | 0.2408 |
| | | **0.1** | **0.1824** | 0.2961 | 0.2919 | 0.2537 | 0.3186 |
| | | **0.3** | **0.4181** | 0.4670 | 0.4254 | 0.7392 | 0.4832 |

---

## 4. Win-Region Boundary and Verdict Verification

### A. Is the Win Region Bounded? (CONFIRM)
The claim that the win is a **bounded region** is fully **CONFIRMED** by the committed sweep data. 
* **Selection Bias vs Heterogeneity Limit:** Under selection (`step` and `copas` mechanisms), AdaptShrink's robust wins are localized to cells with low-to-moderate heterogeneity ($\tau \le 0.1$). 
* At high heterogeneity ($\tau = 0.3$), the selection bias becomes negligible relative to the random-effects variance. Since bias-correction carries a variance premium, AdaptShrink's model-averaging spread widens the interval, causing it to tie or outright lose to efficient estimators like `reml_hksj` or `henmi_copas` on matched width. 
  - *Example ($k=10$, Copas selection, $\tau=0.3$):* AdaptShrink `mciw0` = **0.9288** vs Henmi–Copas = **0.7685** (Outright Loss).
  - *Example ($k=40$, Copas selection, $\tau=0.3$):* AdaptShrink `mciw0` = **0.4181** vs Henmi–Copas = **0.4254** (Tie).

### B. Does it Tie or stay Never-Worse under No Selection? (DIVERGE)
The claim that AdaptShrink **"ties/never-worse under none"** selection is **DIVERGED** (refuted) by the committed sweep results:
* Under zero selection (`none` mechanism), AdaptShrink experiences outright, statistically significant **losses** (wider matched-coverage intervals) at moderate-to-high heterogeneity.
* When selection bias is entirely absent, there is no bias to correct. The efficient random-effects estimators (`dl_hksj`, `reml_hksj`) are minimum-variance and unbiased. AdaptShrink, by paying a variance premium for bias corrections that are unnecessary, produces wider intervals.
  - *Example ($k=10$, none selection, $\tau=0.1$):* AdaptShrink `mciw0` = **0.3555** vs REML+HKSJ = **0.2790** (Outright Loss).
  - *Example ($k=10$, none selection, $\tau=0.3$):* AdaptShrink `mciw0` = **0.8721** vs REML+HKSJ = **0.4742** (Outright Loss, ~84% wider interval).
  - *Example ($k=40$, none selection, $\tau=0.3$):* AdaptShrink `mciw0` = **0.4096** vs REML+HKSJ = **0.2908** (Outright Loss, ~41% wider interval).

### Summary of Pairwise Verdicts vs Henmi–Copas (`henmi_copas`)
* **Under No Selection (`mechanism = none`):**
  - **$k=10$:** 0 Wins, 5 Ties, 4 Losses (Loses at $\tau \in \{0.1, 0.3\}$)
  - **$k=40$:** 4 Wins, 3 Ties, 2 Losses (Loses at $\tau = 0.3$)
* **Under Selection (`mechanism = step / copas`):**
  - **$k=10$:** 4 Wins, 12 Ties, 2 Losses (Loses to Henmi–Copas under Copas selection at $\tau = 0.3$)
  - **$k=40$:** 13 Wins, 4 Ties, 1 Loss (Loses to Henmi–Copas under Copas selection at $\tau = 0.3, \mu = 0.0$)

---

## 5. Conclusion and Witness Signature
Under selection, AdaptShrink Ensemble provides a Pareto-dominant option: it preserves near-nominal deployable coverage ($0.96 \le \text{raw\_cov} \le 0.98$ where all other models collapse) while achieving a significant matched-coverage width advantage over Henmi–Copas in the low-to-moderate heterogeneity region ($\tau \le 0.1$). However, the win is strictly bounded: at high heterogeneity ($\tau = 0.3$) or under no selection, AdaptShrink's bias-correction variance cost results in wider intervals (outright losses) compared to classical efficient random-effects estimators. 

This witness report confirms the mathematical existence and boundaries of the win region, while correcting the over-claim regarding no-selection performance.

**Witnessed by:** Antigravity Third-Vendor Engine  
**Date:** 2026-07-04  
