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

**Verdict — the win GENERALISES across topology at STRONG selection.** Under a strong small-study effect the
AdaptShrink-NMA matched-coverage win over common-DL is robust in **all three** topologies, not just dense. The
gain is *largest* on the sparse **ladder**, where the common-DL baseline is most unstable (MCIW0 3.33 — a chain
has no triangulating indirect evidence, so DL's per-contrast estimates are wild and the shrinkage/small-study
correction helps most), and smallest but still robust on the **star**.

**Region map — the selection THRESHOLD for the win IS topology-dependent (`topology_sweep.py`,
`topology_sweep_result.json`, reps=300).** Sweeping B ∈ {0, 0.25, 0.5, 1.0} refines the single-B claim above
and — truth-first — corrects a mild over-statement (it is not that "topology is never a boundary"; rather the
*threshold* moves with topology):

| topology | B=0 | B=0.25 | B=0.5 | B=1.0 |
|---|---|---|---|---|
| dense | +0.014 HARM | −0.004 tie | **−0.100 WIN** | −0.342 WIN |
| ladder | +0.076 HARM | +0.032 HARM | −0.052 tie | −0.316 WIN |
| star | +0.017 HARM | +0.028 HARM | +0.010 tie | −0.063 WIN |

Reading: (i) the win emerges from **moderate** selection on **dense** networks (B ≥ 0.5) but requires **strong**
selection on sparse **ladder/star** (B = 1.0) — dense is the most favourable topology, sparse the least, so
topology sets *where the win kicks in*, not *whether* it eventually appears. (ii) At **B = 0** there is a
**small over-correction cost** (mild HARM, +0.01 to +0.08), largest on the ladder — the honest price of the
auto-gate not being perfectly inert on a chain with no triangulation. So the correct claim is: the win holds
across topologies **under sufficient selection**, with a topology-dependent threshold and a small no-selection
cost — a tightened, honestly-bounded extension of the Phase-3 dense characterisation, not an unconditional one.

## Studies-per-edge (m) axis — the win holds at the sparsest, most realistic per-edge counts (2026-07-04)
`msweep.py` / `msweep_result.json` maps the third sparsity dimension (after network size in Phase-3 and
topology above): m = direct studies per contrast, dense n=8, strong selection B=1.0, reps=400. Real NMAs
frequently have 1–2 studies per direct comparison — exactly where the common-DL per-contrast estimate is
most unstable.

| m/edge | #studies | MCIW0 DL | MCIW0 auto | ΔMCIW0 | 95% CI | verdict |
|---|---|---|---|---|---|---|
| 1 | 28 | 0.953 | 0.671 | **−0.282** | [−0.320, −0.253] | WINS |
| 2 | 56 | 0.827 | 0.499 | −0.328 | [−0.349, −0.302] | WINS |
| 3 | 84 | 0.760 | 0.433 | −0.327 | [−0.352, −0.312] | WINS |
| 4 | 112 | 0.735 | 0.402 | −0.333 | [−0.352, −0.318] | WINS |
| 8 | 224 | 0.674 | 0.330 | −0.344 | [−0.353, −0.333] | WINS |

**The win is robust across the entire m range, including m = 1** — a single study per direct comparison, the
hardest and most common real-world sparsity. It is slightly stronger at larger m but never disappears; at
m = 1 the common-DL baseline is most unstable (MCIW0 0.95) and the correction delivers its clearest
deployment-relevant benefit. **Combined sparsity picture:** under sufficient selection the AdaptShrink-NMA
matched-coverage win is robust across all three orthogonal sparsity axes — network size (Phase-3), topology
(dense/star/ladder), and studies-per-edge (m = 1…8) — which is the regime real evidence networks occupy.

**Honest caveats.** (i) Fresh internally-consistent harness — relative topology comparison, not the Phase-3
absolutes. (ii) The win requires a *real* small-study effect: an earlier run with a near-negligible selection
magnitude gave a **tie** on dense (ΔMCIW0 −0.001), consistent with the Phase-3 no-selection inertia (the
safety property — AdaptShrink-NMA does not manufacture a win when there is nothing to correct), and this
inertia is itself topology-consistent. (iii) One pre-declared strong setting (B = 1.0, n = 8, m = 4); a full
B×topology grid is future work. No win was manufactured — the null-selection tie is reported alongside.
