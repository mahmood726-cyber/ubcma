# Pre-registration — harms-omission, routing rule, coverage (malaria + TB)

Written BEFORE running the harms analysis. Discipline: a null is publishable; a hyped
result is worthless. Each claim below states exactly what would REFUTE it. Recorded so the
result cannot be moved to fit a desired conclusion (eight retractions came from wanting the
result; the orphan thesis was a clean null — do not rebuild it by another route).

## Definitions (fixed now, not after seeing data)

- **Registry has serious-AE data** := `resultsSection.adverseEventsModule` present AND at
  least one `eventGroups[]` entry has a non-null `seriousNumAffected` (structured serious
  adverse event counts per arm). This is the registry "harms table".
- **Abstract harms mention** := the abstract text matches any harms lexicon term
  (adverse event/effect, side effect, safety, tolerab*, toxicit*, serious adverse, SAE,
  grade 3/4, discontinuation due to, death/mortality-as-harm, withdrawal due to AE).
- **Abstract harms quantified** := a harms term co-occurs with a number/percent in the same
  sentence (e.g., "grade 3–4 events in 12%").
- **Harms omission (contradiction)** := registry HAS serious-AE data AND the abstract is
  **silent** on harms (no mention at all). Diffable denominator = trials with registry
  serious-AE data AND a databank-confirmed index abstract.
- **Harms under-report (weaker gap)** := registry has serious-AE data, abstract mentions
  harms but does NOT quantify them.

These are *reporting-asymmetry* measures, not misconduct claims. An abstract is space-limited;
the honest statement is "the registry harms table is machine-readable and the abstract often
is not," which is exactly the routing point.

## Claim H — harms omission is the dominant discrepancy class

- **Supported** iff, over the diffable denominator, harms-omission rate is (a) ≥ 40% AND
  (b) strictly higher than every efficacy-numeric discrepancy class (enrollment, direction,
  significance) measured on the SAME disease.
- **REFUTED** if harms-omission rate < 40%, OR if any efficacy-numeric class has an
  equal-or-higher confirmed contradiction rate, OR if registry serious-AE completeness among
  results-posted trials is < 80% (then the premise "registry documents harms" fails).
- **Guard against inflation:** if the abstract is a conference abstract or a
  protocol/design/rationale paper (no results), it is EXCLUDED from the denominator — such an
  abstract legitimately has no harms. Also report the weaker "under-report" rate separately;
  do not merge it into the omission headline.

## Claim R — route to the registry table, not the abstract prose

- **Supported** iff, among poolable trials (a usable primary number exists somewhere), the
  fraction where the number is available in the **registry results table but NOT usably in
  the abstract prose** is ≥ 2× the reverse fraction (usable in abstract but not registry).
- **REFUTED** if abstract-prose yields the usable number as often as or more often than the
  registry table (ratio < 1.5×), i.e. prose is an equally good route.

## Claim C — malaria/TB have a coverage advantage over cardiometabolic/oncology

- Must specify the AXIS; do not cherry-pick.
- **Publication-linkage axis:** supported iff malaria/TB reporting-pub coverage > T2D and
  oncology. (Prior data: malaria 66% vs T2D 45%, onc 37.4% — likely supported.)
- **OA full-text axis:** supported iff malaria/TB open-access % (of linked pubs) > a
  cardio/onc comparison run on the same EPMC probe.
- **Abstract-usability axis — PRE-REGISTERED EXPECTATION OF REFUTATION:** malaria abstract
  usability is 17.6% (already observed) which is LOWER than T2D 28.5%. So on the
  abstract-usability axis the coverage-advantage claim is **expected to be REFUTED** — malaria/TB
  abstracts are MORE relative-only/median-only. This must be reported, not hidden. The
  advantage (if any) is on linkage/OA, not on abstract usability.

## Calibration / process guards
- k<10 pooled comparisons flagged; no headline rests on a k≤5 slice (CO2-lane R²≈1.0 was a
  k=5 boundary artefact).
- Hand-validate a harms sample (registry-says-SAE / abstract-silent) by reading both — confirm
  the abstract truly omits harms and the registry truly has them, before believing the rate.
- Cross-vendor the harms headline with a second family (agy→Gemini) if the pool is live; if
  not, report the internal number and name the vendor blocker. Do not block on a dead pool.
