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
| `_synthetic_*` | analytic / seeded ground-truth | exercises the **CONFIRMED → poolable** path with a known HR |
| `dapa_hf` | DAPA-HF (McMurray 2019) | real published HR; stylized low-quality coords → trust gate **FLAGS** the gap |
| `keynote024` | KEYNOTE-024 (Reck 2016) | real published HR; small-N, wide recon CI → trust gate demonstration |

The `dapa_hf` / `keynote024` coordinates are the **stylized** examples bundled
with KMDigitizer (not pixel-accurate) — they intentionally reconstruct to an HR
that disagrees with the published value, demonstrating that the gate withholds a
crudely digitized curve rather than pooling it. Replace them with accurately
digitized coordinates to move a trial from FLAGGED to CONFIRMED.
