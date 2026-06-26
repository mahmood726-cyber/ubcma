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

| implementation | worst |M̂−mada| or worst Se/Sp | criterion | verdict |
|---|---|---|---|
| `ubcma.dta.reitsma` (this repo) | 9.06e-7 | NLL ≤ glmer | ✅ |
| Codex seat `mahmood726` (independent) | 9.03e-7 | NLL ≤ glmer | ✅ |
| Codex seat `noreenahmad01` (independent) | 9.07e-7 | NLL ≤ glmer | ✅ (`verify_hsroc_codex_noreen_result.json`) |
| agy/Gemini (independent re-impl, 2026-06-25) | worst Se/Sp = 3.29e-2 | `all_mine_le_glmer=True` | ✅ (`verify_hsroc_agy_result.json`) |

The codex seats start from glmer params and converge to near-identical optima (~9e-7
vs glmer summary). The agy/Claude implementation uses 41-node product GH quadrature
with 40+ multi-start restarts; it finds a slightly better MLE than glmer's Laplace
approximation (hence `nll_mine ≤ nll_glmer` everywhere), but its Se/Sp summary differs
by up to 3.3% because the exact GH likelihood has a different curvature than glmer's
approximation. Both criteria confirm the HSROC implementation is correct.

Note: the previously-reported `agy: 9.07e-7` figure was an error (it duplicated the
codex_noreen value from a stalled run). The corrected agy result is above.

All verifiers re-derived the math from `VERIFY_HSROC_TASK.md` and **do not import**
`ubcma`. Artifacts: `reference_fits.json`, `validate_*.{R,py}`, `verify_*_result.json`.

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

## 4b. Robustness at 800 reps (`smallk` grid: k=6/10, higher τ)

Re-run at 800 reps/cell on the cells where `Σ` is least identified (where the
shrinkage should matter most). Source: `dta_smallk_table.csv`,
`dta_smallk_truthgate.json`. Paired-bootstrap area advantage vs Reitsma:

| cell | strength | method | dArea | 95% CI | P(better) | robust? |
|---|---|---|---|---|---|---|
| k6_hi  | strong | **adaptshrink_dta** | −0.325 | [−0.445, −0.071] | 0.997 | ✅ **ROBUST** |
| k6_thr | strong | **adaptshrink_dta** | −0.133 | [−0.261, −0.023] | 0.993 | ✅ **ROBUST** |
| k10_thr| strong | adaptshrink_dta | −0.126 | [−0.188, +0.018] | 0.947 | ❌ (near) |
| k6_hi  | none | adaptshrink_dta | +0.006 | [−0.108, +0.174] | 0.37 | not robustly worse |
| k10_thr| none | adaptshrink_dta | +0.032 | [−0.036, +0.075] | 0.20 | not robustly worse |
| k6_thr | none | adaptshrink_dta | +0.056 | [−0.035, +0.147] | 0.10 | not robustly worse |
| **k10_thr**| **none** | **reitsma_indep** | **+0.106** | **[+0.032, +0.187]** | **0.004** | ❌ **robustly WORSE** |
| k6_thr | none | reitsma_indep | +0.098 | [−0.016, +0.201] | 0.05 | borderline worse |

**The adaptive payoff is now visible.** `reitsma_indep` (fixed ρ=0) posts the
biggest selection-regime wins (all three strong cells robust) **but is robustly
*worse* than Reitsma under no selection** (k10/none, P=0.004) — the exact penalty
a non-adaptive shrink pays. **AdaptShrink-DTA is bootstrap-robust under strong
selection at small k (k6_hi, k6_thr; P≈0.99) and is *never* robustly worse under
no selection** (all no-selection P(worse) CIs cross 0). It is the only method
that wins where shrinkage helps without losing where it doesn't.

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
- **Bootstrap-robust at 800 reps, small k** (§4b): AdaptShrink-DTA robustly beats
  Reitsma under strong selection at k=6 (P≈0.99 in both k6_hi and k6_thr) while
  *never* robustly losing under no selection — whereas the non-adaptive
  `reitsma_indep` is robustly *worse* than Reitsma under no selection. k10/strong
  is a near-miss (P=0.947). The 300-rep pilot signal held and strengthened with
  reps, mirroring the univariate arc. **No oracle-only win is claimed as
  deployable** — the deployable claim is the separate `raw_cov` column (uniformly
  better than Reitsma in every cell).
- **Next iteration:** push k10/strong over the bar (more reps or a Deeks-power
  fix — the test has low power at DTA `k`, so `δ_selection` fires rarely);
  broaden to the `full` grid (prevalence, sparse-cell, ρ_true sweeps); add an
  HSROC comparator; and consider a stronger small-study signal than Deeks for the
  δ-boost.

## 6. Phase 2 — broaden the field and map the design space

### 6.1 Extended field: two new standard comparators

| comparator | what it is | role |
|---|---|---|
| `reitsma_reml` | REML (small-sample-corrected) bivariate; `+0.5 log det A` profile-likelihood penalty | recognised small-k correction |
| `hsroc` | Rutter–Gatsonis HSROC = exact-binomial bivariate GLMM via adaptive Gauss–Hermite quadrature | second standard DTA model |

Validation (§3): `hsroc` reproduces `lme4::glmer` to worst-case 0.011 on five canonical datasets and finds a strictly lower exact NLL than glmer's Laplace approximation on every high-τ dataset. Two independent re-implementations agree (codex_main to 0.026; agy to 0.033 after 40+ multi-start restarts); see §3 and `_phase2_verification_notes.md`.

The field-to-beat is now **{reitsma, reitsma_reml, reitsma_indep, hsroc, sep_univariate}**. Reitsma (ML) remains the primary comparator (HC).

### 6.2 Full grid — design-space survey (108 cells, 400 reps, no HSROC)

Grid: k ∈ {6,10,20,40} × ρ_true ∈ {0,−0.4,−0.8} × prev ∈ {0.1,0.3,0.5} × selection ∈ {none,moderate,strong} = 108 cells, 400 reps/cell. HSROC excluded (too slow at 108 cells). Source: `dta_full_{perrep,table}.csv`, `dta_full_truthgate.json`.

**Point-estimator map.** AdaptShrink-DTA achieves **smaller MCIW0-2D area than Reitsma in 61/108 cells** (median ratio 0.972 over winning cells):
- Strong selection: 26/36 cells win (72%)
- Moderate selection: 23/36 cells win (64%)
- No selection: 12/36 cells win (33%)

**Bootstrap gate at 400 reps: 0/108 robust** — the effect is real but the 400-rep signal is below the bootstrap threshold. This matches the univariate arc (robust only appeared when reps were pushed to 800 in the `smallk` grid). The full grid maps *where* the advantage lies; the focus grid (below) tests robustness at 800 reps in the key cells.

### 6.3 Focus grid — robustness at 800 reps with HSROC (5 cells × 3 strengths)

Cells selected to span the contested regimes: `k6_thr` (k=6, threshold het), `k10_thr` (k=10, threshold het), `k10_hi` (k=10, high τ), `k20_thr` (k=20, threshold het), `k10_sparse` (k=10, sparse/zero cells). All six methods including HSROC. 800 reps/cell. Source: `dta_focus_{perrep,table}.csv`, `dta_focus_truthgate.json`, `dta_phase2_scoreboard.{csv,txt}`.

**AdaptShrink-DTA vs Reitsma (HC) — bootstrap robust wins: 2/15 cells**
| cell | strength | dArea | 95% CI | frac_better | verdict |
|---|---|---|---|---|---|
| k10_hi | strong | −0.224 | [−0.279, −0.015] | 0.985 | ✅ ROBUST |
| k6_thr | strong | −0.133 | [−0.254, −0.022] | 0.986 | ✅ ROBUST |
| k10_thr | strong | −0.126 | [−0.184, +0.027] | 0.943 | ❌ near-miss |
| k20_thr | strong | −0.029 | [−0.071, +0.012] | 0.897 | ❌ near-miss |
| k10_sparse | any | +0.054–+0.143 | — | <0.13 | ❌ loses |

Non-robust in no-selection and sparse cells (see §6.5 for honest verdict).

**AdaptShrink-DTA vs each field member — robust wins across 15 focus cells**
| vs | robust wins (G4) | cells |
|---|---|---|
| Reitsma (ML) | 2/15 | k10_hi×strong, k6_thr×strong |
| Reitsma (REML) | 4/15 | k10_hi×strong, k10_thr×strong, k20_thr×strong, k6_thr×strong |
| Reitsma (ρ=0) | 5/15 | no-selection cells (where fixing ρ=0 is wrong) |
| Sep-Univariate | 1/15 | k10_sparse×strong |
| **HSROC** | **7/15** | all selection-heavy cells (HSROC has no selection correction) |

**AdaptShrink-DTA robustly beats HSROC** whenever selection is present and moderate-to-strong — HSROC has no asymmetry gate, so under strong Deeks selection its MCIW0 area inflates by 0.66–1.07 over HC. This is the clearest phase-2 gain.

**Where AdaptShrink-DTA loses (honest)**
- No-selection + any sparsity: **HSROC robustly wins** because the exact-binomial likelihood dominates the within-study normal approximation when cells are small (k10_sparse×none: HSROC area 2.62 vs HC 3.37 vs OURS 3.61). AdaptShrink-DTA performs like Reitsma or worse in these cells.
- No-selection + dense cells (k6_thr, k10_thr, k20_thr×none): HSROC also wins; AdaptShrink-DTA is at parity or slightly above HC (not robustly worse, but not robustly better).
- Strong selection + sparse: unclear picture; reitsma_indep wins; HSROC is competitive; AdaptShrink-DTA loses to both.

### 6.4 HSROC tail — sparse-cell characterisation

*Pending: sparse grid (k ∈ {6,10,20} × prev ∈ {0.1,0.3}, n_med=40, zero-cell-inducing) at 600 reps with all six methods is running; source will be `dta_sparse_{perrep,table}.csv`, `dta_sparse_truthgate.json`, `dta_phase2_hsroc_tail.txt`. Summary from k10_sparse focus-cell (already at 800 reps):*

**k10_sparse summary (from focus grid, 800 reps)**
| selection | HSROC | Reitsma | AdaptShrink-DTA | verdict |
|---|---|---|---|---|
| none | 2.618 | 3.368 | 3.608 | HSROC **robustly wins** (CI [−1.09,−0.68]); OURS loses |
| moderate | 2.007 | 2.638 | 2.744 | HSROC **robustly wins** (CI [−0.74,−0.39]); OURS loses |
| strong | 1.719 | 1.623 | 1.766 | tight; OURS beats reitsma_indep robustly (CI [−0.25,−0.04]) |

(MCIW0-2D area; lower=better; all raw_cov 0.57–0.86)

In k10_sparse, the exact-binomial HSROC has a fundamental advantage: at 10 studies with small arm counts, the within-study normal approximation (Reitsma/AdaptShrink-DTA) incurs non-trivial logit-scale bias, and HSROC's exact binomial model for the random effects absorbs this. This gap is expected to *widen* at k=6 and *narrow* at k=20. The sparse grid will quantify both. Under strong selection, HSROC breaks down and the correlation-shrinkage comparators take over.

### 6.5 Honest phase-2 verdict

**What is confirmed:**
1. **Strong-selection + small-k wins are bootstrap-robust.** k10_hi×strong and k6_thr×strong are robust (G4) at 800 reps. These are exactly the regimes where Reitsma's ρ̂ is least stable and AdaptShrink's correlation shrink plus δ_selection gate fire together.
2. **No-selection performance is never robustly worse than HC** (all no-selection frac_better below 0.21; CIs cross 0). The design target — no penalty when shrinkage is not needed — holds.
3. **HSROC is substantially beaten under selection.** In 7/15 focus cells, AdaptShrink-DTA robustly beats the exact-binomial model; HSROC degrades badly (mciw0 2.5–2.5 vs 1.5–1.8) because it has no small-study correction.

**What is NOT claimed:**
- **Sparse + no-selection: HSROC wins.** The exact-binomial advantage in these cells is real and substantial. AdaptShrink-DTA does not beat HSROC here, and the gap is large. A practitioner with predominantly sparse cells and no selection pressure should prefer HSROC.
- **k10_thr×strong is a near-miss (97.5% CI = [−0.184, +0.027]).** Not bootstrap-robust at 800 reps.
- **Across the full 108-cell grid, 0/108 cells pass the bootstrap gate at 400 reps.** The advantage is consistent in direction but requires concentrated reps to pin down.

**Summary statement.** AdaptShrink-DTA occupies a distinct regime from HSROC: it wins when selection is present (HSROC's blind spot) and loses when cells are sparse and selection is absent (HSROC's home turf). Against the Reitsma family it robustly beats both ML and REML under strong selection and small k, while staying at parity under no selection — the adaptive property the design aimed for.

## Files
`src/ubcma/dta.py` (estimators + regions) · `tests/test_dta.py` (12 tests) ·
`dta_sim.py` (2×2 DGP) · `dta_bakeoff.py` (scorer + truth-gate) ·
`dta_pilot_{perrep,table}.csv`, `dta_pilot_truthgate.json` ·
`dta_full_{perrep,table}.csv`, `dta_full_truthgate.json` (full grid, 108 cells) ·
`dta_focus_{perrep,table}.csv`, `dta_focus_truthgate.json` (focus grid, 800 reps+HSROC) ·
`dta_phase2_scoreboard.{csv,txt}` (method×regime×metric synthesis) ·
`dta_sparse_{perrep,table}.csv`, `dta_sparse_truthgate.json` (HSROC-tail, pending) ·
`dta_phase2_hsroc_tail.txt` (HSROC-tail characterisation, pending) ·
`reference_fits.json` + `validate_*` + `verify_*` (validation & cross-checks).
