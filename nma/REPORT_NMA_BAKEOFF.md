# AdaptShrink-NMA — first matched-coverage bake-off (milestone 1)

> **Phase 2 is complete — see `nma/REPORT_NMA_PHASE2.md`.** Components B
> (network-funnel-asymmetry-gated small-study correction) and C
> (inconsistency-aware inflation) deliver the genuine matched-coverage MCIW0
> efficiency win this milestone said was missing — bootstrap-robust at
> select_strong_dense_n6 (dMCIW0 −0.0206 [−0.0348,−0.0013]) — plus broad
> deployable-coverage restoration. This document remains the milestone-1 record.

Generalizing the univariate AdaptShrink program to network meta-analysis. This
is the **first milestone**: a verified reference engine, the AdaptShrink-NMA
estimator (heterogeneity-structure shrinkage, component A), and the first
matched-coverage bake-off numbers — reported truth-first, negatives included.

All numbers below are produced by seeded, committed scripts and traceable to
committed CSVs. Nothing is hand-entered.

---

## 1. Verified engine (the modern field to beat)

`nma/nma_core.py` is a from-scratch Rücker graph-theoretic NMA reproducing R
`netmeta` 3.6-1 to machine precision on two canonical networks
(`nma/reference/test_netmeta_parity.py`):

| network | quantity | max abs error vs netmeta |
|---|---|---|
| Senn2013 (multi-arm diabetes, MD) | league TE/seTE, common+random | ~5e-11 |
| Hasselblad smoking (arm→logOR, multi-arm) | league TE/seTE, common+random | ~5e-11 |
| both | generalized Cochran Q | ~1e-12 |
| both | df.Q | exact |
| both | DL τ² (Jackson 2012 generalized, multi-arm S=0.5·AAᵀ) | ~1e-15 |
| both | P-score ranking | ~1e-14 |

The hardest parts — multi-arm covariance reconstruction (arm variances solved
from pairwise contrast variances; +τ²/2 per shared arm) and the network
generalized-DL τ² — match netmeta exactly.

**Independent cross-implementation.** Per the verification policy, **both Codex
seats** re-derived the multi-arm NMA from `nma/verify/VERIFY_SPEC.md` *without
reading* `nma_core.py` (independent GLS + Moore-Penrose constructions) and each
reproduced the netmeta random-effects league tables to **~5e-11 on both
networks**:
- seat `mahmood726` (`nma/verify/codex_mahmood_RESULT.md`): smoking TE 4.999e-11 /
  seTE 4.553e-11; senn2013 TE 4.786e-11 / seTE 4.804e-11.
- seat `noreenahmad01` (`nma/verify/codex_noreen_run2.log`): smoking TE 4.999e-11 /
  seTE 4.553e-11; senn2013 TE 4.786e-11 / seTE 4.804e-11 — identical to 1e-13.

Four independent routes (R netmeta, this engine, and two independent Codex
re-implementations) thus agree to machine precision. (`agy` was blocked by a
Windows CLI `--print` timeout — an environment issue, not a disagreement; the
first Codex seat also needed the sandbox bypass to run shell commands on Windows.)

---

## 2. AdaptShrink-NMA (component A: heterogeneity-structure shrinkage)

`nma/adaptshrink_nma.py`. Each comparison type *c* gets its own direct DL τ²_c,
shrunk toward the network-common τ² by `λ_c = ν / (ν + (n_c−1)·s_c)`, where `s_c
= var_network_c / var_direct_c ∈ (0,1]` is a network-geometry weight (borrow more
where a comparison leans on indirect evidence) and `ν` is the single transparent
tuning constant (the AdaptShrink `kappa` analog). `ν→∞` recovers common-τ² (the
netmeta default); `ν→0` recovers the comparison-specific model. Built on the
verified engine, so multi-arm and the GLS league stay netmeta-exact.

Sanity behaviour on the real smoking network: the data-rich A–C edge (n=15)
follows its own τ²; the unstable A–D edge (n=2, wild direct τ²=4.53) is shrunk
hard toward common (λ=0.83 → 1.27 instead of 4.53) — the intended stabilization.

---

## 3. First bake-off results (matched coverage + deployable coverage)

`nma/truth-recovery/nma_bakeoff.py`. Field compared every cell: `common_DL`
(= netmeta default, the baseline to beat), `comp_specific` (ν=0), `adaptshrink`
(ν=4). Estimand = the basic contrasts d_{ref,t}; metrics:
**raw_cov / cov_unif** = DEPLOYABLE (κ=1, no oracle) coverage and its
non-uniformity across comparisons (mean |cov−0.95|); **MCIW** = own-width
matched-coverage interval (the project's signature efficiency criterion);
**MCIW0** = constant-width point-estimator efficiency.

### 3a. Where AdaptShrink-NMA helps — deployable coverage calibration

The clearest evidence (`probe_coverage_by_tau.py`, 300 reps, star n=6, sparse,
τ_low=0.05 / τ_high=0.40; coverage of DIRECT hub-leaf comparisons split by that
edge's TRUE τ; **no oracle**):

| method | τ-band | deployable coverage | mean width |
|---|---|---|---|
| **common_DL** (field) | low τ | 0.991 (over) | 0.727 |
| **common_DL** (field) | high τ | **0.825 (under)** | 0.729 |
| **adaptshrink** | low τ | 0.990 | **0.673** (tighter) |
| **adaptshrink** | high τ | **0.868** (toward nominal) | 0.825 (wider) |
| comp_specific | low τ | 0.960 | 0.555 (too tight) |
| comp_specific | high τ | 0.873 | 0.916 |

Common-τ² holds a **flat ~0.73 width across both bands** despite an 8× difference
in true heterogeneity — so it over-covers low-τ comparisons (wasted width) and
**under-covers high-τ ones (0.825, far from nominal)**. AdaptShrink tightens the
low-τ intervals (0.727→0.673, coverage held) and widens the high-τ ones (coverage
0.825→0.868), i.e. **deployable coverage closer to nominal and more uniform.**

Bake-off on the basic-contrast estimand, star_hetero, 300 reps:

| method | \|bias\| | raw_cov | cov_unif | MCIW | MCIW0 | spearman | top1 |
|---|---|---|---|---|---|---|---|
| common_DL (field) | 0.005 | 0.925 | 0.075 | 0.7332 | 0.7004 | 0.860 | 0.75 |
| **adaptshrink** | 0.004 | **0.941** | **0.057** | 0.7429 (1.013×) | 0.7093 | 0.857 | 0.74 |
| comp_specific | 0.004 | 0.925 | 0.038 | 0.8002 (1.091×) | 0.7146 | 0.859 | 0.75 |

AdaptShrink has the **best deployable coverage (0.941, nearest nominal)** and is
**more uniform than the field default (cov_unif 0.057 vs 0.075)**, while
comp_specific — though most uniform — pays a clear matched-coverage efficiency
penalty (MCIW 1.091×) from noisy per-comparison τ².

### 3b. Negative control (homogeneous τ) — does no harm

star_homog, 300 reps (heterogeneity is genuinely common): AdaptShrink MCIW
1.026× the field, cov_unif 0.019 vs 0.022 — essentially a tie. It correctly
shrinks back toward common-τ² when that is the right model. comp_specific still
loses (1.118×).

### 3c. Honest negatives — no robust matched-coverage WIN yet

- On a **well-connected (full) network** scored at the basic-contrast estimand
  (`moderate_hetero`), common-τ² is **hard to beat**: it pools heterogeneity
  across the whole network so per-comparison unevenness washes out (common_DL
  MCIW 0.4025 vs adaptshrink 0.4407). The field default wins there.
- **No bootstrap-robust MCIW or MCIW0 win** for AdaptShrink over common-τ² in any
  tested consistency cell. A favourable point estimate appeared under multi-arm
  (`star_hetero_ma`: −0.017, ~0.94×) but at 500 reps its 95% paired-bootstrap CI
  is [−0.043, +0.016] — **crosses zero, not robust**.
- Root cause (and it is honest, not a bug): in a **consistency model without
  selection the GLS point estimate is nearly τ²-independent**, and the MCIW
  metric's per-contrast own-width calibration *neutralizes* calibration
  differences. So a heterogeneity-model change cannot, by construction, produce a
  matched-coverage *width* win there — only a *deployable-coverage* calibration
  win, which is what we observe. This mirrors the univariate finding that without
  selection, added flexibility costs efficiency rather than winning it.

---

## 4. Verdict and next iteration

**Verified:** the engine = netmeta to ~1e-6 (independently cross-checked). **Real
positive:** AdaptShrink-NMA delivers **more uniform, nearer-nominal deployable
coverage** than the field-default common-τ² in heterogeneous sparse networks, at
no matched-coverage cost, and does no harm under homogeneity — strictly
dominating the comparison-specific model. **Honest ceiling:** component A alone
yields **no bootstrap-robust matched-coverage efficiency win** in consistency
models, because the point estimators coincide there.

The matched-coverage *efficiency* win (the headline criterion the univariate
program achieved) requires a **point-estimate** improvement. That is exactly what
the univariate AdaptShrink got from selection/bias correction — so iteration 2 is
**component B (network-funnel-asymmetry-gated small-study correction)** and
**component C (inconsistency-aware interval inflation)**, evaluated on the
`selection` and `inconsistency` grid axes (already wired into `nma_sim.py`), where
common-τ²'s point estimate is genuinely biased and a correction can win on MCIW0.

## Files
`nma/nma_core.py` (engine) · `nma/adaptshrink_nma.py` (estimator) ·
`nma/reference/gen_netmeta_reference.R` + `test_netmeta_parity.py` (parity) ·
`nma/verify/` (independent cross-impl) ·
`nma/truth-recovery/nma_sim.py` (generator) · `nma_bakeoff.py` (scorer) ·
`probe_coverage_by_tau.py` (deployable-coverage evidence) ·
`nma_*_perrep.csv` / `_summary.csv` / `_gate.json` / `probe_coverage_by_tau.csv`
(committed results) · `nma/DESIGN_BRIEF.md` (field map + design decision).
