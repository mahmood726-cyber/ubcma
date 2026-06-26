# Phase 2 HSROC verification — findings (for REPORT)

The HSROC estimator (exact-binomial bivariate GLMM via adaptive Gauss-Hermite
quadrature) is validated four independent ways:

1. **Likelihood exactness.** The adaptive-GHQ marginal log-likelihood reproduces
   a brute-force dense (401x401 trapezoidal, +-8 SD) 2-D integral of the same
   model to machine precision at a fixed parameter point (negll diff 0.0 at
   G>=12, ~2e-8 relative at G=6). So the integrator is correct, not just
   internally consistent.

2. **R `lme4::glmer` reference.** The fitted summary (Se, Sp) reproduce the exact
   bivariate GLMM fit by `glmer` (`reference_glmm.json`) to a worst-case 0.011
   across the 5 canonical datasets (AuditC, smoking, Dementia, skin_tests, SAQ);
   the sparse k=10 set (skin_tests) matches to 1e-4. The residual sits on the
   two high-tau datasets (AuditC tau~1.6, SAQ).

3. **Better exact optimum than glmer.** Evaluating the *exact* binomial negative
   log-likelihood at our MLE vs glmer's reported parameters, OUR fit is strictly
   lower on every high-tau dataset (AuditC +0.219, SAQ +0.321, smoking +0.519 in
   deviance/2). glmer's default is Laplace (nAGQ=1), biased for large random
   effects; the residual gap in (2) is glmer's approximation, not ours. (Unit
   test `test_hsroc_is_a_better_exact_optimum_than_glmer_laplace`.)

4. **Independent re-implementations (no `ubcma` import).**
   - **codex_main** (seat mahmood726): independent exact-binomial GLMM, worst
     Se/Sp vs glmer = 0.026, exact-NLL <= glmer's params at every dataset;
     agrees with our fit to 0.02. PASS.
   - **codex_noreen** (seat noreenahmad01): independent product-Gauss-Hermite
     GLMM. Its sandbox could not launch Python (Windows orchestrator error 1223),
     so we ran its (independently written, non-importing) script ourselves: it
     agrees with both glmer and our fit on 4/5 datasets to <=0.031; Dementia is
     an optimizer miss in its implementation (0.117), and its self-comparison
     harness read non-existent glmer field names. Partial corroboration.
   - **agy**: did not produce output within the run window (sandbox stalled);
     inconclusive.

Net: the exact-binomial HSROC is correct (machine-precision integrator + glmer
reference + one clean independent re-impl + a second corroborating on 4/5), and
is in fact a *better* exact maximizer than the standard Laplace GLMM.
