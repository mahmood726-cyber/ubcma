from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit, logsumexp

from .data import MetaAnalysisDataset


def _safe_exp(x: np.ndarray | float) -> np.ndarray | float:
    return np.exp(np.clip(x, -20.0, 20.0))


def _log_normal_pdf(x: np.ndarray | float, mean: np.ndarray | float, sd: np.ndarray | float) -> np.ndarray:
    sd = np.maximum(sd, 1e-9)
    z = (x - mean) / sd
    return -0.5 * np.log(2.0 * np.pi) - np.log(sd) - 0.5 * z * z


def dersimonian_laird(y: np.ndarray, se: np.ndarray) -> dict[str, float]:
    w = 1.0 / np.square(se)
    mu_fixed = np.sum(w * y) / np.sum(w)
    q = np.sum(w * np.square(y - mu_fixed))
    c = np.sum(w) - np.sum(np.square(w)) / np.sum(w)
    tau2 = max(0.0, (q - (len(y) - 1)) / max(c, 1e-9))
    w_re = 1.0 / (np.square(se) + tau2)
    mu_random = np.sum(w_re * y) / np.sum(w_re)
    se_random = np.sqrt(1.0 / np.sum(w_re))
    return {
        "mu": float(mu_random),
        "se": float(se_random),
        "tau": float(np.sqrt(tau2)),
        "ci_low": float(mu_random - 1.96 * se_random),
        "ci_high": float(mu_random + 1.96 * se_random),
    }


def weighted_meta_regression(
    y: np.ndarray,
    se: np.ndarray,
    moderators: np.ndarray | None = None,
    design: np.ndarray | None = None,
) -> dict[str, Any]:
    x_parts = [np.ones((len(y), 1), dtype=float)]
    if moderators is not None and moderators.size:
        x_parts.append(np.asarray(moderators, dtype=float))
    if design is not None and design.size:
        x_parts.append(np.asarray(design, dtype=float))
    x = np.column_stack(x_parts)
    weights = 1.0 / np.square(se)
    xtw = x.T * weights
    xtwx = xtw @ x
    xtwy = xtw @ y
    beta = np.linalg.pinv(xtwx) @ xtwy
    covariance = np.linalg.pinv(xtwx)
    intercept_se = float(np.sqrt(max(covariance[0, 0], 0.0)))
    return {
        "intercept": float(beta[0]),
        "intercept_se": intercept_se,
        "coefficients": beta,
    }


@dataclass
class UBCMAResult:
    success: bool
    message: str
    objective: float
    params: dict[str, Any]
    data: MetaAnalysisDataset
    baseline: dict[str, float]

    def summary_frame(self) -> pd.DataFrame:
        rows = [
            {
                "parameter": "mu_target",
                "estimate": self.params["mu"],
                "description": "Reference-design expected effect at low quality-shift settings and centered moderators",
            },
            {
                "parameter": "tau_main",
                "estimate": self.params["tau1"],
                "description": "Main heterogeneity scale",
            },
            {
                "parameter": "tau_tail",
                "estimate": self.params["tau2"],
                "description": "Tail heterogeneity scale",
            },
            {
                "parameter": "mix_weight_main",
                "estimate": self.params["mix_weight"],
                "description": "Weight on the main heterogeneity component",
            },
            {
                "parameter": "naive_wls_reference_intercept",
                "estimate": self.baseline["wls_reference_intercept"],
                "description": "Reference-design weighted meta-regression intercept without selection or quality adjustment",
            },
            {
                "parameter": "dl_marginal_mean",
                "estimate": self.baseline["dl_marginal_mean"],
                "description": "Marginal DerSimonian-Laird pooled mean on the observed studies",
            },
        ]
        return pd.DataFrame(rows)

    def study_table(self) -> pd.DataFrame:
        loc = self.params["study_location"]
        bias = self.params["study_bias"]
        sel = self.params["study_selection_probability"]
        return pd.DataFrame(
            {
                "study_id": self.data.study_ids,
                "observed_y": self.data.y,
                "sei": self.data.se,
                "quality_score": self.data.quality_score,
                "fitted_location": loc,
                "estimated_quality_shift": bias,
                "selection_probability": sel,
            }
        )

    def to_text(self) -> str:
        parts = [
            "UBCMA fit summary",
            f"success: {self.success}",
            f"message: {self.message}",
            f"mu_target: {self.params['mu']:.4f}",
            f"tau_main: {self.params['tau1']:.4f}",
            f"tau_tail: {self.params['tau2']:.4f}",
            f"mix_weight_main: {self.params['mix_weight']:.4f}",
            f"naive_wls_reference_intercept: {self.baseline['wls_reference_intercept']:.4f}",
            f"naive_wls_reference_se: {self.baseline['wls_reference_se']:.4f}",
            f"dl_marginal_mean: {self.baseline['dl_marginal_mean']:.4f}",
            f"dl_marginal_tau: {self.baseline['dl_marginal_tau']:.4f}",
        ]
        if self.data.moderator_names:
            parts.append("moderator reference values:")
            for name, value in zip(
                self.data.moderator_names,
                self.data.moderator_reference_values,
            ):
                parts.append(f"  {name}: {value:.4f}")
        if self.params["bias_names"]:
            parts.append("quality-shift coefficients:")
            for name, value in zip(self.params["bias_names"], self.params["lambda_bias"]):
                parts.append(f"  {name}: {value:.4f}")
        if self.params["selection_quality_names"]:
            parts.append("selection-quality coefficients:")
            for name, value in zip(
                self.params["selection_quality_names"],
                self.params["gamma_quality"],
            ):
                parts.append(f"  {name}: {value:.4f}")
        return "\n".join(parts)


class UBCMAFit:
    def __init__(
        self,
        quadrature_points: int = 10,
        significance_softness: float = 6.0,
        direction_softness: float = 1.5,
        maxiter: int = 80,
    ) -> None:
        self.quadrature_points = quadrature_points
        self.significance_softness = significance_softness
        self.direction_softness = direction_softness
        self.maxiter = maxiter
        self._gh_x, self._gh_w = np.polynomial.hermite.hermgauss(self.quadrature_points)

    def _selection_probability(
        self,
        y: np.ndarray | float,
        se: np.ndarray | float,
        precision_z: np.ndarray | float,
        quality_features: np.ndarray,
        gamma_common: np.ndarray,
        gamma_quality: np.ndarray,
    ) -> np.ndarray:
        z = np.asarray(y) / np.maximum(np.asarray(se), 1e-9)
        smooth_significance = expit(self.significance_softness * (np.abs(z) - 1.96))
        smooth_direction = np.tanh(z / self.direction_softness)
        quality_array = np.asarray(quality_features, dtype=float)
        quality_term = (
            quality_array @ np.asarray(gamma_quality, dtype=float)
            if quality_array.size
            else 0.0
        )
        linear = (
            gamma_common[0]
            + gamma_common[1] * smooth_significance
            + gamma_common[2] * precision_z
            + gamma_common[3] * smooth_direction
            + quality_term
        )
        return np.clip(expit(linear), 1e-9, 1.0 - 1e-9)

    def _expected_selection_probability(
        self,
        loc: np.ndarray | float,
        sd: np.ndarray | float,
        se: np.ndarray | float,
        precision_z: np.ndarray | float,
        quality_features: np.ndarray,
        gamma_common: np.ndarray,
        gamma_quality: np.ndarray,
    ) -> np.ndarray:
        loc_array = np.atleast_1d(np.asarray(loc, dtype=float))
        sd_array = np.atleast_1d(np.asarray(sd, dtype=float))
        se_array = np.atleast_1d(np.asarray(se, dtype=float))
        precision_array = np.atleast_1d(np.asarray(precision_z, dtype=float))
        quality_array = np.asarray(quality_features, dtype=float)
        if quality_array.ndim == 1:
            quality_array = quality_array[:, None]
        if quality_array.shape[0] != loc_array.shape[0]:
            quality_array = np.broadcast_to(
                quality_array,
                (loc_array.shape[0], quality_array.shape[-1]),
            )

        nodes = loc_array[:, None] + np.sqrt(2.0) * sd_array[:, None] * self._gh_x[None, :]
        tiled_quality = np.repeat(quality_array[:, None, :], repeats=len(self._gh_x), axis=1)
        probs = self._selection_probability(
            nodes,
            se_array[:, None],
            precision_array[:, None],
            tiled_quality,
            gamma_common,
            gamma_quality,
        )
        expected = np.sum(self._gh_w[None, :] * probs, axis=1) / np.sqrt(np.pi)
        if np.isscalar(loc) and np.isscalar(sd):
            return expected[0]
        return expected

    def _build_start(self, data: MetaAnalysisDataset) -> np.ndarray:
        baseline = dersimonian_laird(data.y, data.se)
        n_moderators = data.moderators.shape[1]
        n_design = data.design.shape[1]
        n_quality = data.quality.shape[1]
        n_selection_quality = n_quality if n_quality else (1 if np.any(data.quality_score) else 0)
        start = [
            baseline["mu"],
            *([0.0] * n_moderators),
            *([0.0] * n_design),
            *([0.0] * n_quality),
            -0.5,
            1.0,
            0.1,
            0.0,
            *([0.2] * n_selection_quality),
            np.log(max(baseline["tau"], 0.05)),
            np.log(max(baseline["tau"], 0.05)),
            1.0,
        ]
        return np.asarray(start, dtype=float)

    def fit(self, data: MetaAnalysisDataset, allow_failed: bool = False) -> UBCMAResult:
        if data.n_studies < 4:
            raise ValueError("UBCMA needs at least 4 studies for a stable fit.")

        y = data.y.astype(float)
        se = data.se.astype(float)
        moderators = data.moderators.astype(float)
        design = data.design.astype(float)
        quality = data.quality.astype(float)
        quality_score = data.quality_score.astype(float)
        if quality.shape[1]:
            selection_quality = quality
            selection_quality_names = list(data.quality_names)
        elif np.any(quality_score):
            selection_quality = quality_score.reshape(-1, 1)
            selection_quality_names = ["quality_score"]
        else:
            selection_quality = np.zeros((data.n_studies, 0), dtype=float)
            selection_quality_names = []
        precision = 1.0 / se
        precision_z = (precision - precision.mean()) / max(precision.std(ddof=0), 1e-9)

        n_moderators = moderators.shape[1]
        n_design = design.shape[1]
        n_quality = quality.shape[1]
        n_selection_quality = selection_quality.shape[1]

        def unpack(params: np.ndarray) -> dict[str, Any]:
            idx = 0
            mu = params[idx]
            idx += 1
            beta = params[idx : idx + n_moderators]
            idx += n_moderators
            delta = params[idx : idx + n_design]
            idx += n_design
            lambda_bias = params[idx : idx + n_quality]
            idx += n_quality
            gamma_common = params[idx : idx + 4]
            idx += 4
            gamma_quality = params[idx : idx + n_selection_quality]
            idx += n_selection_quality
            tau1 = _safe_exp(params[idx])
            idx += 1
            tau2 = tau1 + _safe_exp(params[idx])
            idx += 1
            mix_weight = expit(params[idx])

            base_loc = (
                mu
                + (moderators @ beta if n_moderators else 0.0)
                + (design @ delta if n_design else 0.0)
            )
            bias_shift = quality @ lambda_bias if n_quality else np.zeros_like(y)
            loc = base_loc + bias_shift

            return {
                "mu": float(mu),
                "beta": beta,
                "delta": delta,
                "lambda_bias": lambda_bias,
                "gamma_common": gamma_common,
                "gamma_quality": gamma_quality,
                "tau1": float(tau1),
                "tau2": float(tau2),
                "mix_weight": float(mix_weight),
                "base_location": np.asarray(base_loc, dtype=float),
                "bias_shift": np.asarray(bias_shift, dtype=float),
                "location": np.asarray(loc, dtype=float),
            }

        def log_prior(params: np.ndarray, parsed: dict[str, Any]) -> float:
            mu_pen = -0.5 * (parsed["mu"] / 2.5) ** 2
            beta_pen = -0.5 * np.sum(np.square(parsed["beta"] / 1.5))
            delta_pen = -0.5 * np.sum(np.square(parsed["delta"] / 1.5))
            bias_pen = -0.5 * np.sum(np.square(parsed["lambda_bias"] / 0.75))
            gamma_common_pen = -0.5 * np.sum(np.square(parsed["gamma_common"] / 1.0))
            gamma_quality_pen = -0.5 * np.sum(np.square(parsed["gamma_quality"] / 0.75))
            tau_pen = -0.5 * ((parsed["tau1"] / 0.5) ** 2 + (parsed["tau2"] / 1.0) ** 2)
            mix_pen = -0.5 * ((parsed["mix_weight"] - 0.8) / 0.2) ** 2
            return float(
                mu_pen
                + beta_pen
                + delta_pen
                + bias_pen
                + gamma_common_pen
                + gamma_quality_pen
                + tau_pen
                + mix_pen
            )

        def objective(params: np.ndarray) -> float:
            parsed = unpack(params)
            tau1 = parsed["tau1"]
            tau2 = parsed["tau2"]
            w_main = parsed["mix_weight"]
            loc = parsed["location"]
            gamma_common = parsed["gamma_common"]
            gamma_quality = parsed["gamma_quality"]
            sd1 = np.sqrt(np.square(se) + tau1**2)
            sd2 = np.sqrt(np.square(se) + tau2**2)
            log_comp = np.vstack(
                [
                    np.log(w_main + 1e-12) + _log_normal_pdf(y, loc, sd1),
                    np.log(1.0 - w_main + 1e-12) + _log_normal_pdf(y, loc, sd2),
                ]
            )
            log_density = logsumexp(log_comp, axis=0)
            p_select_obs = self._selection_probability(
                y,
                se,
                precision_z,
                selection_quality,
                gamma_common,
                gamma_quality,
            )
            normalizer = (
                w_main
                * self._expected_selection_probability(
                    loc,
                    sd1,
                    se,
                    precision_z,
                    selection_quality,
                    gamma_common,
                    gamma_quality,
                )
                + (1.0 - w_main)
                * self._expected_selection_probability(
                    loc,
                    sd2,
                    se,
                    precision_z,
                    selection_quality,
                    gamma_common,
                    gamma_quality,
                )
            )
            normalizer = np.maximum(normalizer, 1e-9)
            total = np.sum(log_density + np.log(p_select_obs) - np.log(normalizer))
            return float(-(total + log_prior(params, parsed)))

        best = minimize(
            objective,
            self._build_start(data),
            method="L-BFGS-B",
            options={"maxiter": self.maxiter, "ftol": 1e-4},
        )
        if not best.success and not allow_failed:
            raise RuntimeError(f"UBCMA optimization failed: {best.message}")
        parsed = unpack(best.x)
        selection_probs = self._selection_probability(
            y,
            se,
            precision_z,
            selection_quality,
            parsed["gamma_common"],
            parsed["gamma_quality"],
        )
        dl_baseline = dersimonian_laird(y, se)
        wls_baseline = weighted_meta_regression(
            y,
            se,
            moderators=moderators,
            design=design,
        )
        baseline = {
            "dl_marginal_mean": dl_baseline["mu"],
            "dl_marginal_tau": dl_baseline["tau"],
            "wls_reference_intercept": wls_baseline["intercept"],
            "wls_reference_se": wls_baseline["intercept_se"],
        }
        params = {
            "mu": parsed["mu"],
            "beta": parsed["beta"],
            "delta": parsed["delta"],
            "lambda_bias": parsed["lambda_bias"],
            "gamma_common": parsed["gamma_common"],
            "gamma_quality": parsed["gamma_quality"],
            "tau1": parsed["tau1"],
            "tau2": parsed["tau2"],
            "mix_weight": parsed["mix_weight"],
            "study_location": parsed["location"],
            "study_bias": parsed["bias_shift"],
            "study_selection_probability": selection_probs,
            "bias_names": data.quality_names,
            "selection_quality_names": selection_quality_names,
        }
        return UBCMAResult(
            success=bool(best.success),
            message=str(best.message),
            objective=float(best.fun),
            params=params,
            data=data,
            baseline=baseline,
        )
