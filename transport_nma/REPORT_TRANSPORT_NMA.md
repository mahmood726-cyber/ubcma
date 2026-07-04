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

## Head-to-head — external registry-λ vs internal funnel selection models (2026-07-03)
Does the EXTERNAL registry-λ correction beat the INTERNAL published selection models (which see only
the published funnel)? Head-to-head on the senn2013 sim (`h2h_bench.py`; verified by writer re-run —
numbers exact; registry_oracle reproduces tnma's oracle). Every corrector starts from the SAME NMA
league estimate and differs only in how it estimates the per-treatment bias. Two regimes: **A** uniform
multiplicative registry bias (SE-orthogonal → funnel-INVISIBLE); **B** the same magnitude as a
small-study effect (∝ SE → funnel-VISIBLE, the regime purpose-built to favour PET). MCIW0 recovering true
basic contrasts; paired-bootstrap ΔMCIW0 vs unadjusted.

| method | B=0 (A) | B=0.15 (A) | B=0.30 (A) | verdict |
|---|---|---|---|---|
| **registry-λ (oracle κ=B)** | +0.000 tie | **−0.118 WINS** | **−0.306 WINS** | **only reliable winner; inert at B=0** |
| registry-λ (fixed κ=0.5) | +0.416 HARMS | +0.200 HARMS | −0.096 WINS | uncalibrated → over-corrects at low B |
| PET / Egger (per-treatment) | +0.680 HARMS | +0.641 HARMS | +0.577 HARMS | **catastrophic over-correction on noise, every cell** |
| trim-and-fill (Duval–Tweedie) | +0.035 HARMS | +0.021 HARMS | +0.024 HARMS | inert-to-harmful |
| Henmi–Copas (FE proxy) | +0.020 HARMS | +0.002 tie | −0.004 tie | inert |
| Copas–Shi selection MLE | — | — | — | **infeasible** (needs k≳15/unit; network gives ≤6 direct/treatment) |

(PET/TF fire on the 3 treatments with ≥3 direct placebo studies, HC on ≥2; Regime B — funnel-visible —
gives the same qualitative picture: registry-λ WINS at B>0, PET still HARMS every cell.)

**Verdict.** The **external registry-λ correction beats every internal funnel-based published selection
model** (PET, trim-and-fill, Henmi–Copas; Copas-Shi infeasible), in BOTH the funnel-invisible and
funnel-visible regimes, and is exactly inert at B=0. **PET over-corrects catastrophically** because a
per-treatment funnel regression on 3–6 studies has ruinous SE→0-intercept variance — the network is too
sparse per treatment for an internal estimate. The registry λ carries the *direction/ranking* of
selection severity as an external, near-zero-sampling-variance signal the internal methods cannot
recover from a handful of studies. **Honest caveat:** λ supplies the direction, not the magnitude κ — an
ungated fixed κ still harms at B=0 (though it still beats PET everywhere). **Concrete improvement (the
next increment):** estimate a single network-pooled κ̂ by regressing the whole network's residual
small-study effects on (1−λ_t)·SE — λ fixes the per-class direction, the network pools strength for a
stable data-driven magnitude, and it collapses to ≈0 under funnel symmetry (the selection-presence gate).

## FIX3 attempt — data-driven κ̂ to replace the oracle: HONEST NEGATIVE (2026-07-03)
The head-to-head above used an ORACLE magnitude (κ=B). To make the correction deployable we built a
data-driven, GATED estimator (`fix3_pooled_kappa.py`): a network-pooled small-study regression
`y_i = d_{t(i)} + γ·(1−λ_{t(i)})·se_i` over all direct placebo-relative studies (one shared slope γ,
pooling strength across the network instead of PET's noisy per-treatment funnel), applied only when γ
is significant (|t_γ|≥2), correcting each treatment's network estimate by the estimated bias.

**Verdict: HONEST NEGATIVE — the internal data-driven κ̂ does NOT recover the oracle win; it HARMS**
(ΔMCIW0 +0.03 to +0.10 vs unadjusted, both funnel-visible and funnel-invisible regimes, and in both the
replace-intercept and subtract-bias formulations). The γ-gate fires only 6–30% of reps and when it does,
γ̂ is too imprecise on this sparse network (~4–6 direct studies/treatment, ~9 treatments) to correct
usefully. So the registry λ genuinely supplies the *direction/ranking* of selection severity (the oracle
correction wins), but the *magnitude* cannot be recovered from the sparse network's own funnel — the
honest limit. **The real fix is an EXTERNAL magnitude**: estimate the per-class effect-inflation κ
directly from AACT (the registered-vs-published effect-distribution gap per drug class), not from the
in-network funnel. That is the concrete next increment; the internal-funnel route is closed (negative).

## FIX3-EXTERNAL — magnitude from the AACT registered-vs-published gap: MAGNITUDE SOLVED (2026-07-04)
Built the external-magnitude increment (`aact_kappa.py` → `aact_kappa_freeze.py` → `aact_kappa_truthgate.py`,
guarded by `test_aact_kappa.py`, 4/4 green). Turner-2008 logic, done inside the registry: AACT holds
structured RESULTS for many registered T2DM trials; whether a trial's results also reached the **published
literature** is observable via PubMed linkage (`study_references.reference_type ∈ {DERIVED, RESULT}` → a PMID
citing the NCT). Publication selection favours larger effects, so **published** trials should show a larger
HbA1c effect than merely-**results-posted** (registered-only) trials. Endpoint restricted to HbA1c — the
same scale as the senn2013 network we correct. `κ_MD(c) = mean|MD|_published / mean|MD|_registered-only − 1`
per class (mmol/mol→NGSP% via ×0.0915; 464 mean-difference analyses).

**The external data independently validates the registry model's structure — no oracle:**
`corr(κ_MD, 1−λ) = +0.50` — selection-prone (low-λ) classes show *bigger* published-vs-registered effect
gaps, exactly the (1−λ) severity pattern `tnma`/`h2h_bench` assume. Frozen deployable estimates (from the
7 adequately-powered classes, min(n_pub,n_reg)≥8): **κ_pooled = 0.158** (n-weighted absolute inflation),
κ_slope = 0.263 (WLS slope of κ_MD on (1−λ) = an external B estimate). Per-class κ_MD: metformin +0.08,
SGLT2 +0.29, DPP4 +0.21, AGI +0.35, GLP1/TZD/insulin ≈0; small-n classes (SU n_reg=3) unreliable, excluded.

**Truth-gate (senn2013 known-truth sim, frozen external κ, matched-coverage MCIW0, paired bootstrap):**

| true B | method | dMCIW0 (Regime A) | Regime B | verdict |
|---|---|---|---|---|
| 0.15 | oracle (=B, upper bound) | −0.118 | −0.097 | WINS |
| 0.15 | **ext_pooled (κ=0.158, FROZEN)** | **−0.119** | **−0.098** | **WINS — matches oracle** |
| 0.15 | fixed κ=0.5 (naive) | +0.200 | +0.241 | HARMS |
| 0.263 | ext_pooled | −0.212 | −0.184 | WINS |
| 0.30 | ext_pooled | −0.231 | −0.203 | WINS |
| 0.00 | ext_pooled | +0.053 | +0.053 | HARMS (presence-gate limit) |
| 0.00 | fixed κ=0.5 | +0.416 | +0.416 | HARMS |

**EXTERNAL CROSS-VENDOR WITNESS (2026-07-04, Codex Seat A gpt-5.5, `xverify_codex_tnma/`): CONFIRMS.**
Given only a self-contained bundle (per-analysis records + senn2013 + λ + spec) and told to import no ubcma
code, Codex wrote its own aggregation + own graph/WLS RE-NMA + own bootstrap and reproduced: κ_pooled
0.15759 (=0.1576, exact 4dp), corr +0.50142 (=0.501, exact), identical 7 classes + per-class κ_MD; its own
NMA gives senn2013 τ²=0.1094; truth-gate external κ TRACKS oracle at B=0.15 (−0.1020 vs −0.1018, within
0.0002, both win), over-corrects B=0 (+0.055), under-corrects B=0.30. Absolute levels differ slightly
(−0.102 vs our −0.119) only via the independent NMA engine/RNG; conclusion identical. One genuine external
vendor alongside the internal engine + tests. See `xverify_codex_tnma/WITNESS.md`.

**Verdict — the MAGNITUDE question is SOLVED (this is the win FIX3 was missing).** The frozen, oracle-free,
external κ_pooled **matches the oracle at B=0.15** (−0.119 vs −0.118) and WINS across every B≥0.15 in BOTH
funnel-visible and funnel-invisible regimes — decisively better than the arbitrary fixed κ=0.5 (harms at B=0
by +0.42, needs B≥0.30 to help) and than the FIX3-internal κ̂ (harmed everywhere). External AACT data thus
converts the transport-NMA correction from **direction-only → direction + calibrated magnitude**.

**The one residual is NOT a magnitude problem and is provably irreducible here.** A fixed external κ still
over-corrects at true B=0 (+0.053) — the selection-*presence* question, orthogonal to magnitude. Registry λ
is a static class property, so it cannot certify that a *specific* selection-prone-class estimate happens to
be unbiased. We tested the only in-data presence gate (a pooled-network Egger test across all placebo-relative
studies, `ext_pooled_gated`): its **fire-rate is 0.00–0.04 regardless of B** — blind in Regime A (registry
selection is funnel-orthogonal by construction) and underpowered in Regime B (a ~20-study, 4–6-per-treatment
network). Gating therefore removes the B=0 harm but also kills every B>0 win (ties everywhere). So the residual
is the intrinsic presence-detection limit of any registry-scale correction on a sparse network, not a defect
of the external magnitude. **Deployable recommendation:** apply κ_pooled=0.158·(1−λ_t) where selection is a
priori expected (the method's designed regime — a selection-prone class flagged by the registry), where it is
oracle-matching; accept the small bounded over-correction (+0.05 MCIW0) as the honest cost of no presence gate.

## Second-domain replication attempt — antidepressants / HAM-D: HONEST BOUNDARY (2026-07-04)
To test the manuscript's #1 limitation ("single network/endpoint"), we re-ran the exact external-magnitude
machinery (`aact_kappa_depression.py`) in Turner-2008's own domain: major-depression trials, five
antidepressant classes (SSRI/SNRI/TCA/atypical/MAOI), endpoint = HAM-D change, split published (PubMed-linked)
vs registered-only, κ_MD = |MD|_pub/|MD|_reg − 1, plus a per-class λ from AACT depression trials.

**Outcome — does NOT cleanly replicate, and the reason is instructive (not a refutation).** The sign is
positive (corr(κ_MD, 1−λ) = +0.35 over the 3 adequately-powered classes) but the magnitudes are not
credible: κ_MD = +3.5 (SSRI), +9.6 (atypical), with registered-only |MD| means of 0.22–0.35 HAM-D points.
A HAM-D treatment difference of 0.22 points is not a real effect — and indeed **41 % of AACT HAM-D
"mean difference" analyses have |MD| < 0.5** (quantiles 0/0.12/0.70/1.67/2.92 at 10/25/50/75/90 %). Raw
AACT HAM-D mean differences are heterogeneous — they mix 17- vs 21- vs 24-item HAM-D versions, within-arm
change vs between-arm, LS-means vs raw, and multiple timepoints — with no unit normalisation, so the
published-vs-registered *ratio* is dominated by scale/analysis heterogeneity rather than selection.

**Honest boundary (sharpens the manuscript, not a win manufactured).** The external-magnitude construction
requires a **single, standardised endpoint** (HbA1c is one lab value on one scale — hence the clean +0.50
diabetes signal). It does **not** transfer to a raw multi-version rating scale; a proper antidepressant
replication would need standardised effect sizes (Hedges's g from FDA reviews) — exactly what Turner (2008)
used and what AACT does not store. This bounds the raw-MD construction to standardised-measurement endpoints.

## Second-domain replication, DONE PROPERLY — scale-invariant measures REPRODUCE (2026-07-04)
The raw-HAM-D failure above was a **scale artefact**, not a real boundary. Re-running with scale-invariant
effect measures (`aact_kappa_depression_std.py`), so that 17/21/24-item HAM-D and MADRS become comparable,
the registered-versus-published gap **reproduces in the antidepressant domain**:

- **Significance gap** z = |MD|/SE (the standardised signal publication selection acts on): `corr(κ_z, 1−λ)
  = +0.64` over the 3 adequately-powered classes (diabetes reference +0.50). Trial-level paired bootstrap
  grounds it below the fragile 3-class correlation: published trials show **robustly larger** standardised
  effects in the two best-powered classes — **SSRI κ_z +0.69 [+0.23, +1.29]**, **atypical +1.18 [+0.73,
  +1.86]** (both 95% CIs exclude 0) — while SNRI, the *lowest*-severity class (1−λ = 0.565), is null
  (−0.33 [−0.55, +0.26]), consistent with the severity-tracking model.
- **Effect-magnitude gap** |ln OR| on response/remission: **SSRI +0.47 [+0.09, +1.14]** robustly positive;
  class-level correlation underpowered (only 2 classes clear n ≥ 8).

**Verdict — genuine supportive replication, honestly bounded.** The published-vs-registered effect inflation
is not diabetes-specific: on a scale-invariant measure it reproduces the direction and rough magnitude in a
second, independent therapeutic domain (Turner's own), robustly at the trial level where powered. **Caveats
(no over-claim):** only 2–3 antidepressant classes carry adequate registered-only support, so the class-level
correlation is *suggestive*, not inferential; the robust evidence is the per-class trial-level gaps (SSRI,
atypical). Diabetes (7 classes, +0.50) remains the primary validation; this is a corroborating second domain.
Artifacts `aact_kappa_depression_std.json`.

## Third domain — lipid-lowering / LDL-C: inflation REPRODUCES, severity-corr untestable (2026-07-04)
`aact_kappa_lipid.py` applies the same machinery to lipid-lowering therapy (LDL-C change; classes statin
/ ezetimibe / PCSK9 / fibrate / bile-acid / niacin), scale-invariant z-gap primary + a unit-clean
percent-change |MD| secondary. Two honest findings:

- **The published-vs-registered inflation reproduces robustly at the trial level.** In the two
  adequately-powered classes, published trials report much larger LDL effects than registered-only —
  z-gap **statin +1.23 [+0.81, +1.75]**, **ezetimibe +1.33 [+0.88, +1.89]**; percent-change |MD|
  **statin +0.50 [+0.23, +0.85]**, **ezetimibe +0.45 [+0.20, +0.75]** — all four bootstrap CIs exclude 0.
  A clean third-domain confirmation of the core "published effects are inflated" signal.
- **The severity-tracking correlation corr(κ, 1−λ) is not testable here.** Only 2 classes clear the
  min(n_pub, n_reg) ≥ 8 bar: lipid trials are largely *publication-saturated*, so the registered-only arm
  is thin (PCSK9 268 published vs 6 registered-only; fibrate / bile-acid / niacin have **zero**
  registered-only LDL analyses). Directionally the three classes with any data rank as the model predicts
  (statin 1−λ = 0.73 → high κ, ezetimibe 0.62 → high κ, PCSK9 0.38 → κ ≈ 0.24 low), but PCSK9's n_reg = 6
  is too thin to include, so no formal correlation is claimed.

**Verdict.** The "published > registered" half of the registry model now reproduces across **three**
domains (diabetes, antidepressants, lipids). The "gap grows with selection severity" correlation is
established in diabetes (7 classes, +0.50), suggestive in antidepressants (3 classes, +0.64), and
**not testable in lipids** for lack of registered-only spread across classes — an honest data limitation
(publication-saturated domains cannot supply the contrast), not a negative result. Artifacts
`aact_kappa_lipid.json`.
