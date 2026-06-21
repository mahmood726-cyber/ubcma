# Independent verification task: multi-arm graph-theoretic NMA

You are independently re-deriving and re-implementing frequentist network
meta-analysis to cross-check another implementation. **Do not read
`nma/nma_core.py`** — implement from the math yourself, then compare to the R
`netmeta` reference outputs already committed.

## Inputs (committed CSVs, relative to repo root F:\ubcma)
- `nma/reference/smoking_input.csv` — columns studlab,treat1,treat2,TE,seTE.
  This is the Hasselblad smoking-cessation network (4 treatments A,B,C,D; 24
  studies incl. MULTI-ARM 3-arm trials), as logOR contrasts. TE = effect(treat1)
  − effect(treat2).
- `nma/reference/senn2013_input.csv` — same schema, diabetes MD network (10
  treatments, multi-arm).
- Reference truth from R netmeta 3.6-1:
  - `nma/reference/smoking_TE_random.csv`, `_seTE_random.csv` — full league
    table (rows/cols = treatments) of random-effects pooled contrasts + SEs.
  - `nma/reference/smoking_scalars.csv` — has tau2 (DL), Q, df.Q.
  - same for `senn2013_*`.

## What to implement (Rücker graph-theoretic / GLS NMA)
1. Build incidence B (m comparisons × n treatments): +1 at treat1, −1 at treat2.
2. Weight matrix W, block-diagonal by study. For a 2-arm study: 1/seTE².
   For a MULTI-ARM study with p arms and c=p(p−1)/2 contrasts: reconstruct
   per-arm variances σ²_t from the pairwise variances (v_e = σ²_{t1}+σ²_{t2},
   solve the linear system), form the contrast covariance
   V = A diag(σ²) Aᵀ (A = signed within-study incidence), and use
   W_block = Moore–Penrose pinv(V).
3. Random effects: add tau² with the multi-arm structure — diagonal tau²,
   tau²/2 for contrasts sharing an arm. Equivalently per-arm variance
   σ²_t + tau²/2 before forming V.
4. Pooled potentials θ = pinv(BᵀWB) Bᵀ W y; league TE[t,u]=θ_t−θ_u;
   seTE[t,u]=sqrt(Lⁿ[t,t]+Lⁿ[u,u]−2Lⁿ[t,u]) with Lⁿ=pinv(BᵀWB).
5. DL tau²: feed the value from the scalars CSV (you do NOT need to re-derive
   the heterogeneity estimator — just use netmeta's tau2 to check the GLS engine).

## Deliverable
Write a standalone script `nma/verify/<yourname>_nma.py` and a short
`nma/verify/<yourname>_RESULT.md` reporting, for BOTH networks, the max absolute
difference between your random-effects league TE and seTE vs the netmeta
reference CSVs. Target: < 1e-6. If you cannot reach 1e-6, report the largest
discrepancies and your best diagnosis. Do not fabricate numbers — every value
must come from running your own code.
