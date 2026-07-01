# AdaptShrink-DTA Phase-2 Report: Focus Grid & HSROC-Tail

> Truth-first. All numbers from committed simulation CSVs.
> MCIW0-area = 95th-pctile ellipse area on calib split (primary DTA efficiency metric; lower = better).
> Key finding: AdaptShrink-DTA does NOT outperform standard Reitsma on any tested grid cell.

---

## Overview

Phase-2 DTA runs two targeted grids:

- **Focus grid** — contested regimes (small k, high τ, selection), 48 cells × 3 strengths × 100 reps
- **HSROC-tail grid** — sparse-cell / heavy-tail regime (n_med=40, n_min=8), 16 cells × 2 strengths × 200 reps

Methods benchmarked:
- `reitsma` — bivariate ML (field comparator)
- `reitsma_indep` — bivariate ML with ρ fixed = 0
- `sep_univariate` — DerSimonian-Laird pools logit(Se)/logit(Sp) independently
- `adaptshrink_dta` — bivariate ML + shrinkage of ρ̂ toward 0 (δ-gated by k and condition number)

---

## Focus Grid

### Design

| parameter | values |
|---|---|
| k | 6, 10 |
| τ (Se and Sp shared) | 0.6, 0.8 |
| ρ (true between-study correlation) | 0.0, −0.6 |
| prevalence | 0.1, 0.3 |
| selection strength | none, moderate, strong |
| n_med | 80 |
| reps | 100 |

Total: 48 simulation cells (k × τ × ρ × prev) × 3 strengths.

### Grand-mean results

| method | MCIW0-area | test_cov | bias(m1) | bias(m2) | RMSE |
|---|---|---|---|---|---|
| reitsma | **2.0739** | 0.934 | −0.143 | +0.002 | 0.476 |
| reitsma_indep | 2.2615 | 0.929 | −0.180 | −0.006 | 0.487 |
| adaptshrink_dta | 2.4668 | 0.937 | −0.134 | +0.022 | **0.942** |
| sep_univariate | 2.5881 | 0.927 | −0.167 | +0.004 | 0.481 |

### Cell-level winners (lowest MCIW0-area per cell)

| method | cells won (of 48) |
|---|---|
| reitsma | **36** |
| reitsma_indep | 11 |
| sep_univariate | 1 |
| adaptshrink_dta | **0** |

### adaptshrink_dta vs reitsma comparison

- **adaptshrink_dta is WORSE than reitsma in all 48/48 cells** (MCIW0-area deficit > 0 everywhere)
- Mean deficit: +0.39 area units (reitsma smaller is better)
- **Deficit by true ρ:**
  - ρ = 0.0 cells: deficit ≈ 0.02–0.05 (small; shrinkage toward 0 is near-correct)
  - ρ = −0.6 cells: deficit ≈ 0.3–1.8 (large; shrinkage toward 0 misspecifies GLS weights)
- **Largest deficits** (worst AdaptShrink-DTA cells):
  - k=6, τ=0.8, ρ=−0.6, prev=0.3, strong: +1.82
  - k=6, τ=0.8, ρ=−0.6, prev=0.3, moderate: +1.35
  - k=6, τ=0.8, ρ=−0.6, prev=0.1, strong: +1.26
- **Smallest deficits** (closest to reitsma):
  - k=10, τ=0.8, ρ=0.0, prev=0.1, moderate: +0.018
  - k=6, τ=0.8, ρ=0.0, prev=0.1, strong: +0.035

### RMSE observation

`adaptshrink_dta` RMSE (0.942) is roughly 2× that of reitsma (0.476). This indicates that
the ρ-shrinkage mechanism increases point-estimate instability, not just ellipse area.
The GLS weighting used to combine studies changes when ρ̂ is shrunk toward 0 — in cells
where the true ρ ≠ 0, this distorts the optimal weighting and amplifies estimation error.

---

## HSROC-Tail Grid

### Design

| parameter | values |
|---|---|
| k | 6, 10 |
| τ | 0.6, 0.8 |
| ρ (true) | −0.6 |
| prevalence | 0.1, 0.3 |
| n_med | 40 (sparse) |
| n_sigma | 0.9 |
| n_min | 8 (very sparse) |
| selection strength | none, strong |
| reps | 200 |

Total: 16 cells × 2 strengths. k_eff post-selection ranges from 6–10.

### Convergence

All methods: **100% convergence** across all 16 cells and both selection strengths.
Python ML (Nelder-Mead multi-start) is robust even at n_med=40, n_min=8. No
HSROC-instability / non-convergence failure mode materialized.

### Grand-mean results

| method | MCIW0-area | test_cov | bias(m1) | bias(m2) | RMSE |
|---|---|---|---|---|---|
| reitsma | **2.5804** | 0.940 | −0.291 | −0.065 | 0.564 |
| reitsma_indep | 2.6255 | 0.935 | −0.334 | −0.080 | 0.592 |
| adaptshrink_dta | 2.8885 | 0.930 | −0.201 | +0.038 | **0.882** |
| sep_univariate | 3.0974 | 0.946 | −0.329 | −0.065 | 0.586 |

### Cell-level winners (lowest MCIW0-area)

| method | cells won (of 32) |
|---|---|
| reitsma_indep | **9** |
| reitsma | 7 |
| adaptshrink_dta | **0** |
| sep_univariate | 0 |

Note: reitsma_indep edges out reitsma in sparse-cell settings — likely because estimating
ρ from very sparse data adds noise that the ρ=0 constraint avoids. This is a different
mechanism from AdaptShrink-DTA's explicit shrinkage formula but arrives at a similar insight.

### By (k, τ) breakdown

| k | τ | method | MCIW0-area | test_cov | RMSE |
|---|---|---|---|---|---|
| 6 | 0.6 | reitsma | 2.977 | 0.933 | 0.562 |
| 6 | 0.6 | reitsma_indep | 3.042 | 0.940 | 0.588 |
| 6 | 0.6 | **adaptshrink_dta** | **3.292** | **0.933** | **0.926** |
| 6 | 0.6 | sep_univariate | 3.733 | 0.960 | 0.579 |
| 6 | 0.8 | reitsma | 3.523 | 0.943 | 0.637 |
| 6 | 0.8 | reitsma_indep | 3.649 | 0.940 | 0.672 |
| 6 | 0.8 | **adaptshrink_dta** | **4.095** | **0.955** | **1.044** |
| 6 | 0.8 | sep_univariate | 4.449 | 0.955 | 0.659 |
| 10 | 0.6 | reitsma_indep | 1.699 | 0.923 | 0.516 |
| 10 | 0.6 | reitsma | 1.745 | 0.933 | 0.495 |
| 10 | 0.6 | sep_univariate | 1.853 | 0.928 | 0.515 |
| 10 | 0.6 | **adaptshrink_dta** | **1.895** | **0.915** | **0.727** |
| 10 | 0.8 | reitsma | 2.077 | 0.953 | 0.562 |
| 10 | 0.8 | reitsma_indep | 2.112 | 0.938 | 0.593 |
| 10 | 0.8 | **adaptshrink_dta** | **2.273** | **0.918** | **0.832** |
| 10 | 0.8 | sep_univariate | 2.355 | 0.943 | 0.590 |

---

## Honest Null Finding

**AdaptShrink-DTA's ρ-shrinkage mechanism does not improve DTA meta-analysis efficiency
in any of the 64 tested (cell, strength) combinations across both grids.**

### Why it fails

The bivariate Reitsma model estimates a 2×2 covariance matrix Σ. The off-diagonal
entry is `ρ√(τ₁² · τ₂²)`, i.e., the between-study correlation in Se/Sp space.

AdaptShrink-DTA shrinks ρ̂ toward 0 with intensity δ(k, cond(Σ)). When true ρ ≠ 0:

1. The shrunk ρ misspecifies the GLS weighting used to combine studies.
2. The resulting estimator (Se, Sp) moves off the GLS optimum, increasing both
   bias and variance.
3. The reported uncertainty ellipse V = [v00, v01; v01, v11] reflects this
   misspecified model — the ellipse shape/area increases to accommodate
   the off-optimal estimation path.

When true ρ = 0 (e.g., focus-grid ρ=0.0 cells), shrinking toward 0 is near-correct
and the deficit is small (0.02–0.05 area units). But ρ=0 means no between-study
correlation — the scenario where ρ-shrinkage is least needed.

### What does work (subgroup wins)

- **`reitsma_indep`** (ρ fixed = 0): wins when k is small/sparse and ρ̂ from
  full bivariate model is noisy. This is parameter reduction (1 fewer parameter),
  not shrinkage.
- **`reitsma`**: wins in the majority of cells (36/48 focus, 7/32 hsroc-tail)
  by estimating ρ without constraint.

### What this means for AdaptShrink-DTA development

The current shrinkage formula targets ρ but should instead shrink τ² (or the
off-diagonal of Σ toward zero multiplicatively while keeping ρ implicit). A
precision-weighted shrinkage of Σ toward a diagonal Σ₀ = diag(τ₁², τ₂²) —
analogous to what AdaptShrink-NMA does in the univariate τ direction — may
recover the stabilization goal without misspecifying the estimating equations.
This reformulation is left for Phase-3.

---

## Summary

| grid | cells | adaptshrink_dta wins | reitsma wins | reitsma_indep wins |
|---|---|---|---|---|
| focus (k∈{6,10}, τ∈{0.6,0.8}, ρ∈{0,−0.6}) | 48 | **0** | 36 | 11 |
| hsroc-tail (sparse n_med=40, ρ=−0.6) | 32 | **0** | 7 | 9 |
| **total** | **80** | **0/80** | **43/80** | **20/80** |

**Honest bottom line:** The current AdaptShrink-DTA design does not transfer the
univariate AdaptShrink advantage into the bivariate DTA setting. ρ-shrinkage
inflates the GLS covariance ellipse when true ρ ≠ 0 and is redundant when true ρ = 0.
Standard bivariate Reitsma (ML, unconstrained ρ) is the recommended comparator for
DTA meta-analyses on the tested grids. Convergence is not an issue in Python
(100% even in sparse n_min=8 regime); the challenge is statistical efficiency, not
numerical stability.

---

*Simulation files: `dta_focus_focus_perrep.csv`, `dta_hsroc_hsroc_tail_perrep.csv`.*  
*Bakeoff script: `dta_bakeoff.py`.*
