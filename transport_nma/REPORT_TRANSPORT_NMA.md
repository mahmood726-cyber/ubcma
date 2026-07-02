# Transportable NMA with registry-based publication-bias — bounded demonstration

**Branch** `methods-borrowing` · dir `transport_nma/` · 2026-07-02 · truth-first, honest boundary.
A distinct method type in the REGISTRY-BASED-META family, on the validated netmeta-parity engine
`nma/nma_core.py`. First bounded increment: **registry-λ publication-bias adjustment in an NMA**;
the transportability-to-target-population layer is scoped below.

## (A) Real diabetes NMA + registry pub-bias overlay
`dat.senn2013` (metadat): 26 diabetes RCTs, HbA1c change, a connected network (10 treatments). Arms →
pairwise mean-difference contrasts → `fit_nma` (random-effects, τ=0.33, I²=1%). The league reproduces
the known result — rosiglitazone (−1.23), pioglitazone (−1.13), metformin (−1.13) most effective;
sulfonylurea (−0.42) least. Overlaid with the **real AACT registry integrity ratio** λ per class
(`borrowing/class_lambda.json`; results-posted ÷ registered on the 2026-04-12 snapshot): AGI 0.20,
GLP1 0.36, metformin 0.40, TZD 0.42, SU 0.47, DPP4 0.48. Low λ ⇒ strong reporting selection ⇒ that
class's published effect is the tip of a selection-biased iceberg; (1−λ) is the per-treatment
selection-severity proxy.

## (B) Truth-gate — does the registry λ carry usable publication-bias information?
Known-truth sim on the senn2013 network geometry: each active treatment's true placebo-relative effect
is inflated by selection, `d_obs = d_true·(1 + B·(1−λ_t))` (registry-missingness drives the bias);
sweep the true selection strength B. Correction shrinks each basic contrast toward null by
`κ·(1−λ_t)`. Scored at matched coverage (MCIW0 = 2·q95|error| recovering the true basic contrasts;
paired-bootstrap 95% CI). We separate **pattern** (which classes are biased, from λ) from **strength**
(κ) by running κ = oracle(=B) and a fixed κ=0.5:

| true B | unadj MCIW0 | reg-adj κ=B (oracle) | reg-adj κ=0.5 (fixed) |
|---|---|---|---|
| 0.00 | 0.431 | 0.431 — **Δ 0.000 (exactly inert)** | 0.847 — **HARMS +0.416** |
| 0.15 | 0.518 | 0.400 — **WINS −0.118 [−0.132, −0.102]** | 0.718 — HARMS +0.200 |
| 0.30 | 0.686 | 0.380 — **WINS −0.306 [−0.324, −0.280]** | 0.590 — WINS −0.096 |

**Honest verdict.** The registry λ supplies the **correct relative selection-severity pattern**: a
correction whose *strength* matches the true selection (κ≈B) recovers the true relative effects
markedly better than the unadjusted NMA under real selection (WINS at B>0) and is **exactly inert
when there is no selection (B=0)** — the AdaptShrink inertia boundary, preserved. But a **fixed,
uncalibrated κ over-corrects and harms** when the true selection is weak (κ=0.5 harms at B=0, 0.15).
So registry pub-bias adjustment in NMA is beneficial **only with a data-driven strength and a
selection-presence gate** — the registry λ gives the *direction/ranking* of selection severity, not
its magnitude. (Building the truth-gate surfaced and fixed a sign error in the bias-injection sim —
the gate working as intended.)

**Next increment:** replace the oracle κ with a **data-driven** strength estimated from network
funnel asymmetry (the NMA analogue of the univariate PET/AdaptShrink t-statistic), gated on evidence
of asymmetry — turning this from an oracle demonstration into a deployable estimator.

## Transportability layer — BUILT + truth-gated (`transport_truthgate.py`; verified by writer re-run)
Standardising the network to a target population uses a **real** country covariate: World Bank WDI
**diabetes prevalence** (`SH.STA.DIAB.ZS`, 2024; `F:\WorldBankData\...\SH_STA_DIAB_ZS.csv`), aligned
via the WHO `crosswalk.py` (iso2→iso3→ihme/wb), spanning 6.5 % (France) → 31.4 % (Pakistan). Each
treatment's placebo-relative effect is modelled `d_t(X) = d_t0 + β·(X − X_ref)`; to a target with
covariate X*, `d_t^target = d̂_t + β̂·(X* − X_ref)` (β̂ data-driven per rep by precision-weighted
meta-regression; an oracle-β variant separates machinery from estimation noise). Because `dat.senn2013`
has no real per-trial covariate (the pilot-4 wall), studies are assigned real countries across the
gradient and the layer is validated on a **calibrated known-truth sim** — no real-data transport claim.

Truth-gate (matched-coverage MCIW0, paired-bootstrap 95 % CI; writer re-run reproduces exactly):

| condition | β | transport − unstandardised MCIW0 | verdict |
|---|---|---|---|
| **target = pool (X\*=X_ref)** | any | **+0.000 [0,0]** | **exactly inert** (the required boundary) |
| target = far (Pakistan 31.4%) | 0.000 | +0.256 [+0.238,+0.275] (oracle +0.000 inert) | data-driven β̂ **HARMS** (noise × 20.5-pt lever) |
| target = far | 0.008 | ≈ 0 | **threshold** |
| target = far | 0.02 / 0.05 / 0.20 | −0.51 / −1.78 / −7.83 (oracle-confirmed) | **WINS** (unstd error blows up) |

**Honest verdict.** The transport-standardisation machinery is correct: **exactly inert at target=pool
for all β** and inert at β=0 under the oracle (no spurious win), and it recovers the target-population
truth far better than the unstandardised NMA once a real population modifier exists and the target is
far (β ≥ ~0.01). The honest failure mode: with a *data-driven* β̂ and **no** true modifier (β=0) at a
far target, transport HARMS — the estimation noise is amplified by the large covariate lever — so, like
the registry-pub-bias correction and pilot-3, the transport layer must be **GATED on evidence of a real
modifier** (β̂ significantly ≠ 0). This is the same boundary-map discipline throughout the program.

## Files
`tnma.py` (real NMA + registry-λ correction + truth-gate), `tnma_result.{txt,json}`. Reuses
`nma/nma_core.py` (validated netmeta-parity) and `borrowing/class_lambda.json` (real AACT λ).
