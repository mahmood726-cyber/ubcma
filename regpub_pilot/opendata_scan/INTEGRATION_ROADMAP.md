# Open-Access Data Sources — Prioritized Integration Roadmap

**For:** the registered-vs-published discrepancy engine (branch `pilot/regpub-discrepancy`).
**Goal:** USE every openly-accessible source that adds coverage or completeness — ranked by gain-per-effort toward (i) the **abstract+registry poolable ceiling** and (ii) **developing-country coverage** for the no-institutional-access audience.
**Hard constraint:** openly-accessible data ONLY. **No paywalled full text.** Deterministic-core seam respected (network touches acquisition only; pooling/verify stay offline).
**Status:** read-only scan, 2026-07-07. No deploy, no push. Measurements reproducible from `opendata_scan/`.

Companion file `OPENDATA_SCAN_REPORT.md` holds the first-pass detail for the top two sources; this file is the full roadmap and supersedes it as the primary deliverable.

> **⚠️ PHASE 1 EXECUTED 2026-07-07 — see `../PHASE1_FULLTEXT_REPORT.md`.** The Europe PMC + OpenAlex/Unpaywall full-text lever is now wired and MEASURED end-to-end (not projected). Real result: poolable rate **T2D 39.6% → 46.0%**, **onc 24.0% → 32.7%**, **pooled 34.8% → 41.9% (+7.1 pts, +20% relative)**, with 100% source-span provenance and 0 fabricated numbers over 24 hand-validated datapoints. **The §0/§2 projection of "→55–61% / 45–60%" was OPTIMISTIC**: it assumed a 70–90% full-text→poolable conversion; the real conversion on gap trials is ~**21–22%** (most non-poolable trials are structurally non-poolable — single-arm/dose-finding/PK/safety/subgroup/median-only — even at full text). The entire lift came from Europe PMC JATS; bronze/green OA copies added coverage but 0 verified datapoints. Treat the table below as the *availability* ceiling, not the poolable ceiling.

---

## 0. ROADMAP HEADLINE — wire these first

| # | Source(s) | Gain (measured unless marked EST) | Effort | Terms OK? |
|---|---|---|---|---|
| **1** | **Europe PMC / PMC-OA full text** | Poolable ceiling **T2D 28.5% → ~55–61%**, **onc 13.5% → ~45–60%** (≈2–4×). Full text present for **53% / 55%** of index pubs. | **S–M** | ✅ |
| **2** | **OpenAlex + Unpaywall** (OA beyond PMC) | Full-text availability **→ 71.5% / 70.1%** (+18.5 / +15.6 pts). Combined poolable ceiling **→ ~65–75%** both areas. | **M** | ✅ read; bronze not redistributable |
| **3** | **WHO ICTRP** (one hub for PACTR/CTRI/ChiCTR/REBEC/ANZCTR/ISRCTN/EU-CTR) | **+25–33% more registrations** for the same questions (EST); the **developing-country / non-US coverage** play + broadens the non-publication denominator. Registration-only (no results). | **M** | ⚠️ no commercial use |
| **4** | **Conference abstracts** (ASCO/ESMO/ASH/ADA/EASD) — *lower-confidence tier* | Grey-lit results the median MA omits; **0 of 1,093** corpus pubs are currently conference-indexed → pure additive. Viewable-free, **scrape-only**, pooled **only with a confidence flag**. Yield EST. | **L** | ⚠️ view yes / redistribute no; Embase aggregator paywalled = out-of-mission |

**One-line plan:** Phase 1 = full-text lever (Europe PMC XML + OpenAlex/Unpaywall) — the measured 2–4× poolable jump. Phase 2 = WHO ICTRP for developing-country breadth + non-pub denominator. Phase 3 = regulatory oracle (Drugs@FDA) + MA-omission (Epistemonikos) + EU-CTIS results. Phase 4 = conference abstracts (flagged tier) + EMA CSRs (manual) + transportability context.

---

## 1. What was measured (corpus + method)

Reused the pilot's cached data only (no trial re-fetch). Corpus: **T2D** 600 trials / 302 index PMIDs / 1,104 union; **oncology** 350 / 154 / 470; **1,572 unique PMIDs**.

Measurements (scripts in `opendata_scan/`, outputs in `out/`):
- `measure_registry_coverage.py` — cross-registry IDs + country mix on cached CT.gov records.
- `measure_oa_fulltext.py` — live Europe PMC `resultType=core` per PMID → `inEPMC` / `isOpenAccess`.
- `estimate_fulltext_lift.py` — join OA status × current abstract-usability → poolable lift.
- `measure_unpaywall_increment.py` — OpenAlex (`pmid`→DOI+open_access, Unpaywall-derived) on the non-PMC remainder.
- `combined_lift.py` — combined (EPMC + OpenAlex/Unpaywall) poolable lift.
- pubtype scan — conference-abstract presence in the cached PubMed records.
- Cross-check: two independent code paths agree bit-for-bit (11/40 OA, 19/40 inEPMC on a sample). agy second-vendor run did not execute in headless mode (tooling quirk, not a disagreement).

**Estimate flag:** every number below is measured on the pilot corpus unless tagged **[EST]**. The full-text→poolable *conversion rate* is the single estimated parameter (swept 70/80/90%).

---

## 2. TIER 1 — Open full text (the poolable-ceiling lever) ★

This is where the measured gain is, and it directly closes the pilot's stated hard gap ("abstract+registry alone cannot adjudicate intra-trial numeric contradictions — needs the full-text methods section").

### 2.1 Europe PMC / PMC Open Access Subset — **RANK 1**
- **Open API:** free RESTful web service, **no key**; full-text **XML + PDF** for the OA subset via `.../{SOURCE}/{ID}/fullTextXML`. ([RESTful WS](https://europepmc.org/RestfulWebService), [OA downloads](https://europepmc.org/downloads/openaccess))
- **Terms → YES.** OA subset is CC-licensed ("generally allow[s] more liberal redistribution and reuse"; per-article license varies). Mission-compliant. Non-OA-but-in-EPMC full text is readable (author manuscripts) — fine for read+extract, not for redistribution.
- **Measured gain:** index pubs with full text in EPMC = **53.0% (T2D) / 54.5% (onc)**; CC-OA subset **42.1% / 33.1%**. Poolable lift (denomA, databank-confirmed): **28.5% → 55–61% (T2D)**, **13.5% → 45–60% (onc)** [conversion EST 70–90%; reproduces the pilot's 28.5%/13.5% base exactly].
- **Effort: S–M.** One endpoint into the existing cached-HTTP layer; real work = extend the deterministic extractor to parse JATS results tables (structured XML, no OCR). Stays in the deterministic core.

### 2.2 OpenAlex + Unpaywall — **RANK 2**
- **Open API:** OpenAlex REST (`works?filter=pmid:…`) returns DOI + `open_access{is_oa, oa_status, oa_url}` (Unpaywall-derived) for **all** articles, not just PMC. Unpaywall REST by DOI (email param). ([developers.openalex.org](https://developers.openalex.org/), [Unpaywall API](https://unpaywall.org/products/api))
- **Terms → YES (read).** OpenAlex data is CC0 but the API is **now metered — free key, "$1/day free usage"** (a 2026 change; trivial at our volume). Unpaywall free. ⚠️ Of the recovered copies most are **"bronze"** (free-to-read on publisher site, *no* license) — readable for extraction, **not** redistributable; only green/gold/hybrid/diamond carry reuse licenses.
- **Measured gain:** on the non-PMC remainder, OpenAlex/Unpaywall recovers a legal OA copy for **56/142 (T2D)** and **24/70 (onc)** → **full-text availability rises to 71.5% / 70.1%** (+18.5 / +15.6 pts over EPMC alone). Combined poolable ceiling: **28.5% → 65–75% (T2D)**, **13.5% → 61–75% (onc)** [conversion EST]. OA-status mix (T2D): bronze 39, green 7, hybrid 7, gold 2, diamond 1.
- **Effort: M.** Adds PMID→DOI→OA-URL path plus a **publisher-HTML/PDF** extractor for the bronze tier (heavier than PMC XML — the reason it's Phase 1.5/2, not Phase 1).

### 2.3 CORE — rank low (redundant here)
- Open REST v3; unregistered ~5 req/10 s; registered faster (free for public-research/unfunded). OA-only corpus, BOAI license. ([CORE API](https://core.ac.uk/services/api))
- **Terms → YES**, but **incremental value ≈ 0** — its OA full text largely overlaps Europe PMC + Unpaywall; adds repository preprints/theses we don't need. Skip unless a specific gap appears.

### 2.4 bioRxiv / medRxiv — rank low-med
- Metadata via RSS + API; **full-text TDM via a dedicated S3 bucket**; authors consent to text mining. Licenses vary (CC-BY … no-reuse). **Must link back, not re-host.** ([bioRxiv TDM](https://www.biorxiv.org/tdm), [medRxiv TDM](https://www.medrxiv.org/tdm))
- **Terms → YES (read/TDM).** **Value marginal for our *completed, already-published* trials** (the preprint is usually the same work as the published paper). Genuine value is narrow: earlier/interim results for very recent trials and a non-publication timeliness signal. Phase 4 optional.

---

## 3. TIER 2 — Registry coverage breadth (the developing-country play)

Because the pilot corpus was **sampled from ClinicalTrials.gov, 100% of it is already on CT.gov** — so no registry can add coverage to *this* set. Their value is (a) *additional* trials for the same questions and (b) **where the non-publication signal lives for non-US trials**. Measured mission-relevance: **59% of T2D trials (46% onc) have NO US site at all**; 151/59 have Asian sites, 32/12 African. Only **13.2% / 8.0%** carry a non-CT.gov registry ID (EudraCT dominant; CTRI 4, ChiCTR 0, PACTR 0) — cross-registration is rarely captured, so the extra trials must come from the registries directly.

### 3.1 WHO ICTRP — **RANK 3** (the one hub to wire)
- **Open API/bulk:** free ICTRP Web Service + **monthly full CSV** (WHO OneDrive, 10-day link) + SharePoint for increments. Aggregates ~18 primary registries. ([downloads](https://www.who.int/tools/clinical-trials-registry-platform/network/who-data-set/downloading-records-from-the-ictrp-database), [conditions of use](https://www.who.int/publications/m/item/who-ictrp-web-service---conditions-of-use))
- **Terms → CONDITIONAL.** Free with attribution + keep-current + show-processing-date, **but "shall not use … for marketing, promotional or commercial purposes."** ✅ for a research/personal engine; ✋ blocks a commercial product.
- **Results?** **No — registration metadata only.** So ICTRP lifts the *non-publication denominator* and *developing-country coverage*, **not** the poolable rate.
- **Gain [EST]:** CT.gov ≈ **75%** of ICTRP registrations; the other ~25% is led by EUCTR, then CTRI, IRCT, ChiCTR, ISRCTN → **+25–33% more registrations** for the same questions. ([Frontiers Pharmacol. 2023](https://www.frontiersin.org/journals/pharmacology/articles/10.3389/fphar.2023.1228148/full)) Poolable yield of those is low (no results, often no linked publication).
- **Effort: M.** One CSV/Web-Service ingest covers PACTR + CTRI + ChiCTR + REBEC + ANZCTR + ISRCTN + EU-CTR at once.

### 3.2 Individual regional registries — reach via ICTRP, not directly
| Registry | Region | Direct open API? | Verdict |
|---|---|---|---|
| **PACTR** (Pan-African) | Africa | ❌ web search only (free, no login) ([PACTR](https://pactr.samrc.ac.za/)) | **Weight UP for mission** but access via ICTRP. Only African WHO primary registry; feeds ICTRP monthly. |
| **CTRI** (India) | Asia | ❌ web only | Via ICTRP. 2nd-largest non-CT.gov contributor after EUCTR. |
| **ChiCTR** (China) | Asia | ❌ weak/unstable | Via ICTRP. |
| **REBEC** (Brazil) | LatAm | ❌ web only ([REBEC](https://ensaiosclinicos.gov.br/)) | Via ICTRP. |
| **ANZCTR** (Aus/NZ) | Oceania | ⚠️ API but "approved external groups" (gated) | Via ICTRP unless a partnership is set up. |
| **ISRCTN** | UK/intl | ✅ XML API + CSV ([terms](https://www.isrctn.com/page/terms)) | ⚠️ T&Cs **forbid "copy/download/store content to make or populate a database"** — conflicts with our use. Prefer ICTRP feed. |
| **EU-CTR (EudraCT)** | EU | legacy | Superseded by CTIS (below). |

### 3.3 EU-CTIS — **RANK ~7** (the results-bearing exception)
- **Open API:** public JSON API (`POST /ctis-public-api/search`, GET per trial) carrying **protocol *and* results**; now a WHO primary registry. ([CTIS notes](https://hendrik.codes/post/scraping-the-clinical-trials-information-system), [EMA](https://www.ema.europa.eu/en/news/clinical-trials-information-system-designated-who-primary-registry))
- **Terms → YES** (EU public register).
- **Value:** the only registry here with structured *results* — but **EU-only and post-2022**, so near-zero overlap with our completed historical corpus. Rises in value over time. Effort **M**.

---

## 4. TIER 3 — Open regulatory results (high-value oracle, narrow subset)

### 4.1 Drugs@FDA (openFDA) — **RANK ~5**
- **Open API:** REST, no key 240/min + 1k/day; free key 240/min + **120k/day**. ([openFDA auth](https://open.fda.gov/apis/authentication/))
- **Terms → YES** (US public domain).
- **Value:** approval letters, labels, statistical/medical **review PDFs** (since 1998) — regulator-grade results for FDA-approved drugs. Best as an **oracle for flagship CVOT/registration trials**, not broad coverage; **no per-NCT link** (needs a drug-name/indication join). Effort **M**.

### 4.2 EMA EPARs / Policy 0070 CSRs — **RANK ~13** (gold content, no API)
- **No API.** Login-gated portal; on-screen view or download-print; phased (new active substances post-Sept-2023). ([EMA CDP](https://www.ema.europa.eu/en/human-regulatory-overview/marketing-authorisation/clinical-data-publication))
- **Terms → CONDITIONAL** (EMA account; anonymised PDFs).
- **Value:** full **CSRs** are the gold standard for reg-vs-pub discrepancy — but **not programmatically accessible**; a manual per-drug pull. Keep as a manual deep-dive tool, not an automated source.

---

## 5. TIER 4 — Conference abstracts (grey-lit completeness lever, LOWER-CONFIDENCE) 

**Why it matters:** conference abstracts carry primary/interim results for trials the median published MA omits; rigorous MAs are *supposed* to search proceedings, and most don't. **Measured: 0 of 1,093 cached PubMed records are conference/meeting abstracts** — all journal articles. So this content is **entirely invisible** to the current PubMed-linkage channel → any recovery is **purely additive** to coverage.

**Confidence rule (non-negotiable in the pooling layer):** conference abstracts are interim, un-peer-reviewed, and may change at full publication. They are pooled **only** behind an explicit `confidence: conference_abstract` flag with **source-span provenance** (society + meeting + year + abstract ID), **never silently merged** with peer-reviewed effect estimates. Downstream: report as a separate sensitivity stratum (grey-lit-included vs peer-reviewed-only).

| Society / venue | Where abstracts live | Openly viewable? | Programmatic access | Terms | Est. yield |
|---|---|---|---|---|---|
| **ASCO** | JCO supplements + ASCO Meeting Library | ✅ free to view | ❌ no open API (site) | ⚠️ reuse via Copyright Clearance Center / presenter ([JCO permissions](https://ascopubs.org/about/permissions)) | oncology non-pub recovery, **[EST]** |
| **ESMO** | *Annals of Oncology* supplements (Elsevier) | ✅ abstracts free to view | ❌ scrape | ⚠️ publisher reuse terms | oncology, **[EST]** |
| **ASH** | *Blood* supplements + ASH site | ✅ free to view | ❌ scrape | ⚠️ publisher reuse terms | haem-onc, **[EST]** |
| **ADA** | *Diabetes* journal supplement | ✅ online ([ADA abstracts](https://diabetesjournals.org/journals/pages/scientific-sessions-abstracts)) | ❌ scrape | ⚠️ publisher reuse terms | T2D non-pub recovery, **[EST]** |
| **EASD** | *Diabetologia* supplement (Springer) | ✅ (whole supplement sometimes 1 PubMed entry, e.g. PMID 35920845) | ❌ scrape | ⚠️ publisher reuse terms | T2D, **[EST]** |
| **ACC / AHA** | *JACC* / *Circulation* supplements | ✅ free to view | ❌ scrape | ⚠️ publisher reuse terms | cardiometabolic, **[EST]** |
| **Embase** (the real aggregator) | 5.8 M abstracts / 18 k conferences | ❌ | subscription API | **✋ PAYWALLED — OUT OF MISSION** ([Embase](https://www.elsevier.com/products/embase)) | — (flag only) |

- **Terms → view YES / redistribute NO.** For a scientist reading + extracting numbers, viewing free society abstracts is legal; redistributing them is not. Embase — the one place that indexes them comprehensively with an API — is subscription-only, so it is **explicitly out of mission**.
- **Feasibility → L.** No clean APIs: each society needs a targeted, low-volume, rate-limited scraper of its supplement/meeting-library pages, plus abstract-format parsing. Deterministic-core seam holds (acquisition only).
- **Yield [EST]:** literature shows a large minority of conference-presented trials never fully publish or publish years late. Against our non-publication-flagged trials (raw flags 62.6% onc / 55% T2D), conference abstracts could recover *some* results — genuinely additive but **unquantified without wiring**; treat as a completeness/robustness stratum, not a poolable-ceiling driver.

---

## 6. TIER 5 — Review / protocol mapping (opens a *new* discrepancy class)

### 6.1 Epistemonikos — **RANK ~6** (unlocks MA-omission)
- **Open API (beta):** REST, **registration-gated token** (contact dev@epistemonikos.org). Free database; SR→included-study *matrix* (primary_studies + systematic_reviews with PMID/DOI). ([api.epistemonikos.org](https://api.epistemonikos.org/))
- **Terms → YES** (free, token).
- **Value — different axis:** provides the "published-MA trial-list corpus" the pilot named as the missing ingredient for the **MA-omission** discrepancy class (trials eligible for a published MA but left out). Does **not** lift the poolable rate; opens a class that's currently a GAP. Effort **M**.

### 6.2 PROSPERO — **RANK ~14** (low feasibility)
- Free, open, 500k+ protocols, but **no documented public bulk API** (web search / gated). ([PROSPERO](https://www.crd.york.ac.uk/prospero/))
- **Value:** SR protocols (planned vs reported analyses) — useful for outcome-switching context, but access friction is high. Backlog item.

---

## 7. TIER 6 — Context / transportability (marginal for the core engine)

These help the *transportability* layer ([[ubcma-transport-nma]]), **not** within-trial reg-vs-pub pooling. Include only if the transport program is active.

| Source | Open API | License | Terms → use? | Value |
|---|---|---|---|---|
| **World Bank Open Data** | ✅ REST | **CC-BY 4.0** ([WB licenses](https://datacatalog.worldbank.org/public-licenses)) | ✅ | Covariates (GDP, health spend) for effect-modifier / transport. **Marginal** to core. |
| **WHO GHO** | ✅ **OData API** ([GHO OData](https://www.who.int/data/gho/info/gho-odata-api)) | CC | ✅ | Baseline-risk denominators for transport. **Marginal**. |
| **IHME GBD** | ⚠️ Results Tool + data-use agreement ([IHME terms](https://www.healthdata.org/data-tools-practices/data-practices/terms-and-conditions)) | **CC BY-NC-ND** | ⚠️ non-commercial + **no-derivatives** | Disease-burden context for transport. NC-ND limits derived products; **marginal + restrictive**. |
| **Semantic Scholar** | ✅ REST (key free) ([S2 API](https://www.semanticscholar.org/product/api)) | attribution | ✅ | Citation graph / TLDRs; redundant with OpenAlex for our linking. **Low**. |

---

## 8. Ranked gain-per-effort (strict) + phased wiring plan

**Ranking key:** P = poolable-ceiling gain, D = developing-country coverage, E = effort, T = terms-clean.

| Rank | Source | P | D | E | Why this rank |
|---|---|---|---|---|---|
| 1 | Europe PMC OA full text | ★★★ | ★ | S–M | Biggest measured poolable jump, cleanest terms, XML parse. |
| 2 | OpenAlex + Unpaywall | ★★★ | ★ | M | Pushes full text to ~70%; bronze parse is the only cost. |
| 3 | WHO ICTRP | ✩ | ★★★ | M | The developing-country/non-US coverage hub + non-pub denominator (one ingest = 6 registries). Registration-only. |
| 4 | Conference abstracts (flagged tier) | ★★ completeness | ★★ | L | Purely additive grey-lit (0 in corpus now); scrape-only, confidence-flagged. |
| 5 | Drugs@FDA (openFDA) | ★★ (subset) | ★ | M | Regulator oracle for flagship approved-drug trials. |
| 6 | Epistemonikos | — (new class) | ★ | M | Unlocks MA-omission class. |
| 7 | EU-CTIS | ★ (EU results) | ★ | M | Only registry with results, but EU/post-2022 → low overlap now. |
| 8 | bioRxiv/medRxiv | ✩ | ★ | M | Marginal for completed trials. |
| 9 | World Bank / WHO GHO | — | ★ (transport) | S–M | Transportability context only. |
| 10 | CORE / Semantic Scholar | ✩ | ✩ | S | Redundant here. |
| 11 | EMA EPAR CSRs | ★★★ content | ★ | L (manual) | Gold CSRs but no API → manual deep-dive, not automatable. |
| 12 | PROSPERO / IHME | — | ✩ | M/L | Low feasibility or restrictive terms. |

### Phased wiring plan
- **Phase 1 — full-text lever (max measured gain).** Europe PMC OA `fullTextXML` ingest + extractor extension to parse JATS results tables. Add **OpenAlex** for PMID→DOI resolution (also improves linkage). → poolable **28.5%→~55–61% (T2D)**, **13.5%→~45–60% (onc)**.
- **Phase 1.5/2 — non-PMC OA + developing-country breadth.** **Unpaywall/OpenAlex** bronze/green fetch (publisher HTML/PDF parser) → full text ~70%, poolable **~65–75%**. In parallel, **WHO ICTRP** monthly CSV ingest → +25–33% registrations [EST], non-US non-publication denominator. *(Honour ICTRP no-commercial + skip ISRCTN direct DB-population.)*
- **Phase 3 — targeted results + new classes.** **Drugs@FDA** oracle (drug-name join) for flagship trials; **Epistemonikos** token for MA-omission; **EU-CTIS** JSON for EU results as coverage grows.
- **Phase 4 — completeness stratum + context.** **Conference abstracts** per-society scraper behind the `confidence: conference_abstract` flag (grey-lit sensitivity stratum, never silently merged); **EMA EPAR** manual deep-dive; **World Bank/WHO GHO** only if the transport layer is live.

---

## 9. Truth-first ledger (terms that block or constrain)

- **✋ Out of mission:** **Embase** (paywalled) — the only comprehensive conference-abstract API; flagged, not used.
- **⚠️ No commercial use:** **WHO ICTRP**, **IHME GBD** (also NC-**ND** = no derivatives). Fine for a research engine; would block a commercial product / derived redistribution.
- **⚠️ DB-population forbidden:** **ISRCTN** T&Cs — reach its records via ICTRP instead of direct scraping into our store.
- **⚠️ Read-yes / redistribute-no:** conference-abstract society sites; Europe PMC non-OA manuscripts; OpenAlex/Unpaywall **bronze** copies. All fine for read+extract-for-own-MA; none may be re-hosted.
- **⚠️ Metered (new 2026):** **OpenAlex** "$1/day free" — trivial at our volume, but no longer an unlimited polite pool.
- **⚠️ No API:** **EMA EPAR** (login portal), **PROSPERO** (web search), **PACTR/CTRI/ChiCTR/REBEC** (web only → via ICTRP), **ANZCTR** (gated).
- **Estimates, clearly marked:** poolable-lift % (conversion 70–90% EST); ICTRP +25–33% (literature EST); all conference-abstract yields (EST — unquantified without wiring).

## 10. Reproduce
```
cd opendata_scan
python measure_registry_coverage.py      # registry cross-coverage + countries
python measure_oa_fulltext.py            # Europe PMC OA fractions
python estimate_fulltext_lift.py         # EPMC-only poolable lift
python measure_unpaywall_increment.py    # OpenAlex/Unpaywall non-PMC remainder
python combined_lift.py                  # combined poolable lift
```
All read-only; API responses cached under `cache/` + `cache_upw/`; outputs in `out/`. Nothing outside `opendata_scan/` was modified; nothing pushed.
