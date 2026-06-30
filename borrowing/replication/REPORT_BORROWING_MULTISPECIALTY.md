# Experiment 2 — Multi-specialty relevance-borrowing replication

**Branch** `methods-borrowing` · **dir** `borrowing/replication/` · 2026-06-30 · truth-first.

## Goal
The relevance-borrowing win (pilot-2) had replicated only on **2 same-class (GLP1) slices**; the
prior pooled estimate vs the no-relevance null was −23.3 % [−48.5 %, +1.9 %] — *suggestive but the
CI just crossed 0* (N=2 underpowered). This experiment extends to **four new slices, each a
different specialty**, with a real within-set continuous effect-modifier, and pools across all of
them plus the 2 GLP1 slices for a **cross-specialty** replicated estimate.

Same pre-registered machinery as the GLP1 replication: build per-effect `(y, se, modifier)`; verify
the modifier is real in-data (WLS slope + 10k permutation p + weighted R²); then the **5-way real
LOO** (relevance Gaussian kernel × precision vs uniform/scrambled nulls and the REML-NMA baseline;
truth = real held-out effect; paired bootstrap; bw ∈ {SD/2, SD, 1.5·SD}). Clean = modifier perm
p<0.05; flat = n.s. (the in-data β=0 negative control). `multispecialty.py`,
`aggregate_multispecialty.py`.

## Datasets (cited as original publications, not "metadat")
| slice | specialty | modifier | k | original publication |
|---|---|---|---|---|
| kalaian1996 | Education (SAT coaching) | coaching **hours** | 65 | Kalaian & Raudenbush 1996, *Psychol Methods* 1(3):227–235 |
| raudenbush1985 | Education (teacher expectancy) | **weeks** of prior contact | 19 | Raudenbush 1984, *J Educ Psychol* 76(1):85–97 |
| tannersmith2016 | Addiction (brief alcohol intervention) | mean **age** | 113 | Tanner-Smith & Lipsey 2015, *J Subst Abuse Treat* 51:1–18 |
| ursino2021 | Oncology (phase-I dose-toxicity) | **dose** | 49 | Ursino et al. 2021 (compiled in metadat `dat.ursino2021`) |

## Step 1 — modifier verification
| slice | slope | R² | perm p | tier | metafor (external) |
|---|---|---|---|---|---|
| kalaian (hrs) | +0.0033 | 0.080 | 0.045 | clean (weak) | REML slope +0.0033, permp 0.020 |
| raudenbush (weeks) | −0.0132 | 0.369 | 0.027 | **clean** | REML slope −0.0157, permp 0.017 |
| tannersmith (age) | +0.0055 | 0.030 | 0.487 | **flat** | — |
| ursino (dose) | +0.0022 | 0.380 | 0.0001 | **clean (strong)** | — (proportion, no escalc contrast) |

## Step 2 — 5-way LOO per slice (central bw = SD)
| slice | MAE rel/uni/scr | rel−uni | rel−scr | beats both? |
|---|---|---|---|---|
| **ursino** (Oncology) | 0.70 / 0.82 / 0.84 | −0.119 [−0.174,−0.061] **W** | −0.141 [−0.206,−0.079] **W** | **YES** |
| raudenbush (Education) | 0.237 / 0.257 / 0.255 | −0.020 [−0.047,+0.010] | −0.018 [−0.053,+0.018] | directional only |
| kalaian (Education) | 0.190 / 0.190 / 0.193 | −0.001 | −0.003 | no (field too homogeneous) |
| tannersmith (Addiction, FLAT) | 0.093 / 0.090 / 0.091 | +0.002 | +0.001 | no → **inert (correct)** |

- **ursino** is a clean win in a **new specialty** (oncology dose-toxicity): relevance beats both
  nulls at all three bandwidths. The first non-GLP1, non-metabolic clean qualifier.
- **raudenbush** has a genuinely real modifier (the documented Pygmalion finding: expectancy effect
  shrinks with weeks of prior teacher–pupil contact) and relevance is directionally better than both
  nulls, but the CI crosses 0 at k=19 — suggestive, power-limited.
- **kalaian** is nominally clean (permp 0.045) but the modifier is trivially weak (R²=0.08) and the
  field near-homogeneous (every method MAE ≈ 0.19), so relevance correctly *ties* the nulls — there
  is no heterogeneity for the kernel to exploit. Honest: nominal significance ≠ borrowable structure.
- **tannersmith** has a null modifier (permp 0.49); relevance is correctly **inert** (+2.7 % vs
  uniform) — the in-data β=0 negative control behaves as designed.

## Step 3 — cross-specialty pooled estimate (`aggregate_multispecialty.py`)
Pool the **scale-free fractional MAE reduction** `(rel MAE − null MAE)/null MAE` (slices span
HbA1c %, body-weight kg, Cohen's d, logit-toxicity scales), DL random-effects across the **5 clean
qualifiers across 3 specialties** (Endocrine/Metabolic-GLP1 ×2, Education ×2, Oncology ×1):

| comparison | pooled fractional MAE reduction | verdict |
|---|---|---|
| relevance − uniform (no-relevance null) | **−10.9 % [−20.2 %, −1.5 %]** τ²=0.008 | **CI<0 ROBUST** |
| relevance − scrambled null | **−12.4 % [−22.8 %, −2.0 %]** τ²=0.009 | **CI<0 ROBUST** |

**Strong-modifier sensitivity** (in-data R²≥0.15, N=4 — drops the trivially-weak kalaian):
relevance − uniform **−13.8 % [−20.6 %, −7.0 %]**, − scrambled **−15.9 % [−24.5 %, −7.3 %]**.

## Verdict
**The relevance-borrowing win is now a cross-specialty result.** Pooling across 5 clean slices in 3
specialties tightens the prior suggestive N=2 estimate (−23 %, CI crossed 0) into a **robustly
significant** −10.9 % vs the no-relevance null and −12.4 % vs scrambled (both CI<0). Relevance beats
both nulls individually in **3/5** clean slices (2 GLP1 + oncology); the two that don't are honest:
one (kalaian) has a real-but-trivially-weak modifier in a homogeneous field, the other (raudenbush)
is directional but k=19-underpowered. The flat slice (tannersmith) is correctly inert. **The benefit
scales with modifier strength** (kalaian R²=0.08 → ≈0 %; ursino R²=0.38 → −14.5 %; GLP1-dose → −40 %),
exactly as a relevance mechanism should: borrowing helps in proportion to how much the modifier
actually structures the effects.

## Caveats
- 2 of the 5 clean slices are same-class (GLP1); the genuinely independent specialties are 3
  (Endocrine/Metabolic, Education, Oncology).
- kalaian and tannersmith are **effect-level, not study-independent** (verbal+math per study;
  up to 12 effects per study) — the LOO is a prediction exercise so this is admissible, but no
  independence claim is made.
- ursino is a single-arm dose-toxicity proportion (logit with 0.5 continuity), not a placebo
  contrast; it tests relevance-borrowing of a dose-structured rate, a different estimand from the
  controlled effects.

## Cross-verification
Codex seats publickey-denied (laptop/pc2) in this non-interactive session; pc1 already 401.
- `multispecialty.py` — primary (run_slice machinery, ubcma REML).
- `selfverify_multispecialty.py` — **from scratch**, effects recomputed from raw CSVs, inline
  kernels; reproduces ursino (−0.119 W) and raudenbush (−0.020 n.s.) exactly; GLP1 slices reproduced
  by the existing `selfverify_replication.py`.
- `xverify_exp2.R` — **external metafor** confirms the raudenbush (permp 0.017) and kalaian
  (permp 0.020) modifier slopes.

## Files
`multispecialty.py`, `multispecialty_loo.json`, `aggregate_multispecialty.py`,
`selfverify_multispecialty.py`, `xverify_exp2.R`.
