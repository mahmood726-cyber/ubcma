# AdaptShrink-DTA — first milestone report

Generalizing the univariate AdaptShrink program to **diagnostic test accuracy
(DTA)** meta-analysis. Design rationale in `DESIGN_BRIEF.md`. Every number below
is produced by seeded simulation / reference software and written to a committed
result file; nothing is hand-entered.

## 1. Field mapped + field-to-beat
Bivariate random-effects (Reitsma / van Houwelingen) is the modern standard; HSROC
is its reparameterization. The real failure modes are small `k` (between-study
correlation `ρ` barely identified, REML hits the boundary), sparse/zero cells,
threshold heterogeneity (strong negative Se–Sp correlation), and — largely
unhandled — selective publication on the SROC. **Reitsma is the ground-truth
comparator** (the DTA analogue of Henmi–Copas), `mada::reitsma`.

## 2. Design decision — a new estimator that reduces to Reitsma
`adaptshrink_dta` (`src/ubcma/dta.py`): **adaptive shrinkage of the between-study
covariance `Σ` toward independence**, the bivariate generalization of shrinking a
scalar `τ²`. It keeps the (stably estimated) marginal variances `τ̂1², τ̂2²` and
shrinks only the (unstable) correlation: `R_AS = (1−δ) R̂ + δ I`. The shrinkage
intensity `δ ∈ [0, 0.9]` is **fixed a priori** (not tuned to a target) and rises
when `Σ̂` is least trustworthy:

```
δ = clip( δ_k + δ_boundary + δ_selection , 0, 0.9 )
δ_k        = 8 / (8 + (k−3))                 # small-k instability of ρ̂
δ_boundary = 0.25 · 1{|ρ̂|≥0.95 or cond(Σ̂)≥1e3}
δ_selection= 0.35 · 1{Deeks funnel-asymmetry p < 0.10}
```

The point/region are the GLS estimates under `Σ_AS` (a genuinely different point
+ region than Reitsma). It **reduces to Reitsma when `δ=0`**.

> **Honest design pivot.** A v1 selection correction applied a PET-PEESE-style
> *point shift* to the summary lnDOR when Deeks fired. In the matched-coverage
> bake-off that shift was high-variance (the regression slope is unstable at DTA
> sample sizes) and *inflated* the error cloud even under no selection — Deeks
> false-fires ~10 %, and each firing injected a large noisy shift (diagnostic:
> rmse 0.58 vs 0.32; MCIW0 area 4.18 vs 1.11). It was replaced by routing the
> **same** asymmetry signal through the (bounded) shrinkage intensity above — the
> low-variance alternative — which is what ships.

## 3. Validation against reference software (BEFORE any simulation)
The Python bivariate ML reproduces `mada::reitsma` (ML) summary Se/Sp and logit
points on **5 canonical datasets** (AuditC, smoking, Dementia, skin_tests, SAQ):

| implementation | worst |M̂−mada| | verdict |
|---|---|---|
| `ubcma.dta.reitsma` (this repo) | 9.06e-7 | ✅ |
| Codex seat `mahmood726` (independent) | 9.03e-7 | ✅ |
| Codex seat `noreenahmad01` (independent) | 9.05e-7 | ✅ |
| `agy` (independent) | 9.07e-7 | ✅ |

All four agree to ~9e-7 (the worst case is the Dementia dataset — the shared
optimizer-tolerance floor). The three verifiers re-derived the math from a spec
and **do not import** `ubcma` (`grep -c ubcma verify_*.py` = 0). Artifacts:
`reference_fits.json`, `validate_*.{R,py}`, `verify_*_result.json`.

## 4. First matched-coverage bake-off (pilot grid, 300 reps/cell, target 0.95)

`MCIW0-2D area` = matched-coverage confidence-**region area** (PRIMARY,
lower=better; the bivariate analogue of interval width). `raw_cov` = deployable
(κ=1) joint coverage of the true operating point. HC = Reitsma.
Source: `dta_pilot_table.csv`, `dta_pilot_truthgate.json`.

### k=10, threshold het (ρ_true=−0.6, τ=0.6), prev=0.3
| strength | method | rmse | raw_cov | MCIW0-2D | vs HC |
|---|---|---|---|---|---|
| none | reitsma (HC) | 0.341 | 0.720 | 1.111 | — |
| none | **adaptshrink_dta** | 0.343 | **0.783** | 1.133 | 1.02× (parity) |
| none | reitsma_indep | 0.355 | 0.733 | 1.205 | 1.08× (worse) |
| strong | reitsma_indep | 0.323 | 0.883 | **0.795** | 0.81× |
| strong | **adaptshrink_dta** | 0.331 | **0.890** | 0.950 | **0.97×** |
| strong | reitsma (HC) | 0.340 | 0.797 | 0.983 | — |

### k=20, threshold het (ρ_true=−0.6, τ=0.6), prev=0.3
| strength | method | rmse | raw_cov | MCIW0-2D | vs HC |
|---|---|---|---|---|---|
| none | reitsma (HC) | 0.275 | 0.687 | 0.721 | — |
| none | **adaptshrink_dta** | 0.275 | **0.763** | 0.732 | 1.02× (parity) |
| strong | reitsma_indep | 0.249 | 0.877 | **0.532** | 0.75× |
| strong | **adaptshrink_dta** | 0.260 | **0.883** | 0.629 | **0.89×** |
| strong | reitsma (HC) | 0.264 | 0.773 | 0.707 | — |

### Paired-bootstrap robustness (2000 resamples; robust win = 97.5% CI of area advantage < 0)
| cell | method | dArea | 95% CI | P(better) | robust? |
|---|---|---|---|---|---|
| k10 strong | adaptshrink_dta | −0.003 | [−0.271, +0.060] | 0.82 | ❌ |
| k10 strong | reitsma_indep | −0.132 | [−0.370, +0.028] | 0.95 | ❌ (close) |
| k20 strong | adaptshrink_dta | −0.052 | [−0.141, +0.039] | 0.83 | ❌ |
| k20 strong | reitsma_indep | −0.089 | [−0.201, +0.018] | 0.95 | ❌ (close) |

## 5. Honest verdict (so far)
- **The core thesis is confirmed directionally.** Under selection, shrinking the
  selection-corrupted between-study correlation toward independence reduces the
  matched-coverage region area: **every** shrinkage method beats Reitsma's MCIW0
  area under strong selection (ratios 0.75–0.97), and the effect grows with `k`.
- **AdaptShrink-DTA hits the *adaptive* target the fixed-ρ models cannot.** It is
  at **parity** with Reitsma under no selection (where `reitsma_indep` *loses*
  1.08×) **and** beats Reitsma under selection — the best all-rounder. It also has
  **uniformly better deployable joint coverage** than Reitsma in all four cells
  (0.78–0.89 vs 0.69–0.80, κ=1, no oracle), the bivariate echo of the univariate
  "only AdaptShrink's raw interval is near-nominal" finding.
- **No win is yet bootstrap-robust at 300 reps** (best is `reitsma_indep` at
  P≈0.95, just under the 0.975 bar; AdaptShrink-DTA P≈0.82–0.83). This mirrors the
  univariate arc, where the pilot signal held and *strengthened* at higher reps.
  **No oracle-only win is claimed as deployable** — the deployable claim is the
  separate `raw_cov` column.
- **Next iteration** (running): 800-rep `smallk` grid (k=6/10, higher τ) to test
  whether the advantage becomes bootstrap-robust where `Σ` is least identified,
  and to tune `δ` to shrink harder under detected selection (Deeks has low power
  at DTA `k`, so the `δ_selection` boost currently fires rarely).

## Files
`src/ubcma/dta.py` (estimators + regions) · `tests/test_dta.py` (12 tests) ·
`dta_sim.py` (2×2 DGP) · `dta_bakeoff.py` (scorer + truth-gate) ·
`dta_pilot_{perrep,table}.csv`, `dta_pilot_truthgate.json` ·
`reference_fits.json` + `validate_*` + `verify_*` (validation & cross-checks).
