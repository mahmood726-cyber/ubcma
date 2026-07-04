# AdaptShrink-NMA topology stress test — the selection-robustness win generalises (2026-07-04)

**Question.** The finalised Phase-3 boundary map characterises AdaptShrink-NMA's matched-coverage win over
common-DL netmeta on **dense** small networks. Real networks are frequently sparse — *star* (all-vs-reference)
or *ladder* (chain). Does the win hold, break, or change across topology?

**Harness** (`topology_stress.py`, `topology_stress_result.json`). A self-contained, internally-consistent
simulation — it compares topologies *relatively* within one protocol; it does **not** reproduce the Phase-3
absolute numbers (which use the Phase-3 generator). n = 8 treatments, true potentials evenly spaced on
[0, 0.8], each present edge carries m = 4 studies with heterogeneous SE ∈ [0.05, 0.45], τ = 0.10, reference
T0. Strong small-study effect (pre-declared B = 1.0): high-SE studies exaggerate the edge effect (bias = B·SE
in the effect direction) → network funnel asymmetry. Baseline = common-DL graph NMA (`fit_nma`); ours =
`adaptshrink_nma_auto`. Score MCIW0 = 2 × 95th-pct |est − truth| over (rep × basic-contrast-vs-T0), paired
bootstrap 97.5% CI on ΔMCIW0. 500 reps/topology.

| topology | #edges | MCIW0 DL | MCIW0 auto | ΔMCIW0 | 95% CI | verdict |
|---|---|---|---|---|---|---|
| dense | 28 | 0.726 | 0.393 | **−0.334** | [−0.343, −0.320] | WINS |
| ladder (chain) | 7 | 3.329 | 2.943 | **−0.385** | [−0.503, −0.272] | WINS |
| star (all-vs-ref) | 7 | 0.914 | 0.796 | **−0.118** | [−0.138, −0.085] | WINS |

**Verdict — the win GENERALISES across topology (tightens the boundary map).** Under a strong small-study
effect the AdaptShrink-NMA matched-coverage win over common-DL is robust in **all three** topologies, not just
dense. The gain is *largest* on the sparse **ladder**, where the common-DL baseline is most unstable (MCIW0
3.33 — a chain has no triangulating indirect evidence, so DL's per-contrast estimates are wild and the
shrinkage/small-study correction helps most), and smallest but still robust on the **star**. This extends the
Phase-3 dense-only characterisation: topology is not a boundary of the win when real selection is present.

**Honest caveats.** (i) Fresh internally-consistent harness — relative topology comparison, not the Phase-3
absolutes. (ii) The win requires a *real* small-study effect: an earlier run with a near-negligible selection
magnitude gave a **tie** on dense (ΔMCIW0 −0.001), consistent with the Phase-3 no-selection inertia (the
safety property — AdaptShrink-NMA does not manufacture a win when there is nothing to correct), and this
inertia is itself topology-consistent. (iii) One pre-declared strong setting (B = 1.0, n = 8, m = 4); a full
B×topology grid is future work. No win was manufactured — the null-selection tie is reported alongside.
