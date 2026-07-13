# Does a published meta-analysis pool the trial's PRE-REGISTERED primary?

**FIRST LINE (per pre-registration, because this result flatters us):** the dramatic version of
the claim — "reviews unknowingly inherit outcome switching" — is **NOT demonstrated by the
reachable evidence.** The one measurable review pooled the registered primary in only 35% of its
trials, but that 65% "non-primary" is the **benign, by-design behaviour of an outcome-specific
meta-analysis** (cross-vendor confirmed), **not** QRP outcome switching. Reporting it as switching
would be the exact "wanting the result" trap the discipline exists to stop.

## What was measurable
Scale needs `pairwise70` (374 reviews + included NCTs; `local_beae89ce`) — **not in this tree**.
The open-source `metadat` R package carries only **3** NCT-linked meta-analyses, of which only
**Axfors 2021** (HCQ/CQ mortality in COVID-19) has enough linked trials (23) to measure. Trial→NCT
links are **curated in metadat**, so linkage false-positives ≈ 0 (the `shep 1991` trap does not
apply here). openly-accessible sources only.

## The measurement (Axfors 2021, pooled outcome = all-cause mortality, n=23 linked trials)

| classification (was pooled mortality the trial's…) | n | % |
|---|--:|--:|
| **registered PRIMARY** (MATCH) | 8 | 34.8 |
| registered **SECONDARY** (SWITCH) | 8 | 34.8 |
| **NOVEL** — not a registered outcome at all | 7 | 30.4 |
| TIMEPOINT switch | — | n/a (mortality has no timepoint variants) |

Hand-verified: 22/23 classifications correct on inspection (COVID HCQ trials overwhelmingly
registered *viral-clearance* or *clinical-status* primaries; mortality was secondary or absent).
One MATCH is borderline (NCT04261517 shows virological primaries). Each case is checkable in
`out/axfors_switch.json` (NCT · registered primary · class · registration/start dates).

## Why the raw 65% is NOT the headline — the two disciplined findings
1. **Benign, by design.** Axfors 2021 is a *deliberately mortality-specific* pooled analysis — it
   chose mortality precisely because individual COVID trials were underpowered for it. Pooling an
   outcome that was a *secondary* in the source trials is legitimate, standard meta-analysis, not a
   QRP. **agy/Gemini, asked blind: "BENIGN-OUTCOME-SPECIFIC," not "SWITCHING-EVIDENCE."**
2. **Boundary condition of the prescription.** The 23 trials registered ~23 **different** primaries,
   so you literally **cannot** "pool the pre-registered primary" across them — you must pick one
   outcome. **agy/Gemini: "NO-HETEROGENEOUS-PRIMARIES."** So "pool what was promised" is inapplicable
   exactly when the promises differ trial-to-trial. The **conclusion-flip test is therefore
   undefined here** — there is no single registered primary to re-pool.

## What actually survives
- **The clean QRP outcome-switching signal is the TRIAL-LEVEL measurement** (registry primary vs the
  primary the *paper* reported as primary) = **6.1% confirmed** (`OUTCOME_SWITCHING.md`, hand-verified,
  agy 5/5). Registry-first is structurally immune to **that** — the defensible validity claim.
- **A modest, honest transparency gain:** registry-first makes the per-trial registration status of
  a pooled outcome **visible** (here 35% primary / 35% secondary / 30% unregistered). That informs
  GRADE/confidence — most trials weren't designed for the pooled outcome — but it is an annotation,
  not "we catch cheating they can't."

## Verdict vs pre-registration
Not the clean null (reviews don't *mostly* pool the registered primary — 35%), but the **strong
switching-inheritance claim is refuted/qualified**: the evidence is benign outcome-specific pooling,
cross-vendor confirmed. The honest Tuesday sentence contracts to what it can carry:
**"registry-first is structurally immune to *trial-level* outcome switching (6.1%), and makes the
registration status of every pooled outcome visible"** — not "reviews pool switched outcomes most
of the time."

## Named hard blocker
The scaled version (switch/novel/timepoint rates across many reviews, with conclusion-flips) needs
`pairwise70`'s review-pooled-outcome + included-NCT table (`local_beae89ce`), not in this tree, and
a per-trial paper-reported-primary layer to separate benign outcome-specific pooling from QRP
inheritance. Until then only the trial-level 6.1% and this single-review probe are defensible.

## Artifacts
`out/synthesis_switch.json`, `out/axfors_switch.json`, `src/dump_metadat.R`,
`PRE_REGISTRATION_synthesis_switch.md`. DTA70 verified absent.
