"""Independent ML verification for the bivariate Reitsma DTA model.

This script intentionally does not import the project package.  It implements
the model directly from the task specification and compares the concentrated ML
fit against the R mada::reitsma reference values in reference_fits.json.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit


HERE = Path(__file__).resolve().parent
REFERENCE_PATH = HERE / "reference_fits.json"
RESULT_PATH = HERE / "verify_codex_noreen_result.json"
TOL = 1e-6


def corrected_arrays(counts: dict[str, list[float]]) -> tuple[np.ndarray, ...]:
    tp = np.asarray(counts["TP"], dtype=float)
    fp = np.asarray(counts["FP"], dtype=float)
    fn = np.asarray(counts["FN"], dtype=float)
    tn = np.asarray(counts["TN"], dtype=float)
    if min(arr.min() for arr in (tp, fp, fn, tn)) == 0.0:
        tp = tp + 0.5
        fp = fp + 0.5
        fn = fn + 0.5
        tn = tn + 0.5
    return tp, fp, fn, tn


def study_estimates(counts: dict[str, list[float]]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    tp, fp, fn, tn = corrected_arrays(counts)
    y = np.column_stack((np.log(tp / fn), np.log(tn / fp)))
    s1_sq = 1.0 / tp + 1.0 / fn
    s2_sq = 1.0 / tn + 1.0 / fp
    return y, s1_sq, s2_sq


def covariance_parts(theta: np.ndarray, s1_sq: np.ndarray, s2_sq: np.ndarray) -> tuple[np.ndarray, ...]:
    tau1 = np.exp(theta[0])
    tau2 = np.exp(theta[1])
    rho = np.tanh(theta[2])
    cov12 = rho * tau1 * tau2
    v11 = tau1 * tau1 + s1_sq
    v22 = tau2 * tau2 + s2_sq
    v12 = np.full_like(v11, cov12)
    det = v11 * v22 - v12 * v12
    return v11, v22, v12, det


def gls_mean(theta: np.ndarray, y: np.ndarray, s1_sq: np.ndarray, s2_sq: np.ndarray) -> np.ndarray:
    v11, v22, v12, det = covariance_parts(theta, s1_sq, s2_sq)
    w11 = v22 / det
    w22 = v11 / det
    w12 = -v12 / det
    a11 = np.sum(w11)
    a22 = np.sum(w22)
    a12 = np.sum(w12)
    b1 = np.sum(w11 * y[:, 0] + w12 * y[:, 1])
    b2 = np.sum(w12 * y[:, 0] + w22 * y[:, 1])
    normal = np.array([[a11, a12], [a12, a22]])
    rhs = np.array([b1, b2])
    return np.linalg.solve(normal, rhs)


def neg_log_likelihood(theta: np.ndarray, y: np.ndarray, s1_sq: np.ndarray, s2_sq: np.ndarray) -> float:
    v11, v22, v12, det = covariance_parts(theta, s1_sq, s2_sq)
    if not np.all(np.isfinite(det)) or np.any(det <= 0.0):
        return np.inf

    w11 = v22 / det
    w22 = v11 / det
    w12 = -v12 / det

    a11 = np.sum(w11)
    a22 = np.sum(w22)
    a12 = np.sum(w12)
    b1 = np.sum(w11 * y[:, 0] + w12 * y[:, 1])
    b2 = np.sum(w12 * y[:, 0] + w22 * y[:, 1])

    normal = np.array([[a11, a12], [a12, a22]])
    rhs = np.array([b1, b2])
    try:
        mean = np.linalg.solve(normal, rhs)
    except np.linalg.LinAlgError:
        return np.inf

    resid1 = y[:, 0] - mean[0]
    resid2 = y[:, 1] - mean[1]
    quad = np.sum(w11 * resid1 * resid1 + 2.0 * w12 * resid1 * resid2 + w22 * resid2 * resid2)
    return 0.5 * (np.sum(np.log(det)) + quad)


def empirical_start(y: np.ndarray, s1_sq: np.ndarray, s2_sq: np.ndarray) -> np.ndarray:
    sample_cov = np.cov(y.T, ddof=1)
    tau1_sq = max(float(sample_cov[0, 0] - np.mean(s1_sq)), 0.05**2)
    tau2_sq = max(float(sample_cov[1, 1] - np.mean(s2_sq)), 0.05**2)
    tau1 = np.sqrt(tau1_sq)
    tau2 = np.sqrt(tau2_sq)
    denom = tau1 * tau2
    rho = 0.0 if denom == 0.0 else float(sample_cov[0, 1] / denom)
    rho = float(np.clip(rho, -0.8, 0.8))
    return np.array([np.log(tau1), np.log(tau2), np.arctanh(rho)])


def start_grid(y: np.ndarray, s1_sq: np.ndarray, s2_sq: np.ndarray) -> list[np.ndarray]:
    starts: list[np.ndarray] = [empirical_start(y, s1_sq, s2_sq)]
    tau_values = (0.05, 0.15, 0.35, 0.75, 1.5, 3.0)
    rho_values = (-0.9, -0.5, 0.0, 0.5, 0.9)
    for tau1 in tau_values:
        for tau2 in tau_values:
            for rho in rho_values:
                starts.append(np.array([np.log(tau1), np.log(tau2), np.arctanh(rho)]))
    return starts


def fit_reitsma_ml(counts: dict[str, list[float]]) -> dict[str, float]:
    y, s1_sq, s2_sq = study_estimates(counts)
    bounds = ((-12.0, 4.0), (-12.0, 4.0), (-5.0, 5.0))
    best = None

    for start in start_grid(y, s1_sq, s2_sq):
        result = minimize(
            neg_log_likelihood,
            start,
            args=(y, s1_sq, s2_sq),
            method="L-BFGS-B",
            bounds=bounds,
            options={"ftol": 1e-13, "gtol": 1e-8, "maxiter": 2000, "maxls": 50},
        )
        if result.fun == np.inf or not np.isfinite(result.fun):
            continue
        if best is None or result.fun < best.fun:
            best = result

    if best is None or not best.success:
        message = "no successful optimizer result" if best is None else best.message
        raise RuntimeError(f"ML optimization failed: {message}")

    # A second polish from the best point tightens the finite-difference optimum.
    polished = minimize(
        neg_log_likelihood,
        best.x,
        args=(y, s1_sq, s2_sq),
        method="L-BFGS-B",
        bounds=bounds,
        options={"ftol": 1e-15, "gtol": 1e-10, "maxiter": 4000, "maxls": 100},
    )
    if polished.success and np.isfinite(polished.fun) and polished.fun <= best.fun + 1e-9:
        best = polished

    mean = gls_mean(best.x, y, s1_sq, s2_sq)
    return {
        "M1": float(mean[0]),
        "M2": float(mean[1]),
        "sens_summary": float(expit(mean[0])),
        "spec_summary": float(expit(mean[1])),
        "neg_log_likelihood": float(best.fun),
    }


def main() -> None:
    reference = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
    per_dataset: dict[str, dict[str, object]] = {}
    worst_abs_diff = 0.0

    columns = (
        "dataset",
        "abs_M1",
        "abs_M2",
        "abs_sens",
        "abs_spec",
        "max_abs",
    )
    print(f"{columns[0]:<14} {columns[1]:>12} {columns[2]:>12} {columns[3]:>12} {columns[4]:>12} {columns[5]:>12}")
    print("-" * 82)

    for name, ref in reference.items():
        fit = fit_reitsma_ml(ref["counts"])
        diffs = {
            "M1": abs(fit["M1"] - float(ref["m1_logit_sens"])),
            "M2": abs(fit["M2"] - float(ref["m2_logit_spec"])),
            "sens_summary": abs(fit["sens_summary"] - float(ref["sens_summary"])),
            "spec_summary": abs(fit["spec_summary"] - float(ref["spec_summary"])),
        }
        max_abs = max(diffs.values())
        worst_abs_diff = max(worst_abs_diff, max_abs)
        per_dataset[name] = {
            "fit": fit,
            "abs_diff": diffs,
            "max_abs_diff": float(max_abs),
        }
        print(
            f"{name:<14} "
            f"{diffs['M1']:12.4g} {diffs['M2']:12.4g} "
            f"{diffs['sens_summary']:12.4g} {diffs['spec_summary']:12.4g} "
            f"{max_abs:12.4g}"
        )

    passed = bool(worst_abs_diff < TOL)
    verdict = "PASS" if passed else "FAIL"
    print("-" * 82)
    print(f"worst_abs_diff = {worst_abs_diff:.12g}")
    print(f"{verdict} at {TOL:g}")

    RESULT_PATH.write_text(
        json.dumps(
            {
                "worst_abs_diff": float(worst_abs_diff),
                "pass": passed,
                "per_dataset": per_dataset,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
