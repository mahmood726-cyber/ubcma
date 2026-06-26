"""Independent exact-binomial bivariate GLMM verification for HSROC.

Uses only the Python standard library plus numpy/scipy.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, gammaln, log_expit, logsumexp, roots_hermite


ROOT = Path(__file__).resolve().parent
REFERENCE_FITS = ROOT / "reference_fits.json"
REFERENCE_GLMM = ROOT / "reference_glmm.json"
RESULT_PATH = ROOT / "verify_hsroc_codex_main_result.json"

QUAD_NODES = 60
RHO_LIMIT = 0.999
OPT_BOUNDS = [
    (-8.0, 8.0),  # mu1
    (-8.0, 8.0),  # mu2
    (-6.0, 3.0),  # log(t1)
    (-6.0, 3.0),  # log(t2)
    (-4.0, 4.0),  # atanh(rho / RHO_LIMIT)
]


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _correct_counts(raw_counts: dict[str, list[float]]) -> dict[str, np.ndarray]:
    counts = {name: np.asarray(values, dtype=float) for name, values in raw_counts.items()}
    any_zero = any(np.any(values == 0.0) for values in counts.values())
    if any_zero:
        counts = {name: values + 0.5 for name, values in counts.items()}
    return counts


class ExactBivariateBinomial:
    def __init__(self, counts: dict[str, np.ndarray], nodes: int = QUAD_NODES) -> None:
        self.tp = counts["TP"].astype(float)
        self.fp = counts["FP"].astype(float)
        self.fn = counts["FN"].astype(float)
        self.tn = counts["TN"].astype(float)
        self.k = int(self.tp.size)

        if not (self.fp.size == self.fn.size == self.tn.size == self.k):
            raise ValueError("Count arrays must have the same length")

        n1 = self.tp + self.fn
        n0 = self.tn + self.fp
        self.log_choose = (
            gammaln(n1 + 1.0)
            - gammaln(self.tp + 1.0)
            - gammaln(self.fn + 1.0)
            + gammaln(n0 + 1.0)
            - gammaln(self.tn + 1.0)
            - gammaln(self.fp + 1.0)
        )

        gh_x, gh_w = roots_hermite(nodes)
        z = math.sqrt(2.0) * gh_x
        z1, z2 = np.meshgrid(z, z, indexing="ij")
        w2 = np.outer(gh_w, gh_w).reshape(-1) / math.pi

        self.z1 = z1.reshape(-1)
        self.z2 = z2.reshape(-1)
        self.log_weights = np.log(w2)

    @staticmethod
    def pack(mu1: float, mu2: float, t1: float, t2: float, rho: float) -> np.ndarray:
        rho = float(np.clip(rho, -RHO_LIMIT + 1e-12, RHO_LIMIT - 1e-12))
        return np.array(
            [mu1, mu2, math.log(max(t1, 1e-12)), math.log(max(t2, 1e-12)), math.atanh(rho / RHO_LIMIT)],
            dtype=float,
        )

    @staticmethod
    def unpack(theta: np.ndarray) -> tuple[float, float, float, float, float]:
        mu1 = float(theta[0])
        mu2 = float(theta[1])
        t1 = float(math.exp(theta[2]))
        t2 = float(math.exp(theta[3]))
        rho = float(RHO_LIMIT * math.tanh(theta[4]))
        return mu1, mu2, t1, t2, rho

    def nll_from_params(self, mu1: float, mu2: float, t1: float, t2: float, rho: float) -> float:
        if not np.isfinite([mu1, mu2, t1, t2, rho]).all():
            return math.inf
        if t1 <= 0.0 or t2 <= 0.0 or abs(rho) >= 1.0:
            return math.inf

        rho = float(np.clip(rho, -RHO_LIMIT, RHO_LIMIT))
        b1 = t1 * self.z1
        b2 = t2 * (rho * self.z1 + math.sqrt(max(1.0 - rho * rho, 1e-15)) * self.z2)

        eta1 = mu1 + b1
        eta2 = mu2 + b2

        log_se = log_expit(eta1)
        log_not_se = log_expit(-eta1)
        log_sp = log_expit(eta2)
        log_not_sp = log_expit(-eta2)

        log_prob = (
            self.tp[:, None] * log_se[None, :]
            + self.fn[:, None] * log_not_se[None, :]
            + self.tn[:, None] * log_sp[None, :]
            + self.fp[:, None] * log_not_sp[None, :]
            + self.log_choose[:, None]
        )
        per_study = logsumexp(log_prob + self.log_weights[None, :], axis=1)
        if not np.all(np.isfinite(per_study)):
            return math.inf
        return float(-np.sum(per_study))

    def nll(self, theta: np.ndarray) -> float:
        return self.nll_from_params(*self.unpack(theta))


def _empirical_start(counts: dict[str, np.ndarray]) -> np.ndarray:
    tp = counts["TP"]
    fp = counts["FP"]
    fn = counts["FN"]
    tn = counts["TN"]
    se = np.clip(tp / (tp + fn), 1e-5, 1.0 - 1e-5)
    sp = np.clip(tn / (tn + fp), 1e-5, 1.0 - 1e-5)
    logit_se = np.log(se / (1.0 - se))
    logit_sp = np.log(sp / (1.0 - sp))
    mu1 = float(np.median(logit_se))
    mu2 = float(np.median(logit_sp))
    t1 = float(max(np.std(logit_se, ddof=1), 0.25))
    t2 = float(max(np.std(logit_sp, ddof=1), 0.25))
    corr = float(np.corrcoef(logit_se, logit_sp)[0, 1])
    if not math.isfinite(corr):
        corr = 0.0
    return ExactBivariateBinomial.pack(mu1, mu2, min(t1, 3.0), min(t2, 3.0), corr)


def _candidate_starts(counts: dict[str, np.ndarray], glmer: dict) -> list[np.ndarray]:
    starts: list[np.ndarray] = []
    starts.append(_empirical_start(counts))
    starts.append(
        ExactBivariateBinomial.pack(
            glmer["m1_logit_sens"],
            glmer["m2_logit_spec"],
            glmer["tau_sens"],
            glmer["tau_spec"],
            glmer["rho"],
        )
    )

    empirical = starts[0].copy()
    glmer_start = starts[1].copy()
    for base in (empirical, glmer_start):
        for rho in (-0.75, -0.35, 0.0, 0.35):
            varied = base.copy()
            varied[4] = math.atanh(float(np.clip(rho / RHO_LIMIT, -0.99, 0.99)))
            starts.append(varied)
        for scale in (0.5, 1.0, 1.75):
            varied = base.copy()
            varied[2] = math.log(max(math.exp(base[2]) * scale, 1e-6))
            varied[3] = math.log(max(math.exp(base[3]) * scale, 1e-6))
            starts.append(varied)

    unique: list[np.ndarray] = []
    seen = set()
    for start in starts:
        clipped = np.array([np.clip(v, lo, hi) for v, (lo, hi) in zip(start, OPT_BOUNDS)], dtype=float)
        key = tuple(np.round(clipped, 8))
        if key not in seen:
            seen.add(key)
            unique.append(clipped)
    return unique


def fit_dataset(name: str, raw_counts: dict[str, list[float]], glmer: dict) -> dict:
    counts = _correct_counts(raw_counts)
    model = ExactBivariateBinomial(counts)

    glmer_params = (
        float(glmer["m1_logit_sens"]),
        float(glmer["m2_logit_spec"]),
        float(glmer["tau_sens"]),
        float(glmer["tau_spec"]),
        float(glmer["rho"]),
    )
    nll_glmer = model.nll_from_params(*glmer_params)

    best_theta = ExactBivariateBinomial.pack(*glmer_params)
    best_nll = nll_glmer
    for start in _candidate_starts(counts, glmer):
        result = minimize(
            model.nll,
            start,
            method="L-BFGS-B",
            bounds=OPT_BOUNDS,
            options={"maxiter": 450, "ftol": 1e-9, "gtol": 1e-5, "maxls": 30},
        )
        candidate_nll = float(result.fun) if math.isfinite(float(result.fun)) else math.inf
        if candidate_nll < best_nll:
            best_nll = candidate_nll
            best_theta = np.asarray(result.x, dtype=float)

    mu1, mu2, t1, t2, rho = model.unpack(best_theta)
    se = float(expit(mu1))
    sp = float(expit(mu2))
    dse = abs(se - float(glmer["sens_summary"]))
    dsp = abs(sp - float(glmer["spec_summary"]))

    return {
        "se": se,
        "sp": sp,
        "sens_summary": se,
        "spec_summary": sp,
        "mu1": mu1,
        "mu2": mu2,
        "t1": t1,
        "t2": t2,
        "rho": rho,
        "dse_vs_glmer": dse,
        "dsp_vs_glmer": dsp,
        "nll_mine": best_nll,
        "nll_glmer_params": nll_glmer,
        "mine_le_glmer": bool(best_nll <= nll_glmer + 1e-8),
    }


def main() -> None:
    reference_fits = _load_json(REFERENCE_FITS)
    reference_glmm = _load_json(REFERENCE_GLMM)

    per_dataset = {}
    for name, glmer in reference_glmm.items():
        if not glmer.get("ok", False):
            continue
        if name not in reference_fits:
            raise KeyError(f"{name!r} is present in reference_glmm.json but missing from reference_fits.json")
        per_dataset[name] = fit_dataset(name, reference_fits[name]["counts"], glmer)

    worst = max(
        max(values["dse_vs_glmer"], values["dsp_vs_glmer"])
        for values in per_dataset.values()
    )
    result = {
        "per_dataset": per_dataset,
        "worst_se_sp_vs_glmer": float(worst),
        "all_mine_le_glmer": bool(all(values["mine_le_glmer"] for values in per_dataset.values())),
        "quadrature_nodes_per_dimension": QUAD_NODES,
        "continuity_correction": "mada-style: if any zero cell in a dataset, add 0.5 to every cell in that dataset",
    }

    serialized = json.dumps(result, indent=2, sort_keys=True)
    if os.environ.get("VERIFY_HSROC_STDOUT_ONLY") == "1":
        print(serialized)
        return

    with RESULT_PATH.open("w", encoding="utf-8", newline="\n") as f:
        f.write(serialized)
        f.write("\n")

    print(json.dumps({
        "worst_se_sp_vs_glmer": result["worst_se_sp_vs_glmer"],
        "all_mine_le_glmer": result["all_mine_le_glmer"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
