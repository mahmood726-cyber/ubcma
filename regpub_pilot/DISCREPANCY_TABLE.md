# Registered-vs-Published Discrepancy at Scale — Malaria & TB (openly-accessible sources only)

**Date:** 2026-07-13 · **Branch:** `wip/preserve-2026-07-12` · staged/local only — no push.
**Mission:** a Makerere researcher (no Embase, no paywalled full text, weak laptop) must produce
synthesis MORE truthful than the well-resourced version, from open sources alone. Pre-registration
of refutation criteria: `PRE_REGISTRATION_harms.md` (written before running). Deterministic core;
harms + routing added this session. Cross-vendored with agy/Gemini (decorrelated google family).

## The discrepancy / coverage table (per disease)

| Metric | malaria | TB | T2D | oncology |
|---|--:|--:|--:|--:|
| N completed trials | 913 | 705 | 600 | 350 |
| results posted % | 20.8 | 24.0 | 28.8 | 28.9 |
| **reporting-pub linkage %** | **66.0** | **59.1** | 45.0 | 37.4 |
| abstract usability % (det) | 17.6 | 17.0 | 28.5 | 13.5 |
| **non-publication raw %** | **34.0** | **40.9** | 55.0 | 62.6 |
| registry serious-AE table present % | ~99–100 | ~99–100 | ~99–100 | ~99–100 |
| registry ≥1 serious event % (of results-posted) | 55.8 | 61.5 | 56.1 | 79.2 |
| **harms omission % (abstract silent)** | 18.6 | 19.7 | **32.3** | 12.1 |
| **harms non-quantification gap %** | **76.7** | **67.6** | **87.7** | **54.5** |
| routing registry-table : abstract-prose ratio | 1.67× | 1.96× | 2.47× | 4.21× |

(Efficacy-numeric classes — enrollment/direction/significance/endpoint-switch — are reported in
`metrics_<area>.json` but were shown in the T2D adjudication to be ~0 *confirmed* true positives:
artifacts of substudy-N, verbose endpoint names, and secondary publications. Non-publication and
harms are the classes with real signal.)

## Findings vs pre-registration (truth-first — refutations honored)

### Claim H — "harms omission is the dominant discrepancy" → **REFUTED as stated; a weaker form SUPPORTED**
- Pre-registered bar: pure omission ≥ 40% AND higher than every efficacy class. Observed pure
  omission = **12.1–32.3%** (only T2D approaches 40%). **REFUTED.**
- But the **harms non-quantification gap = 54.5–87.7%** is dominant in every disease: the registry
  holds a structured serious-AE table (~99–100% of results-posted trials), yet the abstract
  essentially never quantifies harms. The harms *numbers* are almost never in the prose.
- **Discipline caught inflation:** an earlier cut counted zero-event tables and "safety"-mentioning
  abstracts as omissions (malaria omission 28%→18.6% after fixing `has_sae_data` to require ≥1 real
  event and adding "safety" to the lexicon). The honest direction was *down*.
- **Hand-validated 10/10** flagged omissions are truly silent on harms (e.g. Seasonal Malaria
  Vaccination, NEJM — 262 serious events, abstract silent on safety). **Cross-vendor: agy/Gemini
  agreed 7/8** (the miss = agy counting disease-mortality as a harm — a disclosed boundary case).
- **Caveat:** some databank-linked index abstracts are secondary/mechanism sub-papers (immunogenicity,
  PK) that legitimately omit harms — so the omission rate partly reflects *which paper a searcher
  retrieves*, not proof the main paper suppressed harms. The quantification-gap claim does not depend
  on this and is the robust headline.

### Claim R — "route to the registry table, not the abstract prose" → **SUPPORTED (strongly for harms)**
- Efficacy numbers: the registry table is the sole route **1.67× (malaria) → 4.21× (oncology)** more
  often than the abstract prose. ≥2× (pre-reg bar) met for T2D and oncology; malaria 1.67× is below
  2× but still >1.5×. Directionally the registry table wins in every disease.
- **Harms numbers: the routing rule is overwhelming** — the serious-AE counts are in the registry
  table but not the abstract in **54–88%** of trials. For harms, "go to the registry table" is not
  advice, it is the only option.
- **Actionable Tuesday rule:** for any registered trial, pull the effect and (especially) the harms
  from the **ClinicalTrials.gov results table**, not the abstract. The paywall protects the prose;
  the numbers are open and structured. This is the opposite of standard practice.

### Claim C — "malaria/TB do better than cardiometabolic/oncology" → **AXIS-DEPENDENT (as pre-registered)**
- **SUPPORTED** on openness: reporting-pub linkage **66/59% vs 45/37%**, and **lower non-publication
  (34/41% vs 55/63%)** — neglected-disease trials are published and linked *more*, not less.
- **REFUTED** on abstract usability: malaria/TB **17% vs T2D 28.5%** — their abstracts are *more*
  relative-only / median-only, so the abstract is a *worse* source there. The advantage is in open
  availability and linkage, not in what the abstract hands you — which makes the registry-table
  routing rule *more* important for exactly this researcher.

## Bottom line for the Makerere researcher
From open sources alone, the more-truthful synthesis is achievable — but only by **reading the
registry results table, not the abstract**, especially for **harms**, which the abstract quantifies
in ≤ 1 in 8 trials while the registry quantifies them in ~99%. The neglected-disease literature is
*more* open (higher linkage, lower non-publication) yet its abstracts are *less* usable — the exact
regime where registry-first triangulation wins.

## Artifacts
`out/discrepancy_table.json`, `out/harms_{malaria,tb,t2d,onc}.json`,
`out/harms_agy_crosscheck.json`, `PRE_REGISTRATION_harms.md`, `src/harms.py`, `src/harms_run.py`.
Reproduce: `PILOT_AREA=<area> python harms_run.py <area>`.
