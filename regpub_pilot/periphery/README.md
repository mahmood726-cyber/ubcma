# Periphery extraction layer — RCT full text + KM→IPD survival

Two of Mahmood's **existing** tools, wired into the reg-vs-pub pilot's Phase-1
full-text pipeline as **offline, deterministic periphery components**. Nothing
here touches the network — the only networked step in the whole survival path
stays Phase-1 acquisition (`src/fetch_fulltext.py`). Extraction, reconstruction,
the trust gate and pooling are pure functions over cached inputs.

## The two tools

| Component | Wraps | What it does |
|---|---|---|
| `rct_fulltext.py` | **rct-extractor-v2** (`rct_extractor`) | Deterministic RCT effect / arm-level extraction over OA full text → HR/OR/RR/MD + CI + p + SE, each with a verbatim span and a confidence tier. |
| `km_ipd.py` | **KMDigitizer** (Guyot 2012) | KM curve → pseudo-IPD reconstruction, log-rank HR re-derivation, and the **trust gate**: re-derived HR vs the paper's reported HR. |

Both tools are located at runtime by `toolpaths.py` (env override → candidate-root
discovery → **fail closed**; no hardcoded drive in shippable code). Set
`KMDIGITIZER_HOME` / `RCT_EXTRACTOR_HOME` if your clones live elsewhere.

## Where it plugs into Phase 1

```
 src/fetch_fulltext.py ──(Europe PMC JATS / OA HTML)──▶ data/fulltext_parsed/<pmid>.json
                                                          { results, full_text, tables[], ... }
                                                                     │
                                     ┌───────────────────────────────┴───────────────────────────┐
                                     ▼                                                             ▼
                         periphery/rct_fulltext.py                                   periphery/km_ipd.py
                         rx.extract(results/full_text)                    reconstruct_from_drop(figures/<pmid>/manifest.json)
                                     │                                                             │
                                     ▼                                                             ▼
                        provenance + confidence-tier                         pseudo-IPD → log-rank HR → TRUST GATE
                          effect datapoints                            (reported HR ∈ recon CI  AND  |gap| ≤ tol ?)
                                     └───────────────────────────────┬───────────────────────────┘
                                                                     ▼
                                              periphery/run_survival.py  →  out/survival_extraction_<area>.json
                                   CONFIRMED → poolable (REML+HKSJ via src/pool.py) · FLAGGED → discrepancy (withheld) · UNGATED → held out
```

The integration point is the **parsed full-text object** produced by
`src/jats.py`. The periphery never re-parses XML/PDF and never fetches — it reads
that cached object, so the deterministic-core seam is preserved exactly.

## KM curves are an input artifact, not a raster we trace

Automated tracing of a KM *curve* out of a raster figure needs pixel work and is
deliberately **out of scope** for the deterministic core. A curve is supplied as
a **figure drop**: digitized `time,survival` coordinates (from WebPlotDigitizer or
KMDigitizer's own browser tool) plus the at-risk table and arm sizes, dropped at
`periphery/figures/<pmid>/manifest.json`. See `figures/README.md` for the schema.

Where a paper clearly **has** a KM curve but no drop exists, `run_survival.py`
records it as `km_present_not_digitized` — an honest gap (mirroring Phase-1's
`pdf_unparseable` bound), never a silent skip. The **numbers-at-risk** row is
often present as *text* in the JATS tables, so `numbers_at_risk_from_tables()`
recovers it deterministically to strengthen a drop that lacks one.

## The trust gate (why reconstructed HRs are not blindly pooled)

`km_ipd.trust_gate` marks a reconstruction **CONFIRMED** only when BOTH hold:

1. the paper's reported HR lies inside the reconstructed 95% CI, and
2. the relative gap `|recon − reported|/reported ≤ pct_tol` (default 0.20).

- **CONFIRMED** → poolable datapoint, flagged `reconstructed_from_figure`.
- **FLAGGED** → surfaced as a discrepancy and **withheld from pooling**.
- **UNGATED** → no reported HR to compare; held out (never counted as agreement).

This is what stops a crude digitization (whose reconstruction disagrees with the
published HR) from silently entering a meta-analysis. Guyot et al. (2012) match
the source HR to ~1–3% *only* with accurate digitization + at-risk numbers; the
gate operationalises that caveat.

## Run

```bash
cd regpub_pilot
# point at the concurrent Phase-1 lane's parsed cache if running from a worktree:
REGPUB_FT_PARSED="F:\\ubcma\\regpub_pilot\\data\\fulltext_parsed" \
PILOT_AREA=onc python -m periphery.run_survival
python -m pytest periphery/tests -q
```

## Provenance & confidence on every datapoint

- **RCT effects**: `provenance{source_doc=PMID, channel, section, source_span,
  char_start/end, tool}` + `confidence_tier ∈ {A,B,C}` (folded from the
  extractor's calibrated confidence / plausibility / needs-review).
- **Reconstructed survival**: `reconstructed_from_figure=true`,
  `provenance{figure, digitization{method,quality}, at_risk_source, tool}`,
  `trust_gate{verdict, pct_gap, reported_in_recon_ci}`, and a
  `confidence_tier ∈ {reconstructed_verified[_hi], reconstructed_discrepancy,
  reconstructed_ungated}`.
