# Pre-registration — does the published meta-analysis pool the trial's PRE-REGISTERED primary?

Written BEFORE running. This result would flatter us, so the refutation is fixed first and the
anti-sycophancy gate is explicit: ≥2 distinct vendor families + this criterion before any headline.

## The claim
A meta-analysis built from the REGISTERED protocol is structurally IMMUNE to outcome switching.
A paper-first reviewer pools what the paper calls primary — which the trial may have changed after
seeing the data — and cannot detect the switch, because the evidence of it is in the registry, not
the paper. Measurement: how often does a published review pool an outcome that is NOT the trial's
pre-registered primary?

## What would REFUTE the claim (state the null loudly if it happens)
- **If reviews MOSTLY pool the registered primary** (MATCH ≥ 80% of adjudicable trial-cells), then
  registry-first is NOT meaningfully better on this axis. **That is a clean null and it retires the
  claim — it goes in the FIRST LINE.**
- **If the conclusion NEVER flips** when we re-pool the registered primary, switching is real but
  *inconsequential*: report that — it downgrades the claim from "changes answers" to "changes
  provenance," a weaker (still valid) version.
- **If our matcher's false-positive rate is high** (coincidental value-matches, near-synonym
  outcomes, bad trial→NCT links), the raw switch rate is worthless and only the hand-verified count
  may be quoted. Assume OUR linkage is wrong before assuming the review is.

## Classification (per included trial-cell in a review)
- **MATCH** — the review pooled the registered primary (same construct + timepoint).
- **SWITCH** — the review pooled a registered SECONDARY.
- **NOVEL** — the review pooled an outcome NEVER registered at all.
- **TIMEPOINT** — right construct, different timepoint from the registered primary (look for it
  specifically; sneakiest).
- **COMPOSITE** — the review built a composite not in the protocol.
- **NOT ADJUDICABLE** — say why (no registered outcome; ambiguous; unmappable).

## Matcher discipline (fail closed)
- Trial→NCT link must match on trial identity (name + sample size + condition), never numeric
  proximity. A bad link is worse than none (`shep 1991` → two trials, 2,365 vs 3 patients). Report
  the link matcher's false-positive rate, hand-verified.
- Registered primary from CT.gov `protocolSection.outcomesModule.primaryOutcomes` (`Primary`), with
  its **registration date vs the trial start date** captured (a primary registered AFTER enrolment
  began is itself a red flag).
- Near-synonyms are NOT matches unless the construct is identical. Hand-verify EVERY asserted
  SWITCH/NOVEL/TIMEPOINT before it counts. Cross-vendor (agy-Gemini + Codex if reachable).

## Reporting (non-negotiable deliverable)
Switch / Novel / Timepoint / Composite rates **with their denominator**; the **conclusion-flip
count** (re-pool registered primary vs the review's published estimate); the **matcher FP rate**;
every asserted case individually checkable (review · trial · NCT · registered primary · pooled
outcome · registration date · both locators). Prioritise malaria/TB/HIV. NOTE: the registered
outcome requires only REGISTRATION, not results-posting — so this measurement can reach diseases
where the results-layer audit found zero comparable cells; report whether the protocol layer is
reachable there.

## Named-blocker honesty
This requires (a) the review's pooled outcome + its included-trial list (`pairwise70`, 374 reviews,
`local_beae89ce`) and (b) a trial→NCT link layer (`local_b9ba3a2f`). If neither is reachable in this
tree, that is the named hard blocker and the measurement cannot run at scale — say so plainly rather
than fabricate a rate.
