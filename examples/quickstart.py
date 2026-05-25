# %% [markdown]
# # UBCMA Quick Start
#
# This notebook demonstrates the core UBCMA workflow using the Verde 2021
# aspirin dataset (6 studies examining aspirin for secondary prevention).

# %%
from ubcma import (
    MetaAnalysisDataset,
    UBCMAFit,
    dersimonian_laird,
    information_criteria,
    reml_estimator,
    standardized_residuals,
)

# %% [markdown]
# ## 1. Load Data

# %%
data = MetaAnalysisDataset.from_csv(
    "verde_2021_aspirin.csv",
    quality_cols="rob_selection,rob_measurement,rob_reporting",
    study_id_col="study_id",
)
print(f"Loaded {data.n_studies} studies")
print(f"Effect sizes: {data.y}")

# %% [markdown]
# ## 2. Fit UBCMA

# %%
fitter = UBCMAFit(n_restarts=10, maxiter=60)
result = fitter.fit(data, allow_failed=True)
print(f"UBCMA mu = {result.mu:.4f}")
print(f"tau (main) = {result.tau1:.4f}")
print(f"tau (tail) = {result.tau2:.4f}")
print(f"mix weight = {result.mix_weight:.4f}")

# %% [markdown]
# ## 3. Compare to Standard Estimators

# %%
dl = dersimonian_laird(data.y, data.se)
reml = reml_estimator(data.y, data.se)
print(f"DerSimonian-Laird: mu = {dl['mu']:.4f}, CI = [{dl['ci_low']:.4f}, {dl['ci_high']:.4f}]")
print(f"REML:              mu = {reml['mu']:.4f}, CI = [{reml['ci_low']:.4f}, {reml['ci_high']:.4f}]")
print(f"UBCMA:             mu = {result.mu:.4f}")

# %% [markdown]
# ## 4. Diagnostics

# %%
ic = information_criteria(result, data, fitter)
for model_name, vals in ic.items():
    print(f"  {model_name}: AIC={vals['aic']:.1f}  BIC={vals['bic']:.1f}")

resid = standardized_residuals(result)
print(f"\nResidual mean = {resid.mean():.3f}, SD = {resid.std():.3f}")

# %% [markdown]
# ## 5. Study-Level Results

# %%
table = result.study_table()
print(table.to_string(index=False, float_format="%.3f"))

# %% [markdown]
# ## 6. Interpretation
#
# - **mu** is the bias-calibrated pooled effect, adjusted for publication selection
#   and study quality. It may differ from the naive DL/REML estimate.
# - **selection_probability** near 1.0 means the study was likely published regardless
#   of results; values near 0 suggest it may have been selected for significance.
# - **estimated_quality_shift** shows how much each study's quality indicators
#   shift the estimated effect away from the reference (high-quality) estimate.
