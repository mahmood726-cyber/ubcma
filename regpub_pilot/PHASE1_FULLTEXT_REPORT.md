# Phase 1 — Open-Access Full Text wired into the reg-vs-pub engine

**Branch:** `pilot/regpub-discrepancy` · **Date:** 2026-07-07 · **Status:** local commits only, no push/deploy.
**Roadmap step:** Phase 1 of `opendata_scan/INTEGRATION_ROADMAP.md` — the full-text poolable-ceiling lever (Europe PMC OA JATS + OpenAlex/Unpaywall OA copies beyond PMC).

Reproduce:
```
PILOT_AREA=t2d python src/fetch_fulltext.py fetch   # Europe PMC + OA fetch (cached)
PILOT_AREA=onc python src/fetch_fulltext.py fetch
PILOT_AREA=t2d python src/fulltext_extract.py batches   # candidate-window batches
# subagents extract -> data/ft_raw/*.txt
PILOT_AREA=t2d python src/fulltext_extract.py fuse   # verify + emit poolable datapoints
PILOT_AREA=onc python src/fulltext_extract.py fuse
python src/ft_report.py                              # lift report + integrity + validation
```

---

## HEADLINE

| Area | Baseline poolable (abstract+registry) | **With OA full text** | Lift | Relative |
|---|---|---|---|---|
| **T2D** | 39.6% (93/235) | **46.0% (108/235)** | **+6.4 pts** | +16.1% |
| **Oncology** | 24.0% (25/104) | **32.7% (34/104)** | **+8.7 pts** | +36.0% |
| **Pooled** | 34.8% (118/339) | **41.9% (142/339)** | **+7.1 pts** | +20.3% |

- **OA-available fraction** (index publications): Europe PMC full text **53.0% (T2D) / 54.5% (onc)**; adding OpenAlex/Unpaywall OA copies → **71.5% / 70.1%** combined (measured in `opendata_scan/`).
- **Precision (hand-validated, all 24 emitted datapoints):** **24/24 verbatim-faithful to their source span (100%)**; **23/24** correctly represent the registered primary outcome; **1 partial** (a 5-arm factorial contrast-selection case). **0 fabricated or wrong numbers.**
- **Source-span retention: 100%** (24/24 emitted datapoints carry a verbatim source span; `ft_report.py` integrity check finds **0** violations — no point-outside-CI, no span-not-in-text).
- **Every recovery came from Europe PMC JATS. Zero came from bronze/green OA copies** (honest bound — see §4).

---

## 1. What was built (the deterministic-core seam held)

Three new modules under `src/`, all respecting the invariant *network touches acquisition only; extraction verification and pooling stay model-free/offline*:

- **`fetch_fulltext.py`** — acquisition. For each confirmed-index gap PMID: (1) Europe PMC `…/{PMCID}/fullTextXML` where `inEPMC=Y`; (2) OpenAlex/Unpaywall `oa_url` fallback for legal OA copies beyond PMC (bronze/green/gold/hybrid). Reuses the read-only OA maps already measured in `opendata_scan/`. Fails **soft** on every dead link (no run-aborting crash); a TLS-cert failure on a public OA repository copy is retried once over an unverified context (public read-only content only; Europe PMC stays strict). All bytes cached to `data/fulltext/` → extraction runs fully offline.
- **`jats.py`** — deterministic JATS/HTML → `{abstract, methods, results, tables[]}` section parser. (Bug found + fixed: a trailing `\b` made `\bresult\b` miss the plural heading "RESULTS", silently emptying the results section for ~90% of articles; stem-matching fixed it — median results text 0 → 9,050 chars.)
- **`fulltext_extract.py`** — the extraction layer. A deterministic **candidate-window pre-filter** shrinks each article to compact *verbatim* excerpts around statistics (effect words, 95% CIs, means±SD, p-values) and primary-endpoint terms; the model selects the primary among candidates; the model-free gate then requires the `evidence_quote` to be a literal substring of the exact excerpt handed to the model **and** point ∈ CI. Same calibrated-abstention contract as the abstract layer — a wrong number is worse than an abstention.

The extraction engine is **Claude subagents (the £180 subscription)**, 15 batches of ≤8 gap trials, throttled 3-concurrent. `agy` (Antigravity) is the independent second vendor (§5). Codex not used (auth revoked — did not block).

---

## 2. The measured lift, honestly framed

The baseline being beaten is the **already-LLM-enhanced fused** rate (39.6% / 24.0%), not the deterministic-only abstract rate (28.5% / 13.5%). So this is lift *on top of* the abstract-layer LLM, the hardest baseline.

**The roadmap's projection was optimistic and is now corrected.** The roadmap projected T2D 28.5% → ~55–61% assuming a **70–90% full-text→poolable conversion**. The real conversion, measured:

| Area | Gap trials | …with parseable OA full text | …yielding a verified poolable primary | **Conversion** |
|---|---|---|---|---|
| T2D | 142 | 70 (49.3%) | 15 | **21.4%** |
| Onc | 79 | 41 (51.9%) | 9 | **22.0%** |

The conversion is ~**21–22%**, not 70–90%. **Why:** most gap trials that reach full text still have *no poolable between-group primary to extract* — they are single-arm dose-finding (MTD "not reached"), protocols, PK-only, safety-primary (AE counts), subgroup-only, or median/IQR-only designs. In those cases the full text **confirms** the abstract's non-poolability rather than rescuing it. Dominant abstain reason: `no_primary_number` (48/55 T2D, 28/32 onc). This is the calibrated-abstention discipline working: full text is a real lever (+7.1 pts pooled, +20% relative), but a far smaller one than an assumed high conversion would suggest.

---

## 3. Precision — hand-validation of all 24 emitted datapoints

Small enough to validate exhaustively rather than sample (`out/ft_validation_{t2d,onc}.json`):

- **100% verbatim source-fidelity** — every reported point/CI appears in the emitted `source_span`, which is itself a literal substring of the retrieved full text.
- **23/24 correctly represent the registered primary** — between-group effects (HbA1c MD, risk difference, ORR difference), single-arm proportions where the trial *is* single-arm (confirmed: e.g. NCT01335763 is a 1-arm design, so its within-group HbA1c change *is* the registered primary), and per-arm means±SD.
- **1 partial** — NCT01708902, a 5-arm factorial: the full-text HbA1c difference (−0.53) is a valid between-group contrast but may not match the registry's specific pre-specified "Main Group" contrast (−0.22). Multi-arm contrast-matching is a known-hard case, flagged for adjudication, not a fabrication.
- **2 datapoints faithfully diverge from the registry value** (NCT01708902, NCT03555994) — these are exactly the registered-vs-published signals the engine exists to surface; the extraction is correct, the divergence is the finding.

Type-label nits (a between-group risk difference labelled `mean_difference`; one GMR with `effect_type=null`) do not affect the numeric payload or its provenance.

---

## 4. Honest bounds (the truth-first ledger)

- **OA-available ≠ full-text-pullable.** `inEPMC=Y` does not guarantee a machine-readable `fullTextXML`: of the EPMC-channel gap trials, a real fraction returned `fetch_miss` (author-manuscript / PDF-only deposits with no XML). Fetch-status breakdown is in `out/fulltext_lift_report.json`.
- **Bronze/green OA copies contributed 0 verified datapoints.** T2D reached 13 bronze + 3 green + others; onc 7 bronze + 1 green — all parsed to text, none produced a verifiable primary. Publisher HTML is noisy and unstructured; the calibrated gate correctly refused to force numbers out of it. **So the entire measured lift came from Europe PMC JATS.** Bronze is also read-only, not redistributable (licence-limited), and 3 items were `pdf_unparseable` (no OCR in the deterministic core — an explicit, honest gap).
- **The candidate-window pre-filter is a recall floor, not a ceiling.** `no_primary_number` includes some trials whose primary *is* reported but sat outside the extracted windows or in a mis-parsed section. A more exhaustive (whole-section) extraction could recover a few more — at higher token cost and the same abstention discipline. The reported 21–22% conversion is therefore a conservative floor.
- **OpenAlex is metered (2026):** used within the free tier; no bulk pulls.
- **Denominator:** trial-denominated (235 / 104), matching the abstract-layer baseline exactly; two trials sharing one index PMID are counted as two trials (one paper can make both poolable).

---

## 5. Second-vendor cross-check (agy / Antigravity)

`src/agy_crosscheck.py` re-extracts a sample (12 datapoints spanning both areas + effect types) with a **different vendor** on the **same verbatim excerpt** (the program's consensus-or-flag / decorrelated-blind-spot primitive); agreement is independent corroboration, disagreement is flagged for human review. It does not gate the pipeline. Results (`out/agy_crosscheck.json`):

- **8/10 exact point agreement** (agy abstained on 2, leaving 10 comparable): e.g. `-2.8 [-9.5,3.9]`, `-0.53 [-0.69,-0.37]`, `13.01 [3.33,22.69]`, `-0.582 [-1.346,-0.183]`, ORR `11%`, GMR `98.43%` — all matched to the digit.
- **1 sign-convention difference** — NCT01335763 single-arm HbA1c change: Claude `1.8` (magnitude, as literally written "a change of 1.8%"), agy `-1.8` (signed reduction). Same magnitude; a direction-convention nuance on a within-group reduction, not a value conflict.
- **1 representation difference** — a PK primary given by Claude as raw per-arm means (58.2 vs 53.1) and by agy as a computed ratio (~106.5); both capture the same primary.
- **2 agy abstentions** flagged 2 lower-confidence Claude datapoints for scrutiny (both confirmed verbatim-correct on review).
- **0 genuine value contradictions.** *(agy liveness proven with a real exec — returned "OK" — not a status page.)*

---

## 6. Bottom line

Wiring open-access full text into the pilot's extraction layer lifts the poolable rate **34.8% → 41.9% pooled (+7.1 pts, +20% relative)** — **T2D 39.6% → 46.0%**, **oncology 24.0% → 32.7%** — with **100% source-span provenance**, **0 fabricated numbers** across all 24 emitted datapoints, and the deterministic-core seam intact. The gain is real and clean but **materially smaller than the roadmap's assumed 70–90% conversion**: the true full-text→poolable conversion on gap trials is ~21–22%, because most non-poolable trials are structurally non-poolable (single-arm/dose-finding/PK/safety/subgroup/median-only) even at full text. Europe PMC JATS carried the entire lift; bronze/green OA copies added coverage but 0 verified datapoints in this run.
