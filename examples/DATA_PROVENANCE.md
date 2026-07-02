# Example dataset provenance

Truth-first record of what each example dataset is and how it should (and should not)
be used. Updated 2026-06-20.

## `verde_2021_aspirin.csv` — REAL, citable

The classic six-trial aspirin secondary-prevention meta-analysis (CDP, AMIS, ISIS-2,
UK-TIA, SALT, ESPS-2), effect sizes on the log-odds-ratio scale, with risk-of-bias
indicators. This is the dataset referenced by Verde PE, *Biometrical Journal* 2021;63(2):406-422.
The named trials are real and the values are consistent with the published antiplatelet
secondary-prevention literature (e.g. ISIS-2 log-OR -0.251 ↔ OR ≈ 0.78).

**This is the empirical illustration used in the paper.** UBCMA pooled log-OR +0.011
(95% CI -0.125 to 0.117); DerSimonian-Laird -0.067 (-0.195 to 0.061), I² = 82.6%.
The DL baseline was independently reproduced by hand in R and by an independent agent
(Codex), agreeing to four decimal places.

## `bartos_2022_anderson.csv` — SYNTHETIC placeholder, NOT a real meta-analysis

The rows `study_1 … study_10` are **illustrative placeholder values**, not data extracted
from any published meta-analysis. They originate from a scaffolding step in the build plan
(`docs/superpowers/plans/2026-03-24-ubcma-three-phase-plan.md`, Step 2), which explicitly
flagged that the values had to be replaced with real extracted data from the source paper —
a replacement that never happened.

Because the underlying data is not real, **this dataset is not used as an empirical result
anywhere in the finalized paper or galley.** It is retained only as a load/convergence test
fixture (`tests/test_validation.py::BartosValidationTests`). Do not cite any pooled estimate
from this file as an empirical finding. If a media-violence illustration is wanted in future,
extract the real Anderson/Bartoš RoBMA dataset first.

## `simulated.csv`, `toy_studies.csv` — SYNTHETIC, for demos/tests only.
