"""Independent graph-theoretic random-effects NMA verifier.

This script intentionally does not import the project NMA implementation.  It
uses the R netmeta DL tau^2 values from the committed scalar CSVs, builds
study-level inverse covariance blocks, fits the GLS treatment potentials, and
compares the resulting league tables with the committed netmeta references.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DIR = REPO_ROOT / "nma" / "reference"
NETWORKS = ("smoking", "senn2013")


def read_contrasts(path: Path) -> list[dict[str, object]]:
    with path.open(newline="") as handle:
        rows = []
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "studlab": row["studlab"],
                    "treat1": row["treat1"],
                    "treat2": row["treat2"],
                    "TE": float(row["TE"]),
                    "seTE": float(row["seTE"]),
                }
            )
    return rows


def read_tau2(path: Path) -> float:
    with path.open(newline="") as handle:
        return float(next(csv.DictReader(handle))["tau2"])


def read_square_matrix(path: Path) -> tuple[list[str], np.ndarray]:
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        treatments = next(reader)[1:]
        row_names = []
        values = []
        for row in reader:
            row_names.append(row[0])
            values.append([float(value) for value in row[1:]])

    if row_names != treatments:
        raise ValueError(f"{path} row and column treatment labels differ")
    return treatments, np.asarray(values, dtype=float)


def study_covariance(rows: list[dict[str, object]], tau2: float) -> np.ndarray:
    arms = sorted({str(row["treat1"]) for row in rows} | {str(row["treat2"]) for row in rows})
    arm_index = {arm: index for index, arm in enumerate(arms)}
    n_rows = len(rows)
    n_arms = len(arms)

    incidence = np.zeros((n_rows, n_arms), dtype=float)
    endpoint_sum = np.zeros((n_rows, n_arms), dtype=float)
    pair_variances = np.zeros(n_rows, dtype=float)

    for row_index, row in enumerate(rows):
        treat1 = str(row["treat1"])
        treat2 = str(row["treat2"])
        i = arm_index[treat1]
        j = arm_index[treat2]

        incidence[row_index, i] = 1.0
        incidence[row_index, j] = -1.0
        endpoint_sum[row_index, i] = 1.0
        endpoint_sum[row_index, j] = 1.0
        pair_variances[row_index] = float(row["seTE"]) ** 2

    if n_rows == 1:
        return np.asarray([[pair_variances[0] + tau2]], dtype=float)

    arm_variances = np.linalg.lstsq(endpoint_sum, pair_variances, rcond=None)[0]
    random_arm_variances = arm_variances + tau2 / 2.0
    return incidence @ np.diag(random_arm_variances) @ incidence.T


def fit_random_effects_league(
    rows: list[dict[str, object]], treatments: list[str], tau2: float
) -> tuple[np.ndarray, np.ndarray]:
    treatment_index = {treatment: index for index, treatment in enumerate(treatments)}
    n_contrasts = len(rows)
    n_treatments = len(treatments)

    incidence = np.zeros((n_contrasts, n_treatments), dtype=float)
    observed = np.zeros(n_contrasts, dtype=float)
    by_study: dict[str, list[tuple[int, dict[str, object]]]] = defaultdict(list)

    for row_index, row in enumerate(rows):
        treat1 = str(row["treat1"])
        treat2 = str(row["treat2"])
        incidence[row_index, treatment_index[treat1]] = 1.0
        incidence[row_index, treatment_index[treat2]] = -1.0
        observed[row_index] = float(row["TE"])
        by_study[str(row["studlab"])].append((row_index, row))

    weights = np.zeros((n_contrasts, n_contrasts), dtype=float)
    for study_rows in by_study.values():
        contrast_indices = [row_index for row_index, _ in study_rows]
        covariance = study_covariance([row for _, row in study_rows], tau2)
        weight_block = np.linalg.pinv(covariance, rcond=1e-12)
        weights[np.ix_(contrast_indices, contrast_indices)] = weight_block

    laplacian = incidence.T @ weights @ incidence
    laplacian_pinv = np.linalg.pinv(laplacian, rcond=1e-12)
    theta = laplacian_pinv @ incidence.T @ weights @ observed

    league_te = theta[:, None] - theta[None, :]
    variances = (
        np.diag(laplacian_pinv)[:, None]
        + np.diag(laplacian_pinv)[None, :]
        - 2.0 * laplacian_pinv
    )
    league_sete = np.sqrt(np.maximum(variances, 0.0))
    return league_te, league_sete


def max_abs_difference(computed: np.ndarray, reference: np.ndarray, labels: list[str]) -> dict[str, object]:
    differences = computed - reference
    abs_differences = np.abs(differences)
    row_index, col_index = np.unravel_index(np.argmax(abs_differences), abs_differences.shape)
    return {
        "max_abs": float(abs_differences[row_index, col_index]),
        "row": labels[row_index],
        "col": labels[col_index],
        "computed": float(computed[row_index, col_index]),
        "reference": float(reference[row_index, col_index]),
        "signed": float(differences[row_index, col_index]),
    }


def verify_network(tag: str) -> dict[str, object]:
    rows = read_contrasts(REFERENCE_DIR / f"{tag}_input.csv")
    tau2 = read_tau2(REFERENCE_DIR / f"{tag}_scalars.csv")
    treatments, reference_te = read_square_matrix(REFERENCE_DIR / f"{tag}_TE_random.csv")
    treatments_se, reference_sete = read_square_matrix(REFERENCE_DIR / f"{tag}_seTE_random.csv")
    if treatments_se != treatments:
        raise ValueError(f"{tag} TE and seTE reference treatment labels differ")

    league_te, league_sete = fit_random_effects_league(rows, treatments, tau2)
    return {
        "tag": tag,
        "tau2": tau2,
        "te": max_abs_difference(league_te, reference_te, treatments),
        "sete": max_abs_difference(league_sete, reference_sete, treatments),
    }


def main() -> None:
    results = [verify_network(tag) for tag in NETWORKS]

    print("| network | tau2 | max abs TE error | TE cell | max abs seTE error | seTE cell |")
    print("| --- | ---: | ---: | --- | ---: | --- |")
    for result in results:
        te = result["te"]
        sete = result["sete"]
        print(
            f"| {result['tag']} | {result['tau2']:.15g} | "
            f"{te['max_abs']:.15g} | {te['row']} vs {te['col']} | "
            f"{sete['max_abs']:.15g} | {sete['row']} vs {sete['col']} |"
        )


if __name__ == "__main__":
    main()
