from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.special import expit

from .data import MetaAnalysisDataset
from .model import UBCMAFit, dersimonian_laird, weighted_meta_regression


@dataclass
class SimulationSpec:
    n_studies: int = 80
    mu: float = 0.22
    tau1: float = 0.08
    tau2: float = 0.22
    mix_weight: float = 0.78
    selection_gamma: tuple[float, float, float, float, float] = (-1.0, 2.0, 0.4, 0.1, 0.8)
    bias_lambda: tuple[float, float, float] = (0.12, 0.09, 0.07)


def generate_synthetic_meta_analysis(
    seed: int = 42,
    spec: SimulationSpec | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    spec = spec or SimulationSpec()
    rng = np.random.default_rng(seed)

    study_id = np.array([f"study_{i + 1}" for i in range(spec.n_studies)])
    se = rng.uniform(0.05, 0.22, size=spec.n_studies)
    quality = rng.binomial(
        1,
        p=np.array([0.35, 0.28, 0.22]),
        size=(spec.n_studies, 3),
    ).astype(float)
    quality_score = quality.mean(axis=1)
    design = rng.choice(["RCT", "OBS"], size=spec.n_studies, p=[0.7, 0.3])
    design_shift = np.where(design == "OBS", 0.05, 0.0)
    moderators = rng.normal(0.0, 1.0, size=spec.n_studies)
    moderator_shift = 0.03 * moderators

    tau_component = np.where(
        rng.uniform(size=spec.n_studies) < spec.mix_weight,
        spec.tau1,
        spec.tau2,
    )
    heterogeneity = rng.normal(0.0, tau_component, size=spec.n_studies)
    internal_bias = quality @ np.asarray(spec.bias_lambda)
    true_effect = spec.mu + design_shift + moderator_shift + heterogeneity
    observed_mean = true_effect + internal_bias
    y = rng.normal(observed_mean, se)

    z = y / se
    smooth_significance = expit(6.0 * (np.abs(z) - 1.96))
    smooth_direction = np.tanh(z / 1.5)
    precision = 1.0 / se
    precision_z = (precision - precision.mean()) / max(precision.std(ddof=0), 1e-9)
    g = np.asarray(spec.selection_gamma)
    selection_linear = (
        g[0]
        + g[1] * smooth_significance
        + g[2] * precision_z
        + g[3] * smooth_direction
        + g[4] * quality_score
    )
    selection_probability = expit(selection_linear)
    selected = rng.uniform(size=spec.n_studies) < selection_probability

    full = pd.DataFrame(
        {
            "study_id": study_id,
            "yi": y,
            "sei": se,
            "rob_selection": quality[:, 0],
            "rob_measurement": quality[:, 1],
            "rob_reporting": quality[:, 2],
            "quality_score": quality_score,
            "moderator": moderators,
            "design": design,
            "true_effect": true_effect,
            "internal_bias": internal_bias,
            "selection_probability": selection_probability,
            "selected": selected.astype(int),
        }
    )
    published = full.loc[full["selected"] == 1].reset_index(drop=True)
    if len(published) < 8:
        return generate_synthetic_meta_analysis(seed=seed + 1, spec=spec)
    observed_columns = [
        "study_id",
        "yi",
        "sei",
        "rob_selection",
        "rob_measurement",
        "rob_reporting",
        "quality_score",
        "moderator",
        "design",
    ]
    return published[observed_columns].copy(), full


def benchmark(
    replicates: int = 1,
    seed: int = 42,
    spec: SimulationSpec | None = None,
    progress: bool = False,
) -> pd.DataFrame:
    spec = spec or SimulationSpec()
    rows: list[dict[str, float]] = []
    fitter = UBCMAFit()
    for rep in range(replicates):
        if progress:
            print(f"benchmark replicate {rep + 1}/{replicates}")
        published, _ = generate_synthetic_meta_analysis(seed=seed + rep, spec=spec)
        data = MetaAnalysisDataset.from_dataframe(
            published,
            quality_cols=["rob_selection", "rob_measurement", "rob_reporting"],
            moderator_cols=["moderator"],
            design_col="design",
            design_reference="RCT",
            study_id_col="study_id",
        )
        fit = fitter.fit(data)
        wls_baseline = weighted_meta_regression(
            data.y,
            data.se,
            moderators=data.moderators,
            design=data.design,
        )
        dl_baseline = dersimonian_laird(data.y, data.se)
        rows.append(
            {
                "replicate": rep + 1,
                "n_published": float(len(published)),
                "target_mu": spec.mu,
                "ubcma_mu": fit.params["mu"],
                "ubcma_bias": fit.params["mu"] - spec.mu,
                "wls_reference_mu": wls_baseline["intercept"],
                "wls_bias": wls_baseline["intercept"] - spec.mu,
                "dl_marginal_mean": dl_baseline["mu"],
            }
        )
    return pd.DataFrame(rows)
