# Consensus Engine Independent Third-Vendor Correctness Review Report

This report documents real correctness defects verified from first principles in the consensus and borrowing/field_scale engines of `F:\ubcma` (branch `methods-borrowing`).

## Methodology
- Evaluation of the consensus-or-flag verifier run logic, paired-bootstrap catch-rate, and false-flag-rate computation.
- Verification of matched-false-flag-rate comparison logic (HETERO vs HOMO vs SINGLE comparison at the same false-flag budget).
- Check of any off-by-one or asymmetric threshold, and isolation-test ($f_{sys}=0$ tie) claims.
- Inspection of seeded RNG for determinism.
- Analysis of Fisher-z corpus builder: $v_z = 1/(n-3)$ handling for $n \le 3$, partial correlation $df = n - preds - 3$, and effect family (COR/LOR/SMD) harmonization onto a common scale.

---

## Findings

### Finding 1: Independent RNG streams break paired-bootstrap assumptions and generate false statistical significance at $f_{\text{sys}} = 0$ (Isolation Test)
- **File:Line**: [consensus/consensus_or_flag.py:175-176](file:///F:/ubcma/consensus/consensus_or_flag.py#L175-L176) and [consensus/consensus_or_flag.py:271-283](file:///F:/ubcma/consensus/consensus_or_flag.py#L271-L283)
- **Severity**: P1
- **Concrete Failure**: The simulation initializes separate, independent random number generators (`rng_t` and `rng_f`) with different seeds for each bank (`single`, `homo`, `hetero`). As a result, the simulated true and false claims (difficulty $G$ and noise $E$) are completely independent realizations across the banks. A paired bootstrap assumes that the claims are paired (i.e. evaluated on the same claim realizations). Under the isolation test null hypothesis where the banks are mathematically identical ($f_{\text{sys}} = 0$ and $\rho_{\text{homo}} = \rho_{\text{hetero}} = 0.15$), the expected difference in catch rate is exactly 0. However, because they are simulated independently, the sample mean difference is affected by RNG noise (e.g. $-0.0011$). The paired bootstrap computes a CI around this non-zero difference (e.g. $[-0.0021, -0.0001]$), which incorrectly excludes 0, declaring a statistically significant "LOSS" for hetero due purely to simulation noise.
- **Affects Shipped Claim**: Yes. Directly contradicts the shipped claim that the "isolation test ties at $f_{\text{sys}}=0$."

### Finding 2: Fisher-z transformed partial correlation variance has degrees of freedom off-by-one
- **File:Line**: [borrowing/field_scale/corpus.py:153](file:///F:/ubcma/borrowing/field_scale/corpus.py#L153)
- **Severity**: P1
- **Concrete Failure**: For the partial correlation dataset `aloe2013`, the residual degrees of freedom for the t-to-r conversion is computed as `dfree = df.n - df.preds - 1`, which implies the regression has `df.preds` total predictors. The number of control variables is therefore $c = df.preds - 1$. The sampling variance of the Fisher-z transformed partial correlation should be $v_z = \frac{1}{n - c - 3} = \frac{1}{n - df.preds - 2}$. However, the code uses `vz = 1.0 / np.maximum(df.n - df.preds - 3, 1.0)`. This subtracts one too many degrees of freedom, causing an incorrect overestimation of the sampling variance and mismatching `metafor::escalc(measure="ZPCOR")` (which yields $\frac{1}{n - preds - 2}$).
- **Affects Shipped Claim**: Yes. This corpus feeds the learned-kernel MAE headline, resulting in incorrect weights for `aloe2013` studies.

### Finding 3: Silently clamping sample variance for small correlation samples ($n \le 3$)
- **File:Line**: [borrowing/field_scale/corpus.py:66](file:///F:/ubcma/borrowing/field_scale/corpus.py#L66)
- **Severity**: P2
- **Concrete Failure**: In `_z_from_r`, the variance of the Fisher-z correlation is computed as `vz = 1.0 / np.maximum(n - 3, 1.0)`. For sample sizes $n \le 3$, this clamps the denominator to 1.0 and assigns a finite variance of 1.0. Mathematically, the variance of Fisher's z is undefined or infinite for $n \le 3$ (and R's `metafor::escalc` returns `NA` with a warning). Clamping it to 1.0 silently allows small, highly unreliable studies to be included with high weight.
- **Affects Shipped Claim**: No (internal safety guard/correctness).

---

parity claims safe? no
