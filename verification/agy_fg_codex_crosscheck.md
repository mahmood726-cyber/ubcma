# Codex Cross-Check Verification Findings

## CLAIM 1 [P0] - Copas Selection Model Likelihood Selection
- **Status of Claim:** **AGREE** with Codex's claim that before the fix, the grid loop returned `valid[0]` which corresponded to the first grid point `rho=0` (the naive REML pool), and the fix correctly selects the profile maximum likelihood (minimum stored negative log-likelihood `nll`).
- **File & Line:** [comparators.py:224](file:///F:/ubcma/src/ubcma/comparators.py#L224) (post-fix).
- **Justification:** In the original implementation, the grid search appended results to `results` but then selected `best = valid[0] if valid else ...`. Since the search grid starts at `rho=0.0`, `valid[0]` was always the naive uncorrected estimator. The committed fix adds `nll_adj` to the results and selects the entry with the minimum NLL (`min(scored, key=lambda r: r["nll"])`).
- **Committed Fix Present and Sound:** **Present and Sound**. Under test, the selection shifts appropriately from `rho=0` when selection bias is present, and the comparator tests pass.
- **Correctness of Likelihood/Selection Term:** **PARTIAL**. The model uses Heckman-like conditional moments ($E[y_i \mid Z_i > 0] = \mu + \rho \sigma_i \lambda(u_i)$ and $\operatorname{Var}(y_i \mid Z_i > 0) = \sigma_i^2 (1 - \rho^2 \lambda(u_i)(u_i + \lambda(u_i)))$) to approximate the likelihood under selection. While these moments are mathematically correct conditional moments of the truncated normal, this normal approximation of the conditional likelihood weighted by $\Phi(u_i)$ is functionally distinct from the exact Copas-Shi (2000) joint log-likelihood (which uses the exact joint density of $y_i$ and $Z_i > 0$ without normal moment approximation).
- **New Related Defects:** None.

## CLAIM 2 [P0] - GP Field Scale K-fold Feature Construction
- **Status of Claim:** **AGREE** that the original `predict_kfold` code re-evaluated `build_features` separately on each fold's training and testing subsets, which caused standardisation stats (mean and std of year/log-precision) and categorical mappings (`np.unique(..., return_inverse=True)`) to diverge between the training folds and validation folds.
- **File & Line:** [field_learned.py:196](file:///F:/ubcma/borrowing/field_scale/field_learned.py#L196).
- **Justification:** Calling `build_features` on subsets caused inconsistent category mapping (e.g. Specialty A mapped to code 0 in training, but Specialty B mapped to code 0 in validation) and inconsistent standardization. Building features once on the full block and slicing rows (`X[tr]`, `X[te]`) guarantees consistency across train and validation sets, allowing correct match-kernel comparisons.
- **Committed Fix Present and Sound:** **Present and Sound**. The GP now trains on `X[tr]` and predicts on `X[te]`, resolving the category mapping and standardization shift.
- **Residual Leakage:** **Minor Covariate Leakage (Transductive)**. While target leakage is absent (as the target `yi` is not used in `build_features`), continuous features (`yr` and `lp`) are standardised using the mean and standard deviation computed over the *entire* family block (which includes the held-out validation data). In a strictly leakage-free k-fold setup, standardization statistics must be computed only on the training fold and then applied to the validation fold.

## CLAIM 3 [P2] - AACT Kappa Calculation Guards and Sample Mixing
- **Status of Claim:** **AGREE** that `transport_nma/aact_kappa.py` uses truthiness checks that drop valid `0.0` values and uses non-comparable subsets for `kappa_MD` versus `kappa_z`.
- **File & Line:** [aact_kappa.py:127](file:///F:/ubcma/transport_nma/aact_kappa.py#L127).
- **Justification:** Python's implicit truthiness test `if sp['mean_amd'] and sr['mean_amd']:` evaluates to `False` if either mean is exactly `0.0`, silently dropping a legitimate `0.0` mean absolute difference. Additionally, `kappa_MD` is computed using the entire study list (`amd`), whereas `kappa_z` is computed on a subset filtered for studies with non-None `z` values (valid standard errors), meaning they are calculated on non-comparable subsets of studies.
- **Committed Fix Present and Sound:** **NOT Present**. The bug remains unfixed in `aact_kappa.py` on the `methods-borrowing` branch.
- **New Related Defects:**
  1. The truthiness check on line 129 `if sp['mean_z'] and sr['mean_z']:` similarly drops legitimate `0.0` values for `mean_z`.
  2. Trial-level class assignment in `aact_kappa.py:106` duplicates the same trial effect across multiple drug classes when a trial lists multiple classes, potentially confounding per-class kappa values.
