# Reproducing the UBCMA headline simulation results

The manuscript's Tables 1–3 are built from the **pilot tier** of the factorial
simulation study:

| factor                | levels                                   |
|-----------------------|------------------------------------------|
| selection strength    | none, moderate, strong                   |
| quality bias          | none, moderate                           |
| heterogeneity (tau)   | 0.0, 0.1                                  |
| **scenarios**         | 3 × 2 × 2 = **12**                        |
| replicates / scenario | **50** (600 total)                       |
| studies per dataset   | k = 30                                    |
| true effect           | mu = 0.2, all-RCT designs                 |
| methods               | UBCMA + **8 comparators** (9 total)       |

Comparators: `dl`, `dl_hksj`, `reml`, `reml_hksj`, `trim_and_fill`,
`pet_peese`, `copas`, `quality_effects`.

## Seed

**Random seed = 42** (the value documented in the manuscript:
*"Simulation results can be reproduced using `ubcma study --tier pilot --seed 42`"*).

The run is deterministic: data generation is seeded per replicate
(`seed + scenario*10000 + rep`), and UBCMA's multi-start optimiser uses a fixed
`restart_seed = 12345`.

## How to regenerate

```bash
# Option A: the dedicated reproduction script (writes the files in this folder
# and prints reproduced-vs-published deltas)
python scripts/reproduce_paper_results.py --force

# Option B: the make target (same thing)
make paper-results

# Option C: the CLI directly (writes scratch output to results/pilot/)
python -m ubcma study --tier pilot --seed 42 --replicates 50 --output results
```

Expected wall-clock: ~30–60 minutes (UBCMA's multi-start fit dominates).

## Committed artifacts (this folder)

| file                          | contents                                                        |
|-------------------------------|-----------------------------------------------------------------|
| `pilot_summary.csv`           | overall per-method metrics — source of **Table 1**              |
| `pilot_by_quality_bias.csv`   | per-method metrics split by quality-bias level — source of **Table 3** worst-case coverage |
| `pilot_simulation_study.csv`  | full per-replicate record (600 reps × 9 methods) — audit trail  |

## Reproduced values (seed 42, this commit)

Regenerated 2026-06-19. The reproduced numbers match the published manuscript
values to within Monte-Carlo rounding (largest absolute delta 0.0004):

| quantity                                   | reproduced | published |
|--------------------------------------------|-----------:|----------:|
| UBCMA RMSE                                  |     0.0696 |     0.070 |
| UBCMA coverage                              |     0.8883 |     0.888 |
| DerSimonian-Laird coverage                  |     0.5967 |     0.597 |
| REML-HKSJ coverage                          |     0.6383 |     0.638 |
| trim-and-fill coverage                      |     0.3900 |     0.390 |
| UBCMA coverage, selection+quality bias      |     0.9033 |     0.903 |
| DerSimonian-Laird coverage, sel+quality bias|     0.3133 |     0.313 |

**Verdict: the published headline numbers reproduce. The paper stands.**
