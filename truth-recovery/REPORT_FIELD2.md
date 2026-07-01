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

## (c) result -- continuous HARD grid (c2: tau>=0.1, k in {5,40}, 51 scored cells)

Cells dominated (narrower-or-tied vs every valid comparator at matched coverage
AND near-nominal deployable coverage):

| method | dominated | loss-cells | tau=0.1 | tau=0.3 | tau=0.5 |
|---|---|---|---|---|---|
| adaptshrink_ens | 16 / 51 | 20 | 13/16 | 3/18 | 0/17 |
| adaptshrink_ens_calib | 19 / 51 | 20 | 14/16 | 5/18 | 0/17 |
| adaptshrink_petgate | 18 / 51 | 11 | 6/16 | 7/18 | 5/17 |
| **adaptshrink_auto** | **31 / 51** | **6** | **15/16** | **9/18** | **7/17** |
| adaptshrink_fast | 6 / 51 | 34 | - | - | - |

**The tau-aware `adaptshrink_auto` nearly DOUBLES plain ens (16 -> 31) and cuts
outright losses 20 -> 6 on this hard grid**, by combining ens_calib's low-tau
strength with petgate's high-tau strength. It essentially realizes the oracle
upper bound (a perfect per-cell selector between ens_calib and petgate would get
32/51). Crucially the per-replicate switching did NOT inject the noise that
sank iteration-2's gate -- because it switches between two GOOD estimators on a
STABLE signal (tau_hat), not toward a biased estimator on a noisy one.

### Why petgate works where iteration-2's gate failed
Iteration-2 gated on `|mu_ens - mu_re|`, which is inflated by heterogeneity, so it
misfired at high tau. petgate gates on the funnel-asymmetry t-statistic, whose
expectation is ~0 under no selection regardless of tau -- a genuinely tau-robust
selection detector. That is what lets `auto` recover the tau=0.5 corner
(0 -> 7/17) that no earlier variant could touch.

### Honest residual weaknesses of `adaptshrink_auto` (not hidden)
- The 6 remaining losses are **all step-selection cells**: 3 to `trim_and_fill`
  (the undeployable metric artifact -- its raw coverage is ~0.29) and 3 high-tau
  step k=40 cells to selection-MLEs / adaptshrink_fast where auto's deployable
  coverage is poor (0.20-0.53).
- **Deployable coverage cost:** auto's mean raw coverage is **0.843** (vs
  ens_calib 0.90+), because at high tau it uses petgate, which reverts to
  RE-style intervals that under-cover under residual selection, and because of
  the step-selection centre bias. So `auto` buys matched-coverage domination at
  some cost in out-of-the-box calibration -- a real tradeoff, logged.

## (b) result -- log-OR / binary outcome (l2: 2x2 tables, 30 scored cells)

mu{0,0.4,0.8} x tau{0.15,0.4} x k{10,40} x mech{none,step,copas}.

| method | dominated | loss-cells | tau=0.15 | tau=0.4 | mean deployable cov |
|---|---|---|---|---|---|
| adaptshrink_ens | 14 / 30 | 15 | 6/12 | 8/18 | 0.960 |
| adaptshrink_ens_calib | 15 / 30 | 15 | - | - | - |
| adaptshrink_fast | 15 / 30 | 14 | - | - | - |
| adaptshrink_petgate | 13 / 30 | 8 | 7/12 | 6/18 | 0.797 |
| **adaptshrink_auto** | **20 / 30** | 9 | **10/12** | **10/18** | **0.938** |

**`adaptshrink_auto` is the best variant on binary/log-OR outcomes too** (20/30 vs
14 for plain ens), and here it keeps strong deployable coverage (0.938). So the
tau-aware design transfers from continuous (SMD-like) to log-OR effect sizes --
the win is not an artifact of one effect metric. Its 9 remaining losses are again
dominated by the `trim_and_fill` metric artifact (5 copas-mechanism cells; tf is
undeployable) plus a couple of selection-MLE / fast-ensemble step cells.

## Bottom line so far

Avenue (c) is a **genuine, demonstrated improvement in the high-heterogeneity
regime, confirmed on two effect metrics**:
- continuous hard grid (tau>=0.1, k in {5,40}): `adaptshrink_auto` **31/51** vs 16
  for the plain ensemble (6 losses vs 20);
- log-OR / binary outcome: `adaptshrink_auto` **20/30** vs 14 (deployable coverage
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
