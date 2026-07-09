# 02 — Recommended Architecture + the Deciding Test

## The make-or-break, stated once for all generative engines

Baidu Unlimited OCR, Mistral OCR 4, and the Ollama vision models are all **generative VLM
decoders**: they *predict* the next token of the transcription. That is fundamentally different
from a dedicated OCR recogniser reading glyphs. A generative decoder can emit a fluent, correctly
*formatted* table in which **one digit is silently wrong** — `142` → `147`, `HR 0.83` → `HR 0.88`,
`n=1807` → `n=1087`. OmniDocBench 93% and TEDS 90.93 reward getting the **structure** right; they
do **not** penalise a single flipped digit inside an otherwise perfect cell. For a truth-first
clinical corpus, **one wrong digit is catastrophic** — it silently corrupts an event count or
effect size that then propagates into the borrowing/transport estimates and the RapidMeta corpus.
This is the same failure family we already guard against elsewhere (negated-counts, silent-failure
sentinels): *schema-valid but semantically wrong*.

**Therefore: no generative engine is trusted for unattended numeric extraction until it passes the
digit-exact bake-off below. Structure benchmarks and throughput are not admissible evidence.**

## Recommended architecture (spec only — nothing installed)

```
                         published-paper PDF (RCT / meta-analysis)
                                        │
              ┌─────────────────────────┼─────────────────────────┐
              │ PRIMARY (local, free)   │ CHALLENGER (local, free) │ FALLBACK (paid, opt.)
              ▼                         ▼                          ▼
        MinerU pipeline          Baidu Unlimited OCR         Mistral OCR 4 API
        (layout+PP-OCRv6,        (40+ pages one pass,        (hard pages only,
         CPU-ok default)          best tables — IF it         $4/1k, schema JSON)
              │                    passes the bake-off)             │
              │                         │                           │
              └──────────┬──────────────┴───────────────┬──────────┘
                         ▼                               │
              structured JSON per value:                 │  (Ollama-OCR = optional
              {value, field_type, page, bbox}            │   2nd local-VLM voter)
                         │                               │
                         ▼                               ▼
        ┌────────────────────────────────────────────────────────┐
        │  VERIFICATION / CONFIDENCE-FLAG LAYER  (non-negotiable)  │
        │  1. source-page gate: every number carries page+bbox;   │
        │     drop/flag any value with no provenance.             │
        │  2. consensus-or-flag: run ≥2 engines; FLAG every cell   │
        │     where they disagree → human verifies ONLY conflicts.│
        │  3. sanity gates: 2×2 cells ≤ arm N; CI brackets point;  │
        │     %s in [0,100]; SD>0; negation check on counts.      │
        └────────────────────────────────────────────────────────┘
                         │
                         ▼
        ground-truth corpus  ·  RapidMeta corpus  ·  AACT cross-check
```

### Why this shape
- **MinerU is the default** because its pipeline design (dedicated OCR step) is structurally the
  least likely of the four to free-form-hallucinate a digit, it runs **CPU-only** on any node,
  and it's free at our scale. It is the floor everything else must *beat*, not just match.
- **Baidu Unlimited OCR is the challenger, not the default** — its multi-page-single-pass and
  best-table-score are real advantages for long/appendix-heavy reports and cross-page outcome
  tables, but that value is only bankable if digit-accuracy clears the bar.
- **Mistral OCR 4 is the paid oracle** for genuinely hard pages (poor scans, dense typeset
  tables) and as an independent third voter in disputes — used sparingly to control cost.
- **The verification layer is engine-independent and mandatory.** It is the same
  **consensus-or-flag** primitive already in this repo (`consensus/`) — heterogeneous voters
  (a pipeline OCR + a generative VLM) catch *systematic* single-engine errors that a single
  engine, however good its benchmark, cannot self-detect.

## THE DECIDING TEST — digit-exact table bake-off (run this before anything ships)

**Goal:** decide, on *our* data, whether Baidu Unlimited OCR (and any generative engine) is safe
for unattended numeric extraction, and whether it beats MinerU. **Not** an OmniDocBench re-run.

**Test set (small, real, ground-truthed):**
- Pick **8–12 real trial-report / meta-analysis PDFs already in our ground-truth corpus**, i.e.
  papers whose true numbers we *already hold* from prior manual extraction (the published-meta
  ground-truth audit set). These are the answer key.
- Deliberately include the hard, on-target cases: **2×2 event-count tables, HR/CI subgroup
  tables, means±SD baseline tables, forest-plot value tables, a cross-page table, and a
  supplementary-appendix table** (the multi-page case Baidu is meant to win).

**Engines under test:** MinerU pipeline · MinerU VLM path · Baidu Unlimited OCR (multi-page mode)
· Mistral OCR 4 API · (optional) one Ollama vision model.

**Scoring — exact-match only:**
- For every numeric field (each event count, N, HR, each CI bound, mean, SD, %), score
  **digit-exact match vs the answer key**. Metric = **cell-level exact-match rate** +, more
  importantly, **count of silent digit substitutions** (a formatted-but-wrong number that no gate
  caught). **TEDS / edit-distance / throughput are recorded for interest but do NOT decide.**
- Separately record **cross-page table integrity** (did the outcome table survive as one table)
  and **provenance completeness** (did every value come back with a page number).

**Pass bar (truth-first):**
- An engine is **trusted for unattended numeric extraction** only if, on the held-out set, it hits
  **≥99% cell exact-match AND zero silent digit substitutions on numeric fields**.
- Below that bar it is **not** an unattended extractor. It may still serve as a **second-opinion
  voter** in the consensus layer (its disagreements route a human to the source page — which is
  useful even when it's wrong, because it surfaces the cell to check).

**Verdicts this test forces:**
- **Baidu passes** → it becomes the **front-runner for long / multi-page / appendix-heavy numeric
  documents and cross-page tables** (open + MIT + multi-page + best tables). MinerU stays the
  default for short/simple bulk docs; Baidu takes the long-document lane.
- **Baidu fails digit-accuracy** → it stays a **fallback / consensus voter behind MinerU**; we do
  **not** route accuracy-critical numeric extraction through it unattended, regardless of its
  93% OmniDocBench. Same rule binds Mistral and Ollama.

## Cost/effort to run the Baidu test (honest)
- Needs a **CUDA GPU node + ~3B open weights** pulled locally. A 3B/500M-active MoE is **small**
  (not a heavy pull), so *if* a cluster node already has a suitable GPU this is a **modest
  half-day setup**, not a project.
- **But:** the node reviewing this spec has **no NVIDIA GPU**, and there is **no cluster-hardware
  inventory on disk** to confirm any node does. **Per Mahmood's no-wasteful-pull rule: do not
  download weights until the GPU preflight in [`appendix-A`](appendix-A-mineru-install.md#gpu-preflight)
  confirms a capable node.** MinerU's CPU path lets us stand up the pipeline and the bake-off
  harness *first*, with zero GPU dependency, and add Baidu as soon as a GPU node is confirmed.
