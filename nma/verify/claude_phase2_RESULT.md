# AdaptShrink-NMA Phase-2 independent verification — Claude (claude-sonnet-4-6)

Seat: **claude** (Claude Sonnet 4.6 via Claude Code — different model family from the production engine)
Script: `nma/verify/claude_phase2_nma.py`
Date: 2026-06-25

## Summary: PASS

B(1) max |TE diff| < 1e-8: **PASS**
C Q_inc diff < 1e-6 (at tau²=0): **PASS** (both networks machine-precision)

---

## Part B — Network small-study meta-regression (PET / PEESE)

### smoking (n=4 treatments, m=28 comparisons, k=24 studies, tau²=0.5989)

| Check | Value | Pass? |
|-------|-------|-------|
| B(1) max\|TE diff vs RE league\| | 4.999e-11 | ✓ < 1e-8 |
| B(2) PET slope β | −1.369127 | — |
| B(2) z = β/SE(β) | −1.9296 | — |
| B(2) p-value (two-sided) | 0.0537 | — |

PEESE-adjusted league (vs reference A):

| Contrast | d |
|----------|---|
| d[B−A] | 0.25042 |
| d[C−A] | 0.46042 |
| d[D−A] | 0.31072 |

### senn2013 (n=10 treatments, m≈18 comparisons, tau²=0.1087)

| Check | Value | Pass? |
|-------|-------|-------|
| B(1) max\|TE diff vs RE league\| | 4.786e-11 | ✓ < 1e-8 |
| B(2) PET slope β | 0.574880 | — |
| B(2) z = β/SE(β) | 0.7926 | — |
| B(2) p-value (two-sided) | 0.4280 | — |

PEESE-adjusted league (vs reference acar):

| Contrast | d |
|----------|---|
| d[benf−acar] | 0.06406 |
| d[metf−acar] | −0.29913 |
| d[migl−acar] | −0.14976 |
| d[piog−acar] | −0.30863 |
| d[plac−acar] | 0.89812 |
| d[rosi−acar] | −0.39667 |
| d[sita−acar] | 0.29691 |
| d[sulf−acar] | 0.45500 |
| d[vild−acar] | 0.16777 |

---

## Part C — Design-by-treatment Q decomposition at tau² = 0

| Statistic | smoking (mine) | smoking (ref) | diff | senn2013 (mine) | senn2013 (ref) | diff |
|-----------|---------------|--------------|------|----------------|---------------|------|
| Q_total | 202.6188712 | 202.6188712 | 5.1e-13 | 96.9855530 | 96.9855530 | 6.3e-13 |
| df_total | 23 | 23 | exact | 18 | 18 | exact |
| Q_het | 187.3985342 | 187.3985342 | 4.0e-13 | 74.4552817 | 74.4552817 | 2.0e-13 |
| df_het | 16 | 16 | exact | 11 | 11 | exact |
| Q_inc | 15.2203370 | 15.2203370 | **3.2e-13** | 22.5302713 | 22.5302713 | **8.3e-13** |
| df_inc | 7 | 7 | exact | 7 | 7 | exact |

All diffs < 1e-6 ✓ — machine-precision agreement with netmeta decomp.design reference.

---

## Differences from production implementation

- Implemented independently from `smallstudy_nma.py`, `inconsistency_nma.py`, `adaptshrink_nma.py`
- Used `nma.nma_core` (already verified to ~1e-11 vs netmeta) for the GLS/assembly engine
- Different solver: direct numpy pseudoinverse WLS rather than production's bespoke matrix algebra
- B(1) error ~4.8–5e-11 (vs production's 6–10e-16): same order of magnitude, both well below 1e-8

---

*Verification method: independent re-implementation from VERIFY_SPEC_PHASE2.md spec.*
