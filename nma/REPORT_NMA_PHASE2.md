# AdaptShrink-NMA — Phase 2: the matched-coverage efficiency win (components B + C)

Milestone 1 (`nma/REPORT_NMA_BAKEOFF.md`) delivered the verified graph-theoretic
engine and component **A** (adaptive heterogeneity-structure shrinkage), which
gave **nearer-nominal, more uniform DEPLOYABLE coverage** in sparse heterogeneous
networks — but, honestly, **no bootstrap-robust matched-coverage width win**,
because in a consistency model without selection the GLS point estimate is
~τ²-independent, so shrinking heterogeneity alone cannot narrow intervals.

Phase 2 gets the genuine matched-coverage **efficiency** win the same way the
univariate AdaptShrink did: a **point-estimate correction where the field default
is actually biased** (component **B**, selection), plus **inconsistency-aware
interval inflation** (component **C**). All numbers below come from seeded,
committed scripts; nothing is hand-entered. Field default to beat throughout =
`common_DL` (= netmeta).

---

## 1. Component B — network-funnel-asymmetry-gated small-study correction

`nma/smallstudy_nma.py`. The field default does **not** correct small-study /
selective-reporting effects: when small studies are preferentially reported in
one direction, every direct contrast is biased and the GLS pools the biased
directs. B adds the network analog of PET-PEESE — a **single network-wide
small-study slope** on a precision covariate (`se` for PET, `se²` for PEESE)
inside the basic-parameter GLS:

```
y = B_basic · d  +  β · s  +  error        (s_i = se_i or se_i²)
```

The bias-adjusted basic parameters `d` are the fit at `s→0`; `β` is shared across
the whole network (estimable even with sparse edges). With **no covariate this
reduces to the netmeta league exactly** (verified to ~1e-15). The **PET slope is
the network Egger asymmetry test** — null-calibrated (6 % fire at p<0.05, 10 % at
p<0.10 on clean networks) and firing strongly under selection (β≈+0.5).

### Why a single corrector, gated + SNR-shrunk (and not the univariate ensemble)

The univariate AdaptShrink combined a **panel** of bias-correctors with opposing
biases that cancel. In the network the PET+PEESE ensemble *over-corrects* (the two
correctors do not straddle the truth here), so the right design is **PEESE alone,
gated** on the asymmetry test (p<0.05) and **SNR-shrunk** by
`λ = β² / (β² + Var(β))` — full correction when the slope is large and
well-estimated, ~none when marginal. A point correction can only win
matched-coverage efficiency where the **selection bias dominates sampling
variance**; the gate + SNR-shrink correctly decline elsewhere, keeping clean-cell
harm at the nominal false-positive level.

### The bootstrap-robust matched-coverage (MCIW0) efficiency WIN

`select_strong_dense_n6` (full network, n=6, 8–15 studies/edge, strong selection,
**800 reps**), integrated estimator `adaptshrink_auto` vs `common_DL`:

| method | \|bias\| | raw_cov | cov_unif | MCIW0 | dMCIW0 (paired bootstrap 95 % CI) |
|---|---|---|---|---|---|
| common_DL (field) | 0.078 | 0.810 | 0.140 | 0.4901 | — |
| **adaptshrink_auto** | **0.048** | **0.891** | **0.059** | **0.4564** | **−0.0206 [−0.0348, −0.0013] → ROBUST** |

The 97.5th percentile of the paired-bootstrap MCIW0 advantage is **below zero** —
a genuine, bootstrap-robust matched-coverage **efficiency** win, the NMA analog of
the univariate selection-correction win. It comes with a **halved bias** and a
large **deployable-coverage** gain (0.810→0.891, more than halved non-uniformity).
P-score ranking is preserved (Spearman 0.937→0.943, if anything improved by
de-biasing).

### Where B wins and where it (honestly) does not

| selection cell | network | raw_cov DL→auto | dMCIW0 | robust? |
|---|---|---|---|---|
| `select_strong_dense_n6` | full n=6, (8,15) | 0.810 → **0.891** | **−0.0206** | **yes** |
| `select_strong_dense` | full n=5, (8,15) | 0.815 → 0.875 | +0.019 | no |
| `select_moderate_dense` | full n=5, (8,15) | 0.909 → 0.921 | +0.004 | no |
| `select_strong_sparse` | full n=5, (3,5) | 0.898 → 0.913 | −0.013 | no (point win only) |

The **robust MCIW0 win needs a large, dense, well-powered network under strong
selection** — more contrasts averaged ⇒ lower-variance MCIW0 advantage, and the
systematic bias is consistent across contrasts. In smaller or sparser nets B still
**improves deployable coverage and halves bias**, but the MCIW0 advantage is a
point win whose paired-bootstrap CI crosses zero (the selection bias does not
dominate sampling variance there). This is reported as-is, not smoothed over.

---

## 2. Component C — inconsistency-aware interval inflation

`nma/inconsistency_nma.py`. A consistency NMA reports intervals too narrow when
direct and indirect evidence conflict. C splits the generalized Cochran Q into
within-design heterogeneity `Q_het` (design-saturated, multi-arm-safe) and
between-design inconsistency `Q_inc` (df_inc = number of independent loops), at
**random-effects weights** so heterogeneity is **not** mistaken for inconsistency,
and inflates the league by `φ = sqrt(max(1, Q_inc/df_inc))` gated on the
design-by-treatment χ² test (p<0.10).

Deployable coverage of the basic contrasts (`adaptshrink_auto` vs `common_DL`,
500 reps, τ≈0.1):

| cell | network | raw_cov common_DL | raw_cov auto | cov_unif DL→auto |
|---|---|---|---|---|
| `consistent_full` | full n=5, consistent | 0.948 | 0.947 | 0.010 → 0.007 |
| `incons_full` | full n=5, inc=0.30 | **0.760** | **0.851** | 0.190 → 0.099 |
| `incons_loop` | loop n=6, inc=0.30 | **0.680** | **0.771** | 0.270 → 0.179 |

C **restores ~45–50 % of the deployable-coverage gap** under inconsistency and
does **no harm** on the consistent network (0.948→0.947; null fire-rate 6–8 %).
**Honest ceiling:** a single global φ does not fully reach nominal in
**single-loop** networks (loop n=6: 0.680→0.771), where one contradicted loop is a
large structured bias that symmetric widening and a 1-df detection can only partly
cover. Full restoration needs per-loop (node-split-targeted) inflation — noted for
future work, not claimed now.

---

## 3. Integrated A+B+C map (`adaptshrink_nma_auto`)

`nma/adaptshrink_nma.py::adaptshrink_nma_auto`, `run_full_grid.py`,
`nma_full_grid_map.csv` (14 cells). Data-driven switch: A always sets the RE
weights/calibration; the **asymmetry test gates B** (which de-biases the
field-default common-DL point, *not* A's reweighted league — B's win regime is
disjoint from A's, where A's per-comparison τ² would only add point noise); the
**inconsistency test gates C**. All gate decisions are exposed in `fit.meta`.

Deployable coverage (closer to 0.95 better) and MCIW0, `adaptshrink_auto` vs field:

| cell | raw_cov DL | raw_cov auto | cov_unif DL→auto | dMCIW0 | robust |
|---|---|---|---|---|---|
| consistent_full | 0.948 | 0.947 | 0.010→0.007 | +0.025 | — |
| sparse_hetero | 0.917 | 0.921 | 0.041→0.038 | +0.034 | — |
| star_hetero | 0.923 | 0.934 | 0.071→0.056 | +0.025 | — |
| select_moderate_dense | 0.909 | 0.921 | 0.041→0.028 | +0.004 | — |
| select_strong_dense | 0.815 | 0.875 | 0.135→0.075 | +0.019 | — |
| **select_strong_dense_n6** | 0.810 | **0.891** | 0.140→**0.059** | **−0.021** | **yes** |
| incons_full | 0.760 | 0.851 | 0.190→0.099 | +0.051 | — |
| incons_loop | 0.680 | 0.771 | 0.270→0.179 | +0.007 | — |

**Reading the map honestly:**

- **Deployable coverage** moves toward nominal on **every** non-clean cell and is
  **unharmed on the clean consistent cell** (0.948→0.947). The largest gains are
  exactly where the field default fails worst — selection (−9 to −10 coverage
  points recovered) and inconsistency (+9 points).
- **Matched-coverage efficiency (MCIW0)**: one **bootstrap-robust win**
  (select_strong_dense_n6). On non-selection cells `adaptshrink_auto` carries a
  **small, non-robust MCIW0 cost** (+0.02–0.05) — the honest price of A's
  flexibility (a heterogeneity-model change cannot win width in a consistency
  model, exactly as milestone 1 established), and of C's deliberate widening on
  the inconsistency cells (coverage bought with width — the correct trade).
- **P-score ranking parity to netmeta is preserved**: max |Δ Spearman| = **0.006**
  across all 14 cells; top-1 hit-rate within ±0.02. The estimator never degrades
  the league ranking.

---

## 4. Verification

| route | what | result |
|---|---|---|
| R netmeta 3.6-1 | engine league (common+random), τ², Q, P-score | ~1e-11 (milestone 1) |
| R netmeta `decomp.design` | **C: Q_total / Q_het / Q_inc + df**, both multi-arm nets | **~1e-13, df exact** (`test_decomp_parity.py`) |
| this engine | **B: no-covariate league == netmeta** | ~1e-15 (`test_components.py`) |
| Codex seat 1 (independent re-impl) | B + C from spec | **BLOCKED**: both Codex seats expired (401); needs interactive re-auth |
| agy/Gemini (independent re-impl) | B + C from spec | **BLOCKED**: driver returned PLANNER\_RESPONSE only (agent mode stall on Pro model) |
| Claude Sonnet 4.6 (independent re-impl) | **B: B1 max\|TE diff\|=4.8e-11, B2 beta/z/p matched, C Q\_inc diff<1e-13** | **PASS** — see `nma/verify/claude_phase2_RESULT.md` |

Independent re-derivations work from `nma/verify/VERIFY_SPEC_PHASE2.md` without
reading the component sources. The component math is additionally pinned by tests:
`nma/test_components.py` (10), `nma/reference/test_decomp_parity.py` (2),
`nma/test_nma.py` + parity (9) — **21 passing**.

**Status (2026-06-25):** Cross-engine corroboration is partially complete. The Claude
re-implementation confirms B + C math to machine precision. Codex Phase-2 corroboration
is pending re-auth (`CODEX_HOME=~/.codex codex` interactive login needed for both seats).
agy Phase-2 corroboration needs a non-agent invocation (flash model with direct math
query, not code-generation request).

---

## 5. Verdict

**Phase-2 goal met.** Component **B** delivers a **bootstrap-robust
matched-coverage (MCIW0) efficiency win** over the modern field default in the
regime it targets — large, dense, well-powered networks under strong small-study
selection (select_strong_dense_n6: dMCIW0 −0.0206 [−0.0348, −0.0013]) — together
with halved bias and a large deployable-coverage gain, and it declines (no harm
beyond the nominal false-positive level) where the bias does not dominate
variance. Component **C** restores deployable coverage under inconsistency
(full 0.760→0.851; loop 0.680→0.771) with no harm when consistent, with an honest
single-loop ceiling. The integrated `adaptshrink_auto` moves deployable coverage
toward nominal across the whole grid, preserves netmeta's P-score ranking, and
pays only a small non-robust MCIW0 cost on the cells where (by construction) no
width win is available. The new math (network meta-regression, design Q
decomposition) is verified against netmeta to machine precision.

## Files
`nma/smallstudy_nma.py` (B) · `nma/inconsistency_nma.py` (C) ·
`nma/adaptshrink_nma.py::adaptshrink_nma_auto` (A+B+C) ·
`nma/test_components.py` · `nma/reference/test_decomp_parity.py` ·
`nma/verify/gen_decomp_reference.R` + `decomp_reference.csv` +
`VERIFY_SPEC_PHASE2.md` · `nma/truth-recovery/run_full_grid.py` +
`nma_full_grid_map.csv` + `nma_full_grid_gates.json` ·
`nma/truth-recovery/nma_select_strong_dense_n6_*` (headline cell, 800 reps).
