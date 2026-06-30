import json
import math

import numpy as np
import pandas as pd


TARGETS = [
    ("k10_hi", "strong"),
    ("k6_thr", "strong"),
    ("k10_thr", "strong"),
    ("k20_thr", "strong"),
]


def finite_converged(df):
    return df[
        (df["converged"] == True)
        & np.isfinite(df["m1"])
        & np.isfinite(df["m2"])
    ].copy()


def area_for(rows):
    e = rows[["m1", "m2"]].to_numpy(dtype=float) - rows[["true_m1", "true_m2"]].to_numpy(dtype=float)
    w = np.cov(e, rowvar=False)
    inv_w = np.linalg.inv(w)
    d2 = np.einsum("ij,jk,ik->i", e, inv_w, e)
    return math.pi * np.quantile(d2, 0.95) * math.sqrt(np.linalg.det(w))


def paired_diff(reitsma, adapt):
    return area_for(adapt) - area_for(reitsma)


def main():
    df = pd.read_csv("dta_focus_perrep.csv")
    rng = np.random.default_rng(123)
    cells = []

    for cell, strength in TARGETS:
        subset = finite_converged(df[(df["cell"] == cell) & (df["strength"] == strength)])
        reitsma = subset[subset["method"] == "reitsma"].set_index("rep")
        adapt = subset[subset["method"] == "adaptshrink_dta"].set_index("rep")
        reps = reitsma.index.intersection(adapt.index).sort_values()

        reitsma = reitsma.loc[reps].reset_index()
        adapt = adapt.loc[reps].reset_index()

        darea = paired_diff(reitsma, adapt)
        boot = []
        n = len(reps)
        for _ in range(2000):
            idx = rng.integers(0, n, size=n)
            boot.append(paired_diff(reitsma.iloc[idx], adapt.iloc[idx]))
        boot = np.asarray(boot)
        ci_lo, ci_hi = np.percentile(boot, [2.5, 97.5])

        cells.append(
            {
                "cell": cell,
                "strength": strength,
                "n": int(n),
                "darea": float(darea),
                "ci_lo": float(ci_lo),
                "ci_hi": float(ci_hi),
                "frac_better": float(np.mean(boot < 0)),
                "robust_win": bool(ci_hi < 0),
            }
        )

    result = {
        "seat": "codex_pc2",
        "cells": cells,
        "imported_ubcma": False,
    }

    with open("verify_rederive_codex_pc2_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        f.write("\n")

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
