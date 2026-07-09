# Independent Third-Vendor Witness Report: DTA Truth-Recovery Verification

* **Witness ID:** Antigravity (Independent Third-Vendor Witness)
* **Date:** 2026-07-04
* **Repository:** [ubcma](file:///F:/ubcma)
* **Branch:** `methods-borrowing`
* **OS Environment:** Windows (using `python`)

---

## 1. Overview & Verification Scope

This report provides independent witness verification of the Diagnostic Test Accuracy (DTA) truth-recovery bake-off under the [truth-recovery-dta/](file:///F:/ubcma/truth-recovery-dta) directory, distinct from the `mada::reitsma` parity validation reported in [agy_fg_dta_witness.md](file:///F:/ubcma/verification/agy_fg_dta_witness.md).

We verified:
1. **The Focus grid:** Targeted contested-regime grid (small $k$, high $\tau$, threshold heterogeneity, selection), consisting of 48 simulation cells (16 specs × 3 selection strengths) × 100 reps.
2. **The HSROC-tail grid:** Sparse-cell / heavy-tail regime ($n_{med}=40, n_{min}=8$), consisting of 16 simulation cells (8 specs × 2 selection strengths) × 200 reps.
3. **Determinism and Reproducibility:** Direct execution of the primary bake-off script [dta_bakeoff.py](file:///F:/ubcma/truth-recovery-dta/dta_bakeoff.py) on the committed replicate CSV files [dta_focus_focus_perrep.csv](file:///F:/ubcma/truth-recovery-dta/dta_focus_focus_perrep.csv) and [dta_hsroc_hsroc_tail_perrep.csv](file:///F:/ubcma/truth-recovery-dta/dta_hsroc_hsroc_tail_perrep.csv).

Verification was conducted by:
- Re-running [dta_bakeoff.py](file:///F:/ubcma/truth-recovery-dta/dta_bakeoff.py) using the `--from-csv` flag on the committed per-replicate CSV data for both grids.
- Confirming that the re-computed truthgate JSON files match the committed files [dta_focus_focus_truthgate.json](file:///F:/ubcma/truth-recovery-dta/dta_focus_focus_truthgate.json) and [dta_hsroc_hsroc_tail_truthgate.json](file:///F:/ubcma/truth-recovery-dta/dta_hsroc_hsroc_tail_truthgate.json) to exact bitwise parity.
- Reviewing cell-level winners, grand-means, and comparing actual data on disk against the committed claims in [DTA_REPORT.md](file:///F:/ubcma/truth-recovery-dta/DTA_REPORT.md).

---

## 2. Core Results & Estimator Performance

Across both grids, the primary matched-coverage efficiency metric is **MCIW0-2D Area** (95th-percentile Mahalanobis confidence-region area on calib split; lower is better), and the target coverage is 0.95.

The grand-mean results calculated dynamically from the committed tables on disk are as follows:

### Focus Grid Grand-Means (Actual on disk)
* **Reitsma ([reitsma](file:///F:/ubcma/src/ubcma/dta.py#L318)):** MCIW0-area = `1.6195`, test_cov = `0.878`, bias(m1) = `-0.1426`, bias(m2) = `+0.0022`, RMSE = `0.4759`
* **Reitsma Indep ([reitsma_indep](file:///F:/ubcma/src/ubcma/dta.py#L333)):** MCIW0-area = `1.7337`, test_cov = `0.885`, bias(m1) = `-0.1801`, bias(m2) = `-0.0062`, RMSE = `0.4865`
* **Separate Univariate ([sep_univariate](file:///F:/ubcma/src/ubcma/dta.py#L348)):** MCIW0-area = `1.7056`, test_cov = `0.887`, bias(m1) = `-0.1671`, bias(m2) = `+0.0042`, RMSE = `0.4814`
* **AdaptShrink-DTA ([adaptshrink_dta](file:///F:/ubcma/src/ubcma/dta.py#L445)):** MCIW0-area = `6.1937`, test_cov = `0.907`, bias(m1) = `-0.1342`, bias(m2) = `+0.0218`, RMSE = `0.9424`

### HSROC-Tail Grid Grand-Means (Actual on disk)
* **Reitsma ([reitsma](file:///F:/ubcma/src/ubcma/dta.py#L318)):** MCIW0-area = `2.5930`, test_cov = `0.926`, bias(m1) = `-0.2908`, bias(m2) = `-0.0651`, RMSE = `0.5640`
* **Reitsma Indep ([reitsma_indep](file:///F:/ubcma/src/ubcma/dta.py#L333)):** MCIW0-area = `2.8368`, test_cov = `0.921`, bias(m1) = `-0.3340`, bias(m2) = `-0.0802`, RMSE = `0.5922`
* **Separate Univariate ([sep_univariate](file:///F:/ubcma/src/ubcma/dta.py#L348)):** MCIW0-area = `2.7798`, test_cov = `0.925`, bias(m1) = `-0.3285`, bias(m2) = `-0.0647`, RMSE = `0.5857`
* **AdaptShrink-DTA ([adaptshrink_dta](file:///F:/ubcma/src/ubcma/dta.py#L445)):** MCIW0-area = `6.7792`, test_cov = `0.949`, bias(m1) = `-0.2012`, bias(m2) = `+0.0383`, RMSE = `0.8822`

---

## 3. Discrepancy Analysis & Divergence Verdict

Comparing the actual data stored in the committed tables against the prose claims in [DTA_REPORT.md](file:///F:/ubcma/truth-recovery-dta/DTA_REPORT.md) reveals several significant discrepancies:

### Focus Grid Discrepancies
1. **Grand-Mean MCIW0-area:** [DTA_REPORT.md](file:///F:/ubcma/truth-recovery-dta/DTA_REPORT.md) claims that `reitsma` has a grand-mean MCIW0-area of `2.0739` and `adaptshrink_dta` has `2.4668`. 
   - *Actual on disk:* `reitsma` is `1.6195` and `adaptshrink_dta` is `6.1937`.
2. **Cell-Level Winners:** [DTA_REPORT.md](file:///F:/ubcma/truth-recovery-dta/DTA_REPORT.md) claims that out of 48 cells, `reitsma` won 36, `reitsma_indep` won 11, `sep_univariate` won 1, and `adaptshrink_dta` won 0.
   - *Actual on disk:* `reitsma` won 25 cells, `reitsma_indep` won 13 cells, `sep_univariate` won 9 cells, and `adaptshrink_dta` won **1 cell** (`k10_t0.6_r-0.6_p0.3` with strength `none`).
3. **Claim of Absolute Failure:** [DTA_REPORT.md](file:///F:/ubcma/truth-recovery-dta/DTA_REPORT.md) asserts: *"adaptshrink_dta is WORSE than reitsma in all 48/48 cells (MCIW0-area deficit > 0 everywhere)"* and *"Cell-level winners ... adaptshrink_dta: 0"*.
   - *Actual on disk:* This is incorrect. In cell `k10_t0.6_r-0.6_p0.3` (strength `none`), `adaptshrink_dta` achieved `mciw0_area` = `1.1142` compared to `reitsma`'s `1.1780` (a ratio of `0.946`), with a test coverage of `0.90` (within the `0.06` tolerance). It was the absolute winner of this cell.

### HSROC-Tail Grid Discrepancies
1. **Cell Count in HSROC-Tail:** [DTA_REPORT.md](file:///F:/ubcma/truth-recovery-dta/DTA_REPORT.md) repeatedly references 32 cells (e.g. "Total: 16 cells × 2 strengths" is actually 16 cells, but the winners table and summary table both claim 32 cells).
   - *Actual on disk:* There are exactly 16 cells evaluated in `dta_hsroc_hsroc_tail_table.csv`.
2. **Grand-Mean MCIW0-area:** [DTA_REPORT.md](file:///F:/ubcma/truth-recovery-dta/DTA_REPORT.md) claims `reitsma` has a grand-mean MCIW0-area of `2.5804` and `adaptshrink_dta` has `2.8885`. 
   - *Actual on disk:* `reitsma` is `2.5930` and `adaptshrink_dta` is `6.7792`.
3. **Cell-Level Winners:** [DTA_REPORT.md](file:///F:/ubcma/truth-recovery-dta/DTA_REPORT.md) claims `reitsma_indep` won 9 cells and `reitsma` won 7 cells.
   - *Actual on disk:* `reitsma` won 13 cells, `sep_univariate` won 2 cells, and `reitsma_indep` won 1 cell.
4. **Summary Table Discrepancies:** The summary table at the end of [DTA_REPORT.md](file:///F:/ubcma/truth-recovery-dta/DTA_REPORT.md) lists cell counts of 48 (focus) + 32 (hsroc-tail) = 80 cells total. It claims `reitsma` won 43/80 and `reitsma_indep` won 20/80.
   - *Actual on disk:* There are 48 (focus) + 16 (hsroc-tail) = 64 cells total. The actual winners are:
     - `reitsma`: 25 (focus) + 13 (hsroc-tail) = 38 / 64 cells
     - `reitsma_indep`: 13 (focus) + 1 (hsroc-tail) = 14 / 64 cells
     - `sep_univariate`: 9 (focus) + 2 (hsroc-tail) = 11 / 64 cells
     - `adaptshrink_dta`: 1 (focus) + 0 (hsroc-tail) = 1 / 64 cells

### Verdict: **DIVERGE** on Table Metrics & Counts, but **CONFIRM** on Qualitative Conclusions
- We **DIVERGE** from the reported cell counts, winner tables, and specific `mciw0_area` grand-means in [DTA_REPORT.md](file:///F:/ubcma/truth-recovery-dta/DTA_REPORT.md) as they contradict the committed CSV/JSON files.
- We **CONFIRM** the qualitative conclusion that the current ρ-shrinkage formulation of `adaptshrink_dta` is a failure. By shrinking the correlation parameter $\rho$ towards $0$ when the true $\rho \neq 0$, it severely misspecifies the GLS weights, leading to high RMSE (nearly double that of `reitsma`) and significantly inflated uncertainty region areas (`mciw0_area` grand-means of ~6.19 and ~6.78 vs ~1.62 and ~2.59 for standard `reitsma`).

---

## 4. Static-vs-Dynamic Hardcode-Disclosure Table

In accordance with pipeline protocols, the following table details the boundary between statically configured variables and dynamically computed runtime results in this DTA witness verification:

| Category | Sourced Item | Classification | Verification / Evidence |
| :--- | :--- | :--- | :--- |
| **Static Configuration** | Simulation Specs | Statically set in [dta_bakeoff.py](file:///F:/ubcma/truth-recovery-dta/dta_bakeoff.py#L69-L115) | The grid specs (k, tau, rho, prevalence, selection strength) are defined a priori. |
| **Static Configuration** | Base Random Seed | Statically set in [dta_sim.py](file:///F:/ubcma/truth-recovery-dta/dta_sim.py) | Base seed `12345` is fixed for replicate generation. |
| **Static Configuration** | Bootstrap Seed | Statically set in [dta_bakeoff.py](file:///F:/ubcma/truth-recovery-dta/dta_bakeoff.py#L250) | Paired bootstrap seed `7` is fixed for G4. |
| **Dynamic Data** | Replicate Fits | Dynamically simulated / read from CSV | Stored in [dta_focus_focus_perrep.csv](file:///F:/ubcma/truth-recovery-dta/dta_focus_focus_perrep.csv) and [dta_hsroc_hsroc_tail_perrep.csv](file:///F:/ubcma/truth-recovery-dta/dta_hsroc_hsroc_tail_perrep.csv). |
| **Dynamic Metrics** | matched-coverage areas | Dynamically computed from replicates | `mciw0_area`, `mciw_area`, and `raw_area` calculated by [dta_bakeoff.py](file:///F:/ubcma/truth-recovery-dta/dta_bakeoff.py). |
| **Dynamic Metrics** | paired-bootstrap CI | Dynamically resampled | Paired bootstrap CI bounds and `robust_win` flags computed over 2000 replicates. |

---

## 5. Runtime Errors & Verbatim Output

### Low Replicate Count KeyError
When executing the simulation grid with low replicate counts (e.g. `--reps 5`), [dta_bakeoff.py](file:///F:/ubcma/truth-recovery-dta/dta_bakeoff.py) fails because the calibration split receives $n < 16$ replicates, causing the matched-coverage table to remain empty and raising a `KeyError` on the `'cell'` column.

Verbatim traceback:
```text
Traceback (most recent call last):
  File "F:\ubcma\truth-recovery-dta\dta_bakeoff.py", line 424, in <module>
    main()
    ~~~~^^
  File "F:\ubcma\truth-recovery-dta\dta_bakeoff.py", line 394, in main
    for (cell, strength), sub in table.groupby(["cell", "strength"]):
                                 ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "~\AppData\Local\Programs\Python\Python313\Lib\site-packages\pandas\core\frame.py", line 9210, in groupby
    return DataFrameGroupBy(
        obj=self,
    ...<7 lines>...
        dropna=dropna,
    )
  File "~\AppData\Local\Programs\Python\Python313\Lib\site-packages\pandas\core\groupby\groupby.py", line 1331, in __init__
    grouper, exclusions, obj = get_grouper(
                               ~~~~~~~~___^
        obj,
        ____
    ...<5 lines>...
        dropna=self.dropna,
        ^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "~\AppData\Local\Programs\Python\Python313\Lib\site-packages\pandas\core\groupby\grouper.py", line 1043, in get_grouper
    raise KeyError(gpr)
KeyError: 'cell'
```

---

## 6. Summary Declaration & Authenticity Certification

We ran the verification script on the committed per-replicate CSVs:
- **Pilot Grid Verification:** Wrote `dta_pilot_truthgate.json` matching `dta_test_pilot_truthgate.json` perfectly.
- **Focus Grid Verification:** Re-generated `dta_focus_truthgate.json` matching `dta_focus_focus_truthgate.json` perfectly (bitwise parity).
- **HSROC-Tail Grid Verification:** Re-generated `dta_hsroc_tail_truthgate.json` matching `dta_hsroc_hsroc_tail_truthgate.json` perfectly (bitwise parity).

No fabrication was detected. All numbers are traceably sourced from the committed CSV/JSON datasets.

*Witness Signature:* Antigravity  
*Signature Timestamp:* 2026-07-04T22:24:00+01:00
