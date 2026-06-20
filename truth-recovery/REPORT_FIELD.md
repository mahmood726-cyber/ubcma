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

## Headline (honest)

| AdaptShrink variant | cells dominated | cells with >=1 loss |
|---|---|---|
| **adaptshrink_ens** (UBCMA-based) | **31 / 54** | 18 |
| adaptshrink_fast (no UBCMA) | 13 / 54 | 34 |
| adaptshrink_solo (conformal) | 1 / 54 | 52 |

**No AdaptShrink variant dominates the entire field.** The UBCMA-based ensemble
is clearly the strongest and dominates a majority of cells; the standalone
conformal variant is an honest miss (confirms the earlier realhc finding).

## Where adaptshrink_ens wins, and where it loses

Domination is sharply governed by **heterogeneity**:

| tau | cells dominated |
|---|---|
| 0.0 | 16 / 18 |
| 0.1 | 13 / 18 |
| **0.3** | **2 / 18** |

i.e. **29/36 cells at tau<=0.1, but only 2/18 at tau=0.3.**

### Honest ceiling #1 -- high heterogeneity (tau=0.3)
When between-study variance dominates the selection bias, the efficient
inverse-variance estimators (`reml_hksj`, `dl_hksj`, `henmi_copas`, `copas`) are
narrower at matched coverage: each beats ens in 9 cells, essentially all at
tau=0.3. This is a **fundamental bias-variance fact, not a fixable bug** -- when
there is little bias to remove, paying a bias-correction variance cost cannot
pay off, and a robust estimator cannot beat the efficient one in its own best
case. The most an adaptive method can do here is *tie* by detecting low
selection signal and reverting to RE (the iteration-2 target).

### Honest ceiling #2 -- trim_and_fill's metric artifact under step selection
ens loses to `trim_and_fill` in 8 cells, almost all `step`-mechanism. But this is
hollow: across the grid `trim_and_fill`'s mean **deployable** coverage is
**0.288** (vs ens **0.899**). Its downward bias happens to cancel step
selection's upward bias, so it looks narrow on the oracle MCIW0 metric while its
real intervals cover ~29% of the time. ens vs trim_and_fill head-to-head: **22
wins, 24 ties, 8 losses** -- and every "loss" is to a method no one could deploy.

### Honest ceiling #3 -- ens deployable under-coverage in 10 cells
ens raw coverage is >=0.90 in 38/54 cells (mean 0.899) -- far better than the
comparators that occasionally beat it (henmi_copas mean 0.505, trim_and_fill
0.288). But it **under-covers (<0.80) in 10 cells**, concentrated in:
- **null + step** (mu=0, step): raw_cov 0.46-0.75 -- the bias-correction
  overshoots downward when there is no true effect but strong step selection;
- **tau=0.3 + k=10**: raw_cov 0.68-0.79 -- small samples + high heterogeneity.

## What this means

- **AdaptShrink (ensemble) is the best general-purpose estimator in this field**:
  it dominates more cells than any competitor could, and where it "loses" it is
  almost always either (a) to an efficient estimator in the no-/low-bias high-tau
  regime where losing is unavoidable, or (b) to an undeployable method
  (trim_and_fill) on an oracle-only metric. On the deployable axis it is the only
  method with broadly near-nominal coverage.
- **It is NOT a universal field-wide win.** The strict bar ("narrower-or-tied vs
  every valid comparator in every cell") is not met, and likely cannot be in the
  tau=0.3 no-selection corner.
- **Clear iteration-2 target**: make the ensemble *heterogeneity-aware* -- detect
  when selection signal is weak relative to tau and revert toward the efficient
  RE estimator, to (i) recover ties in the tau=0.3 cells and (ii) fix the
  null+step deployable under-coverage. That would convert losses into ties and
  push domination well above 31/54 without sacrificing the selection-regime wins.

## Files
`field_bakeoff.py` (harness) · `field_v1_perrep.csv` (raw, all 54 cells) ·
`field_v1_scores.csv` · `field_v1_pairwise.csv` · `field_v1_domination_*.csv` ·
`field_v1_summary.json` · tests `test_field_bakeoff.py`,
`test_modern_comparators.py`.
