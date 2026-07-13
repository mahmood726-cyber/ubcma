# Outcome Switching at Scale, from Free Sources — the landmark measurement

**Date:** 2026-07-13 · **Branch:** `wip/preserve-2026-07-12` · local only, no push.
Registry pre-specified primary vs the paper's DECLARED primary (from open-access full-text
methods). Openly-accessible sources only (CT.gov + Europe PMC JATS). Every asserted switch is
individually checkable; every one was hand-verified AND cross-vendored before it counted.

## Why this is the sharpest form of "more truthful, not merely as good"

> **A well-resourced reviewer with full Embase access can pool a switched outcome without ever
> noticing. We cannot — because we start from the registered protocol. The rule "pool the
> pre-registered primary outcome" is simultaneously what is achievable from open sources AND
> more rigorous than standard practice. The constraint becomes the discipline.**

## The measurement (hand-verified + cross-vendored)

| Disease | trials w/ FT methods | scored* | raw LLM flags | **confirmed switches** | **rate** |
|---|--:|--:|--:|--:|--:|
| cardiometabolic (T2D) | 70 | 28 | 2 | **2** | **7.1%** |
| oncology | 41 | 21 | 3 | **1** | **4.8%** |
| **pooled** | 111 | **49** | 5 | **3** | **6.1%** |

\* *scored* = trials whose open-access full text actually declares a primary outcome we can
read. ~45% of FT trials abstained (the OA text is a protocol paper, an author manuscript
without a methods primary, or atypical phrasing) — honest exclusions, not switches.

**Confirmed primary-outcome switching is ~6% (3/49).** All three are demotions/promotions:
- **NCT01719640** — registered primary *macro/microvascular complications*; paper's declared
  primary *C-peptide AUC at 1 year*.
- **NCT02703337** — registered primary *pharmacokinetic insulin-lispro AUC*; paper's primary
  *glucodynamic response* (borderline; PK/PD studies often co-primary).
- **NCT01123902** — registered primary *severity of breathlessness*; paper's primary *use of a
  hand-held fan + wristband* (clinical endpoint demoted to a behavioural one).

Each is checkable: `out/switch_adjudication.json` carries `clinicaltrials.gov/study/<NCT>#outcomes`
+ the verbatim methods span for both values. Full per-trial output: `out/switch_<area>.jsonl`.

## Discipline mattered — the raw rate was ~2× inflated
The raw LLM flag rate (onc 14.3%) **halved to 4.8%** on hand-verification: 2 of 3 oncology flags
were **false positives** — a POLO-trial **HRQoL companion paper** (index-paper-is-secondary
confound) and **inverse phrasing** ("success rate" = complement of "recurrence", same concept).
**agy/Gemini (decorrelated google family) independently reproduced all 5 verdicts — 3 SWITCH,
2 NO-SWITCH — 5/5** (`out/switch_agy_crosscheck.json`). No rate rests on an unverified matcher.

## Three-way agreement — the abstract-spin hypothesis, tested and REFUTED for this phenomenon
Hypothesis (from our own priors): the ABSTRACT would be the odd layer out. **For outcome
switching it is not.** In every confirmed switch, the abstract agrees with the paper's full
text (both report the switched primary); it is the **REGISTRY that differs** — and the registry
is the *truthful* layer, because it holds the pre-specified primary the paper abandoned. So
"odd one out" ≠ "wrong one out": the pre-registration is the anchor, exactly the point of the
method. (Abstract-vs-full-text *spin* — a different phenomenon, within-paper emphasis — is a
separate measurement not run here; **named next step**.)

## Does OUR result change?
At ~6% switching, for a typical meta-analysis (k = 5–20) 0–1 included trials are affected, so
the pooled point estimate rarely flips — **a credible null on "the number moves often."** The
value is not frequent flips; it is **un-foolability**: the switched trial is precisely where a
full-Embase reviewer pools the *published* (switched) primary without noticing, while we start
from the registered primary and flag it. Rare, but exactly the case standard practice misses.

## Honest limitations / named blockers
- **Lower bound.** We compare the CURRENT registry primary (CT.gov v2 public API exposes no
  per-field registration-time history — **named hard blocker**; the strict COMPare comparator
  needs WHO ICTRP / archived snapshots). Trials whose registry was retro-edited to match the
  paper are counted concordant → true switching is higher than 6%.
- **FT-gated + OA-methods-limited.** ~45% of FT trials give no readable declared primary.
- **Cardiometabolic + oncology only.** Malaria/TB/HIV switching is **blocked** on the fleet's
  OA-index scan for those areas (their `fetch_fulltext` errors without `oa_index_records` for
  malaria/TB — I did not rebuild their acquisition cascade). Once that scan runs, this pipeline
  extends unchanged (`PILOT_AREA=<area> python outcome_switch.py batches/fuse`).

## Artifacts
`out/switch_table.json`, `out/switch_adjudication.json`, `out/switch_agy_crosscheck.json`,
`out/switch_{t2d,onc}.jsonl`, `out/switch_summary_{t2d,onc}.json`, `src/outcome_switch.py`.
