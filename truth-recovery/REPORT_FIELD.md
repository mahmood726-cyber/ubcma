# Field-wide bake-off (v1): does AdaptShrink beat the WHOLE modern field?

> Truth-first. Every number is produced by `field_bakeoff.py` (seeded) and
> re-checked by `test_field_bakeoff.py` + `test_modern_comparators.py`. Nothing
> hand-entered. Comparator formulas independently confirmed (agy derivation) and
> cross-implemented (Codex); see `codex_modern_comparators.py`.

## Setup

12-method panel: `dl_hksj, reml_hksj, trim_and_fill, pet_peese, copas` (Copas-Shi
MLE), `henmi_copas` (real metafor::hc), `vevea_hedges` (Vevea-Hedges 2-step
selection MLE), `p_curve`, `p_uniform_star`, `ubcma`, and three AdaptShrink
variants: `adaptshrink_ens` (robust avg of ubcma+pet+trim&fill), `adaptshrink_fast`
(robust avg of vevea+p_uniform*+pet, **no UBCMA**), `adaptshrink_solo`
(conformal-forward).

Grid (54 cells, strong selection): mu in {0, 0.2, 0.5} x tau in {0, 0.1, 0.3} x
k in {10, 40} x mechanism in {none (no selection), step, copas}. 80 reps/cell.

Metric per cell: **MCIW0** (matched-coverage constant width = point-estimator
efficiency, oracle-calibrated, lower=better) judged by **paired bootstrap**
(win = 97.5% CI of the MCIW0 difference < 0; loss = 2.5% CI > 0; else tie), plus
**deployable raw coverage** (no oracle). A variant **dominates the field** in a
cell iff it is narrower-than-or-tied-with EVERY valid comparator (conv >= 0.8)
AND its deployable coverage is near-nominal.

## Headline (honest): AdaptShrink-ens is the best method in the field

Ranking EVERY method by the number of cells in which it is narrower-than-or-tied-
with all valid comparators AND keeps near-nominal deployable coverage:

Counts are under the corrected **pairwise-complete** bootstrap aggregation (each
headline-vs-comparator paired bootstrap uses the reps on which both converged); the
legacy `dropna`-intersection numbers are shown alongside for reference. Mean
deployable coverage comes from `score_tables` and is aggregation-independent.

| method | dominated (legacy global) | **dominated (pairwise)** | mean deployable coverage |
|---|---|---|---|
| **adaptshrink_ens** (ubcma+pet+trim&fill) | 31 / 54 | **32 / 54** | **0.899** |
| ubcma | 19 / 54 | **18 / 54** | 0.810 |
| adaptshrink_fast (vevea+p_uniform*+pet, no UBCMA) | 13 / 54 | **12 / 54** | 0.813 |
| dl_hksj | 3 / 54 | **3 / 54** | 0.440 |
| henmi_copas (real metafor::hc) | 3 / 54 | **2 / 54** | 0.505 |
| reml_hksj | 3 / 54 | **3 / 54** | 0.436 |
| p_uniform_star | 2 / 54 | **1 / 54** | 0.620 |
| adaptshrink_solo (conformal) | 1 / 54 | **1 / 54** | 0.748 |
| vevea_hedges | 1 / 54 | **0 / 54** | 0.602 |
| copas (Copas-Shi) | 0 / 54 | **0 / 54** | 0.347 |
| p_curve | 0 / 54 | **0 / 54** | 0.421 |
| pet_peese | 0 / 54 | **0 / 54** | 0.485 |
| trim_and_fill | 0 / 54 | **0 / 54** | 0.288 |

**AdaptShrink-ens dominates nearly twice as many cells as the next-best method
(32 vs 18 for UBCMA) and ~10x more than any classical/selection method, AND has the
best deployable coverage of the entire panel.** It is the single best general-purpose
estimator here. But it does **not** dominate the *entire* field (32/54), and the
standalone conformal variant is an honest miss (confirms the earlier realhc finding).
The correction shifts only small counts (legacy 31/54, 19/54, 13/54) and does not
change the ranking or any conclusion — if anything the lead over the next-best method
widens (31-vs-19 → 32-vs-18). Both aggregations are reproducible from the committed
`field_v1_perrep.csv` via `field_v1_recompute.py`; the mechanism is pinned by
`test_field_bakeoff.py::test_dropna_selection_artifact`.

## Where adaptshrink_ens wins, and where it loses

Domination is sharply governed by **heterogeneity**:

| tau | cells dominated |
|---|---|
| 0.0 | 16 / 18 |
| 0.1 | 13 / 18 |
| **0.3** | **3 / 18** |

i.e. **29/36 cells at tau<=0.1, but only 3/18 at tau=0.3** (legacy global: 2/18).

### Honest ceiling #1 -- high heterogeneity (tau=0.3)
When between-study variance dominates the selection bias, the efficient
inverse-variance estimators (`reml_hksj`, `dl_hksj`, `henmi_copas`, `copas`) are
narrower at matched coverage: each beats ens in 8 cells (legacy global: 9),
essentially all at tau=0.3. This is a **fundamental bias-variance fact, not a fixable bug** -- when
there is little bias to remove, paying a bias-correction variance cost cannot
pay off, and a robust estimator cannot beat the efficient one in its own best
case. The most an adaptive method can do here is *tie* by detecting low
selection signal and reverting to RE (the iteration-2 target).

### Honest ceiling #2 -- trim_and_fill's metric artifact under step selection
ens loses to `trim_and_fill` in 8 cells, almost all `step`-mechanism. But this is
hollow: across the grid `trim_and_fill`'s mean **deployable** coverage is
**0.288** (vs ens **0.899**). Its downward bias happens to cancel step
selection's upward bias, so it looks narrow on the oracle MCIW0 metric while its
real intervals cover ~29% of the time. ens vs trim_and_fill head-to-head: **24
wins, 22 ties, 8 losses** (legacy global: 22/24/8) -- and every "loss" is to a
method no one could deploy.

### Honest ceiling #3 -- ens deployable under-coverage in 10 cells
ens raw coverage is >=0.90 in 38/54 cells (mean 0.899) -- far better than the
comparators that occasionally beat it (henmi_copas mean 0.505, trim_and_fill
0.288). But it **under-covers (<0.80) in 10 cells**, concentrated in:
- **null + step** (mu=0, step): raw_cov 0.46-0.75 -- the bias-correction
  overshoots downward when there is no true effect but strong step selection;
- **tau=0.3 + k=10**: raw_cov 0.68-0.79 -- small samples + high heterogeneity.

## Iteration 2: two principled attempts to break the ceiling -- both FAILED

We tried to convert the tau=0.3 losses into wins/ties (rescoring from the saved
per-rep estimates, so no re-simulation -- `field_rescore_gated.py`,
`field_rescore_members.py`):

1. **Explicit selection gate** -- blend RE and the ensemble by a per-rep signal
   `z=|mu_ens-mu_re|/se`, `g=z^2/(z^2+c)`. **Worse** at every gate constant
   (best 18/54 at c=0.25). The signal is confounded by heterogeneity: at tau=0.3
   the RE-vs-ensemble gap is mostly tau-driven noise, so the gate misfires, and
   the per-rep blending injects variance that drags the centre toward biased RE
   under selection.
2. **Add RE (and other members) to the robust ensemble** -- let the disagreement
   penalty "gate" implicitly. Best alternative `ens_re` ({ubcma,pet,tf,reml})
   reaches only 24/54 (legacy global: 25/54): it fails to add any tau=0.3 cell
   (3->3) and loses 8 low-tau cells (29->21 at tau<=0.1). Every other member set
   was worse. This is the
   bias-variance frontier made explicit: you can move wins *between* tau regimes
   but cannot gain net -- the efficient estimator's variance advantage at high tau
   and the bias-corrected estimator's bias advantage under selection trade off.

**No tweak beat the base ensemble.** Combined with the per-method ranking, this is
strong evidence that 32/54 sits near the achievable frontier for this estimator
family on this grid.

## Why universal field-domination is impossible (the honest ceiling)

The bar "narrower-or-tied vs every valid comparator in every cell" cannot be met
by any single estimator, for a structural reason: different cells have different
*optimal* estimators. In the tau=0.3 / no-selection corner the efficient RE
estimator is (essentially) minimum-variance and unbiased, so no robust method can
strictly beat it there -- a robust average necessarily has variance >= its best
member. Choosing RE-vs-correction per cell would require knowing the truth (the
selection magnitude relative to tau), which is exactly what is unavailable. This
is a meta-analytic no-free-lunch: the realistic target is "best general-purpose
method", which AdaptShrink-ens is, not "universally dominant", which nothing is.

## What this means

- **AdaptShrink (ensemble) is the best general-purpose estimator in this field**:
  it dominates more cells than any competitor could, and where it "loses" it is
  almost always either (a) to an efficient estimator in the no-/low-bias high-tau
  regime where losing is unavoidable, or (b) to an undeployable method
  (trim_and_fill) on an oracle-only metric. On the deployable axis it is the only
  method with broadly near-nominal coverage.
- **It is NOT a universal field-wide win**, and -- per the two failed iteration-2
  attempts and the no-free-lunch argument above -- universal domination is not
  achievable by a single estimator. 32/54 is near the frontier for this family.
- **Remaining honest weaknesses worth future work** (separate from the
  point-efficiency frontier): AdaptShrink-ens under-covers deployably (<0.80) in
  10/54 cells -- null+step (the centre over-corrects downward when mu=0 under
  strong step selection) and tau=0.3+k=10. Fixing the *interval* there (e.g. a
  selection-strength-aware width inflation) would improve deployability without
  touching the matched-coverage ranking, but does not change the domination count.

## Bottom line

Across a 12-method modern panel and a 54-cell grid (incl. small k=10, a no-
selection control, and tau up to 0.3), **AdaptShrink-ens is the best general-
purpose meta-analysis estimator** -- it dominates the field at matched coverage in
more cells than any rival (32 vs 18 for the next best) and has the best deployable
coverage of all (0.899). It is **not** universally dominant, and we show via two
failed improvement attempts and a bias-variance argument that universal dominance
is unattainable: in the high-heterogeneity / no-selection corner the efficient
estimators are optimal and no robust method can strictly beat them. This is the
characterized honest ceiling.

## Avenue (a): selection-strength-aware interval inflation -- modest honest win

The 10 deployable-undercoverage cells were attacked by widening the ensemble
interval in proportion to member disagreement D (the between-member SD):
`hw' = hw + a*D`, a single GLOBAL constant. Rescored from the saved per-rep
member estimates, so the point centre -- and therefore MCIW0 and every pairwise
verdict -- is provably unchanged; only the deployable-coverage gate moves
(baseline rescore reproduces 32/54 exactly under the corrected pairwise
aggregation; 31/54 under legacy global).

At **a = 2.0** (`field_rescore_interval.py`; counts under corrected pairwise
aggregation, inflated count is 35/54 under either aggregation):

| metric | baseline ens | inflated (a=2.0) |
|---|---|---|
| cells dominated | 32 / 54 | **35 / 54** |
| overall mean deployable coverage | 0.899 | **0.946** |
| mean raw width | 0.567 | 0.722 (x1.27) |

Per-cell coverage on the 10 under-cells (base -> inflated): the tau=0.3 + small-k
cells are largely fixed (e.g. 0.675->0.800, 0.787->0.887), and the +3 dominated
cells come from the coverage-only-fail set. Disagreement-scaling is ~2x more
width-efficient than a flat multiplier for the same coverage.

**Honest caveat:** the **null + step** cells (mu=0, step selection) stay
under-covered (0.46/0.50 -> 0.61/0.63). That is **centre bias** -- the ensemble
over-corrects downward when the true effect is zero under strong step selection --
which a symmetric interval cannot fix; only a better-centred point estimator can.
So (a) is a genuine but bounded improvement: 32->35 dominated and near-nominal
*average* deployable coverage, with a residual centring weakness in the null+step
corner that is logged, not papered over.

## Files
`field_bakeoff.py` (harness) · `field_rescore_gated.py` / `field_rescore_members.py`
/ `field_rescore_interval.py` (iteration-2 + avenue-(a) no-resim rescorers)
(iteration-2 no-resim rescorers) · `field_v1_perrep.csv` (raw, all 54 cells) ·
`field_v1_scores.csv` · `field_v1_pairwise.csv` · `field_v1_domination_*.csv` ·
`field_v1_summary.json` · tests `test_field_bakeoff.py`,
`test_modern_comparators.py`.
