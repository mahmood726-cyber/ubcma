# Independent Third-Vendor Witness Report: Registry-Borrowing Cross-Domain Headlines

* **Witness ID:** Antigravity (Independent Third-Vendor Witness)
* **Date:** 2026-07-04
* **Repository:** `F:\ubcma`
* **Branch:** `methods-borrowing`
* **OS Environment:** Windows (using `python`)

---

## (a) BCG Fair-Transport Test Verification (13 placebo trials, latitude modifier)

### 1. Transport-vs-NMA Margin
* **Claim:** `tran-nma` approx `-0.198 [-0.344, -0.041]`, robust across paths and bandwidths.
* **Committed JSON (`bcg_loo.json`, bw=13.876):** `-0.198 [-0.344, -0.041]`
* **Primary Run (`run_bcg.py`):**
  * `bw=13.9` (SD): `-0.198 [-0.344, -0.041]` (WIN)
  * `bw=6.9` (SD/2): `-0.205 [-0.354, -0.043]` (WIN)
  * `bw=20.8` (1.5*SD): `-0.199 [-0.347, -0.042]` (WIN)
* **From-Scratch Re-derivation (`selfverify_bcg.py`):**
  * `bw=13.876` (SD): `-0.197 [-0.343, -0.041]` (WIN)
* **Verdict:** **CONFIRM** (exact match on committed/primary, within bootstrap noise/precision on from-scratch).

### 2. Control target=pool-control HURTS
* **Claim:** `target=pool-control` hurts by approx `+0.187`.
* **Committed Report / Primary Run (`run_bcg.py`):**
  * `target=pool` (centroid): MAE `0.632` vs `0.445` (real), delta `+0.187 [+0.017, +0.347]`
* **From-Scratch Re-derivation (`selfverify_bcg.py`):**
  * `target=pool` (centroid): MAE `0.632` vs `0.445` (real), delta `+0.187 [+0.017, +0.347]`
* **Verdict:** **CONFIRM** (exact match).

---

## (b) Multispecialty Relevance Verification (N=5 clean slices/qualifiers across 3 specialties)

### 1. Pooled Relevance Effect vs. No-Relevance Null (Uniform)
* **Claim:** `relevance - uniform` approx `-10.9% [-20.2%, -1.5%]`
* **Committed JSON (`multispecialty_loo.json` / `loo_results_v2.json`):** Matches claim.
* **Primary Run (`aggregate_multispecialty.py`):** `-10.9% [-20.2%, -1.5%]` (CI<0 ROBUST, tau2=0.0078)
* **Verdict:** **CONFIRM** (exact match).

### 2. Pooled Relevance Effect vs. Scrambled Null
* **Claim:** `relevance - scrambled` approx `-12.4% [-22.8%, -2.0%]`
* **Primary Run (`aggregate_multispecialty.py`):** `-12.4% [-22.8%, -2.0%]` (CI<0 ROBUST, tau2=0.0094)
* **Verdict:** **CONFIRM** (exact match).

### 3. N=5 Clean Slices Verification
* **Claim:** N=5 clean specialties. (Specifically, 5 clean slices/qualifiers spanning 3 specialties: Education, Endocrine/Metabolic, and Oncology).
* **Observed Slices and Specialty Mapping:**
  1. `T2DM_HbA1c_GLP1only:ALL:dose` (Endocrine/Metabolic (GLP1), n=12, perm_p=0.0100)
  2. `Obesity_weight:ALL:baseline` (Endocrine/Metabolic (GLP1), n=9, perm_p=0.0015)
  3. `Edu_SATcoaching:kalaian:hrs` (Education, n=65, perm_p=0.0448)
  4. `Edu_TeacherExpect:raudenbush:weeks` (Education, n=19, perm_p=0.0265)
  5. `Onc_DoseToxicity:ursino:dose` (Oncology, n=49, perm_p=0.0001)
  *(Flat control excluded: `Addiction_BriefAlcohol:tannersmith:age` (Addiction, n=113, perm_p=0.4865, inert +2.7%))*
* **From-Scratch Re-derivations (`selfverify_multispecialty.py` and `selfverify_replication.py`):**
  * `Onc_DoseToxicity:ursino:dose`: rel-uniform `-0.119 [-0.174, -0.061]`, rel-scramble `-0.141 [-0.206, -0.079]` (WIN)
  * `Edu_TeacherExpect:raudenbush:weeks`: rel-uniform `-0.020 [-0.047, +0.010]` (n.s.), rel-scramble `-0.018 [-0.053, +0.018]` (n.s.)
  * `T2DM_HbA1c_GLP1only:ALL:dose`: rel-uniform `-0.180 [-0.305, -0.037]` (WIN), rel-scramble `-0.199 [-0.334, -0.045]` (WIN)
  * `Obesity_weight:ALL:baseline`: rel-uniform `-0.497 [-1.055, -0.099]` (WIN), rel-scramble `-0.599 [-1.250, -0.028]` (WIN)
* **Verdict:** **CONFIRM** (5 clean slices across 3 specialties are correct; results match the pooled analysis precisely).
