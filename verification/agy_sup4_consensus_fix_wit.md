# Independent Third-Vendor Witness Report: Consensus-or-Flag Seeding Structure Fix

**Task Identification:** Verification of Seeding Structure and Paired Bootstrap in the Consensus-or-Flag Primitive (`methods-borrowing` branch).  
**File under Review:** [consensus_or_flag.py](file:///F:/ubcma/consensus/consensus_or_flag.py) / [consensus_or_flag_result.txt](file:///F:/ubcma/consensus/consensus_or_flag_result.txt)  
**Witness Date:** 2026-07-04  
**OS Platform:** Windows  
**Verdict:** **CONFIRM** (Independent per-bank RNG seeding in [consensus_or_flag.py](file:///F:/ubcma/consensus/consensus_or_flag.py) introduces spurious noise differences under the paired bootstrap at $f_{\text{sys}}=0$. Removing the bank-specific seed offsets shares the noise realization stream, guaranteeing a mathematically perfect TIE of $+0.0000\ [+0.0000, +0.0000]$ at $f_{\text{sys}}=0$, while preserving the headline systematic-error win of $\approx +0.26$ at matched 10% false-flag rate.)

---

## 1. Confirmation of Committed Results

As part of the initial verification, we inspect the committed [consensus_or_flag_result.txt](file:///F:/ubcma/consensus/consensus_or_flag_result.txt). The isolation run at $f_{\text{sys}} = 0.00$ compares homogeneous and heterogeneous banks under identical noise correlations (`homo_rho = hetero_rho = 0.15`). Under these conditions, the two architectures are statistically identical.

However, the committed isolation row at line 75 of [consensus_or_flag_result.txt](file:///F:/ubcma/consensus/consensus_or_flag_result.txt) reads:
```
 f_sys | homo_catch | hetero_catch |        d_catch(all) 95% CI | verdict
  0.00 |     0.9737 |       0.9726 |  -0.0011 [-0.0021,-0.0001] | LOSS
```

### Analysis of the Spurious Loss
1. **Mathematical Identity:** At $f_{\text{sys}} = 0$, there are no systematic errors, and both homogeneous and heterogeneous architectures use $N=3$ verifiers with $\rho = 0.15$. Because they are mathematically identical under these parameters, the expected difference in catch rate is exactly zero (a true tie).
2. **RNG Disconnect:** In [consensus_or_flag.py](file:///F:/ubcma/consensus/consensus_or_flag.py), the function [run_cell](file:///F:/ubcma/consensus/consensus_or_flag.py#L149-L198) loops over the three bank names (`single`, `homo`, `hetero`) and instantiates independent random generators:
   - [run_cell:L175](file:///F:/ubcma/consensus/consensus_or_flag.py#L175): `rng_t = np.random.default_rng(seed + 1000 + {'single':0,'homo':1,'hetero':2}[name])`
   - [run_cell:L176](file:///F:/ubcma/consensus/consensus_or_flag.py#L176): `rng_f = np.random.default_rng(seed + 2000 + {'single':0,'homo':1,'hetero':2}[name])`
3. **Paired Bootstrap Violation:** Because the seeds differ by bank (e.g., `seed + 2001` for `homo` vs. `seed + 2002` for `hetero`), [sim_scores](file:///F:/ubcma/consensus/consensus_or_flag.py#L99-L147) generates completely independent sequences of latent difficulty $G$ and independent noise $E$. Thus, the paired bootstrap conducted in [paired_bootstrap_diff](file:///F:/ubcma/consensus/consensus_or_flag.py#L201-L220) is not evaluating the same set of claims, resulting in sample noise that produces a spurious marginal LOSS (point estimate $-0.0011$, 95% CI $[-0.0021, -0.0001]$) rather than a tie.

---

## 2. Proposed Seeding Fix & Mechanism

To perform a mathematically rigorous paired comparison, the noise realizations must be identical across the arms being compared. 

### Exact Code Fix
The proposed fix is to share a single noise stream across the banks by removing the bank-specific seed offset in [run_cell:L175-176](file:///F:/ubcma/consensus/consensus_or_flag.py#L175-L176):

```diff
-        rng_t = np.random.default_rng(seed + 1000 + {'single':0,'homo':1,'hetero':2}[name])
-        rng_f = np.random.default_rng(seed + 2000 + {'single':0,'homo':1,'hetero':2}[name])
+        rng_t = np.random.default_rng(seed + 1000)
+        rng_f = np.random.default_rng(seed + 2000)
```

### Why this yields an honest tie
1. **Identical Noise Realizations:** When `homo` and `hetero` are simulated, they both initialize `rng_t` and `rng_f` with identical seeds (`seed + 1000` and `seed + 2000`). Under both arms, $N=3$ verifiers are used. Thus, the calls in [sim_scores](file:///F:/ubcma/consensus/consensus_or_flag.py#L99-L147) draw identical arrays for the latent difficulty $G \sim N(0, I_n)$ and independent noise $E \sim N(0, I_{n \times 3})$.
2. **Identical Suspicions at $f_{\text{sys}} = 0$:** Since $f_{\text{sys}} = 0$, the systematic error subset size is 0 (`sys_idx.size = 0`), so no bank-specific blind-spot draws are made from the generators. Consequently, the suspicion scores are identical, the tuned threshold $\tau$ is identical, and the flag decisions are identical for every simulated claim.
3. **Zero-Variance Bootstrap Tie:** Since the output flag decisions are identical for every claim index $i$, the differences `flag_false_hetero[i] - flag_false_homo[i]` are exactly 0. The paired bootstrap results in a difference of exactly $+0.0000\ [+0.0000, +0.0000]$, representing a mathematically perfect, honest tie.

---

## 3. Impact on Systematic-Error Headline

We ran the modified benchmark script incorporating the proposed fix. Below is the comparative analysis of the Headline TRUTH-GATE table showing the difference on systematic-error claims only (`d_catch(SYS only)`):

| $f_{\text{sys}}$ | Original (Independent RNG) | Fixed (Shared RNG) | Impact |
| :---: | :---: | :---: | :---: |
| **0.25** | $+0.2655\ [+0.2597, +0.2715]$ | $+0.2621\ [+0.2565, +0.2681]$ | None (Statistically Indistinguishable) |
| **0.50** | $+0.2610\ [+0.2569, +0.2649]$ | $+0.2656\ [+0.2615, +0.2696]$ | None (Statistically Indistinguishable) |
| **0.75** | $+0.2627\ [+0.2594, +0.2662]$ | $+0.2607\ [+0.2576, +0.2639]$ | None (Statistically Indistinguishable) |
| **1.00** | $+0.2612\ [+0.2583, +0.2643]$ | $+0.2617\ [+0.2588, +0.2644]$ | None (Statistically Indistinguishable) |

### Why the Headline is Not Affected
- **Structural Origin:** The $+0.26$ win is a structural property of the two architectures' blind spot distributions. Homogeneous verifiers share a single blind-spot draw, yielding a $0.60$ probability of missing a systematic error. Heterogeneous verifiers draw blind spots independently, yielding a $0.60^3 = 0.216$ probability of missing a systematic error. This structural difference in detection probability ($\approx 0.384$ probability delta, scaled by the suspicion shift) is the root cause of the win.
- **RNG Role:** Sharing the noise realization stream across banks does not alter the underlying probability distributions or expected performance metrics. It merely eliminates sample noise between the comparison arms. Thus, the point estimate of the systematic win remains centered around $+0.26$ and is **NOT** affected.

---

## 4. Witness Verdict

We **CONFIRM** the seeding nit and verify the proposed fix:
- The committed results in [consensus_or_flag_result.txt](file:///F:/ubcma/consensus/consensus_or_flag_result.txt) line 75 report a spurious marginal `LOSS` of `-0.0011 [-0.0021,-0.0001]` at $f_{\text{sys}} = 0$ due to independent per-bank RNG seeding.
- Removing the bank-specific seed offset in [consensus_or_flag.py:L175-176](file:///F:/ubcma/consensus/consensus_or_flag.py#L175-L176) shares the noise realization stream, yielding a mathematically clean, zero-variance paired bootstrap TIE of `+0.0000 [+0.0000,+0.0000]` at $f_{\text{sys}} = 0$.
- The systematic-error headline of $\approx +0.26$ win is completely unaffected by the fix, remaining statistically identical (e.g., $+0.2621\ [+0.2565, +0.2681]$ at $f_{\text{sys}}=0.25$).
