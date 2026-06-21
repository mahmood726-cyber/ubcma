"""Independent ML verification for the bivariate DTA Reitsma model (agy seat).

This script performs independent Reitsma bivariate DTA estimation and compares
the output parameters to mada reference fits.
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

    # Continuity correction: if ANY study has a zero cell, add 0.5 to EVERY cell of EVERY study
    if np.any(tp == 0.0) or np.any(fp == 0.0) or np.any(fn == 0.0) or np.any(tn == 0.0):
        tp = tp + 0.5
        fp = fp + 0.5
        fn = fn + 0.5
        tn = tn + 0.5

    y = np.column_stack((np.log(tp / fn), np.log(tn / fp)))
    s_diag = np.column_stack((1.0 / tp + 1.0 / fn, 1.0 / tn + 1.0 / fp))
    return y, s_diag


def _decode_theta(theta: np.ndarray) -> np.ndarray:
    tau1 = math.exp(theta[0])
    tau2 = math.exp(theta[1])
    rho = math.tanh(theta[2])
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
            raise FloatingPointError("Non-positive marginal covariance")
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

    starts = [
        np.array([math.log(sd1), math.log(sd2), math.atanh(np.clip(rho, -0.9, 0.9))], dtype=float),
        np.array([0.0, 0.0, 0.0], dtype=float),
        np.array([-1.0, -1.0, 0.0], dtype=float),
        np.array([1.0, 1.0, 0.0], dtype=float),
        np.array([0.5, 0.5, -0.5], dtype=float),
        np.array([0.5, 0.5, 0.5], dtype=float),
    ]
    return starts


def fit_reitsma_ml(counts: dict[str, list[float]]) -> dict[str, float]:
    y, s_diag = _prepare_counts(counts)

    best_fun = float("inf")
    best_x = None

    for start in _initial_thetas(y, s_diag):
        res = minimize(_profile_nll, start, args=(y, s_diag), method="L-BFGS-B")
        if res.success and res.fun < best_fun:
            best_fun = res.fun
            best_x = res.x

    # Fallback to Nelder-Mead if needed
    if best_x is None:
        for start in _initial_thetas(y, s_diag):
            res = minimize(_profile_nll, start, args=(y, s_diag), method="Nelder-Mead")
            if res.fun < best_fun:
                best_fun = res.fun
                best_x = res.x

    if best_x is None:
        raise RuntimeError("Reitsma ML optimization failed to converge")

    sigma = _decode_theta(best_x)
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
    result_path = here / "verify_agy_result.json"

    references = json.loads(reference_path.read_text(encoding="utf-8"))
    per_dataset = {}
    worst_abs_diff = 0.0

    print("dataset\tM1_diff\tM2_diff\tsens_diff\tspec_diff\tmax_diff")
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
            f"{name}\t{diffs['M1']:.6e}\t{diffs['M2']:.6e}\t"
            f"{diffs['sens_summary']:.6e}\t{diffs['spec_summary']:.6e}\t{dataset_worst:.6e}"
        )

    passed = worst_abs_diff < TOL
    print(f"worst_abs_diff\t{worst_abs_diff:.6e}")
    print(f"verdict\t{'PASS' if passed else 'FAIL'}")

    result = {
        "worst_abs_diff": float(worst_abs_diff),
        "pass": bool(passed),
        "per_dataset": per_dataset,
    }
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
