# Registered-vs-Published Discrepancy Engine — Feasibility Pilot

**Branch:** `pilot/regpub-discrepancy` · **Status:** staged results only (no push/deploy).

## Mission

Serve a scientist in a developing country with **no paywalled full-text access**.
Everything runs on **openly accessible data only**:

- **ClinicalTrials.gov API v2** (registry protocol + results) — live, free.
- **PubMed E-utilities** (abstracts + databank NCT↔PMID links) — live, free.

No AACT Postgres dump, no journal full text. Two *independent* readings of each
trial's truth — the abstract and the registry each cover the other's gaps.

## Deterministic-core seam invariant

The only network use is **data acquisition** (`common.py`, `fetch_*`, `link_*`),
cached to `data/`. All **extraction, diff, pooling, and structural checks are pure,
model-free, offline-serializable** functions over cached JSON (`extract.py`,
`diff.py`, `metrics.py`). Same input → same output; no model in the classification path.

## Pipeline

```
fetch_ctgov.py   # page completed interventional T2D trials, cache full records
link_pubmed.py   # NCT->PMID via CT.gov refs + PubMed [si]; cache abstracts
extract.py       # registry facts + abstract usability verdict (rule-based)
diff.py          # three-state poolability + discrepancy classifiers -> out/trials.jsonl
metrics.py       # deliverables + validation sample -> out/metrics.json
```

## Reproduce (from repo root, `regpub_pilot/src/`)

```
python fetch_ctgov.py 600
python link_pubmed.py
python diff.py
python metrics.py
python test_extract.py     # extractor sanity tests
```

Raw caches (`data/ctgov/`, `data/pubmed/`) are git-ignored (reproducible, large);
`out/` analysis artifacts are the staged deliverable.

## Deliverables (see `PILOT_REPORT.md`)

1. Abstract-extraction **usability rate** + reason breakdown.
2. Registry-results **coverage**.
3. Per-class discrepancy **rate** + hand-adjudicated precision/recall.

## Note — RapidMeta feedstock

The poolable dual-source `BOTH`/`ONE` extractions (`out/trials.jsonl`) double as
RapidMeta inline `realData` feedstock: each carries a structured primary effect
(point/CI/p or group means) with provenance (registry vs abstract) and a confidence
tier (dual vs single source).
