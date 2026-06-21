# AdaptShrink-NMA — design brief

Generalizing the univariate AdaptShrink result (`src/ubcma/adaptshrink.py`,
`truth-recovery/REPORT_MATCHED_COVERAGE.md`) to **network meta-analysis**. Same
discipline: a verified reference engine first, an oracle-free estimator second,
a matched-coverage bake-off with a paired-bootstrap truth-gate third, and every
number traceable to a committed result file.

---

## 1. The modern NMA field to beat

| Family | Representative | What it estimates | Heterogeneity model |
|---|---|---|---|
| **Contrast-based frequentist (graph-theoretic)** | Rücker 2012 / `netmeta` | league of relative effects via GLS on an electrical-network Laplacian | **common τ²** (one heterogeneity for the whole net), DL or REML |
| Contrast-based Bayesian | Lu–Ades 2004 (`gemtc`, BUGS) | basic parameters + ranks via MCMC | common τ² (or class) with priors |
| Arm-based | Hong/Zhang 2016 | absolute arm effects | arm-level random effects |
| Inconsistency models | design-by-treatment interaction (White 2012); node-splitting (Dias 2010) | direct vs indirect discrepancy | adds inconsistency variance |
| Small-study / bias | network meta-regression on √(precision) (Chaimani 2012), CINeMA | bias-adjusted effects | covariate on SE |

**Our verified anchor** (`nma/nma_core.py`): the graph-theoretic frequentist
engine, reproducing `netmeta` 3.6-1 to ~1e-6 on Senn2013 (multi-arm diabetes)
and the Hasselblad smoking network — league TE/seTE (common+random), Q, df, the
Jackson-2012 generalized-DL τ², and the P-score ranking. This is the field we
must beat at matched coverage.

### The real failure modes (what we attack)

1. **Heterogeneity structure is poorly estimated in sparse networks.** The
   field default is *common τ²* — one heterogeneity shared by every comparison.
   When heterogeneity genuinely varies by comparison (a well-studied A-vs-B with
   τ≈0 alongside a noisy C-vs-D with τ large), common-τ² over-shrinks the noisy
   comparison's interval (under-coverage there) and over-widens the clean one
   (lost efficiency). The opposite extreme — *comparison-specific τ²_c* — is
   unbiased but its per-comparison DL estimate is wildly unstable when a contrast
   has 1–3 direct studies (the usual case). **Neither is right; the bias–variance
   sweet spot is a data-driven interpolation.** This is the direct analog of the
   univariate problem AdaptShrink solved for a *scalar* τ².
2. **Multi-arm correlation** must be carried exactly (within-study covariance,
   +τ²/2 per shared arm) or both point and interval are wrong. Our engine already
   does this to 1e-6; the new estimator must preserve it.
3. **Inconsistency inflates the truth.** When direct and indirect evidence
   disagree (design-by-treatment interaction), a consistency model reports
   intervals that are too narrow for the true uncertainty → under-coverage.
4. **Small-study / selective-reporting effects** in networks are handled weakly:
   network funnel asymmetry biases the pooled contrasts, and the field rarely
   corrects it by default.

---

## 2. AdaptShrink-NMA — the estimator

Built **on top of** the verified graph-theoretic engine (so multi-arm and the
GLS league stay netmeta-exact), AdaptShrink-NMA replaces the heterogeneity model
and adds two gated components:

**(A) Adaptive heterogeneity-structure shrinkage (the core, genuinely new).**
For each comparison type *c* with `n_c` direct studies, form a direct
DerSimonian–Laird `τ²_c,direct`, and the network common `τ²_common`. Shrink:

```
τ²_c(λ_c) = λ_c · τ²_common + (1 − λ_c) · τ²_c,direct
λ_c       = ν / (ν + (n_c − 1)·s_c)
```

`λ_c → 1` (toward stable common-τ²) when a comparison is **data-poor / peripheral**
(`n_c` small) and **geometrically weak** (`s_c` = a network-geometry weight from
the comparison's leverage in the Laplacian — low leverage ⇒ borrow more). `λ_c → 0`
(trust the comparison's own heterogeneity) when it is data-rich with clear excess
heterogeneity. `ν` is the single transparent tuning constant (the AdaptShrink
`kappa` analog), reported explicitly and calibrated only on a held-out split in
the matched-coverage scorer. The shrunk `τ²_c` enter the per-study weight blocks
(diagonal `τ²_c`, off-diagonal `τ²_c/2` for shared arms), preserving multi-arm
correctness.

**(B) Network-funnel-asymmetry-gated small-study correction (optional, gated).**
A network Egger-type test (regress standardized contrasts on their SE across the
net). Only if asymmetry is significant do we blend toward a precision-adjusted
(PET/PEESE-in-network) refit — exactly the funnel-asymmetry gate of univariate
AdaptShrink. Off by default unless the gate fires, so no efficiency cost on clean
networks.

**(C) Inconsistency-aware interval inflation.** Add the design-by-treatment
interaction excess (the network Q_inc beyond its df) as a between-source variance
term to each contrast's SE — the league widens automatically when direct/indirect
evidence conflict, the structural analog of AdaptShrink's "widen when members
disagree". Off (factor 1) when the network is consistent.

### Decision: **genuinely-new estimator within the AdaptShrink family**

Not a re-skin of the univariate ensemble. The univariate method averages a panel
of *point estimators*; AdaptShrink-NMA instead adaptively shrinks the
*heterogeneity covariance structure itself* across comparisons, governed by
network geometry — a model that did not previously exist in the NMA field
(it strictly interpolates the two standard heterogeneity models and reduces to
each at its λ→0/1 limits). It inherits the AdaptShrink *philosophy* (adaptive
shrinkage + gated bias correction + auto-widening intervals) and is built on the
shared verified engine, but components (A) and (C) are new NMA methodology. The
justification is failure mode #1, which is the dominant, most-cited sparse-network
weakness of the modern field.

---

## 3. Matched-coverage NMA bake-off (protocol)

Generalizes `matched_coverage_bakeoff.py` (MCIW0 + paired-bootstrap truth-gate)
to a vector estimand:

- **Estimand**: the `n−1` basic contrasts `d_{ref,t}` and the treatment ranking.
- **MCIW0 (primary, efficiency)**: per basic contrast, split replicates into
  calibration/test by parity; constant half-width `c = T-quantile of |d̂−d_true|`
  on calib; `MCIW0 = 2c`; test coverage on the held-out half. Aggregate by mean
  over contrasts. Isolates point-estimator efficiency at matched coverage.
- **raw_cov (deployable)**: real per-replicate coverage of `d_true`, κ=1, no
  oracle — the honest number a practitioner gets.
- **Ranking accuracy**: Spearman ρ and top-1 hit-rate of the estimated P-score
  ranking vs the true ranking; reported honestly (no oracle).
- **Truth-gate (win vs the field)**: (G1) every scored replicate finite; (G2)
  winner's matched-coverage calibration generalizes on the test half
  (|test_cov−T|≤0.06); (G4 decisive) **paired bootstrap** over replicates puts
  the 97.5th percentile of the MCIW0 advantage below 0.

### Simulation grid
network geometry {star, line, loop, fully-connected} × n treatments {4,6,8} ×
studies-per-comparison {sparse 1–2, moderate 3–5} × multi-arm fraction {0, 0.3}
× heterogeneity {homogeneous τ, **heterogeneous-across-comparisons τ**} ×
inconsistency {consistent, design-inconsistent} × selection {none, moderate
small-study}. The cells that should expose the field: **sparse + heterogeneous-τ**
(common-τ² mis-specified, comparison-specific unstable) — where the shrinkage core
should win — and **inconsistent / selected** cells for components (C)/(B).

Field compared every cell: `netmeta_common_DL`, `netmeta_common_REML`,
`comparison_specific`, `AdaptShrink-NMA`. All built on the verified engine so the
only thing that differs is the heterogeneity/bias/interval model.

---

## 4. Verification

- **Primary**: `nma/reference/test_netmeta_parity.py` — engine ≡ netmeta to 1e-6.
- **Independent cross-implementation**: Codex (both seats) + agy re-derive the
  multi-arm NMA math from `nma/verify/VERIFY_SPEC.md` and check their own league
  tables vs the netmeta CSVs to 1e-6 (`nma/verify/*_RESULT.md`).
- No oracle-only win is ever reported as deployable; ranking metrics are reported
  with their honest (non-oracle) accuracy.
