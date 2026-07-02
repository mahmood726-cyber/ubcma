# Borrowing Expansion — settling transport-vs-relevance by growing the strong-modifier base

**Branch** `methods-borrowing` · dirs `borrowing/rota/`, `borrowing/agg/`, `borrowing/replication/` ·
2026-07-01 · truth-first, honest negatives. Builds directly on Experiment 1 (BCG, `borrowing/bcg/`).

## The question this cycle attacks
Experiment 1 established, on `dat.bcg` (13 placebo-controlled BCG trials, latitude modifier):
the **full transportability-standardisation method robustly beats textbook random-effects (NMA)**,
but its **incremental gain OVER relevance-only down-weighting was only directional at k=13** (the
transport−relevance 95 % CI crossed 0 at the pre-registered bandwidth). The only way to settle it is
**more placebo-controlled, gradient-spanning, strong-modifier slices**. This cycle adds one big one,
aggregates, and honestly reports where the question now stands.

---

## 1. New slice — Rotavirus vaccine efficacy by under-5 mortality (the oral-vaccine paradox)

**`borrowing/rota/`.** Source = the **deposited per-trial dataset** of Clark et al. 2019
(*Lancet Infect Dis* 19:717–727, "Efficacy of live oral rotavirus vaccines by duration of follow-up:
a meta-regression of RCTs"), GitHub `kevinvzandvoort/rotavirus_vaccine_efficacy` /
`rotavirus_vaccine_efficacy_extracted.csv`. **Every vaccine/placebo severe-rotavirus-gastroenteritis
count is taken verbatim from that verified table** — no hand transcription of individual trial papers,
so transcription risk is eliminated at the source.

**Why it is the right analogue of BCG-by-latitude.** The classic *oral-vaccine paradox*: oral
rotavirus-vaccine efficacy against severe RVGE falls steeply as the population's child-mortality
burden rises (VE ≈ 95 % in low-mortality Europe/US → ≈ 50 % in high-mortality Africa/Asia). The
continuous covariate is the country **under-5 mortality rate (U5MR, deaths/1000)**, **data-derived
from OWID child-mortality** (country × trial-year) — an *external* population gradient known for the
held-out trial, exactly like BCG's absolute latitude.

**Slice construction (cleanliness controls, mirroring BCG's year/alloc checks).**
- One estimand: **Period-1** (first follow-up window) only → minimises VE-waning.
- Multi-arm dependency collapsed: vaccine schedule arms sharing a placebo are **pooled** to one
  vaccine-vs-placebo contrast per (study, country) → **k = 29 independent trial-populations**.
- logRR from the 2×2 counts, textbook variance, 0.5 continuity add only when a zero cell is present.
- Pooled multi-country rows (Europe / Latin Am / SE-Asia / Navajo, 9 of 29) get a documented
  representative U5MR and are flagged → **single-country sensitivity** reported below.

**The modifier is REAL and STRONG** (`prep_rota.py`; U5MR 3 → 136 /1000; logRR −4.41 … 0.00):

| test | statistic | perm p |
|---|---|---|
| WLS slope logRR ~ U5MR | +0.0073/unit (z=+2.30), wR²=0.63 | — |
| Unweighted OLS slope | +0.020 | **0.0001** |
| Spearman rank ρ | **+0.872** | **0.0001** |
| RE(DL) meta-regression | +0.0142/unit (z=+3.61), τ²=0.28 | **0.0072** ← headline |
| **metafor REML (external)** | **+0.0141** (z=3.65, p=3e-4), permutest **p=0.0018**, R²=34 % | — |

**3/3 leverage-robust tests significant** (ρ=0.87 is stronger than BCG's 0.56). The U5MR slope
**survives adjustment** for follow-up months (+0.0073 → +0.0067) and vaccine product (→ +0.0059);
follow-up here works *against* the gradient (low-mortality trials tend to have *longer* follow-up yet
*higher* VE), so it is a conservative confounder. Internal RE slope (+0.0142) matches external metafor
REML (+0.0141) to three decimals.

### 5-way real leave-one-trial-out (`run_rota.py`) — TRUTH = real held-out logRR

| bw | MAE nma/uni/rel/**tran**/scr | cover rel/tran | tran−rel | tran−nma | rel−unif |
|---|---|---|---|---|---|
| SD/2 (17) | 0.84/0.96/0.72/**0.66**/1.00 | 1.00/1.00 | **−0.054 [−0.095,−0.012] W** | −0.181 [−0.317,−0.041] **W** | −0.246 [−0.376,−0.101] **W** |
| **SD (34)** | 0.84/0.96/0.87/**0.76**/0.89 | 0.97/0.93 | −0.110 [−0.212,+0.032] | −0.087 [−0.230,+0.075] | −0.095 [−0.141,−0.043] **W** |
| 1.5·SD (51) | 0.84/0.96/0.91/**0.76**/0.90 | 0.90/0.93 | −0.151 [−0.285,+0.037] | −0.087 [−0.258,+0.096] | −0.144 [−0.238,−0.019] **W** |

**Controls (central bw):** β=0 inertia collapses transport *exactly* onto relevance (Δ=0.0000);
**target=pool** (standardise to donor centroid, not the real target) significantly **hurts**
(+0.172 [+0.023,+0.324]). The machinery isolates the standardisation step, as designed.

**Rotavirus REPLICATES the BCG pattern exactly:** transport beats relevance-only **significantly at
the narrow bandwidth**, directional (CI crosses 0) at central/wide; transport MAE is again strikingly
**bandwidth-stable** (0.66/0.76/0.76) where relevance-only is not.

**Cross-verification (vendor seats down → from-scratch + external + methodologically-distinct):**
`selfverify_rota.py` recomputes with an **independent Mandel-Paule REML pooler + inline kernel** and
reproduces the full-k=29 central-bw deltas *exactly* (tran−rel −0.110, target=pool +0.172, β=0 inert).
`xverify_metafor.R` externally confirms the modifier. **Single-country sensitivity** (drop the 9
pooled-region rows → k=20): tran−rel stays directional **−0.069 [−0.186,+0.101]** but weakens
honestly — the effect leans on the full low-mortality gradient span, not on any single pooled anchor.

---

## 2. Aggregation — is transport-over-relevance robust once k grows? (`borrowing/agg/`)

`aggregate_transport.py` pools the **per-trial paired LOO errors** across **BCG (latitude, k=13) +
Rotavirus (U5MR, k=29) = 42 real held-out trials**, two ways (inverse-variance fixed-effect;
equal-weight), with a stratified bootstrap CI and cross-slice heterogeneity. Reported at the
pre-registered central bw [primary], narrow bw [secondary], and under an Epanechnikov kernel
[distinct 3rd witness]. See `fig_expansion_forest.png`.

### TRANSPORT − RELEVANCE (the binding incremental step)
| bandwidth / kernel | BCG | Rotavirus | **POOLED (inv-var)** | I² | verdict |
|---|---|---|---|---|---|
| **central bw (SD) — PRIMARY** | −0.049 | −0.110 | **−0.069 [−0.134, +0.004]** | 0 % | **just misses (upper CI +0.004)** |
| narrow bw (SD/2) — secondary | −0.083 | −0.054 | **−0.066 [−0.097, −0.034]** | 0 % | **WIN** |
| Epanechnikov (central) — robustness | −0.097 | −0.044 | **−0.061 [−0.090, −0.030]** | 58 % | **WIN** |

### SETTLED headlines (robust at every bandwidth and kernel)
| comparison | POOLED (inv-var), central bw | across all bw/kernels |
|---|---|---|
| **transport − NMA** (full method vs textbook) | **−0.138 [−0.240, −0.028]** | WIN at all (−0.14 … −0.20), I²≈0 % |
| **relevance − uniform** (kernel vs no-relevance) | **−0.104 [−0.146, −0.054]** | WIN at all (−0.10 … −0.22), I²≈0 % |

**Reading it honestly.** Growing the base from k=13 to **k=42** with a *second, independent* strong-
modifier slice:
- **Settles two things.** The full transportability method **robustly beats textbook NMA** (pooled
  −0.14 logRR MAE, CI<0 everywhere), and relevance-down-weighting **robustly beats the no-relevance
  null** — both now with **I² ≈ 0 %**, i.e. BCG and rotavirus agree closely.
- **Moves transport-over-relevance to the threshold, not past it.** The two slices are *homogeneous*
  (I²=0 %, Q=0.63) and *both point the same way*; the pooled point estimate is a stable **−0.07** and
  is a **clean win at 2 of 3 pre-specified bandwidths** (narrow, Epanechnikov). But at the
  **pre-registered central bandwidth the pooled 95 % CI upper bound is +0.004** — it misses
  significance by a hair. **We do not claim transport-beats-relevance is settled.** It is *directionally
  consistent, homogeneous across two independent strong-modifier fields, and on the edge of
  significance at k=42* — materially stronger evidence than the single-slice k=13 verdict, but not yet
  decisive at the conservative bandwidth.
- **Why narrow bw wins and central doesn't** (mechanism, not cherry-pick): at a narrow kernel,
  relevance-only retains very few effective donors and is noisy, so the standardisation shift adds the
  most; at a wide kernel both borrow broadly and the shift matters less. This is disclosed as a
  secondary bandwidth, not promoted to the headline.

---

## 3. Relevance multi-specialty replication — extended (`borrowing/replication/`)

`extend_multispecialty.py` adds a **new strong-modifier slice**: **bangertdrowns2004** (writing-to-learn
→ academic achievement; Bangert-Drowns, Hurley & Wilkinson 2004, *Rev Educ Res* 74:29–58), modifier =
**minutes of writing per assignment** (slope −0.020, **R²=0.466, perm p=0.0008** — the *strongest*
modifier in the education set; the documented finding that brief writing tasks help more). A third
independent Education slice (not a new specialty).

Individually it **beats the no-relevance (uniform) null** (−10.3 %, CI<0 **W**) but **not the
scrambled null** (+11.2 %, fragile at n=24). Pooled (DL random-effects, scale-free fractional MAE
reduction), now **6 clean-by-modifier slices**:

| control | before (5 slices) | **after (6 slices)** | verdict |
|---|---|---|---|
| relevance − **uniform** (no-relevance) | −10.9 % [−20.2 %, −1.5 %] | **−10.4 % [−18.0 %, −2.8 %]** τ²=0.006 | **ROBUST, tighter** |
| relevance − scrambled | −12.4 % [−22.8 %, −2.0 %] | **−8.5 % [−18.3 %, +1.2 %]** τ²=0.010 | **now crosses 0** |

**Honest update:** the **no-relevance result is the more robust of the two controls** — it survives and
tightens with a 6th independent slice. The vs-scrambled result was more fragile: a strong-modifier
slice whose kernel doesn't beat a *permuted-modifier* control on held-out point prediction (n=24,
leverage-prone) pulls the scrambled pool back across 0. The core relevance claim — *borrowing helps
vs not using the modifier at all* — stands across 6 clean slices in 3 specialties.

---

## 4. Cycle-2 consolidation — maximal inference from the real k=42 (`borrowing/agg/consolidate_transport.py`)

This cycle set out to add a **third** deposited placebo-controlled gradient-spanning strong-modifier
slice. **None qualified under the truth-first bar** (documented search log below). Rather than force a
low-quality slice, `consolidate_transport.py` extracts the maximum honest inference from the real 42
held-out trials with methods that need **no new data**, and an **independent base-R engine**
(`verify_consolidate.R`, distinct language, re-implements the whole 5-way LOO from the raw JSON)
re-derives every headline. Findings at the pre-registered central bandwidth (SD):

- **Distribution-free per-trial evidence is significant.** Pooling all 42 paired LOO deltas
  `d_i = |μ_tran,i − y_i| − |μ_rel,i − y_i|` (equal weight per trial): pooled mean **−0.091**,
  **33/42 trials favour transport**. Sign-flip permutation (exact null: d symmetric about 0)
  **one-sided p = 0.022**; Wilcoxon signed-rank **p = 0.0003**; exact binomial sign test **p = 0.0001**.
  R engine reproduces: 33/42, sign-flip p = 0.022, Wilcoxon p = 0.0003 (per-slice means match to
  ≤0.0013; the tiny gap is purely numpy population-SD vs R sample-SD in the bandwidth — the result is
  robust to it).
  **Honest caveat:** the 42 deltas are LOO estimates over *overlapping* donor sets, so they are not
  fully independent — these per-trial tests are the **less-conservative** bound.
- **The conservative 2-slice inverse-variance pool remains on the threshold.** Between-slice IV pool
  **−0.069 [−0.140, +0.003]** (central bw); RE(DL) pool identical (τ²=0, I²=0); the k=2 prediction
  interval [−0.53, +0.39] is essentially uninformative and reported only for transparency. This is
  the number we do **not** claim as a win.
- **The central-bw miss is a narrow local dip, not a general failure.** A fine bandwidth sweep
  (0.4–1.6 × SD) gives a pooled 95 % CI **< 0 at 11 of 13 widths**; only **1.0 and 1.1 × SD cross 0**.
  The pre-registered primary (1.0) happens to land in the one dip. We keep the pre-registered
  "on-threshold" verdict, but the surrounding bandwidth stability materially strengthens the read.
- **Neither slice alone carries it** (leave-one-slice-out: BCG-only −0.049 [−0.136,+0.038]; rota-only
  −0.110 [−0.235,+0.015] — both cross 0 at reduced k, both same sign), and both point the same way.
- **Quantified rate-limiter.** Under the observed homogeneity (I²=0) and effect (−0.069), a precision
  projection says **≈ 1 additional comparable slice** (same effect, same mean per-slice precision)
  would push the conservative central-bw 95 % CI below 0. This is a precision projection, **not** a
  claim that such a slice was found.

**Net:** the weight of evidence for the incremental transport step has strengthened (distribution-free
tests significant; CI<0 across almost the whole bandwidth range), but the pre-registered conservative
between-slice pool at the central bandwidth still just crosses 0. **Verdict unchanged and honest:
still directional / on-threshold at k=42.**

### Deposited-data search log (why no 3rd slice this cycle)
Truth-first requires a *deposited or single-table* per-trial 2×2 + a continuous **external** population
covariate; the program explicitly forbids multi-paper hand transcription (the rota deposited-CSV route
is the model). Checked this cycle:
- **metadat (116-dataset manifest).** Only `dat.bcg` / `dat.colditz1994` carry a latitude/U5MR-type
  external gradient — and `dat.colditz1994 ≡ dat.bcg` (already the primary slice; would double-count).
  No other on-disk or fetchable metadat set has a clean external population gradient.
- **Oral cholera vaccine** (HopkinsIDD/kOCV-review deposit; Lancet GH 2025). Only **~2–3
  placebo-controlled RCTs**, and the modifiers (age <5 vs ≥5, endemicity) are categorical/within-class,
  not a continuous external population gradient. k too small; no clean gradient. **Rejected.**
- **RTS,S malaria vaccine by transmission intensity** (White 2013 phase-2 pooled; a genuine strong
  gradient, VE 60 %→4 % by PrP2-10). Raw data is **GSK-private**; the site table gives **no per-arm
  case counts** and no per-site efficacy — cannot build the 2×2 without an IPD data request. **Rejected.**
- **Vitamin-A / deworming child-mortality by baseline mortality** (the textbook baseline-risk gradient).
  Exists only as **paper-table transcriptions** (Beaton 1993 / Fawzi 1993 / Imdad Cochrane); no
  machine-readable per-arm deposit located. Transcription is forbidden by the program. **Deferred to a
  future data-acquisition (non-headless) session** as the most promising lead.

**Conclusion:** clean deposited transport slices are *structurally rare* exactly as pilot-4 predicted;
the rate-limiter is **data acquisition, not analysis**. The single highest-value next action is to
obtain one more machine-readable deposited per-arm dataset with a continuous external gradient
(vitamin-A baseline-mortality is the best lead) — the I²=0 projection says one such slice likely settles
the central-bw pool.

---

## 5. Third slice — a CROSS-DOMAIN strong-modifier test + scale-free 3-slice pool

An independent public-data scout (fable sub-agent, its gate numbers re-verified here) confirmed
**no external population/geographic gradient slice exists on disk** beyond BCG/rota — but flagged
one dataset that decisively clears the same strong-modifier gate: **`dat.raudenbush1985`**
(Raudenbush 1984, teacher-expectancy experiments; `borrowing/raudenbush/`). k=19 controlled
experiments (induced-expectancy vs control), effect = SMD (Hedges g), modifier = **weeks of prior
teacher-pupil contact** before the induction (0-24). The modifier is strong and leverage-robust
(**Spearman ρ=−0.80, perm p=0.0001**; DL slope −0.0165/week, perm p=0.015; survives year + setting
adjustment) — the classic finding that expectancy effects vanish once teachers already know the pupils.

**Why include it, and the honest caveat.** `weeks` is an *external, study-level covariate shared
across arms and known a-priori* for a target study — structurally exactly what the transport
g-computation step needs, so the **method** applies unchanged. The caveat: it is a
*procedural/contextual* moderator in **education**, not an epidemiological population gradient like
latitude/U5MR. So it does **not** answer "does an external population gradient exist on disk" (it
doesn't) — it tests a *different, valuable* question: **does the transport-over-relevance mechanism
generalise beyond vaccine-epidemiology?**

### raudenbush 5-way real-LOO (`run_raudenbush.py`) — it REPLICATES the BCG/rota pattern
| bw | MAE rel/**tran** | tran−rel | controls |
|---|---|---|---|
| SD/2 | 0.234/**0.217** | **−0.018 [−0.031,−0.004] W** | — |
| **SD (central)** | 0.237/**0.221** | −0.016 [−0.038,+0.010] | β=0 inert (Δ=0.0000); target=pool hurts +0.044 |
| 1.5·SD | 0.244/**0.220** | −0.024 [−0.062,+0.018] | — |

Same signature as BCG and rotavirus: **clean win at the narrow bandwidth, directional at central,
transport MAE bandwidth-stable, β=0 collapses onto relevance exactly, target=pool hurts.** A third
independent reproduction of the mechanism, now in a non-clinical domain on the SMD scale.

### Scale-free 3-slice pool (`borrowing/agg/consolidate3_transport.py`)
SMD cannot be pooled with logRR by mixing raw errors, so all three are combined ONLY by
scale-invariant metrics (central bw):

| scale-free metric across BCG+rota+raudenbush (k=61, 2 domains) | result |
|---|---|
| trials favouring transport (exact binomial sign test) | **46/61, one-sided p < 0.0001** |
| standardised pooled mean delta (units of rel-MAE), sign-flip test | −0.102, **p = 0.008** |
| fractional MAE reduction, equal-weight 3 slices (stratified bootstrap) | **−9.7% [−17.6%, −0.9%] CI<0** |
| RE (DL) pool of the 3 fractional reductions (I²=0, τ²=0) | **−9.1% [−16.8%, −1.4%] CI<0** |
| per-slice fractional reduction (all same sign) | BCG −9.9%, rota −12.7%, raudenbush −6.6% |
| **leave-one-slice-out** (drop each; does the pool stay CI<0?) | **NO — every single drop crosses 0** (drop BCG −9.7% [+0.2%], drop rota −8.2% [+2.5%], drop raudenbush −11.3% [+0.8%]) |
| **95% prediction interval** (t₂, across-slice generalisation) | **[−26.1%, +7.8%] — includes 0** |

**Honest full-inference verdict (`consolidate3_transport.py`, all five tests):** beyond k=13 the
scale-free evidence for transport-over-relevance is **materially strengthened but still DIRECTIONAL,
not decisively settled.** The pooled point estimate is a stable **−9 to −10 %**, both the equal-weight
and random-effects pooled CIs exclude 0, the sign test is strong (p<0.0001), and all three slices agree
across two domains — *but* the pooled win does **not survive leave-one-slice-out** (removing any single
slice pushes the CI across 0), and the **95 % prediction interval includes 0** (with only 3 slices a 4th
could fall either side). So: consistent, cross-domain, pooled-significant, yet fragile to any one slice.
The sign test also carries the §4 LOO-overlap independence caveat, so the fractional/RE bootstrap + LOSO
are the load-bearing tests, not the sign p. **Reported both ways:** the *domain-matched raw-logRR*
central-bw IV pool (BCG+rota, §2) is unchanged and on-threshold (−0.069 [−0.140,+0.003]). The strongest
qualitative signal remains that the mechanism *reproduces* in education SMD exactly as in vaccine logRR
(clean narrow-bw win, β=0 inert, target=pool hurts) — evidence it is general, pending a 4th slice to
harden the pooled inference.

## What is settled vs still open

**Settled (robust, homogeneous, k=42 / 6 slices):**
1. **Transportability-standardisation beats textbook NMA** — pooled −0.14 logRR MAE, CI<0 at every
   bandwidth and kernel, I²≈0 % across BCG and rotavirus.
2. **Relevance down-weighting beats the no-relevance null** — pooled −0.10 (transport LOO) and
   −10.4 % (multi-specialty, 6 slices), both CI<0.
3. The **standardisation control** behaves correctly in both transport slices (β=0 inert;
   target=pool hurts +0.17–0.19) — the gain is real-target g-computation, not generic shrinkage.

**Transport's incremental gain OVER relevance-only — strengthened to a scale-free win, domain-matched
still on threshold (§4, §5):**
- **Scale-free, 3 slices, 2 domains (k=61): DIRECTIONAL, materially strengthened, not decisively
  settled.** Pooled fractional reduction −9.7 % [−17.6 %, −0.9 %] and RE −9.1 % [−16.8 %, −1.4 %] both
  exclude 0; 46/61 trials favour transport (sign p<0.0001); mechanism reproduces in education (SMD)
  exactly as in vaccine-epi (logRR). BUT the pooled win does **not survive leave-one-slice-out** (any
  single drop crosses 0) and the **95 % prediction interval includes 0** — so it is consistent and
  pooled-significant yet fragile at k=3 slices. A **4th** strong-modifier slice is needed to harden it.
- **Domain-matched raw-logRR (BCG+rota only): still on threshold.** The pre-registered central-bw IV
  pool is unchanged at −0.069 [−0.140, +0.003]. A third *logRR population-gradient* slice would settle
  this one directly; the scout confirms none is on disk (see below).
- **The scrambled-null relevance control** is more fragile than the no-relevance control (6-slice pool
  crosses 0). Worth flagging in any relevance claim.

**Data-availability finding (this cycle, fable scout + re-verified):** across the entire on-disk
`F:\public-data\`, the ONLY dataset with a strong external gradient beyond BCG/rota is a *procedural*
(education) modifier, not a population/geographic one. ISRCTN/OWID carry no per-trial effects; the
other web-source dirs are empty. **A 3rd logRR population-gradient slice does not exist on disk.**

**4th-slice reachability (dedicated fable check over `F:\public-data\` + the full AACT snapshot
`F:\AACT-storage\AACT\2026-04-12`) — genuine NO for all three candidate families, needs a
non-headless deposited fetch (NOT forced):**
- **vitamin-A / zinc → child mortality by baseline U5MR:** U5MR covariate is on-disk (`owid/u5mr.csv`),
  but the gradient-spanning child-mortality trials (Nepal/Ghana/Sudan/Indonesia, 1980s–90s) *predate*
  ClinicalTrials.gov; the ≤13 AACT vitamin-A mortality trials are high-income cancer/ICU/transplant
  survival, no child-mortality gradient. Needs a deposited/published-table fetch.
- **pneumococcal / Hib / pertussis efficacy by region/latitude:** placebo-controlled trials with a
  *disease-efficacy* outcome + posted results number **4 / 0 / 0** (all <8), and the pneumo ones are
  multi-country (no clean per-trial latitude).
- **IPTi / IPTp / antimalarial by transmission intensity:** of 49 placebo+efficacy malaria trials with
  results, only 18 single-country; of those only 3 African LMIC (all Uganda → zero gradient), the rest
  US/EU controlled-human-malaria-infection challenge studies; transmission intensity is not on-disk
  (needs Malaria Atlas). AACT structurally compresses the geographic gradient for all three families.

So the domain-matched logRR pool cannot be hardened from on-disk data; a 4th slice requires a deposited
web fetch (child-mortality tables / regional vaccine-efficacy publications / transmission atlas + IPTp
extraction) — deferred to a non-headless data session, per the truth-first rule against forcing it.

---

## Files
`borrowing/rota/`: `prep_rota.py`, `rota_trials.json`, `run_rota.py`, `rota_loo.json`,
`selfverify_rota.py`, `xverify_metafor.R`, `rotavirus_extracted_clark2019.csv`.
`borrowing/agg/`: `aggregate_transport.py`, `aggregate_results.json`, `make_expansion_fig.py`,
`fig_expansion_forest.png`.
`borrowing/replication/`: `extend_multispecialty.py`, `bangertdrowns_entry.json`.

## Provenance / integrity
- Rotavirus counts: verbatim from Clark 2019's deposited `rotavirus_vaccine_efficacy_extracted.csv`
  (peer-reviewed, GitHub-deposited); U5MR from OWID child-mortality (country × year).
- BCG counts: Colditz 1994 *JAMA* / Berkey 1995 *Stat Med* (metadat `dat.bcg` redistribution vehicle).
- bangertdrowns: metadat `dat.bangertdrowns2004` (Bangert-Drowns 2004 *Rev Educ Res*).
- Cross-vendor: Codex seats (laptop `100.80.183.43`, pc2) publickey-denied in this non-interactive
  session; per the standing rule every headline is confirmed ≥3 internal ways (primary ubcma pooler +
  from-scratch MP-REML + Epanechnikov robustness) + external metafor + from-scratch recompute.
