# Narrow & Deep vs Wide & Shallow — the four axes, counted (truth-first)

**Date:** 2026-07-13 · openly-accessible sources only · pre-registered (`PRE_REGISTRATION_axis1.md`).
Mahmood's reframe: we have FEWER outcomes than Cochrane but MORE data on every other axis.
Each axis is countable. Here is the count — including where the count REFUTES us.

## Axis 1 — more trials per (established) outcome → **REFUTED. NEAR-NULL. Reported loudly.**

The registry holds a large pool of completed, results-posted, **never-published** trials
(malaria **47**, TB **54**) — real, and invisible to a journal search. But discipline collapses it:

| step | malaria |
|---|--:|
| raw structurally-missable pool (completed + results-usable + non-published) | 47 |
| after keeping only an **efficacy** primary (drop safety/PK/immunogenicity) | 11 |
| hand + agy adjudicated → **standard drug, matchable to an existing efficacy review** | **1** |
| … novel-drug Phase-II (no review exists yet) | 3 |
| … not a treatment-efficacy trial (challenge/infectivity, safety-primary, PK) | 7 |

**Genuinely "an existing Cochrane efficacy review missed this" ≈ 1** (NCT00297882, artemether-
lumefantrine vs amodiaquine-artesunate, cure rate D28, 2009 — results posted, never published).
**Matcher false-positive rate ≈ 98%** — almost exactly the orphan-trial failure mode the
pre-registration warned against. Cross-vendor: agy/Gemini classified the 11 as 1 A / 3 B / 7 C,
**agreeing the standard-matchable count is 1.**

So on Axis 1's *strong* claim — "registry-k > Cochrane-k for the same established question" — we
are **at a near-null**: naive PICO counting over-states "Cochrane missed N" by ~20–50×. The
narrow-and-deep advantage is **NOT** raw trial-count-per-established-question.
The surviving, narrower, honest Axis-1 value: the registry surfaces unpublished **efficacy**
results for **emerging** antimalarials (SJ733, artefenomel, cipargamin, M5717) before/without
journal publication — useful to someone evaluating new drugs, but not "we beat Cochrane on count."
*Named blockers:* exact per-review non-overlap needs the `pairwise70` gold set (PICO + included
NCTs; `local_beae89ce`) + CDSR access — not in this tree; and modern Cochrane searches registries,
so "non-published" ≠ "review missed it", shrinking the count further.

## Axis 2 — more harms, and finer → **SUPPORTED (dominant).**
Registry serious-AE table present in **~99–100%** of results-posted trials (≥1 real event
56–79%), structured per arm; the abstract fails to **quantify** harms in **55–88%** of trials
(the "non-quantification gap", dominant across malaria/TB/T2D/onc). See `DISCREPANCY_TABLE.md`.

## Axis 3 — cleaner denominators → **SUPPORTED (directional).**
The registry results table carries `seriousNumAtRisk` / per-arm denominators structurally;
abstracts routinely omit them. Captured inside the routing-rule measurement (registry-table is
the sole route to the number 1.67–4.21× more often than the abstract prose). Not separately
hand-counted here — **named next step** (count denominator-present-in-registry / absent-in-paper).

## Axis 4 — no outcome switching → **SUPPORTED (measured).**
Confirmed primary-outcome switching **6.1%** (t2d 7.1%, onc 4.8%), hand-verified, agy 5/5, a
lower bound. We start from the pre-registered primary; a journal-based reviewer cannot. See
`OUTCOME_SWITCHING.md`.

## The honest Tuesday claim
Not "we beat Cochrane on trial count" — **we do not** (Axis 1 near-null; matcher FP ~98%). But:
**fewer outcomes, ~the same trials per established outcome, FAR more harms detail, cleaner
denominators, and a pre-registered target that cannot be silently switched — and here is the
count for each, including the axis where we lose.** Narrow-and-deep is real on harms, switching,
and denominators; it is a null on raw trial count. That distinction is the credible slide.

## Artifacts
`out/axis1_narrow_deep.json`, `PRE_REGISTRATION_axis1.md`, `DISCREPANCY_TABLE.md`,
`OUTCOME_SWITCHING.md`. DTA70 synthetic set verified ABSENT from this lane.
