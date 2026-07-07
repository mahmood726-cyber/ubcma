# Open-Access Data Sources — Feasibility & Coverage-Lift Scan

**Scope:** read-only feasibility scan for the registered-vs-published discrepancy engine.
**Corpus:** the reg-vs-pub pilot's already-fetched trial sets (branch `pilot/regpub-discrepancy`).
**Mission constraint:** openly-accessible data ONLY — target user is a scientist with **no institutional / paywall access**.
**Date:** 2026-07-07. **No deploy / no push / no wiring** — measurement + terms verification only.

---

## 0. Headline numbers (TL;DR)

| Source | Measured / estimated lift on the pilot corpus | Terms OK for mission? | Effort | Rank |
|---|---|---|---|---|
| **Europe PMC / PMC-OA full text** | **Poolable/usable ceiling ~2×–4×:** T2D **28.5% → ~55–61%**, onc **13.5% → ~45–60%** (data-grounded; only conversion-rate estimated) | ✅ Yes (OA subset CC-licensed; free REST API, no key) | **Low–Med** | **★ 1** |
| **Unpaywall + OpenAlex** (PMID→DOI→OA copy) | Extends the same full-text lever to the **~47% of index pubs NOT in Europe PMC**; incremental, PDF-parsing-harder (est. **+5–12 pts**) | ✅ Unpaywall free; ⚠️ OpenAlex now metered ($1/day free tier) | Med | **★ 2** |
| **Epistemonikos** (SR→included-study map) | Unlocks the **MA-omission** discrepancy class — currently a hard GAP (not a poolable-rate lift) | ✅ Free, but registration-gated (token) | Med | 3 (different axis) |
| **WHO ICTRP + regional registries** | **~0 added coverage on THIS corpus** (100% CT.gov by construction); estimated **+25–33% more registrations** for the same questions, but **registration-only (no results)** → low poolable yield | ⚠️ Free but **no commercial use**; results absent | Med–High | 4 |
| Drugs@FDA (openFDA) | Regulatory results for a small drug subset; no per-trial link | ✅ Public domain, free API | Med | 5 |
| EMA EPAR / Policy 0070 CSRs | High-value CSRs but **no API**, login-gated, phased (new substances only) | ⚠️ Manual portal, account required | High | 6 |
| CORE / Semantic Scholar | Redundant with Europe PMC/Unpaywall for our need | ✅ Free | Low value here | 7 |

**Recommendation: wire Europe PMC OA full text FIRST** (largest measured gain toward the poolable ceiling, cleanest terms, lowest effort), then **Unpaywall+OpenAlex** to recover the non-PMC OA remainder. Everything else is a different-axis or lower-yield add.

---

## 1. Corpus used for measurement

Reused verbatim from the pilot caches (`data/ctgov/`, `data/pubmed/`, `data/links_*.json`, `out/trials_*.jsonl`). No re-fetch of trial data.

| | T2D | Oncology |
|---|---|---|
| CT.gov completed interventional trials | 600 | 350 |
| Trials with ≥1 linked publication (union PMIDs) | 1,104 | 470 |
| **Databank-confirmed index publications** (pilot's headline denom) | **235** | **104** |
| Any-index-abstract denom | 296 | 151 |
| Unique PMIDs across both areas (combined) | **1,572** | — |

The pilot corpus was **sampled from ClinicalTrials.gov**, so by construction 100 % of it is on CT.gov. This is important for interpreting the registry sources below (§2).

---

## 2. PRIORITY SOURCE 1 — WHO ICTRP + regional/national registries

### 2a. Open-API status + terms (verified)

- **WHO ICTRP** is an **aggregator, not a registry** — it harvests ~18 primary registries. It offers: an **ICTRP Web Service API**, a **monthly full CSV** (WHO OneDrive, link expires after 10 days), and a **SharePoint request** form for incremental updates. Download is **free, no charge**. ([WHO ICTRP downloads](https://www.who.int/tools/clinical-trials-registry-platform/network/who-data-set/downloading-records-from-the-ictrp-database), [conditions of use](https://www.who.int/publications/m/item/who-ictrp-web-service---conditions-of-use))
- **Terms (flag):** attribution to WHO ICTRP required; keep data current; display processing date; **"shall not use information … for marketing, promotional or commercial purposes"**; no proprietary claims. → **Fine for a research/personal-use engine; blocks a commercial product.**
- **Results:** ICTRP carries **registration metadata only — NO structured results.** (Confirmed on the WHO ICTRP page.)
- **Regional registries individually:**
  - **ISRCTN** — XML API + CSV export; attribution encouraged, but T&Cs **forbid "copy, download, or store any content to make or populate a database"** ([ISRCTN terms](https://www.isrctn.com/page/terms)). ⚠️ direct conflict with our use.
  - **EU-CTR (EudraCT)** — legacy, being superseded by **CTIS**.
  - **EU-CTIS** — has a **public JSON API** (`POST /ctis-public-api/search`, GET per trial) that carries **protocol *and* results**; now a WHO primary registry. ([CTIS public API notes](https://hendrik.codes/post/scraping-the-clinical-trials-information-system), [EMA CTIS](https://www.ema.europa.eu/en/news/clinical-trials-information-system-designated-who-primary-registry)) — but EU-only and new (2022+), so near-zero coverage of our *completed historical* trials.
  - **ANZCTR** — API exists but for "approved external groups" (gated).
  - **CTRI (India), ChiCTR (China), PACTR (Africa)** — web portals; weak/absent programmatic APIs (best reached via ICTRP or the R `ctrdata` package).

### 2b. Measured coverage delta on the pilot corpus

Because the corpus is 100 % CT.gov-sourced, ICTRP cannot add coverage to the *existing* set. What we **can** measure directly is **dual-registration** (CT.gov records that carry another registry's ID) and **mission relevance** (where the trials were actually run). Script: `measure_registry_coverage.py` → `out/registry_coverage.json`.

| Measured on cached CT.gov records | T2D (n=600) | Onc (n=350) |
|---|---|---|
| Carry ≥1 **non-CT.gov registry ID** | **13.2 %** (79) | **8.0 %** (28) |
| — dominant: EudraCT/EU-CTR | 57 | 27 |
| — WHO UTN | 39 | 2 |
| — CTRI (India) / JPRN (Japan) / ChiCTR | 4 / 4 / 0 | 0 / 1 / 0 |
| **Mission relevance — trials with NO US site at all** | **59.0 %** (326/553) | **46.3 %** (155/335) |
| ≥1 non-US site | 69.4 % | 54.9 % |
| ≥1 **Asia** site | 151 | 59 |
| ≥1 **Africa** site | 32 | 12 |

**Reading:** the trials are strongly international (59 % of T2D trials run entirely outside the US), yet they are still on CT.gov — the mission relevance is in the *conduct geography*, not in registry exclusivity. Cross-registration into African/Asian registries is rarely captured in the CT.gov secondary-ID field (CTRI 4, ChiCTR 0, PACTR 0).

### 2c. Estimated *additional* trials not on CT.gov (marked ESTIMATE)

Published ICTRP-distribution analysis: **ClinicalTrials.gov ≈ 75 % of ICTRP registrations**; the remaining ~25 % is led by EUCTR, then CTRI, IRCT, ChiCTR, ISRCTN ([Frontiers Pharmacol. 2023, ICTRP data-integrity review](https://www.frontiersin.org/journals/pharmacology/articles/10.3389/fphar.2023.1228148/full)). So for the *same review questions*, ICTRP could surface on the order of **+25–33 % more trial registrations** than CT.gov alone (**ESTIMATE**, condition-dependent).

**But the poolable yield of those extra trials is low**, because (a) ICTRP records are **registration-only — no results**, and (b) non-CT.gov trials (esp. CTRI/ChiCTR) are less likely to have a PubMed-linked publication with an extractable effect. So ICTRP buys **breadth of the non-publication denominator** (its real value: catching registered-but-never-published trials in non-US registries) but **not** poolable effect estimates. It advances the *non-publication* signal, not the *poolable-ceiling* metric this scan is optimising.

---

## 3. PRIORITY SOURCE 2 — PMC Open Access Subset + Europe PMC full text  ★ THE WIN

### 3a. Open-API status + terms (verified)

- **Europe PMC RESTful API** — free, public, **no API key**; you accept the Privacy Notice. ~10.2 M full-text articles, ~6.5 M open access. ([Europe PMC RESTful Web Service](https://europepmc.org/RestfulWebService))
- **Open Access subset** — full-text **XML and PDF are downloadable via the REST/SOAP API** (`.../{SOURCE}/{ID}/fullTextXML`) under **Creative Commons (or similar) licenses**, "generally allow[ing] more liberal redistribution and reuse"; per-article license varies. ([Europe PMC OA downloads](https://europepmc.org/downloads/openaccess)) → **squarely inside the no-paywall mission.**
- Non-OA-but-in-EPMC full text (author manuscripts / NLM collection) is *readable* and usually API-fetchable but not CC-licensed for redistribution. We report both bounds.

### 3b. Measured full-text availability on the pilot PMIDs

Script: `measure_oa_fulltext.py` (live Europe PMC `resultType=core`, cached) → `out/oa_fulltext.json`.

| Index publications (the abstracts we extract from) | T2D (n=302) | Onc (n=154) |
|---|---|---|
| **`inEPMC` = free full text in Europe PMC** | **53.0 %** | **54.5 %** |
| **`isOpenAccess` = CC-licensed OA subset** | **42.1 %** | **33.1 %** |
| in PMC | 53.0 % | 54.5 % |

(Union of all linked pubs: T2D 44.8 % inEPMC / 31.9 % OA; onc 40.0 % / 21.5 %.)

**Over half of the very publications we currently mine as abstract-only have machine-readable full text sitting in an open API.**

### 3c. Measured poolable-rate LIFT (data-grounded; conversion-rate = ESTIMATE)

Script: `estimate_fulltext_lift.py` → `out/fulltext_lift.json`. Method: join each trial's index publication (`abstract.usable`) with its Europe PMC OA status. **Addressable = index pubs NOT usable from the abstract today but WITH open full text.** Only the *usable-given-full-text conversion rate* is estimated (swept 70/80/90 %); an RCT full text almost always carries the CONSORT results table (mean/SD/CI/effect+CI), so 70 % is conservative.

**T2D** (databank-confirmed denom, n=235):
- usable now (abstract-only): **67 (28.5 %)** ← reproduces the pilot headline exactly (join validated)
- addressable: **96** (has `inEPMC`) / **79** (CC-OA-subset only)
- **projected usable: 57.1 % → 61.2 % → 65.3 %** at conv 70/80/90 % (`inEPMC`); **~55 %** at the strict CC-OA floor (conv 80 %)
- ⇒ **28.5 % → ~55–61 %  (≈ 2×)**

**Oncology** (n=104):
- usable now: **14 (13.5 %)** ← reproduces pilot headline exactly
- addressable: **60** (`inEPMC`) / **41** (CC-OA)
- **projected usable: 53.8 % → 59.6 % → 65.4 %**; **~45 %** at strict CC-OA floor (conv 80 %)
- ⇒ **13.5 % → ~45–60 %  (≈ 3–4×)**

**Context:** this dwarfs the pilot's LLM-extraction lift (28.5 % → 39.6 %, +11 pts). Full text is the single largest lever available and it is **legally free** for the target user. It also directly attacks the pilot's stated hard gap — *"abstract+registry alone cannot adjudicate intra-trial numeric contradictions — needs the full-text methods section"* — which Europe PMC OA now supplies for ~half of trials.

### 3d. License texture (for redistribution vs. read-only)

Of the T2D `inEPMC` full texts: 121 CC-licensed (`cc by` 64, `cc by-nc` 31, `cc by-nc-nd` 23, …) + **39 with null license** (readable author-manuscripts, not redistributable). → For a scientist *reading + extracting numbers for their own meta-analysis*, all `inEPMC` counts. For *redistributing* extracted text, use the CC-OA floor (42 % T2D / 33 % onc).

---

## 4. Lighter assessment — regulatory + discovery sources

| Source | Open API? | Rate limit / key | License / terms | Value for this engine |
|---|---|---|---|---|
| **Drugs@FDA (openFDA)** | ✅ REST | no key 240/min + 1k/day; free key 240/min + **120k/day** ([openFDA auth](https://open.fda.gov/apis/authentication/)) | **US public domain** | **Med.** Approval letters, labels, review PDFs since 1998 for FDA-approved drugs. Adds regulator-grade results for a *small subset* of trials; no per-NCT link (needs drug-name join). Best as an oracle for CVOT-type flagship trials, not broad coverage. |
| **EMA EPAR / Policy 0070 CSRs** | ❌ no API | login-gated portal; on-screen or download-print ([EMA CDP](https://www.ema.europa.eu/en/human-regulatory-overview/marketing-authorisation/clinical-data-publication)) | EMA account; anonymised PDFs | **High content, low feasibility.** Full CSRs (the gold standard for reg-vs-pub), but manual, phased (only new active substances post-Sept 2023), no programmatic access. Not wireable now. |
| **OpenAlex** | ✅ REST | ⚠️ **now metered: free API key, "$1/day free usage"** (2026 change) ([developers.openalex.org](https://developers.openalex.org/)) | **Data CC0** | **Med.** Best for PMID↔DOI↔OA-location resolution + SR/citation graph. The metering is new — no longer the unlimited polite pool. Still cheap at our volume. |
| **Unpaywall** | ✅ REST | free; `?email=` required; ~100k/day | OA-location aggregator, open data | **Med-High as the #2 lever.** Given a DOI, returns the best legal OA copy — recovers full text for the **~47 % of index pubs NOT in Europe PMC**. Needs PMID→DOI first (NCBI ID converter / OpenAlex). Downstream cost: parsing publisher OA **PDFs** (harder than PMC XML). |
| **CORE** | ✅ REST v3 | unregistered ~5 req/10s; registered faster (free for public-research/unfunded) ([CORE API](https://core.ac.uk/services/api)) | OA-only corpus, BOAI | **Low incremental** — overlaps Unpaywall/Europe PMC; adds repository preprints/theses we don't need. |
| **Epistemonikos** | ✅ REST (beta) | **registration-gated token** (contact dev@epistemonikos.org) ([api.epistemonikos.org](https://api.epistemonikos.org/)) | Free database | **Med, DIFFERENT axis.** Its SR→included-study *matrix* (primary_studies + systematic_reviews with PMID/DOI) is exactly the "published-MA trial-list corpus" the pilot named as the missing ingredient for the **MA-omission** discrepancy class. Doesn't lift the poolable ceiling; opens a new class. |
| **Semantic Scholar** | ✅ REST | public no-key (shared, throttled); free key ~1→100 rps ([S2 API](https://www.semanticscholar.org/product/api)) | attribution required | **Low here** — good citation graph / TLDRs, but not full-text OA delivery; redundant with OpenAlex for our linking need. |

---

## 5. Ranked recommendation (toward the abstract+registry poolable ceiling)

1. **★ Europe PMC OA full text — WIRE FIRST.**
   - *Why:* largest measured gain — **T2D 28.5 % → ~55–61 %, onc 13.5 % → ~45–60 %** (≈2–4×), the biggest lever measured and bigger than the LLM layer. Directly closes the pilot's #1 stated gap (intra-trial numeric adjudication needs the methods section).
   - *Terms:* clean — free REST API, no key, CC-licensed OA subset. Mission-compliant.
   - *Effort:* **Low–Medium.** Data acquisition = one endpoint (`/{source}/{id}/fullTextXML`) added to the existing cached-HTTP layer; the real work is extending the deterministic extractor to parse full-text results tables (well-structured JATS XML, no OCR). Stays inside the deterministic-core seam.
   - *Guardrail:* the ~55–61 % is a projection — the conversion rate is the one estimated parameter. First implementation step should **measure the true conversion** on the addressable set before claiming the ceiling.

2. **★ Unpaywall + OpenAlex — WIRE SECOND** (same lever, non-PMC remainder).
   - *Why:* recovers legal OA full text for the ~47 % of index pubs not in Europe PMC. Estimated incremental **+5–12 pts** (ESTIMATE; bounded by publisher-OA availability and PDF-parse yield).
   - *Terms:* Unpaywall free (email param); OpenAlex CC0 but now metered ($1/day free) — fine at our volume; use OpenAlex/NCBI converter for PMID→DOI.
   - *Effort:* Medium — adds a PMID→DOI→OA-PDF path plus a PDF text extractor (heavier than XML).

**If the goal shifts** from poolable-rate to *discrepancy-class coverage*: **Epistemonikos** (#3) is the clean unlock for the MA-omission class, and **WHO ICTRP** (#4) broadens the non-publication denominator into non-US registries (its genuine, mission-relevant value) — but neither raises the poolable ceiling, and ICTRP's no-commercial term must be honoured.

**Do NOT prioritise:** EMA (no API), CORE/Semantic Scholar (redundant here), regional registries individually (weak APIs; reach via ICTRP if needed).

---

## 6. Cross-check, reproducibility, honest limitations

- **Internal cross-check (second code path):** an independent single-PMID live re-query of 40 T2D index PMIDs (`xcheck_internal.py`) matched the batched measurement **exactly** (11/40 OA, 19/40 inEPMC — the 40 are the oldest-by-PMID subset, hence below the 42 % full-set OA rate; older papers are less OA). Both code paths agree bit-for-bit.
- **Second-vendor cross-check (agy):** attempted twice (`agy_crosscheck_prompt.txt` → `out/agy_crosscheck_result*.txt`). agy 1.0.16 in non-interactive `--print` mode did **not execute** the independent measurement — it responded conversationally about its own CLI flags instead of hitting the Europe PMC API (a headless-tooling quirk, **not** a disagreement with the numbers). The second-vendor check is therefore **unconfirmed this session**; the internal two-code-path exact match (above) is the load-bearing cross-check. Re-run interactively (`agy -i`) to obtain the external replication if desired.
- **Truth-first flags:**
  - Poolable-lift % (§3c) is a **projection**: measured addressable counts × an **estimated** 70–90 % conversion. Conservative floor still ≈2× (T2D) / ≈3× (onc). Verify empirically before quoting as fact.
  - `inEPMC` (readable) > CC-OA (redistributable); we report both, lead with the mission-appropriate one per use.
  - ICTRP additional-coverage (+25–33 %) is a **literature estimate**, not measured on our corpus (which is 100 % CT.gov).
  - **Terms conflicts flagged:** ICTRP forbids commercial use; ISRCTN forbids database-population; OpenAlex is now metered; EMA has no API. None blocks the recommended #1/#2 (Europe PMC + Unpaywall).
- **Reproduce:** `python measure_registry_coverage.py`, `python measure_oa_fulltext.py`, `python estimate_fulltext_lift.py` (all read-only; Europe PMC responses cached to `./cache/`). Outputs in `./out/`.

---

*Files: `measure_registry_coverage.py`, `measure_oa_fulltext.py`, `estimate_fulltext_lift.py`, `xcheck_internal.py`; outputs `out/registry_coverage.json`, `out/oa_fulltext.json`, `out/oa_index_records.json`, `out/fulltext_lift.json`. No repo files outside `regpub_pilot/opendata_scan/` were modified; nothing pushed.*
