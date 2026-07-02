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

## 8bis. PROMOTION — the learned-kernel + conformal field as the PRIMARY estimator (hardened, expanded corpus)

The §8.1 result is promoted from a benchmark line to **the method**. This section
documents the hardening and re-validates the headline on a **larger corpus**.

**Hardened implementation (`borrowing/field_scale/field_learned.py`, tested by
`test_field_learned.py`, reproduced by `benchmark_learned.py`).** The learned kernel
is re-implemented as a **compact grouped-ARD Gaussian process** with an **analytic
marginal-likelihood gradient** (Rasmussen–Williams 2006 eq. 5.8–5.9): one signal
variance, an RBF length scale each for standardised **year** and **log-precision**,
and a match/no-match length scale each for **specialty** and **meta-analysis** — four
learned length scales that *are* the data-driven gravity (replacing the ~23 one-hot
ARD scales of the sklearn prototype, which railed to their bounds). Per-study
sampling variance enters the noise diagonal. The **default evaluation is the honest
k-fold refit** (hyper-parameters re-optimised on each training fold; 10 folds, 5
seeds averaged); closed-form LOO is retained only for reference. Conflict-aware
borrowing (adaptive power prior) and a **CV+/split-conformal** coverage layer are in
the same module. 8/8 unit tests pass (leakage-free features; k-fold beats a
no-structure global on learnable synthetic structure; closed-form LOO matches
brute-force; adaptive `a0` monotone in conflict; conformal reaches nominal coverage;
scrambled kernel loses).

**Expanded corpus.** The registry was grown from 779 nodes / 16 MAs to **1177 nodes
/ 28 MAs** by harmonising 12 additional real metadat meta-analyses via
`metafor::escalc` in R (`harmonize_new.R`; authoritative, not hand-rolled): 10 raw
2×2 MAs → log-OR and 2 raw correlation MAs → Fisher-z. This grows the **LOR family
from 3 to 12 meta-analyses** (56 → 380 nodes) — the strongest available test of
whether the learned-kernel win survives more coverage. Two trial-overlap duplicates
were excluded truth-first (`colditz1994` ≡ the existing `bcg`; `egger2001`
IV-magnesium-in-MI shares trials with the existing `li2007`). Family split now
SMD 445 / LOR 380 / COR 352.

### 8bis.1 The win reproduces and broadens (1177 nodes, honest 10-fold, 5-seed)

Truth-gated held-out reconstruction; paired bootstrap vs within-MA
(`benchmark_learned_results.json`):

| method | held-out MAE | vs within-MA [95% CI] | verdict |
|---|--:|---|---|
| **learned-kernel field** | **0.3325** | **−0.0230 [−0.0340, −0.0117]** | **BEATS within-MA** |
| robust-MAP (Schmidli 2014) | 0.3531 | −0.0024 [−0.0091, +0.0043] | ties within-MA |
| hierarchical cross-MA Bayes | 0.3523 | −0.0032 [−0.0091, +0.0027] | ties within-MA |
| within-MA (per-slice) | 0.3555 | — | reference |
| **hand field (AdaptShrink)** | 0.3749 | +0.0195 [+0.0112, +0.0279] | **worse than within-MA** |
| g-modeling / NPMLE EB | 0.4171 | +0.0616 | worse |
| no-borrow (global) | 0.4185 | +0.0630 | worse |
| learned-kernel **scrambled** | 0.3850 | +0.0295 [+0.0153, +0.0435] | worse (control) |

Absolute MAE is higher than on the 779-corpus because the added LOR mass is a
noisier scale — the truth-gated quantity is the **paired contrast**, and the
learned-kernel win of **−0.0230** cleanly reproduces the earlier **−0.025**. Two
things sharpen as coverage grows: (i) the **learned kernel is now the *only* method
that beats within-MA** — robust-MAP and hierarchical cross-MA Bayes drop to a tie;
(ii) the **hand AdaptShrink field is decisively worse than within-MA** (+0.0195),
confirming it as the weak starting instantiation.

### 8bis.2 Per-regime — the win is broad, not a sparse-frontier artifact

learned-kernel − within-MA by home-MA sibling count (paired bootstrap):

| regime | n | learned | within | Δ [95% CI] | verdict |
|---|--:|--:|--:|---|---|
| sparse (k ≤ 8) | 14 | 0.560 | 0.500 | +0.060 [−0.002, +0.117] | n.s. (underpowered, n=14) |
| **mid (9–40)** | 350 | 0.486 | 0.515 | **−0.029 [−0.055, −0.004]** | **learned WINS** |
| **rich (k > 40)** | 813 | 0.263 | 0.285 | **−0.022 [−0.034, −0.010]** | **learned WINS** |

Unlike the *hand* field (which helped only at a single sibling and harmed for k ≥ 2),
the **learned** kernel beats within-MA across both the mid- and rich-home-MA regimes.
The only place it does not win is the 14-study ultra-sparse tail, which is
underpowered (CI includes 0).

### 8bis.3 Conformal calibration — nominal coverage at controlled width

CV+/split-conformal per family, target 90% (`benchmark_learned_results.json`):

| method | model cover / width | conformal cover / width |
|---|--:|--:|
| learned-kernel field | 0.806 / 1.30 | **0.899 / 1.55** |
| within-MA | 0.943 / 1.83 | 0.899 / 1.70 |
| hand field | 0.946 / 1.84 | 0.899 / 1.77 |
| robust-MAP | 0.999 / 7.01 | 0.899 / 1.63 |
| hierarchical cross-MA | 0.777 / 1.30 | 0.899 / 1.61 |

The learned kernel's model-based interval under-covers (0.806); **conformal repairs
every method to exactly nominal 0.899**, and the conformal learned-kernel interval is
the **tightest of any borrowing method** (1.55). Conformal is therefore adopted as
the reported coverage layer of the primary estimator.

### 8bis.4 Negative controls (expanded corpus) — all pass

- learned-kernel − learned-**scrambled** = **−0.0525 [−0.0673, −0.0373]** — true
  (ma, specialty) topology beats permuted labels: the learned gravity is real. ✔
- within-MA − no-borrow = −0.0630 [−0.0772, −0.0492] — within-MA borrowing is real. ✔
- ultra-sparse regime: learned kernel does not beat within-MA (n.s.) — no
  over-claiming where there is no signal to grip. ✔

### 8bis.5 Independent-engine verification

The headline was re-derived by a **second, independent GP engine** that shares no code
with the primary estimator: `verify_learned_independent.py` reads only the exported
`corpus_full_1177.csv`, builds a **sklearn `GaussianProcessRegressor` with a one-hot
ARD-RBF kernel** (per-category length scales — a different parameterisation than the
primary grouped-ARD GP), runs its own honest 10-fold, and pairs it against an
independently-written within-MA pooler.

| quantity | independent engine | primary build | agreement |
|---|--:|--:|---|
| learned-kernel MAE | 0.3314 | 0.3325 | ~0.001 |
| within-MA MAE | 0.3555 | 0.3555 | exact |
| learned − within-MA [95% CI] | **−0.0241 [−0.0366, −0.0116]** | −0.0230 [−0.0340, −0.0117] | MATCH; both CIs exclude 0 |

The win is robust to the GP engine and the kernel parameterisation.

**External vendor confirmation — Codex Seat A, gpt-5.5 (2026-07-02).** The laptop Codex
seat (previously unreachable) now authenticates headless; it was given ONLY
`corpus_full_1177.csv` + `LEARNED_VERIFY_TASK.md` and told to implement the whole thing
from scratch (no shared code). It wrote a **450-line, zero-import** numpy/scipy grouped-ARD
GP (Cholesky NLL + analytic gradient, match/no-match categorical kernels, honest 10-fold CV
with per-fold hyper-parameter refit, 3 fold-seeds) and an independent within-MA pooler
(`xverify_codex_seatA/learned_verify.py`, `xverify_codex_seatA/learned_verify_result.json`):

| quantity | Codex Seat A (external, from scratch) | primary build | agreement |
|---|--:|--:|---|
| learned-kernel MAE | 0.3363 | 0.3325 | ~0.004 |
| within-MA MAE | 0.3555 | 0.3555 | exact |
| learned − within-MA [95% CI] | **−0.0192 [−0.0306, −0.0077]** | −0.0230 [−0.0340, −0.0117] | MATCH; both CIs exclude 0 |
| per-family learned MAE (COR/LOR/SMD) | 0.218 / 0.533 / 0.261 | 0.218 / 0.532 / 0.250 | match |

Codex's verdict verbatim: *"CONFIRMS: the learned kernel beats within-MA borrowing because
delta is negative and the 95% CI excludes 0."*

**Second external vendor — Fable 5, from scratch (2026-07-02).** A Fable-model sub-agent, given the
same two files and the no-shared-code rule, wrote its OWN zero-import numpy/scipy grouped-ARD GP
(`xverify_fable/fable_verify_learned.py`: `cho_factor`/`cho_solve` log-marginal-likelihood,
L-BFGS-B hyper-parameter fit, 10-fold CV × 5 seeds, own within-MA pooler) and independently reported
(`xverify_fable/fable_learned_result.json`): learned-kernel MAE 0.3361, within-MA 0.3575,
**learned − within = −0.0214 [−0.0332, −0.0096]** — negative, CI excludes 0. per-family COR/LOR/SMD
0.219 / 0.534 / 0.260.

**Two-vendor quorum reached.** All four independent engines agree the learned kernel beats within-MA
borrowing, every CI excluding 0:

| engine | learned MAE | within-MA | learned − within [95% CI] |
|---|--:|--:|--|
| primary build (grouped-ARD) | 0.3325 | 0.3555 | −0.0230 [−0.0340, −0.0117] |
| internal sklearn (one-hot ARD) | 0.3314 | 0.3555 | −0.0241 [−0.0366, −0.0116] |
| **Codex gpt-5.5 (external, scratch)** | 0.3363 | 0.3555 | −0.0192 [−0.0306, −0.0077] |
| **Fable 5 (external, scratch)** | 0.3361 | 0.3575 | −0.0214 [−0.0332, −0.0096] |

**Verdict: CONFIRMED by a two-vendor quorum** (Codex gpt-5.5 + Fable 5), each a from-scratch
zero-import re-implementation, alongside three internal engines — not a split, not inconclusive. The
external estimates are marginally more conservative (−0.019 to −0.021 vs −0.023) but all robustly
negative with CI<0. Seat B (pc2) is authenticated but was network-degraded this session (socket-buffer
exhaustion, os error 10055) and was not needed. 779-corpus results were previously reproduced by Codex
Seat A from scratch (§7).

### 8bis.6 Real-AACT corpus-expansion robustness + a scope boundary

A bounded real-AACT LOR slice was extracted truth-first (`aact_lor_expand.py`): sponsors' own
reported Odds-Ratio estimates + 2-sided 95% CIs from `outcome_analyses` (no arm re-derivation),
pre-specified outcomes only, one median-logOR effect per trial, CI round-trip verified, grouped into
coherent (MeSH condition × intervention) meta-analyses. **A data-availability finding in itself:**
once that quality bar is applied, AACT yields only **3 coherent OR meta-analyses (28 trials)** at
k>=8 — the diabetes/oncology candidates collapse because most of their ORs are secondary or lack a
clean 2-sided 95% CI. AACT is structurally thin for clean OR-synthesis (consistent with pilot-4).

Appending those 3 real AACT MAs to the corpus and re-running the field unchanged
(`aact_expand_test.py`, `aact_expand_result.txt`):

| test | learned − within-MA | reading |
|---|---|---|
| **(B) whole expanded corpus (1205 nodes / 31 MAs)** | **−0.0231 [−0.0343, −0.0115] WIN** | headline **survives** adding real AACT MAs — essentially unchanged from −0.0230 |
| (A) held-out AACT rows only (n=28, EXPLORATORY) | +0.025 [−0.015, +0.064] n.s. | on a **cold** new MA with no corpus siblings the learned kernel does **not** transfer |
| (C) raw 90% interval coverage on AACT subset | 0.50 | conformal is corpus-level; cold-MA intervals under-cover |

**Two honest conclusions:** (1) the learned-kernel-beats-within-MA headline is **robust to expanding
the corpus with genuinely new real meta-analyses from a different data source** (ClinicalTrials.gov),
not a metadat artefact. (2) A precise **scope boundary**: the advantage comes from cross-MA structure
*within* the training corpus and does **not** automatically extend to a cold new MA that has no
siblings in training (A, n.s./underpowered) — so the method is for reconstruction *inside* a
populated field, and cold-MA use would need the target regime represented in calibration. Recipe +
deferral rationale in `AACT_SLICE_NEXTSTEP.md`.

### 8bis.7 Bounded real-AACT field + conformal — the "every record exerts influence" demonstration
The AACT extractor was extended truth-first (`aact_expand.py`, `aact_run.py`; verified by an independent
re-run — numbers below are exact) to **two log-effect families** at k≥6: log-odds (LOR) and a new
**log-hazard-ratio (LHR)** family from sponsor-reported HRs + 2-sided 95% CIs (same self-verifying
contract: pre-specified outcomes, one median effect/trial, CI round-trip, explicit specialty map). This
yields a bounded real field of **37 meta-analyses / 412 trials** — LOR 3 MAs/28 nodes (structurally thin,
as before) and **LHR 34 MAs/384 nodes** (oncology-rich: survival HRs of monoclonal antibodies, taxoids,
kinase inhibitors, etc.). (A real slug-collision bug that had silently merged distinct condition×intervention
MAs was found and fixed; distinct MAs now stay distinct.)

| test (learned-kernel field, honest 10-fold, vs within-MA) | learned − within [95% CI] | verdict |
|---|---|---|
| **AACT-only LHR field (n=384)** | **−0.0109 [−0.0192, −0.0027]** | **learned WINS** on the real oncology-HR field |
| AACT-only LOR field (n=28) | +0.050 [−0.026, +0.135] | tie (thin, underpowered) |
| AACT-only ALL (n=412) | −0.0067 [−0.0163, +0.0032] | n.s. (LOR dilutes) |
| corpus+AACT, **corpus-only rows (n=1177)** | **−0.0243 [−0.0361, −0.0126]** | metadat headline **SURVIVES** expansion |
| corpus+AACT, held-out AACT rows (n=412) | −0.0084 [−0.0168, −0.0001] | marginal win (upper CI on boundary) |
| **conformal coverage on AACT rows** | raw **0.672 → conformal 0.903** (nominal 0.90) | **conformal REPAIRS** the real-AACT coverage failure |

**Verdict (bounded, honest):** on bounded real ClinicalTrials.gov data the learned-kernel "every-record-
influence" field is a genuine win on the large oncology hazard-ratio family (−0.0109, n=384) and marginal
on the pooled held-out AACT rows; the committed metadat headline is unchanged under expansion
(corpus-only −0.0243); the 28-node LOR slice is an underpowered tie; and split-conformal calibration
that includes AACT-regime residuals repairs the raw GP under-coverage (0.67) to nominal (0.90). Because
the base corpus has no LHR family, the LHR win is identical AACT-only and in the expanded field — an
internal consistency check (LHR gets no corpus donors). Not a 500k run — a defensible bounded
demonstration on real registry data, verified by independent re-run.

## 9. Verdict

**Is registry-scale borrowing a real improvement over within-MA borrowing? — With
a hand-set kernel, no (except at the sparse frontier); with a modern LEARNED
kernel + conformal calibration, YES — and this is now the primary method.**

- **PRIMARY METHOD — learned kernel + conformal.** On the expanded 1177-node /
  28-MA corpus the learned-kernel field **beats within-MA borrowing by −0.0230
  [−0.0340, −0.0117]** (honest 10-fold, 5-seed; §8bis.1), reproducing the −0.025 of
  the smaller corpus. It is the **only** method that beats within-MA (robust-MAP and
  hierarchical cross-MA Bayes now merely tie it), it wins in **both the mid- and
  rich-home-MA regimes** (§8bis.2), and **conformal calibration** repairs its
  coverage to nominal 0.899 at the tightest borrower width (§8bis.3). This is the
  contribution.
- The corpus field is a **real object with genuine structure**: the learned kernel
  decisively beats its own **scrambled control** (−0.0525 [−0.0673, −0.0373]); the
  relevance topology carries signal.
- **The hand-set AdaptShrink field is the weak baseline, reported honestly.** With
  hand-set γ-weights, cross-MA borrowing does not beat within-MA (it is +0.0195
  *worse* on the expanded corpus, §8bis.1; and on the smaller corpus helped only at
  the single-sibling frontier, §4–5). The upgrade is entirely the **learned**
  gravity: the data-driven relevance metric extracts cross-study signal the fixed
  weights could not.
- The other modern borrowers (robust-MAP, hierarchical cross-MA Bayes) beat the hand
  field but not within-MA; on dynamic borrowing at the sparse frontier the
  power/commensurate/SAM priors beat our AdaptShrink precision fusion (§8.3). Our
  hand-set precision fusion is honestly the weakest borrowing rule.

**Honest caveats.** (a) Corpus coverage: 28 of the 116 catalogued metadat MAs are
now harmonised (up from 16); the field is block-diagonal by 3 effect families, so
cross-family borrowing is a-priori excluded rather than tested. (b) The GP LOO (R&W
eq. 5.12) shares hyper-parameters across folds (mild optimism); the headline uses the
**honest 10-fold refit**, which still beats within-MA. (c) Full ML-NMR /
doubly-robust transport needs IPD or aggregate covariate distributions this corpus
lacks; §8.4 is a bounded g-computation on the one shared node-level covariate
(`year`). (d) No MCMC engine (PyMC/Stan) is installed, so robust-MAP, commensurate,
hierarchical and g-modeling use closed-form / EM / MoM approximations of the cited
full-Bayes methods; `metafor` (external) cross-checks the RE pooling. (e) Pure-prior
held-out reconstruction is demanding; a partial-pooling regime shows smaller effects
both ways (the B2 dynamic-borrowing regime is exactly that). (f) The ultra-sparse
tail (k ≤ 8, n=14) is underpowered — the learned kernel does not beat within-MA
there (n.s.), which we report rather than over-claim. The result is a genuine,
frontier-measured contribution — the learned-kernel field, with conformal
calibration, beats within-MA — not a toy and not a null from lack of power.

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
