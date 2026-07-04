# AdaptShrink external validity on a real ground-truth-anchored case — magnesium/MI (HONEST BOUNDARY)

**Dataset.** `metadat::dat.li2007` (Li 2007) — 22 trials of IV magnesium for acute MI, binary
mortality. The textbook publication-bias story: 20 small early trials reported a large mortality
benefit; the ISIS-4 mega-trial (N=58,050) and MAGIC (N=6,213) then showed essentially no effect.
The two mega-trials are the de-facto **ground truth**. `magnesium_realtest.py`, result JSON committed.

**Design.** Pool the 20 small trials (k=20, N=8,213) with each estimator; measure the distance of its
pooled logOR from the mega-trial IV-pooled truth (logOR **+0.048**, OR 1.05 — no effect). A good
publication-bias correction should move the spuriously-beneficial small-trial estimate toward that truth.

| estimator | logOR | OR | dist to truth | vs naive |
|---|---|---|---|---|
| naive RE (DL) | −0.497 | 0.61 | 0.545 | — (spurious benefit) |
| Henmi–Copas | −0.497 | 0.61 | 0.545 | no move (IV point) |
| **PET (Egger intercept)** | −0.314 | 0.73 | **0.362** | **+34% closer (best)** |
| trim-and-fill | −0.501 | 0.61 | 0.549 | wrong way (misfires) |
| Vevea–Hedges | −0.564 | 0.57 | 0.612 | wrong way (overshoots benefit) |
| AdaptShrink solo | −0.353 | 0.70 | 0.402 | +26% closer |
| AdaptShrink ens | −0.475 | 0.62 | 0.524 | +4% closer (diluted) |

**Verdict — HONEST BOUNDARY, not a win.** Three truths:
1. **No corrector recovers the mega-trial null** (best is PET at OR 0.73, still far from OR 1.05). The
   magnesium small-study effect is famously *more than* publication selection — clinical-era and trial-
   quality confounding — so it is an adversarial case for any funnel-based correction. This is a
   known, contested example; that all methods fall short is the expected, honest finding.
2. **AdaptShrink moves in the right direction** (solo +26%, OR 0.61→0.70) but is **not** the closest here;
   **PET is** (+34%). Note the contrast with the transportable-NMA head-to-head, where PET was
   *catastrophic* on 3–6 studies/contrast — here, on a single k=20 funnel, PET has enough studies to
   behave and does best. Method choice is regime-dependent, and we report it that way.
3. **The AdaptShrink ensemble under-moves (+4%)** because two of its members misfire on this dataset:
   trim-and-fill and Vevea–Hedges push the estimate the *wrong* way (more benefit). The robust
   model-average then dilutes PET's correct pull. This is a real, dataset-specific weakness of the
   ensemble: robust averaging protects against a single bad member on average, but when a majority of
   members misfire on an adversarial case, the average follows them. AdaptShrink-*solo* (omega-shrinkage
   toward the PET intercept) is the more reliable corrector on this case.

**No win manufactured.** On this real ground-truth case AdaptShrink is directionally correct but neither
dominant nor sufficient; the honest lesson is (a) an adversarial non-selection bias defeats all funnel
correctors, and (b) the ensemble is only as safe as the majority of its members on a given dataset —
AdaptShrink-solo is preferable when members may misfire. Bounds the AdaptShrink real-data claim.
