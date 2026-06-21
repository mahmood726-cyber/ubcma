"""Independent ML verification for the bivariate DTA Reitsma model.

This file intentionally does not import the project package.  It reads the
R/mada reference fits, fits the model from the likelihood specification, prints
per-dataset agreement, and writes a machine-readable verdict JSON.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit


TOL = 1e-6


def _prepare_counts(counts: dict[str, list[float]]) -> tuple[np.ndarray, np.ndarray]:
    tp = np.asarray(counts["TP"], dtype=float)
    fp = np.asarray(counts["FP"], dtype=float)
    fn = np.asarray(counts["FN"], dtype=float)
    tn = np.asarray(counts["TN"], dtype=float)

    if np.any(tp == 0.0) or np.any(fp == 0.0) or np.any(fn == 0.0) or np.any(tn == 0.0):
        tp = tp + 0.5
        fp = fp + 0.5
        fn = fn + 0.5
        tn = tn + 0.5

    y = np.column_stack((np.log(tp / fn), np.log(tn / fp)))
    s_diag = np.column_stack((1.0 / tp + 1.0 / fn, 1.0 / tn + 1.0 / fp))
    return y, s_diag


def _decode_theta(theta: np.ndarray) -> np.ndarray:
    tau1 = math.exp(float(theta[0]))
    tau2 = math.exp(float(theta[1]))
    rho = math.tanh(float(theta[2]))
    cov = rho * tau1 * tau2
    return np.array([[tau1 * tau1, cov], [cov, tau2 * tau2]], dtype=float)


def _gls_mean(y: np.ndarray, s_diag: np.ndarray, sigma: np.ndarray) -> tuple[np.ndarray, float]:
    sum_w = np.zeros((2, 2), dtype=float)
    sum_wy = np.zeros(2, dtype=float)
    logdet_sum = 0.0

    for row, diag in zip(y, s_diag):
        v11 = sigma[0, 0] + diag[0]
        v22 = sigma[1, 1] + diag[1]
        v12 = sigma[0, 1]
        det = v11 * v22 - v12 * v12
        if det <= 0.0 or not np.isfinite(det):
            raise FloatingPointError("non-positive marginal covariance")
        w = np.array([[v22, -v12], [-v12, v11]], dtype=float) / det
        sum_w += w
        sum_wy += w @ row
        logdet_sum += math.log(det)

    mean = np.linalg.solve(sum_w, sum_wy)
    return mean, logdet_sum


def _profile_nll(theta: np.ndarray, y: np.ndarray, s_diag: np.ndarray) -> float:
    try:
        sigma = _decode_theta(theta)
        mean, logdet_sum = _gls_mean(y, s_diag, sigma)
    except (FloatingPointError, OverflowError, np.linalg.LinAlgError):
        return float("inf")

    quad = 0.0
    for row, diag in zip(y, s_diag):
        v11 = sigma[0, 0] + diag[0]
        v22 = sigma[1, 1] + diag[1]
        v12 = sigma[0, 1]
        det = v11 * v22 - v12 * v12
        diff = row - mean
        quad += (v22 * diff[0] * diff[0] - 2.0 * v12 * diff[0] * diff[1] + v11 * diff[1] * diff[1]) / det

    return 0.5 * (logdet_sum + quad)


def _initial_thetas(y: np.ndarray, s_diag: np.ndarray) -> list[np.ndarray]:
    sample_cov = np.cov(y, rowvar=False, ddof=1)
    moment_cov = sample_cov - np.diag(np.mean(s_diag, axis=0))

    sd1 = math.sqrt(max(float(moment_cov[0, 0]), 1e-4))
    sd2 = math.sqrt(max(float(moment_cov[1, 1]), 1e-4))
    denom = sd1 * sd2
    rho = float(moment_cov[0, 1] / denom) if denom > 0.0 else 0.0
    rho = float(np.clip(rho, -0.8, 0.8))

    sd_grid = [
        (sd1, sd2),
        (max(sd1, 0.1), max(sd2, 0.1)),
        (0.25, 0.25),
        (0.5, 0.5),
        (1.0, 1.0),
        (1.5, 1.5),
    ]
    rho_grid = [rho, 0.0, -0.5, 0.5, -0.8, 0.8]

    starts: list[np.ndarray] = []
    seen: set[tuple[float, float, float]] = set()
    for s1, s2 in sd_grid:
        for r in rho_grid:
            key = (round(s1, 10), round(s2, 10), round(r, 10))
            if key in seen:
                continue
            seen.add(key)
            starts.append(np.array([math.log(s1), math.log(s2), math.atanh(float(np.clip(r, -0.95, 0.95)))], dtype=float))
    return starts


def fit_reitsma_ml(counts: dict[str, list[float]]) -> dict[str, float]:
    y, s_diag = _prepare_counts(counts)

    best = None
    for start in _initial_thetas(y, s_diag):
        rough = minimize(
            _profile_nll,
            start,
            args=(y, s_diag),
            method="Nelder-Mead",
            options={"maxiter": 5000, "xatol": 1e-11, "fatol": 1e-11},
        )
        for candidate_start in (rough.x if rough.success or np.isfinite(rough.fun) else start, start):
            refined = minimize(
                _profile_nll,
                candidate_start,
                args=(y, s_diag),
                method="BFGS",
                options={"gtol": 1e-8, "maxiter": 5000},
            )
            if best is None or refined.fun < best.fun:
                best = refined

    if best is None or not np.isfinite(best.fun):
        raise RuntimeError("optimization failed")

    sigma = _decode_theta(best.x)
    mean, _ = _gls_mean(y, s_diag, sigma)
    return {
        "M1": float(mean[0]),
        "M2": float(mean[1]),
        "sens_summary": float(expit(mean[0])),
        "spec_summary": float(expit(mean[1])),
    }


def main() -> None:
    here = Path(__file__).resolve().parent
    reference_path = here / "reference_fits.json"
    result_path = here / "verify_codex_main_result.json"

    references = json.loads(reference_path.read_text(encoding="utf-8"))
    per_dataset: dict[str, dict[str, object]] = {}
    worst_abs_diff = 0.0

    print("dataset\tM1\tM2\tsens_summary\tspec_summary\tmax_abs_diff")
    for name, ref in references.items():
        fit = fit_reitsma_ml(ref["counts"])
        diffs = {
            "M1": abs(fit["M1"] - float(ref["m1_logit_sens"])),
            "M2": abs(fit["M2"] - float(ref["m2_logit_spec"])),
            "sens_summary": abs(fit["sens_summary"] - float(ref["sens_summary"])),
            "spec_summary": abs(fit["spec_summary"] - float(ref["spec_summary"])),
        }
        dataset_worst = max(diffs.values())
        worst_abs_diff = max(worst_abs_diff, dataset_worst)
        per_dataset[name] = {
            "fit": fit,
            "abs_diff": diffs,
            "max_abs_diff": float(dataset_worst),
        }
        print(
            f"{name}\t{diffs['M1']:.12g}\t{diffs['M2']:.12g}\t"
            f"{diffs['sens_summary']:.12g}\t{diffs['spec_summary']:.12g}\t{dataset_worst:.12g}"
        )

    passed = worst_abs_diff < TOL
    print(f"worst_abs_diff\t{worst_abs_diff:.12g}")
    print(f"verdict\t{'PASS' if passed else 'FAIL'}")

    result = {
        "worst_abs_diff": float(worst_abs_diff),
        "pass": bool(passed),
        "per_dataset": per_dataset,
    }
    result_json = json.dumps(result, indent=2, sort_keys=True) + "\n"
    try:
        result_path.write_text(result_json, encoding="utf-8")
    except PermissionError:
        print("RESULT_JSON_BEGIN")
        print(result_json, end="")
        print("RESULT_JSON_END")


if __name__ == "__main__":
    main()
