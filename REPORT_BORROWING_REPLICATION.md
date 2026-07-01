# Borrowing-Field Replication — is the relevance-weighted-borrowing win a one-slice fluke or reproducible?

> *Branch:* `methods-borrowing` (F:\ubcma) · *Date:* 2026-06-30 · *Owner:* Mahmood
> *Builds on:* `borrowing/REPORT_BORROWING_PILOT2.md` (the single validated win:
> relevance-weighted borrowing beats both nulls on **GLP1 dose → HbA1c**, n=12).
> *Question this decides:* does that win **replicate** on additional, independent
> AACT slices, or is it a one-slice artefact? Truth-first — non-replications and
> honest failures are reported as informative, not hidden.

## TL;DR — verdict: **REPLICATED as a phenomenon, but bounded (N=2 clean slices)**

Screening **11 condition/outcome/drug-class domains** of AACT for a *real
within-class continuous effect-modifier* (the analog of GLP1 dose), only **two
slices carry a permutation-robust, Simpson-proof modifier**. On **both** of those,
relevance-weighted borrowing **beats both nulls** on real held-out effects:

| slice (modifier) | n | rel−uniform [95% CI] | rel−scrambled [95% CI] | beats both? |
|---|---|---|---|---|
| **GLP1 dose → HbA1c** (anchor, reproduced) | 12 | **−0.180 [−0.305, −0.037]** | **−0.199 [−0.334, −0.045]** | **YES** |
| **GLP1 baseline-weight → weight loss** (NEW) | 9 | **−0.497 [−1.055, −0.099]** | **−0.599 [−1.250, −0.028]** | **YES** |

The new slice replicates the win on a **different outcome** (body weight, kg) and a
**different modifier *type*** (baseline severity, not dose) — so the effect is not
specific to "dose" or to "HbA1c". It is **2/2 on clean qualifying slices**, and the
method is correctly **inert on 3/3 real flat slices** (the in-data β=0 negative
control). The scale-free pooled fractional MAE reduction is **−25.8% [−51.2%, −0.4%]
vs the scrambled null (robust)** and **−23.3% [−48.5%, +1.9%] vs the no-relevance
null (suggestive, CI just crosses 0 at N=2)**.

**So: stronger than single-slice — the win reproduces on an independent modifier —
but not yet a tightly-pooled multi-class result.** The binding constraint is the
*scarcity* of clean within-class permutation-robust modifiers in registry data, the
same wall hit by pilots 1/3/4. Both clean slices are GLP1-class; n is small (9–12).

---

## 1. What "qualifying" means (pre-registered, Simpson-proofed)

A slice may enter the borrowing test **only if its modifier is genuinely present**.
Pilot-3 was killed by the Simpson trap (a cross-class gradient masquerading as a
within-class modifier), so the screen (`replication/screen_v2.py`) requires, per
candidate (condition × outcome × class/molecule × modifier):

1. **n ≥ 8 trials**, ≥ 4 unique modifier values, real spread.
2. **RE meta-regression slope CI excludes 0** (Wald).
3. **Permutation p < 0.05** (2000 perms of the modifier vs effect) — the *honest*
   arbiter; it down-ranks slices whose tight Wald CI is an artefact of a few
   ultra-precise points (see vortioxetine below).
4. **Simpson guard**: single-molecule slices are Simpson-proof by construction
   (drug identity fixed); multi-molecule slices must additionally keep their slope
   sign **within-molecule** (mean-centred per drug) and survive a covariate-adjusted
   re-fit.

Slices are tiered **clean** (qualify), **nearmiss** (real slope, permutation
borderline), or **flat** (no signal — kept as in-data negative controls).

## 2. The five-way real leave-one-trial-out (same gate as pilot-2)

`replication/run_slice.py`. For each held-out real trial *t* (the target, **zero
own data → a pure transportability prediction**) a prior is formed from the **other
real trials** four ways, scored against the trial's **real observed effect** y_t:

* **NMA** — random-effects (REML) pooled mean of the others *(textbook baseline)*
* **uniform** — 1/se² precision-only field mean *(= no-relevance null)*
* **relevance** — Gaussian modifier-distance kernel × precision *(the thesis)*
* **scrambled** — relevance kernel with the modifier permuted *(scrambled null)*

MAE + 95% prediction-interval coverage + paired bootstrap (4000) of relevance MAE
minus each null's MAE (CI < 0 ⇒ relevance better). Bandwidths {SD/2, SD, 1.5·SD};
verdict at the central bandwidth = SD. **Binding: relevance beats BOTH nulls.**

## 3. Slices tried, and which qualified

| domain | outcome | modifier(s) screened | result |
|---|---|---|---|
| T2DM | HbA1c | **GLP1-class dose** | **CLEAN** — slope −0.092 [−0.115,−0.069], permp 0.010, R²0.93, within-mol −0.071 (p .024) |
| T2DM | HbA1c | dapagliflozin dose | flat — slope −0.008, permp 0.56 (SGLT2 dose plateaus) → **negative control** |
| T2DM | HbA1c | cross-class dose; baseline | flat — slope ≈0 (Simpson when classes mixed) → **negative control** |
| Obesity | body weight | **baseline weight/BMI** | **CLEAN** — slope −0.137 [−0.192,−0.081], permp 0.002, R²0.58, within-mol −0.115 (p .069) |
| Obesity | body weight | tirzepatide dose (1-mol) | nearmiss — slope −1.77, R²1.00, **permp 0.109** |
| Obesity | body weight | GLP1-class dose | nearmiss — slope −0.52, R²1.00, permp 0.149, within-mol −1.58 (p<.001) |
| Depression | MADRS/HAMD | vortioxetine dose (1-mol) | flat by permutation — Wald CI excludes 0, R²1.00, **but permp 0.605** |
| Depression | MADRS/HAMD | SSRI-class dose; baseline | Simpson — pooled +0.005 n.s., **within-mol −0.055 (p<.001)** |
| Schizophrenia | PANSS/BPRS | antipsychotic dose; baseline | Simpson — pooled +0.004 (R² invalid), within-mol −0.066 (p .005) |
| Lipid | LDL | statin dose | **insufficient** — only 4 statin-vs-placebo LDL MD trials in AACT |
| Hypertension | SBP / DBP | CCB/ARB dose | **insufficient** — < 8 placebo-anchored trials (azilsartan-dominated) |
| ADHD; Alzheimer; Pain | ADHD-RS; ADAS/MMSE; VAS | stimulant/AChEI/gabapentinoid dose | **insufficient** — sparse placebo-anchored MD with parseable dose |

**Two clean, two near-miss, several Simpson, three flat, six insufficient.**

## 4. Per-slice five-way results (central bandwidth = SD)

```
slice                              tier      n   relMAE  uniMAE  scrMAE   NMA   rel-unif[CI]            rel-scr[CI]            beats both
GLP1 dose -> HbA1c                 clean    12   0.269   0.449   0.467  0.439  -0.180[-0.305,-0.037]W -0.199[-0.334,-0.045]W   YES
GLP1 baseline-weight -> weight     clean     9   3.190   3.688   3.789  3.248  -0.497[-1.055,-0.099]W -0.599[-1.250,-0.028]W   YES
tirzepatide dose -> weight         nearmiss 11   3.810   4.557   4.209  2.261  -0.746[-1.535,+0.018]  -0.399[-1.609,+0.669]    no
GLP1 dose -> weight                nearmiss 17   3.216   3.609   3.249  2.951  -0.393[-0.712,-0.051]W -0.033[-0.692,+0.575]    no
vortioxetine dose -> MADRS         flat*    17   2.107   2.158   1.748  1.220  -0.051[-0.248,+0.059]  +0.359[+0.056,+0.736]    no
dapagliflozin dose -> HbA1c        flat     15   0.147   0.142   0.145  0.142  +0.005[+0.003,+0.008]  +0.002[-0.005,+0.010]    no
cross-class dose -> HbA1c          flat     36   0.373   0.371   0.372  0.389  +0.002[-0.013,+0.018]  +0.001[-0.024,+0.020]    no
```
*vortioxetine: permutation-flat though Wald-significant; see §6.

## 5. Aggregated replication verdict

Scale-free fractional MAE reduction (slices differ in units), DL random-effects
pooled across the **2 clean** slices (`replication/aggregate.py`):

* relevance − scrambled null: **−25.8% [−51.2%, −0.4%] → CI < 0, robust**
* relevance − no-relevance (uniform) null: **−23.3% [−48.5%, +1.9%] → suggestive,
  CI marginally crosses 0** (N = 2 is too few for a tight pooled bound)
* **Beats both nulls in 2/2 clean slices.** Inert in **3/3 flat** slices
  (|fractional advantage| < 4% vs uniform — the in-data β = 0 negative control,
  reproducing pilot-2's simulated β = 0 inertia on *real* data).

## 6. Honest failures and what they teach (the informative part)

* **vortioxetine dose → MADRS** (single-molecule, R² = 1.00, Wald CI excludes 0)
  **fails the permutation gate (p = 0.605)** and, decisively, **fails LOO**:
  out-of-sample the dose-kernel is *worse* than the scrambled null (rel−scr +0.359)
  and far worse than plain NMA (rel−NMA +0.89). Its tight Wald CI was an artefact of
  a few ultra-precise points. **The permutation gate caught a modifier that would
  have produced a false positive — it is doing its job.**
* **tirzepatide dose → weight** (R² = 1.00 in-sample) **fails LOO** because the
  tirzepatide field is so homogeneous/precise that plain NMA already predicts the
  held-out effect well (NMA MAE 2.26 ≪ relevance 3.81). A steep in-sample slope does
  **not** imply out-of-sample borrowing value when the field is tight.
* **Depression & schizophrenia class-dose** are textbook **Simpson**: pooled slope
  ≈ 0 / wrong sign, but within-molecule strongly negative (p < .001). Real signal
  exists *within molecule* but the registry doesn't supply ≥ 8 placebo-anchored
  trials of one molecule across a clean dose range — so they cannot (yet) qualify
  without risking the pilot-3 artefact. **Flagged as the most promising future
  slices** if IPD or more single-molecule dose-finding trials become available.

## 7. Caveats (what bounds the claim)

1. **N = 2 clean slices.** The phenomenon replicates per-slice, but the pooled CI
   vs the *no-relevance* null marginally includes 0. This is a replicated effect,
   **not** a precisely meta-analysed multi-class estimate.
2. **Both clean slices are GLP1-class.** Replication spans outcome (HbA1c vs weight)
   and modifier type (dose vs baseline severity) but **not drug class**. A
   non-GLP1 clean slice remains the key missing piece.
3. **Small per-slice n (9–12)** and AACT's reliance on reported mean-difference CIs
   limit which therapeutic areas are reachable (statins, antihypertensives,
   ADHD/Alzheimer were all data-starved at the active-vs-placebo MD level).
4. The GLP1 "dose" axis partly encodes molecule potency (per pilot-2's honesty
   note); the within-molecule guard (−0.071, p = .024) shows a real residual
   within-molecule slope, but it is not a pure single-molecule dose axis.

## 8. Cross-vendor confirmation

External vendors down on this host (unchanged from pilots 1–4): **Codex** pc1
`refresh_token_invalidated` (401), pc2 `Permission denied (publickey)`; **agy**
returns empty in `-p`. Per the program fallback, the headline is confirmed
**≥ 3 independent internal ways + a from-scratch re-derivation**:

1. `run_slice.py` — primary (kernel = `borrowing_field2.covariate_prior`, NMA = `ubcma.comparators.reml_estimator`).
2. `selfverify_replication.py` — **from-scratch, inline numpy only, no shared
   functions**: reproduces both clean slices to the decimal (rel−uniform −0.180 /
   −0.497; rel−scrambled −0.199 / −0.599).
3. `screen_v2.py` — independent RE meta-regression + 2000-perm test detecting each
   modifier (slope, permutation p, within-molecule guard).
4. `aggregate.py` — independent pooling layer (scale-free fractional reductions).

## 9. Bottom line

The relevance-weighted-borrowing win is **no longer single-slice**: it **replicates**
on an independent slice with a different outcome and a different modifier type, while
staying correctly **inert on real flat slices** and **failing honestly** where the
modifier is out-of-sample-unreliable. It is therefore a **reproducible phenomenon,
bounded by N = 2 clean GLP1-class slices** — a genuine strengthening of pilot-2, but
short of a tightly-pooled, multi-drug-class result. **The rate-limiting step for a
fully robust contribution is finding (or building, via IPD) a non-GLP1 slice with a
clean, permutation-robust within-class modifier** — the depression/schizophrenia
within-molecule dose signals are the leading candidates.

## Reproduce
```
cd F:\ubcma\borrowing\replication
python screen_v2.py                 # screen 11 domains -> all_slices_trials.json, qualifying_slices_v2.json
python run_slice.py                 # 5-way LOO on the curated set -> loo_results_v2.json
python aggregate.py                 # tiered verdict + pooled fractional reduction
python selfverify_replication.py    # from-scratch re-derivation of the 2 clean slices
```
Pre-registered constants: qualify gate (n≥8, permp<0.05, ≥4 unique x, within-mol
sign guard); kernel bandwidth = modifier SD; paired bootstrap 4000; seeds fixed.
