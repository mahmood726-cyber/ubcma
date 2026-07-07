# Is Public Data Enough? Weight-Coverage, Reproduction & Influence of Open-Data Meta-Analysis

**Branch:** `pilot/regpub-opendata-sufficiency` (off `pilot/regpub-discrepancy`) · **Status:** staged, local commits only — no push/deploy.
**Code:** `regpub_pilot/sufficiency/` · **Artifacts:** `regpub_pilot/out/sufficiency_*.{csv,json}` · **Date:** 2026-07-07

---

## The question, honestly reframed

Phase 1 established that a no-paywall researcher (ClinicalTrials.gov API + PubMed
abstracts + Europe PMC/OA full text, all free) can pool ~**42 % of trials BY COUNT**
for a condition, and that most of the rest is *structurally* non-poolable. That
count-based number is the wrong denominator for the question that actually matters.

**The real question is WEIGHT, not count.** A meta-analysis's conclusion is a weighted
average; a handful of large trials can carry almost all of the statistical weight. So a
small *fraction of trials* can be a large *fraction of information* — and conversely,
the trials you cannot pool might carry the signal. This study asks, for a set of **real
published meta-analyses**:

1. **Weight coverage** — what fraction of the published MA's inverse-variance *weight*
   does the open-data-poolable subset hold?
2. **Reproduce** — rebuild the pooled estimate from the open subset; does it match the
   published direction / significance / magnitude?
3. **Robustness / influence** — under worst-case-but-plausible assumptions about the
   trials we could **not** pool (one-directional, publication-bias-style missingness),
   **can the missing evidence overturn the conclusion?** Verdict **ROBUST** vs **FRAGILE**.

The gate is **robustness, not a coverage %** — the "influence condition" form of the
idea that a review is trustworthy from open data if the missing fraction *cannot flip it*.

---

## Universe — 10 real published meta-analyses, two tiers

| Tier | What | N | Extraction tested? |
|---|---|---|---|
| **Tier 1 — extraction** | Modern registered-trial **class** MAs, rebuilt by REAL open-data extraction (CT.gov results + PubMed abstracts) in the reconstruct-and-beat pilot | 6 | **Yes** — real free-source pull |
| **Tier 2 — coverage** | Historical, mixed-era MAs (`metadat`) with a genuine non-poolable tail | 4 | No — per-trial data comes from the published dataset, so only **coverage + influence** are tested |

Tier 1: SGLT2 / GLP-1 / DPP-4 cardiovascular-outcome MACE meta-analyses; anti-PD-(L)1
2nd-line NSCLC OS; CDK4/6 PFS; PARP-maintenance ovarian PFS.
Tier 2: **IV magnesium in acute MI** (`dat.li2007`, incl. ISIS-4 & MAGIC); **BCG vs
tuberculosis** (`dat.bcg`); **St John's wort vs placebo** for depression (`dat.linde2015`);
**metformin vs placebo** HbA1c (`dat.senn2013`).

The two-tier split is stated plainly because it bounds what each result proves: Tier-1
tests whether open extraction *recovers* the evidence; Tier-2 tests whether the open
*subset* would *suffice* even when we hold the real numbers.

### Open-data poolability rule (ESTIMATE for historical trials)

For Tier-2 a trial is deemed open-data-poolable if
`(publication year ≥ 2006)  OR  (total N ≥ 5000)`
— P1 = registry-results era (FDAAA 2007 / registration mandate 2005); P2 = landmark
mega-trial, extractable from free sources regardless of era. The rule is **deterministic
and conservative** (it under-counts coverage, which makes any "still robust" verdict
stronger) and is **marked an ESTIMATE** — its effect is swept in §5. Tier-1 poolability
is *measured*, not ruled: every trial was actually resolved from a free source.

---

## Method

- **Weight coverage** = Σ(poolable IV weights) / Σ(all IV weights), reported both
  **fixed-effect** (`1/vᵢ`) and **random-effects** (`1/(vᵢ+τ²)`, τ² from the full set).
  The two differ sharply when a mega-trial is poolable (see IV Mg).
- **Reproduce** pools the open subset two ways: **standard** (DerSimonian-Laird + normal,
  mimicking the typical published method — isolates the *data/coverage* question) and the
  **house stack** (REML + Hartung-Knapp-Sidik-Jonkman + prediction interval — the rigor
  overlay). `reproduced` uses the standard method for a like-for-like comparison; the
  house stack is reported alongside so small-sample method conservatism is visible, not
  conflated with a data problem.
- **Robustness / influence — breakdown fraction `r*`.** The load-bearing metric is the
  minimum *missing-weight ratio* (missing weight ÷ poolable weight) that flips the
  reproduced conclusion. It is **assumption-free algebra** on the subset:
  adding a hidden block of weight `ρ·W` at effect `μₘ` moves the fixed-effect z to
  `z' = (z + ρ·μₘ/se) / √(1+ρ)`. Two one-directional (publication-bias-style) scenarios:
  **dilution** (`μₘ=0` → `r* = (|z|/1.96)² − 1`) and **reversal** (`μₘ` at the worst
  *observed* opposing effect). For a reproduced *null* the threat inverts (hidden real
  effect manufacturing significance). **This one-directional-missingness sensitivity IS
  the selection-model analysis** — suppressed studies are exactly a hidden block on one
  side. A review is **ROBUST** iff the *actual* missing-weight ratio `ρ` (from coverage)
  is below `r*` — i.e. even if all the missing weight were adversarial, it could not flip
  the conclusion.

---

## Per-review results

| Review | Area | Tier | k pool/tot | Wt-cov fixed | Wt-cov RE | Published | Open-subset (std) | Verdict |
|---|---|---|---:|---:|---:|---|---|---|
| SGLT2 MACE | cardio | 1 | 3/3 | 100 % | 100 % | benefit (HR 0.89) | benefit (0.89) | **ROBUST** ¹ |
| GLP-1 MACE | cardio | 1 | 7/7 | 100 % | 100 % | benefit (0.88) | benefit (0.87) | **ROBUST** |
| DPP-4 MACE | cardio | 1 | 4/4 | 100 % | 100 % | null (0.99) | null (0.99) | **ROBUST** |
| IO 2L-NSCLC OS | onc | 1 | 5/5 | 100 % | 100 % | benefit (0.71) | benefit (0.71) | **ROBUST** |
| CDK4/6 PFS | onc | 1 | 3/3 | 100 % | 100 % | benefit (0.55) | benefit (0.56) | **ROBUST** |
| PARP ovarian PFS | onc | 1 | 4/4 | 100 % | 100 % | benefit (0.53) | benefit (0.53) | **ROBUST** |
| **IV Mg in acute MI** | cardio | 2 | 2/22 | **90 %** | **25 %** | benefit (OR 0.58) | **null (1.05)** | **NOT REPRODUCED** ² |
| **BCG vs TB** | infect | 2 | 6/13 | 71 % | 56 % | benefit (RR 0.49) | **null (0.66)** | **NOT REPRODUCED** ³ |
| St John's wort | psych | 2 | 1/9 | 27 % | 18 % | benefit (OR 2.02) | benefit (1.83) | **FRAGILE** ⁴ |
| Metformin HbA1c | cardio | 2 | 1/4 | 62 % | 30 % | benefit (MD −1.13) | benefit (−0.82) | **ROBUST** ⁵ |

¹ SGLT2: data fully open; the **house REML+HKSJ** stack is *non-significant* at k=3
(HR 0.89, CI 0.77–1.04) — an honest small-sample-method caveat, not a data gap. The
published DL result and the standard reproduction are significant.
² IV Mg breakdown: subset `{ISIS-4, MAGIC}` → OR ≈ 1.05 (null); full set → OR 0.58
protective. See §4.1 — the open answer is arguably the *correct* one.
³ BCG: the 6 large open trials are low-latitude/near-null; the strongly-protective trials
are old high-latitude ones we cannot pool. See §4.2.
⁴ Hypericum: reproduced, but only 1 trial (27 % of weight) is poolable; missing/poolable
weight ρ = 2.73 ≫ breakdown r* = 0.52 → the missing 73 % could overturn it.
⁵ Metformin: single poolable trial but strongly significant; ρ = 0.61 ≪ r* = 16.8 → the
missing weight cannot dilute it. (Single-trial subset — heterogeneity untestable.)

---

## Headline

> **Of 10 real published meta-analyses, 7 could be reproduced to the same clinical
> conclusion from open data alone AND shown robust to the evidence that could not be
> pooled; 1 reproduced but is fragile; 2 could not be reproduced from open data.**

But the composition matters, and the honest signal is in the split:

| | N | Reproduced & **ROBUST** | Reproduced but **FRAGILE** | **NOT** reproduced |
|---|---:|---:|---:|---:|
| **Tier 1** — modern all-open class MAs | 6 | **6** | 0 | 0 |
| **Tier 2** — historical long-tail MAs | 4 | **1** | 1 | 2 |
| **Overall** | 10 | **7** | 1 | 2 |

- **Tier 1 (6/6).** For landmark, registered, mega-trial drug-class meta-analyses,
  **open data is fully sufficient** — 100 % weight coverage, conclusion reproduced and
  robust. This is the good-news anchor and it is real: the entire evidence base is a
  handful of large registered RCTs, all free.
- **Tier 2 (1/4).** For historical, mixed-era meta-analyses with a genuine non-poolable
  tail, **open data was sufficient-and-robust in only 1 of 4.** This is the sobering,
  load-bearing result — and it is *not* a coverage-percent story: IV Mg fails at 90 %
  fixed-weight coverage; the failure is about **which** weight is missing.

**The one-line answer to "what % of published MAs could have been done with free data":**
for modern registered-trial class reviews, ~all of them; for the broad historical
literature, closer to **1 in 4** hold up — and *high trial or even weight coverage does
not guarantee it.* The gate has to be the influence test, not a coverage threshold.

---

## §4 — The two archetypes (why weight ≠ count, in both directions)

### 4.1 IV magnesium in acute MI — a mega-trial carries 90 % of the weight, and the published conclusion was the artifact

`dat.li2007` has 22 trials. Two are open by our conservative rule: **ISIS-4** (58,050
patients) and **MAGIC** (6,213). They hold **90 % of the fixed-effect weight** but only
**25 % of the random-effects weight** — because RE pooling (τ² > 0) deliberately flattens
weights and lets the 20 small trials collectively dominate.

- Open subset → OR ≈ **1.05, null**.
- Full-set RE → OR **0.58, protective, significant** — this *is* the pre-ISIS-4 published
  meta-analytic conclusion (a textbook small-study-effect / publication-bias artifact).

So the open-data subset **fails to reproduce the published RE conclusion** — but the
subset's null is the **modern-consensus correct answer**. Open data, dominated by the
honest mega-trial, *resists* the artifact rather than being "wrong." This is the cleanest
possible demonstration that **weight coverage is model-dependent** (90 % fixed vs 25 % RE)
and that reproducing a *published* number is not the same as reaching the *right* answer.

### 4.2 BCG vs tuberculosis — the missing trials carry the signal

`dat.bcg` has 13 trials; efficacy rises with latitude. The 6 large (open) trials are
low-latitude / near-null (TPT-Madras alone is 176k patients, RR ≈ 1.0); the strongly
protective trials are the old, small, high-latitude ones we cannot pool. Open subset →
RR 0.66 (CI crosses 1, **null**); full set → RR 0.49 (**protective**). Here open data
genuinely *loses the signal* — an effect-modifier concentrated in the non-poolable tail.
FRAGILE/NOT-REPRODUCED is the correct, honest verdict at 71 % fixed / 56 % RE coverage.

Together these bound the phenomenon: **a mega-trial can make a small trial-count
sufficient (IV Mg), and a biased-open subset can make a large weight-coverage
insufficient (BCG).** Neither trial-count nor weight-percent alone is the right gate.

---

## §5 — Poolability sensitivity (Tier-2 verdicts vs the rule)

Because Tier-2 poolability is an **estimate**, the verdicts are re-run under four rules.
The two textbook coverage failures are stable; the thin single-trial cases are sensitive
(an honest limitation — a k=1 open subset is inherently assumption-driven).

| Rule | IV Mg | BCG | Hypericum | Metformin |
|---|---|---|---|---|
| base `y≥2006 ∨ N≥5000` | NOT-REPRO | NOT-REPRO | FRAGILE | ROBUST |
| strict `y≥2010 ∨ N≥5000` | NOT-REPRO | NOT-REPRO | INSUFF (0 pool) | INSUFF (0 pool) |
| lenient `y≥2000 ∨ N≥5000` | NOT-REPRO | NOT-REPRO | NOT-REPRO | ROBUST |
| abstract-era `y≥1995 ∨ N≥5000` | FRAGILE | NOT-REPRO | ROBUST | ROBUST |

**IV Mg and BCG never reproduce cleanly** under any plausible rule — the coverage-driven
failure is robust to the estimate. Metformin is ROBUST under 3 of 4 rules. Only the
generous abstract-era rule flips hypericum/IV-Mg, and even then IV-Mg is at best FRAGILE.

---

## §6 — Second-vendor confirmation (agy / Antigravity)

The two load-bearing cases were re-computed **independently** by a second vendor (agy
wrote its own Python from the raw 2×2 counts — no access to this code). Confirmed:

| | this study | agy | |
|---|---|---|---|
| IV Mg fixed-weight coverage | **90.0 %** | **90.0 %** | ✓ exact |
| IV Mg subset OR | ~1.05 null | 1.03 (0.72–1.49) null | ✓ |
| IV Mg full-set OR | 0.58 protective sig | 0.66 (0.53–0.82) sig | ✓ direction/sig |
| BCG fixed-weight coverage | **71.2 %** | **71.2 %** | ✓ exact |
| BCG subset RR | 0.66 null | 0.66 (0.41–1.05) null | ✓ |
| BCG full-set RR | 0.49 protective sig | 0.49 (0.34–0.70) sig | ✓ |

Both **NOT-REPRODUCED** verdicts independently confirmed. Only difference: RE-weight
coverage for IV Mg (this study 25 % with REML-τ² vs agy 36 % with DL-τ²) — a τ²-estimator
choice; both far below the 90 % fixed figure, so no verdict changes. Raw output:
`out/agy_xcheck_sufficiency.txt`.

---

## §7 — Honest limitations

- **Tier-2 N = 4 is small** and deliberately archetype-anchored (IV Mg, BCG are chosen
  for *known* ground truth). The "1/4" is illustrative of the phenomenon, not a precise
  population rate. A larger Tier-2 sample is the obvious next step.
- **Tier-2 is a counterfactual, not a live extraction.** Per-trial numbers come from the
  published dataset; we test whether the *open subset* would suffice, not whether we could
  re-extract each historical trial. Extraction fidelity is only tested in Tier 1.
- **Poolability is an ESTIMATE** for historical trials (rule-based, conservative). §5
  shows which verdicts survive the estimate (the two archetypes do; the thin cases don't).
- **Single-poolable-trial subsets** (hypericum, metformin) cannot assess heterogeneity;
  their reproduction rests on one study.
- **IV Mg is a nuance, not a clean failure**: open data does not reproduce the *published*
  result but gives the *correct* one. "NOT_REPRODUCED" is scored against the published
  conclusion; the report flags that this is a point in open data's favour.
- **House stack vs published method**: at small k the REML+HKSJ stack is more conservative
  (SGLT2 loses significance at k=3). This is a real property, reported separately so it is
  not mistaken for a coverage effect.

---

## §8 — Reproduce

```
cd regpub_pilot/sufficiency
python reviews.py            # load & summarize the 10 reviews
python analysis.py           # per-review weight coverage + reproduce + verdict
python run_study.py          # full study -> out/sufficiency_{table.csv,headline.json,full.json}
python -m pytest test_sufficiency.py -q     # 13 unit tests on the math
```

Deterministic and offline: `metadat` CSVs from `F:\public-data\metadat`, reconstruct
scorecards from `regpub_pilot/out/`, pooling via the pilot's validated `src/pool.py`
(REML+HKSJ+PI, <1e-4 vs metafor). No network in the analysis path.

**Bottom line.** Open data is *sufficient and robust* for the modern registered-trial
class meta-analyses that dominate today's high-impact literature — but for the broad
historical evidence base, whether public data is enough is decided by **which weight is
missing**, and only an influence test (not a coverage percentage) can tell you. On this
sample, ~1 in 4 historical reviews clears that bar.
