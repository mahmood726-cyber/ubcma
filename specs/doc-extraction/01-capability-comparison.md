# 01 — Capability Comparison (four candidates)

Verified 2026-07-06 against each tool's repo/docs. Every row is tagged **[VERIFIED]**
(confirmed in the primary source I read), **[VENDOR-CLAIM]** (stated by the vendor/author;
not independently reproduced), or **[UNVERIFIED]** (could not confirm — flagged).

> **Truth-first caveat that governs this whole table:** every accuracy number below
> (OmniDocBench, TEDS, OlmOCRBench, win-rates) measures **document-structure reconstruction**,
> **not** exact numeric fidelity. None of them certifies that a 2×2 event count or an HR/CI was
> transcribed digit-for-digit. For our use, structure score ≠ trust. That is why the deciding
> gate in [`02`](02-recommended-architecture.md) is a digit-exact bake-off, not any score here.

## Snapshot

| | **MinerU** | **Baidu Unlimited OCR** | **Mistral OCR 4** | **Ollama-OCR** |
|---|---|---|---|---|
| **What it is** | Pipeline: layout-detect + dedicated OCR + table/formula models, with a small VLM path | Generative VLM decoder (MoE) | Commercial generative OCR model + API | Thin wrapper orchestrating local Ollama vision models |
| **License** | Custom "MinerU Open Source License" (Apache-2.0-derived) **[VERIFIED]** | **MIT**, open weights **[VERIFIED]** | Proprietary; weights **not** openly licensed **[VERIFIED]** | **MIT** (wrapper); underlying models have their own licenses **[VERIFIED]** |
| **Local run** | Yes — CPU-only (pipeline) or small GPU (VLM) **[VERIFIED]** | Yes — needs CUDA GPU + weights **[VERIFIED]** | **Enterprise license only** (single container via vLLM/TGI); else cloud API **[VERIFIED]** | Yes — via local Ollama **[VERIFIED]** |
| **Model size** | `MinerU2.5-Pro` VLM ≈ **1.2B** + `PP-OCRv6` **[VERIFIED]** | **3B total / ~500M active** MoE **[VERIFIED]** | Undisclosed (proprietary) | Depends on chosen model (llava / llama3.2-vision / granite3.2-vision / minicpm-v) |
| **GPU/VRAM** | 2–8 GB for GPU path; CPU path needs none; 16 GB+ RAM **[VERIFIED]** | Not officially documented; 3B/500M-active is small → *plausibly* one 12–16 GB GPU **[UNVERIFIED]** | N/A (API) or enterprise container | Whatever the chosen Ollama model needs (≈8–12 GB for llama3.2-vision 11B) |
| **Multi-page** | Page/section pipeline; merges cross-page tables **[VENDOR-CLAIM]** | **40+ pages in ONE pass, constant KV cache** (R-SWA), 32K ctx **[VENDOR-CLAIM]** | Page-by-page | Page-by-page |
| **Tables** | HTML table structure **[VERIFIED cap]** | **TEDS 90.93** — best reported here (+5.96 vs DeepSeek OCR) **[VENDOR-CLAIM]** | Typed-block table detection **[VERIFIED cap]** | "table" output format **[VERIFIED cap]**; no benchmark |
| **Formulas** | LaTeX **[VERIFIED cap]** | Formula CDM 92.61 **[VENDOR-CLAIM]** | LaTeX-capable **[VENDOR-CLAIM]** | Model-dependent; no benchmark |
| **Structured output** | JSON + Markdown (reading-order) **[VERIFIED]** | Markdown/structured text **[VERIFIED]** | **JSON schema** (output shaped by `mistral-small-2603`) **[VERIFIED]** | markdown/text/json/**structured**/key_value/table **[VERIFIED]** |
| **Cost** | Free (compute only) | Free (compute only) | **$4 / 1k pages** ($2 batch); Document AI $5/1k **[VERIFIED]** | Free (compute only) |
| **Data residency** | Fully local | Fully local | Cloud API unless enterprise self-host **[VERIFIED]** | Fully local |

## Per-tool detail + flags

### MinerU — https://github.com/opendatalab/mineru
- **License flag (correction to the brief):** it is **neither plain Apache 2.0 nor AGPL-3.0**.
  It is a **custom "MinerU Open Source License, based on Apache 2.0"** [VERIFIED from `LICENSE.md`]
  that adds (a) a commercial-license trigger if **MAU > 100M or monthly revenue > USD 20M**, and
  (b) an **attribution requirement** for online-service providers ("clearly indicate MinerU is
  used"). At our scale (a) is irrelevant → **effectively free**. (b) means **if RapidMeta shows
  MinerU-extracted data in a public UI, add a "MinerU used" attribution note.** (Older MinerU
  releases were AGPL-3.0; the brief's "Apache/AGPL" reflects that history — the current repo is
  the custom license.)
- Architecture is a **pipeline** (layout detection → dedicated OCR `PP-OCRv6` → table/formula
  models), plus an optional 1.2B VLM (`MinerU2.5-Pro`). The pipeline path is **less prone to
  free-form digit hallucination** than a pure generative decoder because OCR is a dedicated
  recognition step — this is the main reason it stays the default. The VLM path still carries
  some generative risk and must go through the same bake-off.
- CPU-only via the `pipeline` backend [VERIFIED] → runs on any cluster node with no GPU.
- `pip install mineru[all]`; Docker supported (Linux / Windows WSL2) [VERIFIED].

### Baidu Unlimited OCR — arXiv 2606.23050 · GitHub/HuggingFace (open weights)
All performance numbers are **author-reported [VENDOR-CLAIM] / [UNVERIFIED]**:
- **3B total / ~500M active** MoE decoder [VERIFIED]. **MIT license, open weights** [VERIFIED]
  — cleaner licensing than MinerU.
- **DeepEncoder** compresses a 1024×1024 page to **256 visual tokens** (16× compression) [VERIFIED
  as claim].
- **R-SWA (Reference Sliding Window Attention):** each output token attends to all reference
  (visual+prompt) tokens plus the preceding **n=128** output tokens; older tokens evicted →
  **KV cache bounded by a constant** rather than growing with length. This is the mechanism
  behind **40+ pages parsed in one continuous pass** at ~constant memory/speed [VERIFIED as claim].
- OmniDocBench **v1.5 93.23** (beats DeepSeek OCR by 6.22) / **v1.6 93.92**; **TEDS 90.93**
  (+5.96 over DeepSeek); **text edit distance < 0.11 at 40+ pages** [all VENDOR-CLAIM].
- Runtimes: **Transformers + SGLang** (OpenAI-compatible, `fa3` backend) confirmed [VERIFIED].
  The brief also lists **vLLM / ModelScope** — **[UNVERIFIED]** in the source I read; treat as
  plausible-but-confirm-at-install.
- **GPU footprint not officially published** [UNVERIFIED]; training used 8×A800. Inference for a
  3B/500M-active MoE is small — likely fits a single 12–16 GB GPU, but **confirm before pulling
  weights**.
- **Why it matters here:** the multi-page-single-pass property is a *genuine* fit for long RCT
  reports + supplementary appendices, where page-by-page engines can split a cross-page outcome
  table. And the best table-structure score is directly on-target: **clinical event counts live
  in tables.** But see the make-or-break in [`02`](02-recommended-architecture.md).

### Mistral OCR 4 — https://mistral.ai/news/ocr-4/
- **Self-host licensing flag:** self-hosting exists ("compact enough for a single container")
  but is **enterprise-customers-only via sales**, and **weights are not openly licensed**
  [VERIFIED]. So for us it is effectively a **cloud API**. Published papers are public → cloud
  is acceptable on data-residency grounds, but note documents leave our environment.
- Pricing **$4 / 1k pages** (=$0.004/page), $2/1k with Batch API; Document AI $5/1k [VERIFIED].
- **Schema-based structured JSON**: you define a schema and OCR output is shaped by
  `mistral-small-2603` [VERIFIED] — convenient, but note a second LLM stage sits between the
  pixels and your JSON, which is exactly where a digit can silently change.
- Benchmarks (Mistral-reported): OmniDocBench 93.07, OlmOCRBench 85.20, 72% avg human win-rate
  [VENDOR-CLAIM]; Mistral itself calls these "directional rather than definitive."

### Ollama-OCR — https://github.com/imanoop7/Ollama-OCR
- **Orchestration wrapper**, not a model [VERIFIED]. MIT. Drives local Ollama vision models
  (llava, llama3.2-vision, granite3.2-vision, minicpm-v).
- Output formats incl. `json`, `structured`, `key_value`, `table` [VERIFIED]; PDF supported
  [VERIFIED] (page-render mechanism not documented).
- **No accuracy benchmarks in the repo** [VERIFIED absence]. Value = lowest-friction way to get a
  *second, independent* local VLM opinion for the consensus layer; not a primary extractor.
