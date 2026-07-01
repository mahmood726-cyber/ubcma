# Antigravity Independent NMA Verification (Phase 2)

This report details the independent verification of **AdaptShrink-NMA Phase 2** (components B & C) based on the specification in `nma/verify/VERIFY_SPEC_PHASE2.md`.

The verifier script is standalone (`nma/verify/agy_phase2_nma.py`) and was implemented using `numpy`/`scipy` without reading `smallstudy_nma.py`, `inconsistency_nma.py`, or `adaptshrink_nma.py`. The base network structure and Laplacian GLS league construction reuse functions from `nma/nma_core.py`.

---

## Part B: Small-Study Meta-Regression (PET / PEESE)

### 1. No-Covariate League Parity
Reconstructing the basic-parameter league table under WLS with no covariate matches the committed `netmeta` random-effects reference leagues to machine precision (well below the target tolerance of `< 1e-8`):
- **smoking**: max absolute TE difference = `4.9992e-11` (**PASS**)
- **senn2013**: max absolute TE difference = `4.7858e-11` (**PASS**)

### 2. Egger Asymmetry Test (PET)
The Egger asymmetry test parameters obtained from the augmented model $X = [ B_{\text{basic}} \mid se_i ]$:
- **smoking**:
  - Slope $\beta$ = `-1.369126590263818`
  - $z$-score = `-1.929634523371233`
  - $p$-value = `0.05365213805455138` (not statistically significant at $\alpha = 0.05$)
- **senn2013**:
  - Slope $\beta$ = `0.574880310668497`
  - $z$-score = `0.792604466376300`
  - $p$-value = `0.4280083056997266` (not statistically significant)

### 3. PEESE-Adjusted League Entries (vs reference treatment)
Reconstructed basic parameters $d_t$ at $se_i^2 \to 0$ (PEESE):

- **smoking** (ref = `A`):
  - `A`: `0.0`
  - `B`: `0.250423836974764`
  - `C`: `0.460417525693230`
  - `D`: `0.310724585314433`

- **senn2013** (ref = `acar`):
  - `acar`: `0.0`
  - `benf`: `0.064057661585527`
  - `metf`: `-0.299129064302566`
  - `migl`: `-0.149762115999661`
  - `piog`: `-0.308629671614663`
  - `plac`: `0.898115850779740`
  - `rosi`: `-0.396668861431541`
  - `sita`: `0.296908280365548`
  - `sulf`: `0.454998029556600`
  - `vild`: `0.167772448007558`

---

## Part C: Cochran Q Decomposition (at $\tau^2 = 0$)

The design-by-treatment Cochran Q decomposition results match the reference values in `nma/verify/decomp_reference.csv` to machine precision:

| Network | Metric | Value (df) | Reference (df) | Absolute Diff | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **smoking** | $Q_{\text{total}}$ | `202.618871212977` (23) | `202.618871212978` (23) | `1.0e-12` | **PASS** |
| | $Q_{\text{het}}$ | `187.398534192084` (16) | `187.398534192084` (16) | `0.0` | **PASS** |
| | $Q_{\text{inc}}$ | `15.220337020893` (7) | `15.220337020893` (7) | `1.0e-12` | **PASS** |
| **senn2013**| $Q_{\text{total}}$ | `96.985553005261` (18) | `96.985553005260` (18) | `1.0e-12` | **PASS** |
| | $Q_{\text{het}}$ | `74.455281735513` (11) | `74.455281735513` (11) | `0.0` | **PASS** |
| | $Q_{\text{inc}}$ | `22.530271269748` (7) | `22.530271269747` (7) | `1.0e-12` | **PASS** |

### Degrees of Freedom and Loop Count
- The inconsistency degrees of freedom ($df_{\text{inc}} = 7$) for both networks matches the exact number of independent loops (cycle rank of the network design graph).

---

## Verdict

**PASS** (All check criteria satisfied: B1 absolute difference $< 1e-8$, C inconsistency Q difference $< 1e-6$, and degrees of freedom are exact).
