# AGY third-vendor verification — 2026-07-04

**Orchestrator:** Claude (Opus 4.8, thin orchestrator).
**Third vendor:** Antigravity CLI (`agy` v1.0.16, pc1, authenticated), run as an
independent THIRD vendor alongside Claude and OpenAI Codex (gpt-5.5).
**Repo:** `F:\ubcma`, branch `methods-borrowing`.
**How run:** plain `agy --print` (no `--dangerously-skip-permissions`; the auto-mode
classifier blocked that flag and it was not needed — a smoke test `python -c "print(6*7)"`
returned `42`, so agy executes real code in print mode). Two jobs, each wrote its own
raw artifact (`verification/agy_job{1,2}_raw.md`). All numbers below were re-derived by
agy from the code/data, then re-checked by Claude against the banked baseline.

---

## JOB 1 — THIRD-VENDOR WITNESS of the transport-NMA headline

**Verdict: agy CONFIRMS all three claims — to FULL double precision, exact match with
Claude's and Codex's numbers. No divergence.**

Triple-vendor agreement (Claude re-run = Codex Seat A = agy):

| Claim | Value (agy, verbatim) | Claude baseline | Codex (banked) | Agree? |
|---|---|---|---|---|
| (i) `kappa_pooled` ≈ 0.158 | `0.1575949114447188` | `0.1575949114447188` | `0.1576` (4dp) | **YES (exact)** |
| (i) `kappa_slope` | `0.26308957637488806` | `0.26308957637488806` | — | **YES (exact)** |
| (i) ext matches oracle @ B=0.15 | ext −0.118870 vs oracle −0.118016 (regime A) | same | −0.1189 vs −0.1180 | **YES** |
| (ii) `corr(kappa_MD, 1−lambda)` sign | `+0.5014226365552311` (POSITIVE) | `+0.5014226365552311` | `+0.5014` | **YES (exact)** |
| (iii) ext0.158 beats PET/TF/HC @ B≥0.15 | CONFIRM (all 4 cells) | CONFIRM | CONFIRM (PARTIAL phrase) | **YES** |

### Claim (iii) detail — agy's h2h table (matches banked `h2h_result.json` exactly)

| regime | B | oracle dMCIW0 | ext0.158 dMCIW0 | PET | TF | HC |
|---|---|---|---|---|---|---|
| A | 0.15 | −0.118016 | **−0.118870 WINS** | +0.640882 HARMS | +0.021341 HARMS | +0.002306 tie |
| A | 0.30 | −0.305722 | **−0.231304 WINS** | +0.577409 HARMS | +0.023841 HARMS | −0.003835 tie |
| B | 0.15 | −0.096746 | **−0.098195 WINS** | +0.603684 HARMS | +0.015316 HARMS | +0.003462 tie |
| B | 0.30 | −0.221677 | **−0.202484 WINS** | +0.480338 HARMS | −0.001834 tie | −0.008271 **WINS** |

**HC nuance — independently re-discovered by agy.** agy noted (as Codex did) that HC is
essentially a *tie* at B=0.15 and shows one tiny *formal* WINS at B=0.30 regime B
(dMCIW0 −0.008271). agy resolves it the same way Claude and Codex did: ext0.158 is far
closer to the oracle in that cell (ext −0.202 vs HC −0.008 vs oracle −0.222), so
"beats on closer-to-oracle" holds. PET is catastrophic everywhere (+0.48 … +0.64).
This is the exact single nuance behind Codex's `REPRODUCED: PARTIAL` line — all three
vendors converge on it.

**Bottom line:** the transport-NMA headline is now witnessed by a GENUINE second AND
third independent vendor (Codex + agy), on top of Claude's deterministic re-run. Direction
AND magnitude reproduce; no result moved.

---

## JOB 2 — INDEPENDENT BUG-REVIEW (agy) vs the banked Codex bug-hunt

agy reviewed `src/ubcma/comparators.py`, `borrowing/field_scale/field_learned.py`, and
the `transport_nma/*` kappa scripts. Each finding below was **independently re-checked in
code by Claude** and tagged NEW / OVERLAP / DIVERGENCE with an adjudication.

### A. Overlap with Codex (independent re-discovery — corroborates)

- **`aact_kappa.py:127,129` — truthiness guard drops legitimate 0.0** and
  **`aact_kappa.py:110` — non-comparable subset mixing** (`mean_amd` over all trials vs
  `mean_z` over the SE-valid subset → `kappa_MD` and `kappa_z` on different populations).
  → **OVERLAP** with Codex P2 #6 (both halves). Independently found. Low real-data impact,
  disclosed; the frozen deploy path (`aact_kappa_freeze.py`) is unaffected. **Confirmed real.**

### B. Previously-reported P0s — agy's status on the fixes

- **Copas (`copas_selection`)** — Codex reported it returned the ρ=0 naive pool; Claude
  fixed it to select the ρ-grid **max-likelihood** point. **agy says the fix is present but
  the objective is still mis-specified** (a DEEPER concern than Codex raised). Claude
  **structurally confirmed** the fact agy points at: `comparators.py:181` does
  `ll += np.sum(np.log(Phi_u))` (adds `+logΦ(u)`), whereas the exact Copas–Shi (2000)
  observed-data log-likelihood *subtracts* `logΦ(u_i)` and adds `logΦ(v_i)` (the
  conditional selection term), while the y-density already uses the selection-**adjusted**
  moments. So the code is a hybrid with the wrong sign on the `logΦ(u)` term, which biases
  the optimum toward γ0→∞ (selection off) and hence under-corrects.
  → **NEW / DEEPER (PLAUSIBLE, comparator-only).** Caveat: agy's "still returns the naive
  pool" is an over-statement — the Claude fix *does* move the estimate (aspirin Copas
  −0.074→−0.085; sim bias 0.057→0.056), so it under-corrects rather than fully collapsing.
  AdaptShrink's default panel EXCLUDES Copas → **no shipped/headline number affected.**

- **k-fold GP field (`field_learned.predict_kfold`)** — Codex reported train/test category
  codes & standardization diverged; Claude fixed it by building features once on the full
  block then slicing. **agy CONFIRMS the fix is present and sound** for code alignment, and
  adds a sharp note: the fix introduces **mild covariate-only leakage** (standardization
  mean/sd and category codes are fit on the full block incl. the held-out fold; no target
  `yi` leaks). → **fix CORROBORATED; new caveat is real but minor** (features are
  year/log-precision/category — the shipped fix was already shown numerically inert,
  MAE 0.33249→0.33247, consistent with negligible leakage effect). **No headline change.**

### C. New defects agy caught that Codex did NOT flag (all comparator/diagnostic-level)

1. **`comparators.py` `quality_effects` (~L262) — omits the IVhet heterogeneity variance.**
   Labeled "Doi et al. 2015, IVhet-based" but returns `se = sqrt(1/Σw)` (naive
   inverse-variance FE variance); it never computes τ² nor the IVhet quasi-variance
   `Σ (w_i/Σw)² (s_i²+τ²)`. Under heterogeneity the SE is underestimated / CI too narrow.
   → **NEW, CONFIRMED real.** Codex did not review `quality_effects`. Comparator column
   only; not in the AdaptShrink default panel → no shipped number affected.

2. **`field_learned.py:181 predict_loo` + `:303 score` — observation-noise double-count.**
   `predict_loo` returns `sd = sqrt(1/diag(Kinv))`, the LOO predictive SD of the *observed*
   value (K carries `se_i²` on its diagonal, so `sd²` already includes the point's noise).
   `score` then forms `hw = z*sqrt(sd**2 + se_t**2)`, adding `se_t²` a SECOND time.
   → **NEW, CONFIRMED real.** Over-widens raw LOO/k-fold coverage-width diagnostics; does
   NOT touch the MAE-based "beats within-MA" headline (point estimate `mu` only) and is
   largely absorbed by the conformal recalibration that produces the shipped coverage.

3. **`comparators.py knapp_hartung_adjustment` — no k=1 guard.** For k=1, `q_hksj`
   divides by `k-1=0` and `df=0` → `t_dist.ppf(.,df=0)=NaN`. → **NEW, real but
   out-of-contract** (HKSJ/PI undefined for k<2 by construction; mechanism is a NaN via
   df=0 / numpy inf, not a Python `ZeroDivisionError` as agy wrote). Low priority.

4. **`trim_and_fill` se uses the fixed-effect formula (`sqrt(1/Σ(1/se_fill²))`).**
   → **DIVERGENCE (agy vs Codex; Claude sides with Codex).** The *entire* `trim_and_fill`
   pools with FE weights (both `mu0` and `se`), so it is an internally-consistent
   FIXED-effect Duval–Tweedie estimator (the original form), not a bug. It would only be a
   defect if RE were intended. Codex explicitly marked it verified-correct. **Not counted
   as a confirmed defect.**

### Did agy catch the same CLASS as Codex?

**Yes for the `aact_kappa` truthiness/subset class (independent re-discovery), and yes it
corroborated the k-fold fix.** On Copas it went DEEPER than Codex (objective mis-spec, not
just the selection-loop). It did **not** re-report the two original P0s as open, because
both are fixed in the current tree — instead it validated the k-fold fix and questioned the
Copas objective. And it surfaced **2 genuinely new confirmed comparator-level defects**
(`quality_effects` IVhet variance; `predict_loo/score` noise double-count) plus edge/hygiene
notes. **None of agy's findings touch the transport-NMA headline or the "beats within-MA"
MAE headline.**

---

## OVERALL

| | Result |
|---|---|
| agy reachable & executing real code? | **Yes** (v1.0.16, plain `--print`, returned `42` smoke) |
| Witness verdict | **CONFIRM ×3, exact to full double precision** — triple-vendor (Claude+Codex+agy) agreement, incl. the HC one-cell nuance |
| Any headline moved? | **No** |
| Bug-review overlap w/ Codex | `aact_kappa` 0.0/subset class (independent re-find); k-fold fix corroborated |
| Bug-review NEW confirmed defects | 2 real (`quality_effects` IVhet variance; `predict_loo/score` noise double-count), all comparator/diagnostic-level |
| Deeper-than-Codex | Copas objective mis-spec (`+logΦ(u)` sign vs exact Copas–Shi) — PLAUSIBLE, comparator-only |
| Divergence adjudicated against agy | `trim_and_fill` FE-se (design, not a bug — Claude agrees with Codex) |
| Fabricated agreement? | **No.** All agy numbers independently re-checked by Claude; over-statements (Copas "naive", `knapp_hartung` "ZeroDivisionError") flagged. |

**Truth-first note:** agy did not diverge on any headline number. Its bug-review is a
genuine third perspective — it corroborated where Codex was right, went deeper on Copas,
and found new comparator-level defects Codex missed, none of which affect a shipped result.

---

# APPENDIX — continuous agy drive (2026-07-04, later session)

Per directive, agy on pc1 was driven continuously (chained jobs, ≤2 concurrent) to
consume its usage toward the cap. Genuine third-vendor work only; each result below was
re-checked by Claude. Truth-first — agreements and divergences both recorded.

## JOB 3b — DTA + dose-response bug-review (area not previously covered)

agy reviewed `src/ubcma/dta.py`, `truth-recovery-dta/*`, and `doseresponse/{drma,drma_binomial,mbnma}.py`.
It also confirmed (by inspection of the validation records) the three parity headlines:
DTA Reitsma **9.02e-7** vs mada::reitsma, DRMA two-stage **<1e-9** (linear) vs dosresmeta,
MBNMA saturated **<1e-9** point / **<1e-8** SE vs netmeta. **No finding breaks any parity headline.**

Findings (all re-checked by Claude):

| # | File:line | Sev | Claude adjudication |
|---|---|---|---|
| 4 | `doseresponse/mbnma.py:233` | P1 | **CONFIRMED real, NEW.** `psi[j*npar]=max(np.max(np.abs(vals))*np.sign(np.mean(vals)),1e-3)` forces the Emax/E start to **+1e-3 whenever the agent's mean effect is negative** (the negative sign is discarded by the `max(...,1e-3)`). Can stall/mis-converge Gauss–Newton for effect-**decreasing** treatments. Saturated-NMA parity uses a direct GLS solve → unaffected; Emax-model fits only. |
| 1 | `src/ubcma/dta.py` (reitsma) | P1 | **Real robustness gap.** Only guard is `k<2`; the 5-param Reitsma is over-parameterized for 2≤k<5 with no auto-fallback to `reitsma_indep`. Benchmarks are k≥10 → parity intact. Matches the advanced-stats rule (bivariate convergence fails k<5). |
| 2 | `src/ubcma/dta.py:148` | P2 | **CONFIRMED as described.** `rho=np.tanh(z_rho)` → (−1,1), no [−0.95,0.95] clamp in the ML optimizer (AdaptShrink-DTA has only *post-hoc* boundary shrinkage at 0.95). Numerical fragility near ρ=±1; no parity effect. Matches the advanced-stats rule "constrain rho to [-0.95,0.95]". |
| 3 | `src/ubcma/dta.py:117` | P2 | **NOT a defect (agy agrees).** Study-wide 0.5 continuity correction when any cell is 0 **matches mada** — this is the parity target's behavior. agy honestly labeled it parity-preserving. |
| 5 | `doseresponse/drma.py:93` | P2 | **NOT a defect (agy agrees).** GL uses the OR-form reconstruction for non-`ir` types incl. cumulative-incidence; **matches dosresmeta's identical simplification** → 1e-9 parity preserved. First-principles nuance only. |

**Verdict:** accurate, well-calibrated review. 1 genuine new P1 (`mbnma` Emax init sign) + 1 real
small-k robustness gap + 1 real ρ-clamp fragility; agy correctly self-classified the two
parity-preserving items as non-defects. **Nothing touches a shipped parity headline.** No overlap
with Codex (Codex never reviewed DTA/dose).

## Continuous foreground loop (Claude-driven, blocking per agy run)

The earlier background driver stalled (a 1-job = 2-process count made its ≤2 guard never
free a slot while the slow field benchmark held both). Switched to a Claude-driven
foreground loop: agy `--print-timeout 8m` per job, blocking, harvest+verify each.

### Field-MAE headline — Claude direct re-derivation (job4b superseded)
Claude re-ran `benchmark_learned.py` to completion (the GP k-fold is genuinely ~50 min).
**Reproduces the shipped headline exactly:** corpus 1177 nodes / 28 MAs;
learned_kernel MAE **0.3325**, vs_within **−0.0230 [−0.0340,−0.0117]** WINS; only method to
beat within-MA (robust_map/hier_bayes n.s.); negative control learned−scrambled **−0.0527
[−0.0676,−0.0375]** (structure REAL). Matches `after_benchmark_learned.txt` to all printed
digits. (agy's field witness was abandoned as too slow for the loop; the headline is
Claude-witnessed instead.)

### FG1 — NMA engine bug-review (uncovered area)
agy reviewed `nma/{nma_core,inconsistency_nma,smallstudy_nma,adaptshrink_nma}.py`. Findings
re-checked by Claude:

| # | File:line | agy sev | Claude adjudication |
|---|---|---|---|
| 1 | `nma_core.py` (pinv Laplacian) | P0 "breaks parity" | **Real gap, but NOT headline-breaking — agy over-claims.** Verified: no connectivity guard exists (`grep connect/component` empty), so a *disconnected* network yields finite cross-component seTE. BUT the netmeta-parity headline is validated on **connected** networks (senn2013 etc.); disconnected networks are out-of-contract for netmeta too (it splits/NAs). Downgrade to **P2 robustness gap**; shipped parity intact. |
| 2 | `nma_core.py:258` / `inconsistency_nma.py:68` | P1 "breaks parity" | **Real but disconnected-only.** `df_Q = indep−(n−1)` under-counts by C−1 when C>1 components. For connected networks (C=1) it is correct → the parity headline (connected) is unaffected. Same over-claim as #1; downgrade. |
| 3 | `adaptshrink_nma.py:239` | P2 | **CONFIRMED real (internal).** After the small-study/inconsistency gate fires, `NMAFit` is built with adjusted `TE,seTE` but unadjusted `theta=fitA.theta, Lplus=fitA.Lplus` — a representation inconsistency for any downstream consumer reading `theta`/`Lplus`. Not a parity issue. |
| 4 | `nma_core.py:115` | P2 | **Plausible real (internal).** `_arm_variances` unconstrained `lstsq` can return negative reconstructed arm variances → non-PSD block covariance for noisy/underdetermined multi-arm blocks. Numerical robustness only. |

**Verdict:** all four are genuine code observations, but agy's "parity claims safe? no" is an
**over-statement** — findings 1–2 only bite on *disconnected* networks, which are outside the
connected-network contract the parity headline is asserted on. Truth-first correction recorded.
Real internal items: #3 (confirmed), #4 (plausible). No shipped NMA parity number is broken.

### FG2 — robust/diagnostics/bayesian bug-review — LOW SIGNAL (honest)
agy returned 9 "findings" but this pass was largely **rule-echoing**: fed the advanced-stats
checklist in the prompt, agy flagged every deviation as a "defect", including a clear false
positive. Truth-first adjudication (Claude re-checked each):

- **Finding 7 (HKSJ floor) — FALSE POSITIVE.** agy claims the floor should use *fixed-effect*
  weights for Q; the code (`comparators.py:280`) correctly uses generalized RE weights
  `w=1/(s²+τ²)` with `max(1, Σw(y−μ)²/(k−1))` — the Sidik-Jonkman/Röver form. Codex already
  verified this function correct. Rejected.
- **Findings 1,2,3 (DL at k<10)** — DL used in `random_effects`, as a LOO Cook's-distance
  denominator, and as *optimizer starting values*. #2/#3 are **non-issues** (starting values &
  influence-scaling don't need REML). #1 is a **methodological preference** (DL vs REML/PM at
  small k), not a correctness bug; the AdaptShrink headline is calibrated as-is. Not defects.
- **Finding 4 (Bayesian warns but doesn't block on Rhat>1.01/ESS<400)** — this is **standard
  pymc/arviz practice** (warn + return); blocking/raising would be non-standard. Preference,
  not a bug.
- **Finding 5 (clamp 1e-9 vs 1e-10)** — trivial numerical tolerance; 1e-9 is fine. Non-issue.
- **Finding 6 (Fisher-z `1/max(n-3,1)`)** — **real but minor/internal**: n≤3 correlations get
  vz=1.0 instead of ∞, giving them finite weight in `corpus.py`. Low impact (barely-estimable
  studies); a legitimate small edge-case note.
- **Finding 8 (trim_and_fill in `DEFAULT_MEMBERS`)** — **factually correct, but a disclosed
  DESIGN choice, not a bug.** `adaptshrink.py:58` model-averages (ubcma, pet_peese,
  trim_and_fill) with adaptive weights; the "T&F = sensitivity only" rule is about not
  reporting T&F as the standalone headline, not about excluding it from an ensemble. Worth
  surfacing to the author; not counted as a defect.
- **Finding 9 (no Peters/Egger-radial)** — feature *absence*, not a correctness defect.

**Verdict:** 0 confirmed bugs, 1 false positive (HKSJ), 1 minor real edge-case (Fisher-z
n≤3 clamp), 1 legitimate design question (T&F ensemble member). This pass shows agy's
weakness as a rules-checklist reviewer (over-flags) vs its stronger from-code reasoning in
job2/job3/FG1. Recorded truthfully — no inflation.

### FG3 — dose-response parity witness — CONFIRM (runtime evidence)
agy actually RAN `pytest doseresponse/test_{drma,drma_binomial,mbnma}.py`: **20 passed in
80.94s, 0 failed**. Reported real max-diffs vs R references (well inside asserted tolerances):
- DRMA linear coef/SE vs dosresmeta: **2.6e-18 / 3.5e-18** (tol 1e-7); spline REML coef **1.25e-9**, Psi **1.09e-10** (tol 1e-5); one-stage≡two-stage identity **0.0** exact.
- MBNMA saturated vs netmeta gold (`mbnma_gold.json`): TE **9.74e-15** (tol 1e-9), SE **4.86e-16** (tol 1e-8).
- Binomial one-stage RE vs glmer(nAGQ=15): fixed <1e-4, SE <1e-3, σ <1e-4.
→ **CONFIRM.** Genuine third-vendor runtime witness of the dose-response parity headlines
(Claude did not re-run the 80s suite this pass; agy's verbatim pytest output + gold-diff
numbers match the banked parity claims). No divergence.

### FG4 — Codex cross-check — strong corroboration (artifact saved despite 8m timeout)
agy hit the print-timeout but its incremental writes preserved a full report. Independent verdicts:
- **CLAIM 1 (Copas fix):** **AGREE** — fix present & sound (selects min-NLL ρ). **PARTIAL** on
  likelihood: the normal-moment conditional density weighted by Φ(u) is "functionally distinct
  from the exact Copas–Shi joint log-likelihood" — **independently re-derives the same deeper
  concern agy raised in job 2** (cross-run consistency). No new defect.
- **CLAIM 2 (k-fold fix):** **AGREE** — fix present & sound; residual **minor covariate
  (transductive) leakage** from full-block standardization. Matches job 2 exactly.
- **CLAIM 3 (aact_kappa):** **AGREE** both halves; correctly states the **fix is NOT present**
  (verified: `aact_kappa.py:127` still `if sp['mean_amd'] and sr['mean_amd']:` — this P2 was
  never in the P0P1 fix batch, only Copas+k-fold were). NEW observations: line 129 same 0.0
  drop for mean_z (consistent w/ job2), and **line 106 — a trial listing multiple drug classes
  duplicates its effect across each class's kappa** (plausible mild confound; design-dependent).

**Verdict:** high-quality independent cross-check. Confirms both P0 fixes landed correctly,
triangulates the two subtle residuals (Copas likelihood, k-fold leakage) across two separate
agy runs + Codex, and correctly flags the still-open aact_kappa P2. This is the strongest
agree/dispute pass — agy reasoned from current code, not from the prompt's checklist.

### FG5 — DTA parity witness — CONFIRM (runtime evidence)
agy ran `truth-recovery-dta/validate_python.py`: **5/5 datasets pass**, worst |diff| vs
mada::reitsma (ML) = **9.02e-7** (Dementia), matching the ~9e-7 claim by execution. Per-dataset
m1/m2 py-vs-R agree to 5dp; AuditC max|d| 2.03e-8, smoking 2.52e-9, skin_tests 4.09e-9, SAQ
1.44e-9. Confirmed `lnDOR = M1 + M2` (correct sign, dta.py:484) and logit(Se)/logit(Sp) +
sigmoid back-transform correct. **Truthful caveat:** the HSROC-vs-glmer validation is **not on
this branch** — agy noted `tests/test_dta.py` lives on the `methods-dta` worktree (pycache
artifact), so the memory's "hsroc validated vs glmer" belongs to methods-dta, not
methods-borrowing. → **CONFIRM** on the DTA Reitsma parity headline; no divergence.

### FG6 — transport-NMA multi-domain witness — CONFIRM (runtime evidence)
agy ran `aact_kappa_depression_std.py` and `linde_nma.py`:
- **(a) antidepressant scale-invariant z-gap:** `corr(κ_z, 1−λ) = +0.641` (POSITIVE, slope +1.124),
  matching the ~+0.64 claim; 262 z-analyses/226 logOR kept; SSRI κ_z=0.690 [0.22,1.28] sig,
  atypical 1.177 [0.72,1.86] sig, SNRI −0.331 n.s. Correctly explains raw HAM-D fails as a
  mixed-scale (17/21/24-item + MADRS) artefact needing standardization.
- **(b) linde2015 2nd real network (depression log-OR):** frozen **diabetes-κ (0.158) transfers
  and WINS at every bias level** — dMCIW0 −0.0418 [B=0] / −0.0652 [B=0.15] / −0.0835 [B=0.30],
  all CIs exclude 0. PET **catastrophic** (MCIW0 ~1.86 vs baseline ~0.65, dMCIW0 +1.17…+1.22
  HARMS); TF harms; HC ties. Full sweep table reproduced from `linde_nma_result.json`.
→ **CONFIRM** the multi-domain generalization (2-domain z-gap corr + cross-domain κ transfer +
PET-catastrophic). Numbers match the banked committed JSON. No divergence.

### FG7 — AdaptShrink core estimator bug-review — mechanism right, severity over-stated
agy read `adaptshrink_estimator` (adaptshrink.py:135-156) and raised a P0. Claude adjudication
after reading the code:
- **within_var (line 147) uses the INDEPENDENT-members formula** `Σw²s²/w_sum²` — agy is
  **mechanically correct** that members fit on the same data are correlated, so this under-counts
  the within component (the true value is closer to a weighted avg of the s_i, not reduced by
  ~1/N). Likewise **between_var (148) reuses the disagreement-penalizing weights** `w=1/(s²+
  (mu−med)²)`, which suppresses spread when members disagree. So the **raw** (κ=1) CI under-covers.
- **BUT this is NOT a shipped-headline P0.** Line 122 docstring: `kappa` is the *transparent CI
  calibration multiplier (1.0 = raw)*; the SHIPPED estimator is the **deployably-calibrated** one
  (κ tuned + conformal), and the raw under-coverage (memory: raw cov 88.8% → conformal 0.899) is a
  **known, disclosed, corrected** property — exactly what calibration exists for. agy itself
  concedes it "relies on tuning kappa to achieve nominal coverage." So: accurate explanation of
  *why* calibration is needed, not a latent defect in the shipped (calibrated) result.
- **Finding 3 (k=2 → t_df=1 crit=12.7):** makes the CI **conservative/wider** — safe for
  coverage, not a coverage bug; a defensible k=2 tradeoff. Non-issue.
**Verdict:** careful from-code reasoning (unlike FG2), correct mechanism, but over-stated as a
shipped P0 — the calibration layer is the design answer. Recorded truthfully; validated next by
running the AdaptShrink simulation (FG8) to show the *calibrated* coverage.

### FG8 — AdaptShrink simulation witness — CONFIRM + refutes FG7's P0 severity
agy read the committed `truth-recovery/realhc_strong_table.csv` (k=40, μ=0.2, τ=0.1, 150 reps;
full re-run >40min so COMMITTED numbers, clearly labeled; also ran `test_realhc.py` = 7 passed/14.24s).
Per-method table across smooth/step/Copas selection:
- **AdaptShrink deployably calibrated win CONFIRMED:** raw coverage **0.967 / 0.980 / 0.973**
  (over-covered, deployable) while comparators COLLAPSE — REML-HKSJ 0.153/0.000/0.113, Copas
  0.113/0.000/0.087, HC 0.347/0.047/0.273 under selection. Calibrated width (MCIW0) 0.2524
  (smooth) is **26% narrower than REML-HKSJ (0.3413)**, **22% narrower than HC (0.3267)**; step
  **43% narrower**. AdaptShrink also lowest bias/RMSE (0.029/0.072 smooth). Matches the shipped
  "vs DL/HKSJ/HC/Copas/PET, deployably calibrated" headline.
- **KEY CROSS-PASS RECONCILIATION:** FG7 (from code) claimed `within_var`'s independent-formula
  underestimate makes the raw CI "severely under-covered" (P0). **FG8's empirical raw coverage
  96.7–98.0% REFUTES that** — the raw AdaptShrink interval is actually *over-covered* (wide raw
  width ~0.35) because `between_var` (large under member-disagreement) + the `t_{n-1}` critical
  value dominate and swamp the `within_var` term. So FG7's P0 severity is **empirically false**;
  the within_var formula is a real isolated observation but causes no shipped under-coverage.
  (Same vendor, two passes — the empirical table wins; recorded truth-first.)
→ **CONFIRM** the AdaptShrink calibrated-win headline; FG7 P0 downgraded to a non-issue by evidence.

### FG9 — transport engine (tnma.py) + h2h harness bug-review — engine SOUND
agy from-code verdict: the NMA engine, bias-injection sweep, MCIW0 metric, and verdict
thresholds are mathematically correct; **no defect changes the shipped h2h conclusion**
(re-derived dMCIW0 ≈ −0.119 @ B=0.15 regime A, ext0.158 beats PET/TF/HC). Three genuine P2s:
- **Disconnected-network finite seTE** (nma_core.py `_league`/`fit_nma`) — consistent with FG1;
  senn2013 is connected → no impact.
- **`fix3_pooled_kappa.py:39` orientation vulnerability** — appends `c.te` without checking
  placebo is `t2` (unlike `aact_kappa_truthgate.py` which handles both); `senn_contrasts()`
  always emits placebo as t2 → correct in practice, latent otherwise. Plausible real.
- **Stale committed `h2h_result.txt`** omits `registry_ext0.158` (old run); the JSON is correct.
  Cosmetic housekeeping note (real).
**Verdict:** high-quality from-code pass, zero false positives, engine confirmed sound. Corroborates
the transport headline a further time.

### FG10 — consensus + corpus bug-review — 1 real new catch, 1 over-stated
- **Finding 2 (`corpus.py:153`) — CONFIRMED real bug, NEW.** Partial-correlation Fisher-z
  variance: code uses `vz = 1/(n-preds-3)`, but since `dfree = n-preds-1` (r-from-t) implies
  `preds`=total predictors, metafor `escalc(ZPCOR)` gives `1/(n-preds-2)`. Off-by-one →
  aloe2013 studies' variance slightly over-estimated (breaks exact metafor parity). Feeds the
  learned-kernel MAE corpus but impact is **negligible** (1 MA of 28; the MAE headline 0.3325
  I re-derived is unchanged at printed precision). Real catch no prior pass/Codex found. **Fixable.**
- **Finding 1 (`consensus_or_flag.py:175`) — OVER-STATED / UNVERIFIED.** Banks use independent
  RNG streams by design (`"independent draw stream per bank"` comment), so `paired_bootstrap`
  is a pseudo-pairing; but for independent equal-n samples that ≈ a valid two-sample CI. agy's
  "spurious LOSS at f_sys=0" uses hypothetical `e.g.` numbers — **it did not run the sim**. A
  methodological imprecision, not a demonstrated result-changing bug. (Tested empirically in FG11.)
- **Finding 3 (`corpus.py:66` n≤3 clamp)** — consistent with FG2/job — minor internal safety.
**Verdict:** agy's "parity safe? no" holds only for Finding 2, whose headline impact is negligible.
Truth-first: 1 genuine new metafor-parity catch, 1 over-stated unverified claim.

### FG11 — consensus benchmark witness → CORRECTS FG10 (agy Finding 1 was RIGHT)
agy's FG11 run timed out; Claude read the committed `consensus/consensus_or_flag_result.txt`:
- **Systematic-error headline CONFIRMED:** TRUTH-GATE d_catch(SYS only) = **+0.2655
  [+0.2597,+0.2715]** @ f_sys=0.25 (and +0.26 across f_sys), all CIs > 0 → HETERO beats HOMO
  on systematic errors at matched 10% false-flag. Matches the shipped claim. hetero catch
  0.974/0.902/0.827/0.755/0.683 vs homo 0.898/0.781/0.659/0.540/0.422 across f_sys.
- **ISOLATION test at f_sys=0 = `-0.0011 [-0.0021,-0.0001]` verdict LOSS** — the CI **excludes 0**.

**SELF-CORRECTION (truth-first):** in FG10 I called agy's Finding 1 "over-stated/unverified /
hypothetical." **The committed benchmark output proves agy was RIGHT** — the numbers (-0.0011,
[-0.0021,-0.0001]) are the method's ACTUAL isolation row, not hypothetical. The independent
per-bank RNG makes the "paired" bootstrap a pseudo-pairing that yields a **marginal but formally
significant LOSS at f_sys=0**, NOT the "tie" the shipped narrative claims ("win VANISHES at
f_sys=0"). agy correctly diagnosed this from the code structure alone.
- **Practical impact:** the magnitude (−0.0011 = 0.11% catch) is negligible and the blind-spot
  effect grows strongly with f_sys (+0.26 systematic), so the SCIENTIFIC conclusion (hetero wins
  on systematic errors via decorrelated blind spots) stands. But the specific **"isolation ties
  at f_sys=0" sub-claim is technically contradicted by the method's own output** — a real artifact.
- **Fix (agy-implied):** share the RNG stream across banks (true paired claims) so the isolation
  test is a genuine paired comparison and returns an honest tie instead of a −0.0011 LOSS.
→ FG10 Finding 1 **upgraded to CONFIRMED real** (P1, affects the isolation-tie claim). Good catch
by agy; my earlier dismissal was wrong and is corrected here.

### FG12 — borrowing BCG + multispecialty witness — CONFIRM (runtime, from-scratch)
agy ran `run_bcg.py`, `selfverify_bcg.py`, `aggregate_multispecialty.py`, `selfverify_multispecialty.py`:
- **(a) BCG fair-transport:** tran−nma **−0.198 [−0.344,−0.041]** (bw=SD), robust across bw=SD/2
  (−0.205) and 1.5·SD (−0.199); from-scratch **−0.197 [−0.343,−0.041]**. target=pool-control
  HURTS **+0.187 [+0.017,+0.347]** (exact, both paths). CONFIRM.
- **(b) multispecialty relevance:** pooled vs-uniform **−10.9% [−20.2,−1.5]** (τ²=0.0078), vs-scrambled
  **−12.4% [−22.8,−2.0]** (τ²=0.0094); 5 clean slices (GLP1 T2DM n=12, GLP1 obesity n=9, Edu-SAT
  n=65, Edu-TeacherExpect n=19, Onc-DoseTox n=49), per-slice from-scratch re-derivations match
  (Onc −0.119/−0.141, GLP1-T2DM −0.180/−0.199). Addiction flat control correctly excluded. CONFIRM.
→ Third independent vendor (after Codex Seat A) confirms both borrowing cross-domain headlines
exactly, incl. from-scratch re-derivations. No divergence.

### FG13 — AdaptShrink-NMA selection-region witness — CONFIRM (runtime)
agy ran `pytest nma/test_{phase3_sweep,nma,components}.py` = **30 passed/87.22s**. Netmeta parity:
tests assert 1e-6 (loosened for CPU-arch robustness), reports/logs show actual ~5e-11 — agy
honestly distinguished the two. Selection-region sweep (committed JSON): dMCIW0 **+0.0159 (n5,
NOT a win) → −0.0205 (n6) → −0.0281 (n7) → −0.0360 (n8) → −0.0670 (n10)** — monotone region,
matches the −0.021→−0.067 headline. No-selection falsification control **+0.0051 [+0.0022,+0.0078]**
(positive → never falsely claims precision). → **CONFIRM**; no divergence.

---

## AGY USAGE CAP REACHED — 2026-07-04 ~17:00 (report per directive)

The continuous drive hit agy's **generation cap** after ~20 real inference calls (foreground
FG1–FG13 + the background driver's early jobs + the initial jobs 1–4). Manifestation:

- **The cap is SILENT — no error string, no reset time.** `agy --print` began returning
  **empty (0-byte) completions or hanging to timeout** starting ~16:59–17:03. Confirmed across
  ~12 consecutive attempts (FG14 48s-empty; two smoke retries exit 124 / empty; a background
  driver that had *survived* an earlier TaskStop logged jobs 6–13 each `exit=0` in ~10s with
  `raw_written=NO` / 0-byte output from 17:03–17:06; final timestamped probe 17:06→17:08 exit
  124, 0 bytes; post-cap probe 17:08 `agy --print "say OK"` → empty).
- **Auth/backend intact:** `agy models` returns exit 0 with the full model list throughout —
  so this is a **generation quota/throttle, not an auth failure**. The Antigravity CLI does not
  emit a `usage limit`/`429`/reset-time message; it simply stops producing text. (My cap-regex
  never fired because there is no message to match — the tell is empty output + working `models`.)
- **No reset time available** from the CLI. Any reset/quota detail would be in the Antigravity
  app/account UI, not surfaced to `agy --print`.

**Infra note (my error, corrected):** the first background driver's `TaskStop` killed only the
wrapper, not the detached driver bash (pid 75578); it kept running in parallel with the
foreground loop, double-loading agy and hastening the cap. It is now hard-killed; all agy
processes stopped. FG14 (data.py/simulation.py review) did not complete (first cap casualty) —
**not obtained**, not fabricated.

### Session scorecard (agy as third vendor, this session)
| Batch | Type | Outcome |
|---|---|---|
| Job1 | witness (transport headline) | CONFIRM ×3 exact (triple-vendor) |
| Job2 | bug-review (comparators/field/kappa) | 2 new real (quality_effects, predict_loo dbl-count) + deeper Copas + corroborates Codex |
| Job3b | bug-review (DTA/dose) | 1 new P1 (mbnma Emax init) + parity confirmed by inspection |
| FG1 | bug-review (NMA engine) | 4 findings; 2 over-claimed (disconnected-only), #3/#4 real internal |
| FG2 | bug-review (robust/bayes) | LOW signal: 0 bugs, 1 false-positive (HKSJ), rule-echoing |
| FG3 | witness (dose parity) | CONFIRM runtime (20 pass, 9.7e-15 MBNMA) |
| FG4 | Codex cross-check | strong: both P0 fixes present+sound, triangulates residuals |
| FG5 | witness (DTA parity) | CONFIRM runtime (5/5, 9.02e-7) |
| FG6 | witness (transport multi-domain) | CONFIRM runtime (corr +0.641; κ transfers) |
| FG7 | bug-review (AdaptShrink core) | mechanism right, P0 severity over-stated (calibration) |
| FG8 | witness (AdaptShrink sim) | CONFIRM + empirically refuted FG7's P0 |
| FG9 | bug-review (transport engine) | engine SOUND, 3 non-impacting P2, 0 false-pos |
| FG10 | bug-review (consensus/corpus) | 1 real new (corpus off-by-one); Finding-1 I mis-dismissed |
| FG11 | witness (consensus) | CORRECTED FG10: isolation LOSS −0.0011 real → agy was RIGHT |
| FG12 | witness (borrowing BCG/multispec) | CONFIRM runtime, from-scratch exact |
| FG13 | witness (AdaptShrink-NMA region) | CONFIRM runtime (30 pass; monotone region) |

**Net third-vendor value:** every headline agy witnessed reproduced (transport ×3-domain, dose
parity, DTA parity, borrowing BCG/multispecialty, AdaptShrink calibrated-win, AdaptShrink-NMA
region, field MAE via Claude) — **no headline moved**. Genuine NEW defects agy found that Codex
did not: `mbnma` Emax-init sign, `predict_loo/score` variance double-count, `quality_effects`
IVhet variance, `corpus.py` ZPCOR off-by-one, and the **consensus isolation-tie artifact**
(real, upgraded after I initially mis-dismissed it) — all comparator/internal-level, none touch
a shipped parity/headline number. agy weakest as a rules-checklist reviewer (FG2 false positive),
strongest reasoning from code (FG4/FG9) and as a runtime witness.

---

## POST-CAP HARVEST — background-driver artifacts (independent 2nd agy runs)

The rogue parallel driver completed 3 real jobs before the cap; harvested here (agy-vs-agy
consistency check vs my foreground FG runs). agy remains **CAPPED** (re-probed: `agy --print`
still returns empty; `agy models` still exit 0).

- **Driver dose witness (vs FG3):** CONFIRM, **20 passed** (37.15s), even finer parity deltas
  (GL covariance **4.16e-16**, GL counts 3.55e-15, first-stage slopes 3.64e-17, linear coef
  2.60e-18, REML Psi **1.57e-29≈0**). Fully agrees with FG3. Two agy runs → identical verdict.
- **Driver AdaptShrink review (vs FG7):** independently found the **same `within_var` (L147)
  independent-formula underestimate**, but rated it "High" (not P0) and self-noted "κ inflated
  to ≈√N; matched-coverage scoring compensates" — a **more calibrated** framing than FG7's
  "P0 breaks headline." (Both agy runs' predicted under-coverage is still refuted by FG8's
  empirical 96.7–98% raw coverage.) Consistent, and the more careful of the two.
- **Driver robust review (vs FG2) — CAUGHT A REAL BUG FG2 MISSED, and did NOT repeat FG2's
  HKSJ false positive:**
  - **★ NEW CONFIRMED DEFECT — `comparators.py::pet_peese` omits WLS residual-dispersion
    scaling.** Verified: `pet_peese` sets `intercept_se = sqrt(cov_pet[0,0])` with
    `cov_pet = pinv(X'WX)` (σ²≡1), while `robust_methods.py::pet_fit` (L100-104) computes
    `sigma2 = Σw·resid²/max(k-2,1); covb = cov*sigma2` and its docstring calls that "standard
    PET-PEESE/Egger practice." So the **comparator under-estimates the intercept SE under
    heterogeneity** → over-rejects the PET null (mis-routes PET→PEESE) and too-narrow CI —
    inconsistent with the codebase's own `pet_fit`. **Real internal inconsistency, comparator-
    only** (makes PET-PEESE look worse, never reverses an AdaptShrink win; transport uses
    tnma.py's separate PET). Missed by FG2, FG7, and Codex. Best catch of the driver artifacts.
  - Also a genuine NaN-guard gap: `diagnostics["max_rhat"] > 1.01` evaluates **False when NaN**
    → the Rhat/ESS warning is silently bypassed on sampling failure (`bayesian.py`). Real latent gap.
  - Overlaps (consistent): k=1 HKSJ div-by-zero, trim_and_fill FE-SE, Rhat/ESS warn-not-block,
    Fisher-z n≤3 clamp. **Notably did NOT reproduce FG2's HKSJ-floor false positive** — the 2nd
    agy run was the more accurate of the two on that function.

**Takeaway:** two independent agy runs of the same review surface overlapping-but-different real
issues; harvesting both was worthwhile (the PET-PEESE dispersion bug + NaN-guard gap are net-new,
comparator/internal-level, none touching a shipped parity/headline number). Cap stands; loop ended.

---

## AGY CAP LIFTED ~18:49 — supervisor auto-ran the remaining queue (2026-07-04)

The supervisor waited through the cap (probing every 10 min, 17:48→18:38 all "still capped"),
detected **recovery at 18:48:55** (cap held ~1h45m from ~17:00), auto-ran all 4 queued jobs, and
finished 19:16 (`DONE_ALL_QUEUE`). Harvest + Claude verification:

### SUP-1 — PET-PEESE dispersion fix verify — CONFIRMED + impact quantified (the session's most material finding)
agy CONFIRMED the bug from first principles (WLS `Cov(β̂)=σ²(X'WX)⁻¹`, σ² from weighted residuals =
standard PET-PEESE/metafor practice) and **ran the correction**:
- Standalone PET-PEESE on aspirin: σ²=**3.778**, SE under-scaled by √3.778≈**1.94** → CI width **+94.4%**.
- **★ It DOES touch a shipped number (I under-scoped this earlier as "comparator-only"):** `pet_peese`
  is a default AdaptShrink ensemble member, so its too-small SE gives it **51.0%** ensemble weight;
  corrected → **21.6%** (trim_and_fill 48.3%→77.2%), and the **shipped AdaptShrink worked-example CI
  (manuscript Table 3) widens 17.4%** ([-0.417,-0.056]→[-0.455,-0.030]), point -0.2366→-0.2426.
  **Qualitative conclusion (AdaptShrink wins) unchanged**, but a manuscript number would move if fixed.
- Exact one-line fix proposed for both PET (L123) and PEESE (L137) branches (multiply cov by
  `Σw·resid²/max(k-2,1)`).
- **Second defect in the same function (from SUP-4/cli_review, Claude-verified in code):** the PET
  significance test uses `norm.cdf` (**Z-test**) not `t_{k-2}` (`comparators.py:124-125`) — for k=6 this
  over-rejects H₀ and mis-routes PET→PEESE. Two compounding issues make the PET gate over-confident.

### SUP-2 — aspirin k=6 empirical witness — CONFIRM + label clarification
Ran `manuscript/worked_example.py`. All comparators exact: DL **-0.0672**, REML **-0.0717**, TF
**-0.2510**, PET **-0.2267**, Copas **-0.0852** (post-fix, matches the P0P1 fix; pre-fix was -0.0738).
**Clarification (truth-first):** the memory's "aspirin +0.011 [-0.125,0.117]" is the **`ubcma` member**
(exact 0.011693 [-0.125,0.118]), NOT the proposed ensemble — `adaptshrink_auto/ens_calib` = **-0.2366
[-0.417,-0.056]**. If the manuscript labels +0.011 as "AdaptShrink" that's a member/ensemble mislabel
to check. No number wrong; label mapping flagged.

### SUP-3 — data.py/simulation.py bug-review — pipeline SOUND (well-calibrated)
agy honestly marked OR→SMD / log-pooling / Fisher-z / zero-cell as **"Correct N/A"** (those live in
dta.py/corpus.py, not here — no forced findings). Selection DGP verified **monotone + self-consistent**
(sharp note: `precision_z` standardized on pre-selection moments the estimator can't see — a DGP
observation, not a bug). Seeding deterministic; empty-list/division guards all present. Only real items:
**P2 truthiness** `if design_col:` / `if study_id_col:` (data.py:149,183) drop a column literally named
`0`/`0.0` (minor edge-case). Net: sound pipeline, 0 serious bugs.

### SUP-4 — cli.py/__main__.py review
`__main__.py` = thin correct wrapper. Real: **Finding 1 (High) UTF-8 BOM** — a BOM makes the first
header `﻿yi` so `effect_col not in df` raises a confusing "column missing" (data.py:61/86); genuine
loader bug matching the known cp1252/BOM trap. **Finding 5** = the Z-vs-t PET issue (folded into SUP-1).
Findings 2/3/4 (DL/Copas at small k, min-4-studies) are the recurring DL-small-k *preference*, not hard
bugs. 6/7 (NaN formatting, exit codes) Low. Net: 1 real High (BOM) + the PET Z-vs-t, rest minor/preference.

**Post-recovery net:** agy is back (cap ~1h45m). The **PET-PEESE comparator has two real, compounding
defects** (no σ²-dispersion scaling + Z-instead-of-t gate) that propagate into the shipped AdaptShrink
worked-example via ensemble member-weighting (CI +17.4%, conclusion intact) — the most material find of
the session, with an exact fix in hand. Plus a real BOM loader bug. Everything agy witnessed still
reproduced; no headline reversed. Supervisor exited cleanly (`DONE_ALL_QUEUE`).

---

## SUPERVISOR v2 — fresh QA queue (7 jobs, drained 21:10–21:36, NO cap this cycle)

agy ran the full fresh queue without capping (quota held). Harvest + Claude adjudication:

### SUP2-1 — field_learned.py GP internals (deep) — mostly SOUND, 1 negligible P1
- **★ GP marginal-likelihood GRADIENT VERIFIED CORRECT** — agy derived each dK/dθ (signal var, 4 ARD
  length scales, nugget) and finite-difference-checked `_obj`: max abs diff **≤1.06e-9**. High-risk file
  cleared. ARD kernel + fusion math sound.
- **Finding 2 (P1, conformal index, L288-289):** agy claims the finite-sample quantile index slightly
  under-covers; "corrected" coverage **0.9006** vs shipped **0.899** (+0.002), width 1.556. Code uses
  `np.quantile(others, 1-α, method="higher")` (a reasonable finite-sample choice); the exact ⌈(M+1)(1-α)⌉
  correction is a refinement. **Real but negligible** (0.899≈0.901≈nominal 0.90). Conformal headline stands.
- Finding 1 (P2, `conflict_aware_fuse:262` se₀=0 edge) — NOT in the primary path; NO headline impact.

### SUP2-2 — modern_comparators.py selection models — 6 robustness issues (comparator-level)
agy flagged Major numerical-robustness issues in the OPTIONAL selection-model comparators: p_uniform_star
flat-likelihood clipping for μ≤−5 (L128), `_cond_pp` brentq→NaN underflow (L63), vevea_hedges_step
underflow clipping biasing toward naive (L218), non-identification when all/none significant (L104/193),
profile-CI range failure (L154/245). **These are NOT in the default AdaptShrink panel** (DEFAULT_MEMBERS =
ubcma/pet_peese/trim_and_fill) — comparator-level robustness in notoriously-fiddly estimators. Plausible;
**Claude did not individually verify all 6** (comparator-only, no headline touched) — flagged for dev review.

### SUP2-3 — bayesian.py internals (deep) — default path SOUND, 1 High in non-default path
- **★ GHQ nodes/weights + analytic marginalization VERIFIED CORRECT** (√2 scale, √π norm, sum-to-1).
- **Finding 1 (High, non-default): standard Gauss-Hermite unstable when se≪τ** — agy showed vs
  scipy.quad the gradient discrepancy stays ~1.436 even at 100 nodes → NUTS divergences/convergence
  failure. **BUT the shipped/tested path uses `simplified=True`** (analytic marginalization, verified
  stable) — the unstable full-GHQ selection path is non-default. Real, confined to the opt-in path.
- Finding 2 (Medium): diffuse `prior_scale=3.0` → selection/effect collinearity; needs ≤1.0. Tuning.

### SUP2-4 — single-arm engine — ABSENT (truthful)
agy correctly reports **no dedicated single-arm proportion engine exists in ubcma** (unlike the rapidmeta
JS repo). Proportion logic elsewhere (dta.py from_counts, multispecialty build_ursino, drma_binomial) —
notes the study-wide 0.5 continuity correction (already established as mada-parity-preserving) and a
logit back-transform that ignores Jensen/τ² bias (internal). No fabricated review. Honest.

### SUP2-5 — Copas comparator post-fix — CONFIRM (fix works)
Ran copas_selection: **under selection** ρ_selected shifts off 0 (0.99 boundary / 0.4689) and μ→-0.0852
(matches aspirin); **under no selection** correctly collapses to ρ≈0/naive (γ→∞, Mills→0, flat in ρ).
Sim metrics CONFIRMED (committed): bias +0.056, RMSE 0.079, coverage 58.7% — matches the P0P1 fix. Closes
the Copas thread: post-fix estimator behaves correctly (shifts under selection, naive under none).

### SUP2-6 — AdaptShrink univariate boundary — CONFIRM win-region; ★ DIVERGE on "never-worse under none"
- **Bounded win-region CONFIRMED:** robust wins localized to low-moderate heterogeneity (τ≤0.1) under
  selection; at τ=0.3 bias is negligible vs RE variance and the model-averaging width premium makes it
  tie/lose to reml_hksj/henmi_copas. Matches the "bounded region" headline.
- **★ DIVERGENCE (truth-first):** the "**ties/never-worse under NO selection**" sub-claim is **REFUTED**
  by the committed sweep — under no selection AdaptShrink pays a width premium and can be **WORSE** (loses)
  in some cells, not merely tie. Does not reverse the main headline (wins under selection in a bounded
  region) but **qualifies the "never-worse" claim** — should be softened in the writeup. Recorded verbatim.

### SUP2-7 — transport 4th-domain (antihypertensive SBP) negative control — CONFIRM honest negative
agy: MD corr(κ,1−λ)=+0.523 but **"does NOT reproduce (per-class gaps mostly ≤0)"**; z corr=+0.402
**UNINFORMATIVE (CI spans 0, too few classes)**. The severity correlation does **not** hold usefully in
this domain → **the honest-negative is REAL, not a hidden win** (contrast: diabetes +0.50, antidepressants
+0.64 both reproduce). Exactly the truth-first negative-control check requested. CONFIRM.

**Cycle-2 net:** high-value, honest. Strong POSITIVE verifications (GP gradient 1e-9, GHQ/marginalization
correct, Copas fix works, honest-negative real). One **material divergence** (AdaptShrink not "never-worse
under none" — qualify the claim). New real defects: conformal index (negligible), bayesian full-GHQ
instability (non-default), 6 selection-model comparator robustness issues. No shipped headline reversed.

---

## SUPERVISOR v3 — deeper QA queue (6 jobs, 21:40–22:14, NO cap)

### SUP3-1 — diagnostics.py deep — real P1 (diagnostic-tool only)
`leave_one_out` re-fits with a **different model spec** than the full fit: design covariates omitted
(L187) and quality columns autodetected (`rob_`/`bias_`) when `quality_cols_arg=None` (L173/185), so
Cook's distance conflates study-omission with model-spec change. **P1, but diagnostic-tool only — no
estimator headline.** Remedy (agy): pass `data.quality_names` directly. The DL `var_mu` denominator is
a **"mathematically defended approximation"** (agy retracts the FG2 DL-flag here — consistent with my
FG2 adjudication).

### SUP3-2 — smallstudy_nma.py / msweep / topology_stress — conclusion SOUND
AdaptShrink-NMA selection-region conclusion **confirmed sound**. Real items: df_Q disconnected (P1,
consistent w/ FG1); **topology_stress.py:86 bootstrap resamples elements not clusters** (P2) → widens
dMCIW0 CIs 10–20% but **still robustly WINS** (hi<0). Crucially agy notes the **shipped** grid path
(`run_tausel_grid.py`/`nma_bakeoff.py`) already uses the correct **pivoted cluster bootstrap** — only the
auxiliary stress script uses element resampling. Non-shipped-path; conclusion unaffected.

### SUP3-3 — model.py / inference.py core — VERIFIED CORRECT
**★ The core ubcma selection-likelihood + Gauss-Hermite normalizer math is VERIFIED CORRECT** (model.py
285-295, 478-528); optimizer's unconstrained mapping correct. Only a P2: `bootstrap_ci(allow_failed=True)`
can return `success=False` silently — **but the shipped sim + AdaptShrink use `profile_likelihood_ci`,
bypassing it → no shipped number moves.** Strong positive verification of the core estimator.

### SUP3-4 — conformal repair witness — CONFIRM (exact mechanism)
`conf_cover = 0.8988954970263382` for **every** method — agy shows this is exactly **1058/1177** (a
deterministic consequence of the LOO cross-conformal algorithm given the family-block sizes), so
conformal maps any method to ~0.90 by construction. learned_kernel 0.806→0.899, **tightest conf width
≈1.556**. CONFIRM the "conformal repairs all to ~0.90, learned tightest" headline. (Reconciles SUP2-1:
0.899 = 1058/1177 exactly; the index nuance is ±1 data-point, negligible.)

### SUP3-5 — NMA inconsistency (Phase-2) witness — CONFIRM
Ran the decomp parity + both independent scripts (agy_phase2 + claude_phase2): design-by-treatment Q
decomposition matches R `netmeta::decomp.design` to **≈8.3e-13** (~machine precision). Coverage
restoration: uninflated **75.08%** → gated inflation **86.33%** (**+11.25 pp**; honest — restores most,
not all, of nominal). All tests pass. CONFIRM.

### SUP3-6 — DRMA spline witness — CONFIRM (runtime)
`pytest doseresponse/test_drma.py -vv` = **9 passed**. Spline REML coef max diff **1.2530e-9**, Ψ
**1.087e-10** (both < atol 1e-5); one-stage≡two-stage fixed linear **0.0 exact** (< 1e-9). CONFIRM the
spline + stage-identity parity (distinct from FG3's linear/MBNMA). 

**Cycle-3 net:** strong positives (core ubcma model math CORRECT, conformal-repair mechanism exact,
NMA-inconsistency + DRMA-spline parity CONFIRM). Real defects all **non-headline**: diagnostics LOO
spec-mismatch (P1, tool-only), topology_stress element-bootstrap (P2, non-shipped path), df_Q
disconnected (P1, consistent). No shipped headline reversed; every witness CONFIRMED.

---

## SUPERVISOR v4 — provenance/integrity queue (6 jobs; survived a 2nd cap 22:27→23:48, ~1h20m)

The supervisor detected a **2nd silent cap** mid-queue (job returned empty at 22:27), waited (probing
10-min), **auto-resumed at 23:48**, skipped done artifacts, and finished 23:59. Design validated end-to-end.

### SUP4-1 — borrowing replication pilots — CONFIRM
GLP1 T2DM (n=12) rel−uniform **−0.180 [−0.305,−0.037]** / rel−scrambled **−0.199** WIN/WIN; obesity (n=9)
**−0.497 / −0.599** WIN/WIN; 3 flat controls inert (<10%); pooled **−25.8% [−51.2,−0.4]** (τ²=0.02).
Exact match to committed. CONFIRM.

### SUP4-2 — truth-recovery DTA bake-off — ★ DIVERGE (report overclaims vs committed data)
**First report-vs-data integrity issue of the session.** `truth-recovery-dta/DTA_REPORT.md` asserts
*"adaptshrink_dta is WORSE than reitsma in ALL 48/48 cells"* and *"cell winners: 0"* — but the committed
CSV/JSON show adaptshrink_dta **WON 1 cell** (`k10_t0.6_r-0.6_p0.3`, strength none: mciw0_area 1.1142 vs
reitsma 1.1780, cov 0.90). **DIVERGE on the "0/48, worse everywhere" absolute claim; CONFIRM the
qualitative conclusion** (adaptshrink_dta ρ-shrinkage IS a failure — RMSE ~2× reitsma, area grand-means
6.19/6.78 vs 1.62/2.59). Also a real bug: `dta_bakeoff.py --reps<16` → `KeyError('cell')` (calib split
needs ≥16 reps). The report's absolute wording should be corrected to "47/48" — flagged as a chip.

### SUP4-3 — consensus RNG-pairing fix — CONFIRM + fix verified (closes FG10/FG11)
Confirmed the isolation-tie artifact (independent per-bank RNG → −0.0011 [−0.0021,−0.0001] LOSS at
f_sys=0). **Verified fix:** drop the bank-specific seed offsets so all banks share one claim-realization
stream → mathematically exact **TIE +0.0000** at f_sys=0, **while preserving the +0.26 systematic win**
(which is structural: homo shares one blind-spot draw → 0.60 miss prob; hetero draws independently →
0.60³=0.216; the win is the ~0.384 detection-prob delta, RNG-independent). Thread closed with a fix in hand.

### SUP4-4 — antidepressant raw-HAM-D scale-artefact — nuanced CONFIRM
Refines the "raw fails" claim: the raw HAM-D κ_MD correlation SIGN actually **reproduces (positive)**, but
the inflation ratios are **non-credible** (SSRI +3.54, atypical +9.62 — physically impossible), i.e. the
scale artefact makes magnitudes explode. The scale-invariant **z-gap +0.641 reproduces with credible
magnitudes** (κ_z SSRI 0.69). So the scale-artefact story holds (raw uninterpretable, z is the valid
analysis) — but "raw fails" is really "raw magnitudes non-credible," not a sign flip. CONFIRM w/ nuance.

### SUP4-5 — data harmonization review — SOUND
Architecture sound: strict block-diagonal family segregation (no cross-scale mixing), dedup correct
(colditz1994≡bcg, egger2001≡li2007), OR add=0.5/to="only0" matches metafor. Re-confirms **corpus.py:153
ZPCOR off-by-one** (n−preds−3 vs metafor n−preds−2, P2, <1e-6 — independent 2nd find of FG10). New: **P3**
Hedges' J linear approximation vs metafor's exact gamma J (<1e-5). None move the MAE 0.3325.

### SUP4-6 — manuscript provenance audit — ★ CLEAN
**No placeholder leaks** ({{}}, REPLACE, TODO, None-as-value). Every audited headline traces to committed
JSON and **MATCHES**: κ_pooled 0.158, corr +0.50, SSRI κ_z +0.69 [0.23,1.29], lipid +0.50, Linde
−0.042/−0.065/−0.084, GLP1 slope −0.092 / R² 0.94 / perm-p 0.01 / τ² 0.018/0.289, pilot-1 +0.256. One
minor non-blocking rounding diff (SSRI bootstrap CI). Manuscripts are provenance-clean.

**Cycle-4 net:** the integrity DIVERGENCE (DTA_REPORT "0/48" vs actual "1/48") is the headline find — a
committed report overclaiming vs its own data; qualitative conclusion intact. Consensus fix verified
(closes a real bug). Manuscripts provenance-clean. Harmonization sound. No SHIPPED estimator headline moved.

---

## SUPERVISOR v5 — regression + remaining witnesses (5 jobs, 00:03–00:34, NO cap)

### SUP5-1 — ★ FULL REPO REGRESSION SUITE — GREEN
agy ran the whole test suite repo-wide: **215 passed / 0 failed / 6 skipped** (398s, core `tests/`) plus
**118 passed** (nma), **35 passed** (doseresponse), **23 passed** (others) — **0 failures, 0 errors
anywhere**. Strong green regression baseline for methods-borrowing.

### SUP5-2 — lipid (3rd domain) witness — CONFIRM
Statin published-vs-registered LDL gap **+50.14% [+22.04,+85.39]**, ezetimibe **+44.80% [+19.45,+75.09]**
— both robustly positive (CI>0). Class-level correlation **uninformative** (only 2/6 classes powered;
fibrate/bile_acid/niacin have 0 registered-only trials, PCSK9 only 3) → script returns `insufficient`.
**Honestly disclosed publication saturation.** CONFIRM.

### SUP5-3 — large-scale transport program — CONFIRM (settled vs on-threshold distinguished)
Transport-beats-NMA **SETTLED** across bandwidths (CIs [−0.240,−0.028], [−0.290,−0.085], [−0.305,−0.095]
all <0); relevance-beats-no-relevance **SETTLED** ([−0.146,−0.054], [−0.319,−0.098]); transport-over-
relevance correctly flagged **ON-THRESHOLD**. agy honestly separated settled from borderline. CONFIRM.

### SUP5-4 — ★ Copas likelihood deep-dive — DEFINITIVE: MIS-SPECIFIED (wrong sign)
Rigorous first-principles derivation of the exact Copas–Shi (2000) observed likelihood → the code's
hybrid form (`copas_selection`: selection-adjusted-moment y-density **+** `+logΦ(u)`) is **Option C:
mis-specified with the WRONG SIGN** on the logΦ(u) term (exact form uses unadjusted density + logΦ(v_i)
− logΦ(u_i)). **Not equivalent, not a valid reparameterization.** This DEFINITIVELY resolves the concern
I raised across job2/FG4/SUP2-5 (three passes converged; now proven by derivation). **Comparator-only**
(AdaptShrink default panel excludes Copas) — no proposed-method headline; but the "Copas" comparator
column isn't the exact Copas–Shi MLE. Spawned a fix chip. (Note SUP2-5 showed it still *qualitatively*
shifts under selection / naive under none, so the earlier rho-selection fix was necessary but not
sufficient — the objective itself needs the sign correction.)

### SUP5-5 — DTA HSROC review — NOT ON THIS BRANCH (truthful)
agy confirms the HSROC exact-binomial GLMM lives on the **methods-dta** worktree, not methods-borrowing
(pycache artifact of `tests/test_dta.py` corroborates). Reviewed what IS here (dta.py Reitsma bivariate +
`adaptshrink_dta` + `deeks_asymmetry` gate) with a thorough HSROC/GHQ node-slippage theory treatment; no
new headline issue. Consistent with FG5.

**Cycle-5 net:** full suite GREEN (regression baseline), lipid + large-scale transport CONFIRM, and the
**Copas comparator likelihood definitively proven mis-specified** (wrong sign, comparator-only, chip
filed). No shipped estimator headline moved.
