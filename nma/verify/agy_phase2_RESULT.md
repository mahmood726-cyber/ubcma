# Antigravity Independent NMA Verification (Phase 2)

Command run from repo root:

```powershell
python nma/verify/agy_phase2_nma.py
```

The verifier is standalone, does not read `smallstudy_nma.py` or `inconsistency_nma.py`, and layers the math on `nma/nma_core.py`. It uses the netmeta DL `tau2` values from `*_scalars.csv` for the random-effects weight matrix.

## Part B: Small-Study Meta-Regression (PET / PEESE)

### 1. No-Covariate League Parity
Reconstructing the basic-parameter league table under WLS with no covariate matches the netmeta random-effects league table to machine precision (well below the `1e-8` target):
- **Smoking**: max absolute TE difference = `4.9992e-11` (PASS)
- **Senn2013**: max absolute TE difference = `4.7858e-11` (PASS)

### 2. Egger Asymmetry Test (PET)
- **Smoking**:
  - Slope $\beta$ = `-1.369126590263818`
  - $z$-score = `-1.929634523371233`
  - $p$-value = `0.05365213805455138` (not statistically significant at $\alpha = 0.05$)
- **Senn2013**:
  - Slope $\beta$ = `0.574880310668497`
  - $z$-score = `0.792604466376300`
  - $p$-value = `0.4280083056997266` (not statistically significant)

### 3. PEESE-Adjusted League Entries (vs reference treatment)
PEESE basic parameters (reconstructed at $se_i^2 \to 0$):

- **Smoking** (ref = `A`):
  - `A`: `0.0`
  - `B`: `0.250423836974764`
  - `C`: `0.460417525693230`
  - `D`: `0.310724585314433`

- **Senn2013** (ref = `acar`):
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

## Part C: Cochran Q Decomposition

The Q-decomposition results (at $\tau^2 = 0$) match the reference values in `decomp_reference.csv` exactly:

| network | Q_total (df) | Q_het (df) | Q_inc (df) | Target Tolerance | Status |
|---|---|---|---|---|---|
| **smoking** | `202.618871212977` (23) | `187.398534192084` (16) | `15.220337020893` (7) | `< 1e-6` | **PASS** |
| **senn2013** | `96.985553005261` (18) | `74.455281735513` (11) | `22.530271269748` (7) | `< 1e-6` | **PASS** |

The inconsistent degrees of freedom (`df_inc = 7` for both networks) match the number of independent loops.

---

### Verdict
**PASS** (B1 < 1e-8 and C_Qinc matches reference to 1e-6)
