# External cross-vendor verification task — transportable-NMA registry publication-bias headline

You are an independent verifier. Re-derive the two headline claims below **from scratch** in a single
Python script (`verify_tnma.py`) using only numpy / scipy / pandas / standard library. **Do NOT import,
read, or reference any code from the ubcma project** — only the three data files in this directory.
Write your own everything (aggregation, NMA, bootstrap). Print results and dump `verify_result.json`.

## Data files (this directory)
- `aact_hba1c_records.csv` — one row per (HbA1c mean-difference analysis × drug class) from
  ClinicalTrials.gov/AACT type-2-diabetes trials. Columns: `nct_id`, `drug_class`, `published`
  (1 = the trial's results are linked to a PubMed publication; 0 = results posted to the registry but
  not linked to a publication = "registered-only"), `abs_md_pct` (absolute HbA1c treatment mean
  difference, normalised to NGSP %).
- `class_lambda.json` — per drug class, `lambda` = (registered T2DM trials of that class that posted
  results) / (registered trials of that class). Lower lambda = more reporting selection.
- `dat.senn2013.csv` — a real diabetes network meta-analysis dataset (metadat). Columns include
  `study`, `treatment`, `mi` (mean change in HbA1c), `sdi` (SD), `ni` (arm n).

## CLAIM 1 — external validation of the registry model (engine-free, must reproduce closely)
For each `drug_class` with min(n_published, n_registered-only) >= 8:
  kappa_MD(c) = mean(abs_md_pct | published=1) / mean(abs_md_pct | published=0) - 1
Then over those classes:
  - kappa_pooled = weighted mean of max(0, kappa_MD(c)), weights = min(n_pub, n_reg).   EXPECT ~0.158
  - corr = Pearson correlation of kappa_MD(c) with (1 - lambda_c).                       EXPECT ~+0.50
Report both. (This says: published trials report larger HbA1c effects than registered-only, and the
gap grows with reporting-selection severity.)

## CLAIM 2 — the external magnitude recovers the correction strength (your own NMA + sim)
Build your OWN random-effects network meta-analysis of `dat.senn2013`, reference = "placebo":
  1. Reduce arms to study-level pairwise mean-difference contrasts: for each study, for each non-placebo
     arm t, TE = mi[t] - mi[placebo], seTE = sqrt(sdi[t]^2/ni[t] + sdi[placebo]^2/ni[placebo]). (If a
     study has no placebo arm use its first arm as the within-study reference.)
  2. Fit a random-effects NMA (any valid method: graph-Laplacian / electrical-network, or two-stage
     with a DerSimonian-Laird or REML tau^2). Obtain each active treatment's placebo-relative effect.
Map treatments to classes and lambda with this dict (unlisted -> lambda = 1, no correction):
  metformin->metformin, sitagliptin->DPP4, vildagliptin->DPP4, sulfonylurea->SU,
  pioglitazone->TZD, rosiglitazone->TZD, acarbose->AGI, miglitol->AGI, benfluorex->None, placebo->None
Truth-gate (known-truth simulation on the senn2013 geometry):
  - true placebo-relative effect d_true(t) = your fitted NMA effect for t.
  - For B in {0.0, 0.15, 0.30}, over ~400 replicates: simulate each contrast's TE as
    (d_obs(t1) - d_obs(t2)) + Normal(0, seTE), where d_obs(t) = d_true(t) * (1 + B*(1 - lambda_t))
    for active t (0 for placebo). Refit the NMA each replicate.
  - Score MCIW0 = 2 * 95th-percentile of |estimate - d_true| over all (replicate x active-treatment)
    cells, for three estimators of each treatment's effect md:
      unadjusted:  md
      oracle:      md * (1 - B     * (1 - lambda_t))
      external:    md * (1 - 0.158 * (1 - lambda_t))     <- the FROZEN external magnitude from Claim 1
  - Report dMCIW0 = MCIW0(estimator) - MCIW0(unadjusted) for oracle and external at each B, with a
    paired bootstrap 95% CI on dMCIW0 (resample the cell-level absolute errors).
EXPECT: at B=0.15 the external (0.158) dMCIW0 closely MATCHES the oracle dMCIW0 (both roughly -0.10 to
-0.12, i.e. both improve / "win"); at B=0 the external over-corrects slightly (dMCIW0 ~ +0.05, oracle ~0).

## Output
Print a table and write `verify_result.json` with:
  {"kappa_pooled":..., "corr":..., "classes_used":[...],
   "truthgate":{"0.0":{"oracle":...,"external":...}, "0.15":{"oracle":...,"external":...}, "0.30":{"oracle":...,"external":...}},
   "verdict":"CONFIRMS" or "DIVERGES", "notes":"..."}
Set verdict = CONFIRMS if kappa_pooled is ~0.13-0.18, corr is clearly positive (>0.3), and at B=0.15 the
external dMCIW0 is within ~0.03 of the oracle and both are negative (a win). Otherwise DIVERGES, and say
exactly which claim diverged and by how much. Be truthful — a divergence honestly reported is the point.
