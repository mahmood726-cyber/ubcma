# AdaptShrink: a τ-aware, selection-robust random-effects estimator for meta-analysis that moves the heterogeneity × publication-bias no-free-lunch boundary

**Mahmood Ahmad**¹²

¹ Royal Free Hospital, London, United Kingdom
² Tahir Heart Institute, Rabwah, Pakistan

ORCID: 0000-0001-9107-3704
Correspondence: Mahmood Ahmad (mahmood726@gmail.com)

**Competing interests.** The author is an honorary member of the editorial board of *Synthēsis* (former Editor-in-Chief) and had no role in the handling, peer review, or editorial decision-making for this manuscript; any submission would be handled independently by another editor of the journal.

**Funding.** None.

---

## Structured abstract

**Background.** Random-effects meta-analysis must contend with two largely orthogonal threats: between-study heterogeneity (τ) and publication/selection bias. Heterogeneity-only estimators (DerSimonian–Laird, REML, HKSJ) are efficient but inherit selection bias; selection-bias correctors (PET-PEESE, trim-and-fill, Copas/Henmi–Copas, p-uniform*, Vevea–Hedges) trade variance for bias reduction and each fails in a different region of the heterogeneity × selection plane. There is a meta-analytic no-free-lunch: no single fixed estimator is uniformly best, because the locally optimal estimator depends on the (unobservable) ratio of selection magnitude to τ.

**Methods.** We develop **AdaptShrink**, an oracle-free random-effects estimator, and its τ-aware variant **`adaptshrink_auto`**. The base estimator robustly model-averages a panel of *bias-corrected* members (UBCMA, PET-PEESE, trim-and-fill) with disagreement-penalised weights `w_j = 1/(se_j² + (μ_j − median μ)²)` and a model-averaging variance that widens automatically when members diverge. A calibrated variant inflates the interval by member disagreement. `adaptshrink_auto` switches on two *observable* signals: it uses the calibrated ensemble when the DerSimonian–Laird τ̂ < 0.2 (where bias correction pays off) and a funnel-asymmetry-gated estimator otherwise, with the gate driven by the small-study-effects t-statistic t₁ (a τ-robust selection detector). We evaluate every method under a **matched-coverage protocol**: each method is calibrated to 95% coverage, after which we compare the constant matched-coverage interval width MCIW0 (pure point-estimator efficiency) with a paired-bootstrap win criterion (97.5th percentile of the MCIW0 advantage below 0), alongside the deployable (no-oracle) coverage a practitioner actually obtains.

**Results.** Against a modern panel of up to 15 estimators (13–15 valid comparators per cell) across continuous (standardised-mean-difference-like) and binary/log-odds-ratio outcomes, k ∈ {5, 10, 40}, τ up to 0.5, and three selection mechanisms (none/step/Copas), `adaptshrink_auto` leads the field in **31/51 continuous cells** and **20/30 binary cells**, versus **16** and **14** for the plain ensemble. It recovers the high-heterogeneity corner that earlier work characterised as an honest ceiling (τ = 0.5: **0 → 7/17** continuous cells dominated). On a focused strong-selection comparison at k = 40, AdaptShrink reaches near-nominal deployable coverage (0.96–0.98) while needing 25–37% narrower matched-coverage intervals than the in-repo Henmi–Copas comparator, whose deployable coverage collapses to 0.00–0.08. Honest limitations: `adaptshrink_auto`'s mean deployable coverage eases to **0.843** on the hard continuous grid (0.938 on log-OR), and its residual losses are step-selection cells to trim-and-fill, which only "wins" the oracle point-efficiency metric while being undeployable (deployable coverage ≈ 0.29). The estimator does not strictly dominate every cell.

**Conclusions.** A τ-aware switch between a bias-corrected ensemble and a funnel-asymmetry-gated estimator, keyed on observable signals, demonstrably moves — but does not abolish — the heterogeneity × selection no-free-lunch boundary, on two effect metrics. `adaptshrink_auto` is a strong default general-purpose random-effects estimator when publication/selection bias cannot be ruled out, provided its eased deployable coverage at high τ is reported alongside the point estimate.

**Keywords:** meta-analysis; publication bias; selection models; heterogeneity; random-effects; robust estimation; matched-coverage efficiency.

---

## 1. Introduction

Meta-analysis aggregates study-level effect estimates into a pooled effect and an interval that is meant to support decision-making. Two threats to that interval are largely independent in origin but interact severely in practice. The first is **between-study heterogeneity**: real effect variation across studies, summarised by the between-study standard deviation τ. The second is **publication and selection bias**: the studies that reach the analyst are a non-random, effect-dependent subset of those conducted, so the observed effects are shifted away from the truth in a direction (usually upward in magnitude) and by an amount that depends on an unobserved selection mechanism.

The standard toolkit addresses these threats separately. **Heterogeneity-only** estimators — DerSimonian–Laird (DL), restricted maximum likelihood (REML), and their Hartung–Knapp–Sidik–Jonkman (HKSJ) interval refinements — model τ but assume the sample of studies is unbiased; under selection their inverse-variance centre is biased and their intervals, however well-calibrated for heterogeneity, under-cover the true effect. **Selection-bias correctors** take the opposite stance. Trim-and-fill imputes "missing" studies from funnel asymmetry; PET-PEESE regresses the effect on its standard error and extrapolates to infinite precision; Copas-type selection models (and the robust Henmi–Copas interval) posit a latent selection process; p-uniform* and p-curve exploit the distribution of significant p-values; Vevea–Hedges fits a step-function selection weight. Each removes some bias at a variance cost, and — crucially — each is built around a *specific* selection model and therefore fails, sometimes badly, when the true mechanism differs.

The result is a **meta-analytic no-free-lunch**. In a corner of the parameter space where heterogeneity dominates and selection is mild, the efficient inverse-variance estimator is essentially minimum-variance and unbiased, and no bias-correcting estimator can strictly beat it there: paying a bias-correction variance premium when there is little bias to remove cannot pay off, and a robust average necessarily has variance no smaller than its best member. In the opposite corner — strong selection, modest heterogeneity — the efficient estimator is sharply biased and any reasonable bias corrector dominates it. Because the locally optimal estimator depends on the ratio of selection magnitude to τ, and that ratio is not observable, **no single fixed estimator can be uniformly best**. Choosing per-analysis would require knowing the truth.

This motivates an *adaptive* estimator that detects, from observable signals, which regime it is in. The contribution of this paper is threefold:

1. **AdaptShrink** — an oracle-free robust model-average of *bias-corrected* members, with disagreement-penalised weights and a model-averaging variance that widens automatically when the panel disagrees (i.e. when selection is severe).
2. **`adaptshrink_auto`** — a τ-aware selector that switches between a calibrated AdaptShrink ensemble (low heterogeneity, where bias correction pays) and a funnel-asymmetry-gated estimator (high heterogeneity, where it leans toward the efficient estimator), keyed on the *observable* DL τ̂ and the small-study-effects t-statistic.
3. A **matched-coverage evaluation protocol** that compares methods fairly by first calibrating each to the same coverage, then comparing interval width with a paired-bootstrap win criterion, while separately reporting the deployable (no-oracle) coverage.

We show that this adaptive design demonstrably *moves* the no-free-lunch boundary — it reclaims the high-heterogeneity corner that a fixed ensemble cannot — without claiming to abolish it, and we are explicit about where and why it still loses.

## 2. Methods

### 2.1 The bias-corrected ensemble

AdaptShrink does not observe the truth. It begins from the empirical observation, established in the accompanying simulation work, that under strong selection misspecification the naive random-effects centre and Copas-type selection MLEs are biased upward (bias ≈ +0.10–0.15), trim-and-fill is biased downward (≈ −0.06), while PET-PEESE (≈ +0.06) and UBCMA (≈ +0.02) sit closer to the truth. Because the errors of the *bias-corrected* members partly straddle the truth, a robust weighted combination can have both lower bias (opposing biases partly cancel) and lower variance (averaging partly independent errors) than any single member.

Let the default panel be the bias-corrected members $\{\text{UBCMA},\ \text{PET-PEESE},\ \text{trim-and-fill}\}$, each contributing a point estimate $\mu_j$ and standard error $se_j$. The naive RE and Copas members are deliberately **excluded** from the default panel: under selection they share the same upward bias and would simply out-vote the corrections. AdaptShrink forms the robust median $m = \mathrm{median}_j\,\mu_j$ and the **disagreement-penalised** weights

$$ w_j = \frac{1}{se_j^2 + (\mu_j - m)^2}, \qquad \hat\mu_{\mathrm{AS}} = \frac{\sum_j w_j \mu_j}{\sum_j w_j}. $$

This down-weights both noisy members (large $se_j$) and outlying members (large disagreement) — exactly the behaviour wanted when one member's selection model is misspecified. The interval uses a **model-averaging variance** that adds the within-member sampling variance of the weighted mean to the between-member spread (a Burnham–Anderson-style decomposition),

$$ \widehat{\mathrm{Var}}(\hat\mu_{\mathrm{AS}}) = \underbrace{\frac{\sum_j w_j^2 se_j^2}{(\sum_j w_j)^2}}_{\text{within}} + \underbrace{\frac{\sum_j w_j (\mu_j - \hat\mu_{\mathrm{AS}})^2}{\sum_j w_j}}_{\text{between}}, $$

so the between-member term widens the interval automatically when the panel disagrees, i.e. when selection is severe and the members diverge. The half-width is $\kappa\, t_{n-1,\,0.975}\,\sqrt{\widehat{\mathrm{Var}}}$ where $n$ is the number of surviving members and $\kappa$ is a single, transparent calibration multiplier ($\kappa = 1$ for the raw model-averaging interval). Nothing is tuned to a target number: the member set and weighting rule are fixed a priori. (Source: `src/ubcma/adaptshrink.py`.)

### 2.2 The calibrated ensemble (`adaptshrink_ens_calib`)

The raw ensemble interval can deployably under-cover in a minority of cells. A no-resimulation analysis showed that widening the half-width in proportion to member disagreement $D$ (the between-member standard deviation), $hw' = hw + a\,D$ with a single global constant $a = 2.0$, is roughly twice as width-efficient as a flat multiplier for the same coverage. The calibrated ensemble keeps the AdaptShrink centre unchanged — so the matched-coverage point-efficiency metric and every pairwise verdict are provably unaffected — and only moves the deployable interval. On the original 54-cell strong-selection grid this raised the number of dominated cells from 31 to 35 and lifted mean deployable coverage from 0.899 to 0.946 at a 1.27× width cost. (Source: `truth-recovery/REPORT_FIELD.md`; `field_rescore_interval.py`; commit `82b73e9`.)

### 2.3 The funnel-asymmetry (PET) gate (`adaptshrink_petgate`)

For the high-heterogeneity regime we want to *lean toward the efficient estimator* unless there is genuine evidence of small-study effects. The detector is the **funnel-asymmetry t-statistic** $t_1$ from the PET regression of the effect on its standard error: its expectation is approximately 0 under no selection *regardless of τ*, which is precisely what makes it a τ-robust selection signal (unlike the difference $|\hat\mu_{\mathrm{ens}} - \hat\mu_{\mathrm{RE}}|$, which is inflated by heterogeneity and misfires at high τ). The gate weight is

$$ g = \frac{t_1^2}{t_1^2 + c}, \qquad c = 4 \ \ (|t_1| = 2 \Rightarrow g = 0.5), $$

and the estimator blends the efficient REML-HKSJ estimator with the calibrated ensemble in both centre and half-width:

$$ \hat\mu_{\mathrm{pg}} = (1-g)\,\hat\mu_{\mathrm{RE}} + g\,\hat\mu_{\mathrm{ens}}, \qquad hw_{\mathrm{pg}} = (1-g)\,hw_{\mathrm{RE}} + g\,(hw_{\mathrm{ens}} + a\,D). $$

When there is no asymmetry it reverts to RE; when asymmetry is strong it uses the bias-corrected ensemble. (Source: `truth-recovery/field_bakeoff2.py`.)

### 2.4 The τ-aware auto selector (`adaptshrink_auto`)

The two regimes are reconciled by a selector keyed on the **observable** DerSimonian–Laird heterogeneity estimate:

$$ \texttt{adaptshrink\_auto} = \begin{cases} \texttt{adaptshrink\_ens\_calib} & \text{if } \hat\tau_{\mathrm{DL}} < \tau_0 = 0.2 \ \text{(low heterogeneity: bias correction pays)} \\ \texttt{adaptshrink\_petgate} & \text{otherwise (high heterogeneity: lean efficient).} \end{cases} $$

Crucially the switch is between **two good estimators on a stable signal** ($\hat\tau_{\mathrm{DL}}$), not toward a biased estimator on a noisy one. This is why the per-analysis switching does not inject the variance that sank an earlier per-replicate gating attempt (which gated on $|\hat\mu_{\mathrm{ens}} - \hat\mu_{\mathrm{RE}}|$ and was beaten at every constant). (Source: `truth-recovery/field_bakeoff2.py`; `REPORT_FIELD2.md`.)

### 2.5 The matched-coverage evaluation protocol

Comparing raw interval widths across methods is unfair when the methods have wildly different coverage — a method can look "narrow" only because it under-covers. We therefore put every method on the same coverage footing first. For each (mechanism, method) the replicates are split by index parity into disjoint **calibration** and **test** halves. The primary metric is the **constant matched-coverage width**

$$ \mathrm{MCIW0} = 2c,\quad c = \text{the }0.95\text{-quantile of } |\hat\mu - \mu_{\mathrm{true}}| \text{ on the calibration half}, $$

with $\text{test\_cov} = P(|\hat\mu - \mu_{\mathrm{true}}| \le c)$ on the held-out half. MCIW0 isolates point-estimator efficiency (tail error) with no interval-modelling confound; the true $\mu$ is used **only** to calibrate the width, so this is an efficiency statement, not a deployable interval. A secondary metric (MCIW) instead rescales each method's own per-replicate interval to hit the target on calibration, rewarding informative, difficulty-tracking uncertainty.

A method is credited with a win over a comparator **only** when a three-part truth gate passes: (G1) every scored replicate has a finite estimate and interval (no fabricated rows); (G3) the winner's MCIW0 is below the comparator's and its constant-width calibration still covers on the held-out test half ($|\text{test\_cov} − 0.95| \le 0.06$); and (G4, decisive) a **paired bootstrap** over replicates (2000 resamples, errors paired across methods within a mechanism) places the 97.5th percentile of the MCIW0 advantage below 0 — i.e. the win survives resampling. Separately, and most importantly for practice, we report **deployable raw coverage**: the no-oracle ($\kappa = 1$) coverage a practitioner actually obtains. A method **dominates the field** in a cell iff it is narrower-than-or-tied-with every valid comparator (convergence ≥ 0.8) at matched coverage **and** its deployable coverage is near-nominal. (Sources: `truth-recovery/matched_coverage_bakeoff.py`, `field_bakeoff.py`, `REPORT_MATCHED_COVERAGE.md`.)

## 3. Simulation study

**Comparator panel.** The full panel comprises up to 15 estimators, with 13–15 valid comparators per cell after convergence filtering: `dl_hksj`, `reml_hksj`, `trim_and_fill`, `pet_peese`, `copas` (the Copas–Shi selection MLE), `henmi_copas` (a direct port of `metafor::hc`, validated to 2 × 10⁻⁸ against metafor v5.0-1), `vevea_hedges` (two-step selection MLE), `p_curve`, `p_uniform_star`, `ubcma`, and the AdaptShrink family (`adaptshrink_solo` conformal, `adaptshrink_ens`, `adaptshrink_fast`, `adaptshrink_ens_calib`, `adaptshrink_petgate`, `adaptshrink_auto`). Comparator formulas were independently confirmed by a symbolic derivation pass and cross-implemented in a second codebase (`truth-recovery/codex_modern_comparators.py`). (Source: `truth-recovery/field_bakeoff.py`, `REPORT_FIELD.md`.)

> **A note on nomenclature.** The `copas` comparator is the Copas–Shi (2000) selection MLE, not the Henmi–Copas (2010) robust interval; the genuine Henmi–Copas method is the separately validated `henmi_copas` port. In the focused matched-coverage comparison (§4.1) the `copas` row is used as the reference; the field-domination analyses (§4.2–4.4) include both `copas` and `henmi_copas` as distinct comparators.

**Data-generating processes.** Continuous (SMD-like) outcomes are generated by the misspecification harness with a quality-dependent internal-bias term; binary outcomes use a fresh 2×2-table binomial DGP (group sizes drawn in [20, 200], control risk in [0.1, 0.5]) with Haldane–Anscombe 0.5 continuity correction, yielding log-odds-ratio effects. Three **selection mechanisms** are applied: `none` (no selection control), `step` (a Vevea–Hedges step-function on the z-score, deliberately misspecified relative to the smooth model), and `copas` (a latent-variable Copas mechanism, also misspecified). A `smooth` mechanism matched to UBCMA's own selection model is used in the focused comparison. Selection strength is `strong` (the headline grids) or `moderate`.

**Grids.** Three grids are reported. (i) The **focused matched-coverage** grid (§4.1): μ = 0.2, τ = 0.1, k = 40, 300 replicates per cell, mechanisms {smooth, step, copas}, at both strong and moderate strength. (ii) The **original field grid v1** (§4.2): μ ∈ {0, 0.2, 0.5} × τ ∈ {0, 0.1, 0.3} × k ∈ {10, 40} × mechanism ∈ {none, step, copas} = 54 cells, 80 reps/cell, strong selection. (iii) The **broadened grids v2** (§4.3–4.4): a deliberately hard continuous slice (`c2`) μ ∈ {0, 0.2, 0.5} × τ ∈ {0.1, 0.3, 0.5} × k ∈ {5, 40} × mechanism ∈ {none, step, copas} = 54 cells (51 scored), and a log-OR slice (`l2`) μ ∈ {0, 0.4, 0.8} × τ ∈ {0.15, 0.4} × k ∈ {10, 40} × mechanism ∈ {none, step, copas} = 36 cells (30 scored), 40 reps/cell. Everything is seeded and reproducible (§7). (Sources: `truth-recovery/field_bakeoff.py`, `field_bakeoff2.py`, `misspec_harness.py`.)

## 4. Results

### 4.1 Matched-coverage efficiency against Henmi–Copas (focused grid)

Under strong selection (μ = 0.2, τ = 0.1, k = 40, 300 reps), AdaptShrink achieves near-nominal **deployable** coverage in all three mechanisms (smooth 0.967, step 0.960, Copas 0.977) while needing substantially narrower matched-coverage intervals than the reference. Its MCIW0 is 0.2526 (smooth), 0.2568 (step) and 0.2194 (Copas), versus the `copas`/Henmi–Copas reference at 0.3731, 0.4055 and 0.2915 — width ratios of 0.677, 0.633 and 0.753, i.e. the reference needs roughly 25–37% wider intervals to reach the same coverage. The reason is bias: the reference's point estimate is biased by 0.099–0.146 under selection, against AdaptShrink's 0.014–0.053. The reference's *deployable* coverage, in contrast, collapses to 0.083 (smooth), 0.003 (step) and 0.070 (Copas) (Figure 4; Table 1). The advantage is paired-bootstrap robust in all three mechanisms (97.5% CI of the MCIW0 advantage below 0) under both strong and moderate selection — 6/6 cells. (Source: `truth-recovery/mc_strong_table.csv`, `REPORT_MATCHED_COVERAGE.md`.)

The companion estimator UBCMA wins the matched-coverage metric too (MCIW0 ratios 0.70–0.78) but its raw interval under-covers (0.65–0.83) and would need recalibration; AdaptShrink is the only method that delivers both the efficiency *and* near-nominal off-the-shelf coverage. trim-and-fill posts the smallest MCIW0 under smooth/step but only because its downward bias happens to cancel selection's upward bias there; under the Copas mechanism that cancellation reverses and it is no better than — or worse than — the reference, and its deployable coverage is poor throughout (0.187–0.600). It cannot be trusted as a general selection-robust estimator.

### 4.2 Field domination on the original grid (v1)

Ranking every method by the number of 54 strong-selection cells in which it is narrower-than-or-tied-with all valid comparators at matched coverage **and** keeps near-nominal deployable coverage, the base ensemble `adaptshrink_ens` leads with **31/54** dominated cells and the best mean deployable coverage of the entire panel (**0.899**). The next best is UBCMA at 19/54 (0.810); `adaptshrink_fast` 13/54; every classical or selection method reaches at most 3/54 (`dl_hksj`, `henmi_copas`, `reml_hksj` each 3/54, mean deployable coverage 0.44–0.51); trim-and-fill dominates 0/54 with mean deployable coverage **0.288**. (Source: `truth-recovery/REPORT_FIELD.md`, `field_v1_*`.)

Domination on this grid is sharply governed by heterogeneity: the base ensemble dominates 16/18 cells at τ = 0, 13/18 at τ = 0.1, but only **2/18 at τ = 0.3**. This is the **honest ceiling**: in the high-heterogeneity / low-selection corner the efficient inverse-variance estimators are essentially optimal and no robust average can strictly beat them. Two principled attempts to break it without re-simulation — an explicit per-replicate selection gate and the addition of RE to the ensemble — both failed (best alternatives 18/54 and 25/54 respectively): they moved wins between τ regimes but could not gain net, exactly as the bias–variance argument predicts.

### 4.3 The broadened grid and the τ-aware selector (continuous)

On the deliberately hard continuous grid (τ ≥ 0.1, k ∈ {5, 40}, 51 scored cells), the τ-aware **`adaptshrink_auto` dominates 31/51 cells with only 6 outright losses**, versus 16/51 (20 losses) for the plain ensemble, 19/51 for the calibrated ensemble, and 18/51 for the PET-gated estimator alone (Figure 1; Table 2). Stratified by heterogeneity (Figure 2):

| τ | ens | ens_calib | petgate | **auto** |
|---|---|---|---|---|
| 0.1 | 13/16 | 14/16 | 6/16 | **15/16** |
| 0.3 | 3/18 | 5/18 | 7/18 | **9/18** |
| 0.5 | 0/17 | 0/17 | 5/17 | **7/17** |

`adaptshrink_auto` combines the calibrated ensemble's low-τ strength with the PET-gate's high-τ strength and **recovers the τ = 0.5 corner that no fixed variant could touch (0 → 7/17)** — the corner that the v1 ceiling flagged as out of reach. It essentially realises the oracle upper bound: a perfect per-cell selector between `ens_calib` and `petgate` would reach 32/51. This is why the τ-robust funnel-asymmetry signal matters: it lets `auto` detect selection at high τ without being fooled by heterogeneity. (Source: `truth-recovery/field2_c2_summary.json`, `field2_c2_domination_*.csv`, `REPORT_FIELD2.md`.)

### 4.4 Transfer to binary / log-odds-ratio outcomes

On the log-OR grid (30 scored cells), `adaptshrink_auto` is again the best variant: **20/30 dominated** versus 14/30 for the plain ensemble, 15/30 for the calibrated ensemble and `adaptshrink_fast`, and 13/30 for the PET-gate (Figure 1). Stratified, it dominates 10/12 cells at τ = 0.15 and 10/18 at τ = 0.4, and here it retains strong mean deployable coverage (**0.938**). The τ-aware design therefore transfers from continuous SMD-like effects to log-OR effects — the win is not an artefact of one effect metric. (Source: `truth-recovery/field2_l2_summary.json`, `field2_l2_domination_*.csv`.)

### 4.5 Deployable coverage and honest limitations

The per-cell verdict map for `adaptshrink_auto` on the continuous grid (Figure 3) makes the residual weaknesses explicit. Its mean deployable coverage on this hard grid eases to **0.843** (vs 0.90+ for the calibrated ensemble), because at high τ it uses the PET-gate, which reverts toward RE-style intervals that under-cover under residual selection, and because of a centre bias in the null + step corner. The six remaining continuous losses are **all step-selection cells**: three to trim-and-fill (the undeployable metric artefact, deployable coverage ≈ 0.29) and three high-τ, k = 40 step cells to selection-MLEs or the fast ensemble where `auto`'s own deployable coverage is poor (0.20–0.53). The nine binary losses are likewise dominated by the trim-and-fill artefact (five Copas-mechanism cells) plus a few selection-MLE / fast-ensemble cells. `adaptshrink_auto` **buys matched-coverage domination at some cost in out-of-the-box calibration on the hardest continuous cells** — a real trade-off, logged rather than hidden. It does not strictly dominate every cell, and universal domination is provably unattainable for a single estimator (§6).

## 5. Worked example: aspirin secondary prevention

We illustrate the estimator on the classic six-trial aspirin secondary-prevention dataset (CDP, AMIS, ISIS-2, UK-TIA, SALT, ESPS-2; log-odds-ratio scale; `examples/verde_2021_aspirin.csv`), a real dataset known for substantial heterogeneity (the large, precise ISIS-2 trial is an outlier). The numbers below were computed by running the committed estimators on the committed data (`manuscript/worked_example.py`); they are code-and-data-derived rather than drawn from a results CSV, and are reproducible.

The observable signals are τ̂_DL = 0.140 (so τ̂ < τ₀ = 0.2 and the auto selector picks the calibrated ensemble) and a funnel-asymmetry statistic t₁ = 2.94 (significant small-study asymmetry, gate weight g = 0.68). The estimators disagree exactly as the no-free-lunch picture predicts (Figure 5; Table 3): the heterogeneity-only estimators report a near-null effect (DL-HKSJ −0.067 [−0.235, +0.101]; REML-HKSJ −0.072 [−0.208, +0.064]), UBCMA is essentially null (+0.012 [−0.125, +0.118]), while the bias-correcting members react to the funnel asymmetry and report a protective effect (PET-PEESE −0.227 [−0.285, −0.168]; trim-and-fill −0.251 [−0.288, −0.214]). AdaptShrink-auto pools the bias-corrected members to **−0.237 [−0.417, −0.056]** — a protective log-OR with an interval widened (relative to the raw ensemble −0.237 [−0.368, −0.105]) by member disagreement, reflecting the genuine ambiguity about whether the asymmetry is selection or the ISIS-2 outlier. This example is a methods illustration of the estimator's mechanism, not a clinical re-appraisal: it shows transparently how `adaptshrink_auto` resolves a real disagreement between heterogeneity-only and selection-aware estimators, and why its interval is appropriately wide when they conflict.

## 6. Discussion

**What moved the boundary.** The v1 analysis characterised an honest ceiling: a single fixed ensemble could not win the high-heterogeneity corner, and two natural fixes failed. The advance here is not a better single estimator but an *observable* switch. Two facts make it work. First, the switching signal is stable: DL τ̂ is a low-variance, model-light estimate, so conditioning on it does not inject the per-replicate noise that sank earlier gating. Second, the within-regime selection detector is τ-robust: the funnel-asymmetry t-statistic has expectation ≈ 0 under no selection irrespective of τ, so at high τ the PET-gate does not mistake heterogeneity for selection. Together these let `auto` reach 31/51 (continuous) and 20/30 (binary), recovering the τ = 0.5 corner (0 → 7/17). The no-free-lunch boundary has **moved** — the high-τ corner is now reachable oracle-free — but it has **not vanished**.

**Why universal domination remains impossible.** The bar "narrower-or-tied versus every valid comparator in every cell" cannot be met by any single estimator, for a structural reason. In the high-τ, no-selection corner the efficient RE estimator is (essentially) minimum-variance and unbiased, so any robust average — whose variance is bounded below by its best member's — cannot strictly beat it. Choosing RE-versus-correction per cell with certainty would require knowing the selection magnitude relative to τ, which is exactly what is unavailable. `adaptshrink_auto` approximates that oracle choice from observable signals; it cannot equal it. The realistic target is therefore "best general-purpose method", which `auto` is on these grids, not "universally dominant", which nothing is.

**Honest limitations.** Three are worth restating. (i) **Eased deployable coverage:** on the hard continuous grid `auto`'s mean deployable coverage is 0.843 (0.938 on log-OR). At high τ, where it uses the PET-gate, its off-the-shelf interval can under-cover under residual selection; users at high heterogeneity should treat the interval as somewhat optimistic and report τ̂ alongside. (ii) **The trim-and-fill metric artefact:** several of `auto`'s "losses" are to trim-and-fill on the oracle MCIW0 metric in step/Copas cells. This is hollow — trim-and-fill's deployable coverage is ≈ 0.29; its downward bias coincidentally cancels selection's upward bias in those cells, so it looks narrow on an oracle metric while its real intervals cover under a third of the time. It is not a deployable competitor. (iii) **Null + step centre bias:** when the true effect is zero under strong step selection, the bias correction over-corrects downward; a symmetric interval cannot repair this, and only a better-centred point estimator would. These are characterised, not papered over.

**A second real dataset — magnesium/MI, an adversarial boundary.** We also ran the estimator on the classic magnesium-for-myocardial-infarction meta-analysis (`metadat::dat.li2007`, `examples/li2007_magnesium.csv`; `truth-recovery/magnesium_realtest.py`), which has a rare *external ground truth*: after 20 small trials suggested a large mortality benefit, the ISIS-4 (N=58,050) and MAGIC (N=6,213) mega-trials found essentially no effect (pooled log-OR +0.05, OR 1.05). Pooling the 20 small trials and asking each estimator to move the spurious benefit (naive DL OR 0.61) back toward that truth is a demanding real-data test, and we report it honestly. **No corrector reaches the mega-trial null** — the magnesium small-study effect is famously more than publication selection (clinical-era and quality confounding), so it is adversarial for any funnel-based method. AdaptShrink-*solo* moves in the right direction (+26 % closer, OR 0.70) but is not the closest; PET-PEESE is (+34 %, OR 0.73) — on a single k = 20 funnel PET has enough studies to behave, in contrast to its instability on the few-studies-per-contrast networks where it fails badly. The AdaptShrink *ensemble* under-moves here (+4 %) because two members (trim-and-fill, Vevea–Hedges) misfire on this dataset and dilute PET's correct pull: robust averaging is only as safe as the majority of its members, so on an adversarial case AdaptShrink-solo is preferable. This is a boundary, not a win — a non-selection bias defeats all funnel correctors, and the ensemble's safety is contingent on member agreement.

**When to use it.** `adaptshrink_auto` is a sensible default when publication or selection bias cannot be ruled out and the analyst wants a single estimator that behaves well across the heterogeneity spectrum, on either SMD-like or log-OR effects. When heterogeneity is known to be low and selection plausible, the calibrated ensemble is marginally preferable for deployable coverage; when heterogeneity is high and selection implausible, an efficient REML-HKSJ analysis is appropriate and `auto` will (by design) lean toward it. The matched-coverage protocol itself is a reusable contribution: it is the fair way to compare estimators that differ in coverage, and we recommend reporting MCIW0 and deployable coverage together.

**Relation to prior work.** AdaptShrink is an aggregation layer over existing correctors rather than a new selection model; it is closest in spirit to model-averaging and to robust combination of estimators, but specialised to the bias structure of publication selection. It does not require external information (unlike identifiable Copas models) and does not assume a specific selection function (unlike Vevea–Hedges or p-uniform*). Its cost is that it inherits its members' failure modes when *all* members fail in the same direction (the null + step corner).

## 7. Reproducibility

All quantitative claims derive from committed, seeded result files on branch `truth-recovery-misspec` of the repository (commit `b908caf`). Key artefacts:

- **Estimator:** `src/ubcma/adaptshrink.py` (base ensemble); `truth-recovery/field_bakeoff2.py` (calibrated ensemble, PET-gate, τ-aware auto selector). Henmi–Copas port and validation: `src/ubcma/robust_methods.py`, `truth-recovery/validate_henmi_copas.R`, `hc_reference.json`.
- **Matched-coverage protocol & truth gate:** `truth-recovery/matched_coverage_bakeoff.py`, `field_bakeoff.py`; reproduce with `bash truth-recovery/reproduce_matched_coverage.sh`.
- **Result files (numbers in this paper):** focused matched-coverage — `mc_strong_table.csv`, `mc_strong_truthgate.json`, `REPORT_MATCHED_COVERAGE.md`; field grid v1 — `field_v1_*`, `REPORT_FIELD.md`; broadened grids v2 — `field2_c2_*` (continuous), `field2_l2_*` (log-OR), `field2_*_summary.json`, `REPORT_FIELD2.md`.
- **Tests / truth gate:** `tests/test_adaptshrink.py`, `truth-recovery/test_matched_coverage.py`, `test_field_bakeoff.py`, `test_modern_comparators.py`.
- **Worked example:** `examples/verde_2021_aspirin.csv` (real data; provenance in `examples/DATA_PROVENANCE.md`); recompute with `python manuscript/worked_example.py` → `manuscript/worked_example.json`.
- **Figures:** regenerate with `python manuscript/make_figures.py` (reads only the committed CSV/JSON sources above).

The win criterion is conservative by construction: a win is credited only when finite-output (G1), held-out matched-coverage validity (G3), and a paired-bootstrap 97.5%-CI sign test (G4) all pass.

---

## Figures

**Figure 1.** Field-domination at matched coverage by AdaptShrink variant, on the continuous (SMD, 51 scored cells) and binary/log-OR (30 scored cells) grids. The τ-aware `auto` selector leads every variant (31/51 and 20/30). *(`fig1_variant_dominance.png`)*

**Figure 2.** Cells dominated stratified by heterogeneity τ on the continuous grid. The plain ensemble dominates 0/17 cells at τ = 0.5; `adaptshrink_auto` recovers 7/17, moving the high-τ no-free-lunch boundary. *(`fig2_tau_frontier.png`)*

**Figure 3.** Per-cell verdict map for `adaptshrink_auto` on the continuous grid (rows: μ × τ; columns: k × mechanism). Green = dominates field; amber = narrower/tied at matched coverage but deployable coverage < 0.90; red = loses ≥ 1 comparator. Cell text is the deployable coverage. *(`fig3_auto_heatmap.png`)*

**Figure 4.** Matched-coverage efficiency (MCIW0, lower = better) versus deployable coverage (text labels) by mechanism, strong selection, μ = 0.2, τ = 0.1, k = 40, 300 reps. AdaptShrink (blue) is both efficient and near-nominally covering; the other methods under-cover. *(`fig4_matched_coverage.png`)*

**Figure 5.** Worked example: aspirin secondary-prevention forest plot (k = 6, real data). Individual studies (top) and pooled estimates from each method (bottom); `adaptshrink_auto` in blue. τ̂_DL = 0.140 (< τ₀, so auto selects the calibrated ensemble); funnel-asymmetry t₁ = 2.94. *(`fig5_aspirin_forest.png`)*

## Tables

**Table 1.** Focused matched-coverage comparison, strong selection (μ = 0.2, τ = 0.1, k = 40, 300 reps); deployable coverage (raw_cov), MCIW0, and MCIW0 ratio vs the Henmi–Copas reference, by mechanism. Source: `mc_strong_table.csv`.

| Mechanism | Method | bias | deployable cov | MCIW0 | ratio vs HC |
|---|---|---|---|---|---|
| smooth | AdaptShrink | 0.030 | 0.967 | 0.2526 | 0.677 |
| smooth | UBCMA | 0.045 | 0.765 | 0.2852 | 0.764 |
| smooth | trim-and-fill | −0.028 | 0.477 | 0.2451 | 0.657 |
| smooth | Copas–Shi (HC) | 0.123 | 0.083 | 0.3731 | — |
| smooth | REML-HKSJ | 0.124 | 0.120 | 0.3745 | 1.004 |
| step | AdaptShrink | 0.053 | 0.960 | 0.2568 | 0.633 |
| step | trim-and-fill | 0.010 | 0.600 | 0.1709 | 0.421 |
| step | Copas–Shi (HC) | 0.146 | 0.003 | 0.4055 | — |
| copas | AdaptShrink | 0.014 | 0.977 | 0.2194 | 0.753 |
| copas | UBCMA | 0.021 | 0.828 | 0.2046 | 0.702 |
| copas | Copas–Shi (HC) | 0.099 | 0.070 | 0.2915 | — |

**Table 2.** Cells dominated (and outright losses) by AdaptShrink variant on the broadened grids, with τ stratification (continuous) and mean deployable coverage. Sources: `field2_c2_summary.json`, `field2_l2_summary.json`, `field2_*_domination_*.csv`, `field2_*_scores.csv`.

| Variant | Continuous 51 (τ0.1 / 0.3 / 0.5) | Binary 30 (τ0.15 / 0.4) | mean deployable cov (cont / bin) |
|---|---|---|---|
| ens | 16 (13 / 3 / 0) | 14 (6 / 8) | 0.899* / 0.956 |
| ens_calib | 19 (14 / 5 / 0) | 15 (6 / 9) | — / 0.980 |
| petgate | 18 (6 / 7 / 5) | 13 (7 / 6) | — / 0.795 |
| **auto** | **31 (15 / 9 / 7)** | **20 (10 / 10)** | **0.843 / 0.938** |

\* ens mean deployable coverage 0.899 is for the v1 strong grid; the v2 per-variant continuous means are reported per cell in `field2_c2_scores.csv`.

**Table 3.** Worked example (aspirin, k = 6, log-OR): pooled estimates and 95% intervals. Computed by `manuscript/worked_example.py` from committed code and data. Source: `manuscript/worked_example.json`.

| Method | μ̂ (log-OR) | 95% CI |
|---|---|---|
| DerSimonian–Laird (HKSJ) | −0.067 | [−0.235, +0.101] |
| REML (HKSJ) | −0.072 | [−0.208, +0.064] |
| PET-PEESE | −0.227 | [−0.285, −0.168] |
| Trim-and-fill | −0.251 | [−0.288, −0.214] |
| Copas–Shi | −0.074 | [−0.171, +0.023] |
| Henmi–Copas (`metafor::hc`) | −0.154 | [−0.396, +0.089] |
| UBCMA | +0.012 | [−0.125, +0.118] |
| AdaptShrink petgate | −0.185 | [−0.351, −0.018] |
| AdaptShrink ens_calib | −0.237 | [−0.417, −0.056] |
| **AdaptShrink auto** | **−0.237** | **[−0.417, −0.056]** |

τ̂_DL = 0.140; funnel-asymmetry t₁ = 2.94; PET-gate weight g = 0.68; auto selection = calibrated ensemble (τ̂ < 0.2).
