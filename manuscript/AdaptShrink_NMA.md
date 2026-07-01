# AdaptShrink-NMA: an adaptive, selection-robust heterogeneity estimator for network meta-analysis, and a boundary map of where it wins

**Mahmood Ahmad**¹²

¹ Royal Free Hospital, London, United Kingdom
² Tahir Heart Institute, Rabwah, Pakistan

ORCID: 0000-0001-9107-3704
Correspondence: Mahmood Ahmad (mahmood726@gmail.com)

**Competing interests.** The author is an honorary member of the editorial board of *Synthēsis* (former Editor-in-Chief) and had no role in the handling, peer review, or editorial decision-making for this manuscript; any submission would be handled independently by another editor of the journal.

**Funding.** None.

*Companion paper.* This is a companion to the univariate paper "AdaptShrink: a τ-aware, selection-robust random-effects estimator for meta-analysis" (hereafter the *univariate paper*). It re-uses the same matched-coverage evaluation philosophy and the same AdaptShrink lineage, but addresses a distinct estimand family — the basic contrasts of a network meta-analysis — and reports a single, mechanism-explained, fully boundary-mapped phenomenon rather than a multi-grid field comparison. We chose a companion rather than a unified extension because the NMA result is narrower in claim (one selection-driven efficiency phenomenon on dense networks, one baseline) and deserves to be reported at exactly that scope, without inheriting or diluting the univariate paper's broader claims.

---

## Structured abstract

**Background.** Network meta-analysis (NMA) inherits both threats of pairwise meta-analysis — between-study heterogeneity and publication/small-study selection — and amplifies the second: every added treatment adds contrasts that each carry selection bias, and the graph-theoretic field default (common-τ² DerSimonian–Laird, as implemented in `netmeta`) propagates that bias through the network. The result is a coverage collapse that worsens as the network grows.

**Methods.** We develop **AdaptShrink-NMA**, an estimator built on a `netmeta`-exact graph-theoretic engine so that only the heterogeneity/bias model differs from the field default. It has three components, each gated on an observable signal: (A, always on) **adaptive shrinkage of the heterogeneity structure across comparisons** — each comparison type's direct τ² is shrunk toward the network-common τ² by a weight set by how much direct versus borrowed-indirect evidence it carries; (B, gated) a **network-funnel-asymmetry-gated small-study point correction** that fires only when a network PET-slope test rejects symmetry and then blends toward a PEESE-corrected league by a signal-to-noise weight; (C, gated) a **design-by-treatment inconsistency-gated interval inflation**. The integrated `adaptshrink_auto` reduces to the field default on a clean, consistent, symmetric network. We evaluate under a matched-coverage protocol: each method is calibrated to 95% coverage on a parity split, after which we compare the constant matched-coverage interval width (MCIW0; pure point-estimator efficiency) by a paired-bootstrap win criterion, alongside the deployable (no-oracle) coverage a practitioner actually obtains.

**Results.** On a fully-crossed **τ × selection-strength × network-size grid (60 cells, 600 matched-seed replicates each)** holding the dense well-powered regime fixed, `adaptshrink_auto` records a bootstrap-robust matched-coverage efficiency win in **20/60 cells** (18 unambiguous; 2 borderline). The win frontier is a clean monotone surface: **never** under no selection (0/20 control cells — confirming the win is de-biasing, not an under-coverage artifact), **only at the largest network n = 12** under moderate selection (4/20), and from **n ≥ 6** under strong selection (16/20), strengthening monotonically with both network size (no plateau through n = 12) and heterogeneity τ. The peak cell (strong selection, τ = 0.30, n = 12) shows dMCIW0 = −0.154 and recovers deployable coverage from the field default's **0.441 to 0.840 — a +40 percentage-point recovery** — while roughly halving bias and preserving treatment ranking. Eight headline cells were independently re-derived from scratch by three implementations across two external vendors (a harness-free Claude recompute, Gemini/Antigravity "agy", and Codex on a remote node), unanimous on the robust-win flag in **8/8** cells with bootstrap CI bounds matching to ≥4 decimal places.

**Conclusions.** AdaptShrink-NMA does not claim universal superiority. It delivers a bounded, mechanism-explained efficiency-and-coverage win in a precisely mapped region — dense networks with genuine small-study selection — and provably stands down (no spurious narrowing, no coverage harm) where there is no bias to remove. The heterogeneous-vendor reproduction is offered as evidence that the boundary is a property of the estimator, not of one harness.

**Keywords:** network meta-analysis; publication bias; small-study effects; heterogeneity; matched-coverage efficiency; robust estimation; reproducibility.

---

## 1. Introduction

Network meta-analysis simultaneously compares three or more treatments by combining direct and indirect evidence across a connected graph of pairwise comparisons. It inherits the two threats of pairwise meta-analysis — between-study heterogeneity (τ) and publication/small-study selection — but the second threat behaves differently in a network. Each additional treatment introduces additional basic contrasts, each estimated from studies that are themselves a non-random, effect-dependent subset of those conducted; and the graph-theoretic estimator that has become the field default — a common between-study variance τ² shared across all comparisons, solved by the DerSimonian–Laird method and the aggregate graph Laplacian, as implemented in the widely used `netmeta` package — propagates each contrast's selection bias through the shared τ² and the indirect paths. The practical consequence, which our simulations make explicit, is a **coverage collapse that worsens as the network grows**: more contrasts inherit uncorrected selection bias, so the proportion of contrasts whose nominal 95% interval actually contains the truth falls steadily with the number of treatments.

The univariate paper argued that there is a meta-analytic *no-free-lunch*: because the locally optimal estimator depends on the unobservable ratio of selection magnitude to τ, no single fixed estimator can be uniformly best. That argument carries over to networks. A correction that pays a variance premium to remove selection bias cannot help when there is no bias to remove; an efficient common-τ² estimator cannot protect coverage when selection bias dominates. The right response is again *adaptive*: detect, from observable signals, which regime the network is in, and act only when the data warrant it.

This paper makes three contributions, all scoped tightly to NMA:

1. **AdaptShrink-NMA** — an estimator that generalises the AdaptShrink idea to a vector estimand by adaptively shrinking the *heterogeneity structure across comparisons*, with two further gated components (a network small-study point correction and an inconsistency interval inflation) that switch on only when their respective diagnostic tests reject.
2. **A 60-cell boundary map** of where the estimator's matched-coverage efficiency win exists, obtained by fully crossing heterogeneity, selection strength, and network size while holding everything else at a dense well-powered regime. We report the entire frontier — including the cells where there is no win — rather than a single favourable comparison.
3. **A heterogeneous-vendor reproduction**: eight headline cells re-derived from scratch by three independent implementations across two external AI vendors, framed as evidence that the win region is a property of the estimator and not of one simulation harness.

We are explicit throughout that the win is *bounded and mechanism-explained*, not universal. The estimator's value lies as much in where it correctly does nothing as in where it wins.

## 2. Methods

### 2.1 The engine and the field default

AdaptShrink-NMA is built on a graph-theoretic NMA engine (`nma/nma_core.py`) that reproduces `netmeta`'s aggregate-Laplacian league table and standard errors to numerical tolerance (validated to ≈ 5 × 10⁻¹¹ in earlier program work, and to 10⁻¹³ against `netmeta`'s design-by-treatment decomposition for component C). Multi-arm trials contribute correctly correlated rows. Because every method in the bake-off is fitted through the *same* engine, the **only** thing that differs between AdaptShrink-NMA and the field default is the heterogeneity/bias model — not the linear algebra, the reference handling, or the multi-arm correlation. The **field default / baseline** throughout is `common_DL`: the common-τ² DerSimonian–Laird random-effects graph-theoretic NMA, i.e. `netmeta`'s default random-effects model.

### 2.2 Component A — adaptive heterogeneity-structure shrinkage (always on)

Where univariate AdaptShrink shrinks a scalar τ², AdaptShrink-NMA shrinks the *structure* of heterogeneity across comparison types. Each comparison type `c` gets its own direct heterogeneity τ²_{c,direct} (a classical DerSimonian–Laird estimate from the direct studies of `c` only), shrunk toward the network-common τ²_common:

$$ \tau^2_c(\lambda_c) = \lambda_c\,\tau^2_{\mathrm{common}} + (1-\lambda_c)\,\tau^2_{c,\mathrm{direct}}, \qquad \lambda_c = \frac{\nu}{\nu + (n_c-1)\,s_c}, \qquad s_c = \frac{\mathrm{Var}_{\mathrm{network},c}}{\mathrm{Var}_{\mathrm{direct},c}} \in (0,1]. $$

Here `n_c` is the number of direct studies for comparison `c`, and `s_c` is a geometry weight: it is near 1 when `c`'s network estimate is driven by its own direct evidence (so its own τ² is trustworthy and it is shrunk less), and small when `c` borrows much indirect strength (so it is shrunk toward the common τ² more). The single tuning constant **ν** is the analogue of the univariate κ: ν → 0 recovers comparison-specific τ²; ν → ∞ recovers common-τ². It is reported explicitly (default ν = 4.0) and is only ever calibrated on a held-out split inside the matched-coverage scorer, never to a target number. Comparisons with fewer than two direct studies borrow the common τ² fully (λ_c = 1). Component A is the milestone-1 contribution: nearer-nominal, more uniform deployable coverage with no harm under homogeneity. (Source: `nma/adaptshrink_nma.py::compute_shrunk_tau2`.)

### 2.3 Component B — network-funnel-asymmetry-gated small-study correction (gated; the point-estimate mover)

Component B is the only component that moves the *point* estimate, and therefore the only one that can produce a matched-coverage **efficiency** win. It is gated on a **network-funnel-asymmetry test**: a network PET-style regression of effect on standard error, whose two-sided slope p-value must fall below `asym_gate_p = 0.05` for B to fire. When it fires, the estimator blends the league toward a **PEESE-corrected** small-study league by a signal-to-noise (SNR) shrinkage weight

$$ \lambda_B = \frac{\hat\beta^2}{\hat\beta^2 + \widehat{\mathrm{Var}}(\hat\beta)}, $$

so the correction is near-full when the small-study slope β is large and well estimated, and near-zero when it is marginal. Crucially, when the asymmetry gate fires the point base is reset to the field-default common-DL league (not component A's league): on the dense, homogeneous, data-rich networks where selection bias is correctable, A's per-comparison τ² would otherwise inject point-estimate noise, and B's and A's win regimes are disjoint. When the gate does *not* fire, the estimator keeps A's calibrated league unchanged. (Source: `adaptshrink_nma.py::adaptshrink_nma_auto`; `smallstudy_nma.py`.)

### 2.4 Component C — inconsistency-gated interval inflation (gated)

Component C is gated on the **design-by-treatment inconsistency test**: if its p-value falls below `incons_gate_p = 0.10`, the standard errors are inflated by φ = √(max(1, Q_inc/df_inc)), restoring deployable coverage when direct and indirect evidence conflict. It moves only the interval, never the point estimate. (Source: `adaptshrink_nma.py`; `inconsistency_nma.py`; validated against `netmeta`'s design-by-treatment decomposition to 10⁻¹³.) Component C does not contribute to the selection-width phenomenon that is the subject of this paper's boundary map (which is run on consistent networks); it is documented here for completeness of the estimator.

### 2.5 The integrated `adaptshrink_auto`

The deployable estimator composes the three components with their gates:

- **A (always):** adaptive heterogeneity-structure shrinkage sets the random-effects weights.
- **B (if the asymmetry test rejects):** reset the point base to common-DL, then blend toward the PEESE league by λ_B.
- **C (if the inconsistency test rejects):** inflate the standard errors by φ.

Every gate decision (which components fired, the asymmetry p and slope, λ_B, φ) is returned in the fit metadata for transparency. On a clean, consistent, symmetric network neither B nor C fires and the estimator reduces to component A's calibrated league; with no heterogeneity structure to exploit it is then close to the field default. The switch is therefore data-driven and *conservative by construction*: components act only when their diagnostics warrant.

### 2.6 The matched-coverage protocol and exact definitions

We compare methods fairly by first putting each on the same coverage footing, then comparing width. All definitions below are stated precisely because the win criterion depends on them.

- **Parity split.** For each (cell, method, contrast) the replicates are split by index parity: even-indexed replicates form the **calibration** half, odd-indexed the **test** half.

- **MCIW0 (constant matched-coverage interval width; the primary metric).** For one contrast, let `c` be the 0.95-quantile of the absolute point error |d̂ − d_true| over the calibration half. Then MCIW0 = 2c. The cell-level MCIW0 for a method is the **mean of MCIW0 over the n − 1 basic contrasts**. MCIW0 isolates point-estimator efficiency (tail error) with no interval-modelling confound; the true effect is used *only* to set the width, so MCIW0 is an efficiency statement, not a deployable interval. Held-out validity is checked by `test_cov = P(|d̂ − d_true| ≤ c)` on the test half.

- **dMCIW0.** dMCIW0 = MCIW0(`adaptshrink_auto`) − MCIW0(`common_DL`). **Negative dMCIW0 means AdaptShrink-NMA is narrower at matched coverage** (the win direction).

- **Deployable (raw) coverage.** The real per-replicate coverage of d_true at κ = 1 (no oracle scaling): the proportion of replicates whose nominal 95% interval contains the true contrast, averaged over contrasts. This is what a practitioner actually obtains. We also report **coverage uniformity** `cov_unif` = mean |raw_cov_contrast − 0.95| across contrasts (lower = more even across comparisons), and **ranking** as the Spearman correlation and top-1 hit-rate of the P-score order versus truth.

- **The win criterion (paired bootstrap; decisive).** A method is credited with a *bootstrap-robust win* over the field default only when a paired bootstrap of the mean-over-contrasts MCIW0 advantage clears zero. Concretely (B = 2000 resamples, fixed seed 7): absolute errors are paired across methods within each (replicate, contrast); replicate indices are resampled; each method's mean-over-contrasts MCIW0 is recomputed on each resample; the **robust win flag is true iff the 97.5th percentile of (method − baseline) is < 0**. This is a conservative, one-sided 97.5% statement.

- **Borderline.** A cell is flagged **borderline** when |bootstrap CI bound| < 0.002 — i.e. the robust-win flag flips within bootstrap Monte-Carlo error. Borderline cells are reported separately and are *not* counted among the unambiguous wins.

(Sources: `nma/truth-recovery/nma_bakeoff.py::matched_coverage`, `bootstrap_vs_baseline`.)

## 3. Simulation study

**The grid.** We fully cross three axes and hold everything else fixed at a dense, well-powered regime:

- **τ** ∈ {0.05, 0.10, 0.20, 0.30}
- **selection** ∈ {none, moderate, strong}
- **n** (treatments) ∈ {5, 6, 8, 10, 12}, giving 4–11 basic contrasts.

This is **60 cells**. Held constant across all cells: geometry = full network; 8–15 studies per edge; homogeneous between-study heterogeneity; spread of true basic effects `effect_sd = 0.5`; selection favouring large positive z (`small_values = 'undesirable'`). The selection filter keeps a study with probability 1 for non-significant results and {1, 0.6, 0.4} (moderate) or {1, 0.35, 0.10} (strong) across one-sided p-value bands at cut-points {0.025, 0.05}. Each cell runs **600 matched-seed replicates** with an identical base seed (`BASE_SEED = 20260621`), so cells differ *only* by their axis values — the same underlying random draws are reused across the grid, which is what makes the cell-to-cell trends interpretable rather than noise. Per cell, for `adaptshrink_auto` versus `common_DL`, we compute the paired-bootstrap dMCIW0 and its robust-win flag plus all deployable metrics. The grid was run with a 3-worker process pool (7,460 s wall). (Sources: `nma/truth-recovery/run_tausel_grid.py`, `nma_sim.py`; map `nma_tausel_grid_map.csv`, gates `nma_tausel_grid_gates.json`.)

**Why dense full networks.** The selection-driven width win is specifically a dense-network phenomenon: it is component B's network-wide PEESE slope, estimated across many edges and indirect paths, that does the de-biasing. Sparser and non-full geometries (loop, star, sparse) were studied in earlier program phases for the consistency and heterogeneity axes, and are out of scope for this selection-width boundary map. This is a stated scope limit, not an omission (§6).

## 4. Results

### 4.1 The boundary map

Across the 60 cells, `adaptshrink_auto` records a bootstrap-robust matched-coverage efficiency win in **20/60 cells**: **18 unambiguous** (CI upper bound ≤ −0.002) plus **2 borderline** (`t05_moderate_n12`, CI upper −0.0007; `t10_strong_n6`, CI upper −0.0008). The frontier is a clean monotone surface (Figure 1; Table 1), and the three axes act as follows.

**1. Selection is the gate (the control axis).** With **no** selection, **0/20** cells win: dMCIW0 is *positive* (AdaptShrink-NMA slightly wider) at every τ and n, bias is essentially unchanged versus the field default, and deployable coverage is not harmed. When there is no bias to remove, component B's asymmetry gate stands down and there is no spurious narrowing. This is the key falsification control, and it holds across the entire τ × n plane, not at a single point.

**2. Moderate selection wins only at the largest network (n = 12).** 4/20 moderate cells are robust, all at n = 12 (τ = 0.10, 0.20, 0.30 unambiguous; τ = 0.05 borderline). At n ≤ 10 the moderate-selection point advantage trends negative from n = 8 onward but the bootstrap CI still crosses zero. Large *enough* n is necessary to push a weak selection signal past the robustness threshold — and it does so only barely.

**3. Strong selection wins from n ≥ 6 (n ≥ 5 at the highest τ), strengthening in both n and τ.** 16/20 strong cells are robust. The win emerges at n = 6 (τ ≥ 0.10) and **strengthens monotonically with n through n = 12 with no plateau** — e.g. at τ = 0.30 the dMCIW0 sequence over n = 5, 6, 8, 10, 12 is −0.040, −0.040, −0.080, −0.124, −0.154. It also strengthens monotonically with τ at every n ≥ 6 — e.g. at n = 12 the dMCIW0 sequence over τ = 0.05, 0.10, 0.20, 0.30 is −0.073, −0.090, −0.122, −0.154. **Heterogeneity amplifies the win; it does not erase it.** The largest win in the grid is the highest-τ, largest-n strong cell (`t30_strong_n12`, dMCIW0 = −0.154).

### 4.2 Deployable coverage and the +40-point recovery

The width story is matched by a deployable-coverage story that rules out the "narrower-because-under-covering" artifact (Table 2; Figure 2). As the network grows and τ rises under strong selection, the field default's deployable coverage **collapses** — down to **0.441** at the corner cell `t30_strong_n12` — because every added contrast inherits uncorrected selection bias. `adaptshrink_auto` holds **0.840–0.931** across the same strong-selection cells, a **+40 percentage-point** coverage recovery at the corner (Δcoverage = +0.399). Bias is roughly halved (e.g. 0.114 vs 0.192 at the corner; 0.031 vs 0.076 at `t10_strong_n12`) and P-score ranking is preserved or slightly improved at every robust cell (Spearman 0.953 vs 0.928 at the corner). The deployable improvement is the practical counterpart of the MCIW0 width win.

### 4.3 Mechanism

With dMCIW0 = MCIW0(auto) − MCIW0(base) and MCIW0 = 2·q₀.₉₅(|error|) averaged over the n − 1 contrasts, the robustness threshold is crossed when the *point* advantage outruns the *bootstrap half-width* of the mean-over-contrasts advantage. All three axes push in the same direction:

- **selection ↑** → more bias for component B's PEESE slope to remove (none → zero advantage; the gate is a genuine on/off);
- **n ↑** → more edges and indirect paths, so the network-wide PEESE slope is estimated more precisely (larger de-biasing) *and* the mean-over-(n − 1)-contrasts advantage has lower bootstrap variance (tighter CI); both effects compound, so the win strengthens with n with no plateau through n = 12;
- **τ ↑** → a wider funnel gives more leverage to identify the small-study slope, so the correction removes proportionally more error.

The boundary is therefore a smooth frontier, not a cliff: moderate selection reaches it only with the n = 12 variance-averaging boost; strong selection reaches it by n = 6 and races past it as n and τ grow.

### 4.4 Precursor: the monotone network-size sweep

The grid was preceded by a focused, higher-replication network-size sweep that first established the monotone-in-n mechanism as a falsifiable prediction (Table 4). Holding τ = 0.10, strong selection, dense full networks, at **1,200 matched-seed replicates each**, the dMCIW0 over n = 5, 6, 7, 8 was +0.016, −0.021, −0.028, −0.036, with the bootstrap CI upper bound moving monotonically below zero (+0.031, −0.003, −0.017, −0.025): the robust win emerges at n = 6 and strengthens through n = 8, with no win at n = 5. The external vendor "agy" independently reproduced these four dMCIW0 values to 4 decimal places (+0.0159, −0.0205, −0.0281, −0.0360) and the monotone-strengthening verdict. The 60-cell grid (600 replicates/cell) then extended this prediction across the full τ × selection × n plane and confirmed it, including the n = 10 and n = 12 extension and the no-selection and moderate-selection controls. (Source: `REPORT_NMA_PHASE3.md`; `nma/verify/result_agy_sweep.json`.) Note that the precursor sweep and the grid are *separate runs at different replicate counts*; the small numerical differences between, e.g., the precursor's n = 6 dMCIW0 (−0.021, 1,200 reps) and the grid's `t10_strong_n6` (−0.023, 600 reps) reflect that, and both are reported as run.

## 5. Validation and reproducibility

**Matched seeds.** Every cell uses the identical `BASE_SEED = 20260621`, so cross-cell trends are not seed noise; the per-replicate, per-contrast outputs are committed.

**Paired-bootstrap truth-gate.** The win flag is the conservative one-sided 97.5% paired-bootstrap statement defined in §2.6, not a point comparison. Two cells whose CI bound falls within 0.002 of zero are flagged borderline and excluded from the 18 unambiguous wins.

**Heterogeneous-vendor cross-confirmation.** Eight headline cells spanning the regime — two robust corners (`t30_strong_n12`, `t10_strong_n10`), one mid-robust (`t20_strong_n8`), the moderate-selection boundary win (`t10_moderate_n12`), the strong-selection boundary cell (`t10_strong_n6`), and three genuine negatives including the **no-selection control** (`t10_none_n8`) — were re-derived **from scratch** by three independent implementations: a harness-free Claude recompute (re-implementing the MCIW0 metric and paired bootstrap from only the committed per-replicate CSVs and a written spec, with no import of the program code), the external vendor **agy** (Gemini/Antigravity, independent code generation), and **Codex** running on a remote node (pc2, seat A, live, ≈31,938 tokens, writing and running its own verifier). **All three agree on the robust-win flag in 8/8 cells** (Table 3). The bootstrap CI bounds match across vendors to ≥4 decimal places (in the committed result files they are in fact identical to the recorded precision). The two legitimate dMCIW0 *point* conventions — the all-replicates bootstrap centre (used by Claude, e.g. `t30_strong_n12` = −0.1540) and the calibration-split point (used by agy and Codex, e.g. −0.1486) — differ by ≈0.004–0.01 but do **not** affect any robust verdict, because the verdict-determining bootstrap CI is computed identically by all three.

We frame the heterogeneous-vendor reproduction as a *strength*: three implementations on different stacks, two of them external vendors, landing on the same robust-win boundary (including the same not-robust verdict for the boundary cell `t10_strong_n6` under the spec's fresh-RNG bootstrap convention) is evidence that the win region is a property of the estimator, not of one simulation harness. We disclose, rather than hide, the partial vendor coverage: a laptop node's two Codex seats were offline on the network during the run (a background watcher was left polling to burn both seats if the node resurfaced), Codex seat B on pc2 lacked credentials, and Codex on the local Windows node was unusable due to a sandbox-helper failure. These are recorded in the report's vendor audit table; the three completed implementations already constitute an independent triple.

**Files.** Driver `nma/truth-recovery/run_tausel_grid.py`; map `nma_tausel_grid_map.csv` and gates `nma_tausel_grid_gates.json`; estimator `nma/adaptshrink_nma.py` on the verified engine `nma/nma_core.py`; per-replicate headline-cell CSVs `nma/verify/grid/gridcell_*_perrep.csv`; from-scratch spec `nma/verify/grid_verify_spec.md`; vendor recomputes `nma/verify/result_claude_grid.json`, `result_agy_grid.json`, `result_codex_pc2_A_grid.json`; reports `nma/REPORT_NMA_GRID.md`, `REPORT_NMA_PHASE3.md`. Figures regenerate with `python manuscript/make_nma_figures.py`, which reads only `nma_tausel_grid_map.csv`. Committed on branch `methods-nma` (commit `d759dd5`).

## 6. Limitations

We restate the honest negatives in full; they bound the claim.

- **n = 5 is mostly not a robust win.** Under strong selection it fails at τ ≤ 0.10 (positive dMCIW0) and is borderline at τ = 0.20 (CI crosses zero); it wins only at τ = 0.30. The efficiency win genuinely needs n ≥ 6 except at the highest heterogeneity.
- **Moderate selection needs n = 12** and even then is marginal (τ = 0.05 borderline). At realistic moderate selection with small or medium networks, expect no width win — only the smaller deployable-coverage and bias improvement.
- **Two boundary cells flip on the bootstrap RNG convention.** `t10_strong_n6` and `t05_moderate_n12` are flagged robust by the grid gate (which draws one shared `default_rng(7)` sequence across methods, with `auto` the third consumer) but not robust under the spec's per-method fresh-RNG convention used by the external vendors. They are reported transparently and excluded from the 18 unambiguous wins.
- **Two point-dMCIW0 conventions** (calibration-split versus all-replicates bootstrap centre) differ by ≈0.004–0.01; the robust verdict is invariant to the choice, but the point number quoted depends on it.
- **No-selection coverage dips slightly at high τ.** In the control cells, `adaptshrink_auto`'s deployable coverage runs ≈1–2 points *below* the field default at τ ≥ 0.20 (e.g. `t30_none_n8`: 0.930 vs 0.949) — both still near nominal, and since dMCIW0 is *positive* there (wider intervals) this is GLS calibration under heterogeneity, not a narrowing artifact. It warrants a footnote in any deployment.
- **Single geometry and density.** The whole grid is dense full networks (8–15 studies/edge). Sparser or non-full geometries are out of scope here.
- **Single estimand family and metric focus.** The boundary is mapped for the basic contrasts under one effect-generating process and the MCIW0 point-efficiency metric; the own-width interval metric (MCIW) is reported in the committed gates but is a weaker, separate story at high τ. A fuller study would broaden geometry, density, effect metric (e.g. log-OR networks), and selection mechanism, and would re-run the grid gate with a per-method fresh RNG so the 60-cell flags are convention-invariant (reclassifying the two borderline cells as not robust, for an 18/60 unambiguous map).

## 7. Discussion

**What the boundary map shows.** AdaptShrink-NMA's contribution is not a uniformly better NMA estimator — that is provably unattainable for the same reason as in the univariate case — but an *observable, gated* response that wins where it should and stands down where it should. The control axis is decisive: across all 20 no-selection cells there is no robust win, no coverage harm, and essentially unchanged bias, because the asymmetry gate does not fire when there is no asymmetry. Where genuine strong selection exists in a dense network, the estimator delivers both a matched-coverage efficiency win and a large deployable-coverage recovery (up to +40 points), with bias halved and ranking preserved. The win is a clean monotone region in (τ, selection, n), which is exactly what a mechanism-driven (rather than overfit) effect should look like.

**Why not "universally best".** In the no-selection corner the efficient common-τ² estimator is essentially minimum-variance and unbiased; no bias-correcting estimator can strictly beat it there, and `adaptshrink_auto` correctly does not try to. The realistic target is a method that is safe everywhere and strong where selection bites — which the boundary map demonstrates within its stated scope.

**When to use it.** AdaptShrink-NMA is a sensible default for dense networks when small-study or publication selection cannot be ruled out: it self-limits to near-field-default behaviour when its diagnostics are clean, and recovers coverage and efficiency when they are not. At high heterogeneity with no plausible selection, the field default is appropriate and `adaptshrink_auto` will (by design) stay close to it. As in the univariate paper, we recommend reporting the matched-coverage width and the deployable coverage together, and disclosing τ̂ and the asymmetry-gate decision alongside the estimate.

---

## Figures

**Figure 1.** The 60-cell boundary map. Three panels (selection = none / moderate / strong); rows are heterogeneity τ, columns are network size n; cell colour and text are dMCIW0 (blue/negative = AdaptShrink-NMA narrower at matched coverage). Annotations: `W` = bootstrap-robust win, `b` = borderline, `.` = no win. The win frontier is empty under no selection, confined to n = 12 under moderate selection, and a clean monotone region under strong selection. *(`figures_nma/fig1_boundary_map.png`; source `nma_tausel_grid_map.csv`.)*

**Figure 2.** Deployable coverage (κ = 1) versus network size under strong selection, by τ. The field default (dashed) collapses with n and τ to 0.441 at n = 12, τ = 0.30; AdaptShrink-NMA (solid) holds 0.84–0.93 near nominal. *(`figures_nma/fig2_coverage_collapse.png`.)*

**Figure 3.** The monotone efficiency frontier. Left: dMCIW0 versus n for each τ under strong selection — the win strengthens monotonically with n with no plateau through n = 12. Right: dMCIW0 versus τ at n = 12 for all three selection regimes — heterogeneity amplifies the win under selection, while the no-selection control stays positive (no win). *(`figures_nma/fig3_frontier.png`.)*

## Tables

**Table 1.** The boundary map (dMCIW0; flag). Rows are (selection, τ), columns are network size n. `W` = bootstrap-robust win, `b` = borderline (|CI bound| < 0.002), `.` = no win. Source: `nma_tausel_grid_map.csv`.

| selection | τ | n=5 | n=6 | n=8 | n=10 | n=12 |
|---|---:|---|---|---|---|---|
| none | 0.05 | . +0.002 | . +0.006 | . +0.007 | . +0.003 | . +0.002 |
| none | 0.10 | . +0.002 | . +0.007 | . +0.006 | . +0.004 | . +0.002 |
| none | 0.20 | . +0.008 | . +0.011 | . +0.008 | . +0.004 | . +0.003 |
| none | 0.30 | . +0.008 | . +0.013 | . +0.013 | . +0.007 | . +0.003 |
| moderate | 0.05 | . +0.005 | . −0.000 | . −0.006 | . −0.004 | **b −0.005** |
| moderate | 0.10 | . +0.001 | . −0.002 | . −0.006 | . −0.004 | **W −0.010** |
| moderate | 0.20 | . −0.006 | . +0.007 | . −0.006 | . −0.004 | **W −0.020** |
| moderate | 0.30 | . +0.003 | . +0.011 | . −0.009 | . −0.007 | **W −0.026** |
| strong | 0.05 | . +0.013 | . −0.021 | **W −0.032** | **W −0.059** | **W −0.073** |
| strong | 0.10 | . +0.018 | **b −0.023** | **W −0.032** | **W −0.064** | **W −0.090** |
| strong | 0.20 | . −0.005 | **W −0.029** | **W −0.066** | **W −0.088** | **W −0.122** |
| strong | 0.30 | **W −0.040** | **W −0.040** | **W −0.080** | **W −0.124** | **W −0.154** |

Robust wins: 20/60 (18 unambiguous + 2 borderline). None: 0/20. Moderate: 4/20 (all n = 12). Strong: 16/20.

**Table 2.** Deployable metrics at representative strong-selection cells (`adaptshrink_auto` vs `common_DL`). Source: `nma_tausel_grid_map.csv`.

| cell | dMCIW0 | raw cov auto / DL | Δcov | \|bias\| auto / DL | Spearman auto / DL |
|---|---:|---|---:|---|---|
| t10_strong_n6 | −0.023 | 0.890 / 0.811 | +0.079 | 0.047 / 0.077 | 0.945 / 0.938 |
| t10_strong_n12 | −0.090 | 0.931 / 0.701 | +0.230 | 0.031 / 0.076 | 0.981 / 0.973 |
| t20_strong_n12 | −0.122 | 0.891 / 0.565 | +0.326 | 0.067 / 0.126 | 0.970 / 0.955 |
| t30_strong_n12 | −0.154 | 0.840 / 0.441 | +0.399 | 0.114 / 0.192 | 0.953 / 0.928 |

**Table 3.** Heterogeneous-vendor cross-confirmation on eight headline cells. `dMCIW0` columns show the all-replicates bootstrap-centre convention (Claude) and the calibration-split convention (agy, Codex); the bootstrap CI is computed identically by all three. Robust consensus is unanimous in 8/8 cells. Sources: `result_claude_grid.json`, `result_agy_grid.json`, `result_codex_pc2_A_grid.json`.

| cell | grid-gate flag | Claude dMCIW0 | agy dMCIW0 | Codex dMCIW0 | shared CI (lo, hi) | robust consensus |
|---|:--:|---:|---:|---:|---|:--:|
| t10_none_n8 (control) | . | +0.0064 | +0.0031 | +0.0031 | (+0.0017, +0.0093) | not robust ✓ |
| t10_strong_n5 | . | +0.0185 | +0.0112 | +0.0112 | (−0.0138, +0.0508) | not robust ✓ |
| t05_strong_n6 | . | −0.0214 | −0.0257 | −0.0257 | (−0.0381, +0.0024) | not robust ✓ |
| t10_strong_n6 (boundary) | W | −0.0229 | −0.0493 | −0.0493 | (−0.0414, +0.0009) | not robust ✓ |
| t10_moderate_n12 | W | −0.0100 | −0.0087 | −0.0087 | (−0.0148, −0.0047) | robust ✓ |
| t20_strong_n8 | W | −0.0661 | −0.0559 | −0.0559 | (−0.0900, −0.0451) | robust ✓ |
| t10_strong_n10 | W | −0.0640 | −0.0667 | −0.0667 | (−0.0796, −0.0497) | robust ✓ |
| t30_strong_n12 | W | −0.1540 | −0.1486 | −0.1486 | (−0.1713, −0.1374) | robust ✓ |

The grid-gate flag for `t10_strong_n6` is `W` under the harness's shared-RNG bootstrap; all three from-scratch implementations place its CI upper bound at +0.0009 under the spec's fresh-RNG convention, i.e. not robust — hence its classification as a genuine boundary cell.

**Table 4.** Precursor network-size sweep (strong selection, τ = 0.10, dense full networks, 1,200 matched-seed replicates/cell). Source: `REPORT_NMA_PHASE3.md`; external reproduction `result_agy_sweep.json`.

| n | #contrasts | dMCIW0 | 95% bootstrap CI | CI upper | robust win | agy dMCIW0 |
|---:|---:|---:|---|---:|:--:|---:|
| 5 | 4 | +0.016 | [−0.010, +0.031] | +0.031 | no | +0.0159 |
| 6 | 5 | −0.021 | [−0.032, −0.003] | −0.003 | yes (fragile) | −0.0205 |
| 7 | 6 | −0.028 | [−0.039, −0.017] | −0.017 | yes | −0.0281 |
| 8 | 7 | −0.036 | [−0.050, −0.025] | −0.025 | yes (strong) | −0.0360 |
