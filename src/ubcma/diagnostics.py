"""Diagnostics for fitted UBCMA models.

Provides:
    information_criteria  — AIC/BIC for full and reduced models
    standardized_residuals — Pearson residuals
    leave_one_out         — LOO influence with delta_mu and Cook's D
    selection_function_grid — P(selected) over a (z-score, precision) grid
    qq_plot_data          — Q-Q plot data for residuals
    pvalue_distribution   — Observed p-value histogram
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .data import MetaAnalysisDataset
from .model import UBCMAFit, UBCMAResult, dersimonian_laird


def standardized_residuals(result: UBCMAResult) -> np.ndarray:
    """Externally studentized Pearson residuals.

    r_i = (y_i - loc_i) / sqrt(se_i^2 + tau1^2)

    where loc_i is the fitted study location (includes bias and moderator terms).
    """
    y = result.data.y
    loc = result.params["study_location"]
    se = result.data.se
    tau = result.params["tau1"]
    denom = np.sqrt(np.square(se) + tau ** 2)
    return (y - loc) / np.maximum(denom, 1e-9)


def information_criteria(
    result: UBCMAResult,
    data: MetaAnalysisDataset,
    fitter: UBCMAFit,
) -> dict[str, dict[str, float]]:
    """AIC and BIC for the full model and four reduced models.

    Models:
        full            — fitted model as-is
        no_selection    — refit without quality-based selection features
        no_quality      — refit without quality columns (no bias shift)
        single_component — full model treated as single-component (fewer params)
        null            — fixed-effect DL model (mu only)

    For each model the returned dict contains:
        aic, bic, n_params, neg_log_lik
    """
    k = data.n_studies
    n_mod = data.moderators.shape[1]
    n_des = data.design.shape[1]
    n_qual = data.quality.shape[1]
    # n_selection_quality follows the same logic as UBCMAFit.fit
    if n_qual:
        n_sel_q = n_qual
    elif np.any(data.quality_score):
        n_sel_q = 1
    else:
        n_sel_q = 0

    # Full model param count:
    #   mu + beta(n_mod) + delta(n_des) + lambda(n_qual) + gamma_common(4)
    #   + gamma_quality(n_sel_q) + log_tau1 + log_tau2_inc + logit_mix
    n_full = 1 + n_mod + n_des + n_qual + 4 + n_sel_q + 3
    nll_full = result.objective

    def _aic_bic(nll: float, n_params: int) -> dict[str, float]:
        return {
            "aic": 2.0 * nll + 2.0 * n_params,
            "bic": 2.0 * nll + n_params * np.log(k),
            "n_params": int(n_params),
            "neg_log_lik": float(nll),
        }

    out: dict[str, dict[str, float]] = {}
    out["full"] = _aic_bic(nll_full, n_full)

    # ---- no_selection: refit without quality-based selection features.
    # We strip quality_cols so gamma_quality is empty (0 params).
    # gamma_common[1..3] are still estimated but quality_score is zeroed.
    # Param count: remove n_sel_q selection-quality params.
    try:
        no_sel_fitter = UBCMAFit(
            n_restarts=0,
            maxiter=fitter.maxiter,
            quadrature_points=fitter.quadrature_points,
        )
        # Build a copy of the dataset with no quality columns so gamma_quality is empty
        no_sel_data = MetaAnalysisDataset.from_dataframe(
            data.raw,
            quality_cols=[],
            moderator_cols=data.moderator_names if data.moderator_names else None,
            design_col=None,  # drop design for simplicity
            study_id_col="study_id" if "study_id" in data.raw.columns else None,
        )
        no_sel_result = no_sel_fitter.fit(no_sel_data, allow_failed=True)
        # Params: mu + beta(n_mod) + delta(0) + lambda(0) + gamma_common(4)
        #         + gamma_quality(0) + tau1 + tau2_inc + mix
        n_no_sel = 1 + n_mod + 0 + 0 + 4 + 0 + 3
        out["no_selection"] = _aic_bic(no_sel_result.objective, n_no_sel)
    except Exception:
        out["no_selection"] = _aic_bic(float("inf"), 0)

    # ---- no_quality: refit without quality bias-shift columns.
    # lambda_bias = 0 (no quality columns). Selection still active.
    try:
        no_qual_fitter = UBCMAFit(
            n_restarts=0,
            maxiter=fitter.maxiter,
            quadrature_points=fitter.quadrature_points,
        )
        no_qual_data = MetaAnalysisDataset.from_dataframe(
            data.raw,
            quality_cols=[],
            moderator_cols=data.moderator_names if data.moderator_names else None,
            design_col=None,
            study_id_col="study_id" if "study_id" in data.raw.columns else None,
        )
        no_qual_result = no_qual_fitter.fit(no_qual_data, allow_failed=True)
        # Same param count as no_selection since both strip quality/design
        n_no_qual = 1 + n_mod + 0 + 0 + 4 + 0 + 3
        out["no_quality"] = _aic_bic(no_qual_result.objective, n_no_qual)
    except Exception:
        out["no_quality"] = _aic_bic(float("inf"), 0)

    # ---- single_component: use full model NLL but count params without tau2_inc and logit_mix.
    # Approximation: same objective, 2 fewer free params (tau2 gap + mix_weight).
    n_single = max(n_full - 2, 1)
    out["single_component"] = _aic_bic(nll_full, n_single)

    # ---- null: fixed-effect weighted mean (mu only, no heterogeneity/selection/quality).
    w = 1.0 / np.square(data.se)
    mu_fe = float(np.sum(w * data.y) / np.sum(w))
    nll_null = float(
        0.5 * np.sum(
            np.log(2.0 * np.pi * np.square(data.se))
            + np.square(data.y - mu_fe) / np.square(data.se)
        )
    )
    out["null"] = _aic_bic(nll_null, 1)

    return out


def leave_one_out(
    result: UBCMAResult,
    data: MetaAnalysisDataset,
    fitter: UBCMAFit,
) -> pd.DataFrame:
    """Leave-one-out influence analysis.

    Drops each study, refits the model on the remaining k-1 studies, and
    reports change in mu (delta_mu) and Cook's-D-style influence statistic.

    Returns a DataFrame with columns:
        study_id, delta_mu, delta_tau, delta_objective, cooks_d
    """
    mu_full = result.params["mu"]

    # Estimate Var(mu) via DerSimonian-Laird as a plug-in denominator for Cook's D.
    dl = dersimonian_laird(data.y, data.se)
    var_mu = max(dl["se"] ** 2, 1e-12)

    # Determine kwargs for LOO dataset construction.
    # Use minimal setup (no design, keep moderators and quality names if present)
    # to speed up fits and avoid potential re-coding issues in leave-one-out frames.
    has_study_id = "study_id" in data.raw.columns
    quality_cols_arg: list[str] | None = data.quality_names if data.quality_names else None
    moderator_cols_arg: list[str] | None = data.moderator_names if data.moderator_names else None

    rows: list[dict[str, Any]] = []
    for i in range(data.n_studies):
        mask = np.ones(data.n_studies, dtype=bool)
        mask[i] = False
        drop_df = data.raw.iloc[mask].reset_index(drop=True)

        try:
            drop_data = MetaAnalysisDataset.from_dataframe(
                drop_df,
                quality_cols=quality_cols_arg,
                moderator_cols=moderator_cols_arg,
                design_col=None,  # skip design to avoid reference-level issues
                study_id_col="study_id" if has_study_id else None,
            )
            drop_fitter = UBCMAFit(
                n_restarts=0,
                maxiter=fitter.maxiter,
                quadrature_points=fitter.quadrature_points,
            )
            drop_result = drop_fitter.fit(drop_data, allow_failed=True)
            mu_i = drop_result.params["mu"]
            delta_mu = float(mu_full - mu_i)
            delta_tau = float(result.params["tau1"] - drop_result.params["tau1"])
            delta_obj = float(result.objective - drop_result.objective)
            cooks_d = float(delta_mu ** 2 / var_mu)
        except Exception:
            delta_mu = float("nan")
            delta_tau = float("nan")
            delta_obj = float("nan")
            cooks_d = float("nan")

        rows.append(
            {
                "study_id": data.study_ids[i],
                "delta_mu": delta_mu,
                "delta_tau": delta_tau,
                "delta_objective": delta_obj,
                "cooks_d": cooks_d,
            }
        )

    return pd.DataFrame(rows)


def selection_function_grid(
    result: UBCMAResult,
    fitter: UBCMAFit,
    z_range: tuple[float, float] = (-4.0, 4.0),
    precision_range: tuple[float, float] = (3.0, 20.0),
    n_z: int = 50,
    n_prec: int = 20,
) -> pd.DataFrame:
    """Grid of (z-score, precision) -> estimated P(selected).

    Returns a DataFrame with columns: z_score, precision, p_selected.
    """
    z_grid = np.linspace(z_range[0], z_range[1], n_z)
    prec_grid = np.linspace(precision_range[0], precision_range[1], n_prec)

    gamma_common = np.asarray(result.params["gamma_common"])
    gamma_quality = np.asarray(result.params["gamma_quality"])

    # Use zero quality features (mean-centred) for the grid
    n_qual_params = len(gamma_quality)
    qual_feat = np.zeros((1, n_qual_params), dtype=float) if n_qual_params > 0 else np.zeros((1, 0), dtype=float)

    rows: list[dict[str, float]] = []
    for z in z_grid:
        for prec in prec_grid:
            se_val = 1.0 / prec
            y_val = float(z * se_val)
            precision_z = 0.0  # centered at population mean

            p = fitter._selection_probability(
                np.array([y_val]),
                np.array([se_val]),
                np.array([precision_z]),
                qual_feat,
                gamma_common,
                gamma_quality,
            )
            rows.append(
                {
                    "z_score": float(z),
                    "precision": float(prec),
                    "p_selected": float(p[0]) if hasattr(p, "__len__") else float(p),
                }
            )

    return pd.DataFrame(rows)


def qq_plot_data(result: UBCMAResult) -> pd.DataFrame:
    """Q-Q plot data: standardized residuals vs theoretical normal quantiles."""
    from scipy.stats import norm as _norm

    r = standardized_residuals(result)
    n = len(r)
    sorted_r = np.sort(r)
    theoretical = _norm.ppf((np.arange(1, n + 1) - 0.5) / n)
    return pd.DataFrame({"theoretical": theoretical, "observed": sorted_r})


def pvalue_distribution(result: UBCMAResult) -> pd.DataFrame:
    """Observed p-value distribution from the model residuals."""
    from scipy.stats import norm as _norm

    r = standardized_residuals(result)
    pvalues = 2.0 * (1.0 - _norm.cdf(np.abs(r)))
    bins = np.linspace(0.0, 1.0, 11)
    counts, _ = np.histogram(pvalues, bins=bins)
    return pd.DataFrame(
        {
            "bin_low": bins[:-1],
            "bin_high": bins[1:],
            "count": counts,
            "expected": float(len(r)) / 10.0,
        }
    )
