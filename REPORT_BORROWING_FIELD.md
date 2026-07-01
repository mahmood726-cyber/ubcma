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

## 8. Verdict

**Is registry-scale borrowing a real improvement over within-MA borrowing? — No,
not in general; yes, narrowly, at the sparse frontier.**

- The corpus field is a **real object with genuine structure**: it decisively
  beats its own scrambled control, and its relevance topology carries signal.
- But on a 779-study, 16-MA, 3-family corpus, **cross-MA borrowing does not beat
  within-MA** whenever the home MA has ≥2 usable studies — within-MA donors are
  same-population, same-topic, and are simply the best predictor of a held-out
  study. Cross-MA mass, however carefully down-weighted, pulls the estimate back
  toward the global-family mean — re-introducing exactly the bias that within-MA
  borrowing removed.
- The field's useful domain is **sharp and bounded**: the *single-sibling*
  regime (a one-study or two-study evidence base), where it cuts held-out error
  ~11%, robustly across the stand-down constant. This is precisely where a
  meta-analyst has the least information and most needs a principled prior.
- The **a-priori home-anchored stand-down** is the key safety property: it makes
  the field inert (no harm) exactly where within-MA is already sufficient, so the
  field can be deployed as a fallback that never degrades a data-rich analysis.

**Honest caveats.** (a) Corpus coverage: 16 of the 116 catalogued metadat MAs were
staged as usable CSVs on disk; the field is block-diagonal by 3 effect families,
so cross-family borrowing was never tested (a-priori excluded). (b) The topic tags
and a-priori kernel constants are reasonable but hand-set; a learned metric could
shift the crossover, though the C-sweep shows within-MA optimality at m≥2 is
robust. (c) Pure-prior held-out reconstruction is a demanding test (the target
contributes zero own data); a partial-pooling regime (target + field) would show
smaller effects in both directions. (d) `|error|` on the effect scale mixes three
families; the family-stratified rows control for this and agree with the pooled
story. The result is a genuine, defensible **bound** on the gravitational-field
vision, not a null from lack of power (the sparse test is powered at ~19k pairs).
