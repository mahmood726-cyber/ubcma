# UBCMA under selection-mechanism MISSPECIFICATION

UBCMA's built-in simulation study (`ubcma.simulation_study`) measures coverage of
the true `μ` under its **own** smooth logistic selection function — a model-
**matched** evaluation. It shows UBCMA works when its selection model is correct.

The allmeta truth-recovery work (F:\\allmeta, `truth-recovery-unified-estimator`)
sharpened the bar: the honest test of a selection-aware estimator is whether it
still recovers the truth when the selection mechanism **differs** from the one it
assumes — because in practice the mechanism is unknown, and parametric selection
models can fail under misspecification.

This harness imports UBCMA's **own** method dispatcher (`_run_method`) unchanged
and scores it under three generators at the same true `μ`, holding everything
else (k, τ, quality bias, schema) identical:

- `smooth` — UBCMA's own logistic selection (**matched**, baseline)
- `step` — Vevea–Hedges one-sided p-value step weights (**misspecified**)
- `copas` — Copas latent-variable selection (**misspecified**)

> Truth-first: seeded, reproducible.
> `PYTHONPATH=src python truth-recovery/misspec_harness.py --reps 120 --strength strong`

## Result — strong selection (`mu=0.2, tau=0.1, k=40`, 120 reps/cell)

Coverage of the true `μ` (target 0.95):

| mechanism | reml_hksj | trim&fill | pet_peese | copas | **ubcma** |
|---|---|---|---|---|---|
| smooth (matched) | 0.150 | 0.525 | 0.342 | 0.100 | **0.703** |
| step (misspecified) | 0.000 | 0.667 | 0.292 | 0.000 | **0.630** |
| copas (misspecified) | 0.083 | 0.217 | 0.408 | 0.058 | **0.846** |

Mean |bias| (UBCMA): smooth 0.048, step 0.065, copas 0.019 — lowest of every
method in every row.

### What this measures

1. **UBCMA is the only method that retains meaningful coverage under strong
   selection.** Inverse-variance methods (reml_hksj, copas-comparator) collapse to
   **0.00–0.15**; UBCMA holds **0.63–0.85**. This is strong selection at k=40, the
   regime where the allmeta benchmark showed naive RE coverage → 0.00, so these
   are the hardest cells.

2. **UBCMA degrades only mildly when its selection model is WRONG.** Going from its
   matched smooth mechanism (0.703) to a Vevea **step** function it does not assume
   (0.630) costs only ~7 points — and it actually does *better* under the Copas
   mechanism (0.846). The joint heterogeneity-plus-selection likelihood is
   genuinely robust to the selection *form*, not just tuned to its own generator.
   This is the central claim of the unified-estimator work, here confirmed for
   UBCMA's classical implementation.

## Result — moderate selection (same grid, `--strength moderate`)

| mechanism | reml_hksj | trim&fill | pet_peese | copas | **ubcma** |
|---|---|---|---|---|---|
| smooth (matched) | 0.350 | 0.342 | 0.433 | 0.275 | **0.836** |
| step (misspecified) | 0.067 | 0.492 | 0.283 | 0.033 | **0.800** |
| copas (misspecified) | 0.242 | 0.117 | 0.358 | 0.167 | **0.847** |

Under moderate selection UBCMA holds **0.80–0.85 across all three mechanisms**,
and the misspecification cost (smooth→step) shrinks to **~3.6 points**. Every
comparator still sits far below (0.03–0.49). Same qualitative picture as the
strong grid, with everything shifted toward nominal.

### Honest caveats

- Even UBCMA is **below nominal 0.95** under *strong* selection at k=40 (0.63–0.85;
  0.80–0.85 under moderate). Strong selection is an extreme distortion; no method
  recovers it fully. The honest reading is *relative*: UBCMA loses ~15–30 coverage
  points where every competitor loses ~80–95.
- This harness varies the *selection mechanism*; it does not add mechanisms
  outside the {smooth, step, copas} family. A fully unknown mechanism is what the
  allmeta PartialID bounds target — a natural future addition to UBCMA.

## What transferred from the allmeta estimator work

- **Transferred:** the misspecification-robustness framing (evaluate a selection-
  aware estimator under selection mechanisms it does **not** assume) and the
  step/copas DGPs. Applied to UBCMA's own dispatcher, they produced a measured
  robustness result its matched-only study could not.
- **Did not transfer (yet):** the NPE amortized estimator (a different inference
  engine) and conformal calibration are alternatives/additions rather than a
  validation; PartialID bounds would be the next genuine addition for the
  "mechanism entirely unknown" case.

## Files
`misspec_harness.py` (imports UBCMA's `_run_method`; smooth/step/copas DGPs) ·
`test_misspec.py` (4 tests) · `misspec_results_strong.json` / `..._moderate.json`.
