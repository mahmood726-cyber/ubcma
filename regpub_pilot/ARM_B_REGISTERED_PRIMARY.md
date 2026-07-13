# Arm B — does the meta-analysis pool the trial's PRE-REGISTERED primary? (scaled)

**Date:** 2026-07-13 · built ON TOP of the fleet's Cochrane↔registry warehouse
(`C:\Projects\cochrane-vs-registry\`: `comparisons.json`, `links.json`, `aact.duckdb`) — Arm A is
theirs (0 transcription errors both sides; not duplicated). Pre-registration:
`PRE_REGISTRATION_synthesis_switch.md`. Two vendor families + hand-verification on every headline.

## ⚖️ FAIRNESS TO COCHRANE — held in every line
This is **NOT** a finding that Cochrane made errors. Cochrane pooled what the papers reported,
correctly and with dual independent extraction. The finding is about **the whole field's method of
starting from published papers**, of which Cochrane is the best practitioner. A registry-first
synthesis simply *sees* something a paper-first one cannot.

## The measurement
For 120 cleanly-comparable trial-cells (24 Cochrane reviews, 28 trials) where the fleet matched a
review-pooled outcome to a registry outcome, I compared what the review pooled against the trial's
**PROTOCOL-registered primary** (CT.gov `outcomesModule.primaryOutcomes` — the pre-specified
outcome, *what the trialists promised before seeing the data*). Note: the fleet's `aact_type` is the
*results-section* designation, which can itself be switched; the **protocol** primary is the correct
comparator (Mahmood: "from PROTOCOL onwards"). 32 (trial × pooled-outcome) cells classified.

| classification | agy/Gemini | Claude | consensus |
|---|--:|--:|--:|
| **MATCH** — pooled a registered PRIMARY | 25.0% | 34.4% | **25.0%** (both agree: 8/32) |
| **SWITCH** — pooled a registered SECONDARY | 28.1% | 31.3% | — |
| **NOVEL** — pooled an UNregistered outcome | 46.9% | 34.4% | — |
| TIMEPOINT | 0 | 0 | 0 |

**Headline (cross-vendored, hand-verified): the review pooled the trial's registered primary in
only ~25–34% of cells; 66–75% pooled a secondary or unregistered outcome.** Two-family concordance:
exact-class 87.5%, primary-vs-not 90.6% (the 4 disagreements are all agy-stricter near-synonym
calls; consensus-primary 25% is the conservative anchor). This is **not the pre-registered null** —
reviews do **not** mostly pool the registered primary.

### Hand-verified exemplars (each checkable: review · NCT · registered primary · pooled outcome)
- **NCT03389555** (CD002243): review pooled **28-day mortality**; registered primary was **SOFA score at 72 h** → SWITCH (mortality was a registered secondary; the trial was powered for SOFA).
- **NCT02025621** LEVO-CTS (CD013781): review labels "**Primary outcome: all-cause mortality**"; the registered primary was a **composite** (dual/quad efficacy endpoint) → NOVEL/COMPOSITE.
- **NCT02282293** (CD006689, **MALARIA**): review pooled **maternal peripheral parasitaemia**; registered primary was **placental malaria** → SWITCH. *(Arm B reaches malaria where the results-layer audit got 0 comparable cells — because the protocol needs only REGISTRATION, not results-posting. This is why Arm B succeeds exactly where Arm A could not.)*
- **NCT02164734** (CD008309): review pooled "**failure to place** LMA/ETT at first attempt"; registered secondary was "complications **during insertion**" → correctly kept NOVEL, not matched (the "placement ≠ insertion-complication" near-synonym trap the discipline flagged).

## What this means — and does NOT mean
- **Largely legitimate outcome-selection, not misconduct.** A Cochrane review defines its own
  clinically-important outcome (mortality, parasitaemia, hospitalisation); that outcome is
  frequently a *secondary* in the source trials — or, for review-level composites/constructs, not
  separately registered. Pooling it is standard, correct meta-analysis. It is **not** proof that
  trials switched, and **not** a Cochrane error.
- **The registry-first value is VISIBILITY + IMMUNITY, not a bigger number.** Only ~25% of pooled
  datapoints correspond to a pre-registered PRIMARY (high-confidence: powered, low-multiplicity);
  the other ~75% are secondary/unregistered (more exposed to selective reporting, multiplicity,
  under-powering). A registry-first synthesis can **annotate every pooled datapoint with its
  pre-registration status** — a GRADE/confidence signal invisible to a paper-first reviewer — and is
  **structurally immune** to the QRP subset where a trial's *reported* primary was switched from its
  registered one (the reachable rate for that subset is the trial-level **6.1%**, `OUTCOME_SWITCHING.md`).

## Arm B2 (the conclusion-flip counterfactual) — a CONSTRUCTIBILITY WALL, named
"Re-pool each review on the registered primary and count conclusion-flips" is **largely not
constructible at scale**: the trials within a review register **heterogeneous** primaries (SOFA /
composite / knowledge-scale / placental-malaria) that differ from the review's question and from
each other, so there is no shared registered-primary construct to re-pool. This is the same boundary
found earlier (Axfors: 23 trials, ~23 different primaries) — now confirmed across 24 reviews. **First
line for B2: the flip count cannot be computed where the prescription is not constructible; say so.**
Where it *is* constructible (reviews whose trials share a registered primary that equals the pooled
outcome — the 25% MATCH cells) re-pooling is by definition identical, so **0 flips there**. The
reviews where a flip could arise are exactly the ones where "pool the registered primary" has no
shared target — a named hard blocker, not a hidden null.

## Verdict vs pre-registration
- NOT the clean null (reviews pool the registered primary only ~25–34%).
- But the strong "reviews unknowingly pool switched primaries" reading is **qualified**: most of the
  75% is legitimate review outcome-selection, cross-vendor-supported. The **defensible, fair claim**:
  *registry-first synthesis makes the pre-registration status of every pooled outcome visible (only
  ~1 in 4 is a registered primary) and is immune to trial-level primary-switching (6.1%) — a paper-
  first reviewer, however careful, can guarantee neither.*

## Named hard blockers
- Arm B2 flip: not constructible where trials register heterogeneous primaries (most reviews); and
  where re-poolable it needs per-trial registered-primary EFFECTS (results-posting/extraction).
- Registration-date-vs-start red-flag: capture incomplete (wrong CT.gov date field) — a small gap to
  close, not run here.
- Scale beyond 24 reviews needs the full `pairwise70`→NCT join (the fleet's `links.json` covers 3027
  NCTs; only ~28 fall in cleanly count-comparable cells — the comparability bottleneck is Arm A's, not
  Arm B's; Arm B classification could extend to all 3027 links since it needs only registration).

## Artifacts
`out/armb_data.json` (comparisons + protocols), `out/armb_agy.txt`, `data/claude_armb.txt`,
`out/armb_agy.json`, `data/armb_classify.json`. Built on the fleet's `cochrane-vs-registry` warehouse.
