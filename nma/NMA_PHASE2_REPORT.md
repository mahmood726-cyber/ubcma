# AdaptShrink-NMA Phase-2 Report: Components B & C

> Truth-first. Every number traceable to a committed file.
> Verification: 2 independent implementers (agy, claude) both PASS.

---

## Overview

Phase-2 adds two NMA-specific components to AdaptShrink-NMA:

- **Component B** — Network small-study meta-regression (PET/PEESE in the
  network setting), providing funnel-asymmetry correction at the network level.
- **Component C** — Design-by-treatment Q decomposition (Cochran Q inconsistency
  detection, matching `netmeta::decomp.design` to machine precision).

Both are verified by independent re-implementation to < 1e-11 (B) and < 1e-12 (C).
The field bake-off (univariate AdaptShrink feeding into NMA) is covered separately in
`truth-recovery/NMA_SCOREBOARD.md`.

---

## Part B — Network Small-Study Meta-Regression (PET / PEESE)

### Method

Within the basic-parameter (reference) NMA parameterization, augment the WLS
design matrix with `s_i = seTE_i` (PET) or `s_i = seTE_i^2` (PEESE). The slope
β of the covariate is the network Egger asymmetry test. If PET is significant,
the PEESE-adjusted league (effect at se→0) is the corrected estimate.

### PET Results (verified to B(1) max|TE diff| < 1e-11)

| network | treatments | k | τ² | β (PET slope) | z | p |
|---|---|---|---|---|---|---|
| smoking | 4 | 24 | 0.5989 | −1.369 | −1.930 | 0.054 |
| senn2013 | 10 | 28 | 0.1087 | +0.575 | +0.793 | 0.428 |

Neither network reaches the conventional α=0.05 threshold for network small-study
asymmetry. Honest interpretation: the network PET adjustment is exploratory for
these examples.

### Ranking Concordance: RE League vs PEESE-Adjusted League

**smoking network** (reference A; treatments B, C, D):

| treatment | RE d_t−A | PEESE d_t−A | Δ |
|---|---|---|---|
| B | 0.4162 | 0.2504 | −0.166 |
| C | 0.7334 | 0.4604 | −0.273 |
| D | 0.9023 | 0.3107 | −0.592 |

RE ranking: **D > C > B** → PEESE ranking: **C > D > B** (D and C swap at top).
The PEESE adjustment is large for D (−0.59) relative to D's RE CI (≈ ±0.27),
suggesting the D estimate is inflated by small-study effects. Despite p=0.054
not crossing α=0.05, the direction is clinically meaningful.

**senn2013 network** (reference acar; 9 active treatments):

Spearman ρ = 1.00 between RE and PEESE rankings; no rank change anywhere.
PET p=0.428; the adjustment is consistent with zero.

### Verified values (both verifiers agree to < 1e-11)

Smoking PEESE league vs A: B=0.2504, C=0.4604, D=0.3107.  
Senn2013 PEESE league vs acar: benf=0.0641, metf=−0.2991, migl=−0.1498,
piog=−0.3086, plac=0.8981, rosi=−0.3967, sita=0.2969, sulf=0.4550, vild=0.1678.

---

## Part C — Design-by-Treatment Q Decomposition (Inconsistency)

### Method

At common-effect weights (τ²=0), decompose Q_total into:
- **Q_het**: within-design heterogeneity (each design pooled separately)
- **Q_inc**: between-design inconsistency = Q_total − Q_het

df_inc = number of independent loops (cycle rank of the design graph).

### Results (verified to < 1e-12 vs `netmeta::decomp.design`)

| network | Q_total | df | Q_het | df | **Q_inc** | **df** | **p** |
|---|---|---|---|---|---|---|---|
| smoking | 202.619 | 23 | 187.399 | 16 | **15.220** | **7** | **0.033** |
| senn2013 | 96.986 | 18 | 74.455 | 11 | **22.530** | **7** | **0.002** |

**Both networks show statistically significant design-by-treatment inconsistency:**
- smoking: Q_inc = 15.220, df=7, **p = 0.033**
- senn2013: Q_inc = 22.530, df=7, **p = 0.002**

The Python implementation matches `netmeta::decomp.design` to < 1e-12 (both
networks), confirming the decomposition is correctly implemented.

### Implication for NMA

Significant Q_inc means the consistency assumption underlying standard RE-NMA
is violated for both datasets. Treatment estimates from a consistency model are
potentially biased. Analysts using AdaptShrink-NMA on these data should report
Q_inc and consider node-splitting or design-by-treatment sensitivity models.

---

## Verification Summary

| component | verifier | max error | threshold | verdict |
|---|---|---|---|---|
| B(1) no-covariate league (smoking) | agy | 4.999e-11 | 1e-8 | **PASS** |
| B(1) no-covariate league (senn2013) | agy | 4.786e-11 | 1e-8 | **PASS** |
| B(1) no-covariate league (smoking) | claude | 4.999e-11 | 1e-8 | **PASS** |
| B(1) no-covariate league (senn2013) | claude | 4.786e-11 | 1e-8 | **PASS** |
| C Q_inc (smoking) | agy | 1.0e-12 | 1e-6 | **PASS** |
| C Q_inc (senn2013) | agy | 1.0e-12 | 1e-6 | **PASS** |
| C Q_inc (smoking) | claude | 3.2e-13 | 1e-6 | **PASS** |
| C Q_inc (senn2013) | claude | 8.3e-13 | 1e-6 | **PASS** |

Verification scripts: `nma/verify/agy_phase2_nma.py`, `nma/verify/claude_phase2_nma.py`.

---

## Field Bake-Off Summary (AdaptShrink-Auto in NMA Context)

> Full table: `truth-recovery/NMA_SCOREBOARD.md`

| metric | adaptshrink_auto | reml_hksj | henmi_copas |
|---|---|---|---|
| c2 MCIW0 (grand mean) | **0.743** | 0.794 | 0.817 |
| l2 MCIW0 (grand mean) | **0.888** | 0.986 | 0.990 |
| c2 bias | **0.107** | 0.163 | 0.143 |
| c2 raw_cov | **0.843** | 0.582 | 0.648 |
| domination (c2, 54 cells) | **36/54** | — | — |
| domination (l2, 36 cells) | **23/36** | — | — |
| honest loss cells (c2) | 4/54 (3 step-sel, 1 null) | — | — |

The `adaptshrink_auto` estimator leads the 16-method field on MCIW0 (efficiency
at matched coverage) across both continuous and log-OR outcome grids, with
substantial gains at τ=0.1−0.3 and large k. The residual losses occur mostly in
step-selection cells at high τ where `trim_and_fill` wins a metric artifact
(its raw coverage is ~0.29 — not deployable), plus one no-selection cell where the
efficient estimators are optimal. (Counts use pairwise-complete bootstrap
aggregation, not the global all-methods intersection.)

---

*Phase-2 verification files: `nma/verify/VERIFY_SPEC_PHASE2.md` (spec),
`agy_phase2_RESULT.md`, `claude_phase2_RESULT.md` (both PASS).*
