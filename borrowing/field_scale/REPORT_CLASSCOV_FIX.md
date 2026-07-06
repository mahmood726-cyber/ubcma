# Class-covariate prototype: does a leakage-free drug-class term close the cold-transfer method gap?

**Status: prototype + mechanism check (isolated; the shipped `field_learned.py` is UNCHANGED).**
Builds directly on `REPORT_DONOR_CEILING.md`, which decomposed the cold-transfer negative into a
**method** component (the specialty+precision+year kernel routes only 37% of the cold gap even when
a level-matched same-class donor is injected) and named the concrete fix target: *a leakage-free
class/effect-level covariate so the field can route a novel MA's level from a same-class donor
WITHOUT the ma-identity match.* This report tests that fix target directly.

## What was built (isolated from the shipped estimator)
- `field_classcov.py` — the committed grouped-ARD GP with ONE added dimension: a class-match term
  `1[cls_s != cls_t]/l_cls^2` with its own marginal-likelihood-fit length scale. The class label is
  parsed ONLY from the MA-name metadata (`aact_<condition>_<drugclass>`), never from the effect yi →
  leakage-free. Two grains: **drug** (the drug-class token) and **cond** (the therapeutic-area token).
  With `l_cls → ∞` the kernel reduces exactly to the committed 4-group kernel, so at the ML optimum
  the added term cannot hurt the fit (up to local optima).
- `donor_ceiling_classcov.py` — the SAME deterministic donor/test split and within-MA reference as
  `donor_ceiling.py`, run under 3 kernels × 4 arms (A cold_nodonor / B cold_sibling / C warm_sibling /
  D scrambled-control), plus a corpus-wide honest-k-fold **regression gate** (added feature must not
  worsen the committed MAE by >2%).
- `donor_ceiling_classcov_witness.py` — an INDEPENDENT engine (Nadaraya-Watson kernel average,
  GP-free, zero shared estimator code) that re-derives the decisive GLP1 claim.

## Pre-declared hypotheses / decision rule
- **H1 (drug-class is the fix mechanism):** under the drug grain, arm B (sibling present as a DISTINCT
  ma-code, so the ma-match term does NOT fire) recovers toward arm C — the held-out GLP1 posterior
  moves from the specialty/precision/year-only value (~+1.1) toward the sibling level (+2.9).
- **H2 (grain matters):** the condition grain does NOT recentre GLP1 (a therapeutic-area match averages
  insulin +0.19 … glucagon +3.18, so it cannot isolate the extreme MA). ⇒ the actionable fix is a
  **drug-class/mechanism grain**, not a therapeutic-area grain.
- **Guard:** the scrambled negative control (D) must NOT recover under any grain (else the term is just
  adding neighbours, not matching level).
- **Regression:** corpus MAE with the added feature must not worsen the committed MAE by >2%.

## Result — independent Nadaraya-Watson witness (RAN, confirms direction)
GLP1 test-half true level **+2.90**. GLP1 arm-B posterior by grain:

| engine | none | cond | drug | warm-C (drug) | scrambled-D (drug) |
|---|---|---|---|---|---|
| Nadaraya-Watson (GP-free) | +0.56 | +0.73 | **+1.24** | +3.06 (≈true) | +0.54 (no recovery) |

→ the drug-class term **>2×** the B posterior vs the committed kernel; the condition grain barely
moves it; the scrambled donor does not recover. **H1, H2, and the guard all hold in an independent
model family.** (NW under a fixed mismatch penalty only partially recovers B, +1.24 not +2.9, because
it blends the matched sibling with the lower-level same-area neighbours; the GP, which LEARNS l_cls,
is expected to recover more — see below.)

## Result — primary grouped-ARD GP  (donor_ceiling_classcov_results.json)

Δ vs within-MA on the SAME test-half rows (+ = learned loses to within); recovery = (dA−dB)/(dA−dC):

| kernel | dA cold | dB sibling | dC warm | dD scrambled | recovery frac | GLP1 B-post | GLP1 C-post |
|---|---|---|---|---|---|---|---|
| none (committed) | +0.1084 | +0.0523 | −0.0444 | +0.1356 | **0.37** | +1.12 | +3.11 |
| cond | +0.1395 | +0.0740 | −0.0611 | +0.1454 | **0.33** | +1.23 | +3.06 |
| drug | +0.1165 | **−0.0631** | −0.0611 | +0.1325 | **1.01** | **+2.98** | +3.14 |

**Decisive readings:**
- **drug grain recovers the ENTIRE cold gap** — recovery fraction 0.37 → **1.01**. Arm B (the
  level-matched sibling present only as a DISTINCT ma-code, so the ma-match term never fires) now
  reaches dB **−0.0631**, statistically indistinguishable from the exact-identity warm bound dC
  −0.0611. A leakage-free drug-class term routes the level as well as knowing it is literally the
  same MA.
- **GLP1 held-out posterior +1.12 → +2.98** ≈ true **+2.90**. The extreme MA that drove the whole
  cold-transfer negative is now correctly recentred WITHOUT the ma-identity match.
- **Grain matters (H2):** the condition grain barely moves it (rec 0.33, GLP1 B +1.23) — a
  therapeutic-area match averages insulin +0.19 … glucagon +3.18 and cannot isolate the extreme MA.
  The actionable covariate is a DRUG-CLASS / mechanism grain, not a therapeutic-area grain.
- **Guard holds:** scrambled control dD +0.1325 ≈ cold dA +0.1165 → no recovery when the donor is at
  the WRONG level. The active ingredient is genuine level matching, not extra neighbours.

Corpus regression gate (honest 10-fold, 3-seed): committed MAE **0.3343**;
+class[cond] 0.3343 (**+0.00%**); +class[drug] 0.3343 (**+0.00%**). Gate ≤2% → **PASS**. The class
feature is INERT on the standard corpus (drug classes are mostly singletons there, so l_cls is
redundant with l_ma and the ML fit ignores it) yet fully recovers the cold-donor scenario — the
desired "help when a same-class donor exists, harmless otherwise" property.

Pre-declared verdict (from the JSON): **H1 True, H2 True, guard True.** Both the GP (this table) and
the independent Nadaraya-Watson engine (above) agree on direction; the GP quantifies full recovery.

## Honest caveat (truth-first — this is a MECHANISM check, not a deployment payoff)
The injected sibling is the SAME MA split in half, so it sits at the test half's EXACT level. This is
an **upper bound** on the class-covariate benefit: it answers *"can the GP route level via a
leakage-free class term at all?"* — not *"how much does it help in deployment?"*. Real payoff is
bounded by (a) how close a genuine same-drug-class donor's level is to the novel MA, and (b) corpus
coverage (whether such a donor exists at all — the original ceiling). The corpus here has exactly one
genuine multi-MA drug class (`antibodies`, spanning 3 conditions at different levels), so the
cross-MA generalisation of `l_cls` is under-identified from this slice and should be re-checked on a
larger AACT expansion with several real same-drug-class MA pairs before any promotion. **This
prototype does NOT modify the shipped estimator and is NOT a promotion.**

## Suggested next step (for owner + witness)
If the GP confirms H1/H2 and the regression gate passes, the promotable form is a leakage-free
drug-class / ATC-5 / mechanism embedding added to `field_learned.build_features` (a real registry
covariate, not the split-derived class token), re-run arm B on a larger slice with genuinely distinct
same-class MA pairs, and route through the same multi-engine + external-vendor witness gate the
donor-ceiling headline used. Codex witness task W5 (`codex-witness-tasks-2026-07-06.md`) re-derives
the GLP1 B-posterior with an independent GP engine.
