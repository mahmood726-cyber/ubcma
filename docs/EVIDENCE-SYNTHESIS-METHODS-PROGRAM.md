# Truth Recovery in Evidence Synthesis — Program & Roadmap

### A manifesto and roadmap — recovering the true effect from distorted evidence, under a verification-first ethos

> *Status:* living document · *Owner:* Mahmood · *Created:* 2026-06-22 · *Branch of record:* `methods-nma` (F:\ubcma); methods spine `truth-recovery-misspec`
>
> *Truth-first note:* Every claim in the **Inventory** below is grounded in what was actually found on disk — source files, verification logs, test counts, `E156-PROTOCOL.md` records, and the `rewrite-workbook.txt` entries. Where a number comes from a project's own protocol/README and was **not** independently re-derived in this survey, it is marked **[as-documented]**. Where something could not be verified, it is flagged explicitly. Marketing language has been stripped; only what the artifacts support is stated.

---

## 1. The thesis: TRUTH RECOVERY

There is a true effect. The evidence we are handed is a *distorted image* of it — bent by publication selection, small-study effects, heterogeneity misspecification, network inconsistency, and outright data-integrity failures. The single organizing aim of this entire program is **truth recovery**: to recover the true effect from that distorted evidence, and to *prove* the recovery is real rather than another illusion.

This is the spine. Every method family is one **front** in the same war:

- **Robust / selection-aware pooling** recovers truth when *publication selection and small-study effects* bend the funnel.
- **DTA and NMA variants** recover it in the harder geometries — the *bivariate* (Se/Sp) and *network* settings — where the distortion couples across dimensions or hides in a single contradicted loop.
- **Heterogeneity / regime models** recover it when the *between-study model is misspecified* and a single pooled number is the wrong object entirely.
- **Bias & reproducibility forensics** (Benford, the bias-fingerprint, reproducibility and registry audits) answer the prior question: *is the underlying evidence even truthful?* — detecting when no estimator can recover truth because the inputs are corrupt.
- **Tooling / automation** makes recovery *deployable* — at the analyst's desk, in the browser, without an oracle.

And binding all of them: **the matched-coverage truth gate is how we prove recovery happened.** A narrower interval is not recovery; a point estimate that happens to land near zero is not recovery. Recovery is demonstrated only when the estimator beats the field *at equal coverage*, deploys *without an oracle*, and survives an *independent re-implementation*. Anything less is an illusion of recovery, which is worse than honest distortion because it is believed.

We pursue this the way Ibn al-Nafīs took the physiology of his age past Galen: not by louder claims, but by reasoning from first principles, stating the logic so plainly that anyone can check it, and refusing to assert what has not been shown. The orthodoxy of evidence synthesis rests on conventions rarely stress-tested at their foundations — DerSimonian–Laird τ², inverse-variance pooling under an assumed-correct selection model, prediction intervals that quietly under-cover, network confidence that ignores where the inconsistency actually lives. This program does not reject those tools. It **corrects them from within**, builds estimators that recover truth where they cannot, and submits every recovery claim to the truth gate before it is allowed to be called one. If the honest answer is "not recovered," the result is logged as a null and the limit is named — naming exactly where truth *cannot yet* be recovered is itself a contribution.

---

## 2. The al-Nafīs working principles

Ibn al-Nafīs (1213–1288) is the patron of truth recovery. He *recovered* a true fact of human physiology — the pulmonary transit of blood — from an authoritative but distorted account, three centuries before Servetus and Harvey. He did it while writing *a commentary on Galen*: correcting the authority from inside the authority's own framework, stating his reasoning so cleanly that the correction was checkable on its own terms. That is exactly the move this program makes against the orthodoxy of evidence synthesis. Five principles, each mapped to how it already shows up as truth-recovery practice:

| # | Principle | Al-Nafīs | How it shows up here (truth recovery) |
|---|-----------|----------|----------------------|
| 1 | **First principles over deference** | Rejected Galen's invisible inter-ventricular pores because the septum is *solid* — reasoned from the anatomy, not the textbook. | We do not assume the selection model is correct. AdaptShrink model-averages bias-corrected members with disagreement-penalised weights; DL-τ² is replaced by network-shrunk τ² only where the geometry warrants it. Truth is recovered from the data's structure, not from a convention. |
| 2 | **Correct the authority from within** | Worked inside Galenic medicine, not outside it. | The netmeta-parity engine reproduces `netmeta` to ~5e-11 *first* — recovery is a strict extension of the trusted baseline, reducing to it exactly when its gates do not fire (Component B no-covariate limit reproduces the engine league to 1e-10). We out-recover the authority without abandoning it. |
| 3 | **State the logic so plainly it can be checked** | Wrote the argument out fully so it could be verified by inspection. | Every recovery claim is a seeded harness + per-replicate CSV + a report separating *confident* from *uncertain*. Independent Codex re-implementations re-derive the math from a spec without reading the source and agree to ~1e-13 — recovery anyone can re-run. |
| 4 | **Honesty about nulls and limits** | Did not over-claim beyond what the anatomy showed. | Where truth *cannot yet* be recovered, we say so: the null+step centre-bias ceiling, the single-loop inconsistency ceiling, the conformal-CI miss (1/54 cells) are documented *as failures*. BenfordMA's headline is literally "finds **no** corpus-level digit anomaly" — the absence of distortion is reported as faithfully as its presence. |
| 5 | **Priority through provenance** | His priority rests on a dated, surviving manuscript. | HMAC-signed export provenance chains; committed seeds and commit hashes for every quantitative claim; the matched-coverage truth gate (paired-bootstrap 97.5% CI of advantage < 0) is the dated, checkable record that a recovery actually happened. |

---

## 3. Guiding epigraphs

Presented respectfully as inspiration. Each verse is given with surah name and chapter:verse, a short widely-accepted English rendering, and one line on how it maps to the truth-recovery ethos. References have been checked for accuracy.

> **Ṭā-Hā 20:114** — *"My Lord, increase me in knowledge."*
> Truth recovery as an ongoing obligation, never a finished state. Every honest ceiling — every place truth is not yet recovered — is an invitation to the next increase.

> **Al-Baqarah 2:111** — *"Produce your proof, if you should be truthful."*
> The burden of proof sits with whoever claims a recovery. A new estimator is not believed because it is clever; it must produce its proof — matched-coverage evidence, independently re-implemented.

> **Ar-Raḥmān 55:9** — *"And establish weight in justice and do not make deficient the balance."*
> Calibration as the just measure of recovery. An interval that under-covers is a deficient balance — it claims to have recovered truth while skimping the coverage. Recovery is weighed at the nominal level, never narrowed to look precise.

> **Al-Baqarah 2:42** — *"And do not mix the truth with falsehood or conceal the truth while you know [it]."*
> The forensics charge directly: distortion is detected and named, not laundered. Against p-hacking, specification-shopping, and selective reporting — nulls reported as nulls, the multiverse shown in full, never collapsed to the convenient cell. You cannot recover truth you are willing to conceal.

> **Yūnus 10:101** — *"Say, 'Observe what is in the heavens and the earth.'"*
> Empiricism over authority. We recover truth by testing the field's conventions against simulated and real data — not by accepting them because they are conventional.

> **Fuṣṣilat 41:53** — *"We will show them Our signs in the horizons and within themselves until it becomes clear to them that it is the truth."*
> Recovery confirmed across independent vantage points until it is unmistakable — the spirit of the truth gate's cross-engine and cross-implementation checks (netmeta, mada, metafor; two independent Codex seats agreeing to 1e-13).

> **Ash-Sharḥ 94:6** — *"Indeed, with hardship [will be] ease."*
> Perseverance on the hard fronts of recovery. The high-τ corner, the single-loop inconsistency ceiling, the DTA selection model — these are hard, and the recovery comes after, not instead of, the hardship.

---

## 4. Inventory — the fronts of truth recovery

What exists, what is proven, what is the open frontier. Seven method families, each a **front** in truth recovery. Counts in the workbook (`F:\E156\rewrite-workbook.txt`, 1,873 total entries, **504 methods-category**, 11 submitted) indicate the *breadth of intent*; the per-project evidence below indicates the *depth of proof*.

### Family A — Robust / selection-aware pooling  *(the flagship front)*

**The front:** recover the true effect when publication selection and small-study effects bend the funnel. This is the cutting edge of the program and where the strongest recovery proofs live.

- **AdaptShrink (univariate)** — `F:\ubcma\src\ubcma\adaptshrink.py`, `robust_methods.py`. Oracle-free adaptive RE estimator: model-averages three bias-corrected members (UBCMA, PET-PEESE, trim-and-fill) with disagreement-penalised weights `w_j = 1/(se_j² + (μ_j − median μ)²)`; interval widens automatically when members diverge. τ-aware `adaptshrink_auto` switches between a calibrated ensemble (low τ) and a funnel-gated re-weighting (high τ).
  - **Proven:** Bootstrap-robust matched-coverage (MCIW0) win vs Henmi–Copas in strong selection, k=40: ΔMCIW0 = **−0.126 [−0.146, −0.101]**; deployable (no-oracle) coverage **0.967 / 0.960 / 0.977** (smooth/step/copas) vs HC 0.083–0.123. Dominates **31/51** continuous + **20/30** binary cells on the hard grid; calibrated variant raises 31→35/54 with mean coverage 0.899→0.946. All wins pass the paired-bootstrap G4 gate. *(`truth-recovery/REPORT_MATCHED_COVERAGE.md`, `REPORT_FIELD.md`, `REPORT_FIELD2.md`.)*
  - **Frontier:** null+step centre-bias (deployable coverage 0.46–0.75 when μ=0 under strong step selection — a *point-estimator* problem a symmetric interval cannot fix); high-τ (0.3–0.5) corner partly recovered (0→7/17 cells) but not eliminated; unknown-mechanism partial-identification bounds untouched.
- **UBCMA** — `src\ubcma\model.py` (23 KB mixture-normal core) + full CLI/Bayesian/bootstrap stack; 138 test functions; validated against 8 comparators (DL, DL-HKSJ, REML, REML-HKSJ, trim-fill, PET-PEESE, Copas, quality-effects). Joint heterogeneity + selection + quality-bias model. **[as-documented]** test count from package survey. Pip prototype v0.1.0, not yet shipped as a dashboard.
- **conformal-ma** — `~\code\conformal-ma` (primary) + `F:\Models\ConformalMA` mirror. Distribution-free prediction intervals. **[as-documented]** 92.1% empirical coverage vs 70.5% standard / 67.0% HKSJ across 307 Cochrane reviews. *Caveat:* the in-repo conformal CI for AdaptShrink (`adaptshrink_conformal`) is an **honest miss** — dominates only 1/54 cells; the confidence-only approach loses the bias–variance trade to model averaging. Documented, not recommended without rework.
- **SafeMA** — `F:\Models\SafeMA`. Anytime-valid sequential MA with product e-values / confidence sequences; 21 tests; live. **[as-documented]** 97% sequential coverage vs 82% traditional.
- **ImpossibleMA** — `F:\Models\ImpossibleMA`. Bounded adversarial envelopes for "unpoolable" reviews; 88 tests + 23 property-tested inputs; submitted.
- **Henmi–Copas note:** the repo `copas` app is **Copas–Shi MLE, not** metafor's `hc` Henmi–Copas — a known naming hazard recorded in memory; the *true* Henmi–Copas baseline lives in `robust_methods.py::henmi_copas` (wraps metafor::hc) and is the one used in the AdaptShrink bake-offs.

### Family B — Diagnostic test accuracy (DTA)

**The front:** recover truth in the *bivariate* geometry, where distortion couples sensitivity and specificity and threshold heterogeneity hides the true operating point.

- **AdaptShrink-DTA (methods-dta, Phase 2 in flight)** — `src\ubcma\dta.py`; sim/bake-off in worktree `F:\ubcma-dta\truth-recovery-dta`. Adaptive Σ-shrinkage of the bivariate (logit-Se, logit-Sp) covariance toward independence/threshold-aware target + Deeks-asymmetry-gated small-study correction.
  - **Proven:** bivariate likelihood validated vs R `mada::reitsma` to **~1e-3** (memory records ~9e-7 on the estimator core, cross-checked by two Codex seats + agy) on canonical datasets (Glas, AuditC); first matched-coverage milestone shows **bootstrap-robust wins at small k (k=6, 800 reps)** on the MCIW0-2D ellipse-area metric. Vectorized likelihood 3.4× faster (commit `fa67cbc`).
  - **Frontier:** Phase-2 HSROC (exact-binomial GLMM, adaptive GHQ) + REML comparator field wired in (`2a22d12`, `24af60e`) but the full per-cell report is not yet committed; not bootstrap-robust at 300 reps across the full grid yet; sparse-cell (0.5-correction) bias not yet tuned per-prevalence; the per-comparison selection model (Component c) is architecture-started, not finalised.
- **SROCPlotter** — `F:\Models\SROCPlotter`. Bivariate RE SROC; **[as-documented]** matches mada to 3 d.p., 94% simulated coverage. Shipped.
- **DTA70** *(workbook)* — an R package of 76 DTA datasets for methods research; a benchmarking asset for the family.

### Family C — Network meta-analysis (NMA)

**The front:** recover truth across a *network* of treatments, where the distortion can hide in a single contradicted loop and standard confidence ignores where the inconsistency actually lives.

- **AdaptShrink-NMA (methods-nma, Phase 2 complete)** — `F:\ubcma\nma`. Graph-theoretic engine + three components: **A** heterogeneity-structure shrinkage (shrink direct DL-τ²_c toward network-common τ² by geometry weight), **B** network-wide PEESE gated on asymmetry, **C** inconsistency-aware inflation from a Q decomposition into within/between-design.
  - **Proven:** engine reproduces `netmeta` 3.6-1 league TE/seTE to **~5e-11** on Senn2013 + smoking; two **independent Codex re-implementations** agree to **1e-13**; generalized-DL τ² to ~1e-15; multi-arm covariance (+τ²/2 shared-arm) exact; P-score ranking to ~1e-6. Component C's Q decomposition equals `netmeta::decomp.design` to **1e-13**. Component B no-covariate limit reproduces the engine league to 1e-10. **21 tests pass.** Bootstrap-robust matched-coverage win in the dense, well-powered, strong-selection cell `select_strong_dense_n6`: ΔMCIW0 **−0.021 [−0.035, −0.001]**. Component C restores coverage under inconsistency (0.760→0.851 full; 0.680→0.771 loop). *(`nma/REPORT_NMA_PHASE2.md`, `nma/verify/`.)*
  - **Frontier:** per-loop (node-split-targeted) inflation to close the single-loop ceiling (0.771 vs 0.95 nominal); selection in *sparse* networks; no Bayesian backend yet.
- **Workbook NMA family (51 entries, 3 submitted):** **ComponentNMA** (additive components, cross-validated vs netmeta, 25 tests), **SheafNMA** (cellular-sheaf inconsistency localisation — flags localized inconsistency in 5/13 nets where design-by-treatment χ² fails to reject **[as-documented]**), **SeqNMA** (sequential NMA with O'Brien–Fleming boundaries; submitted; full VERIFICATION.md), **advanced-nma-pooling** (multilevel network meta-regression with bias adjustment, Stan backend), **IPDNMA**, **Surrogate-Assisted NMA**. These are mostly browser-app methods demonstrators; the rigor ceiling (matched-coverage truth gate) currently lives in the `nma/` engine, not the apps.

### Family D — Bias & reproducibility forensics

**The front:** the *prior question* — is the underlying evidence even truthful? No estimator can recover truth from corrupt inputs; this family detects when the inputs are corrupt, so a recovery is never attempted on a foundation of fabrication or irreproducibility. The most populous proven family (84 workbook entries, 5 submitted).

- **MetaReproducer** — re-extracts effects from source PDFs and re-pools; audit of 501 Cochrane reviews / 14,340 studies; **[as-documented]** only 11.8% had accessible PDFs; 2/6 sufficiently-covered reviews showed major discrepancies incl. one direction change. Honest about its infrastructure ceiling (open-access barrier).
- **reprocheck** (`<projects>\repro-checker`) — live editorial gate for Synthēsis + standalone tool; re-sources trials from PubMed/PMC/CT.gov and recomputes DL+REML; validation suite flags corrupted cases correctly.
- **spec-collapse-atlas / MES / MultiverseMA** — multiverse synthesis at corpus scale: **[as-documented]** 55% false-robustness rate across 473 Cochrane reviews (naive IV-RE Type-I error 70–81%; weighted-likelihood interval restores 94–99% coverage). MES runs 648 specs/review across 403 reviews.
- **BenfordMA** *(workbook)* — Benford screen of 1.2M meta-analytic values: headline is an honest **null** ("no corpus-level digit anomaly").
- **The Prediction Gap** *(workbook)* — 70% of significant MAs have null-spanning prediction intervals.
- **OutcomeSwitchDetector, ContradictionMap, GWAM (ghost-weighted), EcoBiasMA, the CT.gov "hiddenness" audit family** (96 registry-audit entries).

### Family E — Heterogeneity / regime models

**The front:** recover truth when the *between-study model is misspecified* — when a single pooled number is the wrong object, the regime has shifted, or the dependence structure is non-Gaussian. (The methods spine `truth-recovery-misspec` lives here in the most literal sense.)

- **EvidenceCopula** (Clayton/Frank/Gumbel joint dependence; **[as-documented]** 89% generating-family recovery), **EvidenceHalfLife** (53.4% of MAs never analytically stabilise; 365 reviews), **EvidenceEntropy** (Shannon/KL/MI heterogeneity; entropy r=0.91 with PI width vs 0.73 for I²), **MetaShift** (changepoint regime detection in cumulative MA), **EvidenceExtremes**, **MetaFolio**. 30 workbook entries, 0 submitted — a proven-but-unsubmitted reservoir.

### Family F — Tooling & automation

**The front:** make recovery *deployable* — at the analyst's desk, in the browser, with no oracle and no server. A recovery method that only works in a simulation is not yet a recovery; this family carries it to where evidence is actually synthesised.

- **allmeta** (`F:\allmeta`) — 124-entry browser-only toolkit hub; **[as-documented]** 334 test functions, 63 parity tests at 1e-6 vs 41 R oracles, Zenodo DOI `10.5281/zenodo.20516880`, live. Includes the **km-reconstructor** (Guyot IPD reconstruction) and the **rct-extractor** bridge.
- **RapidMeta / Living-MA portfolio** (`F:\rapidmeta-finerenone`) — 57-app living-MA platform, 31 inlined engines, CT.gov integration; **[as-documented]** 17/17 in-repo apps within 10% of published benchmarks under `--strict` (dated 2026-04-16 — *re-run date not current; flag before citing*).
- **KMDigitizer** (`F:\Models\KMDigitizer`) — standalone Guyot digitizer; **[as-documented]** DAPA-HF HR within 2%.
- **RCT Extractor v5** (`<projects>\rct-extractor-v2` + ~20 domain variants) — 180+ regex patterns, Proof-Carrying Numbers with hash/provenance. Production-grade.
- Domain-specific shipped tools validated vs R: **PrognosisMeta** (93.3% match vs metafor **[as-documented]**), **RMSTmeta**, **SafetyMA**, **PredModelMA**, **ProportionMA**.

### Family G — Registry / transparency audits

**The front:** recover the *evidence that should exist but is missing* — the trials never published, the outcomes switched, the enrollment that never reached a synthesis. Truth recovery is incomplete if the distortion is in *what we were never shown*. 96 workbook entries — the CT.gov "hiddenness" / reporting-gap / outcome-switching / publication-undercount family, plus **Denominator-Calibrated Living NMA** (rankings calibrated against CT.gov enrollment denominators — 3/12 comparisons shift ranking). High breadth, 0 submitted; these are data-forensics papers more than estimator methods, but they feed the integrity ethos directly.

---

## 5. Prioritized roadmap

Ranked by *expected frontier impact × proximity to a verifiable win*. For each: the next concrete milestone, what "beating the field" means, and how it would be verified. **⚑ = already in flight.**

> **P1 — AdaptShrink univariate → StatMed submission + the null-bias fix.** ⚑ partly in flight (manuscript drafted in `F:\ubcma\manuscript`).
> *Milestone:* fix the null+step centre-bias by replacing the symmetric interval's centre with a better-centred point estimator (the limit is a point problem, not an interval problem); close the high-τ corner past 7/17. *Beating the field:* bootstrap-robust matched-coverage dominance over Henmi–Copas **and** REML-HKSJ across the full continuous+binary grid, including the μ=0 step cell. *Verification:* paired-bootstrap G4 gate (97.5% CI of advantage < 0) + deployable (κ=1, no-oracle) coverage ≥ 0.94, per-rep CSV committed. **This is the closest publishable frontier win and should ship first.**

> **P2 — AdaptShrink-NMA → per-loop inconsistency inflation + sparse-network selection.** ⚑ Phase 2 complete; this is Phase 3.
> *Milestone:* replace the global symmetric φ with node-split-targeted per-loop inflation to push the single-loop ceiling from 0.771 toward nominal 0.95; characterise Component B under sparse selection. *Beating the field:* deployable coverage restoration under inconsistency that `netmeta` + standard design-by-treatment cannot match, with no harm on consistent networks. *Verification:* cross-engine (netmeta decomp.design parity already at 1e-13) + matched-coverage bake-off + the standing two-seat Codex re-implementation.

> **P3 — AdaptShrink-DTA → Phase-2 report + bootstrap-robustness at full reps.** ⚑ in flight (`F:\ubcma-dta`, HSROC+REML field wired).
> *Milestone:* commit the per-cell HSROC-vs-Reitsma-vs-AdaptShrink-DTA report; achieve bootstrap-robust MCIW0-2D wins at 300+ reps beyond just k=6; finalise the per-comparison selection model (Component c). *Beating the field:* smaller matched-coverage ellipse area than Reitsma under threshold heterogeneity + selection. *Verification:* mada-parity (already ~1e-3 / core ~9e-7) + two-seat Codex re-derivation + paired-bootstrap gate.

> **P4 — Multiverse/forensics → a single calibrated "robustness verdict" estimator.** (spec-collapse-atlas + MES proven at corpus scale.)
> *Milestone:* unify the multiverse work into one weighted-likelihood interval with a calibrated false-robustness verdict, packaged as a methods paper rather than N browser apps. *Beating the field:* nominal coverage where naive IV-RE shows 70–81% Type-I error, demonstrated on the full Pairwise70 corpus. *Verification:* corpus-scale coverage calibration + R-oracle parity for the base estimators.

> **P5 — Surrogate / Component / Sheaf NMA → fold the app demonstrators behind the verified `nma/` engine.** (Workbook breadth, engine-grade rigor gap.)
> *Milestone:* re-implement ComponentNMA and SheafNMA inconsistency localisation on top of the netmeta-parity engine so their claims inherit the 5e-11 / 1e-13 verification standard, then truth-gate them. *Beating the field:* localized inconsistency detection with a controlled Type-I error that design-by-treatment χ² misses, *proven on the verified engine* not a standalone app. *Verification:* simulation Type-I/sensitivity + engine parity + matched-coverage.

*Lower tier (proven, awaiting packaging):* heterogeneity-regime family (Family E) → consolidate EvidenceCopula/EvidenceEntropy/MetaShift into one heterogeneity-characterisation paper; tooling (allmeta/RapidMeta/KMDigitizer) is shipped and serves as the dissemination substrate rather than a frontier target.

---

## 6. Publication & dissemination

Two tracks, matched to two audiences:

- **StatMed-class methods manuscripts** — the rigor frontier. AdaptShrink (univariate) is drafted (`F:\ubcma\manuscript`, all numbers truth-gated); AdaptShrink-NMA and AdaptShrink-DTA follow as companion methods papers once their Phase-2/3 milestones close. Each carries: a seeded reproduction harness, per-replicate data, cross-engine parity, and an independent re-implementation appendix. These are the papers that argue *from first principles* and must withstand a referee re-running the gate.
- **Synthēsis (E156 micro-papers)** — the dissemination frontier. The 7-sentence contract is the venue for the forensics, registry-audit, and tooling families (Families D/F/G), where the contribution is a finding or a deployable tool rather than a new estimator. *Editorial-integrity constraint (non-negotiable):* because of editorial-board overlap with Synthēsis, methods submissions there take **middle-author only** positions with explicit independent-editor handling and full disclosure (board membership, no role in the editorial decision). Disclosure-only is insufficient; the structural separation is the guarantee.

The dual track is itself an al-Nafīs move: the deep correction goes to the journal that will check it hardest (StatMed-class), and the broad correction reaches the field fastest (Synthēsis micro-papers) — neither over-claims beyond what its evidence supports.

---

## 7. The truth gate — how we prove recovery is real (applies to everything above)

The gate is the instrument that separates *recovery* from the *illusion of recovery*. A result graduates from "interesting" to "truth recovered" only when it passes all of:

1. **Matched coverage** — recovery is measured at equal (nominal) coverage, never by a narrower interval that under-covers. A tighter interval that recovered nothing is the illusion the gate exists to reject. *(Ar-Raḥmān 55:9.)*
2. **Deployable coverage** — it recovers at κ=1, with no oracle calibration the analyst would not have in practice. Recovery that needs the answer in advance is not recovery.
3. **Paired-bootstrap robustness** — the 97.5% CI of the advantage excludes zero (the G4 gate). The recovery is not a lucky draw.
4. **Cross-engine / cross-implementation agreement** — parity with netmeta/mada/metafor *and* an independent re-derivation from spec. The recovery is confirmed from independent vantage points. *(Fuṣṣilat 41:53.)*
5. **Honest null otherwise** — if it does not pass, the limit is named and committed as a result: *this is where truth cannot yet be recovered.* *(Al-Baqarah 2:42.)*

> *"Produce your proof, if you should be truthful."* — Al-Baqarah 2:111
