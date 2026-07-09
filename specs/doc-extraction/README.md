# Doc-Extraction Tooling Spec — Index

**Purpose:** evaluate document-extraction tools for the published-paper → structured-data
pipeline that feeds the borrowing/transport ground-truth corpus, the RapidMeta app corpus,
and AACT cross-checks. **Truth-first:** extraction *accuracy* (every extracted number
digit-exact and traceable to its source page) outranks speed and throughput.

**Status:** authored 2026-07-06. Covers **four** candidates. An earlier draft of this
comparison (MinerU / Mistral OCR 4 / Ollama-OCR) was discussed in a prior session but was
**never persisted to disk** — this is the authoritative first written version, now including
Baidu Unlimited OCR as candidate #4.

## Files

| File | Deliverable |
|---|---|
| [`01-capability-comparison.md`](01-capability-comparison.md) | Four-way capability comparison (local-run, cost, GPU, tables/formulas, structured output, licensing) with per-claim verification + flags |
| [`02-recommended-architecture.md`](02-recommended-architecture.md) | Recommended architecture + the **one deciding test** (digit-exact bake-off) + verification/confidence-flag layer |
| [`03-integration-point.md`](03-integration-point.md) | Where it plugs into the ground-truth/RapidMeta/AACT workflow and what it improves |
| [`appendix-A-mineru-install.md`](appendix-A-mineru-install.md) | Exact MinerU install/verify commands for a cluster node + GPU-inventory preflight (**nothing installed yet — spec only**) |

## Headline recommendation

1. **MinerU stays the free local default** for bulk PDF→structured extraction on the cluster
   (pipeline backend runs CPU-only; VLM path wants a small GPU). Custom-but-effectively-free
   license at our scale.
2. **Baidu Unlimited OCR (MIT, open weights, 3B/500M-active) is the strongest *new* challenger**
   — uniquely, it parses **40+ pages in one pass at constant memory** (a real fit for long trial
   reports and supplementary appendices where the others go page-by-page and can fragment
   cross-page tables) and reports the **best table-structure score** of the four. It does **not**
   auto-promote to front-runner: it is a generative VLM decoder, so **digit-level hallucination
   in numeric tables is the make-or-break risk**. It earns front-runner status **only if it
   passes the digit-exact bake-off**; otherwise it stays a fallback/second-opinion behind MinerU.
3. **Mistral OCR 4** = optional **paid** high-accuracy fallback/benchmark oracle for hard pages
   (API $4/1k pages; self-host is enterprise-license-only, weights not open).
4. **Ollama-OCR** = convenient MIT wrapper around local Ollama vision models — useful as an easy
   second-opinion voter, but no published benchmarks and the same generative-hallucination risk.

**The deciding test is unchanged and applies to every generative engine:** digit-exact table
extraction on a handful of *real trial-report PDFs whose true numbers we already hold*
(event counts / HR-CI / means-SD), scored by **exact match**, **not** OmniDocBench/TEDS/throughput.
See [`02`](02-recommended-architecture.md).

**Do not pull any model weights until a cluster node with a suitable CUDA GPU is confirmed**
(this reviewing node has none; no cluster-hardware inventory exists on disk — see
[`appendix-A`](appendix-A-mineru-install.md) preflight).
