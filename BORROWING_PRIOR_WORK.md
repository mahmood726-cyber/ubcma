# Prior-Work Catalog — "Gravitational Borrowing Field" Methods Program

> *Read-only reconnaissance · compiled 2026-06-30 · owner: Mahmood · host: pc1 (this workstation)*
> Purpose: ensure the new **registry-scale borrowing field** program (registry-scale Bayesian borrowing + transportability + registry-based publication bias + dose-response MA/NMA + large-scale NMA) builds on existing work instead of reinventing it.
> Scope of the new idea: *every trial influences every result* — a borrowing "field" where the strength of borrowing between any two trials is modulated by their transportability, their registry/selection status, and the network/dose geometry.
> Method: directory + git survey across F:\ubcma, F:\E156, F:\allmeta, F:\Models, <projects>, ~\code, and a full-drive sweep (C:, F:, G:) for external data. No files changed. Counts/claims are from on-disk artifacts; where a number is a project's own README it is marked **[as-documented]**.

---

## 0. The foundation already written down

The program already has a manifesto: **`F:\ubcma\docs\EVIDENCE-SYNTHESIS-METHODS-PROGRAM.md`** ("Truth Recovery in Evidence Synthesis"). It organizes the existing portfolio into seven method families (A robust/selection pooling, B DTA, C NMA, D forensics, E heterogeneity, F tooling, G registry audits) all bound by a **matched-coverage truth gate**. The borrowing-field program is best framed as a *new front* on that spine: it fuses Family A (borrowing), the transportability work (new), Family G (registry pub-bias), dose-response (new), and Family C (large-scale NMA) into one coupled estimator. **Reuse: adopt this doc's truth-gate as the borrowing field's acceptance criterion verbatim.**

---

## 1. Borrowing / shrinkage / empirical-Bayes / priors  *(the kernel)*

| Component | Path | What it does | State | Reuse note |
|---|---|---|---|---|
| **AdaptShrink** ⭐ | `F:\ubcma\src\ubcma\adaptshrink.py` (+`robust_methods.py`, `comparators.py`) | Oracle-free adaptive shrinkage; model-averages bias-corrected members (UBCMA, PET-PEESE, trim-fill) with disagreement-penalised weights `w_j = 1/(se_j² + (μ_j−median)²)`; total SE = √(within + between-member); κ-scaled interval auto-widens on member disagreement. | `methods-nma`, dirty (submission artifacts only); 25 tests | **The literal borrowing kernel.** Each trial supplies several borrowing estimators; AdaptShrink fuses them and inflates uncertainty when they disagree. Generalises to "borrow from neighbours" by treating other trials as members. |
| **GWAM** ⭐ | `F:\Models\GWAM` | Ghost-Weighted Aggregate MA: CT.gov-linkage → ghost classification (no PMID + no posted results) → λ "integrity ratio" ∈ [0,1] shrinkage; Pairwise70-benchmarked; review-clustered bootstrap on λ posterior. | `master`, dirty (e156/final-package); 9 tests; `fetch_ctgov_registry.py` | **Registry-scale, selection-aware borrowing weight.** Every trial earns a λ from its registry footprint; linked→borrow more, ghost→shrink hard. Directly the "registry pub-bias × borrowing" coupling. |
| **MAPriors** ⭐ | `F:\Models\MAPriors` | MAP / robust-mixture priors from historical trials; dynamic-borrowing weight slider w∈[0,1], ESS per component, prior-data-conflict detector, commensurate-prior robustification. | `master`, clean; 60+ Selenium | **Dynamic-borrowing + commensurate-prior front end.** Robust prior = w·MAP + (1−w)·vague; conflict detector auto-downweights when historical data clashes with current. Pairwise borrowing → generalise to many-source. |
| **HyperMeta** (New_Heterogeneity_Model) | `F:\Models\New_Heterogeneity_Model` | Empirical-Bayes τ² shrinkage toward an outcome-specific prior atlas built from **17,066 Cochrane reviews** (`granular_priors.csv`); conflict-aware weight; HKSJ on pooled SE. (R) | `master`, clean; 15 unit tests | **Drop-in EB prior for the field's between-study variance.** No tuning — decades of evidence baked into the atlas; auto-downweights when observed τ² conflicts. |
| **PriorLab** | `F:\Models\PriorLab` | SHELF prior elicitation: 6 families, quantile matching, multi-expert linear/log pools, JSON/R/Python export, TruthCert provenance. | `master`, clean; 31 tests | **How analysts specify borrowing appetite.** Exported priors feed BayesianMA; log-pool = consensus weighting across borrowing strategies. |
| **BayesianMA** | `F:\Models\BayesianMA` | Normal-Normal hierarchical MA, grid posterior (200×200), study shrinkage plot, 3 prior postures (vague/weak/skeptical), MAIF export. | `master`, clean; cross-checked vs `bayesmeta` R | **Hierarchical-borrowing frontend + shrinkage visualization.** Conjugate-only (no selection model) — a display/decision layer, not the engine. |
| **PlatformTrialMA** | `F:\Models\PlatformTrialMA` | GLS pooling with shared-control covariance (off-diagonal τ²/2), non-concurrent-control adjustment, Higham nearPD. | `master`, clean; 21 tests | **The "field coupling" math.** Correct covariance when trials share controls/arms — the mechanical core of letting one trial influence another. |
| **FederatedMA** | `F:\Models\FederatedMA` | Differential-privacy (Laplace, per-site ε) + secure aggregation; precision-privacy tradeoff; ε budget tracker. | `master`, clean; 17 tests | **Multi-institution borrowing under data-sharing constraints.** Seeded PRNG = reproducible noise. |
| **DPMA** | `F:\Models\DPMA` | Dirichlet-process mixture MA — learns K subgroups from data (CRP Gibbs) vs DL baseline. | `truth-recovery-validation`; 2 tests | **Nonparametric latent-subgroup borrowing** — borrow within discovered clusters; template for dose-curve mixtures. |
| **ROBMA** | `F:\Models\ROBMA` | Reproducible-MA workflow + leave-one-out + model averaging over 5 variants; F1000 validation capsule. | `master`, clean; 2 tests | **Reproducibility wrapper** — wrap any borrowing method for LOO diagnostics + capsule provenance. |

**Borrowing shortlist:** AdaptShrink (kernel) · GWAM (registry-scale selection weight) · MAPriors+HyperMeta (commensurate/EB priors).

---

## 2. Transportability / target-population standardization / fusion  *(the new modulating layer)*

| Component | Path | What it does | State | Reuse note |
|---|---|---|---|---|
| **TransportabilityCalc** ⭐ | `F:\Models\TransportabilityCalc` | Composite CTE penalty index = temporal decay × age/sex mismatch × heterogeneity inflation × domain attenuation; tested on 445 reviews × 11,974 comparisons. | `master`, clean; 20 Selenium | **Aggregate-only transportability score — batchable across the whole registry.** This penalty is the natural modulator of borrowing strength between trial and target. |
| **TransportMA** ⭐ | `F:\Models\TransportMA` | Causal transportability: inverse-odds-of-selection weighting (IOSW) + calibration + doubly-robust estimator (587-line JS). | `master`, clean; ~20 Selenium; manuscript | **The principled transport estimator** to map trial→target before borrowing; doubly-robust under covariate shift. |
| **tda-meta** ⭐ | `F:\Models\tda-meta` | Persistent-homology detection of "holes" = populations with **zero transportable evidence** in 7D covariate space (Vietoris-Rips → isolation score 0–100). | `master`, dirty (cache); pipeline+contract tests | **The positivity certificate.** Flags where the borrowing field has *no support* — must not borrow into a hole. (This is the "topo-transport" work referenced in memory; lives here + TDA_MA.) |
| **HTA_Transportability_Engine** | `F:\Models\HTA_Transportability_Engine` | R pipeline: Cochrane × CT.gov linkage, transportability scaffold, target-population CV, CTE penalty model. | `master`, dirty (config_paths.R); 2 R tests | **Ready-made R pipeline joining reviews to the registry** + target-population cross-validation. |
| **TargetTrialMA** | `F:\Models\TargetTrialMA` | RE-MA of RCTs + target-trial emulations with ROBINS-I quality weighting; interaction test RCT vs TTE. | `master`, clean; 18 Selenium | **When observational emulations can strengthen trial-based transport** (quality-weighted). |
| **EquityMA** | `F:\Models\EquityMA` | PROGRESS-Plus equity-stratified MA; subgroup interaction power. | `master`, clean; Selenium | **Transportability along social-determinant strata** when sample↔target mismatch is equity-driven. |
| **CausalFusion** | `F:\Models\CausalFusion` | — | **STUB / empty** | Reserved namespace; the data-fusion engine the program wants does **not** yet exist here. |

**Transportability shortlist:** tda-meta (positivity gaps) · TransportabilityCalc (scalable penalty) · TransportMA (doubly-robust estimator).

---

## 3. Large-scale / Network MA  *(the geometry)*

| Component | Path | What it does | State | Reuse note |
|---|---|---|---|---|
| **AdaptShrink-NMA engine** ⭐ | `F:\ubcma\nma` (`nma_core.py`, `adaptshrink_nma.py`, `inconsistency_nma.py`, `smallstudy_nma.py`) | Graph-theoretic (Rücker electrical-network) NMA, multi-arm covariance, generalized-DL τ²; **netmeta 3.6-1 parity ~5e-11**, two independent Codex re-impls agree 1e-13. Components A (heterogeneity shrinkage toward network-common τ²), B (network-funnel PET-PEESE), C (inconsistency-aware inflation from design Q-split). | `methods-nma`; 21–23 tests; Phase-2 complete | **The verified large-scale network backbone.** Component A *already is* geometry-weighted borrowing (`λ_c = ν/(ν+(n_c−1)s_c)`). Borrowing field extends A/B/C across the whole network. |
| **advanced-nma-pooling** | `F:\Models\advanced-nma-pooling` | AD-NMA + IPD/AD (ML-NMR), design-stratified bias adjustment, **Stan + analytic Bayesian backends**, survival NPH; pub-grade validation gates. | `main`; 25 tests | **The Bayesian + ML-NMR backend the `nma/` engine lacks.** Config-driven `.inference` layer is the orchestration seam for a registry-scale Bayesian field. |
| **ComponentNMA** | `F:\Models\ComponentNMA` (+ allmeta `cnma-receptor.js`) | Additive component NMA (Welton/Rücker), cross-validated vs netmeta::discomb 1e-6. | app + module | **Borrow across shared treatment *components*** (e.g. receptor agonism) — a borrowing axis orthogonal to trials. |
| **SheafNMA** | `F:\Models\SheafNMA` | Cellular-sheaf localisation of inconsistency (flags localized inconsistency where design-by-treatment χ² fails). | app | **Localise where the field's coupling breaks** (inconsistent loops) before borrowing through them. |
| **IPDNMA / IndirectComparison / MultivarMA / CINeMA** | `F:\Models\{IPDNMA,IndirectComparison,MultivarMA,CINeMA}` | IPD-NMA, Bucher indirect, multivariate MA, confidence-in-NMA grading. | apps | Supporting geometry + credibility grading for network borrowing. |
| **allmeta NMA modules** | `F:\allmeta\shared\{nma-multiarm-v1,multiplicative-nma,nma-meta-regression,multi-outcome-nma}.js` | Multi-arm GLS (netmeta ≤1e-6), multiplicative-heterogeneity NMA, network meta-regression (treatment×covariate, PM τ²), multi-outcome NMA. | R-verified modules | **Browser-deployable network primitives**; nma-meta-regression is the entry point for covariate-modulated (transported) network borrowing. |

**NMA shortlist:** `F:\ubcma\nma` engine (verified core + A/B/C template) · advanced-nma-pooling (Bayesian/ML-NMR backend) · allmeta nma-meta-regression (covariate modulation).

---

## 4. Dose-response MA/NMA & model-based NMA  *(thin — mostly a gap)*

| Component | Path | What it does | State | Reuse note |
|---|---|---|---|---|
| **dose-response.js** | `F:\allmeta\shared\dose-response.js` | Two-stage **Greenland–Longnecker / Orsini** linear dose-response: within-study GL covariance reconstruction (cc/ir/ci designs) → per-study GLS slope → REML pool. Verified vs R `dosresmeta` ~1e-6 (alcohol_cvd). | R-verified module | **The only real DRMA on disk.** Self-contained linear-dose pipeline; covariance reconstruction reusable; **needs extension to splines + dose-class NMA.** |
| **multiplicative-nma.js / cnma-receptor.js** | `F:\allmeta\shared` | Overdispersion NMA; additive component NMA with receptor decomposition (GLP-1/GIP/GCG). | modules | **Closest thing to model-based NMA** — component/receptor structure is a dose-mechanism analogue. |
| **MetaRegression** | `F:\Models\MetaRegression` | Mixed-effects meta-regression, ≤5 moderators, permutation tests, Akaike model averaging. | app | **Dose as a continuous moderator** + permutation null for dose-effect testing. |
| **DPMA** | `F:\Models\DPMA` | (see §1) DP mixture. | | **DP-valued dose-effect curves** — nonparametric dose-response borrowing template. |

**Gap flag:** no spline/non-linear DRMA, no dose-response *NMA* (model-based network DR), no dose-borrowing across curves. This is the least-covered program component.

---

## 5. Registry-based publication bias / selection models  *(Family G + selection)*

| Component | Path | What it does | State | Reuse note |
|---|---|---|---|---|
| **GWAM** | `F:\Models\GWAM` | (see §1) — registry-linkage → λ selection weight. | | **The registry-vs-published selection model**, already CT.gov-wired and Pairwise70-benchmarked. |
| **Denominator_Calibrated_Living_NMA** | `F:\Models\Denominator_Calibrated_Living_NMA` | Living NMA calibrated against registry denominators; models silent trials, endpoint/publication missingness, extraction uncertainty, multi-witness disagreement; rct-extractor-v2 bridge; cardio HF/AF datasets. | `master`; smoke tests | **Registry-denominator calibration scaffold** — the "trials that should exist but didn't publish" layer of the field. |
| **PubBiasSuite** | `F:\Models\PubBiasSuite` | 12-method pub-bias ensemble (Egger/Begg, trim-fill, PET/PEESE, 3PSM, p-curve, p-uniform*, WAAP-WLS, limit-MA, 3 funnels) + traffic-light verdicts. | app | **Full selection-model toolbox** to characterise corpus-level selection before borrowing. |
| **realhc_bakeoff.py** | `F:\ubcma\truth-recovery\realhc_bakeoff.py` | Genuine Henmi–Copas (metafor::hc, 2e-8) vs UBCMA/Copas-Shi under matched coverage. | in ubcma | **The selection-model baseline** the field must beat; HC naming-hazard already resolved here. |
| **OutcomeSwitchDetector / ProtoPubDrift / GuidelineLag / CTGovHub** | `F:\Models\*` | Outcome switching (registry vs published), protocol-drift, evidence→guideline lag, CT.gov v2 API bridge (dose schedules, eligibility). | apps/modules | **Registry-integrity selection components** + the CT.gov ingestion layer (CTGovHub) for live denominators. |

**Pub-bias shortlist:** GWAM (registry λ) · Denominator_Calibrated_Living_NMA (denominator scaffold) · CTGovHub (live CT.gov ingestion).

---

## 6. Truth-gate / matched-coverage bake-off / reproduce-or-remove  *(the acceptance instrument)*

| Component | Path | What it does | Reuse note |
|---|---|---|---|
| **matched_coverage_bakeoff.py** ⭐ | `F:\ubcma\truth-recovery\matched_coverage_bakeoff.py` | MCIW0 metric (calibrate κ to hit target coverage on held-out split, measure width on disjoint test); EFFICIENCY vs DEPLOYABLE (κ=1) claims; G3 coverage gate + **G4 paired-bootstrap gate** (97.5% CI of advantage < 0). | **The gold-standard acceptance test for any borrowing-field claim.** Per-cell, seeded, reproducible. |
| **field_bakeoff.py** | `F:\ubcma\truth-recovery\field_bakeoff.py` | 12-estimator tournament, per-cell paired-bootstrap verdicts; shardable (`--shard/--nshards`). | **Method-tournament harness** — drop borrowing-field variants into the panel. |
| **misspec_harness.py** | `F:\ubcma\truth-recovery\misspec_harness.py` | Robustness under *mismatched* selection mechanism (smooth/step/copas at same true μ). | **Mechanism-misspecification robustness** for the field's selection layer. |
| **NMA_SCOREBOARD.py** | `F:\ubcma\truth-recovery\NMA_SCOREBOARD.py` | Aggregates per-rep CSVs → per-(τ,k) MCIW0 scoreboard + honest residual-weakness report. | **Final-report generator** template. |
| **repro-checker** | `<projects>\repro-checker` (`synthesis_gate.py`) | Re-sources trials from PubMed/PMC/CT.gov, recomputes DL+REML, flags divergence; editorial gate + standalone; 7 tests + known-truth fixtures. | **Reproduce-or-remove gate** — re-source registry data, recompute, flag before borrowing. |
| **truth-recovery-sweep** | `<projects>\truth-recovery-sweep` | Distributed sweep orchestrator, 125 subprojects (incl. `dose-response-pro`, `component-nma`, `adaptsim`), RUNNING_TABLE.md. | **Parallel platform** to run the field tournament at registry scale. Not a git repo (orchestrator). |
| **conformal-ma** | `~\code\conformal-ma` (+ `F:\Models\ConformalMA`) | Distribution-free prediction intervals; **[as-documented]** 92.1% vs 70.5% standard across 307 reviews. *Caveat:* in-repo conformal AdaptShrink is an honest miss (1/54 cells). | **Coverage layer** for the field's intervals; use the standalone conformal PI, not the AdaptShrink-conformal combo. |

**Harness shortlist:** matched_coverage_bakeoff.py (MCIW0 + G4 gate) · field_bakeoff.py (tournament) · repro-checker (reproduce-or-remove).

---

## 7. External data on disk  *(the registry + target-population layer)*

> **Drives present on pc1:** C: (Main, 235 GB), F: (Storage, 466 GB), G: (Google Drive, 235 GB). D: = empty optical (0 B). No network drives mounted. The WHO/World Bank data my first pass missed live on **F:\**, not <projects>.

### 7a. ClinicalTrials.gov / AACT  *(the trial registry)*
- **`F:\AACT-storage\AACT\2026-04-12`** — full AACT snapshot, **~14 GB, 49 pipe/tab-delimited `.txt` tables** (studies, outcomes, outcome_analyses, baseline_measurements, design_outcomes, conditions, facilities…). DuckDB-queryable via `read_csv()`.
- Access libs: **`<projects>\aact-kit`** (5-backend lib), **`F:\aact-cockpit`** (ingests → `data/warehouse/aact_<date>.duckdb` ~2 GB). Candidate roots in code: `F:\AACT-storage\AACT`, `D:\AACT-storage\AACT`, `D:\AACT`, `C:\AACT`. (`E:\AACT` does **not** exist.)
- Gold-file builders: `<projects>\cm-factory\scripts\*\build_aact_*_gold.py`.
- **Reuse: the trial universe** — every node of the borrowing field; CT.gov linkage is also GWAM's λ source.

### 7b. IHME / Global Burden of Disease  *(target-population disease burden)*
- **`<projects>\ihme-data-lakehouse`** *(also mirrored at `<projects>\ihme-data-lakehouse`)* — git repo, **39 passing tests**. GBD 2023: Deaths/DALYs **13,872 rows × 204 countries (1990–2023)**, Population 20,808, **SDI 52,992 (1950–2021)**, YLL/YLD, CVD subset 8,736; CSV + Parquet; bronze/silver/datasets medallion; `ihme-data` CLI (`fetch/promote/search`).
- **`F:\data\Obesity-IHME`** — ~**1 GB** of IHME global+USA overweight/obesity prevalence 1990–2050 by age/sex (CSV).
- **`F:\data\Research-Archives\IHME`** + **`F:\Downloads\IHME-GBD_2023_DATA-ba202403-1\*.csv`** — additional GBD extracts.
- **Reuse: target-population baselines** (SDI, mortality, DALYs, demographics, obesity prevalence) → the covariate distributions transportability weighting standardizes toward.

### 7c. WHO Data Lakehouse  *(corrected — IS on disk)*
- **`<projects>\who-data-lakehouse`** *(README installs from `<projects>\who-data-lakehouse`)* — git repo, **81 tests** (mock, no-network). Medallion layout: **raw ~9.25 GB (3,543 files), silver ~6.8 GB (7,527 parquet)**, `catalog.parquet`.
  - **Sources:** GHO OData (indicators/dimensions), **WHO Mortality Database** (`morticd09/10`, 5 parts ~60 MB), **GHED** Global Health Expenditure (`ghed_data.parquet` 25 MB), **HIDR** Health Inequality Data Repository (`rep_gho`, `rep_gho_ncd`, `rep_ghe_daly/deaths_age`, `rep_ihme_malaria`), GLAAS, COVID, World Health Statistics, **XMart** services (mncah ~41M rows, wiise/immunization ~53M rows, ncd, ntd, nutrition, flumart). Life-expectancy `LIFE_*` + `GHE_DALYNUM` parquet.
  - **6 domain extractors** → DataFrame `(country_iso3, year, indicator, value, sex, data_source)`: Mortality (life-exp, U5MR, maternal, neonatal), Morbidity (TB/malaria/HIV/NCD obesity), Risk Factors (tobacco/alcohol/obesity/raised-BP), Health Systems (UHC index, doctors, beds), Expenditure (CHE/GDP, OOP, GGHE), Immunization (DTP3, MCV1, BCG).
  - ⭐ **`crosswalk.py`** — maps **WHO ISO3 ↔ IHME location_id ↔ World Bank country code for 66 countries** (`enrich_dataframe()`). **This is the join key that fuses all three data systems** — directly the transportability target-population fabric.
- **Reuse: WHO is the country-level target-population + health-systems covariate layer**; the crosswalk is the single most reusable artifact for cross-source fusion.

### 7d. World Bank  *(corrected — IS on disk)*
- **`F:\WorldBankData`** — **~38 GB, 27,391 files**; fetchers `download_worldbank.py`, `download_fast.py`, `explore_data.py`.
  - `bulk_downloads`: **WDI** (World Development Indicators, `WDICSV.csv` 190 MB), **HNP_Stats** (Health/Nutrition/Population, 60 MB), Gender_Stats (100 MB), EdStats (311 MB), Wealth, QEDS, ADI, Jobs, IDS, ICP.
  - `api_data`: Subnational Malnutrition DB (~70 MB), Education Statistics, Joint External Debt Hub.
- **Reuse: socioeconomic + HNP covariates** (income, GDP, health expenditure, malnutrition, education) for the transportability standardization model; HNP_Stats is the most clinically relevant subset.

**Data-layer summary:** AACT (trials) + IHME (disease burden) + WHO (country health indicators, with the ISO3↔IHME↔WB crosswalk) + World Bank (socioeconomic) = the full target-population covariate fabric the borrowing field needs. **All four are on disk and queryable today.**

---

## 8. Gaps — what the borrowing-field program needs that does NOT exist yet

1. **The coupled "borrowing field" engine itself.** Every piece is siloed: AdaptShrink fuses *estimators within one MA*; GWAM weights *one corpus*; MAPriors borrows *historical→current pairwise*; the `nma/` engine couples *within one network*. **Nothing makes every trial influence every result across the registry graph.** This unifying coupled estimator is net-new.
2. **Transportability-modulated borrowing.** The transportability penalty (TransportabilityCalc / TransportMA / tda-meta) is **not wired into** the borrowing weight (MAPriors / AdaptShrink / GWAM-λ / NMA Component A). Fusing *"how transportable"* → *"how much to borrow"* is the program's novel core and has no implementation.
3. **Commensurate / power priors at registry scale.** MAPriors is pairwise; **`CausalFusion` is an empty stub**. No engine scales commensurate-prior borrowing to thousands of trials.
4. **Dose-response is barely covered.** Only one linear GL DRMA (`dose-response.js`). No spline/non-linear DRMA, **no model-based dose-response NMA**, no borrowing across dose-response curves.
5. **No scalable Bayesian backend in the verified path.** `F:\ubcma\nma` explicitly has no Bayesian backend; `advanced-nma-pooling` has Stan but isn't truth-gated. A registry-scale borrowing field is inherently hierarchical-Bayesian — this seam must be bridged and gated.
6. **Registry pub-bias not run at full AACT scale as the field's live selection layer.** GWAM's λ and Denominator-Calibrated NMA exist but aren't executed against the 14 GB AACT snapshot as a standing selection model feeding the borrowing weights.
7. **The truth gate is single-analysis, not registry-wide.** `matched_coverage_bakeoff.py` validates one MA/NMA; certifying a *registry-wide* borrowing field (and its per-target coverage) needs new harness design.
8. **Data systems not yet fused into a live target layer.** AACT + IHME + WHO + World Bank are on disk, and `who-data-lakehouse/crosswalk.py` provides the ISO3↔IHME↔WB key — but nothing joins them into the live target-population distributions the transport step would standardize toward.

---

## 9. Recommended starting points (build-on, don't reinvent)

- **Kernel:** extend `adaptshrink.py` so its "members" can be *neighbouring trials* weighted by a transportability×selection kernel — the smallest step from existing code to a borrowing field.
- **Modulator:** call `TransportabilityCalc`'s CTE penalty (or `TransportMA`'s IOSW) to set inter-trial borrowing strength; gate with `tda-meta` positivity (never borrow into a hole).
- **Selection:** reuse `GWAM` λ + `CTGovHub`/AACT for the registry pub-bias layer.
- **Geometry:** sit it on the verified `F:\ubcma\nma` engine; borrow `advanced-nma-pooling`'s Stan backend for the Bayesian field.
- **Target data:** join AACT × IHME × WHO × World Bank via `who-data-lakehouse/crosswalk.py`.
- **Acceptance:** every claim through `matched_coverage_bakeoff.py` (G4 gate) + `repro-checker`, per the truth-recovery manifesto.

---
*Read-only survey. `F:\ubcma` is a git repo with a dirty working tree (modified submission files + untracked artifacts), so this catalog is saved but NOT committed.*
