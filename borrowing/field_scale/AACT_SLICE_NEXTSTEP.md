# Designed next-step: a bounded real-AACT out-of-corpus generalisation slice

**Status:** designed + data-sourced, deliberately NOT rushed this overnight session.
**Why deferred (truth-first):** a meaningful learned-kernel test needs the AACT trials
grouped into *coherent* meta-analyses (same condition × same intervention class × same
outcome), and doing that grouping cleanly cannot be rushed without risking a heterogeneous,
semantically meaningless "slice" — a wrong/misleading number is worse than no number. This
note fixes the exact clean recipe so a dedicated session can execute it deterministically.

## The question it answers
The committed headline (learned-kernel GP + conformal, `benchmark_learned.py`) shows the
learned kernel beats within-MA borrowing **inside** the 28-MA / 1177-node corpus
(−0.0230 [−0.0340, −0.0117], reproduced by an independent sklearn engine −0.0241 and — this
session — externally by Codex Seat A). Open question: does that advantage **transfer to a
cold, fresh slice whose `ma` is NOT in the training corpus**? On a new `ma` the learned
kernel cannot use its `ma`-kernel term, so it must generalise via `specialty` + precision +
year alone. This is a genuine external-validity probe, and an **honest null is an acceptable
outcome** (it would simply bound the headline to in-corpus reconstruction).

## Clean data recipe (no arm-labeling risk)
Source: `F:/AACT-storage/AACT/2026-04-12/` (full pipe-delimited snapshot, 2026-04-12).

1. **Effects from sponsor-reported analyses, not re-derived from arms.** Read
   `outcome_analyses.txt`; keep rows with `param_type` in {`Odds Ratio (OR)`, `Odds Ratio`}
   AND a 2-sided 95% CI present (`ci_percent≈95`, both `ci_lower_limit`/`ci_upper_limit`
   numeric, `ci_n_sides`=2). Then
   `yi = log(param_value)`, `se = (log(ci_upper) − log(ci_lower)) / (2·1.959964)`.
   ~18k such rows exist. This avoids the CT.gov arm-labeling trap entirely (the effect and
   its CI are taken verbatim; the extraction is self-verifying — recompute the CI back from
   yi±1.96·se and assert it matches the reported CI to rounding).
2. **Family = LOR** (matches the corpus LOR family; never mix families).
3. **Coherent MA grouping (the careful part).** Join `nct_id`→`browse_conditions` (MeSH)
   and `browse_interventions`; define a candidate MA as (MeSH condition term × intervention
   class) with **k ≥ 8** contributing trials. Keep only groups whose members share one
   outcome direction (drop mixed efficacy/safety within a group). Assign `specialty` from the
   MeSH condition via the same map used to build the corpus (`corpus.py`). `year` = study
   `start_date` year (standardised, missing→0), matching the corpus feature contract.
4. **Sanity filters:** |yi| ≤ 5, 0.01 ≤ se ≤ 3, drop non-finite; cap any single MA at its
   natural k (no synthetic replication). Log every dropped group with its reason (no silent
   truncation).

## Test protocol (reuse existing gate, no new machinery)
- Append the qualifying slice(s) as **held-out** `ma` blocks to the 1177-node corpus.
- Run the committed learned-kernel field (`field_learned.py`, honest k-fold with per-fold
  hyper-parameter refit) and the within-MA baseline **restricted to predicting the held-out
  AACT rows** (train on corpus + other slice members, predict each held-out AACT trial).
- Report per-slice and pooled `learned − within_MA` MAE with a paired-bootstrap CI, plus the
  conformal coverage on the held-out slice. **Win / null / negative — whichever is true.**
- Cross-verify the extraction (CI round-trip) and the headline delta on ≥1 external engine.

## Integrity notes
- All numbers come from AACT's own reported `outcome_analyses` estimates + CIs; nothing is
  hand-transcribed from papers and no effect is re-derived from raw counts.
- Expected caveat to disclose: AACT effect gradients are compression-biased (pilot-4), and a
  cold new-`ma` slice is the hardest regime for the learned kernel — so a modest or null
  transfer result would NOT contradict the in-corpus headline; it would delimit its scope.
