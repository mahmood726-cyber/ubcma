# From-scratch verification task: learned-kernel registry field vs within-MA

**You are given ONE file:** `corpus_full_1177.csv` with columns
`ma, family, specialty, yi, se, year` — 1177 real meta-analysis study nodes from
28 published meta-analyses, harmonised into 3 effect families (SMD, COR = Fisher-z,
LOR = log-odds-ratio). `yi` is the study effect, `se` its standard error.

**Do NOT import any of my code.** Implement everything yourself in numpy/scipy
(and pandas for I/O). Work **within each family block only** (never mix families).

## What to compute (held-out reconstruction of the real `yi`)

For each family separately, treat every study's `yi` as an unknown to reconstruct
from a leakage-free feature vector — **never use `yi` (or any function of it) as a
feature.** Features per study: standardised `year` (missing → 0), standardised
`log(1/se^2)`, the categorical `specialty`, and the categorical `ma`.

Implement two predictors and score mean absolute held-out error |pred − yi|:

1. **LEARNED-KERNEL FIELD (honest k-fold).** A Gaussian-process regressor with a
   kernel that has a signal variance `sf2`, an RBF over the two continuous features
   with their own length scales, and a match/no-match ("categorical") kernel term
   over `specialty` and over `ma`, each with its own length scale — i.e. a
   *grouped-ARD* kernel with 4 length scales. Per-study noise variance = `se^2`
   plus a small learned nugget. Fit the hyper-parameters by maximising the log
   marginal likelihood. Evaluate with **honest 10-fold cross-validation: re-fit the
   hyper-parameters on each training fold and predict the held-out fold** (do NOT
   share hyper-parameters across folds; do NOT use closed-form LOO). Average over a
   few random fold seeds (e.g. 3–5) to reduce fold noise.

2. **WITHIN-MA (per-slice).** For a target study, pool ONLY the other studies in the
   same `ma` by inverse-variance (precision) weighting, optionally with a Gaussian
   kernel on standardised-year distance (bandwidth ~1). Predict that pooled mean.

## Report

- The honest-k-fold learned-kernel MAE (per family and overall), and the within-MA
  MAE (overall).
- The paired difference **learned_kernel − within_MA** with a paired-bootstrap 95%
  CI over the per-study absolute errors. Negative ⇒ the learned kernel beats
  within-MA borrowing.

Return these numbers as JSON. My build reports overall learned-kernel(10-fold) MAE
≈ 0.2x and a learned − within-MA difference that is **negative with a CI excluding
0** (the learned kernel beats within-MA borrowing across the corpus). Confirm or
refute from the data alone.
