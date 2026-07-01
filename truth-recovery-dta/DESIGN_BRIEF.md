# AdaptShrink-DTA — design brief

Generalize the univariate AdaptShrink program (`src/ubcma/adaptshrink.py`,
`truth-recovery/REPORT_MATCHED_COVERAGE.md`) to **diagnostic test accuracy (DTA)
meta-analysis**, inheriting the same truth-first discipline: matched-coverage
bake-off, paired-bootstrap truth-gate, no oracle-only wins claimed as deployable,
every number traceable to a committed result file.

---

## 1. The modern DTA field to beat

A DTA meta-analysis pools per-study 2×2 tables (TP, FP, FN, TN). On the logit
scale each study contributes `y1 = logit(Se)`, `y2 = logit(Sp)` with within-study
variances `s1² ≈ 1/TP + 1/FN`, `s2² ≈ 1/TN + 1/FP` and **zero within-study
covariance** (diseased and non-diseased groups are independent).

| model | what it estimates | standard ref | role here |
|---|---|---|---|
| **Bivariate random-effects (Reitsma)** | `(M1,M2)` summary logit-Se/Sp + between-study `Σ=[[τ1²,ρτ1τ2],[ρτ1τ2,τ2²]]` via ML/REML of `N(M, Σ+S_i)` | Reitsma 2005; van Houwelingen 1993 | **primary field-to-beat** (`mada::reitsma`) |
| **HSROC** | accuracy/threshold/shape; reparam of bivariate | Rutter–Gatsonis 2001 | equivalent to bivariate w/o covariates (Harbord 2007) |
| **Riley overall-correlation / bivariate-with-ρ-fixed** | bivariate with ρ stabilized (often → 0) | Riley 2007 | small-k stabilizer; one comparator |
| **Separate univariate** | pool logit-Se and logit-Sp independently (ρ≡0) | naive | lower-bound comparator |
| **Multiple-thresholds / sparse-cell corrections** | continuity correction, exact within-study | various | feature of the generator, not a pooled model here |

### Real failure modes (the targets)
1. **Few studies (k small).** `Σ` — especially `ρ` — is barely identified; REML
   routinely returns `ρ̂ = ±1` (boundary) or fails to converge. This noise in
   `ρ̂` propagates into the GLS weights and inflates the variance of `(M̂1,M̂2)`.
2. **Sparse / zero cells.** `logit` undefined; the 0.5 continuity correction
   biases Se/Sp toward 0.5 and shrinks within-study variance.
3. **Between-study correlation poorly estimated** (the #1 instability) → unstable
   SROC and summary-point covariance.
4. **Threshold variability** across studies induces strong *negative* Se–Sp
   correlation; if `Σ` is mis-estimated the summary point is biased.
5. **Selective publication / small-study effects on the SROC** — *largely
   unhandled* in DTA (no established Copas/PET-PEESE analogue for the bivariate
   summary). A study with unimpressive accuracy (low DOR, small N) is less likely
   to be published; this biases the summary operating point.

---

## 2. AdaptShrink-DTA — the design decision

**Decision: a genuinely new estimator, not a cosmetic variant — but one that
reduces *exactly* to Reitsma in its trust-REML limit (`δ=0`, no asymmetry).**
Justification from the failure-mode analysis: the univariate win came from
(a) shrinking an unstable scalar `τ̂²` and (b) a funnel-asymmetry-gated selection
correction. The DTA analogues require new machinery that Reitsma does not have:

### (a) Adaptive shrinkage of the between-study covariance `Σ` (generalizes τ²-shrink)
Replace the scalar `τ̂²` shrink with a **structured shrinkage of the bivariate
`Σ̂`** toward a stable target:

```
Σ_AS = D^{1/2} · [ (1−δ) R̂ + δ R_T ] · D^{1/2}        D = diag(τ̂1², τ̂2²)
```

- `R̂` = REML between-study correlation matrix; `R_T` = structured target.
  Primary target `R_T = I` (independence — the Riley/`mada` small-sample
  stabilizer; directly attacks failure mode #3). A threshold-aware negative-`ρ`
  target is a documented variant.
- The marginal between-study variances `τ̂1², τ̂2²` are kept (they are estimated
  far more stably than `ρ̂`); only the **correlation** — the unstable quantity —
  is shrunk. This is the precise bivariate generalization of "shrink the unstable
  between-study scale."

### (b) Condition/`k`-gated shrinkage intensity `δ` (generalizes the τ̂-switch)
`δ ∈ [0, δ_max]` is **fixed a priori** (never tuned to a target), increasing when
`Σ̂` is least trustworthy:

```
δ = clip( δ_k + δ_boundary , 0, δ_max )
δ_k        = κ0 / (κ0 + (k − 3))          # small-k → more shrink; →0 as k grows
δ_boundary = b · 1{ |ρ̂| ≥ 0.95  or  cond(Σ̂) ≥ C }   # boundary/ill-conditioned ρ̂
```

with `κ0=8, b=0.25, δ_max=0.9, C=1e3` set a priori. At `k=40`, `δ_k≈0.18`; at
`k=8`, `δ_k≈0.62`; on a boundary `ρ̂` a further `+0.25`. The summary point and its
covariance are then the GLS estimates **using `Σ_AS`** (different weights → a
genuinely different point + region than Reitsma).

### (c) Deeks-asymmetry-gated SROC selection correction (generalizes the funnel gate)
The univariate funnel-asymmetry gate becomes a **Deeks' funnel asymmetry test**
on `lnDOR` vs `1/√(effective sample size)`. If asymmetry is detected (slope
p < `p_gate`), apply a regression-based small-study correction to the summary
`lnDOR` (a PET-PEESE analogue on the diagnostic odds ratio), projected back onto
the summary operating point along the SROC. If not detected, the correction is
the identity — so under no selection AdaptShrink-DTA = shrunk-Reitsma, and under
large-`k`-no-selection it = Reitsma. This addresses failure mode #5, which the
field leaves open.

---

## 3. Matched-coverage DTA bake-off (MCIW0 generalized to the bivariate region)

Univariate MCIW0 matched the coverage of a scalar interval then compared width.
The bivariate analogue matches the **joint coverage of the summary operating
point `(M1,M2)`** then compares **confidence-region area** (the direct efficiency
analogue; smaller area at matched coverage = more efficient).

For each (cell, method), split replicates into calib/test by rep-parity:

- **MCIW0-2D (primary, point-estimator efficiency, constant region).**
  Let `e_i = (M̂1−M1, M̂2−M2)`. On calib compute `W=cov(e)`, Mahalanobis radii
  `d_i² = e_iᵀ W⁻¹ e_i`, and `q = T-quantile(d²)`. Region = `{e: eᵀW⁻¹e ≤ q}`,
  **area = π·q·√det(W)**. Test coverage = fraction of test `e` inside; lower area
  at matched test coverage wins. (No width-model confound — isolates the error
  cloud, exactly like the 1-D MCIW0.)
- **MCIW-2D (secondary).** Scale each method's *own* 95% ellipse by `κ` to hit
  `T` on calib; compare ellipse area on test. Rewards informative, difficulty-
  tracking uncertainty.
- **Deployable (raw, κ=1).** The method's actual joint coverage and area — the
  no-oracle claim a practitioner gets.

**Truth-gate (same spine as univariate):**
- **G1** every scored replicate has a finite `(M̂1,M̂2)` and a finite, positive-
  definite region (no fabricated rows; PD-fail rows counted, excluded, reported).
- **G2/G3** a win requires MCIW0-2D area below Reitsma's *and* the winner's
  constant-region calibration to generalize on test (`|test_cov − T| ≤ tol`).
- **G4 (decisive)** a **paired bootstrap** over replicates puts the 97.5th
  percentile of the (method − Reitsma) area advantage **below 0**.

Reitsma is the ground-truth comparator (the DTA analogue of Henmi–Copas).

### Simulation grid
`k ∈ {6, 10, 20, 40}` · prevalence `∈ {0.1, 0.3, 0.5}` · threshold heterogeneity
(ρ_true `∈ {0, −0.4, −0.8}`, `τ ∈ {low, high}`) · `Σ` structure · selection
strength `∈ {none, moderate, strong}` (Deeks-style suppression of low-DOR/small-N
studies). Sparse-cell cells force small per-arm `n` so zero cells arise.

---

## 4. Validation (before trusting any simulation number)
Reproduce published summary estimates with `mada::reitsma` (installed: 0.5.12)
and `metafor::rma.mv` on canonical datasets (Glas telomerase; `mada`'s
`AuditC`/`smetelomerase`) — the in-repo Python bivariate likelihood must agree
with `mada::reitsma` to ~1e-3 on `(M1,M2)` and the summary Se/Sp, and the GLS
covariance to comparable tolerance, **before** the estimator is trusted in
simulation. Independent cross-implementation by Codex (both seats) and agy of the
estimator math, checked to ~1e-6 against the reference packages.

---

## 5. Files
- `src/ubcma/dta.py` — bivariate likelihood, `reitsma`, `reitsma_indep`,
  `sep_univariate`, `adaptshrink_dta`, region utilities.
- `truth-recovery-dta/dta_sim.py` — 2×2 generator (bivariate logit-normal `Σ`,
  prevalence, threshold het, sparse cells, Deeks selection).
- `truth-recovery-dta/dta_bakeoff.py` — matched-coverage region bake-off +
  truth-gate + paired bootstrap.
- `truth-recovery-dta/validate_*.R` / `.py` — reference-package validation.
- `tests/test_dta.py` — estimator unit + region PD + calibration tests.
