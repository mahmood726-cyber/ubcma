# Stage 4 -- dose-response as a within-class relevance covariate for the borrowing field

This is a design note (a bridge to the `borrowing/` thread), not a validated
result. It records *how* the dose-response machinery connects to the borrowing
field and what the first honest test would be.

## The link
Borrowing **pilot-2** found that *relevance is real* when a covariate predicts
between-study heterogeneity: within the GLP1 class, a dose/exposure covariate was
a genuine effect modifier, and relevance-weighted **precision fusion** beat both
null comparators on real held-out effects (`borrowing/REPORT_BORROWING_PILOT2.md`;
memory `ubcma-borrowing-field-pilot`). Pilot-3 then showed transportability does
*not* beat relevance-only on a T2DM slice -- relevance-only is the shipped
contribution.

**Dose is exactly such a within-class relevance covariate**, and the
dose-response thread gives two concrete ways to use it:

1. **MBNMA already *is* dose-borrowing.** The parametric curve f_a(dose) borrows
   strength across every dose of agent a -- a 4-dose agent's Emax/slope is
   informed by all of its arms jointly. That is precisely pilot-2's
   relevance-weighted precision fusion, with **dose proximity as the relevance
   kernel** instead of a discrete class label. The frequentist MBNMA in
   `mbnma.py` makes this borrowing explicit and verifiable (saturated == netmeta;
   constrained == borrowed).

2. **Forward test (proposed).** Set the borrowing field's per-pair shrinkage
   weight lambda_ij as a function of dose distance |dose_i - dose_j| (or of the
   model-predicted effect proximity |f_a(dose_i) - f_a(dose_j)|) instead of a
   binary same-class flag. Hypothesis: on the real GLP1-dose slice where pilot-2
   *already* established dose as a real modifier, **dose-modified relevance beats
   class-only relevance** at matched coverage on held-out effects.

## Why this is promising where the Stage-3 slope bake-off was a null
Stage 3 asked a *different* question (can an aggregate beat two-stage REML on the
pooled slope under selection?) and returned an honest null -- there was no valid
oracle-free bias-corrected member to gain from. The borrowing connection does not
need a bias corrector: it exploits **dose as structure for variance reduction**
(borrow precision across nearby doses), which pilot-2 already showed pays off when
the covariate is a true modifier. The two threads are complementary: Stage 3 is
about the *point estimate under selection*; the borrowing link is about
*relevance-weighted precision*.

## First step when picked up
Reuse `borrowing/class_lambda.py` + `borrowing/real_glp1.py`; replace the binary
class relevance with a dose-distance kernel; rerun the pilot-2 matched-coverage
held-out test with the same truth-gate. Honest null or win region either way.
