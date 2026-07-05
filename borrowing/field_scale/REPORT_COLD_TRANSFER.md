# Cold out-of-corpus transfer of the learned-kernel borrowing field (honest boundary)

**Branch** `methods-borrowing` · **Date** 2026-07-05 · truth-first. Runs the open probe
designed in `AACT_SLICE_NEXTSTEP.md`, which had been designed + data-sourced but never
executed. Every number below is reproduced by `cold_transfer.py`
(`cold_transfer_results.json`) and cross-checked by two independent engines.

## 1. The question (and why it was genuinely open)

The committed headline (`benchmark_learned.py`) shows the learned-kernel GP beats within-MA
borrowing **inside** the 28-MA / 1177-node corpus (−0.0230 [−0.0340, −0.0117]). The
corpus-**expansion** test (`aact_run_ext.py`) shows it survives when real AACT MAs are
**added** to the corpus — but that test scores AACT trials by **random k-fold**, so an AACT
trial's own same-MA siblings sit in the training folds and the GP's `ma`-match kernel term
still fires. That is **not** a cold test. The genuinely cold external-validity question —
*does the advantage transfer to a fresh registry `ma` the kernel has NEVER trained on, where
it must generalise via specialty + log-precision + year alone?* — was still open. An honest
null/negative was pre-declared an acceptable outcome (it would bound the headline to
in-corpus reconstruction).

## 2. Data (truth-first extraction, `aact_coldslice.py`)

A cold AACT LOR slice from the 2026-04-12 snapshot: **144 nodes / 13 MAs** across four
specialties **present in the corpus LOR family** (so a same-specialty relevance signal
exists to transfer) — clinical_medicine (6 MAs: diabetes ×5 + spondylarthropathies),
oncology (5: bronchogenic-carcinoma / neoplasms — the corpus has a matching lung-cancer
donor `hackshaw1998`), infectious_disease (hepatitis-C), psychiatry (depressive). Effects
are sponsors' **own** reported Odds-Ratios + their 2-sided 95% CIs (`logOR=log(OR)`,
`se=(log(ci_hi)−log(ci_lo))/(2·1.96)`); every row is self-verifying (CI round-trip ≤5%, 10
failures dropped); one **median-logOR** node per trial controls multiplicity; a MA = one
(MeSH condition × first-MeSH intervention class) group with k≥8. Matches the note's ~18k
all-OR recipe (16,798 analyses kept).

## 3. Result — the cold transfer is an HONEST NEGATIVE, cleanly bounded

**Leave-one-MA-out (each target AACT `ma` fully held out, `ma`-term cannot fire):**

| stratum | n | learned MAE | within MAE | Δ (learned−within) | verdict |
|---|---|---|---|---|---|
| **all AACT (headline)** | 144 | 0.778 | 0.627 | **+0.152 [+0.050, +0.263]** | **within-MA better** |
| clinical_medicine | 77 | 0.976 | 0.709 | +0.267 [+0.086, +0.465] | within better |
| oncology | 49 | 0.524 | 0.543 | −0.019 [−0.056, +0.020] | **tie** |
| infectious_disease | 10 | 0.713 | 0.505 | +0.208 [−0.020, +0.400] | tie (wide) |
| psychiatry | 8 | 0.514 | 0.500 | +0.014 [−0.166, +0.194] | tie (wide) |

On a genuinely cold registry MA the learned field **does not beat within-MA pooling**;
overall it loses (Δ=+0.152, CI excludes 0). This bounds the committed headline to in-corpus
reconstruction — as the design note anticipated.

**But the negative is nuanced and the field still carries real signal:**
- **Negative control passes:** the real cold kernel significantly **beats** its
  scrambled-(ma,specialty)-label version (Δ_real−scr = **−0.109 [−0.187, −0.030]**). The cold
  field is not noise — it extracts genuine cross-MA relevance; it simply cannot recover
  MA-specific effect *levels* well enough to beat local pooling.
- **The loss is concentrated, not uniform:** **7 of 13 MAs individually favour the cold
  kernel** (point). The pooled negative is dominated by one extreme-level MA —
  `aact_diabetesme_glucagon-l` (GLP1, mean logOR +3.18, Δ=+1.62): cross-MA borrowing cannot
  recentre so extreme a level. Oncology, which has a real same-specialty corpus donor, is a
  **clean tie**.
- **Warm-vs-cold decomposition isolates the `ma`-term:** with the `ma`-term firing (random
  k-fold, WARM) the kernel **ties** within-MA (Δ=−0.049 [−0.100, +0.003], reproducing the
  `aact_run_ext` LOR result); removing it (COLD) costs ≈+0.20. **The in-corpus/expansion
  advantage was carried by the same-MA kernel term**, not by transferable specialty/precision/
  year structure.
- **Corpus-only-trained** (no AACT in training at all) is worse still (Δ=+0.664), as expected
  — the hardest regime.
- **Conformal coverage holds cold:** raw 0.833 → split-conformal **0.896** at nominal 0.90.
  The distribution-free calibration layer transfers even when the point predictor does not.

## 4. Verification (consensus-or-flag)

- **Engine 1 (primary, `field_learned` — L-BFGS marginal-likelihood grouped-ARD GP):**
  Δ = **+0.1515 [+0.0501, +0.2634]**.
- **Engine 2 (independent, `cold_transfer_witness.py` — from-scratch GP, grid-search NLML,
  own feature build + own within-MA; shares NO method code, only reads the same data):**
  Δ = **+0.2361 [+0.1224, +0.3616]**.
- **Method 3 (GP-free, `field_learned`-independent):** a simple **cold specialty-pool**
  predictor — precision-weighted mean of same-specialty, different-`ma` donors — also loses to
  within-MA: Δ = **+0.2811 [+0.1712, +0.4026]** (`within_mae`=0.6259). A different method family
  reaching the same sign rules out a GP-specific artefact.
- **Engine 4 (third vendor, `agy` / Gemini, fully independent re-implementation):** reproduced
  the cold specialty-pool metric **to 4 dp** — `AGY2 delta=0.2811 within_mae=0.6259 n=144
  verdict=within_better`.

All four agree in **sign** (within-MA beats cold cross-MA borrowing) with CIs excluding 0; the
two GP engines verify the exact learned-kernel claim, the specialty-pool + agy verify the
general phenomenon. Codex was unavailable this session (workspace out of credits) — recorded
honestly; agy served as the external vendor.

## 5. Verdict

**Honest negative, cross-engine confirmed.** The learned-kernel borrowing-field advantage is
a property of **in-corpus** reconstruction (where the same-MA term contributes) and **does
not transfer** to a cold, out-of-corpus registry MA, where it ties at best (oncology) and
loses overall (driven by extreme-level MAs it cannot recentre). The field nonetheless beats
its scrambled control (real structure) and its conformal layer stays calibrated cold. This
**bounds** the capstone item-4 headline; it does not overturn the in-corpus win.

Files: `aact_coldslice.py`, `aact_coldslice_nodes.csv`, `cold_transfer.py`,
`cold_transfer_witness.py`, `cold_transfer_results.json`, `cold_transfer_witness.json`.
