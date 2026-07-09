# 03 — Integration Point

## Where this plugs in

Today the ground-truth numbers that feed the borrowing/transport corpus and the RapidMeta app
corpus are extracted from PDFs **largely by hand** — that manual step is the stated
**biggest data-quality bottleneck**. The extraction stack specified here inserts **one new stage**
directly in front of the existing published-meta ground-truth audit:

```
BEFORE:   PDF  ──(manual read + type)──►  ground-truth corpus / RapidMeta corpus
                                              │
                                              └──► (later) AACT cross-check, borrowing/transport

AFTER:    PDF ─► [MinerU (+Baidu/Mistral)] ─► structured JSON w/ page provenance
                                              │
                                              ▼
                          verification / confidence-flag layer
                          (consensus-or-flag + source-page gate + sanity gates)
                                              │
                       ┌──────────────────────┼───────────────────────┐
                       ▼                       ▼                       ▼
              ground-truth corpus     RapidMeta corpus         AACT cross-check
              (borrowing/transport)   (app data issues)        (registry vs published)
```

The human does not leave the loop — they move from *transcribing every number* to
*adjudicating only the flagged cells* (engine disagreements, missing provenance, failed sanity
gates). That is the throughput win, and it is a strict accuracy improvement because every
unflagged number is now corroborated by ≥2 independent engines and pinned to a source page.

## What it improves — concretely

### 1. RapidMeta data issues
- The current corpus carries silent transcription errors (the exact failure family behind the
  negated-counts and placeholder-leak lessons). Routing new papers through the extraction +
  **consensus-or-flag** layer converts *silent wrong numbers* into *flagged cells a human checks*.
- Every value gains a `{page, bbox}` stamp → any RapidMeta number becomes **click-through
  traceable to the source page**, satisfying the truth-first "traceable to source" requirement
  that manual entry does not enforce.
- Faster corpus growth: bulk PDFs go through MinerU's CPU pipeline unattended overnight; only
  conflicts surface for review.

### 2. AACT cross-check (two-way validator)
- We already compare **registered (AACT results-posted)** vs **published (PubMed)** values in the
  transport-NMA pub-bias work (`transport_nma/`, the HbA1c registered-vs-published gap →
  frozen κ). Automated PDF extraction feeds the **published** side of that comparison at scale.
- Each extracted registry-linked number (event counts, HbA1c change, N randomized) can be
  **auto-diffed against its AACT record**. A mismatch is diagnostic in *both* directions:
  - if the PDF-extracted number disagrees with a clean AACT value → likely an **extraction
    error** → the engine/cell is flagged and fixed (a free accuracy check on the extractor);
  - if extraction is verified correct but still disagrees with AACT → a **real
    registered-vs-published discrepancy** → exactly the signal the transport/pub-bias method
    consumes (severity of selective reporting). So the extraction layer doesn't just *feed*
    the pub-bias work, it **sharpens** it by separating transcription noise from true discrepancy.
- Guard rails carry over from `rules/lessons.md`: AACT is lowercase-typed, search by specific
  drug name, verify columns exist per snapshot, validate >0 rows before trusting a cross-check.

### 3. Ground-truth corpus for borrowing/transport
- The corpus (`corpus_nodes_*.csv`, the metafor-harmonized MA nodes) grows only as fast as numbers
  are extracted. A vetted extraction lane lets us add MAs/trials faster **without** lowering the
  numeric-integrity bar — the pass gate (≥99% cell exact-match, zero silent digit substitutions)
  is the same integrity contract the borrowing estimates depend on.
- The **cross-page / supplementary-appendix** case is where Baidu Unlimited OCR's single-pass
  parsing specifically helps: outcome data split across a page break or buried in an appendix is
  a known manual-extraction trap, and page-by-page engines can fragment those tables.

## Sequencing (no install in this task)
1. Stand up the **MinerU CPU pipeline** + the **verification layer** + the **digit-exact bake-off
   harness** first — zero GPU dependency (see [`appendix-A`](appendix-A-mineru-install.md)).
2. Run the bake-off ([`02`](02-recommended-architecture.md#the-deciding-test--digit-exact-table-bake-off-run-this-before-anything-ships))
   on the 8–12 ground-truthed PDFs.
3. Only if the GPU preflight confirms a capable node: add **Baidu Unlimited OCR** to the bake-off
   and, if it clears the bar, give it the long-document lane.
4. Wire **Mistral OCR 4** in as a paid, sparing third voter for hard pages / disputes.
5. Everything ships behind the consensus-or-flag + source-page gate — never a raw single-engine
   number into the corpus.
