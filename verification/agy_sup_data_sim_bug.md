# Data and Simulation Engine Independent Correctness Review Report

This report documents correctness reviews verified from first principles for `src/ubcma/data.py` and `src/ubcma/simulation.py` on the `methods-borrowing` branch of `F:\ubcma`.

## Methodology
- Inspection of data loading, validation, and feature parsing in `src/ubcma/data.py`.
- Inspection of synthetic meta-analysis generation, scenario simulation, and benchmarking in `src/ubcma/simulation.py`.
- First-principles review of specific target areas: effect-size conversions (such as OR->SMD), log-scale pooling, Fisher-z calculations, zero-cell corrections, publication-bias selection simulation generators, seeding/determinism, truthiness guards dropping `0.0`, empty-list any/all handling, and division-by-zero.

---

## Findings & Adjudication

### 1. Effect-Size Conversions (OR -> SMD constant)
- **Check**: Verification of whether the OR -> SMD conversion constant is implemented correctly (i.e., using $\frac{\sqrt{3}}{\pi} \approx 0.5513$, not $\sqrt{3/\pi} \approx 0.9772$).
- **Adjudication**: **Correct (N/A).** Neither `src/ubcma/data.py` nor `src/ubcma/simulation.py` performs any effect-size conversions. The data parser expects effect sizes `yi` and standard errors `sei` to be pre-calculated in the input CSV/DataFrame, and the simulator draws them directly from their latent normal distributions on the additive scale.

### 2. Log-Scale Pooling
- **Check**: Verification of whether pooling operations are correctly performed on the log-scale (or appropriate additive scale) without mixing raw odds ratios or relative risks.
- **Adjudication**: **Correct (N/A).** `src/ubcma/data.py` does not perform pooling. The `benchmark` function in `src/ubcma/simulation.py` uses linear models (`dersimonian_laird` and `weighted_meta_regression`) which operate correctly on the additive scale of the simulated $y$ values (which represent pre-transformed values like log-OR or SMD).

### 3. Fisher-z $1/(n-3)$ Variance
- **Check**: Verification of whether Fisher's z correlation variance is computed correctly as $1/(n-3)$.
- **Adjudication**: **Correct (N/A).** Neither `src/ubcma/data.py` nor `src/ubcma/simulation.py` handles correlation datasets or computes Fisher-z transformations. *(Note: While Fisher-z is calculated in the internal data-harmonisation script `borrowing/field_scale/corpus.py:66` and uses clamping `vz = 1.0 / np.maximum(n - 3, 1.0)`, it is absent from the core libraries reviewed here).*

### 4. Zero-Cell Correction (0.5 only when a cell is 0)
- **Check**: Verification of zero-cell Haldane-Anscombe corrections.
- **Adjudication**: **Correct (N/A).** Neither file handles raw cell counts ($2 \times 2$ tables) or performs zero-cell adjustments. The simulator generates continuous standard errors `se` directly from a uniform distribution ($[0.05, 0.22]$). *(Note: Zero-cell corrections are correctly isolated to the DTA engine in `src/ubcma/dta.py` and the preprocessing script `borrowing/field_scale/corpus.py`).*

### 5. Publication-Bias Selection Simulation Generators (smooth/step/Copas)
- **Check**: Review of the simulation selection probability function for monotonicity in $p$-value/effect and self-consistency of the Data Generating Process (DGP).
- **Adjudication**: **Correct / Self-Consistent.**
  - `src/ubcma/simulation.py` implements a **smooth** selection probability model based on logit-linear combination of soft-significance (`sig`), direction (`tanh(z)`), standardized precision, and quality score.
  - **Monotonicity**: Selection probability is monotone in the one-sided sense. For positive $z$ (favoured results), selection probability increases monotonically with effect size and decreases monotonically with $p$-value. For negative $z$, the direction term suppresses selection, opposing the significance term (representing realistic one-sided bias/suppression of negative results).
  - **DGP Consistency**: The DGP is self-consistent: it draws observed $Y_i \sim N(\text{true\_effect} + \text{bias}, SE^2)$ first, then evaluates selection status using the observed $Y_i$ and $SE_i$ values.
  - **Minor Note**: Standardizing precision (`precision_z`) uses the pre-selection generated pool's mean/sd. While consistent for the DGP, estimation models do not have access to these unselected population moments.
  - *(Note: A **step** selection generator is used in the dose-response simulator `doseresponse/sim_doseresponse.py` and is monotone in the one-sided z-statistic. No Copas selection generator is implemented).*

### 6. Seeding and Determinism
- **Check**: Verification of deterministic replication of simulated datasets.
- **Adjudication**: **Correct.** Both `generate_synthetic_meta_analysis` and `benchmark` instantiate localized random number generators using `np.random.default_rng(seed)`. There are no global state leaks or non-deterministic calls.

### 7. Truthiness Guards Dropping Numeric `0.0`
- **Check**: Detection of `if value:` style checks that inappropriately drop `0.0` or integer `0` as valid inputs.
- **Adjudication**: **Robustness Gap Found.**
  - **File:Line**: [src/ubcma/data.py:149](file:///F:/ubcma/src/ubcma/data.py#L149)
  - **Severity**: P2
  - **Defect**: The check `if design_col:` is used to parse the design column name. If a dataset has a column named `0` or `0.0` (as allowed in pandas integer indexing), the truthiness guard evaluates to `False`, silently dropping the column name and failing to parse the design categories.
  - **Shipped-vs-internal**: Shipped (library loader).
  
  - **File:Line**: [src/ubcma/data.py:183](file:///F:/ubcma/src/ubcma/data.py#L183)
  - **Severity**: P2
  - **Defect**: The check `if study_id_col:` is used to identify the study ID column. If `study_id_col` is integer `0` or float `0.0`, the guard evaluates to `False`, dropping the user-provided column and reverting to the default column name `"study_id"` or index-based study IDs.
  - **Shipped-vs-internal**: Shipped (library loader).

### 8. Empty-List `all()` / `any()` Logical Issues
- **Check**: Verification of built-in or numpy `all` / `any` calls on empty lists or arrays that return unintended truth values.
- **Adjudication**: **Correct.** In `src/ubcma/data.py:26`, `values.size` is checked before evaluating `np.all(np.isfinite(values))`, which correctly guards against empty arrays. In `src/ubcma/data.py:93`, `np.any(se <= 0)` is safe and correctly evaluates to `False` on empty inputs.

### 9. Division-by-Zero
- **Check**: Verification of potential zero divisions.
- **Adjudication**: **Correct.** All division operations are guarded:
  - `src/ubcma/data.py:123` protects `quality.mean(axis=1)` by checking `if quality.shape[1]:`.
  - `src/ubcma/data.py:141` protects `moderators.mean(axis=0)` by checking `if moderators.shape[1]:`.
  - `src/ubcma/simulation.py:59` protects standardization division by using `max(precision.std(ddof=0), 1e-9)`.
  - `src/ubcma/simulation.py:58` is safe because `se` is generated strictly in $[0.05, 0.22]$.
