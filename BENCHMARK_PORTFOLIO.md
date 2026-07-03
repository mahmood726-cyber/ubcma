# Methods portfolio — head-to-head vs published comparators (capstone)

**Branch** `methods-borrowing` (+ `methods-dta` worktree) · 2026-07-03 · truth-first.
One table per novel method: the best published comparators, the honest verdict (beats / ties / loses),
the regime, and — where we do **not** dominate — the concrete improvement that would close the gap.
Every number links to a committed REPORT_*.md + result artifact; nothing here is computed fresh.

---

## 1. AdaptShrink univariate — matched-coverage under publication selection
Comparators: DerSimonian–Laird, REML+HKSJ (Veroniki 2016), Henmi–Copas (Copas 2010), Copas–Shi selection
MLE, PET-PEESE, trim-and-fill (Duval–Tweedie). Sim: μ=0.2, τ=0.1, k=40, 3 selection mechanisms.
**VERDICT — BEATS the RE + selection-model comparators.** `adaptshrink` (ensemble) is the only estimator
both narrow at matched coverage **and** deployably well-calibrated (raw_cov 0.96–0.98) across all three
mechanisms; DL/REML-HKSJ/HC/Copas/PET all under-cover to 0.00–0.12 deployably. Paired-bootstrap robust
win vs HC in all mechanisms (smooth −0.126, step −0.162, copas −0.066).
**Non-dominance:** trim-and-fill attains a narrower matched-*width* in smooth/step — but at broken
deployable coverage (0.19–0.60) and it fails in the copas mechanism. **Fix:** add a Vevea–Hedges
step-weight member to the ensemble. (`truth-recovery/REPORT_MATCHED_COVERAGE.md`.)

## 2. AdaptShrink-NMA — network matched-coverage under selection
Comparator: netmeta common-effect / common-DL baseline (Rücker; engine matches netmeta to ~1e-11).
**VERDICT — BEATS in a characterised region.** `adaptshrink_auto` is a paired-bootstrap robust
matched-coverage win over common-DL at strong selection in the dense small-network regime (n6, reps=800:
ΔMCIW0 −0.021 [−0.035, −0.001]); the win grows with network size (−0.021→−0.067, n6→n10) and is absent in
consistency-only cells (where point estimators coincide — honest boundary). 32 tests green.
(`nma/REPORT_NMA_BAKEOFF.md`, committed gates.)

## 3. AdaptShrink-DTA — bivariate Se/Sp matched-coverage under selection
Comparators: Reitsma bivariate model (`mada::reitsma`), HSROC, Henmi–Copas.
**VERDICT — engine EXACT + BEATS HC in a boundary region.** Σ-shrinkage engine matches `mada::reitsma`
to 9.0e-7 across 5 real datasets. Boundary map: 8 paired-bootstrap robust matched-coverage wins vs
Henmi–Copas (e.g. −0.28 [−0.42, −0.13] at strong-selection small-k), 3-vendor + from-scratch verified.
Honest: the robust win is a small-k × strong-selection region, gone by k≥10. (`truth-recovery-dta/REPORT_DTA.md`.)

## 4. Learned-kernel + conformal registry-scale borrowing field
Comparators: within-MA borrowing, robust-MAP (Schmidli 2014), hierarchical cross-MA Bayes (Higgins 2009),
power prior (Ibrahim–Chen 2000), commensurate (Hobbs 2011), SAM (Yang 2023), MAP (Neuenschwander 2010),
g-modeling NPMLE (Efron 2016), conformal (Lei 2018 / Barber 2021).
**VERDICT — BEATS all on the primary estimand.** On full-corpus held-out reconstruction (1177 nodes /
28 MAs) the learned-kernel GP is the **only** method that beats within-MA (−0.0230 [−0.0340, −0.0117]);
robust-MAP & hier-Bayes only tie; hand-field/g-model/no-borrow lose; scrambled-kernel control loses
(falsification passes). **Two-vendor external quorum** (Codex gpt-5.5 −0.0192, Fable 5 −0.0214, both
from-scratch) + 2 internal engines, all CIs<0. Conformal restores nominal 0.90 at the tightest width
(1.553). Survives real-AACT corpus expansion; wins on the real oncology-HR family (−0.0109, n=384).
**Non-dominance:** at the sparse frontier (m=1 single new study) our precision-**fusion** loses to the
power prior (+0.021) and every modern dynamic-borrowing prior. **Fix:** replace fixed inverse-variance
fusion with a learned power-prior discount a₀ (or estimated mixture weight) driven by the conflict
statistic. (`REPORT_BORROWING_FIELD.md` §11.)

## 5. Transportable NMA + registry publication-bias
Comparators (internal funnel selection models): PET/Egger, trim-and-fill, Henmi–Copas, Copas–Shi;
standard (unadjusted) transport. Real senn2013 network + real AACT registry λ + real World Bank covariate.
**VERDICT — external registry-λ BEATS every internal selection model.** On the sim, registry-λ (oracle κ)
is the only reliable winner (ΔMCIW0 −0.118/−0.306 at B=0.15/0.30), inert at B=0, in BOTH funnel-invisible
and funnel-visible regimes; **PET over-corrects catastrophically** (+0.58–0.68 every cell — per-treatment
funnel regression on 3–6 studies is too noisy); trim-fill/HC inert; Copas–Shi infeasible (k≤6/treatment).
Transportability layer: exactly inert at target=pool, WINS at a far target once a real modifier exists
(β≥~0.01). **Magnitude now supplied externally (2026-07-04): FIXED.** The registered-vs-published HbA1c
effect gap in AACT gives a frozen, oracle-free per-class inflation — `corr(κ_MD, 1−λ)=+0.50` independently
validates the (1−λ) severity model — and κ_pooled=0.158 **matches the oracle at B=0.15** (−0.119 vs −0.118)
and WINS across B≥0.15 in both funnel regimes, beating the arbitrary fixed κ=0.5. So the correction is now
*direction + calibrated magnitude*, not direction-only. The internal-funnel κ̂ was an honest negative;
the external route works. **Residual (irreducible here):** a fixed external κ over-corrects at true B=0
(+0.05) — the selection-*presence* question; the only in-data gate (network Egger) has fire-rate ≤0.04
regardless of B (funnel-orthogonal in Regime A, underpowered on ~20 studies in Regime B), so it can't
distinguish B=0 from B>0. Deploy where selection is a priori expected.
(`transport_nma/REPORT_TRANSPORT_NMA.md`, `aact_kappa*.py`.)

## 6. Dose-response MA/NMA
Comparators: `dosresmeta` (Crippa–Orsini; Greenland–Longnecker 1992), MBNMA (Mawdsley 2016) / netmeta,
`lme4::glmer`; and — for the AdaptShrink dose bake-off — two-stage REML.
**VERDICT — engines EXACT vs the gold standards; shrinkage a robust honest NULL.** Two-stage GL DRMA
matches dosresmeta to 1e-9 (linear + RCS-spline); one-stage exact-binomial logistic matches glmer to
4.5e-6; saturated MBNMA reduces to netmeta at 9.7e-15. The AdaptShrink dose-shrinkage bake-off is a
robust honest NULL vs two-stage REML across linear, interior-nonlinear, and heavy-τ/extrapolated regimes
(no valid oracle-free bias-corrector for log-RR slopes; at extrapolation shrinkage HARMS). Two-stage REML
is the right estimator. Stage-4 dose-borrowing link: kernel + dose-response model both beat the no-dose
null on real GLP1 (tie head-to-head). (`REPORT_DOSERESPONSE.md`.)

## 7. consensus-or-flag — heterogeneous verification primitive
Comparators: single verifier; homogeneous self-consistency (same verifier ×N, correlated blind spots).
**VERDICT — BEATS both on systematic errors, ties when there are none.** At matched false-flag, N=3,
heterogeneous consensus-or-flag lifts systematic-error catch by ~+0.26 over homogeneous (all CIs<0);
homogeneous barely beats single. Isolation test: at f_sys=0 (no systematic errors) hetero−homo ≈ 0 —
the advantage is provably a decorrelated-blind-spot effect. **Honesty:** modeling result; direction +
tie-at-f_sys=0 are structural, magnitudes need real-corpus calibration. (`consensus/REPORT_CONSENSUS_OR_FLAG.md`.)

---

## Portfolio verdict (honest)
In their designed regimes, **our methods beat or match the best published comparators**, each verified
by a matched-coverage / held-out truth-gate and (for the headlines) cross-vendor:
- **Clear wins:** learned-kernel field (reconstruction, two-vendor), AdaptShrink univariate (RE + selection
  models, deployably-calibrated), transportable-NMA registry-λ (vs all internal selection models),
  consensus-or-flag (vs single + self-consistency on systematic errors); DRMA/MBNMA/DTA engines are exact
  vs the gold standards.
- **Region-bounded wins (honest boundary):** AdaptShrink-NMA (dense small-network × strong selection) and
  AdaptShrink-DTA (small-k × strong selection).
- **Honest non-dominances — outcomes after implementing the named fixes (2026-07-03):**
  - (a) *sparse-frontier m=1 fusion lost to the power prior* → **FIXED / deficit closed** (`2928636`): our
    DEPLOYED fusion `conflict_aware_fuse` is byte-identical to the power prior and **ties it exactly** on
    the corpus m=1 (the loss was the pilots benchmarking the *naive* `precision_fuse`). A strict m=1 win
    comes from a better *prior* (the learned kernel — already the full-corpus headline), not the fusion rule.
  - (b) *trim-and-fill narrower matched-width than AdaptShrink in smooth/step* → **CLARIFIED as illusory**
    (`f3fec75`): trim-fill's narrow width sits at over-coverage (test_cov 0.99) with broken deployable
    coverage (raw_cov 0.19–0.66); on the metric that matters (robust matched-coverage vs HC **with**
    deployable calibration, raw_cov 0.96–0.98) AdaptShrink already dominates. The tried Vevea–Hedges member
    is an **honest negative** — too high-variance at k=40, it hurt the ensemble, so it is not adopted.
  - (c) *fixed-κ registry pub-bias correction: λ gave direction, not magnitude* → **MAGNITUDE SOLVED via the
    external AACT gap (2026-07-04)**: the internal data-driven κ̂ was an honest negative (`52233ac`, γ too noisy),
    but the **external** registered-vs-published HbA1c effect gap in AACT delivers it — `corr(κ_MD,1−λ)=+0.50`
    validates the severity model and the frozen κ_pooled=0.158 **matches the oracle at B=0.15** and WINS across
    B≥0.15 in both funnel regimes (beats the arbitrary fixed κ=0.5). Correction is now direction + calibrated
    magnitude. Residual = the orthogonal *selection-presence* gate, provably irreducible on a sparse network
    (in-data Egger gate fire-rate ≤0.04 regardless of B); deploy where selection is a priori expected.
  - (d) *dose-response predicted-effect shrinkage is a genuine null* (linear + Emax, incl. heavy-τ/
    extrapolated) → two-stage REML stays the estimator (no fix warranted).

These are the demonstrable head-to-head results the manuscripts lead with. Fix outcomes reported
truth-first: **(a) closed; (b) the gap was a coverage artefact — AdaptShrink already dominates deployably,
V-H not adopted; (c) magnitude SOLVED via the external AACT registered-vs-published gap (internal κ̂ was a
negative; external κ_pooled matches the oracle and wins B≥0.15), residual is only the irreducible
presence-gate; (d) genuine null.** No win was manufactured where the numbers did not support it.
