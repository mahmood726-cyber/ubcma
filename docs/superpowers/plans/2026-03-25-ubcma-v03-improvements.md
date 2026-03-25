# UBCMA v0.3.0 Publication-Ready Improvements — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Four targeted improvements (HKSJ correction, API ergonomics, simulation tiers, docs) to make UBCMA submission-ready for a dual methods+software paper.

**Architecture:** Build in dependency order: HKSJ first (comparators need it before simulation), then API ergonomics (used by docs), then simulation tiers (use updated methods list), then README + example notebook (uses polished API).

**Tech Stack:** Python 3.13, scipy, numpy, pandas. PyMC optional for Bayesian. unittest for tests.

**Test runner:** `cd C:\ubcma\tests && PYTHONPATH=../src python -m unittest <module> -v`

**Important performance note:** Each UBCMA model fit takes ~2s on this machine. Import overhead is ~16s. Use module-level cached fixtures. Keep `n_restarts=0-2, maxiter=20-30` in tests. Never run >20 bootstrap replicates or >50 simulation reps in unit tests.

---

### Task 1: HKSJ / Knapp-Hartung adjustment function

**Files:**
- Modify: `src/ubcma/comparators.py` (add function at end)
- Modify: `tests/test_comparators.py` (add new test class)

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_comparators.py`:

```python
from scipy.stats import t as t_dist

# Dataset for HKSJ tests
Y_SMALL = np.array([0.30, 0.45, 0.10, 0.55, 0.25])
SE_SMALL = np.array([0.10, 0.12, 0.08, 0.15, 0.09])


class HKSJTests(unittest.TestCase):
    def test_hksj_ci_wider_than_z_ci(self) -> None:
        """HKSJ CI must be at least as wide as z-based CI."""
        from ubcma.comparators import knapp_hartung_adjustment
        from ubcma.model import dersimonian_laird
        dl = dersimonian_laird(Y_SMALL, SE_SMALL)
        hksj = knapp_hartung_adjustment(Y_SMALL, SE_SMALL, dl["mu"], dl["tau"] ** 2)
        z_width = dl["ci_high"] - dl["ci_low"]
        hksj_width = hksj["ci_high"] - hksj["ci_low"]
        self.assertGreaterEqual(hksj_width, z_width - 1e-9)

    def test_hksj_uses_t_distribution(self) -> None:
        """Critical value must be t(k-1), not z."""
        from ubcma.comparators import knapp_hartung_adjustment
        from ubcma.model import dersimonian_laird
        dl = dersimonian_laird(Y_SMALL, SE_SMALL)
        hksj = knapp_hartung_adjustment(Y_SMALL, SE_SMALL, dl["mu"], dl["tau"] ** 2)
        k = len(Y_SMALL)
        t_crit = t_dist.ppf(0.975, df=k - 1)
        expected_half_width = t_crit * hksj["se_adjusted"]
        actual_half_width = (hksj["ci_high"] - hksj["ci_low"]) / 2.0
        self.assertAlmostEqual(actual_half_width, expected_half_width, places=6)

    def test_hksj_converges_to_z_at_large_k(self) -> None:
        """At k=200, HKSJ and z-based widths should be within 5%."""
        from ubcma.comparators import knapp_hartung_adjustment
        from ubcma.model import dersimonian_laird
        rng = np.random.default_rng(99)
        y_big = rng.normal(0.3, 0.15, size=200)
        se_big = rng.uniform(0.05, 0.15, size=200)
        dl = dersimonian_laird(y_big, se_big)
        hksj = knapp_hartung_adjustment(y_big, se_big, dl["mu"], dl["tau"] ** 2)
        z_width = dl["ci_high"] - dl["ci_low"]
        hksj_width = hksj["ci_high"] - hksj["ci_low"]
        ratio = hksj_width / max(z_width, 1e-9)
        self.assertAlmostEqual(ratio, 1.0, delta=0.05)

    def test_hksj_returns_required_keys(self) -> None:
        from ubcma.comparators import knapp_hartung_adjustment
        from ubcma.model import dersimonian_laird
        dl = dersimonian_laird(Y_SMALL, SE_SMALL)
        hksj = knapp_hartung_adjustment(Y_SMALL, SE_SMALL, dl["mu"], dl["tau"] ** 2)
        for key in ("mu", "se_adjusted", "ci_low", "ci_high", "q_hksj", "df"):
            self.assertIn(key, hksj)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd C:\ubcma\tests && PYTHONPATH=../src python -m unittest test_comparators.HKSJTests -v`
Expected: ImportError — `knapp_hartung_adjustment` not found

- [ ] **Step 3: Implement knapp_hartung_adjustment**

Add to end of `src/ubcma/comparators.py`:

```python
from scipy.stats import t as t_dist


def knapp_hartung_adjustment(
    y: np.ndarray, se: np.ndarray, mu: float, tau2: float,
    alpha: float = 0.05,
) -> dict[str, float]:
    """HKSJ-adjusted SE and CI using t-distribution.

    Implements IntHout et al. (2014) / Rover et al. (2015) with floor at 1.0.
    """
    k = len(y)
    s2 = np.square(se)
    w = 1.0 / (s2 + tau2)
    se_mu = float(np.sqrt(1.0 / np.sum(w)))

    # HKSJ scaling factor
    q_hksj = float(np.sum(w * np.square(y - mu)) / (k - 1))
    # Floor at 1.0 (Rover et al. 2015) — ensures HKSJ never narrows the CI
    q_hksj = max(q_hksj, 1.0)
    se_adj = se_mu * np.sqrt(q_hksj)

    df = k - 1
    t_crit = float(t_dist.ppf(1.0 - alpha / 2.0, df=df))
    return {
        "mu": mu,
        "se_adjusted": float(se_adj),
        "ci_low": mu - t_crit * se_adj,
        "ci_high": mu + t_crit * se_adj,
        "q_hksj": q_hksj,
        "df": df,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd C:\ubcma\tests && PYTHONPATH=../src python -m unittest test_comparators.HKSJTests -v`
Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
cd C:\ubcma && git add src/ubcma/comparators.py tests/test_comparators.py
git commit -m "feat: add HKSJ / Knapp-Hartung adjustment (Task 1)"
```

---

### Task 2: Add DL+HKSJ and REML+HKSJ to simulation study methods

**Files:**
- Modify: `src/ubcma/simulation_study.py` (add methods to `_run_method`)
- Modify: `src/ubcma/comparators.py` (add `hksj` param to `reml_estimator`)

- [ ] **Step 1: Add hksj parameter to reml_estimator**

In `src/ubcma/comparators.py`, change `reml_estimator` signature and CI computation:

```python
def reml_estimator(y: np.ndarray, se: np.ndarray, hksj: bool = False) -> dict[str, float]:
```

After computing `mu`, `se_mu`, `tau`, add before the return:

```python
    if hksj:
        hk = knapp_hartung_adjustment(y, se, mu, tau2, alpha=0.05)
        return {
            "mu": mu,
            "se": float(hk["se_adjusted"]),
            "tau": float(tau),
            "ci_low": hk["ci_low"],
            "ci_high": hk["ci_high"],
        }
```

- [ ] **Step 2: Add dl_hksj and reml_hksj to _run_method in simulation_study.py**

Add these cases after the existing `"reml"` case in `_run_method`:

```python
        elif method == "dl_hksj":
            from .comparators import knapp_hartung_adjustment
            r = dersimonian_laird(y, se)
            hk = knapp_hartung_adjustment(y, se, r["mu"], r["tau"] ** 2)
            return {"mu_hat": r["mu"], "ci_low": hk["ci_low"], "ci_high": hk["ci_high"], "converged": True}
        elif method == "reml_hksj":
            r = reml_estimator(y, se, hksj=True)
            return {"mu_hat": r["mu"], "ci_low": r["ci_low"], "ci_high": r["ci_high"], "converged": True}
```

- [ ] **Step 3: Run existing comparator + simulation tests to check nothing broke**

Run: `cd C:\ubcma\tests && PYTHONPATH=../src python -m unittest test_comparators test_simulation_study -v`
Expected: All existing tests PASS (no regressions)

- [ ] **Step 4: Commit**

```bash
cd C:\ubcma && git add src/ubcma/comparators.py src/ubcma/simulation_study.py
git commit -m "feat: add DL+HKSJ and REML+HKSJ methods for simulation study (Task 2)"
```

---

### Task 3: API ergonomics — properties on UBCMAResult

**Files:**
- Modify: `src/ubcma/model.py` (add properties + `fitter` field to `UBCMAResult`)
- Create: `tests/test_api.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_api.py`:

```python
"""Tests for API ergonomics — property access, ci(), to_dict, to_json."""
from __future__ import annotations

import json
import unittest

import numpy as np
import pandas as pd

from ubcma.data import MetaAnalysisDataset
from ubcma.model import UBCMAFit

# Minimal cached fixture
_RESULT = None
_DATA = None
_FITTER = None


def _get_result():
    global _RESULT, _DATA, _FITTER
    if _RESULT is None:
        rng = np.random.default_rng(7)
        n = 8
        df = pd.DataFrame({
            "study_id": [f"s{i}" for i in range(n)],
            "yi": rng.normal(0.3, 0.15, size=n),
            "sei": rng.uniform(0.05, 0.12, size=n),
        })
        _DATA = MetaAnalysisDataset.from_dataframe(df, study_id_col="study_id")
        _FITTER = UBCMAFit(n_restarts=0, maxiter=20)
        _RESULT = _FITTER.fit(_DATA, allow_failed=True)
    return _RESULT, _DATA, _FITTER


class PropertyTests(unittest.TestCase):
    def test_mu_property(self) -> None:
        result, _, _ = _get_result()
        self.assertEqual(result.mu, result.params["mu"])

    def test_tau1_property(self) -> None:
        result, _, _ = _get_result()
        self.assertEqual(result.tau1, result.params["tau1"])

    def test_tau2_property(self) -> None:
        result, _, _ = _get_result()
        self.assertEqual(result.tau2, result.params["tau2"])

    def test_mix_weight_property(self) -> None:
        result, _, _ = _get_result()
        self.assertEqual(result.mix_weight, result.params["mix_weight"])

    def test_fitter_stored(self) -> None:
        result, _, fitter = _get_result()
        self.assertIs(result.fitter, fitter)


class ToDictTests(unittest.TestCase):
    def test_to_dict_has_mu(self) -> None:
        result, _, _ = _get_result()
        d = result.to_dict()
        self.assertIn("mu", d)
        self.assertEqual(d["mu"], result.mu)

    def test_to_dict_has_tau(self) -> None:
        result, _, _ = _get_result()
        d = result.to_dict()
        self.assertIn("tau1", d)
        self.assertIn("tau2", d)

    def test_to_dict_serializable(self) -> None:
        result, _, _ = _get_result()
        d = result.to_dict()
        # Must be JSON-serializable (no numpy arrays)
        json_str = json.dumps(d)
        self.assertIsInstance(json_str, str)


class ToJsonTests(unittest.TestCase):
    def test_to_json_roundtrip(self) -> None:
        result, _, _ = _get_result()
        json_str = result.to_json()
        d = json.loads(json_str)
        self.assertAlmostEqual(d["mu"], result.mu, places=6)

    def test_to_json_to_file(self) -> None:
        import tempfile, os
        result, _, _ = _get_result()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "result.json")
            result.to_json(path=path)
            self.assertTrue(os.path.exists(path))
            with open(path) as f:
                d = json.load(f)
            self.assertIn("mu", d)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd C:\ubcma\tests && PYTHONPATH=../src python -m unittest test_api -v`
Expected: AttributeError — `UBCMAResult` has no `mu` property

- [ ] **Step 3: Add `fitter` field and properties to UBCMAResult**

In `src/ubcma/model.py`, modify the `UBCMAResult` dataclass at line 68:

```python
@dataclass
class UBCMAResult:
    success: bool
    message: str
    objective: float
    params: dict[str, Any]
    data: MetaAnalysisDataset
    baseline: dict[str, float]
    fitter: Any = None  # UBCMAFit reference, set during fit()

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

    def to_dict(self) -> dict[str, Any]:
        """Flat dict of key estimates, JSON-serializable."""
        return {
            "mu": self.mu,
            "tau1": self.tau1,
            "tau2": self.tau2,
            "mix_weight": self.mix_weight,
            "success": self.success,
            "objective": self.objective,
            "beta": [float(x) for x in self.params["beta"]],
            "delta": [float(x) for x in self.params["delta"]],
            "lambda_bias": [float(x) for x in self.params["lambda_bias"]],
            "gamma_common": [float(x) for x in self.params["gamma_common"]],
            "baseline": {k: float(v) for k, v in self.baseline.items()},
        }

    def to_json(self, path: str | None = None, indent: int = 2) -> str:
        """JSON export. If path given, writes to file."""
        import json
        from pathlib import Path
        s = json.dumps(self.to_dict(), indent=indent)
        if path is not None:
            Path(path).write_text(s, encoding="utf-8")
        return s
```

- [ ] **Step 4: Pass `fitter` reference in UBCMAFit.fit()**

In `src/ubcma/model.py`, in the `fit()` method (around line 556 where `UBCMAResult` is constructed), add `fitter=self`:

```python
        return UBCMAResult(
            success=bool(best.success),
            message=str(best.message),
            objective=float(best.fun),
            params=params,
            data=data,
            baseline=baseline,
            fitter=self,
        )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd C:\ubcma\tests && PYTHONPATH=../src python -m unittest test_api -v`
Expected: All 10 tests PASS

- [ ] **Step 6: Run full suite to check no regressions**

Run: `cd C:\ubcma\tests && PYTHONPATH=../src python -m unittest test_smoke test_model test_inference test_diagnostics test_validation test_comparators test_simulation_study test_api -v`
Expected: All tests PASS (some Bayesian tests may be skipped)

- [ ] **Step 7: Commit**

```bash
cd C:\ubcma && git add src/ubcma/model.py tests/test_api.py
git commit -m "feat: add properties, to_dict, to_json to UBCMAResult (Task 3)"
```

---

### Task 4: API ergonomics — BayesianUBCMAResult properties

**Files:**
- Modify: `src/ubcma/bayesian.py` (add properties to `BayesianUBCMAResult`)

- [ ] **Step 1: Add properties to BayesianUBCMAResult**

In `src/ubcma/bayesian.py`, add after the existing `to_text()` method on `BayesianUBCMAResult` (around line 48):

```python
    @property
    def mu(self) -> float:
        return self.summary["mu"]["mean"]

    def ci(self, prob: float = 0.95) -> tuple[float, float]:
        """HDI interval for mu."""
        lo_key = f"hdi_{(1 - prob) / 2 * 100:.1f}%"
        hi_key = f"hdi_{(1 + prob) / 2 * 100:.1f}%"
        mu_stats = self.summary["mu"]
        return (mu_stats.get(lo_key, float("nan")), mu_stats.get(hi_key, float("nan")))

    def to_dict(self) -> dict[str, Any]:
        """Flat dict of posterior summaries + diagnostics."""
        d = {"mu_mean": self.mu, "diagnostics": self.diagnostics}
        for param, stats in self.summary.items():
            for stat_name, val in stats.items():
                d[f"{param}_{stat_name}"] = val
        return d

    def to_json(self, path: str | None = None, indent: int = 2) -> str:
        import json
        from pathlib import Path
        s = json.dumps(self.to_dict(), indent=indent)
        if path is not None:
            Path(path).write_text(s, encoding="utf-8")
        return s
```

- [ ] **Step 2: Run existing Bayesian tests to check no regressions**

Run: `cd C:\ubcma\tests && PYTHONPATH=../src python -c "from ubcma.bayesian import BayesianUBCMAResult; print('import OK')"` (quick import check — full Bayesian tests are slow)
Expected: "import OK"

- [ ] **Step 3: Commit**

```bash
cd C:\ubcma && git add src/ubcma/bayesian.py
git commit -m "feat: add mu property, ci(), to_dict, to_json to BayesianUBCMAResult (Task 4)"
```

---

### Task 5: Simulation study tier functions + format_table

**Files:**
- Modify: `src/ubcma/simulation_study.py` (add `run_pilot`, `run_focused`, `run_full`, `format_table`)
- Modify: `tests/test_simulation_study.py` (add tier + formatting tests)

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_simulation_study.py`:

```python
from ubcma.simulation_study import (
    ScenarioParams, run_scenario, compute_metrics,
    pilot_scenarios, focused_scenarios, format_table,
)


class TierTests(unittest.TestCase):
    def test_pilot_has_12_scenarios(self) -> None:
        self.assertEqual(len(pilot_scenarios()), 12)

    def test_focused_has_36_scenarios(self) -> None:
        self.assertEqual(len(focused_scenarios()), 36)


class FormatTableTests(unittest.TestCase):
    def test_markdown_has_header_separator(self) -> None:
        df = pd.DataFrame({
            "method": ["dl", "reml"],
            "bias": [0.01, 0.02],
            "rmse": [0.10, 0.11],
            "coverage": [0.95, 0.94],
            "interval_width": [0.40, 0.42],
            "convergence_rate": [1.0, 1.0],
        })
        md = format_table(df, fmt="markdown")
        self.assertIn("|", md)
        self.assertIn("---", md)

    def test_latex_has_tabular(self) -> None:
        df = pd.DataFrame({
            "method": ["dl", "reml"],
            "bias": [0.01, 0.02],
            "rmse": [0.10, 0.11],
            "coverage": [0.95, 0.94],
            "interval_width": [0.40, 0.42],
            "convergence_rate": [1.0, 1.0],
        })
        tex = format_table(df, fmt="latex")
        self.assertIn("\\begin{tabular}", tex)
        self.assertIn("\\end{tabular}", tex)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd C:\ubcma\tests && PYTHONPATH=../src python -m unittest test_simulation_study.TierTests test_simulation_study.FormatTableTests -v`
Expected: ImportError — functions not found

- [ ] **Step 3: Implement tier functions and format_table**

Add to `src/ubcma/simulation_study.py`:

```python
import itertools


def pilot_scenarios() -> list[ScenarioParams]:
    """12-cell pilot: 3 selections x 2 biases x 2 taus, fixed mu=0.2/k=30/all_rct."""
    scenarios = []
    for sel, bias, tau in itertools.product(
        ["none", "moderate", "strong"],
        ["none", "moderate"],
        [0.0, 0.1],
    ):
        scenarios.append(ScenarioParams(
            mu=0.2, tau=tau, selection_strength=sel,
            quality_bias=bias, k=30, design_mix="all_rct",
        ))
    return scenarios


def focused_scenarios() -> list[ScenarioParams]:
    """36-cell focused: 3 mus x 2 taus x 3 selections x 2 biases, fixed k=30/all_rct."""
    scenarios = []
    for mu, tau, sel, bias in itertools.product(
        [0.0, 0.2, 0.5],
        [0.0, 0.1],
        ["none", "moderate", "strong"],
        ["none", "moderate"],
    ):
        scenarios.append(ScenarioParams(
            mu=mu, tau=tau, selection_strength=sel,
            quality_bias=bias, k=30, design_mix="all_rct",
        ))
    return scenarios


def full_scenarios() -> list[ScenarioParams]:
    """324-cell full factorial."""
    scenarios = []
    for mu, tau, sel, bias, k, des in itertools.product(
        [0.0, 0.2, 0.5],
        [0.0, 0.1, 0.3],
        ["none", "moderate", "strong"],
        ["none", "moderate"],
        [10, 30, 80],
        ["all_rct", "mixed"],
    ):
        scenarios.append(ScenarioParams(
            mu=mu, tau=tau, selection_strength=sel,
            quality_bias=bias, k=k, design_mix=des,
        ))
    return scenarios


def run_tier(
    tier: str,
    methods: list[str],
    n_reps: int,
    seed: int,
    output_dir: str,
) -> pd.DataFrame:
    """Run a complete simulation tier with checkpointing."""
    from pathlib import Path
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if tier == "pilot":
        scenarios = pilot_scenarios()
    elif tier == "focused":
        scenarios = focused_scenarios()
    else:
        scenarios = full_scenarios()

    all_results = []
    for i, params in enumerate(scenarios):
        print(f"  [{tier}] scenario {i+1}/{len(scenarios)}: "
              f"mu={params.mu} tau={params.tau} sel={params.selection_strength} "
              f"bias={params.quality_bias} k={params.k}")
        df = run_scenario(
            params, methods=methods, n_reps=n_reps,
            seed=seed + i * 10000,
            checkpoint_path=str(out / f"scenario_{i:04d}.csv"),
        )
        all_results.append(df)

    full = pd.concat(all_results, ignore_index=True)
    full.to_csv(out / "simulation_study.csv", index=False)
    metrics = compute_metrics(full)
    metrics.to_csv(out / "simulation_summary.csv", index=False)
    return full


def format_table(summary_df: pd.DataFrame, fmt: str = "markdown") -> str:
    """Format a compute_metrics() DataFrame as markdown or LaTeX table."""
    cols = ["method", "bias", "rmse", "coverage", "interval_width", "convergence_rate"]
    present = [c for c in cols if c in summary_df.columns]
    df = summary_df[present].copy()

    # Format numeric columns
    for c in present:
        if c != "method":
            df[c] = df[c].map(lambda x: f"{x:.4f}" if isinstance(x, float) else str(x))

    if fmt == "latex":
        header = " & ".join(present)
        lines = [
            "\\begin{tabular}{" + "l" * len(present) + "}",
            "\\hline",
            header + " \\\\",
            "\\hline",
        ]
        for _, row in df.iterrows():
            lines.append(" & ".join(str(row[c]) for c in present) + " \\\\")
        lines.append("\\hline")
        lines.append("\\end{tabular}")
        return "\n".join(lines)
    else:  # markdown
        header = "| " + " | ".join(present) + " |"
        sep = "| " + " | ".join("---" for _ in present) + " |"
        rows = []
        for _, row in df.iterrows():
            rows.append("| " + " | ".join(str(row[c]) for c in present) + " |")
        return "\n".join([header, sep] + rows)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd C:\ubcma\tests && PYTHONPATH=../src python -m unittest test_simulation_study -v`
Expected: All tests PASS (old + new)

- [ ] **Step 5: Commit**

```bash
cd C:\ubcma && git add src/ubcma/simulation_study.py tests/test_simulation_study.py
git commit -m "feat: add tier functions (pilot/focused/full) and format_table (Task 5)"
```

---

### Task 6: Update CLI study command with --tier flag

**Files:**
- Modify: `src/ubcma/cli.py`

- [ ] **Step 1: Replace hardcoded factorial in CLI with tier dispatch**

In `src/ubcma/cli.py`, update the `study_parser` section (around line 75-82):

Replace:
```python
    study_parser = subparsers.add_parser("study", help="Run the simulation study")
    study_parser.add_argument("--replicates", type=int, default=100)
    study_parser.add_argument("--seed", type=int, default=42)
    study_parser.add_argument("--output", type=Path, default=Path("results"))
    study_parser.add_argument(
        "--methods",
        default="dl,reml,trim_and_fill,pet_peese,copas,quality_effects,ubcma",
    )
```

With:
```python
    study_parser = subparsers.add_parser("study", help="Run the simulation study")
    study_parser.add_argument("--tier", default="pilot", choices=["pilot", "focused", "full"])
    study_parser.add_argument("--replicates", type=int, default=50)
    study_parser.add_argument("--seed", type=int, default=42)
    study_parser.add_argument("--output", type=Path, default=Path("results"))
    study_parser.add_argument(
        "--methods",
        default="dl,dl_hksj,reml,reml_hksj,trim_and_fill,pet_peese,copas,quality_effects,ubcma",
    )
```

Replace the entire `if args.command == "study":` handler (lines 193-225) with:

```python
    if args.command == "study":
        from .simulation_study import run_tier, compute_metrics, format_table
        methods = [m.strip() for m in args.methods.split(",")]
        output_dir = str(args.output / args.tier)
        full_df = run_tier(args.tier, methods, args.replicates, args.seed, output_dir)
        metrics = compute_metrics(full_df)
        print(f"\n{format_table(metrics)}")
        print(f"\nResults saved to {output_dir}")
        return
```

- [ ] **Step 2: Verify CLI parses correctly**

Run: `cd C:\ubcma && PYTHONPATH=src python -m ubcma.cli study --help`
Expected: Shows --tier flag with pilot/focused/full choices

- [ ] **Step 3: Commit**

```bash
cd C:\ubcma && git add src/ubcma/cli.py
git commit -m "feat: update CLI study command with --tier flag (Task 6)"
```

---

### Task 7: README.md

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README.md**

Create `README.md` at repo root:

```markdown
# UBCMA: Unified Bias-Calibrated Meta-Analysis

A Python framework for meta-analysis that jointly models heterogeneity, publication selection bias, and study quality-dependent bias. UBCMA uses a mixture normal likelihood with a smooth selection function, optimized via multi-start L-BFGS-B with optional Bayesian (PyMC) inference.

## Install

```bash
pip install .               # frequentist only
pip install ".[bayes]"       # adds PyMC for Bayesian inference
```

## Quick Start

```python
from ubcma import MetaAnalysisDataset, UBCMAFit

data = MetaAnalysisDataset.from_csv("data.csv", study_id_col="study_id")
result = UBCMAFit(n_restarts=20).fit(data)
print(f"mu = {result.mu:.3f}, tau = {result.tau1:.3f}")
print(result.study_table())
```

## CLI

```bash
# Fit a model
ubcma fit data.csv --quality rob_selection,rob_measurement --profile-ci

# Run diagnostics (AIC/BIC, LOO influence, residuals)
ubcma diagnose data.csv

# Bayesian fit with prior sensitivity
ubcma fit-bayes data.csv --chains 4 --prior-sensitivity

# Simulation study (pilot tier, ~30 min)
ubcma study --tier pilot --replicates 50
```

## Key Features

- **Multi-start optimization** with Latin hypercube sampling
- **Profile likelihood CIs** (exact, no HKSJ correction needed)
- **BCa bootstrap CIs** with jackknife acceleration
- **Bayesian backend** via PyMC (NUTS, prior sensitivity analysis)
- **5 comparator methods**: REML, trim-and-fill, PET-PEESE, Copas, quality-effects
- **HKSJ correction** for DL and REML comparators
- **Diagnostics**: AIC/BIC for 5 model variants, LOO influence, Cook's D
- **Three-tier simulation study** framework (pilot/focused/full factorial)

## Citation

```bibtex
@software{ubcma2026,
  title  = {UBCMA: Unified Bias-Calibrated Meta-Analysis},
  year   = {2026},
  url    = {https://github.com/TODO/ubcma}
}
```

## License

MIT
```

- [ ] **Step 2: Commit**

```bash
cd C:\ubcma && git add README.md
git commit -m "docs: add README with install, quickstart, CLI examples (Task 7)"
```

---

### Task 8: Example quickstart notebook

**Files:**
- Create: `examples/quickstart.py`

- [ ] **Step 1: Write percent-format notebook**

Create `examples/quickstart.py`:

```python
# %% [markdown]
# # UBCMA Quick Start
#
# This notebook demonstrates the core UBCMA workflow using the Verde 2021
# aspirin dataset (6 studies examining aspirin for secondary prevention).

# %%
from ubcma import (
    MetaAnalysisDataset, UBCMAFit, dersimonian_laird,
    reml_estimator, information_criteria, standardized_residuals,
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
```

- [ ] **Step 2: Verify it runs**

Run: `cd C:\ubcma\examples && PYTHONPATH=../src python quickstart.py`
Expected: Prints results without errors

- [ ] **Step 3: Commit**

```bash
cd C:\ubcma && git add examples/quickstart.py
git commit -m "docs: add quickstart example notebook (Task 8)"
```

---

### Task 9: Update __init__.py exports and tag v0.3.0

**Files:**
- Modify: `src/ubcma/__init__.py`

- [ ] **Step 1: Update exports**

Add `knapp_hartung_adjustment` to `src/ubcma/__init__.py`:

```python
from .comparators import (
    reml_estimator,
    trim_and_fill,
    pet_peese,
    copas_selection,
    quality_effects,
    knapp_hartung_adjustment,
)
```

And add `"knapp_hartung_adjustment"` to `__all__`.

- [ ] **Step 2: Run full test suite**

Run: `cd C:\ubcma\tests && PYTHONPATH=../src python -m unittest test_smoke test_model test_inference test_diagnostics test_validation test_comparators test_simulation_study test_api -v`
Expected: All tests PASS

- [ ] **Step 3: Commit and tag**

```bash
cd C:\ubcma && git add src/ubcma/__init__.py
git commit -m "chore: update exports and finalize v0.3.0 (Task 9)"
git tag v0.3.0 -m "v0.3.0: publication-ready (HKSJ, API ergonomics, simulation tiers, docs)"
```

---

### Task 10: Run pilot simulation study

**Files:**
- Output: `results/pilot/` (gitignored)

- [ ] **Step 1: Run the pilot tier (12 cells, 50 reps, 9 methods)**

Run: `cd C:\ubcma && PYTHONPATH=src python -m ubcma.cli study --tier pilot --replicates 50 --output results`

This will take ~30-60 min. Run in background. Methods: dl, dl_hksj, reml, reml_hksj, trim_and_fill, pet_peese, copas, quality_effects, ubcma.

- [ ] **Step 2: Inspect results**

Run: `cd C:\ubcma && PYTHONPATH=src python -c "
import pandas as pd
from ubcma.simulation_study import compute_metrics, format_table
df = pd.read_csv('results/pilot/simulation_study.csv')
metrics = compute_metrics(df)
print(format_table(metrics))
"`

Expected: Table showing bias/RMSE/coverage/width for all 9 methods. UBCMA should show lower bias than DL/REML under selection, and better coverage than uncorrected methods.

- [ ] **Step 3: Save formatted table**

Run: `cd C:\ubcma && PYTHONPATH=src python -c "
import pandas as pd
from ubcma.simulation_study import compute_metrics, format_table
df = pd.read_csv('results/pilot/simulation_study.csv')
metrics = compute_metrics(df)
with open('results/pilot/table1_draft.md', 'w') as f:
    f.write(format_table(metrics))
with open('results/pilot/table1_draft.tex', 'w') as f:
    f.write(format_table(metrics, fmt='latex'))
print('Tables saved')
"`
