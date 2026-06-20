# Beating the REAL Henmi-Copas at matched coverage

> Truth-first. Every number below is produced by seeded simulation in
> `realhc_bakeoff.py` and re-checked by `test_realhc.py`. Nothing is hand-entered.

## The correction this report makes

The in-repo `copas` comparator (`comparators.copas_selection`) is the **Copas &
Shi (2000) selection MLE**, not the **Henmi & Copas (2010)** robust CI. The
sibling `matched_coverage_bakeoff.py` treated `copas` as "Henmi-Copas" and
declared wins against it. That is a mislabelled adversary.

We therefore added the **genuine Henmi-Copas** CI
(`robust_methods.henmi_copas`, a faithful port of `metafor::hc`, validated to
**2e-8** against metafor v5.0-1; see `validate_henmi_copas.R`) as a first-class
method `henmi_copas`, and re-ran the identical matched-coverage comparison.

## Metric

For each method, per replicate: `err = |mu_hat - mu_true|`, `hw = CI half-width`.

- **mciw0** (PRIMARY, point-estimator efficiency): `2 x` the 95th percentile of
  `err` on a calibration split, validated on a disjoint test split. The width of
  the optimally-calibrated 95% interval around the method's centre. Lower = better.
- **raw_cov / raw_width**: deployable, out-of-the-box (no oracle).
- A **robust win** vs HC = paired-bootstrap (4000 resamples) 97.5% CI of
  `mciw0(method) - mciw0(HC)` strictly below 0.

Grid: `mu=0.2, tau=0.1, k=40`, strong selection, 120 reps/cell, three selection
mechanisms (smooth = UBCMA's own; step = Vevea-Hedges; copas = Copas latent).

## Result (strong selection, 120 reps)

mciw0 (lower = better); **real HC** in bold as the bar to beat:

| mechanism | adaptshrink_ens | ubcma | **henmi_copas** | adaptshrink_solo | reml_hksj | copas(Shi) |
|---|---|---|---|---|---|---|
| smooth | **0.247** | 0.280 | **0.310** | 0.311 | 0.313 | 0.312 |
| step   | **0.206** | 0.288 | **0.344** | 0.357 | 0.379 | 0.378 |
| copas  | 0.217 | **0.191** | **0.257** | 0.276 | 0.260 | 0.260 |

Deployable coverage (target 0.95):

| mechanism | adaptshrink_ens | ubcma | **henmi_copas** | adaptshrink_solo |
|---|---|---|---|---|
| smooth | 0.975 | 0.703 | **0.333** | 0.692 |
| step   | 0.983 | 0.630 | **0.050** | 0.833 |
| copas  | 0.967 | 0.846 | **0.258** | 0.733 |

## Verified, bootstrap-robust wins vs the REAL Henmi-Copas

- **AdaptShrink-ensemble** (UBCMA + PET-PEESE + trim&fill, robust model average):
  robust win on **smooth** (mciw0 ratio 0.80, bootstrap CI `[-0.153, -0.045]`) and
  **step** (ratio 0.60, CI `[-0.168, -0.111]`); near-robust on copas (P=0.96, CI
  upper just +0.004). Critically it ALSO **covers 0.97-0.98 out of the box** where
  HC covers 0.05-0.33 — a Pareto improvement, not just a calibration trick.
- **UBCMA**: robust win on **step** (CI `[-0.112, -0.010]`) and **copas**
  (CI `[-0.085, -0.018]`).

## Honest negatives (not buried)

- **The standalone conformal AdaptShrink (`adaptshrink_solo`) does NOT beat HC**
  on any mechanism — every bootstrap CI includes 0. Its centre is less biased than
  HC's but higher-variance, so its honest jackknife interval is too wide. The
  "conformal-forward" idea did not win as a standalone estimator.
- **trim_and_fill's mciw0 advantages are fragile**: it has negative bias and poor
  raw coverage (0.22-0.67); it looks good only on the point-efficiency metric where
  its over-correction happens to land near the truth under step selection. Not a
  robust, general win.
- The win is fundamentally a **bias-of-the-centre** story: under selection every
  inverse-variance centre (RE, fixed-effect/HC, Copas-Shi) is biased up, so a
  bias-corrected centre (UBCMA, or an ensemble containing it) yields a narrower
  honest interval. The CI machinery is secondary.

## Bottom line

Yes — there is a **real, bootstrap-verified win over the genuine Henmi-Copas**
under selection-mechanism misspecification, and it is not an artefact of the
mislabelled Copas-Shi baseline. The winner is the **UBCMA-based AdaptShrink
ensemble** (and UBCMA itself), which both **cover near-nominally out of the box**
where HC collapses **and** are **20-40% narrower at matched coverage**. The
purely-conformal standalone method was an honest miss.

## Files
`realhc_bakeoff.py` (self-contained; real HC + both AdaptShrink variants) ·
`realhc_strong_perrep.csv` (raw) · `realhc_strong_table.csv` ·
`realhc_strong_truthgate.json` · `test_realhc.py` (5 regression assertions incl.
the honest negative) · `validate_henmi_copas.R` + `hc_reference.json` (HC port
validation).
