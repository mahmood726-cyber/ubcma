# Open-supplement recovery of the paywalled-paper loss pocket — feasibility probe

**Branch:** `pilot/regpub-open-supplements` · **Dir:** `regpub_pilot/paywall_recovery/`
**Date:** 2026-07-07 · **Access premise:** read-only; genuinely-open channels ONLY; local commits, no push.
**Second vendor:** agy (Google Antigravity CLI) — live, decorrelated re-extraction. Codex down (not blocking).

---

## Headline

- **Genuine open-supplement recovery of the paywalled pocket: 1 / 108 papers ≈ 0.9%** (agy-CONFIRMED, max abs dev 0.0).
- Including one open-license article that was in the pocket only for lack of a PDF parser (a *tooling* gap, not a paywall): **2 / 108 ≈ 1.9%**.
- **Pivotal survival HRs newly recovered: 0.** No open supplement in the pocket contained a Kaplan–Meier curve + numbers-at-risk table, so the re-derive-HR trust gate had nothing to run on.
- **The two cleanest, explicitly-sanctioned channels (Europe PMC + NCBI PMC OA supplement bundles) recover exactly 0** — every in-PMC paper in this pocket is an author-manuscript that is **not** in the OA subset, so both open-redistribution APIs *refuse* to serve its supplement.

**Honest bottom line:** open supplements close only a **~1% sliver** of this paywalled-loss pocket. This is a genuinely low rate, and the probe says so plainly. The barrier is not that supplements don't exist — 10 papers *have* an EPMC supplement bundle — it is that the supplements sit behind the **same access control as the article** (the OA-subset / redistribution flag), which is exactly the ethical line we refuse to cross.

---

## 0. Scope correction (truth-first)

The prompt named OAK, CheckMate-017/057, KEYNOTE-010, PAOLA-1 and VELIA as target classes. **None of these trials is in the pilot corpus at all** — not by PMID and not by NCT (verified: 0 index hits for all six PMIDs and all six NCT IDs in `data/ctgov_index_onc.json` / `data/links_onc.json`). The pilot corpus is a different CT.gov-derived sample. So this probe measures recovery on the **actual 108-paper paywalled pocket that *is* in the corpus**, not on the named exemplars. The earlier survival note already flagged that the pivotal OS-KM classes are paywalled NEJM/Lancet and absent from the OA corpus; this probe confirms they are absent from the whole denominator.

## 1. The paywalled loss pocket (denominator = 108)

"Paywalled" = a confirmed-index target whose **main text could not be parsed** under the no-paywall premise (`fulltext_fetch` status ≠ `parsed`): **onc 38 + t2d 70 = 108** unique papers. Structure:

| Sub-pocket | n | Open-supplement route? |
|---|---:|---|
| In PMC as **author-manuscript, non-OA-subset** (`inEPMC=Y`, `isOpenAccess=N`) | 31 | supplement bundle exists for 10, but **gated** (§2) |
| **Truly closed** — no OA copy anywhere (`oa_status` closed/none) | 44 | none by definition |
| **Bronze** free-to-read (publisher page, not redistributable) | 20 | supplement behind publisher control |
| **Open-license** (gold 2 / hybrid 6 / diamond 1 / green 4) | 13 | the only place a genuinely-open supplement can live (§3) |

(The 31 in-PMC papers each returned `epmc_jats` **fetch-miss** in the original run: EPMC holds the record but has **no machine-readable full-text JATS** for author manuscripts — the exact case this probe was built to interrogate.)

## 2. Coverage by channel

| Channel | Legitimate endpoint | Candidates | Genuinely open & served | Coverage of pocket |
|---|---|---:|---:|---:|
| **A — Europe PMC supplementaryFiles** | `…/rest/{PMCID}/supplementaryFiles` | 31 (have PMCID) | **0** | 0.0% |
| **B — NCBI PMC OA Web Service** | `…/pmc/utils/oa/oa.fcgi?id={PMCID}` | 31 (have PMCID) | **0** | 0.0% |
| **C — publisher/repository open-license** | DOI / OA-platform (figshare, J-STAGE, repos) | 13 | **2 retrieved** (1 true supplement) | 1.9% |
| **D — preprint server supplement** | bioRxiv / medRxiv | 0 | 0 | 0.0% |

**Why A and B are both 0:** the EPMC endpoint returns, verbatim, `errMsg: "Article with id PMCxxxxxxx is not open access one"` for **all 31**; the NCBI OA service refuses the same 31 (not in the PMC Open Access Subset). **10 of the 31 have `hasSuppl=Y`** — EPMC physically holds a supplement bundle for them (Blood, JAMA Oncology, Diabetologia, Gastroenterology, …) — but serves none, because every one is `isOpenAccess=N`. *Supplement exists ≠ supplement open.*

**Channel C detail (13 open-license candidates):** cleanly retrieved on a 200 = 2 (figshare CC BY 4.0; J-STAGE diamond). The other 11 were **blocked or absent and recorded as such, not routed around**: UCL institutional-repo PDF → `404`; diabetesjournals / Annals of Oncology / Wiley / GIE / DRCP publisher PDFs → `403` anti-bot; two 2026 gold/CC-BY papers (Wiley EDM, BMC Nutrition) → not yet in any OA aggregator and their DOI landings block bots.

## 3. Content yield of what was retrieved (n = 2)

| Content class | count |
|---|---:|
| Poolable **structured tables** (direct extraction, no digitization) | **2 / 2** |
| **KM curve + numbers-at-risk** (reconstruction candidate) | **0 / 2** |

## 4. Worked recoveries

### 4a. TRUE open-supplement recovery — PMID 24552155 (albiglutide, Japanese T2D dose-finding RCT)
- **Article access:** subscription (*Current Medical Research & Opinion*). Main text unreachable under the premise (figshare landing had no article text).
- **Open channel:** a **CC BY 4.0** green deposit on **figshare** (open-data repository) carrying the supplement `icmo_a_896327_sm0001.pdf` (retrieved via the figshare open API, 200).
- **Recovered content:** *Supplemental table 1 — HbA1c change from baseline at week 16 by prior therapy*: LS-mean differences vs placebo with 95% CIs across three albiglutide arms × two prior-therapy strata (18 numbers). Poolable as structured data — **no digitization**.
- **Consensus-or-flag (claude vs agy, decorrelated re-extraction):** all 18 values identical, **max abs dev = 0.0 → CONFIRMED** (`out/recovery_xcheck_verdict.json`, agy raw in `out/agy_figshare_xcheck.txt`). Both vendors independently restored the negative signs (HbA1c reductions) that the PDF text layer dropped.

### 4b. Open-license article — PMID 25186922 (*Circulation Journal*, diamond OA, 2014)
- Retrieved cleanly from J-STAGE (200). Contains structured result tables. **But this is a *diamond-OA* (free) article** — it sat in the loss pocket only because the pilot's deterministic core has no PDF parser, **not because of a paywall**. Flagged as a *tooling-gap* recovery, **not** counted in the genuine open-supplement rate.

### 4c. Survival / KM recovery — **none**
- 0 open supplements in the pocket contained a KM curve + at-risk table. The re-derive-HR **trust gate** (CONFIRMED iff reported HR ∈ recon CI and gap ≤ 20 %) therefore produced **0 CONFIRMED, 0 FLAGGED** — nothing to reconstruct. This is consistent with the prior survival-periphery finding: the multi-trial pivotal OS-KM classes are paywalled, and (see §0) the named ones are not even in the corpus.

## 5. Recovery-rate estimate (marked as estimates)

| Estimate | n / 108 | % of pocket |
|---|---:|---:|
| Genuine open-supplement recovery of poolable data | 1 | **≈ 0.9%** |
| + open-license article recoverable with a PDF parser (different gap) | 2 | **≈ 1.9%** |
| Pivotal survival HRs newly recovered | 0 | 0% |
| KM+at-risk reconstruction candidates in open supplements | 0 | 0% |

These are point estimates on one corpus (108 papers, T2D + oncology); treat as a **feasibility signal, not a population rate**. The direction is robust and unlikely to move with more papers: the rate is capped by the OA-subset flag (channels A/B) and by publisher anti-bot controls (channel C), neither of which a larger sample relaxes.

## 6. Legal / ethical log

**Open-and-USED (genuinely free, redistributable):**
- PMID 24552155 — figshare item 11830233, licence **CC BY 4.0**, supplement PDF via figshare open API (200).
- PMID 25186922 — J-STAGE **diamond OA** article PDF (200). *(open-license; flagged tooling-gap, not paywall recovery)*

**Gated / blocked — RECORDED, NOT routed around (no bypass, mirror, or paywall circumvention attempted):**
- 31 in-PMC author-manuscripts — EPMC supplementaryFiles + NCBI OA service both **refused** ("not open access"). Recorded gated; not used.
- PMID 29320312 — UCL institutional-repo PDF `404` (absent). Not used.
- PMIDs 34737187, 22420843, 30481287, 36514847, 38280531, 38978184, 39368488 — publisher PDF endpoints `403` (anti-bot). Recorded blocked; not retried via any alternate path.
- PMIDs 41891171, 42169191 — 2026 gold/CC-BY, not yet in any OA aggregator; DOI landings block bots. Recorded; not used.
- 20 bronze free-to-read papers — publisher-hosted, not redistributable, supplements behind the same control. Not probed for supplement extraction.

Every network call went through the pilot's single sanctioned throttled fetch path (`src/fetch_fulltext.http_get_bytes`), which fails closed on error payloads. No access control was circumvented at any point.

## 7. Reproduce

```
python build_set.py          # define pocket + EPMC core metadata  -> out/paywalled_set.json
python probe_supp.py         # channels A/B (EPMC + NCBI OA)        -> out/supp_probe.json
python probe_channelC.py     # channel C open-license retrieval     -> out/channelC_probe.json
python compute_coverage.py   # consolidate coverage + estimate      -> out/coverage_summary.json
python -m pytest test_paywall_recovery.py -q   # 5 regression guards on the headline numbers
```
