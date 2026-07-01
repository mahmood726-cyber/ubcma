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

## What is settled vs still open

**Settled (robust, homogeneous, k=42 / 6 slices):**
1. **Transportability-standardisation beats textbook NMA** — pooled −0.14 logRR MAE, CI<0 at every
   bandwidth and kernel, I²≈0 % across BCG and rotavirus.
2. **Relevance down-weighting beats the no-relevance null** — pooled −0.10 (transport LOO) and
   −10.4 % (multi-specialty, 6 slices), both CI<0.
3. The **standardisation control** behaves correctly in both transport slices (β=0 inert;
   target=pool hurts +0.17–0.19) — the gain is real-target g-computation, not generic shrinkage.

**Still open:**
- **Transport's incremental gain OVER relevance-only.** Pooled −0.07, I²=0 %, significant at 2/3
  pre-specified bandwidths, but the **pre-registered central-bw CI just crosses 0** (+0.004) at k=42.
  On the threshold, not settled. **Rate-limiter: a *third* independent placebo-controlled
  gradient-spanning strong-modifier slice.** With BCG+rota homogeneous at I²=0 %, one more comparable
  slice would very likely push the primary pooled CI below 0.
- **The scrambled-null relevance control** is more fragile than the no-relevance control (6-slice pool
  crosses 0). Worth flagging in any relevance claim.

**Candidate 3rd transport slices** (for the next cycle, same gate): oral cholera vaccine efficacy by
setting; pneumococcal/Hib conjugate vaccine by region; vitamin-A / zinc mortality trials by baseline
under-5 mortality; IPTi/IPTp antimalarial efficacy by transmission intensity. Each needs a deposited or
single-table per-trial 2×2 + a continuous population covariate (the rotavirus route — a verified
deposited dataset — is the model to prefer over multi-paper transcription).

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
