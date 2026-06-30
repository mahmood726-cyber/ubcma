# Borrowing-Field Pilot 4 — is there a REAL slice where a *strong* population effect-modifier lets TRANSPORTABILITY beat relevance-only?

> *Branch:* `methods-borrowing` (F:\ubcma) · *Date:* 2026-06-30 · *Owner:* Mahmood
> *Builds on:* `REPORT_BORROWING_PILOT3.md` — pilot-3 gate **NO** on a real T2DM/obesity
> slice (modifier β≈0.006, too weak), but a calibrated sim proved the transport machinery
> is correct and *would* win once a population modifier exceeds **β ≈ 0.02** (standardised
> units). Pilot-4 is the decisive search for that qualifying slice.
> *Question this pilot decides:* does a REAL therapeutic slice exist in the registry where a
> population covariate (WB / IHME-SDI) is a **strong, documented, confounder-robust** effect
> modifier — and if so, does transportability-weighted borrowing beat relevance-only on real
> held-out data? Truth-first: if no qualifying slice exists, that bounds the method.

## TL;DR — verdict: **NO qualifying slice exists in this registry, for a STRUCTURAL reason that itself bounds the method.** Transportability still does not beat relevance-only on the best-available real slice. Relevance-only (pilot-2) stays the shipped contribution.

The search was genuine and multi-domain. The decisive finding is **structural, not a near-miss**:
a transportability test needs three things to coincide in **one** slice — (1) a population gradient
the trials actually **sample**, (2) a clean, exchangeable, **placebo-anchored** treatment effect,
(3) adequate n. **The registry systematically separates them.**

- **Every placebo-anchored continuous-outcome domain is gradient-COMPRESSED by trial-site
  selection.** Across 13 major areas, SDI coefficient-of-variation is ≤ 0.09 for diabetes,
  hypertension, depression, asthma, COPD, pain, heart failure, obesity, schizophrenia, RA, COVID —
  trials cluster in high-income/high-SDI sites. Even in **depression**, where the income/region
  gradient in drug–placebo separation is famous, the covariate barely varies (within-slice
  SDI **CV = 0.04**, log-GDP **CV = 0.04**) and the income/SDI modifier is **null** (perm p ≈ 0.6) —
  *because the registry does not sample the gradient*.
- **The wide gradient lives only in infectious-disease domains** — malaria (**SDI CV = 0.37**,
  range 0.26–0.94), TB (0.21), enteric/diarrhoeal (0.18), HIV (0.17) — where outcomes are **binary**
  and the available effects are predominantly **drug-vs-drug or single-arm** (you cannot
  placebo-control active anti-infective treatment), so there is **no exchangeable placebo anchor**
  to borrow.

On the **best-available real slice** that *does* have a clean placebo-anchored effect (MADRS
antidepressant-vs-placebo, n = 36, candidate modifier = WB under-5 mortality, the only covariate
with a nominally significant adjusted slope), transportability **does not beat relevance-only**:
ΔMAE **+0.066 [−0.158, +0.304]** (n.s.), worse in every regime; independently reproduced from
scratch **+0.059 [−0.141, +0.260]**. A known-truth sim on the *same* trial structure proves the
machinery is correct — inert at β = 0, **transport wins decisively once β ≳ 0.5/unit** — so this is
a **data/estimation limit, not a method failure**. The real modifier point-estimate sits *near* that
threshold (≈ 0.5–0.74 /SD) but is **too fragile** (perm p = 0.09, 1-of-8 tests) and its per-fold
standardisation slope too unstable for transport to net a win.

**Conclusion:** the full transportability-weighted method remains **CONDITIONAL / UNPROVEN on real
registry data**. We do **not** scale it to the field or claim it in the paper as a win. We can now
state *precisely* what would settle it (below). **Relevance-only is the validated, shipped
contribution.**

---

## 1. The search — what was tried, what qualified

All extraction is from AACT `2026-04-12` (DuckDB over the pipe-delimited dumps); covariates are real,
external, per recruiting country, latest year: World Bank adult obesity (`SH.STA.OB18`), log GDP/capita
(`NY.GDP.PCAP.CD`), under-5 mortality (`SH.DYN.MORT`), and IHME GBD **SDI** (2019). Crosswalk aliases
carried from pilot-3 + extended.

| # | candidate slice | design | n (clean) | why pursued / dropped |
|---|---|---|---|---|
| 1 | **Antihypertensive SBP change** vs placebo | continuous MD (mmHg, common scale) | **8** | documented race/region modifier, but only 8 clean active-vs-placebo monotherapy trials — BP trials are active-comparator. **Too thin.** |
| 2 | **Depression (antidepressant vs placebo)** MADRS/HAMD change | continuous MD | **61** (55 w/ cov) | placebo-controlled + famous income/region modifier. **Pursued** — but gradient compressed (below). |
| 3 | **Gradient precondition scan** (13 areas) | — | — | the decisive test: only infectious domains sample a wide gradient (§2). |
| 4 | **HIV** CD4-change | continuous MD | 205 analyses | widest *continuous*-MD gradient (CV 0.20) but effects are **regimen-vs-regimen**, no exchangeable placebo anchor. Dropped. |
| 5 | **Malaria / TB / enteric** (binary) | event counts → efficacy | 188 / 163 / 164 | widest gradients of all (malaria SDI CV 0.37), but outcomes **binary & drug-vs-drug/single-arm**; no clean placebo-anchored exchangeable effect. Dropped. |

**Qualifying-gate result (binding requirement 1 of the brief): no slice passed.** No slice combined
(a) a *strong, robust, confounder-clean* population modifier with (b) a clean exchangeable
placebo-anchored effect and (c) adequate n. We nonetheless ran the full 5-way on the best-available
slice (#2/MADRS) to demonstrate the predicted null concretely (§3–§5).

---

## 2. Why — trial-site selection compresses the population gradient (the structural finding)

`hunt_gradient.py` — for every condition bucket among the 6 233 trials with ≥1 between-group MD
analysis, join recruiting countries → IHME SDI and measure the **spread** of trial-level mean SDI.
Transportability cannot be exercised where the trials do not sample the gradient.

| bucket (continuous MD outcomes) | n w/ SDI | SDI range | **SDI CV** |
|---|---|---|---|
| HIV | 107 | 0.379–0.880 | **0.200** |
| hypertension | 176 | 0.458–0.899 | 0.088 |
| type-2 diabetes | 198 | 0.482–0.889 | 0.075 |
| **depression (MDD)** | 216 | 0.488–0.897 | **0.066** |
| schizophrenia / COVID | 86 / 47 | — | 0.064 |
| RA / obesity / COPD / asthma | 108–226 | — | 0.043–0.057 |
| heart failure | 76 | 0.696–0.899 | 0.039 |

Every placebo-anchored continuous-outcome domain is compressed to **CV ≤ 0.09** (high-SDI cluster).
By contrast, **binary-outcome** infectious-disease trials sample the whole spectrum:

| bucket (binary outcomes) | n w/ SDI | SDI range | **SDI CV** |
|---|---|---|---|
| **malaria** | 188 | **0.260–0.940** | **0.374** |
| TB | 162 | 0.379–0.940 | 0.205 |
| enteric / diarrhoeal | 164 | 0.260–0.884 | 0.183 |
| HIV | 1672 | 0.315–0.909 | 0.169 |

**Reading:** the population gradient that transportability is built to exploit exists in the
registry *only* where the borrowable estimand does not (binary, drug-vs-drug, no placebo anchor),
and is *absent* wherever the estimand is clean (placebo-anchored, continuous). This is a deeper,
more general statement of pilot-3's null: it is not that one modifier was weak — it is that the
registry's well-posed-for-borrowing domains do not vary the population.

The depression slice makes it concrete: 55 trials, but log-GDP **CV 0.04**, SDI **CV 0.04**
(SDI 0.70–0.87, all high); single-country anchors are US ×19, Japan ×10, China ×1. The famous
income/region antidepressant modifier is **null here** (marginal −0.12/SD, p 0.64; +class&scale FE
−0.38/SD, p 0.56) — not because it is unreal in the world, but because the registry does not sample
low-income settings for these drugs.

---

## 3. The candidate modifier on the best-available slice (binding requirement 3, checked first)

`hunt_dep.py` modifier screen (effect = MADRS/HAMD MD vs placebo, w = 1/se², standardised covariate,
permutation p; Simpson guard = class + scale fixed effects):

| covariate | marginal /SD (p) | +scale FE (p) | +class&scale FE (p) |
|---|---|---|---|
| log GDP/capita | −0.14 (0.57) | −0.16 (0.71) | −0.49 (0.45) |
| SDI | −0.12 (0.64) | −0.16 (0.72) | −0.38 (0.56) |
| obesity % | −0.19 (0.43) | −0.19 (0.66) | −0.56 (0.32) |
| **under-5 mortality** | +0.20 (0.39) | +0.36 (0.35) | **+0.92 (0.009)** |

Only **under-5 mortality**, fully adjusted, is nominally significant (+0.92 MADRS-pt/SD, perm
p = 0.009 over all scales). But it is **fragile**: MADRS-only it is +0.74/SD, **p = 0.09**; it is
**1 of 8 tests** (no multiplicity survival); its LOO slope is sign-stable [+0.50,+1.02] but the
"high-mortality" anchors are mixed Eastern-European/Latin-American multi-country trials
(under-5 mort 6–9 /1000 — still low), i.e. a **narrow-band proxy**, not a genuine high-burden
population. It does **not** clear a "strong, robust, confounder-clean" bar. We carry it forward only
as the registry's *best available* candidate.

---

## 4. The 5-way real LOO (the headline test)

`run_pilot4.py` — MADRS slice, n = 36, `pop_ob := under-5 mortality`. Each trial held out in turn
(zero own data → pure transportability prediction of the real held-out `y_t`); prior built from all
others five ways; paired bootstrap; regime split (target far/near donor-pool mortality); single-country
subset. Carry-overs unchanged: conflict-discounted precision fusion; β = 0 and target = pool as
standing negative controls; bw = mortality SD.

| regime | n | MAE nma | MAE relevance | MAE transport | MAE scrambled |
|---|---|---|---|---|---|
| ALL | 36 | 1.547 | **1.554** | 1.620 | 1.520 |
| FAR (mort-distant) | 10 | 1.454 | 1.473 | 1.497 | 1.494 |
| NEAR (mort-central) | 26 | 1.583 | 1.586 | 1.668 | 1.529 |
| single-country | 20 | 1.441 | 1.453 | 1.586 | 1.442 |

Paired-bootstrap contrasts (Δ < 0 = first better):

| contrast (ALL) | ΔMAE [95% CI] | verdict |
|---|---|---|
| **transport − relevance** | **+0.066 [−0.158, +0.304]** | **n.s. — transport does NOT beat relevance** |
| transport − nma | +0.073 [−0.148, +0.310] | n.s. |
| transport − scrambled | +0.101 [−0.023, +0.224] | n.s. |
| relevance − nma | +0.007 [−0.074, +0.089] | n.s. (relevance adds nothing here either) |

Transport is directionally **worse** than relevance in every regime. Unlike pilot-3 (where relevance
beat NMA), here even relevance ≈ NMA — antidepressant drug–placebo effects are similar across class
and baseline, so the relevance kernel has little to grip and the population kernel only adds noise.

---

## 5. Negative controls, coverage, and the known-truth sim (requirements 2 + 4)

**Controls** (`run_pilot4.py`):

| control | result | reading |
|---|---|---|
| target = donor pool (`ob_t := median`) | transport − relevance **+0.088 [+0.009, +0.159]** | transport **worse** (adds noise), never spuriously better — directionally safe; the standardisation injects noise when there is no real modifier |
| β_ob = 0 (no standardisation) | **+0.018 [−0.063, +0.107]** | **nearly inert** — isolates the cost to the *standardisation* step using a noisy estimated slope |

The β = 0 control being near-inert while the full-transport control is +0.088 worse pinpoints the
mechanism: **transport's gain requires estimating the modifier slope per fold; when the true modifier
is weak, that estimate is noise and standardising on it hurts.** Coverage of the real `y_t` (95% PI):
nma 0.86, relevance 0.86, transport 0.83, scrambled 0.89 — apples-to-apples, no transport coverage
benefit.

**Known-truth sim** (`sim_madrs.py`) — keep the real MADRS structure (class, mortality, SEs), regenerate
`y = a_class + β·(mort − ref) + ε` with class effects + τ = 1.36 estimated from the real data, LOO-predict
all 36, sweep β:

| true β (/unit) | MAE nma | MAE rel | MAE transport | transport − relevance |
|---|---|---|---|---|
| 0.00 | 0.758 | 0.715 | 0.761 | +0.045 [+0.038,+0.053] (kernel/estimation cost) |
| 0.05 | 0.761 | 0.720 | 0.761 | +0.041 |
| 0.20 | 0.799 | 0.762 | 0.761 | −0.002 (crossover) |
| 0.50 | 0.959 | 0.927 | **0.761** | **−0.166 TRANSPORT WINS** |
| 1.00 | 1.331 | 1.307 | **0.761** | **−0.546 TRANSPORT WINS** |

Transport MAE is **flat at 0.761** across the sweep (it standardises the population shift away) while
nma/relevance blow up as β grows. So the machinery is correct on *this* slice too: inert at β = 0,
robustly winning once β is strong. The crossover (≈ 0.2–0.5 /unit ≈ 0.3–0.7 /SD) is **right where the
real point-estimate sits** — which is exactly why a *fragile* real estimate cannot deliver: the
estimation noise (the +0.045 cost at β = 0) swamps the marginal signal.

---

## 6. Cross-confirmation (requirement 4) — externals down, ≥3 internal + from-scratch

Externals re-checked this run and **down**, as in pilots 1–3:
- **Codex** (`codex-cli 0.142.3`): `401 refresh_token_invalidated` (token revoked); pc2 SSH refuses
  non-interactive exec.
- **agy**: on PATH but its `--print` interface changed / returns empty.

Per the program's fallback, the headline (**transport does not beat relevance; no qualifying slice;
the gradient is the binding constraint**) is confirmed **≥3 independent internal ways + 1 from-scratch
re-derivation**:
1. `hunt_gradient.py` — structural: only infectious binary domains sample a wide gradient.
2. `hunt_dep.py` — modifier screen: income/SDI null, mortality fragile (p = 0.09 MADRS).
3. `run_pilot4.py` — real 5-way LOO: transport − relevance n.s./positive in every regime.
4. `sim_madrs.py` — **methodologically independent** known-truth DGP: machinery correct, real β in the
   fragile/crossover corner.
5. `selfverify4.py` — **from-scratch, no shared functions** (Epanechnikov kernel + jackknife CI instead
   of Gaussian + bootstrap): transport − relevance **+0.059 [−0.141, +0.260]**, relevance − nma
   **+0.002 [−0.033, +0.036]** — same sign, same decision.

---

## 7. Honest verdict, caveats, and what would settle it

**Verdict (gate): NO.** Transportability-weighted borrowing does **not** beat relevance-only on a real
slice, and pilot-4 explains *why* at the level of registry structure, not just one weak covariate:
no registry slice furnishes a **strong, sampled** population modifier together with a **clean,
exchangeable, placebo-anchored** effect. The transport machinery is provably correct (it wins under
known strong truth and is inert under the two controls), so the limitation is the **data**.

**Honest power / caveats.**
- Best real slice is small (**n = 36** MADRS trials) and its single-country targets are clustered
  (US/Japan), limiting gradient leverage.
- The one nominally-significant modifier (under-5 mortality) is **fragile** (p = 0.09 MADRS, 1-of-8
  tests, narrow-band proxy) and mechanistically weak for depression — we did **not** treat it as a
  genuine strong modifier; we treated it as the registry's *best available* and showed even that does
  not deliver.
- We did not extract binary infectious-disease efficacy effects (malaria/TB/enteric); those slices have
  the gradient but lack a clean placebo-anchored exchangeable estimand in CTGov results, and pooling
  across heterogeneous head-to-head anti-infective contrasts is not well-posed borrowing.

**What real slice would settle it (pre-registered for a future pilot):** a **placebo-controlled,
gradient-spanning vaccine or chemoprevention programme** — rotavirus / oral-cholera / malaria-vaccine
(RTS,S, R21) / seasonal malaria chemoprevention — where (a) efficacy vs placebo is a clean exchangeable
binary effect, (b) the population modifier (under-5 mortality / transmission intensity / SDI) is
**documented and large** (the oral-vaccine "efficacy paradox": 85–98% high-SDI → 40–60% low-SDI), and
(c) the trials genuinely span the income spectrum. Such evidence lives in **IPD or curated global-health
syntheses**, not in CTGov mean-difference analyses. Using that slice, apply the same β-threshold power
gate (sim crossover) before the 5-way.

**Shipped contribution unchanged:** relevance-only (pilot-2) — class + baseline relevance with
conflict-discounted precision fusion — remains the validated borrowing contribution. Transportability
is a **correct, ready layer** held in reserve, to be claimed only on a slice that passes the gradient +
modifier-strength gate. **Do not scale transportability to the registry-wide field or claim it in the
paper as a win.**

---

## Reproduce
```
cd F:\ubcma\borrowing\pilot4
python hunt_scan.py          # outcome-family survey (where are the multi-country MD trials)
python hunt_sbp.py           # SBP slice -> too thin (8 trials)
python hunt_dep.py           # depression slice + modifier screen -> dep_modifier_screen.json
python diag_dep.py           # covariate-spread + under-5-mort robustness diagnostics
python hunt_gradient.py      # PRECONDITION scan: SDI spread by condition (the structural finding)
python prep_madrs.py         # MADRS -> transport schema (pop_ob := under-5 mortality)
python run_pilot4.py         # REAL 5-way LOO + controls + coverage -> pilot4_loo_summary.json
python sim_madrs.py          # known-truth beta sweep (machinery correctness) -> sim_madrs_results.json
python selfverify4.py        # from-scratch re-derivation (Epanechnikov + jackknife)
```
Pre-registered carry-overs (not re-tuned): conflict-discounted precision fusion for own⊕prior; β = 0
and target = pool as standing negative controls; covariate fixed a priori; bw = mortality SD. Numbers
above are the committed seeded runs.
