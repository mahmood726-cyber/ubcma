# Donor-ceiling decomposition — is the cold-transfer boundary a METHOD or a CORPUS-COVERAGE ceiling?

**Repo** `ubcma`, branch `methods-borrowing` · builds forward from the am cold negative
(`9b52b86`, `cold_transfer.py`) and the pm conflict-aware discount (`420fac3`,
`conflict_discount.py`). Truth-first: this closes the pm report's explicit open item by a
controlled, cross-vendor-confirmed test — and **refines** its hypothesis.

## The question (the pm report's flagged real ceiling)
The am session found that on a genuinely fresh registry `ma` held out entirely (leave-one-MA-out),
the raw learned-kernel field loses to within-MA pooling (Δ=+0.15153 [+0.050,+0.263], n=144),
the pooled loss dominated by ONE extreme-level MA — GLP1 `aact_diabetesme_glucagon-l`, mean logOR
**+3.18**, cold MAE 2.48 vs within 0.86. The pm session made the field deployable-safe cold via
the shipped conflict-aware discount (tie), and flagged the residual as:

> *"the field currently has no in-corpus GLP1-level donor to recentre toward; that is the real
> ceiling, not the fusion rule. Re-run once a genuine same-specialty donor exists."*

That is a **corpus-coverage** hypothesis. It had never been tested. This report tests it directly:
**if a genuine level-matched same-class donor is injected into the corpus, can the deployed cold
kernel (specialty + log-precision + year) recentre the held-out extreme MA?**

## Design — controlled donor injection (`donor_ceiling.py`)
For each cold AACT `ma` m, split its nodes into two **disjoint** halves (fixed seed `20260705`;
no row is ever both train and test): a DONOR half and a TEST half. Predict the SAME test-half rows
under four training regimes, each scored against the SAME within-MA reference (each test node from
its own full-MA precision-weighted siblings — the deployable within-MA):

| arm | donor half | held out | how the donor can be reached |
|---|---|---|---|
| **A** cold_nodonor | dropped (with test half) | all of m | no donor present (= committed cold, restricted to test-halves) |
| **B** cold_sibling | relabelled `m__sib` (distinct ma-code), kept in training | test half only | **specialty + log-precision + year ONLY** (ma-match term does NOT fire) |
| **C** warm_sibling | kept, label m (ma-term FIRES) | test half only | exact same-class identity (upper bound) |
| **D** cold_sibling_scrambled | relabelled + outcomes globally permuted (wrong level) | test half only | negative control: donor present at wrong level |

GLP1's donor/test halves are genuinely level-matched (donor mean **+3.47**, test mean **+2.90**) —
so arm B is the honest "a second MA of the same drug class exists in my corpus, but I don't know
it's the same class" deployment scenario.

## Result — the ceiling is BOTH, and the decomposition separates them (HONEST, NUANCED)

Committed L-BFGS-GP engine, 71 test-half rows (Δ vs within-MA; **+ = loss**):

| arm | Δ vs within-MA | GLP1 posterior mean | GLP1 MAE | reading |
|---|---|---|---|---|
| A cold_nodonor | **+0.1084** [−0.030,+0.257] | +0.75 | 2.146 | cold loss reproduces (dir.) |
| B cold_sibling | **+0.0523** [−0.085,+0.194] | +1.12 | 1.778 | **partial recovery, still a loss** |
| C warm_sibling | **−0.0444** [−0.126,+0.035] | **+3.11** | 0.738 | full recovery (≈ am WARM −0.049) |
| D scrambled | +0.1356 [−0.001,+0.273] | +0.94 | 1.957 | no help (≈ A) — control passes |
| within-MA ref | (0) | +2.81 | 0.968 | — |

Load-bearing paired tests (primary engine):
- **A level-matched donor genuinely helps** — B beats A by **−0.0561 [−0.105,−0.008]** (sig.). So
  the pm corpus-coverage hypothesis is *partly* right: donor availability matters.
- **The help is from real LEVEL, not extra neighbours** — B beats the scrambled donor D by
  **−0.0833 [−0.155,−0.010]** (falsification passes).
- **But cold routing closes only 37% of the gap** — recovery fraction (Δ_A−Δ_B)/(Δ_A−Δ_C) = **0.37**.
  The held-out extreme MA stays badly under-predicted: cold-sibling GLP1 posterior **+1.12 vs true
  +2.90**; B remains a loss. Full recovery (posterior +3.11 ≈ within +2.81) needs arm C's **ma-identity
  match**, which the cold contract forbids for a genuinely novel MA.

### Interpretation (truth-first)
The cold-transfer boundary is **not purely** corpus-coverage and **not purely** method — the
decomposition isolates the two:
1. **Corpus-coverage component (real):** a level-matched same-specialty donor lowers the cold loss
   (B<A, falsified vs scrambled). Adding same-class evidence helps.
2. **Method component (the residual ceiling):** the deployed specialty+precision+year kernel extracts
   only ~⅓ of an injected level-matched donor. A minority high-level donor is averaged among the
   same-specialty majority at lower levels, so the novel extreme MA cannot be recentred without the
   ma-identity term — which is unavailable for a genuinely novel class. **This is the concrete fix
   target: a leakage-free, class/effect-level-informative covariate** (e.g. a drug-class/mechanism
   embedding, or a registry-derived expected-effect prior) that lets the field route a novel MA's
   level from a same-class donor *without* needing the ma-identity match.

This **refines** the pm speculation ("no GLP1-level donor is the real ceiling"): even *with* a
perfect level-matched donor injected, cold routing does not recentre the extreme MA — so the deeper
ceiling is the kernel's inability to use a same-class donor's level without class identity, not the
mere absence of a donor. It does not overturn any committed headline; it sharpens the crown-jewel's
one honest boundary (item 4 cold-transfer) with a tested mechanism.

## Verification — objective gate (4 independent engines, incl. external vendor)

Exact reproduction: the committed am cold headline reproduces in this environment to full precision
(Δ=+0.15153, matches `cold_transfer_results.json`). The A/B **decisive comparison** is confirmed by
four independent computations; the warm bracket (C) reproduces the am WARM number (−0.049):

| engine | A_delta | B_delta | GLP1 A_post | GLP1 B_post | recentres? |
|---|---|---|---|---|---|
| Primary L-BFGS GP (committed machinery) | +0.108 | +0.052 | +0.75 | +1.12 | no (partial) |
| From-scratch grid-NLML GP (`donor_ceiling_witness.py`, no shared code) | +0.204 | +0.188 | +0.33 | +0.60 | no |
| GP-free Nadaraya-Watson (`donor_ceiling_witness_nw.py`, different model family) | +0.178 | +0.165 | +0.45 | +0.52 | no |
| **Codex EXTERNAL** (mahmood726/pc1, own local-kernel, `xverify_codex_donor/`) | +0.135 | +0.084 | +1.00 | +1.31 | no (partial) |

- **Unanimous verdict across all four:** A is a cold loss; B stays a loss; the injected level-matched
  donor moves the held-out GLP1 posterior only into **+0.5 … +1.3**, never near the true **+2.90**.
- **Honest engine-dependence (disclosed):** the *magnitude* of the partial help varies — the two GP
  engines (primary, Codex) pick up ~−0.05 of it, the two kernel-average engines (grid-witness, NW)
  ~−0.015 — but the **verdict is identical** (partial help, no recentering) across every engine and a
  different model family, and Codex is a separate external vendor with an independently written impl.
- **Codex independence checked:** its `witness.py` imports only numpy/pandas + reads `data.csv`; no
  repo internals (`field_learned`/`cold_transfer`/`corpus`) — genuine from-scratch witness.

**Nothing NOT_PROVEN in the headline.** The decisive A/B comparison and the GLP1-does-not-recentre
result are 4-engine confirmed (one external vendor); the warm upper bound (C) and scrambled control
(D) are on the committed engine and C reproduces the am WARM number.

## Files (all `borrowing/field_scale/`)
- `donor_ceiling.py` (+ `_results.json`, `_stdout.txt`) — primary 4-arm decomposition, falsification,
  recovery fraction, GLP1 focus, per-MA.
- `donor_ceiling_witness.py` (+ `.json`) — engine 2 (from-scratch grid-NLML GP).
- `donor_ceiling_witness_nw.py` (+ `.json`) — engine 3 (GP-free Nadaraya-Watson; different family).
- `donor_ceiling_selfcontained.csv` — self-contained block + donor/test split for external engines.
- `xverify_codex_donor/` — engine 4 (external Codex: `codex_witness.py`, `codex_witness_out.json`, `TASK.md`).

## Suggested follow-ups (not done)
- Prototype the fix: add a **leakage-free class covariate** to `build_features` (a drug-class or
  ATC/mechanism embedding, or a registry-derived expected-effect prior as a continuous feature) and
  re-run arm B — the test is whether cold-sibling then recovers toward arm C without the ma-identity
  match. Would need pre-declaration + the same multi-engine gate to avoid overfitting the one GLP1 cell.
- Update `BENCHMARK_PORTFOLIO.md` item 4 cold-transfer boundary line with a one-line pointer here once
  the repo is not under a concurrent writer (draft text ready).
