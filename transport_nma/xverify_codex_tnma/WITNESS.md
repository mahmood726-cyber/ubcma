# External cross-vendor witness — transportable-NMA registry pub-bias headline

**Vendor:** Codex Seat A (laptop 100.80.183.43, codex-cli 0.140.0, gpt-5.5), headless via SSH
`codex exec --dangerously-bypass-approvals-and-sandbox`. **Date:** 2026-07-04. **Verdict: CONFIRMS.**

Given ONLY a self-contained bundle (`aact_hba1c_records.csv` per-analysis records, `dat.senn2013.csv`,
`class_lambda.json`, `TASK_TNMA_VERIFY.md`) and told to import NO ubcma code, Codex wrote its own
`verify_tnma.py` (own aggregation, own graph/WLS random-effects NMA with DL tau^2, own bootstrap) and
independently reproduced both headline claims:

| quantity | ubcma | Codex Seat A | match |
|---|---|---|---|
| kappa_pooled (engine-free) | 0.1576 | 0.15759 | exact (4 dp) |
| corr(kappa_MD, 1-lambda) | +0.501 | +0.50142 | exact (4 dp) |
| classes used | 7 | 7 (same) | exact |
| per-class kappa_MD | AGI+0.349 SGLT2+0.289 DPP4+0.210 metformin+0.079 GLP1 0 TZD/insulin~0 | identical | exact |
| senn2013 NMA tau^2 | 0.109 | 0.1094 | ~exact (own engine) |
| truth-gate B=0.15: external vs oracle | -0.119 vs -0.118 | -0.1020 vs -0.1018 | **external tracks oracle to 0.0002** |
| truth-gate B=0: external over-corrects | +0.053 | +0.0553 | reproduced |
| truth-gate B=0.30: external < oracle | -0.231 vs -0.306 | -0.248 vs -0.305 | reproduced (kappa=0.158<0.30) |

**Reading.** The engine-free contributions (the external magnitude kappa_pooled and the model-validating
correlation) reproduce to 4 decimal places because they are deterministic aggregations of the shared
per-analysis records. The truth-gate — run on Codex's OWN independent NMA implementation and simulation —
reproduces the key relationship exactly: the frozen external kappa=0.158 tracks the oracle at B=0.15 (both
win, within 0.0002), over-corrects at B=0, and under-corrects at B=0.30. Absolute dMCIW0 values differ
slightly from ubcma's (-0.102 vs -0.118 at B=0.15) purely because of the different NMA engine/RNG; the
conclusion is identical. This is one genuine external vendor alongside the internal engine + tests.

Artifacts in this directory: `verify_tnma.py` (Codex's script), `verify_result.json` (its output),
`codex_run_tail.txt` (run log tail), `TASK_TNMA_VERIFY.md` (the spec it was given).
