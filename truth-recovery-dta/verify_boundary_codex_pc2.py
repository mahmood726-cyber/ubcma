import json
import math

import numpy as np
import pandas as pd


INPUT = "dta_boundary_perrep.csv"
OUTPUT = "verify_boundary_codex_pc2_result.json"
CELLS = ["k6_thr", "k8_thr", "k10_thr", "k12_thr", "k16_thr", "k20_thr"]
METHODS = ["reitsma", "adaptshrink_dta"]
BOOTSTRAPS = 2000


def finite_converged_rows(df):
    return df[
        (df["strength"] == "strong")
        & (df["converged"].astype(bool))
        & np.isfinite(df["m1"])
        & np.isfinite(df["m2"])
    ].copy()


def ellipse_area(errors):
    w = np.cov(errors, rowvar=False)
    inv_w = np.linalg.inv(w)
    d2 = np.einsum("ij,jk,ik->i", errors, inv_w, errors)
    return math.pi * np.quantile(d2, 0.95) * math.sqrt(np.linalg.det(w))


def aligned_errors(df, cell):
    cell_df = df[df["cell"] == cell]
    method_frames = {}
    for method in METHODS:
        method_df = cell_df[cell_df["method"] == method].set_index("rep")
        method_frames[method] = method_df[["m1", "m2", "true_m1", "true_m2"]]

    reps = method_frames["reitsma"].index.intersection(method_frames["adaptshrink_dta"].index)
    reps = reps.sort_values()

    errors = {}
    for method in METHODS:
        aligned = method_frames[method].loc[reps]
        errors[method] = aligned[["m1", "m2"]].to_numpy() - aligned[["true_m1", "true_m2"]].to_numpy()
    return reps, errors


def main():
    df = pd.read_csv(INPUT)
    valid_df = finite_converged_rows(df)
    rng = np.random.default_rng(123)
    cells = []

    for cell in CELLS:
        reps, errors = aligned_errors(valid_df, cell)
        reitsma_errors = errors["reitsma"]
        adapt_errors = errors["adaptshrink_dta"]

        reitsma_area = ellipse_area(reitsma_errors)
        adapt_area = ellipse_area(adapt_errors)
        darea = adapt_area - reitsma_area

        n = len(reps)
        diffs = np.empty(BOOTSTRAPS)
        for i in range(BOOTSTRAPS):
            idx = rng.integers(0, n, size=n)
            diffs[i] = ellipse_area(adapt_errors[idx]) - ellipse_area(reitsma_errors[idx])

        ci_lo, ci_hi = np.percentile(diffs, [2.5, 97.5])
        result = {
            "cell": cell,
            "n": int(n),
            "area_reitsma": float(reitsma_area),
            "area_adaptshrink_dta": float(adapt_area),
            "darea": float(darea),
            "ci_lo": float(ci_lo),
            "ci_hi": float(ci_hi),
            "frac_better": float(np.mean(diffs < 0)),
            "robust_win": bool(ci_hi < 0),
        }
        cells.append(result)

    output = {
        "seat": "codex_pc2",
        "input": INPUT,
        "cells": cells,
        "imported_ubcma": False,
    }

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
        f.write("\n")

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
