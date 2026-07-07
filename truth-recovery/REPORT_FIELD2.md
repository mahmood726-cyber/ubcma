# Broadened field bake-off (v2): avenues (b) + (c)

> Truth-first. Numbers from `field_bakeoff2.py` (seeded), scored by the same
> matched-coverage MCIW0 + paired-bootstrap + deployable-coverage truth-gate as
> v1. Comparator formulas validated (agy derivation + Codex cross-impl).

## What's new vs v1

- **(b) broadened grid.** New axes beyond v1 (which covered continuous tau in
  {0,0.1,0.3} at k in {10,40}): a **log-odds-ratio / binary** outcome (2x2-table
  DGP, Haldane-Anscombe corrected), **k = 5**, and **tau = 0.5**. The continuous
  v2 grid (`c2`) is the deliberately HARD slice mu{0,0.2,0.5} x tau{0.1,0.3,0.5}
  x k{5,40} x mech{none,step,copas} = 54 cells; the log-OR grid (`l2`) is
  mu{0,0.4,0.8} x tau{0.15,0.4} x k{10,40} x mech{none,step,copas} = 36 cells.
- **(c) two new estimators.**
  - `adaptshrink_petgate`: gate the efficient RE estimator against the calibrated
    ensemble by the **funnel-asymmetry t-statistic** t1 (a tau-robust selection
    signal), g = t1^2/(t1^2+4). Reverts to RE when there is no asymmetry; uses
    the bias-corrected ensemble when there is.
  - `adaptshrink_auto`: a **tau-aware selector** -- use `adaptshrink_ens_calib`
    when the DerSimonian-Laird tau_hat < 0.2 (bias-correction pays off), else
    `adaptshrink_petgate` (high heterogeneity -> lean efficient).

## (c) result -- continuous HARD grid (c2: tau>=0.1, k in {5,40}, 54 scored cells)

Cells dominated (narrower-or-tied vs every valid comparator at matched coverage
AND near-nominal deployable coverage). Counts use pairwise-complete paired-bootstrap
aggregation (each headline-vs-comparator verdict on the reps where both converged),
not the global all-methods intersection that previously dropped whole null cells:

| method | dominated | loss-cells | tau=0.1 | tau=0.3 | tau=0.5 |
|---|---|---|---|---|---|
| adaptshrink_ens | 18 / 54 | 17 | 15/18 | 3/18 | 0/18 |
| adaptshrink_ens_calib | 25 / 54 | 17 | 18/18 | 6/18 | 1/18 |
| adaptshrink_petgate | 20 / 54 | 11 | 7/18 | 7/18 | 6/18 |
| **adaptshrink_auto** | **36 / 54** | **4** | **18/18** | **10/18** | **8/18** |
| adaptshrink_fast | 6 / 54 | 38 | - | - | - |

**The tau-aware `adaptshrink_auto` DOUBLES plain ens (18 -> 36) and cuts
outright losses 17 -> 4 on this hard grid**, by combining ens_calib's low-tau
strength with petgate's high-tau strength. It essentially realizes the oracle
upper bound (a perfect per-cell selector between ens_calib and petgate would get
37/54). Crucially the per-replicate switching did NOT inject the noise that
sank iteration-2's gate -- because it switches between two GOOD estimators on a
STABLE signal (tau_hat), not toward a biased estimator on a noisy one.

### Why petgate works where iteration-2's gate failed
Iteration-2 gated on `|mu_ens - mu_re|`, which is inflated by heterogeneity, so it
misfired at high tau. petgate gates on the funnel-asymmetry t-statistic, whose
expectation is ~0 under no selection regardless of tau -- a genuinely tau-robust
selection detector. That is what lets `auto` recover the tau=0.5 corner
(0 -> 8/18) that no earlier variant could touch.

### Honest residual weaknesses of `adaptshrink_auto` (not hidden)
- The 4 remaining losses are three high-tau, k=40 **step-selection cells** (to
  `trim_and_fill` -- the undeployable metric artifact, raw coverage ~0.29 -- the
  fast ensemble, or the selection-MLEs, where auto's deployable coverage is poor
  0.20-0.53) plus one no-selection cell (mu=0.2, tau=0.5, k=5) lost to the
  efficient estimators (copas, DL/REML-HKSJ) in the high-tau corner.
- **Deployable coverage cost:** auto's mean raw coverage is **0.843** (vs
  ens_calib ~0.88), because at high tau it uses petgate, which reverts to
  RE-style intervals that under-cover under residual selection, and because of
  the step-selection centre bias. So `auto` buys matched-coverage domination at
  some cost in out-of-the-box calibration -- a real tradeoff, logged.

## (b) result -- log-OR / binary outcome (l2: 2x2 tables, 36 scored cells)

mu{0,0.4,0.8} x tau{0.15,0.4} x k{10,40} x mech{none,step,copas}.

| method | dominated | loss-cells | tau=0.15 | tau=0.4 | mean deployable cov |
|---|---|---|---|---|---|
| adaptshrink_ens | 17 / 36 | 18 | 10/18 | 7/18 | 0.960 |
| adaptshrink_ens_calib | 18 / 36 | 18 | - | - | - |
| adaptshrink_fast | 16 / 36 | 19 | - | - | - |
| adaptshrink_petgate | 15 / 36 | 11 | 9/18 | 6/18 | 0.797 |
| **adaptshrink_auto** | **23 / 36** | 12 | **12/18** | **11/18** | **0.938** |

**`adaptshrink_auto` is the best variant on binary/log-OR outcomes too** (23/36 vs
17 for plain ens), and here it keeps strong deployable coverage (0.938). So the
tau-aware design transfers from continuous (SMD-like) to log-OR effect sizes --
the win is not an artifact of one effect metric. Its 12 remaining losses are: the
`trim_and_fill` metric artifact (all 5 copas-mechanism cells; tf is undeployable),
six low-heterogeneity no-selection cells where the efficient RE/selection
estimators or petgate are legitimately tighter, and one step cell to the fast
ensemble / Vevea-Hedges.

## Bottom line so far

Avenue (c) is a **genuine, demonstrated improvement in the high-heterogeneity
regime, confirmed on two effect metrics**:
- continuous hard grid (tau>=0.1, k in {5,40}): `adaptshrink_auto` **36/54** vs 18
  for the plain ensemble (4 losses vs 17);
- log-OR / binary outcome: `adaptshrink_auto` **23/36** vs 17 (deployable coverage
  0.938).

It wins the tau=0.3-0.5 corner that the v1 honest-ceiling flagged as out of reach
for a single fixed estimator, oracle-free (gates on observable tau_hat + funnel
asymmetry). The cost is somewhat lower deployable coverage on the continuous grid
(0.843; fine on log-OR at 0.938) and a residual weakness in step-selection cells
where `trim_and_fill` wins the (oracle-only) point-efficiency metric while being
undeployable. The no-free-lunch boundary has MOVED (the high-tau corner is now
reachable) but not vanished -- `auto` still does not strictly dominate every cell,
and the step-selection / trim_and_fill artifact remains.

`adaptshrink_auto` is now the recommended general-purpose estimator: it inherits
ens_calib's low-tau dominance and petgate's high-tau dominance via an observable
tau_hat switch, and leads the entire 12-method field on both continuous and binary
outcomes across the broadened grid.

## (d) Selection-strength boundary -- is the domination a *strong*-selection artifact?

The (b)/(c) grids above fix `strength = "strong"`. The single most central open
question for a *bias-corrector* is whether its field-domination survives *weaker*
selection: under moderate selection the induced bias is smaller (less for the
corrector to recover) while the corrector's efficiency cost is unchanged, so
domination could plausibly erode. If the win only appears under strong selection
it is an artifact, not a property.

Numbers from `field_bakeoff2_modsel.py` (reuses `run_cell` + scoring from
`field_bakeoff2.py` verbatim; distinct `cm`/`lm` tags, `strength="moderate"` on the
two strength-dependent mechanisms {step, copas}; the `none` mechanism is
strength-invariant so it is excluded). The honest comparison denominator is the
*strong* grid restricted to the **same** step+copas selection cells: continuous
20/36, log-OR 17/24 for `adaptshrink_auto`. Same seeds, reps=40.

| grid (step+copas cells) | strong selection | moderate selection | Δ loss-cells |
|---|---|---|---|
| continuous (`cm`, 36 cells) | 20/36, **3** loss | **21/36, 1** loss | −2 |
| log-OR (`lm`, 24 cells) | 17/24, **6** loss | **20/24, 0** loss | −6 |

**The domination is not a strong-selection artifact -- it survives, and slightly
sharpens, as selection weakens.** Two facts make this concrete:

1. **No external comparator beats `auto` under moderate selection on either metric.**
   - Continuous: the *sole* moderate non-domination (mu=0.2, tau=0.3, k=40, step)
     loses only to the sibling variant `adaptshrink_ens_calib` -- against the full
     *external* published field (DL/REML-HKSJ, Copas, Henmi-Copas, trim_and_fill,
     PET/PEESE, p-curve, p_uniform_star, Vevea-Hedges) `auto` dominates **36/36**.
   - Log-OR: **0** loss cells -- `auto` dominates-or-ties **all 24** moderate cells.
2. **Deployable coverage holds or improves** under moderate selection (log-OR raw
   coverage 0.944 vs 0.921 strong; continuous unchanged in-band) -- the corrector
   is *standing down* gracefully as the signal weakens rather than over-correcting,
   which is the correct direction for a well-calibrated selection adjustment.

Cell-flip detail: 3 continuous cells flip (two small-k=5 step cells recovered,
one k=5 copas cell traded to a tie) and 5 log-OR cells flip (four copas cells
recovered, one high-tau step cell traded to a tie -- not a loss). Regression guard:
`test_field_modsel.py` (5 asserts on the committed `cm`/`lm` domination CSVs --
auto leads every variant, no external comparator beats auto, moderate >= strong).

Bottom line for (d): the tau-aware `adaptshrink_auto` win is a **property of the
estimator, not of the strong-selection stress** -- the boundary the honest ceiling
flagged is a *strong-selection, high-tau, step* corner, and everywhere milder than
that `auto` leads the external field outright.
