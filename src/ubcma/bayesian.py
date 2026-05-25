"""Bayesian UBCMA via PyMC — NUTS sampler with mixture likelihood and selection model."""
from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any

import numpy as np

try:
    import arviz as az
    import pymc as pm
    from pytensor import tensor as pt
    HAS_PYMC = True
except ImportError:
    HAS_PYMC = False

from .data import MetaAnalysisDataset


def _check_pymc():
    if not HAS_PYMC:
        raise ImportError(
            "PyMC is required for Bayesian UBCMA. Install with: pip install ubcma[bayes]"
        )


@dataclass
class BayesianUBCMAResult:
    summary: dict[str, dict[str, float]]
    diagnostics: dict[str, Any]
    idata: Any  # arviz.InferenceData
    data: MetaAnalysisDataset

    def to_text(self) -> str:
        parts = ["Bayesian UBCMA fit summary"]
        for param, stats in self.summary.items():
            mean = stats.get("mean", float("nan"))
            sd = stats.get("sd", float("nan"))
            lo = stats.get("hdi_2.5%", float("nan"))
            hi = stats.get("hdi_97.5%", float("nan"))
            parts.append(f"  {param}: mean={mean:.4f} sd={sd:.4f} 95%CrI=[{lo:.4f}, {hi:.4f}]")
        diag = self.diagnostics
        parts.append(f"max_rhat: {diag.get('max_rhat', 'N/A')}")
        parts.append(f"min_ess_bulk: {diag.get('min_ess_bulk', 'N/A')}")
        parts.append(f"n_divergences: {diag.get('n_divergences', 'N/A')}")
        return "\n".join(parts)

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
        d: dict[str, Any] = {"mu_mean": self.mu, "diagnostics": self.diagnostics}
        for param, stats in self.summary.items():
            for stat_name, val in stats.items():
                d[f"{param}_{stat_name}"] = val
        return d

    def to_json(self, path: str | None = None, indent: int = 2) -> str:
        """JSON export. If path given, writes to file."""
        import json
        from pathlib import Path

        def _convert(obj: Any) -> Any:
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj

        s = json.dumps(self.to_dict(), indent=indent, default=_convert)
        if path is not None:
            Path(path).write_text(s, encoding="utf-8")
        return s


class BayesianUBCMAFit:
    def __init__(
        self,
        quadrature_points: int = 10,
        significance_softness: float = 6.0,
        direction_softness: float = 1.5,
    ) -> None:
        _check_pymc()
        self.quadrature_points = quadrature_points
        self.significance_softness = significance_softness
        self.direction_softness = direction_softness
        gh_x, gh_w = np.polynomial.hermite.hermgauss(quadrature_points)
        self._gh_x = gh_x
        self._gh_w = gh_w

    def build_model(
        self,
        data: MetaAnalysisDataset,
        prior_scale: float = 1.0,
        simplified: bool = False,
    ) -> pm.Model:
        """Build the PyMC model.

        If simplified=True, skips the Gauss-Hermite quadrature selection normalizer
        (much faster compilation, suitable for testing without C compiler).
        """
        y = data.y.astype(float)
        se = data.se.astype(float)
        n = data.n_studies
        moderators = data.moderators.astype(float)
        design_mat = data.design.astype(float)
        quality = data.quality.astype(float)
        quality_score = data.quality_score.astype(float)

        n_mod = moderators.shape[1]
        n_des = design_mat.shape[1]
        n_qual = quality.shape[1]
        if n_qual:
            sel_quality = quality
            n_sel_q = n_qual
        elif np.any(quality_score):
            sel_quality = quality_score.reshape(-1, 1)
            n_sel_q = 1
        else:
            sel_quality = np.zeros((n, 0))
            n_sel_q = 0

        precision = 1.0 / se
        precision_z = (precision - precision.mean()) / max(precision.std(ddof=0), 1e-9)
        s = prior_scale

        gh_x = self._gh_x
        gh_w = self._gh_w
        sig_soft = self.significance_softness
        dir_soft = self.direction_softness

        with pm.Model() as model:
            mu = pm.Normal("mu", mu=0, sigma=2.5 * s)

            if n_mod:
                beta = pm.Normal("beta", mu=0, sigma=1.5 * s, shape=n_mod)
                mod_term = pt.dot(moderators, beta)
            else:
                mod_term = 0.0

            if n_des:
                delta = pm.Normal("delta", mu=0, sigma=1.5 * s, shape=n_des)
                des_term = pt.dot(design_mat, delta)
            else:
                des_term = 0.0

            if n_qual:
                lambda_bias = pm.Normal("lambda_bias", mu=0, sigma=0.75 * s, shape=n_qual)
                bias_term = pt.dot(quality, lambda_bias)
            else:
                bias_term = 0.0

            log_tau1 = pm.Normal("log_tau1", mu=-1, sigma=1.0 * s)
            log_tau2_gap = pm.Normal("log_tau2_gap", mu=-1, sigma=1.0 * s)
            tau1 = pm.Deterministic("tau1", pt.exp(pt.clip(log_tau1, -20, 5)))
            tau2 = pm.Deterministic("tau2", tau1 + pt.exp(pt.clip(log_tau2_gap, -20, 5)))

            mix_logit = pm.Normal("mix_logit", mu=1.4, sigma=1.0 * s)
            mix_weight = pm.Deterministic("mix_weight", pm.math.sigmoid(mix_logit))

            gamma_common = pm.Normal("gamma_common", mu=0, sigma=1.0 * s, shape=4)
            if n_sel_q:
                gamma_quality = pm.Normal("gamma_quality", mu=0, sigma=0.75 * s, shape=n_sel_q)

            # Mixture marginal log-likelihood
            loc = mu + mod_term + des_term + bias_term
            sd1 = pt.sqrt(se ** 2 + tau1 ** 2)
            sd2 = pt.sqrt(se ** 2 + tau2 ** 2)

            def _log_norm(x, mean, sd_val):
                z = (x - mean) / sd_val
                return -0.5 * pt.log(2.0 * np.pi) - pt.log(sd_val) - 0.5 * z * z

            log_c1 = pt.log(mix_weight + 1e-12) + _log_norm(y, loc, sd1)
            log_c2 = pt.log(1.0 - mix_weight + 1e-12) + _log_norm(y, loc, sd2)
            log_density = pt.logaddexp(log_c1, log_c2)

            # Selection probability for observed studies
            z_obs = y / pt.maximum(se, 1e-9)
            smooth_sig = pm.math.sigmoid(sig_soft * (pt.abs(z_obs) - 1.96))
            smooth_dir = pt.tanh(z_obs / dir_soft)
            sel_linear = (
                gamma_common[0]
                + gamma_common[1] * smooth_sig
                + gamma_common[2] * precision_z
                + gamma_common[3] * smooth_dir
            )
            if n_sel_q:
                sel_linear = sel_linear + pt.dot(sel_quality, gamma_quality)
            p_sel = pt.clip(pm.math.sigmoid(sel_linear), 1e-9, 1.0 - 1e-9)

            if simplified:
                # Simplified: use only mixture density × selection (no normalizer)
                # This is faster to compile and sufficient for testing
                total_ll = pt.sum(log_density + pt.log(p_sel))
            else:
                # Full model: selection normalizer via Gauss-Hermite quadrature
                def _expected_sel_component(loc_comp, sd_comp):
                    nodes = loc_comp[:, None] + np.sqrt(2.0) * sd_comp[:, None] * gh_x[None, :]
                    z_nodes = nodes / pt.maximum(se[:, None], 1e-9)
                    sig_nodes = pm.math.sigmoid(sig_soft * (pt.abs(z_nodes) - 1.96))
                    dir_nodes = pt.tanh(z_nodes / dir_soft)
                    lin = (
                        gamma_common[0]
                        + gamma_common[1] * sig_nodes
                        + gamma_common[2] * precision_z[:, None]
                        + gamma_common[3] * dir_nodes
                    )
                    if n_sel_q:
                        lin = lin + pt.dot(sel_quality, gamma_quality)[:, None]
                    p_nodes = pt.clip(pm.math.sigmoid(lin), 1e-9, 1.0 - 1e-9)
                    return pt.sum(gh_w[None, :] * p_nodes, axis=1) / np.sqrt(np.pi)

                e_sel = (
                    mix_weight * _expected_sel_component(loc, sd1)
                    + (1.0 - mix_weight) * _expected_sel_component(loc, sd2)
                )
                e_sel = pt.maximum(e_sel, 1e-9)
                total_ll = pt.sum(log_density + pt.log(p_sel) - pt.log(e_sel))

            pm.Potential("ubcma_likelihood", total_ll)

        return model

    def fit(
        self,
        data: MetaAnalysisDataset,
        chains: int = 4,
        draws: int = 2000,
        tune: int = 1000,
        target_accept: float = 0.9,
        prior_scale: float = 1.0,
        random_seed: int = 42,
        simplified: bool = False,
    ) -> BayesianUBCMAResult:
        model = self.build_model(data, prior_scale=prior_scale, simplified=simplified)
        with model:
            idata = pm.sample(
                draws=draws,
                tune=tune,
                chains=chains,
                cores=1,  # sequential to avoid multiprocess PyTensor compilation
                target_accept=target_accept,
                random_seed=random_seed,
                progressbar=False,
            )

        summary = _extract_summary(idata)
        diagnostics = _extract_diagnostics(idata)

        if diagnostics["max_rhat"] > 1.01:
            warnings.warn(f"Rhat > 1.01 detected ({diagnostics['max_rhat']:.3f})")
        if diagnostics["min_ess_bulk"] < 400:
            warnings.warn(f"Low ESS ({diagnostics['min_ess_bulk']:.0f})")
        if diagnostics["n_divergences"] > 0:
            warnings.warn(
                f"{diagnostics['n_divergences']} divergences. "
                "Consider increasing target_accept or reparameterizing."
            )

        return BayesianUBCMAResult(
            summary=summary,
            diagnostics=diagnostics,
            idata=idata,
            data=data,
        )

    def prior_sensitivity(
        self,
        data: MetaAnalysisDataset,
        chains: int = 4,
        draws: int = 2000,
        tune: int = 1000,
        random_seed: int = 42,
        simplified: bool = False,
    ) -> dict[str, BayesianUBCMAResult]:
        scales = {"informative": 0.5, "weakly_informative": 1.0, "diffuse": 3.0}
        results = {}
        for name, scale in scales.items():
            results[name] = self.fit(
                data,
                chains=chains,
                draws=draws,
                tune=tune,
                prior_scale=scale,
                random_seed=random_seed,
                simplified=simplified,
            )
        return results


def _extract_summary(idata) -> dict[str, dict[str, float]]:
    summary_df = az.summary(idata, hdi_prob=0.95)
    result = {}
    for param in summary_df.index:
        row = summary_df.loc[param]
        result[str(param)] = {
            "mean": float(row["mean"]),
            "sd": float(row["sd"]),
            "hdi_2.5%": float(row.get("hdi_2.5%", float("nan"))),
            "hdi_97.5%": float(row.get("hdi_97.5%", float("nan"))),
        }
        if "r_hat" in row:
            result[str(param)]["rhat"] = float(row["r_hat"])
        if "ess_bulk" in row:
            result[str(param)]["ess_bulk"] = float(row["ess_bulk"])
    return result


def _extract_diagnostics(idata) -> dict[str, Any]:
    summary_df = az.summary(idata, hdi_prob=0.95)
    max_rhat = float(summary_df["r_hat"].max()) if "r_hat" in summary_df else float("nan")
    min_ess = float(summary_df["ess_bulk"].min()) if "ess_bulk" in summary_df else float("nan")
    n_div = int(idata.sample_stats["diverging"].sum().values) if hasattr(idata, "sample_stats") else 0
    return {
        "max_rhat": max_rhat,
        "min_ess_bulk": min_ess,
        "n_divergences": n_div,
    }
