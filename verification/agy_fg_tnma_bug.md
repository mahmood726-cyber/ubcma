# Independent Third-Vendor Correctness Bug-Review: Transport-NMA Engine & Simulation Harness
This document records findings from the independent verification of the Transport-NMA engine (`tnma.py`), simulation harness (`h2h_bench.py`), and pooled kappa estimator (`fix3_pooled_kappa.py`).

## Summary Verdict
The core transport-NMA engine, simulation sweeps, bias-injection mechanisms, and MCIW0 metrics are mathematically correct and behave as described. No defects were found that change the shipped h2h conclusion (that `ext0.158` beats `PET/TF/HC` at $B \ge 0.15$). The codebase is highly robust, and all key claims are supported by first-principles verification and automated regression tests.

---

## Findings

### Finding 1: Disconnected Network Variance Handling (P2 - Internal/Edge-Case)
* **File & Line**: [nma/nma_core.py](file:///F:/ubcma/nma/nma_core.py#L188-L199) (in `_league`) and [nma/nma_core.py](file:///F:/ubcma/nma/nma_core.py#L270-L274) (in `fit_nma`).
* **Concrete Failure**: The frequentist NMA solver computes treatment contrast potentials $\theta_a - \theta_b$ and standard errors `seTE` using `np.linalg.pinv` on the weighted Laplacian matrix $L$. When the network is disconnected (composed of multiple disjoint subgraphs), the Laplacian is singular with a null-space dimension greater than 1. The pseudoinverse still computes a finite variance for contrasts between disconnected treatments: $\operatorname{Var}(\theta_a - \theta_b) = L^+_{aa} + L^+_{bb} - 2 L^+_{ab} = L^+_{aa} + L^+_{bb}$, yielding a finite standard error (`seTE`) instead of infinity or NaN. This means the engine reports valid-looking point estimates and standard errors for treatment pairs with no direct or indirect connection in the network.
* **Change Shipped h2h Conclusion**: **No**. The simulation sweeps use the network geometry of `dat.senn2013`, which is fully connected, meaning no disconnected components ever occur in the benchmark.

### Finding 2: Comparison Orientation Vulnerability in Pooled Kappa Regression (P2 - Internal/Robustness)
* **File & Line**: [transport_nma/fix3_pooled_kappa.py](file:///F:/ubcma/transport_nma/fix3_pooled_kappa.py#L39-L45).
* **Concrete Failure**: In the network-pooled small-study regression, direct placebo-relative studies are stacked by directly appending `c.te` to `rows_y` without checking whether `c.t2 == "placebo"` or `c.t1 == "placebo"`. If a comparison in the input list had placebo as `t1` instead of `t2`, the sign of `c.te` would be flipped, violating the assumed regression orientation and corrupting the estimated bias $\gamma$. Unlike `aact_kappa_truthgate.py`, which robustly handles both orientations via `(sim[i].te if sim[i].t2=="placebo" else -sim[i].te)`, `fix3_pooled_kappa.py` is vulnerable to the sorting of comparison treatments.
* **Change Shipped h2h Conclusion**: **No**. In the current senn2013 network and the benchmark setup, `senn_contrasts()` always outputs comparisons with placebo in `t2`. Therefore, the signs are correct in practice.

### Finding 3: Stale `h2h_result.txt` Log on Disk (P2 - Cosmetic/Stale File)
* **File & Line**: [transport_nma/h2h_result.txt](file:///F:/ubcma/transport_nma/h2h_result.txt).
* **Concrete Failure**: The committed simulation run log `h2h_result.txt` was generated from an older version of `h2h_bench.py` and is stale; it does not list `registry_ext0.158` in the printed results table, even though `registry_ext0.158` is correctly computed and logged to `h2h_result.json` in the codebase. When the benchmark is re-run with the current code, the output table displays `registry_ext0.158` correctly.
* **Change Shipped h2h Conclusion**: **No**. The actual code and JSON results contain the correct values, and the current code prints the results correctly.
