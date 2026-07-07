# Survival digitization — verification & truth-first triage

## Triage of the 16 `km_present_not_digitized` oncology papers

The high-value pivotal trials requested (OAK, CheckMate-017/057, KEYNOTE-010,
PAOLA-1, VELIA) are **absent from the OA corpus** — paywalled NEJM/Lancet,
unreachable under the pilot's no-paywall premise (verified: none present in
`data/fulltext_parsed/`). Their KM figures cannot be digitized.

Of the 16 OA-flagged papers, figures + designs were inspected. Exactly **one** is a
genuine two-arm survival RCT with a reported HR and a fetchable OA KM figure:

| PMID | What it is | Two-arm OS/PFS + reported HR? |
|---|---|---|
| **33191408** | Belotecan vs Topotecan, relapsed SCLC (RCT) | **YES** — Fig 2b OS, HR 0.69, at-risk table |
| 31562758 | POLO (olaparib vs placebo) | two-arm but KM = **HRQoL** time-to-deterioration, not OS/PFS |
| 37350968 | immunotherapy cohort | **single-arm** PFS (n=40, one curve + 95% CI band) |
| 23578144, 34253577, 30060083, 31576173, 37840530, 36754451, … | phase-I / single-arm / observational-bioinformatic / QoL / symptom | no comparative survival KM |

So only 33191408 yields a comparative survival HR from OA sources. This is itself a
finding: the OA oncology subset is dominated by single-arm, phase-I, QoL and
observational papers, while the multi-trial pivotal OS-KM classes sit behind paywalls.

## Reconstruction of PMID 33191408 (belotecan vs topotecan OS)

Digitized from the Europe PMC OA figure raster (Fig 2b), anchored on the printed
12-mo OS (58% / 27%) and the numbers-at-risk row (belotecan 72→39→11→6→3→0,
topotecan 76→20→6→2→0→0). Raster acquisition is an artifact step outside the
deterministic core; only the traced coordinates are committed.

**Sanity gate (medians):** reconstructed 13.0 / 7.8 mo vs reported 13.2 / 8.2 mo — match.

**Trust gate (HR):**

| Estimator | HR (belo vs topo) | 95% CI | p | gap vs reported 0.69 |
|---|---|---|---|---|
| KMDigitizer log-rank (Mantel-Haenszel) | 0.56 | 0.388–0.809 | 0.002 | 19% |
| **Independent R `survival::coxph`** (cross-impl. check) | **0.587** | 0.415–0.828 | 0.0025 | 15% |
| Reported (paper) | 0.69 | 0.48–0.99 | 0.018 | — |

Reported HR 0.69 lies inside both reconstructed CIs; gap < 20% tol → **CONFIRMED**.
The independent R Cox re-derivation (a different codebase entirely) reproduces the
KMDigitizer HR, so the reconstructed effect is not a tool-specific artifact. Note the
reconstruction shows a somewhat stronger separation (p≈0.002) than the reported
log-rank (p=0.018) — within tolerance, but flagged here for honesty.

## Pooling

Only **k=1** real CONFIRMED OS reconstruction exists among OA-reconstructable papers,
so **no multi-trial clinical pool is formable** (the pivotal multi-trial IO-NSCLC-OS
class is paywalled). The REML+HKSJ pooling engine is validated separately on the
synthetic drops (`synthetic:true`, pooled apart, engine-check-only: k=2, HR 0.772).

## Before / after (oncology KM→IPD survival)

- reconstructed CONFIRMED survival datapoints: **0 → 1** (real: belotecan/topotecan OS).
- `km_present_not_digitized`: **16 → 15**.
- Full-text-extracted tier-A survival HRs (rct-extractor, unchanged): 13.
- Multi-trial pooled survival HR from reconstruction: **not formable** (k=1 real).
