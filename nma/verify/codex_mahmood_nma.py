"""Independent graph-theoretic NMA verifier.

This script intentionally does not import the project NMA implementation.  It
rebuilds the random-effects GLS engine from the committed contrast-level CSVs
and compares the resulting league tables to the R netmeta references.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / "nma" / "reference"
NETWORKS = ("smoking", "senn2013")


@dataclass(frozen=True)
class ComparisonResult:
    network: str
    tau2: float
    max_abs_te: float
    max_abs_sete: float
    max_te_row: str
    max_te_col: str
    max_te_ours: float
    max_te_ref: float
    max_sete_row: str
    max_sete_col: str
    max_sete_ours: float
    max_sete_ref: float


def _study_covariance(block: pd.DataFrame, tau2: float) -> np.ndarray:
    """Return the within-study random-effects covariance for one study."""

    if len(block) == 1:
        return np.array([[float(block["seTE"].iloc[0]) ** 2 + tau2]], dtype=float)

    labels = sorted(set(block["treat1"]).union(block["treat2"]))
    index = {label: i for i, label in enumerate(labels)}

    incidence = np.zeros((len(block), len(labels)), dtype=float)
    variances = np.square(block["seTE"].to_numpy(dtype=float))

    for row_i, row in enumerate(block.itertuples(index=False)):
        incidence[row_i, index[row.treat1]] = 1.0
        incidence[row_i, index[row.treat2]] = -1.0

    pair_sum = np.square(incidence)
    arm_variances, *_ = np.linalg.lstsq(pair_sum, variances, rcond=None)
    arm_variances = arm_variances + tau2 / 2.0
    return incidence @ np.diag(arm_variances) @ incidence.T


def _block_diag(blocks: list[np.ndarray]) -> np.ndarray:
    rows = sum(block.shape[0] for block in blocks)
    out = np.zeros((rows, rows), dtype=float)
    cursor = 0
    for block in blocks:
        size = block.shape[0]
        out[cursor : cursor + size, cursor : cursor + size] = block
        cursor += size
    return out


def _random_effects_tables(
    data: pd.DataFrame, tau2: float, treatments: list[str]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    study_blocks = [block.copy() for _, block in data.groupby("studlab", sort=False)]
    data = pd.concat(study_blocks, ignore_index=True)
    treatment_index = {label: i for i, label in enumerate(treatments)}

    b_matrix = np.zeros((len(data), len(treatments)), dtype=float)
    for row_i, row in enumerate(data.itertuples(index=False)):
        b_matrix[row_i, treatment_index[row.treat1]] = 1.0
        b_matrix[row_i, treatment_index[row.treat2]] = -1.0

    y = data["TE"].to_numpy(dtype=float)

    cov_blocks = [_study_covariance(block, tau2) for block in study_blocks]
    covariance = _block_diag(cov_blocks)
    weight = np.linalg.pinv(covariance)

    laplacian = b_matrix.T @ weight @ b_matrix
    laplacian_pinv = np.linalg.pinv(laplacian)
    theta = laplacian_pinv @ b_matrix.T @ weight @ y

    te = theta[:, None] - theta[None, :]
    variances = (
        np.diag(laplacian_pinv)[:, None]
        + np.diag(laplacian_pinv)[None, :]
        - 2.0 * laplacian_pinv
    )
    variances = np.maximum(variances, 0.0)
    sete = np.sqrt(variances)

    return (
        pd.DataFrame(te, index=treatments, columns=treatments),
        pd.DataFrame(sete, index=treatments, columns=treatments),
    )


def _read_reference_table(path: Path) -> pd.DataFrame:
    table = pd.read_csv(path, index_col=0)
    table.index = table.index.astype(str)
    table.columns = table.columns.astype(str)
    return table.astype(float)


def _max_discrepancy(
    ours: pd.DataFrame, reference: pd.DataFrame
) -> tuple[float, str, str, float, float]:
    diff = (ours.loc[reference.index, reference.columns] - reference).abs()
    row_i, col_i = np.unravel_index(np.nanargmax(diff.to_numpy()), diff.shape)
    row = str(diff.index[row_i])
    col = str(diff.columns[col_i])
    return (
        float(diff.iloc[row_i, col_i]),
        row,
        col,
        float(ours.loc[row, col]),
        float(reference.loc[row, col]),
    )


def run_network(network: str) -> ComparisonResult:
    data = pd.read_csv(REF / f"{network}_input.csv")
    te_reference = _read_reference_table(REF / f"{network}_TE_random.csv")
    sete_reference = _read_reference_table(REF / f"{network}_seTE_random.csv")
    scalars = pd.read_csv(REF / f"{network}_scalars.csv")
    tau2 = float(scalars["tau2"].iloc[0])

    treatments = list(te_reference.columns)
    te, sete = _random_effects_tables(data, tau2, treatments)

    max_te, te_row, te_col, te_ours, te_ref = _max_discrepancy(te, te_reference)
    max_sete, sete_row, sete_col, sete_ours, sete_ref = _max_discrepancy(
        sete, sete_reference
    )

    return ComparisonResult(
        network=network,
        tau2=tau2,
        max_abs_te=max_te,
        max_abs_sete=max_sete,
        max_te_row=te_row,
        max_te_col=te_col,
        max_te_ours=te_ours,
        max_te_ref=te_ref,
        max_sete_row=sete_row,
        max_sete_col=sete_col,
        max_sete_ours=sete_ours,
        max_sete_ref=sete_ref,
    )


def main() -> None:
    results = [run_network(network) for network in NETWORKS]
    print("| network | tau2 | max_abs_TE | TE cell | ours | reference | max_abs_seTE | seTE cell | ours | reference |")
    print("|---|---:|---:|---|---:|---:|---:|---|---:|---:|")
    for result in results:
        print(
            f"| {result.network} | {result.tau2:.15g} | "
            f"{result.max_abs_te:.12g} | {result.max_te_row},{result.max_te_col} | "
            f"{result.max_te_ours:.12g} | {result.max_te_ref:.12g} | "
            f"{result.max_abs_sete:.12g} | {result.max_sete_row},{result.max_sete_col} | "
            f"{result.max_sete_ours:.12g} | {result.max_sete_ref:.12g} |"
        )


if __name__ == "__main__":
    main()
