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

## DONE (2026-07-02) -- head-to-head on the real GLP1 slice (`borrowing/stage4_doselink.py`)
Executed as a head-to-head (pilot-2 already uses the dose-distance kernel): on the real GLP1 field
(n=12, dose 1.1-14 mg, HbA1c; modifier real, slope -0.092 %/mg, R2=0.94) a leave-one-trial-out test
(truth = real held-out effect) pits **the dose-response MODEL** (linear DRMA/MBNMA = RE meta-regression
predicting a+b*dose at the held-out dose) against **the borrowing-field dose-distance kernel**
(`borrowing_field2.covariate_prior`, identical code) and the no-dose null:

| method | LOO MAE | cover | vs no-dose null |
|---|---|---|---|
| dose_metareg (linear DRMA/MBNMA) | **0.204** | 0.83 | -0.244 [-0.443,-0.027] **WIN** |
| kernel relevance (central bw) | 0.269 | 1.00 | -0.180 [-0.306,-0.035] **WIN** |
| uniform (no dose borrowing) | 0.449 | 1.00 | -- |

**Verdict (honest):** BOTH real dose-borrowing methods robustly beat the no-dose null (Stage-4
hypothesis -- dose-borrowing pays -- confirmed on real data). Head-to-head, the parametric model is
**directionally more accurate** at every bandwidth (metareg-kernel -0.041/-0.064/-0.136 as the kernel
over-smooths) but **not significant at n=12 -- a statistical TIE** (central-bw -0.064 [-0.155,+0.023]).
The two threads are the *same dose-borrowing mechanism*: when the true dose-response is ~linear (GLP1)
the correctly-specified parametric model is at-least-as-good, while the kernel buys robustness to
functional-form misspecification at a small efficiency cost. Result JSON `borrowing/stage4_doselink_result.json`.

## FIRM-UP (2026-07-02) -- generalised across clean-modifier slices (`borrowing/stage4_multi.py`)
Ran the same parametric-MODEL vs relevance-KERNEL vs no-covariate-null head-to-head on every real slice in
`replication/all_slices_trials.json`, gated truth-first on the pre-registered modifier test (perm p<0.05).
Only **2 of 8 candidate slices pass the gate** -- GLP1 dose (p=0.010) and Obesity baseline-weight (p=0.002);
the other 6 (obesity dose, tirzepatide dose, depression×2, schizophrenia) have a non-significant modifier and
are correctly SKIPPED (borrowing cannot help without a real modifier -- the program's inertia boundary,
intact). On both gated slices:

| gated slice | k | metareg / kernel / null MAE | metareg − kernel [95% CI] | kernel − null |
|---|---|---|---|---|
| GLP1 dose | 12 | 0.204 / 0.269 / 0.449 | −0.064 [−0.155, +0.025] **tie** | −0.180 [−0.305, −0.036] **kernel WINS null** |
| Obesity baseline-weight | 9 | 2.313 / 3.190 / 3.688 | −0.878 [−1.527, −0.319] **metareg WINS** | −0.497 [−1.055, −0.099] **kernel WINS null** |

**Firmed verdict (honest):** dose/covariate borrowing pays on BOTH gated slices — the kernel robustly beats
the no-covariate null in 2/2 (the Stage-4 hypothesis holds beyond GLP1). Head-to-head, the parametric model
is a tie on GLP1 and a **significant win on obesity-baseline** (where the linear covariate signal is strong
and the n=9 kernel over-smooths): so the parametric dose/covariate MODEL is at-least-as-good and sometimes
strictly better than the nonparametric kernel — refining the earlier "tie" to "parametric ≥ kernel on
well-specified linear modifiers." (Only 2 slices clear the gate, so a pooled cross-slice CI is not claimed;
per-slice results are reported. Result JSON `borrowing/stage4_multi_result.json`.)
