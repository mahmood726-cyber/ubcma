# Independent verification task: AdaptShrink-NMA Phase 2 (components B + C)

You are independently re-deriving two pieces of new NMA methodology to cross-check
another implementation. **Do not read** `nma/smallstudy_nma.py`,
`nma/inconsistency_nma.py`, or `nma/adaptshrink_nma.py` — implement the math
yourself from this spec, then compare to the committed R `netmeta` references.

You MAY read `nma/nma_core.py` (the engine is already verified to ~1e-11 vs
netmeta) and reuse its GLS league construction — the new math is layered on it.

## Inputs (committed, relative to repo root)
- `nma/reference/smoking_input.csv`, `nma/reference/senn2013_input.csv` —
  columns studlab,treat1,treat2,TE,seTE. Multi-arm networks. TE = effect(treat1)
  − effect(treat2).
- `nma/reference/{smoking,senn2013}_TE_random.csv`, `_seTE_random.csv` — netmeta
  random-effects league. `_scalars.csv` — tau2 (DL), Q, df.Q.
- `nma/verify/decomp_reference.csv` — netmeta `decomp.design` Q decomposition
  (Q.total, Q.het within designs, Q.inc between designs, with df) for both nets.

## Part B — network small-study meta-regression (PET / PEESE)
Work in the basic-parameter (reference) parameterization. Pick reference r (first
treatment alphabetically). Basic parameters d_t = effect(t) − effect(r), d_r = 0.
Each comparison row i: y_i = (d_{t1} − d_{t2}) + error, with the SAME block
precision weight matrix W the engine uses for the random-effects model (network
DL tau^2 from the scalars CSV; multi-arm blocks via pinv of the contrast
covariance). Build the basic design matrix B_basic (m × (n−1), the engine
incidence with the reference column dropped) and **augment** with one column:

    X = [ B_basic | s ]        s_i = se_i  (PET)   or   s_i = se_i^2  (PEESE)

Solve weighted least squares  coef = (XᵀWX)^+ XᵀWy. The first n−1 entries are the
bias-adjusted basic parameters d (effect at s→0); the last entry is the network
small-study slope beta, with Var(beta) = [(XᵀWX)^+]_{last,last}.

**Checks to report (both networks):**
1. With NO covariate (X = B_basic) your basic-parameter league d_t − d_u must
   reproduce the netmeta random-effects league to < 1e-8. (Sanity: confirms your
   augmented model reduces to the field default.)
2. Report the PET slope beta, its z = beta/sqrt(Var(beta)), and two-sided p
   (network Egger asymmetry test).
3. Report the PEESE-adjusted league entries vs the reference treatment.

## Part C — design-by-treatment Q decomposition (inconsistency)
At the common-effect weights (tau^2 = 0):
- Q_total = generalized Cochran Q of the consistency fit, df_total = (Σ_studies
  (arms−1)) − (n−1).
- Q_het = Σ over **designs** (a design = the set of treatments compared in a
  study; group studies by that set) of the within-design generalized Q, pooling
  each design's studies on their own; df_het = Σ within-design df. (For 2-arm
  designs this is the per-edge fixed-effect Q.)
- Q_inc = Q_total − Q_het, df_inc = df_total − df_het.

**Check:** your Q_total, Q_het, Q_inc and their df must match
`nma/verify/decomp_reference.csv` (netmeta decomp.design) to < 1e-6 / exact df.
Confirm df_inc equals the number of independent loops.

## Deliverable
A standalone script `nma/verify/<yourname>_phase2_nma.py` and a short
`nma/verify/<yourname>_phase2_RESULT.md` with the numbers and max abs differences
for Parts B(1) and C, plus the Part B(2) asymmetry statistics. Report honestly.
