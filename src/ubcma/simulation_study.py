"""Factorial simulation study runner for UBCMA comparative evaluation."""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.special import expit

from .comparators import (
    copas_selection,
    pet_peese,
    quality_effects,
    reml_estimator,
    trim_and_fill,
)
from .data import MetaAnalysisDataset
from .model import UBCMAFit, dersimonian_laird


@dataclass
class ScenarioParams:
    mu: float
    tau: float
    selection_strength: str  # "none", "moderate", "strong"
    quality_bias: str  # "none", "moderate"
    k: int
    design_mix: str  # "all_rct", "mixed"


def _selection_gamma(strength: str) -> tuple[float, ...]:
    if strength == "none":
        return (0.0, 0.0, 0.0, 0.0, 0.0)
    if strength == "moderate":
        return (-0.5, 1.0, 0.2, 0.1, 0.4)
    # strong
    return (-1.5, 2.5, 0.4, 0.2, 0.8)


def _quality_lambda(bias: str) -> tuple[float, ...]:
    if bias == "none":
        return (0.0, 0.0, 0.0)
    # moderate
    return (0.1, 0.08, 0.06)


def generate_scenario_data(
    params: ScenarioParams, seed: int
) -> tuple[pd.DataFrame, float]:
    """Generate one replicate of synthetic data for a scenario."""
    rng = np.random.default_rng(seed)
    k = params.k
    se = rng.uniform(0.05, 0.25, size=k)
    quality = rng.binomial(1, p=np.array([0.35, 0.28, 0.22]), size=(k, 3)).astype(float)
    quality_score = quality.mean(axis=1)

    if params.design_mix == "all_rct":
        design = np.array(["RCT"] * k)
        design_shift = np.zeros(k)
    else:
        design = rng.choice(["RCT", "OBS"], size=k, p=[0.7, 0.3])
        design_shift = np.where(design == "OBS", 0.05, 0.0)

    heterogeneity = rng.normal(0, params.tau, size=k) if params.tau > 0 else np.zeros(k)
    bias_lambda = np.array(_quality_lambda(params.quality_bias))
    internal_bias = quality @ bias_lambda
    true_effect = params.mu + design_shift + heterogeneity
    y = rng.normal(true_effect + internal_bias, se)

    # Publication selection
    gamma = np.array(_selection_gamma(params.selection_strength))
    z = y / se
    sig = expit(6.0 * (np.abs(z) - 1.96))
    direction = np.tanh(z / 1.5)
    prec = 1.0 / se
    prec_z = (prec - prec.mean()) / max(prec.std(ddof=0), 1e-9)
    sel_prob = expit(
        gamma[0] + gamma[1] * sig + gamma[2] * prec_z
        + gamma[3] * direction + gamma[4] * quality_score
    )
    selected = rng.uniform(size=k) < sel_prob

    if selected.sum() < 4:
        return generate_scenario_data(params, seed + 1000)

    df = pd.DataFrame({
        "study_id": [f"s{i}" for i in range(k)],
        "yi": y,
        "sei": se,
        "rob_selection": quality[:, 0],
        "rob_measurement": quality[:, 1],
        "rob_reporting": quality[:, 2],
        "quality_score": quality_score,
        "design": design,
    })
    return df[selected].reset_index(drop=True), params.mu


def _run_method(
    method: str, y: np.ndarray, se: np.ndarray,
    quality_score: np.ndarray, data: MetaAnalysisDataset | None
) -> dict[str, Any]:
    """Run a single comparator method."""
    try:
        if method == "dl":
            r = dersimonian_laird(y, se)
            return {"mu_hat": r["mu"], "ci_low": r["ci_low"], "ci_high": r["ci_high"], "converged": True}
        if method == "reml":
            r = reml_estimator(y, se)
            return {"mu_hat": r["mu"], "ci_low": r["ci_low"], "ci_high": r["ci_high"], "converged": True}
        if method == "dl_hksj":
            from .comparators import knapp_hartung_adjustment
            r = dersimonian_laird(y, se)
            hk = knapp_hartung_adjustment(y, se, r["mu"], r["tau"] ** 2)
            return {"mu_hat": r["mu"], "ci_low": hk["ci_low"], "ci_high": hk["ci_high"], "converged": True}
        if method == "reml_hksj":
            r = reml_estimator(y, se, hksj=True)
            return {"mu_hat": r["mu"], "ci_low": r["ci_low"], "ci_high": r["ci_high"], "converged": True}
        if method == "trim_and_fill":
            r = trim_and_fill(y, se)
            return {"mu_hat": r["mu"], "ci_low": r["ci_low"], "ci_high": r["ci_high"], "converged": True}
        if method == "pet_peese":
            r = pet_peese(y, se)
            return {"mu_hat": r["mu"], "ci_low": r["ci_low"], "ci_high": r["ci_high"], "converged": True}
        if method == "copas":
            r = copas_selection(y, se)
            return {"mu_hat": r["mu"], "ci_low": r["ci_low"], "ci_high": r["ci_high"], "converged": True}
        if method == "quality_effects":
            r = quality_effects(y, se, quality_score)
            return {"mu_hat": r["mu"], "ci_low": r["ci_low"], "ci_high": r["ci_high"], "converged": True}
        if method == "ubcma":
            if data is None:
                return {"mu_hat": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"), "converged": False}
            fitter = UBCMAFit(n_restarts=5, maxiter=60)
            result = fitter.fit(data, allow_failed=True)
            from .inference import profile_likelihood_ci
            ci = profile_likelihood_ci(result, data, fitter, n_points=0)
            return {
                "mu_hat": result.params["mu"],
                "ci_low": ci["ci_low"],
                "ci_high": ci["ci_high"],
                "converged": result.success,
            }
        return {"mu_hat": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"), "converged": False}
    except Exception:
        return {"mu_hat": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"), "converged": False}


def run_scenario(
    params: ScenarioParams,
    methods: list[str],
    n_reps: int,
    seed: int,
    checkpoint_path: str | None = None,
) -> pd.DataFrame:
    """Run all methods on all replicates of a single scenario."""
    rows = []
    for rep in range(n_reps):
        df, true_mu = generate_scenario_data(params, seed=seed + rep)
        y = df["yi"].values
        se = df["sei"].values
        q = df["quality_score"].values if "quality_score" in df else None

        ubcma_data = None
        if "ubcma" in methods:
            try:
                has_design = df["design"].nunique() > 1 if "design" in df else False
                ubcma_data = MetaAnalysisDataset.from_dataframe(
                    df,
                    quality_cols=["rob_selection", "rob_measurement", "rob_reporting"],
                    design_col="design" if has_design else None,
                    design_reference="RCT" if has_design else None,
                    study_id_col="study_id",
                )
            except Exception:
                pass

        for method in methods:
            result = _run_method(method, y, se, q, ubcma_data)
            rows.append({
                "mu": params.mu,
                "tau": params.tau,
                "selection": params.selection_strength,
                "quality_bias": params.quality_bias,
                "k": params.k,
                "design_mix": params.design_mix,
                "method": method,
                "replicate": rep,
                "true_mu": true_mu,
                "k_published": len(df),
                **result,
            })

    result_df = pd.DataFrame(rows)
    if checkpoint_path:
        result_df.to_csv(checkpoint_path, index=False)
    return result_df


def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate performance metrics by method."""
    def _agg(group):
        bias = (group["mu_hat"] - group["true_mu"]).mean()
        rmse = np.sqrt(((group["mu_hat"] - group["true_mu"]) ** 2).mean())
        coverage = (
            (group["ci_low"] <= group["true_mu"]) & (group["true_mu"] <= group["ci_high"])
        ).mean()
        width = (group["ci_high"] - group["ci_low"]).mean()
        conv = group["converged"].mean() if "converged" in group else 1.0
        return pd.Series({
            "bias": bias,
            "rmse": rmse,
            "coverage": coverage,
            "interval_width": width,
            "convergence_rate": conv,
        })

    return df.groupby("method").apply(_agg, include_groups=False).reset_index()


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
    # markdown
    header = "| " + " | ".join(present) + " |"
    sep = "| " + " | ".join("---" for _ in present) + " |"
    rows = []
    for _, row in df.iterrows():
        rows.append("| " + " | ".join(str(row[c]) for c in present) + " |")
    return "\n".join([header, sep] + rows)
