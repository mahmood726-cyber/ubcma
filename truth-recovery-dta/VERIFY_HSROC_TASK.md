# Independent verification task: HSROC (exact-binomial bivariate GLMM) ML

You are an INDEPENDENT re-implementer. **Do NOT read or import
`src/ubcma/dta.py`** — implement the estimator yourself from the math spec below,
using only numpy / scipy, and check it against the reference fits.

## Background
The Rutter–Gatsonis HSROC model is (Harbord 2007) a reparameterization of the
**bivariate generalized linear mixed model** fit by the **exact binomial**
likelihood (as opposed to Reitsma's within-study normal approximation). We verify
the exact-binomial fit two ways: against R `lme4::glmer`
(`truth-recovery-dta/reference_glmm.json`), and by the deviance check below.

## Math spec
Per study `i` with counts (TP, FP, FN, TN): diseased arm size `n1 = TP+FN`,
non-diseased `n0 = TN+FP`. Use the SAME continuity-corrected counts as the
reference (mada-style: if ANY study has a zero cell, add 0.5 to EVERY cell of
EVERY study). Random effects per study `(b1_i, b2_i) ~ N(0, Sigma)` with
`Sigma = [[t1^2, rho t1 t2],[rho t1 t2, t2^2]]`. Conditional on the random
effects:

```
logit Se_i = mu1 + b1_i ,   logit Sp_i = mu2 + b2_i
TP_i ~ Binomial(n1_i, Se_i) ,   TN_i ~ Binomial(n0_i, Sp_i)
```

The marginal log-likelihood of study `i` integrates the two binomials over the
bivariate-normal random effects:

```
L_i = ∫∫ Bin(TP_i; n1_i, expit(mu1+b1)) · Bin(TN_i; n0_i, expit(mu2+b2))
          · N2((b1,b2); 0, Sigma) db1 db2
```

Maximize `sum_i log L_i` over `(mu1, mu2, t1, t2, rho)`. The summary operating
point is `(mu1, mu2)`; summary Se = `expit(mu1)`, Sp = `expit(mu2)`. Integrate
the 2-D random effect however you like (dense product quadrature, adaptive
Gauss–Hermite, Monte-Carlo with enough draws) — your choice, independent of any
other implementation. A non-adaptive grid needs many nodes; a dense
trapezoidal/GH grid of ±6 SD with ≥60 nodes per dim is a safe simple choice.

## What to do
1. Write a standalone `truth-recovery-dta/verify_hsroc_<seat>.py` (numpy/scipy
   only, NO `ubcma` import).
2. For each dataset in `reference_glmm.json` with `ok=true`, take the raw 2×2
   counts from `truth-recovery-dta/reference_fits.json` under the SAME dataset
   name (`counts.TP/FP/FN/TN` arrays), fit your estimator, and record your
   `(sens_summary, spec_summary, mu1, mu2, t1, t2, rho)`.
3. Report, per dataset, the absolute difference of your summary Se/Sp vs the
   glmer reference (`sens_summary`, `spec_summary`). glmer uses the Laplace
   approximation (nAGQ=1), which is biased for large random effects, so expect
   agreement to ~0.01–0.02, not 1e-6.
4. **Deviance check (the decisive one):** evaluate your own exact marginal
   negative log-likelihood at (a) your MLE and (b) glmer's reported parameters
   (`m1_logit_sens, m2_logit_spec, tau_sens, tau_spec, rho`). Your MLE's NLL must
   be ≤ glmer's-params NLL (you maximize the exact likelihood at least as well).
5. Write `truth-recovery-dta/verify_hsroc_<seat>_result.json` with
   `{"per_dataset": {name: {se, sp, dse_vs_glmer, dsp_vs_glmer, nll_mine,
   nll_glmer_params, mine_le_glmer}}, "worst_se_sp_vs_glmer": <float>,
   "all_mine_le_glmer": <bool>}`.

Report only: your worst Se/Sp agreement vs glmer, and whether your exact-NLL is
≤ glmer's at every dataset. No fabricated numbers — every figure must come from
running your code.
