# UBCMA v0.3.0 Publication-Ready Improvements — Design Spec

**Goal:** Four targeted improvements to make UBCMA submission-ready for a dual methods+software paper (e.g., *Statistics in Medicine* + *JOSS*).

**Baseline:** UBCMA v0.2.0 — 11 source modules, 75 tests, multi-start frequentist engine + PyMC Bayesian backend + 5 comparators + simulation study framework.

**Non-goals:** Sphinx docs, full API reference, paper manuscript text, CI/CD pipeline, PyPI packaging.

---

## 1. Simulation Evidence — Three-Tier Progressive Study

### Problem
The simulation framework exists (`simulation_study.py`) but no actual results have been generated. The paper's core claim — that UBCMA outperforms standard estimators under publication bias and quality-dependent bias — has no evidence yet.

### Design

Three tiers, each building on the previous via checkpointed CSVs:

#### Tier 1: Pilot (12 cells, 50 reps)
- **Factors:** selection ∈ {none, moderate, strong} × quality_bias ∈ {none, moderate} × tau ∈ {0.0, 0.1}
- **Fixed:** mu=0.2, k=30, design_mix=all_rct
- **Methods:** DL, REML, trim-and-fill, PET-PEESE, Copas, quality-effects, UBCMA (7 methods)
- **Output:** `results/pilot/simulation_study.csv`, `results/pilot/simulation_summary.csv`
- **Runtime:** ~30-60 min
- **Purpose:** Validate pipeline, catch bugs, produce draft Table 1

#### Tier 2: Focused (36 cells, 100 reps)
- **Factors:** mu ∈ {0.0, 0.2, 0.5} × tau ∈ {0.0, 0.1} × selection ∈ {none, moderate, strong} × quality_bias ∈ {none, moderate}
- **Fixed:** k=30, design_mix=all_rct (add k=10 variant = 72 cells if time allows)
- **Methods:** Same 7
- **Output:** `results/focused/`
- **Runtime:** ~2-4 hours
- **Purpose:** Main paper table + heatmap figure data

#### Tier 3: Full (324 cells, 100 reps)
- Complete factorial: 3 mus × 3 taus × 3 selections × 2 biases × 3 ks × 2 designs
- Background job with per-scenario checkpointing
- Results for supplementary materials

### New code

**`src/ubcma/simulation_study.py`** — additions:
- `run_pilot(seed, output_dir)` — hardcoded pilot tier params
- `run_focused(seed, output_dir)` — hardcoded focused tier params
- `run_full(seed, output_dir)` — full factorial
- `format_table(summary_df, format="markdown")` — produces markdown or LaTeX table from `compute_metrics()` output. Columns: Method, Bias, RMSE, Coverage, Width. Rows grouped by scenario.

**`src/ubcma/cli.py`** — update `study` command:
- `--tier pilot|focused|full` flag (default: pilot)
- Calls the appropriate `run_*` function

### Tests
- `test_format_table_markdown` — produces valid markdown with header row
- `test_format_table_latex` — produces valid LaTeX tabular
- `test_pilot_tier_has_12_scenarios` — verify the cell count
- `test_focused_tier_has_36_scenarios` — verify the cell count

---

## 2. HKSJ / Knapp-Hartung Correction

### Problem
All comparator CIs use z=1.96. For small k, this undercovers badly. Standard practice since 2014 (IntHout et al., Hartung-Knapp-Sidik-Jonkman) is to use t(k-1) with an adjusted SE. Reviewers will reject without this.

### Design

**New function in `comparators.py`:**

```python
def knapp_hartung_adjustment(
    y: np.ndarray, se: np.ndarray, mu: float, tau2: float
) -> dict[str, float]:
    """HKSJ-adjusted SE and CI using t-distribution.

    q_hksj = sum(w_i * (y_i - mu)^2) / (k - 1)
    se_hksj = se_mu * sqrt(max(q_hksj, 1.0))  # floored at 1.0 per Rover et al.
    CI: mu +/- t(k-1, alpha/2) * se_hksj
    """
```

**Modified functions:**
- `reml_estimator(y, se, hksj=True)` — when `hksj=True`, replaces z-based CI with HKSJ t-based CI. Default `True`.
- Add `dersimonian_laird_hksj(y, se)` wrapper in `model.py` — DL point estimate with HKSJ CI. This is the most common comparator in modern MA.

**Simulation study methods list update:**
- Add `"dl_hksj"` and `"reml_hksj"` as method options. These use HKSJ correction. The uncorrected `"dl"` and `"reml"` remain for comparison.

**UBCMA — no change needed:**
- Profile likelihood CIs are already exact (don't assume normality of the estimator)
- Bootstrap CIs are distribution-free
- This is a paper selling point: "Unlike DL and REML, UBCMA's profile likelihood CI does not require the HKSJ correction because it directly inverts the likelihood"

### Tests
- `test_hksj_ci_wider_than_z_ci` — HKSJ CI width >= z-based CI width
- `test_hksj_uses_t_distribution` — verify df=k-1 critical value
- `test_hksj_converges_to_z_at_large_k` — at k=200, HKSJ width ≈ z width (within 5%)
- `test_dl_hksj_returns_required_keys` — same interface as `dersimonian_laird`

---

## 3. API Ergonomics

### Problem
`result.params["mu"]` is awkward for a software paper. Users expect `result.mu`.

### Design

**`UBCMAResult` additions:**

```python
@property
def mu(self) -> float:
    return self.params["mu"]

@property
def tau1(self) -> float:
    return self.params["tau1"]

@property
def tau2(self) -> float:
    return self.params["tau2"]

@property
def mix_weight(self) -> float:
    return self.params["mix_weight"]

@property
def beta(self) -> np.ndarray:
    return np.asarray(self.params["beta"])

@property
def delta(self) -> np.ndarray:
    return np.asarray(self.params["delta"])

@property
def lambda_bias(self) -> np.ndarray:
    return np.asarray(self.params["lambda_bias"])

def ci(self, method: str = "profile", alpha: float = 0.05,
       fitter: UBCMAFit | None = None) -> tuple[float, float]:
    """Confidence interval for mu.

    method: "profile" (default) or "bootstrap" or "bootstrap_bca"
    fitter: required for profile/bootstrap (stored from fit call if not provided)
    Returns (ci_low, ci_high) namedtuple.
    Caches result for repeated calls with same arguments.

    Note: UBCMAResult needs to store a reference to the fitter that produced it.
    Add `fitter: UBCMAFit` field to UBCMAResult dataclass, set during fit().
    """

def to_dict(self) -> dict[str, Any]:
    """Flat dict of all estimates, CIs, diagnostics, and baseline.
    Suitable for JSON serialization or DataFrame row construction."""

def to_json(self, path: str | Path | None = None, indent: int = 2) -> str:
    """JSON export. If path given, writes to file and returns the string."""
```

**`BayesianUBCMAResult` additions:**

```python
@property
def mu(self) -> float:
    return self.summary["mu"]["mean"]

def ci(self, prob: float = 0.95) -> tuple[float, float]:
    """HDI interval for mu."""

def to_dict(self) -> dict[str, Any]:
    """Flat dict of posterior summaries + diagnostics."""

def to_json(self, path: str | Path | None = None, indent: int = 2) -> str:
```

**No breaking changes.** The `params` dict and existing methods remain. Properties are pure sugar.

### Tests
- `test_mu_property_equals_params` — `result.mu == result.params["mu"]`
- `test_ci_profile_returns_tuple` — returns 2-tuple of floats
- `test_ci_caches_result` — second call is instant (no recomputation)
- `test_to_dict_has_mu_and_ci` — dict contains "mu", "ci_low", "ci_high"
- `test_to_json_roundtrip` — `json.loads(result.to_json())` produces valid dict

---

## 4. README + Example Notebook

### README.md (repo root)

Sections:
1. **Title + badge area** — "UBCMA: Unified Bias-Calibrated Meta-Analysis"
2. **What it does** — 1 paragraph: joint model for heterogeneity, publication bias, quality-dependent bias
3. **Install** — `pip install .` and `pip install .[bayes]`
4. **Quick start** — 5-line Python snippet: load → fit → CI → print
5. **CLI** — 4 examples (fit, diagnose, fit-bayes, study)
6. **Key features** — bullet list: multi-start, profile CI, BCa bootstrap, Bayesian, 5 comparators, simulation framework
7. **Citation** — BibTeX placeholder
8. **License** — MIT (or user's choice)

### examples/quickstart.py (percent-format notebook)

```python
# %% [markdown]
# # UBCMA Quick Start
# ...
# %%
# Cell 1: Load data
# %%
# Cell 2: Fit UBCMA + CI
# %%
# Cell 3: Compare to DL/REML
# %%
# Cell 4: Diagnostics
# %%
# Cell 5: Study table
# %%
# Cell 6: Interpretation
```

Uses `verde_2021_aspirin.csv`. No new dependencies. Runnable as plain Python or as notebook via jupytext.

### Tests
- No new tests for docs (README is not testable). The notebook cells are validated by the existing test suite covering the same API.

---

## File Change Summary

| File | Action | Section |
|------|--------|---------|
| `src/ubcma/simulation_study.py` | Modify | 1 |
| `src/ubcma/cli.py` | Modify | 1 |
| `src/ubcma/comparators.py` | Modify | 2 |
| `src/ubcma/model.py` | Modify | 2, 3 |
| `src/ubcma/bayesian.py` | Modify | 3 |
| `tests/test_simulation_study.py` | Modify | 1 |
| `tests/test_comparators.py` | Modify | 2 |
| `tests/test_model.py` | Modify | 3 |
| `tests/test_api.py` | Create | 3 |
| `README.md` | Create | 4 |
| `examples/quickstart.py` | Create | 4 |

**Estimated new tests:** ~13
**Total after:** ~88 tests
**No breaking changes.**
