# Borrowing-Field Pilot 3 — does TRANSPORTABILITY (standardise to a target population + down-weight non-transporting trials) beat relevance-only borrowing?

> *Branch:* `methods-borrowing` (F:\ubcma) · *Date:* 2026-06-30 · *Owner:* Mahmood
> *Builds on:* `REPORT_BORROWING_PILOT2.md` (pilot-2 gate = **YES**: relevance is real
> when a covariate genuinely predicts effect; own⊕prior fixed by conflict-discounted
> precision fusion).
> *Question this pilot decides (design-brief Gap 2, the genuinely novel core):* is
> **transportability** — standardising borrowed evidence to a defined TARGET population
> and down-weighting trials whose population does not transport — a real improvement
> *over relevance-only borrowing*, or does it add nothing?

## TL;DR — verdict: **NO on this real slice — relevance-only is the contribution here.** (The transport machinery is provably correct; the real population-modifier is just too weak.)

On a **real** T2DM HbA1c slice with real recruiting countries (AACT) joined to real
population obesity (World Bank), transportability-weighted borrowing **does not beat
relevance-only** on leave-one-trial-out prediction of real held-out effects
(ΔMAE **+0.022 [−0.037, +0.082]**, n.s.; independently reproduced **+0.005
[−0.019, +0.030]**). The reason is honest and specific: **the population obesity
covariate carries essentially no effect-modification signal once drug class is known**
(class-adjusted slope **−0.002**, permutation **p = 0.97**; real within-class slope
**β ≈ 0.006 %HbA1c per obesity-%**). With no population signal to exploit, standardising
to the target and down-weighting non-transporting trials only adds noise.

This is **not** a machinery failure. A calibrated sim with the *same real trial
structure* but a **known, tunable** obesity slope shows the transport layer is correct
and powerful: it is **inert at β = 0** and when **target = donor pool** (the two negative
controls), **reproduces the real-data null exactly at the real β = 0.006**, and then
**robustly, monotonically beats relevance-only once β ≳ 0.02** (transport MAE stays flat
at 0.228 while relevance MAE blows up to 1.58 at β = 0.10). So the thesis is sound in
principle; **this particular evidence base simply lacks a strong population-transportable
modifier.**

**Recommendation:** relevance-only (pilot-2) is the validated contribution. Transportability
is a correct, ready layer that should be re-tested on a slice where a population covariate
is a *strong* effect modifier (the sim says β ≳ 0.02 is the threshold) — e.g. an outcome/
covariate pair with documented ancestry- or adiposity-driven effect modification — before
claiming it as a contribution. **Do not over-claim transportability on the registry-wide
field yet.**

---

## 1. The slice + target (real populations, real covariate)

Same pilot-2 AACT T2DM HbA1c slice, now joined to **populations**:

- **Trial → countries:** AACT `countries.txt` (real recruiting countries; 38/46 trials
  have country data, 12 are **single-country** — the clean population anchors:
  US ×5, Japan ×4, China ×2, India ×1).
- **Country → population covariate:** World Bank **adult obesity prevalence**
  (`SH.STA.OB18`, BMI > 30, 18+, mean of male+female; latest year per country). This is
  the mechanistically-correct effect-modifier axis for T2DM drug response — the
  **East-Asian low-adiposity / insulin-deficient phenotype**: US **36.2 %**, UK 27.8 %,
  Canada 29.4 % vs **Japan 4.2 %, China 6.2 %, India 3.9 %**.
- **Trial population covariate** = mean obesity over its recruiting countries (WB-covered).
- Diabetes prevalence (`SH.STA.DIAB.ZS`) carried as a secondary covariate.
- Crosswalk (`F:\Projects\who-data-lakehouse\src\who_data_lakehouse\crosswalk.py`) confirmed
  WHO-ISO3 ↔ IHME ↔ WB alignment; the WB join is by country name with a small alias map.

**Target = a population, not just another trial.** Each held-out single-country trial is
treated as a target *population* whose covariate `ob_t` comes from World Bank (population
data, independent of the trial's effect) — a genuine transportability prediction.

*(Honesty note: World Bank `SH.STA.OWGH.ZS` ("overweight") is a **children-under-5**
indicator and was rejected after its values came back implausible — US 9.5 %. The adult
`SH.STA.OB18` series is the correct one. 7 countries — incl. South Korea, Russia, Taiwan —
lack obesity coverage; their trials contribute via covered co-recruiting countries, and all
12 single-country targets are fully covered.)*

---

## 2. Is the transport signal real? (binding requirement 3 — checked FIRST)

`probe_transport.py` — RE meta-regression of effect on population obesity, with a
permutation test, **before any borrowing machinery**:

| model | obesity slope | perm p | reading |
|---|---|---|---|
| marginal `y ~ obesity` | −0.034 /SD | 0.65 | n.s. |
| **+ drug-class fixed effects** | **−0.002 /SD** | **0.97** | **signal vanishes — proxies class** |
| within GLP1 (n=17) | +0.044 /SD (z +1.65) | 0.84 | weak |
| within SGLT2 (n=13) | +0.051 /SD (z +1.47) | 0.21 | weak |
| within DPP4 (n=6) | +0.140 /SD (z +3.36) | 0.14 | suggestive but n=6 |
| residual corr (after class) | −0.023 | — | ≈ 0 |

**Finding:** the within-class obesity slope is **directionally consistent** across all three
classes (positive: higher-obesity populations get *smaller* HbA1c reductions — the expected
East-Asian-responsiveness direction), and the marginal sign reverses only by class
confounding (a Simpson reversal: high-efficacy GLP1 is tested more in high-obesity US). But
the magnitude is tiny and **not robust after class** (pooled within-class
**β ≈ 0.0061 %HbA1c/obesity-%**; per class GLP1 0.0053, SGLT2 0.0051, DPP4 0.0131). Honest
power: only DPP4 hints at a real slope and it has **n = 6**. **The population covariate does
not add over relevance (= class + baseline) on this slice.**

---

## 3. The 5-way comparison (real LOO on single-country targets)

`run_pilot3.py` — held-out single-country trial = target (ZERO own data → pure
transportability prediction); prior built from all other trials; truth = real `y_t`;
paired bootstrap over the 12 folds. Borrowing weight = **relevance(class,baseline) ×
transportability(obesity kernel + standardisation) × precision**.

| method | mean abs error (real `y_t`) |
|---|---|
| standard NMA (precision only) | 0.354 |
| **relevance-only** (pilot-2 winner; no population data) | **0.293** |
| relevance × transportability (the thesis) | 0.314 |
| scrambled (obesity permuted) | 0.316 |

Paired-bootstrap contrasts (Δ < 0 = first method better):

| contrast | ΔMAE [95 % CI] | verdict |
|---|---|---|
| relevance − NMA | **−0.062 [−0.119, −0.007]** | **relevance WINS** (pilot-2 reproduced) |
| **transport − relevance** | **+0.022 [−0.037, +0.082]** | **n.s. — transport does NOT beat relevance** |
| transport − NMA | −0.040 [−0.125, +0.037] | n.s. |
| transport − scrambled | −0.001 [−0.080, +0.068] | n.s. |

Coverage of real `y_t` = **0.92** for all methods (apples-to-apples). The single-country
targets are **all** far from the donor median on obesity (Asian very-low, US high), so the
real anchor has **no near-target regime** — that inert regime is supplied by the controls
below and the sim.

---

## 4. Negative controls (binding requirement 2)

| control | result | reading |
|---|---|---|
| **NEW: target population = donor pool** (`ob_t := median`) | transport − relevance = **+0.004 [−0.004, +0.012]** | **INERT** — when the target *is* the trials, transport correctly collapses to relevance-only |
| **β_ob = 0** (standardisation off; carry-over from pilot-2) | **+0.000 [−0.021, +0.022]** | inert — no signal, no effect |
| scrambled obesity | transport − scrambled n.s. | the kernel has nothing real to grip (consistent with §2) |

Both required negative controls behave exactly as a correct transport layer must.

---

## 5. The machinery IS correct — calibrated sim with known truth (binding requirements 1 + 2 + 4)

`sim_transport.py` — keep the **real** trial structure (real classes, real obesity, real
SEs of all 38 trials); regenerate effects under a known DGP
`y = a_class + β·(ob − ob_ref) + ε` so the obesity slope **β is known and tunable**; LOO-predict
the same 12 targets; score to **known truth μ\***; sweep β:

| true β | MAE NMA | MAE relevance | MAE transport | transport − relevance [95 % CI] | |
|---|---|---|---|---|---|
| 0.000 | 0.278 | 0.222 | 0.228 | +0.006 [+0.004, +0.008] | inert (tiny kernel cost) |
| **0.006 (real)** | 0.266 | 0.228 | 0.228 | **+0.000 [−0.003, +0.003]** | **n.s. — reproduces the real null** |
| 0.020 | 0.360 | 0.339 | 0.228 | **−0.111 [−0.118, −0.104]** | **TRANSPORT WINS** |
| 0.050 | 0.754 | 0.777 | 0.228 | **−0.549 [−0.559, −0.538]** | **TRANSPORT WINS** |
| 0.100 | 1.556 | 1.580 | 0.228 | **−1.352 [−1.364, −1.340]** | **TRANSPORT WINS** |

**Transport MAE stays flat at 0.228 across the entire sweep** (it standardises the
population shift away), while NMA and relevance-only blow up as β grows because neither can
account for the target population being far from the donors. The crossover is at
**β ≈ 0.01–0.02**, ~2–3× the real value. So:

- **inert at β = 0 and target = pool** ✔ (controls)
- **reproduces the real-data null at the real β** ✔ (why §3 is n.s.)
- **robustly + monotonically beats relevance-only + nulls once the population modifier is
  strong** ✔ (the thesis works *when the signal exists*)
- **no harm** beyond a tiny (+0.006) inert-regime kernel cost when β = 0.

The binding requirements are therefore met *as functions of the signal*: transport beats
relevance-only and the nulls **in the transport-relevant regime that has a real modifier**,
is inert when there is none, and never harms materially. **This real slice sits in the inert
corner.**

---

## 6. Cross-vendor confirmation (requirement 4)

Both external vendors remain down on this host (as in pilots 1–2, re-checked this run):
- **Codex** (local & pc2 `100.127.107.46`): `401 token_invalidated`; pc2 SSH connects but
  refuses non-interactive command exec.
- **agy**: present on PATH, returns empty in `--print`.

Per the program's fallback, the headline is confirmed **≥3 independent internal ways + one
methodologically-independent re-derivation**:
1. `probe_transport.py` — meta-regression: population signal vanishes after class (p = 0.97).
2. `run_pilot3.py` — real LOO: transport n.s. vs relevance; relevance beats NMA.
3. `selfverify3.py` — **from-scratch, no shared functions** (Epanechnikov kernel + jackknife
   CI instead of Gaussian kernel + bootstrap): relevance − NMA **−0.062 [−0.121, −0.002] WIN**;
   transport − relevance **+0.005 [−0.019, +0.030] n.s.** — same sign, same decision.
4. `sim_transport.py` — **methodologically independent** (known-truth calibrated DGP):
   machinery correct, real β in the inert corner.

---

## 7. Honest verdict & next step

**The genuinely novel core — transportability as a multiplicand on the borrowing weight —
does not improve over relevance-only on this real T2DM HbA1c slice, because the population
obesity covariate is not a strong enough effect modifier here (β ≈ 0.006, n.s. after class).**
We report this plainly, as the brief requires. Three things are nonetheless established:

1. **Relevance-only borrowing replicates as the contribution** (relevance beats NMA on real
   held-out effects, −0.062 [−0.119, −0.007]) — pilot-2 holds under a fresh slice + anchor.
2. **The transportability layer is correct, not broken.** With known truth it is inert when
   it should be (β = 0, target = pool), reproduces the real null at the real β, and beats
   relevance-only monotonically once the population modifier is strong (β ≳ 0.02). The
   limitation is the **data**, not the method.
3. **The honest threshold is quantified:** transportability earns its keep only when a
   population covariate modifies the effect at β ≳ ~0.02 %HbA1c per covariate-unit (≈ 3× what
   obesity delivers here).

**Next step (do NOT scale to the registry-wide field as a transportability win yet):** keep
relevance-only as the shipped contribution; re-test transportability on a slice/outcome with
a *documented strong* population effect modifier (e.g. ancestry-driven pharmacogenomic
response, or an absolute-risk outcome where baseline risk transports strongly), using the
β ≳ 0.02 threshold as the pre-registered power gate. The negative controls (target = pool,
β = 0) and conflict-discounted precision fusion (pilot-2) carry over unchanged.

---

## Reproduce
```
cd F:\ubcma\borrowing
python prep_transport.py     # join slice + AACT countries + WB obesity -> trials_transport.json
python probe_transport.py    # IS the transport signal real? -> probe_transport_summary.json
python run_pilot3.py         # REAL LOO 5-way + negative controls -> pilot3_loo_summary.json
python sim_transport.py      # known-truth beta-sweep (method correctness) -> sim_transport_results.json
python selfverify3.py        # independent from-scratch re-derivation (Epanechnikov + jackknife)
python make_figure3.py       # fig_borrowing_pilot3.png
```
Pre-registered carry-overs (not re-tuned): conflict-discounted precision fusion for
own⊕prior; β = 0 and target = pool as standing negative controls; transport-value regime =
sparse + covariate-distant. Population covariate fixed a priori = WB adult obesity
`SH.STA.OB18`; bw_obesity = donor obesity SD. Numbers above are the committed seeded runs.
