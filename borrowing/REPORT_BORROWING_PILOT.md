# Borrowing-Field Pilot — the decisive first experiment

> *Branch:* `methods-borrowing` (F:\ubcma) · *Date:* 2026-06-30 · *Owner:* Mahmood
> *Scope:* design-brief gaps **#1 (borrowing field)** + **#2 (stand-down)**, minimal
> version. **NO transportability layer** (that is the next experiment *iff* this passes).
> *Status of brief:* the named file `gravitational_borrowing_field_design_brief.md`
> was **not found on disk**; this experiment was built from the inline task spec,
> which is self-contained. Flagged here for provenance.

## TL;DR — gate verdict: **NO** (do not build further yet)

The auditable **covariate-relevance × selection-integrity borrowing field**, fused
through the validated AdaptShrink kernel and scored through the existing
matched-coverage (MCIW0) + paired-bootstrap truth gate, **does not pass the
decisive test on a real AACT therapeutic slice**. Two of the four binding
requirements fail:

- **(b) "no worse in the data-rich regime" FAILS** — borrowing **robustly harms**
  the outlier class (GLP1) in the rich regime (ΔMCIW0 = **+0.256 [+0.183, +0.313]**,
  entire 95% paired-bootstrap CI > 0). The stand-down *detects* the conflict
  (mean δ → 0.20, mean Q ≈ 7) but does **not** fully neutralise a confident-but-wrong
  prior.
- **(d) negative controls FAIL** — the sparse-regime win is **reproduced by a
  no-relevance null** ("shrink toward the precision-weighted field mean", no
  gravity, no λ) and **survives scrambling the relevance map**. So the benefit
  that exists is **generic shrinkage, not the covariate gravity**. The relevance ×
  integrity machinery — the actual thesis — is **near-inert** on this slice.

What *did* work (DPP4-sparse robust win, maintained calibration on the
mechanism-coherent classes) is real but is **not attributable to the borrowing
field's structure**. Per the program's truth-first logic, this is a **negative
result on the decisive question**: we do **not** proceed to the
transportability-weighted layer on this evidence.

---

## 1. The experiment as built

**Question.** For a *target* treatment comparison with only *sparse* direct
evidence, does forming a borrowing prior from the rest of a registry "field"
— each source weighted by **relevance** (covariate/indication distance) ×
**selection-integrity** (GWAM-style registry-linkage λ) × **precision**, fused
via AdaptShrink with an explicit **stand-down** — beat standard NMA on
held-out effects, with maintained calibration, scored through the existing gate?

**Held-out design.** For each target drug class *c*:
- **Truth** μ\*_c = REML pool over **all** of *c*'s trials (the data-rich gold standard).
- **Regimes:** SPARSE (k = 2 sampled *c*-trials) and RICH (k = 8). 300 random
  subsamples per (class, regime); methods are **paired** within a subsample.
- **Methods (paired):**
  - `nma` — **standard NMA**, the netmeta-parity engine (`F:\ubcma\nma\nma_core.py`)
    on the full field + the sampled *c*-trials → TE[*c*, placebo]. *No-borrow comparator.*
  - `borrow` — the borrowing field: own sampled *c* (REML) ⊕ cross-class
    relevance×λ×precision prior, with conflict stand-down, fused by
    `adaptshrink_estimator`.
  - `shrink_mean` — **null diagnostic**: identical pipeline but the prior is a
    plain inverse-variance field mean (relevance ≡ 1, λ ≡ 1). Isolates whether the
    gravity adds anything.
- **Scoring:** MCIW0 (constant-width matched coverage; point-estimator efficiency,
  calib = even reps / test = odd reps, 95% target) + paired bootstrap of the
  MCIW0 advantage vs `nma` (2000 resamples, seed 7). This is the **same gate** as
  `truth-recovery/matched_coverage_bakeoff.py`, baseline swapped to `nma`.
- **Negative control:** permute the mechanism-relevance map across the present
  classes; re-run. A valid gravity would lose its win under scrambling.

**Reused, validated components (not rebuilt):** AdaptShrink kernel
(`src/ubcma/adaptshrink.py`), comparators (`comparators.py`), netmeta-parity NMA
engine (`nma/nma_core.py`), GWAM integrity ratio (`F:\Models\GWAM` —
`model_gwam.py`), and the matched-coverage MCIW0 + paired-bootstrap gate
(`truth-recovery/matched_coverage_bakeoff.py`).

**Stand-down (gap #2).** Prior-data conflict Q = (μ₀−μ_p)² / (se₀²+se_p²);
discount δ = exp(−η·max(0, Q−c₀)) with **a-priori, non-tuned** η = 0.5, c₀ = 1.
The prior's SE is inflated by 1/√δ before fusion, so under conflict the fused
estimate falls back toward no-borrowing with a widened interval. Constants were
fixed before scoring and are **not** retuned to rescue any cell.

**Comparator is not a strawman.** Verified empirically: in this star field,
netmeta TE[*c*, placebo] for a spoke **equals** the inverse-variance pool of *c*'s
direct trials at the network τ² (diff 8.9e-16). Standard NMA gets no indirect
information to a spoke — which is precisely the structural gap the borrowing
field is meant to exploit. We report this openly rather than dress NMA up.

---

## 2. The slice (real AACT data)

AACT snapshot `F:\AACT-storage\AACT\2026-04-12` (DuckDB over the pipe-delimited
tables). Slice = **Type-2 diabetes, HbA1c-change mean differences vs placebo**,
extracted from `outcome_analyses` (reported between-group estimates with CIs →
SE), classified by intervention keyword, with covariates and a registry-integrity
λ. Provenance kept per row (`nct_id`, `analysis_id`).

| | count |
|---|---|
| T2DM trials in snapshot | 5,041 |
| HbA1c outcomes | 4,078 |
| Reported HbA1c mean-difference analyses (with CI) | 488 (478 sane) |
| Active-vs-placebo effects after classification | 100 |
| Independent trial-level effects (IV-pooled within trial×class) | **46** |

**Per-class field** (REML pooled "truth", the held-out targets):

| class | k trials | REML μ\* (HbA1c %) | τ | GWAM λ (results-posted / registered) |
|---|---|---|---|---|
| **GLP1**  | 17 | **−1.172** | 0.568 | 0.360 |
| **DPP4**  | 14 | **−0.606** | 0.217 | 0.481 |
| **SGLT2** | 13 | **−0.522** | 0.137 | 0.338 |
| TZD | 1 | −0.681 | — | 0.421 |
| insulin | 1 | −0.970 | — | 0.362 |

Three well-populated targets. Crucially their truths **differ**: GLP1 (−1.17) is
far stronger than DPP4 (−0.61) and SGLT2 (−0.52). This makes the slice a genuine
test with **built-in kill-potential**: borrowing should help DPP4/SGLT2 (close
truths) but is a **stand-down trap for GLP1** (borrowing biases it toward the
field mean ≈ −0.55). The two sparse classes (TZD, insulin) enter only as sources.

---

## 3. Per-regime results (main run, 300 reps/cell)

MCIW0 = matched-coverage width (lower = better); `mc0_cov` should ≈ 0.95.

### SPARSE (k = 2)
| target | method | bias | MCIW0 | mc0_cov | ΔMCIW0 vs nma [95% CI] | verdict |
|---|---|---|---|---|---|---|
| GLP1 | nma | −0.02 | 1.658 | 0.97 | — | |
| GLP1 | borrow | +0.22 | 1.596 | 0.95 | −0.058 [−0.110, +0.057] | n.s. |
| GLP1 | shrink_mean | +0.23 | 1.586 | 0.95 | (−0.067 [−0.124, +0.043]) | n.s. |
| **DPP4** | nma | 0.00 | 0.539 | 0.93 | — | |
| **DPP4** | **borrow** | −0.01 | 0.493 | 0.93 | **−0.039 [−0.090, −0.014]** | **ROBUST WIN** |
| DPP4 | shrink_mean | 0.00 | 0.482 | 0.95 | −0.073 [−0.151, −0.041] | robust win |
| SGLT2 | nma | −0.01 | 0.452 | 0.98 | — | |
| SGLT2 | borrow | −0.03 | 0.457 | 0.99 | −0.060 [−0.101, +0.005] | n.s. (P=0.83) |
| SGLT2 | shrink_mean | −0.04 | 0.459 | 0.99 | −0.056 [−0.098, +0.035] | n.s. |

### RICH (k = 8)
| target | method | bias | MCIW0 | mc0_cov | ΔMCIW0 vs nma [95% CI] | verdict |
|---|---|---|---|---|---|---|
| **GLP1** | nma | +0.02 | 0.587 | 0.75 | — | |
| **GLP1** | **borrow** | +0.18 | 0.862 | 0.95 | **+0.256 [+0.183, +0.313]** | **ROBUST HARM** |
| GLP1 | shrink_mean | +0.18 | 0.888 | 0.95 | +0.286 [+0.207, +0.337] | robust harm |
| DPP4 | nma | 0.00 | 0.210 | 1.00 | — | |
| DPP4 | borrow | 0.00 | 0.204 | 1.00 | −0.005 [−0.014, +0.005] | n.s. |
| SGLT2 | nma | 0.00 | 0.133 | 1.00 | — | |
| SGLT2 | borrow | −0.01 | 0.124 | 1.00 | −0.006 [−0.020, +0.003] | n.s. |

**Does the gravity add anything? `borrow` vs `shrink_mean`** (the decisive
diagnostic): differences are **tiny** (|ΔMCIW0| ≈ 0.003–0.030) against the
0.04–0.26 borrow-vs-nma effects, and inconsistent in sign — the relevance term
**hurts** DPP4-sparse (+0.034) while marginally helping the GLP1/SGLT2 rich cells.
The borrowing field is ~95 % explained by plain field-mean shrinkage.

**Stand-down behaviour.** δ ≈ 1.00 (no conflict) for DPP4/SGLT2; for GLP1 it fires
(sparse δ ≈ 0.53, rich δ ≈ 0.20; mean Q ≈ 7). It correctly *detects* the
conflict but the residual ~20 % prior weight in the rich regime — where own data
is precise and the prior is *confidently wrong* (sources agree with each other,
not with GLP1) — is enough to inflate bias and width. **Confident-but-wrong
priors are the adversarial case the conflict statistic under-corrects.**

### Negative control (relevance map scrambled, 300 reps/cell)
| target/regime | borrow vs nma ΔMCIW0 [95% CI] | vs real run |
|---|---|---|
| DPP4 / sparse | −0.041 [−0.057, +0.004] | ≈ real (−0.039) — **win persists** |
| GLP1 / rich | +0.240 [+0.175, +0.320] **robust harm** | ≈ real (+0.256) — **harm persists** |

Scrambling the gravity changes essentially nothing → the result is **not** driven
by valid relevance structure.

---

## 4. Gate verdict against the four binding requirements

| # | requirement | result |
|---|---|---|
| (a) | beat NMA in the **sparse** regime | **PARTIAL** — DPP4 robust win; SGLT2 & GLP1 favourable but not bootstrap-robust |
| (b) | **no worse** in the **rich** regime | **FAIL** — GLP1 robustly harmed (CI entirely > 0) |
| (c) | calibrated coverage in **both** | **PARTIAL** — maintained for DPP4/SGLT2 (≈0.93–0.95, both regimes); GLP1 sparse under-covers (~0.55) but so does NMA (shared, high-τ problem) |
| (d) | pass **negative controls** | **FAIL** — no-relevance null reproduces both the win and the harm; scrambling relevance preserves them. Gravity not the driver. |

**Decisive answer to "does the auditable borrowing field beat NMA on sparse
held-out effects with maintained calibration?" → NO.** The mechanism that helps
(field-mean shrinkage) is not the thesis, is indistinguishable from the null and
from scrambled relevance, and the same mechanism robustly harms the outlier class
in the rich regime where the stand-down should have protected it.

---

## 5. Cross-vendor confirmation

The two requested external vendors were **unavailable on this machine**:
- **Codex (pc2 seat A, `-m gpt-5.5`)** — auth token revoked (`HTTP 401
  token_invalidated` / `refresh_token_invalidated`); needs interactive re-login,
  which cannot be done headlessly here.
- **agy** — returns empty output / hangs in `--print` mode on this host.

The headline numbers were instead **independently re-derived three ways and agree
to ≥4 decimals**:
1. `run_pilot.py` (primary scorer).
2. `selfverify.py` — a **separate, independently-written scorer** (different code
   path, no shared functions).
3. A **from-scratch agent re-derivation** that read only the per-rep CSV and the
   metric spec (no repo scoring code): DPP4-sparse borrow_vs_nma
   **−0.0387 [−0.0904, −0.0138] robust win**; GLP1-rich borrow_vs_nma
   **+0.2556 [+0.183, +0.313] robust harm** — matching to the 4th decimal.

The cross-engine NMA sanity (netmeta == direct pool, 8.9e-16) is a fourth
independent check on the comparator. The verdict does **not** rest on a single
implementation. *(External-vendor confirmation remains open; re-run once Codex/agy
auth is restored — it would not change the sign of any headline.)*

---

## 6. Honest verdict & next step

**The core idea is not validated by this decisive test.** A borrowing field whose
benefit (a) cannot be distinguished from generic shrink-to-the-mean, (b) does not
depend on its relevance/integrity weighting, and (c) robustly harms the
data-rich outlier, has **not** earned the transportability layer. Building
transportability-weighted borrowing on top of a borrowing core that the truth
gate just failed would be building on sand.

**We do NOT proceed to the transportability experiment on this evidence.**

Two specific, falsifiable preconditions must be met first — and the pilot
localises them exactly:

1. **The relevance gravity must be shown to be *necessary*.** Re-run on a slice
   where covariates genuinely predict effect heterogeneity (this slice's
   baselines were near-uniform ~8.1 % and only 3 effective classes, two with
   similar truths — so the kernel had almost nothing to discriminate on). The
   negative control (scrambled relevance) and the no-relevance null
   (`shrink_mean`) **must both lose** before any win counts as gravity.
2. **The stand-down must guarantee no rich-regime harm** against a
   *confident-but-wrong* prior (sources mutually agreeing yet wrong for the
   target). The Q-statistic detects it but under-corrects; a harder fallback
   (e.g. full stand-down past a conflict threshold, or a prior SE that reflects
   *target-vs-field* discrepancy rather than only between-source spread) is
   needed — and must be fixed **a priori**, not tuned to this cell.

Until both hold on a fair slice, the auditable borrowing field is an honest
**null**: it shrinks toward the field mean, which helps when the target sits near
the field and hurts when it does not — exactly what the truth gate is built to
expose.

---

## Reproduce
```
cd F:\ubcma\borrowing
python build_field.py        # AACT -> field.json   (DuckDB)
python inspect_field.py      # -> trials.json (46 trial-level effects, per-class truths)
python class_lambda.py       # GWAM-style integrity ratios -> class_lambda.json
python run_pilot.py --reps 300                 # main: perrep CSV, table, bootstrap
python run_pilot.py --reps 300 --scramble      # negative control
python selfverify.py         # independent re-derivation of the two headline cells
python sanity_nma.py         # netmeta == direct-pool sanity
python make_figure.py        # fig_borrowing_pilot.png
```
Artifacts: `pilot_perrep.csv`, `pilot_table.csv`, `pilot_bootstrap.json`,
`pilot_scramble_*`, `fig_borrowing_pilot.png`. Seeds fixed; numbers above are the
committed run.
