# Registered-vs-Published Discrepancy Engine — Feasibility Pilot Report

**Date:** 2026-07-07 · **Branch:** `pilot/regpub-discrepancy` · **Dir:** `F:\ubcma\regpub_pilot`
**Status:** staged results only — no push / deploy / merge. Read-only external data.

---

## 0. Mission frame (drives every design choice)

Target user: a scientist in a developing country with **no paywalled full-text access**.
The engine must therefore run on **openly-accessible data only** — PubMed **abstracts** +
ClinicalTrials.gov / AACT **registry**. No local AACT dump was needed or found; we use the
**live CT.gov API v2**, which is the same data a no-institution scientist can actually reach
for free. Everything is measured against *"what can be verified/pooled from abstract + registry
alone."*

**Scope (first cut):** 600 completed **interventional type-2-diabetes** trials (densest CT.gov
results coverage), sampled from CT.gov API v2. NCT↔PMID linkage via two independent channels
(CT.gov references + PubMed `[si]` reverse-databank).

**Deterministic-core seam honoured:** the only network use is data *acquisition* (cached to
disk). All extraction / diff / pooling / structural checks are pure, model-free,
offline-serializable functions (`extract.py`, `diff.py`, `metrics.py`) — same input → same
output, no model in the classification path.

---

## 1. Headline numbers

| Deliverable | Result |
|---|---|
| **Abstract-extraction usability rate** | **28.5%** deterministic → **39.6%** with the LLM-assisted layer (§1b); 100% of emitted datapoints source-linked |
| **Registry-results coverage** | **28.8%** of completed trials post results; **94.8%** of *those* are usable → **27.3%** of all completed trials have usable registry results |
| **Combined poolable yield (the "better at scale" core)** | **33.7%** (202 / 600) poolable when registry **and** abstract are fused, vs **11.2%** (67/600) from abstracts alone — abstracts add **38** trials registry misses; registry adds **135** abstracts miss |
| **Only discrepancy class with genuine signal** | **Non-publication**: 55% raw flag rate, hand-adjudicated precision **≈0.67** → bias-corrected true non-publication **≈35–40%** |
| **Intra-trial numeric discrepancy classes** | Endpoint-switch / enrollment / direction / significance: **~0 confirmed true positives** on the validated sample — dominated by artifacts (see §5). Honest GAP. |

**One-line verdict:** the "better at scale" demonstration **holds for pooling feedstock and for
non-publication screening**, but **fails (honestly) for fine-grained numeric contradiction
detection** — that provably needs the full-text methods section the mission's abstract-only
constraint forbids.

---

## 1b. LLM-assisted extraction layer (added 2026-07-07) — before/after

An **optional enrichment stage OUTSIDE the deterministic core**. The LLM (Claude
subagents under the £180 subscription — never API-key Claude) only **proposes** an
extraction plus a **verbatim `evidence_quote`**; the **verification is model-free**
(this stays in the deterministic core): a datapoint is emitted only if its quote is a
literal substring of the abstract **and** its point lies inside its CI. Otherwise the
layer **abstains** (calibrated abstention — a wrong number is worse than none).

Run over the same **235** databank-confirmed T2D index abstracts (16 batches, 234
processed):

| Metric | Deterministic core | + LLM layer (fused) | Δ |
|---|---:|---:|---:|
| **Abstract usability rate** | 28.5% (67/235) | **39.6% (93/235)** | **+11.1 pts (+39% rel)** |
| **Point-extraction precision** (registry-anchored, same-family) | 80.0% (4/5)\* | **94.4% (17/18)** | +14 pts **at 3.6× coverage** |
| Emitted datapoints with a **source span** | — | **100% (93/93)** | transparency invariant holds |
| Abstracts where the layer **abstained** | — | 170/234 | calibrated |

\* The deterministic point precision is 80% only *after* the point-in-CI self-consistency
guard (§3) — but that guard buys reliability by shrinking confident ratio/diff output to
just **5** trials. The LLM extracts a verified point for **18** and is more accurate on
each. (The earlier "~17%" figure was pre-guard.)

**Transparency confirmed: 100% of emitted datapoints retain a source-span link**
(`provenance.source_doc` = PMID, `provenance.source_span` = the verbatim abstract
sentence, `provenance.confidence` = tier). A human verifies any number in seconds by
reading the attached span; the LLM never becomes an opaque oracle. The single
registry-mismatch (NCT02128932) is a faithful extraction of a *different comparator*
("difference versus insulin glargine −0.38%"), not an error. Hand-validation: 8/8
spot-checked datapoints match their span (7/8 CI-anchored exact; 1 point-only borderline).

Artifacts: `out/enriched_t2d.jsonl` (per-trial datapoint + provenance),
`out/llm_summary_t2d.json`, `out/point_precision_t2d.json`. Engine: `src/llm_extract.py`
(seam-respecting), `src/score_points.py`.

## 2. Data & pipeline

```
fetch_ctgov.py 600   → 600 completed interventional T2D full records (CT.gov API v2)
link_pubmed.py       → 304/600 trials link ≥1 PMID; abstracts cached (2 channels, cap 6/trial)
extract.py           → registry facts + abstract usability verdict (rule-based)
diff.py              → three-state poolability + 5 discrepancy classifiers → out/trials.jsonl
metrics.py           → deliverables → out/metrics.json
validate_nonpub.py   → active-search confirmation of non-publication flags
adjudicate_dump.py   → readable cards → out/adjudication_cards.txt (hand-adjudicated)
```
Tests: `test_extract.py` (EMPA-REG registry HR 0.86/CI 0.74–0.99 + 5 synthetic usability cases),
`test_diff.py` (index selection, predate filter, direction helper). All green.

---

## 3. Deliverable 1 — Abstract-extraction usability

Denominator = the **235** trials with a *databank-confirmed* index abstract (a paper a scientist
can actually retrieve for the trial — its NCT appears in the paper's PubMed databank field).

**Usability rate = 67/235 = 28.5%.**

| Verdict | Reason | n | share |
|---|---|---:|---:|
| **usable** | means ± SD (poolable directly) | 45 | 19.1% |
| usable | effect + 95% CI | 14 | 6.0% |
| usable | effect + p (SE recoverable) | 8 | 3.4% |
| **unusable** | **relative-only** (% change, no CI/SD) | **99** | **42.1%** |
| unusable | numbers, no estimate | 35 | 14.9% |
| unusable | p-value only (no estimate) | 15 | 6.4% |
| unusable | median, no dispersion | 11 | 4.7% |
| unusable | no abstract | 4 | 1.7% |
| unusable | narrative only | 4 | 1.7% |

**Dominant failure = "relative-only" (42%)**: abstracts report "reduced by 23%" / event
percentages with no CI, SD, or absolute counts → not poolable. This single mode is the largest
lever for the mission user.

**Caveat from hand-validation (important):** usability *screening* is accurate (8/8 usable
labels confirmed to contain poolable data), **but the auto-extracted POINT estimate is
unreliable** — the regex grabs dose numbers ("1.8 mg" → OR 1.8) and HbA1c thresholds
("≤7.0%" → OR 7.0). A point-in-CI self-consistency guard (added this pilot) corrects 3/14
CI-anchored points; **means±SD is the most reliable extraction path**, ratio/point extraction
needs a stronger parser (a heterogeneous-verification / LLM-assisted layer *outside* the
deterministic core).

---

## 4. Deliverable 2 — Registry-results coverage + three-state poolability

- **28.8%** (173/600) of completed T2D trials post structured results on CT.gov.
- **94.8%** (164/173) of those have a **usable** primary outcome (numeric analysis with
  point/CI/p, or ≥2 group means) — when results exist, they are almost always machine-usable.
- **45.0%** (270/600) of completed trials have a *reporting* publication (databank-linked).

**Three-state model per trial (the complementarity that makes it "better at scale"):**

| State | Definition | n | share |
|---|---|---:|---:|
| **BOTH** | registry **and** abstract usable → cross-check + dual-source pool | 29 | 4.8% |
| **ONE** | exactly one usable → single-source pool, lower confidence | 173 | 28.8% |
| **NEITHER** | neither usable → honest exclusion | 398 | 66.3% |

**Poolable = BOTH + ONE = 202/600 = 33.7%.** Decomposition: registry-only **135**,
abstract-only **38**, both **29**. **The two sources are genuinely complementary** — abstracts
recover 38 trials with no usable registry results; registry recovers 135 the abstract can't
support. Fusing them ~triples the poolable yield vs abstracts alone (33.7% vs 11.2%).

---

## 5. Deliverable 3 — Per-class discrepancy rate + hand-adjudicated precision

Every class separates **`contradicts`** (both sources state a comparable fact and they differ)
from **`silent_on`** (one source is silent — **never** a discrepancy). Full adjudication in
`out/adjudication_results.json`; cards in `out/adjudication_cards.txt`.

| Class | Raw `contradicts` | Diffable denom | Raw rate | **Adjudicated precision** | Verdict |
|---|---:|---:|---:|---:|---|
| **non_publication** | 330 | 600 | 55.0% | **≈0.67** (6 TP / 9) | **Real signal**, needs active-search confirmation |
| enrollment_mismatch | 41 | 72 | 56.9% | **0.0** (0 / 8) | All FP (substudy/PRO/pooled-PK/analyzed-set) |
| primary_endpoint (switch-cand.) | 54* | 205 | 26.3% | **0.0** (0 / 8) | All FP (secondary pub / wording) — GAP |
| direction_flip | 0 | 4 | 0.0% | n/a (2 pre-fix FP suppressed) | No genuine flips |
| significance_flip | 0 | 4 | 0.0% | n/a (1 pre-fix FP suppressed) | No genuine flips |
| ma_omission | — | — | — | — | **GAP** (needs published-MA trial-list corpus) |

\* `switch_candidate`, not confirmed `contradicts`.

### 5.1 Non-publication (the one that works)
Flag = completed trial with **no** NCT-databank-linked publication. Active PubMed search
(`validate_nonpub.py`) confirms: of 20 flagged, a bare-NCT full-text search returned **0** hits
for all 20 — but targeted drug+design searches found genuine publications for **3/9** carefully
adjudicated (STABLE/gemigliptin → PMID 28058753; LY2409021 → 28191913; Glucovance → 12915642) —
real papers that simply **never registered their NCT in any PubMed field**. So precision ≈0.67
and the **raw 55% over-estimates true non-publication**; the bias-corrected ~35–40% matches the
trial-publication literature. **Design consequence:** the flag is a *screen*; each hit needs the
active-search confirmation step before it is a confirmed non-publication.

### 5.2 Why the numeric classes fail (the rigor trap, empirically)
The mission's abstract-only constraint is exactly what breaks fine-grained detection:
- **Enrollment**: abstract N and registry enrollment routinely denote **different populations**
  (a PRO substudy n=56 of 112; a pooled-PK n=974; a program-wide renal pool n=4,545; analyzed
  vs randomized). Not a discrepancy.
- **Endpoint switch**: the term-overlap heuristic flags "index abstract doesn't lexically match
  the registry primary" — dominated by **multi-publication trials** (the picked index is a
  secondary/ancillary/review paper) and **verbose registry names** ("Glycosylated A1c" vs the
  abstract's "A1C"). True switching needs the publication's *declared* primary (methods section),
  absent from abstracts.
- **Direction / significance**: near-null sign changes are noise (both CIs cross the null); a
  cross-endpoint comparison (registry HbA1c mean vs abstract responder OR) is not a flip. Both
  suppressed by guards added this pilot (both-null rule, CI-anchor requirement, family-match gate).

This is a **genuine, honest feasibility result**, not a failure to build: abstract+registry alone
**cannot** reliably adjudicate intra-trial numeric contradictions; that capability requires
full-text, which the target user cannot access.

---

## 6. RapidMeta feedstock

The 202 poolable `BOTH`/`ONE` extractions in `out/trials.jsonl` double as RapidMeta inline
`realData` feedstock: each carries a structured primary effect (point/CI/p **or** group means)
with **provenance** (registry vs abstract) and a **confidence tier** (dual-source vs
single-source). Recommended gate before auto-pooling: prefer `means_sd` and CI-anchored effects;
withhold point-only ratio extractions pending the stronger parser (§3 caveat).

---

## 7. Limitations & GAPs (truth-first)

- **Single therapeutic area** (T2D). Cross-area generalization unverified — GAP.
- **Per-trial abstract cap = 6**; a trial's true primary-results paper could sit beyond the cap
  (mitigated by ordering RESULT/`[si]` first, but not eliminated).
- **Non-publication precision from n=9** carefully-adjudicated trials — wide CI; directional, not
  definitive.
- **MA-omission class not attempted** — needs a published-MA included-trials corpus (design:
  intersect a MA's NCT/PMID list against registry-completed trials in the same PICO). GAP.
- **Point-extraction precision is low** for ratio/point effects (§3) — the deterministic core
  screens well but does not yet extract the right number reliably.
- Databank linkage misses publications that never NCT-tagged (§5.1) — affects both the
  non-publication numerator and the usability denominator.

---

## 8. Reproduce

```
cd regpub_pilot/src
python fetch_ctgov.py 600
python link_pubmed.py
python diff.py
python metrics.py
python test_extract.py && python test_diff.py
python validate_nonpub.py         # active-search non-pub confirmation
```
Raw caches (`data/ctgov`, `data/pubmed`) are git-ignored (reproducible); `out/` is the staged
deliverable. Numbers above are from `out/metrics.json` + `out/adjudication_results.json`.
