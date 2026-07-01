# Registry-scale borrowing FIELD — build, test, and honest bound

**Branch:** `methods-borrowing` · **Date:** 2026-07-01
**Code:** `borrowing/field_scale/` (`corpus.py`, `field.py`, `downsample.py`, `c_sweep.py`, `make_fig.py`)
**Data:** `F:\public-data\metadat` (staged by the public-data scout; no fetching)

## 1. The vision, made concrete

The per-slice relevance-weighted borrowing method (validated on branch
`methods-borrowing`: pilots 1–4, GLP-1 replication, BCG transport, cross-specialty
relevance) borrows **within one meta-analysis (MA)**. This build takes it to its
culmination — the original *gravitational-field* idea: represent a whole **corpus
of real meta-analyses as one field**, where every study exerts a
relevance-weighted ("gravity decays with distance") influence on every other
estimate, and ask whether borrowing **across** MAs beats borrowing **within** an MA.

Truth-first: this is a genuine build with real published data and a real
held-out reconstruction test. The headline is an **honest, sharply-bounded
result**, not a demo.

## 2. The corpus (what the field is built on)

Harmonised from the staged `metadat` CSVs into one node table
(`borrowing/field_scale/corpus_nodes.csv`): every study is a node carrying
`(ma, family, specialty, yi, se, year)`.

| | value |
|---|---|
| **Nodes (studies)** | **779** |
| **Meta-analyses** | **16** |
| **Effect families** | 3 — SMD (445), Fisher-z correlation (278), log-OR (56) |
| **Specialties** | education, clinical medicine, clinical/behavioral, psych-criminology, health-psych, I/O-psych, psychiatry, infectious disease |

Effect harmonisation: Hedges *g* from arm means (or pre-computed `yi/vi`) for the
SMD family; Fisher *z* from correlations for COR; log-odds-ratio from 2×2 / network
response counts for LOR. **Cross-family borrowing is stood down a-priori (weight 0)** —
the scales are not comparable, so the field is **block-diagonal by family**. That
block structure is also the tractability story at *N* ≈ thousands: the kernel is
block-sparse (family) and, within a family, sparse by specialty.

MAs span genuinely related and distant neighbourhoods within a family — e.g. the
SMD block holds an *education* cluster (Kalaian SAT-coaching, Konstantopoulos,
Raudenbush teacher-expectancy, Bangert-Drowns writing-to-learn), a *clinical*
cluster (Tanner-Smith, Gibson, Normand, Senn), and *psych-criminology* (Assink) —
so "related-topic" vs "distant" borrowing is real, not nominal.

## 3. The field, as built

For a held-out target study *t*, its borrowing prior is a relevance-weighted
precision pool over **all other studies**, reusing the validated per-slice
machinery (weight = relevance × precision; weighted mean with within+between
variance — exactly `borrowing_transport.transport_prior`):

```
weight(s → t) = precision(s)
              × [family(s) == family(t)]        # a-priori STAND-DOWN (block-diagonal)
              × topic(s, t)                      # 1 same-MA · 0.50 same-specialty · 0.15 far
              × year_kernel(s, t)                # Gaussian gravity, neutral if year missing
```

Gravity decays with distance: same MA (closest) > same specialty > distant
specialty, and with calendar-year distance. **No effect value enters the
distance** — `yi` is the reconstruction target only, never a feature (no leakage).

**Home-anchored adaptive field (`field_adapt`).** The fixed field re-dilutes rich
MAs toward the global mean. The principled cure is the a-priori *stand-down*: keep
all same-MA donors at full weight and scale the cross-MA mass by `C/(C + n_home)`
with `C = 5` ("~5 good siblings is enough"). A rich home MA → cross mass vanishes →
the field defers to within-MA (inert, no harm); a starved home MA → the field
reaches out. All hyper-parameters (`γ_spec = 0.50`, `γ_far = 0.15`, `bw_year = 1`,
`C = 5`) are fixed a-priori, **not tuned to the outcome**.

## 4. Test: corpus-wide REAL leave-one-out reconstruction

Hold out each study's real effect `yi`; reconstruct it from the field (its own
`yi` removed from every pool); score `|prediction − yi|`. Predictors:

- **global** — family precision-mean (no-locality floor)
- **withinMA_rel** — same MA only, year-kernel × precision (**the per-slice method**)
- **field** — whole family, topic × year × precision (fixed cross-MA field)
- **field_adapt** — home-anchored field with stand-down
- **field_cross** — field *excluding* the home MA (pure cross-MA signal)
- **scrambled** — field with `(ma, specialty)` labels permuted (negative control)

### Mean absolute held-out reconstruction error (779 studies)

| stratum | n | global | withinMA_rel | field | field_adapt | field_cross | scrambled |
|---|--:|--:|--:|--:|--:|--:|--:|
| ALL | 779 | 0.3243 | **0.2776** | 0.3020 | 0.2875 | 0.3482 | 0.3232 |
| SMD | 445 | 0.3469 | 0.2914 | 0.3307 | 0.3087 | 0.3510 | 0.3488 |
| COR | 278 | 0.1972 | 0.1868 | 0.1837 | 0.1853 | 0.2469 | 0.1976 |
| LOR | 56 | 0.7757 | 0.6190 | 0.6615 | 0.6256 | 0.8295 | 0.7434 |

### Key contrasts (paired bootstrap; negative = field better)

| contrast | Δ [95% CI] | verdict |
|---|---|---|
| **withinMA_rel − global** | **−0.0467 [−0.0611, −0.0331]** | within-MA borrowing is REAL |
| field − withinMA_rel (ALL) | +0.0244 [+0.0142, +0.0348] | fixed field **harms** |
| field_adapt − withinMA_rel (ALL) | +0.0099 [+0.0029, +0.0167] | adaptive halves harm, still mild |
| **field_adapt − withinMA_rel (rich, k>40)** | **+0.0007 [−0.0004, +0.0020]** | **INERT — no harm to data-rich** |
| field − scrambled | −0.0212 [−0.0263, −0.0161] | **structure is REAL** |
| field_adapt − scrambled | −0.0358 [−0.0451, −0.0266] | **structure is REAL** |

**Coverage (95% held-out PI):** global 0.90, withinMA 0.92, field 0.92,
**field_adapt 0.93** (best calibrated), field_cross 0.87 (under-covers), scrambled 0.90.

Reading: (i) within-MA borrowing clearly beats the no-locality floor — the
per-slice method works. (ii) The field's topology carries **genuine signal** (both
field variants beat scrambled decisively). (iii) But cross-MA borrowing **cannot
beat within-MA** on the full corpus — at best inert (adaptive, data-rich, COR),
at worst mildly harmful (fixed, SMD). (iv) The a-priori stand-down does its job:
**perfectly inert for data-rich studies** (negative control "no systematic harm
in data-rich studies" ✔).

## 5. Where the field DOES help: the sparse frontier

Natural data has only 14 genuinely-sparse studies (≤8 siblings) — underpowered.
So we **starve each home MA on purpose** (`downsample.py`): keep only *m* random
same-MA siblings and ask whether reaching into the corpus beats within-MA(*m*).
25 random draws × every eligible target, paired.

| home siblings *m* | pairs | within | field | Δ (within−field) [95% CI] | verdict |
|--:|--:|--:|--:|--:|---|
| **1** | 19 475 | 0.3811 | 0.3403 | **+0.0408 [+0.0351, +0.0464]** | **FIELD HELPS (~11%)** |
| 2 | 19 475 | 0.3287 | 0.3360 | −0.0073 [−0.0118, −0.0029] | field harms |
| 3 | 19 475 | 0.3102 | 0.3324 | −0.0222 [−0.0260, −0.0185] | field harms |
| 5 | 19 350 | 0.2969 | 0.3255 | −0.0285 [−0.0317, −0.0254] | field harms |
| 10 | 19 125 | 0.2814 | 0.3064 | −0.0249 [−0.0274, −0.0226] | field harms |

**The crossover sits between one and two siblings.** When a target MA is reduced
to a *single* usable study, the cross-MA field cuts held-out error by ~11%
(0.381 → 0.340). With even two same-MA siblings, within-MA is already better and
any cross contribution harms.

**Robustness to the stand-down constant (`c_sweep.py`):** at *m* = 1 the field
helps for **every** `C ∈ [1, 20]` (+0.040 to +0.042) — the sparse-frontier win is
not a tuning artifact. At *m* = 2 no `C` rescues it (inert only as `C → 0`, i.e.
by turning the field off); at *m* = 3 it harms for all `C`. So **within-MA is the
frequentist optimum once ≥2 siblings exist**, for any reasonable stand-down.

## 6. Negative controls — all pass

1. **Inert where no relevant neighbours / data-rich home** — the home-anchored
   stand-down makes `field_adapt` statistically indistinguishable from within-MA
   for data-rich studies (k>40: +0.0007, n.s.). ✔
2. **Scramble destroys the gain** — permuting the `(ma, specialty)` labels makes
   the field significantly worse than the true-topology field (−0.021 to −0.036).
   The distance structure, not the mere act of pooling, is what carries signal. ✔
3. **No systematic harm to data-rich studies** — same as (1); the fixed field
   harmed them (+0.007, rich stratum), the adaptive field does not. ✔

## 7. External verification

`corpus_nodes.csv` was shipped to the laptop Codex (Seat A, `codex-cli 0.140.0`,
headless over SSH) with a from-scratch spec (`FIELD_VERIFY_TASK.md`, no ubcma
import). Codex independently re-implemented the field (its own `own_verify.py`, retrieved
as `borrowing/field_scale/codex_own_verify.py`) and re-derived the headline
numbers from the node table alone:

| quantity | Codex (from scratch) | this build | verdict |
|---|--:|--:|---|
| within-MA − global (does same-MA help?) | **−0.04522** | −0.045 / −0.047 | MATCH — within-MA borrowing real |
| sparse *m*=1: within mean | **0.38088** | 0.381 | MATCH |
| sparse *m*=1: field mean | **0.34071** | 0.340 | MATCH |
| sparse *m*=1: Δ (within−field) | **+0.04017** | +0.0408 | MATCH — **field helps at 1 sibling** |
| sparse *m*=2: Δ (within−field) | **−0.00779** | −0.0073 | MATCH — **field harms at 2 siblings** |

All five reproduce to within RNG-draw noise (Codex ran an independent sampling
stream). One genuine external vendor (Codex Seat A, `codex-cli 0.140.0`, gpt-5.5,
headless over SSH) alongside the internal derivation confirms the field's
behaviour and its sharp sparse-frontier boundary. No number changed.

A second from-scratch task (`FIELD_VERIFY2_TASK.md` → `codex_own_verify2.py`)
independently re-derived the **modern-benchmark** headlines:

| quantity | Codex (from scratch) | this build | verdict |
|---|--:|--:|---|
| robust-MAP transductive MAE | **0.2716** | 0.2716 | MATCH |
| dynamic borrow *m*=1: own-only | 0.3809 | 0.3836 | MATCH (RNG) |
| dynamic borrow *m*=1: power prior | **0.3524** | 0.3512 | MATCH |
| dynamic borrow *m*=1: precision fusion (ours) | 0.3720 | 0.3723 | MATCH |
| ordering power-prior < ours < own-only | **True** | True | MATCH — modern prior wins |

The external vendor independently confirms both the negative (our precision fusion
is beaten by the power prior) and the positive (borrowing beats no-borrow at the
sparse frontier). No committed number changed.

## 8. Benchmark against the modern statistical frontier

The hand-set field reuses the AdaptShrink-style machinery; is it competitive with
the *current* frontier? We benchmarked it, truth-gated on the same real held-out
reconstruction, against modern hierarchical/Bayesian borrowing, a learned kernel,
modern shrinkage, dynamic borrowing, transportability, and conformal calibration —
all implemented from scratch (`field_modern.py`, `benchmark.py`; RBesT, REBayes,
deconvolveR, bayesmeta are **not installed** on this host, so from-scratch
implementations are used and the canonical packages are cited; `metafor` 5.0.1 is
used as an external RE cross-check; the GP uses scikit-learn 1.8).

### 8.1 Transductive reconstruction (B1) — modern methods beat the hand field

| method | held-out MAE | vs hand field [95% CI] |
|---|--:|---|
| **GP learned kernel** (Rasmussen–Williams 2006) | **0.2527** (honest 10-fold refit) / 0.2399 (R&W-LOO) | **−0.0476 [−0.0644, −0.0310]** |
| robust MAP prior (Schmidli 2014) | 0.2716 | −0.0159 [−0.0268, −0.0051] |
| hierarchical cross-MA Bayes | 0.2707 | −0.0168 [−0.0266, −0.0071] |
| within-MA (per-slice) | 0.2776 | −0.0099 [−0.0167, −0.0029] |
| **hand field (AdaptShrink)** | 0.2875 | — |
| g-modeling / NPMLE EB (Efron 2016) | 0.3230 | +0.0355 (worse; transductive prior mean) |
| no-borrow (global) | 0.3243 | |

**The single most important modern result:** a **learned Gaussian-process kernel**
— data-driven "gravity" (ARD-RBF over year, log-precision, one-hot specialty & MA,
with per-study sampling-variance noise; hyper-parameters by marginal likelihood) —
**beats within-MA borrowing**, and the win survives an honest 10-fold refit that
removes the shared-hyperparameter LOO optimism: **GP(10-fold) − within-MA =
−0.0250 [−0.0414, −0.0095]**. This *refines* §5–7: cross-study borrowing **can**
beat within-MA after all — but only when the relevance kernel is **learned from
data**, not hand-set. The hand-set AdaptShrink field is in fact the *weakest* of
the smart borrowers; robust-MAP, hierarchical cross-MA Bayes, and within-MA all
beat it. g-modeling's point MAE is ≈ global (as expected — its transductive
prediction is the prior mean; its value is a richer predictive, below).

### 8.2 Calibration (conformal) — the modern way to guarantee coverage

Distribution-free split-conformal / jackknife+ intervals (Vovk et al. 2005; Lei et
al. 2018; Barber et al. 2021), scored per family, target 90%:

| method | model PI cover / width | conformal cover / width |
|---|--:|--:|
| GP kernel | 0.955 / 1.41 | **0.899 / 1.08** |
| hierarchical cross-MA | 0.741 (under) / 0.78 | **0.899 / 1.17** |
| robust MAP | 0.999 (over) / 4.86 | **0.899 / 1.21** |
| within-MA | 0.924 / 1.24 | 0.899 / 1.25 |
| hand field | 0.931 / 1.28 | 0.899 / 1.30 |

Model-based intervals are badly mis-calibrated in both directions (hierarchical
Bayes under-covers at 0.74; robust-MAP over-covers at 0.999 with width 4.9).
**Conformal calibration repairs every one to nominal 90% at controlled, often much
smaller width** (robust-MAP 4.86 → 1.21). This is the current best practice for
coverage and should be the field's calibration layer alongside the bootstrap gate.

### 8.3 Dynamic borrowing at the sparse frontier (B2) — modern priors beat ours

At *m*=1 sibling (where borrowing helps), fusing own ⊕ cross-MA field prior:

| rule | MAE (m=1) | vs our precision-fusion [95% CI] |
|---|--:|---|
| **power prior** (Ibrahim–Chen 2000) | **0.3512** | **−0.0212 [−0.0237, −0.0187]** |
| robust-MAP mixture (Schmidli 2014) | 0.3562 | −0.0161 [−0.0182, −0.0141] |
| commensurate prior (Hobbs 2011) | 0.3611 | −0.0112 [−0.0127, −0.0097] |
| SAM prior (Yang 2023) | 0.3619 | −0.0104 [−0.0118, −0.0090] |
| **precision fusion (ours)** | 0.3723 | — |
| own only (no borrow) | 0.3836 | +0.0113 (worse — borrowing helps) |

**Every modern dynamic-borrowing prior extracts more from the registry field than
our conflict-discounted precision fusion**, the power prior most (−0.021). All beat
no-borrow at *m*=1; the gap closes by *m*≥2 (borrowing matters less). Honest
negative for our fusion rule; honest positive for the modern frontier.

### 8.4 Transportability (B3) — covariate g-computation, modifier-specific

A covariate g-computation / reweighting analogue of ML-NMR (Phillippo et al. 2020)
and IOSW transport (Dahabreh et al. 2020) — standardising donor effects to the
target's covariate via a within-family meta-regression slope (full ML-NMR needs IPD
/ aggregate covariate distributions this corpus lacks; `year` is the only shared
node-level covariate). It **helps only where the covariate genuinely predicts the
effect** — Assink Δ+0.094 [0.048, 0.138], BCG Δ+0.137 [0.014, 0.279] — and is inert
or mildly harmful elsewhere (Konstantopoulos −0.022, Li −0.040). This mirrors the
per-slice BCG finding (§5.6 of the manuscript): transport earns its keep in
proportion to modifier strength, and nothing more.

## 9. Verdict

**Is registry-scale borrowing a real improvement over within-MA borrowing? — With
a hand-set kernel, no (except at the sparse frontier); with a modern LEARNED
kernel, yes.**

- The corpus field is a **real object with genuine structure**: it decisively
  beats its own scrambled control, and its relevance topology carries signal.
- With the **hand-set kernel**, cross-MA borrowing does not beat within-MA once
  the home MA has ≥2 studies (§4–5), and helps only at the single-sibling frontier
  (~11% error cut). This bound is real but **specific to the hand-set weights**.
- With a **learned Gaussian-process kernel** (§8.1), the field **beats within-MA
  across the whole corpus** (−0.025 [−0.041, −0.010], honest 10-fold) — the
  data-driven relevance metric extracts cross-study signal the fixed γ-weights
  could not. **This is the central upgrade**: the gravitational field becomes a
  genuine improvement over within-MA once its gravity is learned, not assumed.
- The modern frontier beats the hand field throughout: robust-MAP and hierarchical
  cross-MA Bayes on reconstruction (§8.1); power/commensurate/SAM/robust-MAP on
  dynamic borrowing at the sparse frontier (§8.3); conformal on calibration (§8.2).
  Our AdaptShrink-style precision fusion is honestly the weakest borrowing rule.
- The **a-priori stand-down** remains the key safety property (inert, no harm to
  data-rich studies); **conformal calibration** is the right coverage layer.

**Honest caveats.** (a) Corpus coverage: 16 of the 116 catalogued metadat MAs were
staged as usable CSVs on disk; the field is block-diagonal by 3 effect families, so
cross-family borrowing is a-priori excluded. (b) The GP LOO (R&W eq. 5.12) shares
hyper-parameters across folds (mild optimism); the headline uses the **honest
10-fold refit**, which still beats within-MA. (c) Full ML-NMR / doubly-robust
transport needs IPD or aggregate covariate distributions this corpus lacks; §8.4 is
a bounded g-computation on the one shared node-level covariate (`year`). (d) No
MCMC engine (PyMC/Stan) is installed, so robust-MAP, commensurate, hierarchical and
g-modeling use closed-form / EM / MoM approximations of the cited full-Bayes
methods; `metafor` (external) cross-checks the RE pooling. (e) Pure-prior held-out
reconstruction is demanding; a partial-pooling regime shows smaller effects both
ways (the B2 dynamic-borrowing regime is exactly that). The result is a genuine,
frontier-measured contribution — the field, with modern components, beats
within-MA — not a toy and not a null from lack of power.

## 10. Methods and citations (modern comparators)

- **Robust MAP prior** — Schmidli H, et al. *Robust meta-analytic-predictive priors
  in clinical trials with historical control information.* Biometrics 2014;70:1023.
  Software: Weber S, et al. *RBesT.* J Stat Softw 2021;100(19). (not installed)
- **Commensurate prior** — Hobbs BP, et al. *Commensurate priors for incorporating
  historical information.* Biometrics 2011;67:1047; Bayesian Anal 2012;7:639.
- **Power prior** — Ibrahim JG, Chen M-H. *Power prior distributions for regression
  models.* Stat Sci 2000;15:46; Duan Y, et al. (normalized) Environmetrics 2006.
- **SAM prior (self-adapting mixture)** — Yang P, et al. *SAM priors for dynamic
  borrowing.* Stat Med 2023;42:2626.
- **Gaussian-process / learned kernel** — Rasmussen CE, Williams CKI. *Gaussian
  Processes for Machine Learning.* MIT Press 2006 (LOO eq. 5.12). scikit-learn 1.8.
- **g-modeling / NPMLE empirical Bayes** — Efron B. *Empirical Bayes deconvolution
  estimates.* JASA 2016;111:1131; Koenker R, Mizera I. *Convex optimization / NPMLE.*
  JASA 2014;109:674. Software: deconvolveR, REBayes (not installed).
- **Hierarchical random-effects predictive** — Higgins JPT, Thompson SG,
  Spiegelhalter DJ. JRSS-A 2009;172:137; Gelman A, Hill J. *Data Analysis Using
  Regression and Multilevel Models*, CUP 2007.
- **Conformal prediction** — Vovk V, Gammerman A, Shafer G. *Algorithmic Learning in
  a Random World.* Springer 2005; Lei J, et al. *Distribution-free predictive
  inference.* JASA 2018;113:1094; Barber RF, et al. *Predictive inference with the
  jackknife+.* Ann Stat 2021;49:486.
- **Transportability / data fusion** — Phillippo DM, et al. *Multilevel network
  meta-regression (ML-NMR).* JRSS-A 2020;183:1189; Dahabreh IJ, et al. *Extending
  inferences from a randomized trial to a target population (IOSW / doubly-robust).*
  Biometrics 2020;76:1035.

See Figure `borrowing/field_scale/fig_field_modern.png` (manuscript Figure 5).
