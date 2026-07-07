# Figure drops — digitized KM curves for reconstruction

Each subdirectory is one trial's KM figure, digitized once (WebPlotDigitizer or
KMDigitizer's browser tool) and saved as `manifest.json`. `run_survival.py` loads
every `*/manifest.json`, keyed by `pmid`.

## Schema

```jsonc
{
  "pmid": "27718847",              // links the drop to the Phase-1 full-text doc
  "nct": "NCT02142738",            // optional
  "trial": "KEYNOTE-024",
  "endpoint": "Progression-free survival",
  "figure": "Fig 2A (PFS KM)",     // which figure was digitized (provenance)
  "source_citation": "Reck et al. NEJM 2016",
  "digitization": {
    "method": "webplotdigitizer",  // how coords were obtained
    "quality": "high",             // high|pixel → tier bonus; low → flagged
    "note": "…"
  },
  "tx":   { "label": "Pembrolizumab", "n0": 154,
            "coords": "0,1.00\n2,0.82\n…",   // "time,survival" per line
            "at_risk": "0,154\n6,90\n…" },   // "time,n" per line (optional but recommended)
  "ctrl": { "label": "Chemotherapy", "n0": 151, "coords": "…", "at_risk": "…" },
  "reported": { "hr": 0.50, "ci_lo": 0.37, "ci_hi": 0.68 }  // the paper's HR → trust gate
}
```

`coords` / `at_risk` accept either the newline string form above **or** a list of
`[time, value]` pairs. `at_risk` is optional; supply it whenever the paper prints
a numbers-at-risk row — it is what lets Guyot recover censoring correctly and is
the single biggest driver of reconstruction accuracy.

## Bundled examples

| Dir | Trial | Purpose |
|---|---|---|
| `belotecan_topotecan_os` | Belotecan vs Topotecan, relapsed SCLC (PMC7884704, BJC 2021) | **REAL** OA figure, hand-traced from Europe PMC → CONFIRMED (recon HR 0.56 [0.39–0.81] vs reported 0.69; recon medians 13.0/7.8 mo ≈ reported 13.2/8.2) |
| `_synthetic_*` | analytic / seeded ground-truth (`synthetic:true`) | exercises the **CONFIRMED → poolable** path + REML+HKSJ engine with a known HR |
| `dapa_hf` | DAPA-HF (McMurray 2019) | real published HR; stylized low-quality coords → trust gate **FLAGS** the gap |
| `keynote024` | KEYNOTE-024 (Reck 2016) | real published HR; small-N, wide recon CI → trust gate demonstration |

Drops with `"synthetic": true` are pooled **separately** (engine validation only) and never mixed into the clinical pool.

### Acquisition (outside the deterministic core)

Real curves are digitized from the **OA figure raster**, fetched from Europe PMC's
`www.ebi.ac.uk/.../{PMCID}/supplementaryFiles` (the OA zip carries the main figure
JPEGs; `europepmc.org/.../bin/…` is rate-blocked). The raster is cached under
`figures/_raster_cache/` which is **git-ignored** (publisher copyright) — only the
digitized coordinates in `manifest.json` are committed. Tracing is done by eye at
~1–2-month resolution, anchored on printed landmark survival % and the numbers-at-risk
row; reconstructed medians are checked against the paper's reported medians as a
sanity gate before the HR trust gate runs.

The `dapa_hf` / `keynote024` coordinates are the **stylized** examples bundled
with KMDigitizer (not pixel-accurate) — they intentionally reconstruct to an HR
that disagrees with the published value, demonstrating that the gate withholds a
crudely digitized curve rather than pooling it. Replace them with accurately
digitized coordinates to move a trial from FLAGGED to CONFIRMED.
