# Pre-registration — Axis 1: more trials per outcome (narrow & deep)

Written BEFORE running the matcher. The orphan-trial study was a clean NULL (47.9% false
positive on naive PICO linkage). Naive PICO matching WILL over-match. This file fixes the
acceptance criteria and the refutation so the count cannot be moved to fit the desired result.

## The claim being tested
For a given Cochrane review's question, the registry holds **completed, results-posted trials
that were never published in a journal** — trials a journal-based reviewer structurally cannot
find. So the registry-available evidence base can be LARGER than the review's.

## Definitions (fixed now)
A registry trial is a **structurally-missed candidate** for a review iff ALL hold:
1. `overallStatus == COMPLETED`.
2. Results posted on the registry (`hasResults`) with a usable primary outcome.
3. **Non-published**: no journal publication linked (no RESULT-type reference and no PubMed
   `[si]` databank link) AND a targeted title/drug PubMed search finds no matching paper
   (the active-search check, to control the databank-miss false-positive from prior lanes).
4. **PICO match on ALL five axes** (not numeric proximity):
   - condition matches the review's condition,
   - intervention is the review's intervention (specific drug/agent, not class-adjacent),
   - comparator is within the review's allowed comparators,
   - the trial reports the review's primary OUTCOME,
   - population matches (adult/child, line of therapy, disease severity).
5. Completed within the review's search window (not after the review's last search date) —
   otherwise it is a *temporal* addition, NOT a structurally-missed trial. Temporal additions
   are reported SEPARATELY and never counted as "Cochrane missed it."

## Procedure
1. For each review: record Cochrane k, PICO, and last-search date from the review.
2. Query the registry for completed + results-posted trials matching the PICO.
3. Apply criteria 1–5. **Hand-verify EVERY surviving candidate** by reading its registry record
   (condition, intervention, comparator, outcome, population, dates) + confirming non-publication
   by active PubMed search.
4. Report the matcher's **false-positive rate**: of raw PICO-query hits, what fraction fail
   hand-verification. A rate is only reported after this subtraction.

## What would REFUTE the claim
- If, after hand-verification, the count of genuinely structurally-missed trials is **0** for a
  review, report **0** — that review's evidence base is complete and the claim fails there.
- If registry-available k is **≤ Cochrane k** for a review, report that (LOUDLY) — narrow-deep
  loses on the trial-count axis there.
- If the matcher FP rate is high (>50%, like the orphan study), the naive count is worthless and
  only the hand-verified count may be quoted.

## Reporting
Per review: **Cochrane k / registry completed+results-posted matched / hand-verified
structurally-missed / their combined N / does the pooled estimate change / matcher FP rate.**
Cross-vendor the missed count (agy-Gemini + Codex if reachable). A null is publishable; a hyped
count is worthless. Scale beyond the pilot requires the `pairwise70` gold set (machine-readable
PICO + included-trial NCTs), owned by `local_beae89ce` — named blocker if unavailable.
