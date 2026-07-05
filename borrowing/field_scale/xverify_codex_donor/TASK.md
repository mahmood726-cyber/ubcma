You are an INDEPENDENT numerical witness. Work only in this directory. A dataset is at ./data.csv.

Columns: ma, specialty, yi (log-odds-ratio effect), se (standard error), year, is_aact (1=held-out registry MA, 0=base corpus), split_role (donor|test|none). There are 524 nodes: a base corpus (is_aact=0, role=none) plus 13 held-out registry meta-analyses (is_aact=1), each split into disjoint donor and test halves.

Implement, FROM SCRATCH IN YOUR OWN WAY (your choice of estimator: Gaussian process, kernel-weighted average, k-NN regression, anything), a LEAKAGE-FREE cross-MA predictor of yi. Features must be ONLY: standardized year, standardized log-precision (log(1/se^2)), specialty (categorical), ma (categorical). A node's own yi must NEVER enter its own features.

Predict the TEST-half rows of each is_aact=1 MA m under two regimes:
  A (no donor):  train on all rows with ma != m (exclude BOTH donor and test halves of m). Predict m's test half.
  B (sibling):   relabel m's DONOR-half rows to ma = m+"__sib" (a NEW distinct category), keep them in training; hold out ONLY m's test half (label m). Predict m's test half. (So the level-matched donor is present but its ma category does not match the test rows -> only specialty/precision/year can route to it.)

Also compute a within-MA baseline: each test node predicted by the precision-weighted (1/se^2) mean of its OWN full-MA siblings (all other rows sharing its original ma).

Report ONLY a JSON object to ./witness_out.json with keys:
  A_delta   = pooled MAE(regime A) - MAE(within) over all test rows
  B_delta   = pooled MAE(regime B) - MAE(within) over all test rows
  glp1_true = mean yi of test half of ma "aact_diabetesme_glucagon-l"
  glp1_A_post = mean predicted value on that test half under A
  glp1_B_post = mean predicted value on that test half under B
  verdict   = one sentence: does injecting the level-matched GLP1 donor (donor mean ~+3.47) let the field recentre the held-out GLP1 test half (true ~+2.90) under B? yes/no and why.

The scientific question: can a specialty+precision+year kernel route EFFECT LEVEL to a held-out MA when a level-matched same-specialty donor exists? Print the JSON to stdout too.
