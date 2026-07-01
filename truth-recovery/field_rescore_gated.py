"""field_rescore_gated.py -- test heterogeneity-aware AdaptShrink WITHOUT re-sim.

Iteration-2 hypothesis: adaptshrink_ens loses at tau=0.3 only because it pays a
bias-correction variance cost where there is no bias to remove. A *gated* variant
should revert to the efficient RE estimator when the selection signal is weak and
use the ensemble when it is strong:

    d  = mu_ens - mu_re                 (bias-correction magnitude)
    s  = sqrt(se_re^2 + se_ens^2)       (its sampling scale)
    z  = |d| / s                        (selection-signal strength)
    g  = z^2 / (z^2 + c)                (smooth gate in [0,1])
    mu = (1-g)*mu_re + g*mu_ens
    hw = (1-g)*hw_re + g*hw_ens         (interval interpolation)

This is computed PURELY from quantities already saved in field_v1_perrep.csv
(reml_hksj and adaptshrink_ens point + CI per replicate), so we can sweep the
gate constant c instantly and re-run the exact field-domination truth-gate before
committing to a fresh (slow) confirmatory simulation.

Usage:
    PYTHONPATH=src python truth-recovery/field_rescore_gated.py --tag v1 --c 1.0
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import field_bakeoff as F  # noqa: E402

Z975 = 1.959963984540054
OUT = Path("truth-recovery")
CELL_KEYS = F.CELL_KEYS


def build_gated(raw: pd.DataFrame, c: float, anchor: str = "adaptshrink_ens",
                base: str = "reml_hksj", name: str = "adaptshrink_gated") -> pd.DataFrame:
    """Construct gated-method per-rep rows from saved base/anchor estimates."""
    key = CELL_KEYS + ["rep"]
    a = raw[raw.method == anchor].set_index(key)
    b = raw[raw.method == base].set_index(key)
    common = a.index.intersection(b.index)
    a, b = a.loc[common], b.loc[common]
    mu_a, mu_b = a["mu_hat"].to_numpy(), b["mu_hat"].to_numpy()
    hw_a = (a["ci_high"].to_numpy() - a["ci_low"].to_numpy()) / 2.0
    hw_b = (b["ci_high"].to_numpy() - b["ci_low"].to_numpy()) / 2.0
    conv = a["converged"].to_numpy() & b["converged"].to_numpy() \
        & np.isfinite(mu_a) & np.isfinite(mu_b)
    se_a = hw_a / Z975
    se_b = hw_b / Z975
    s = np.sqrt(np.square(se_a) + np.square(se_b)) + 1e-9
    z = np.abs(mu_a - mu_b) / s
    g = np.square(z) / (np.square(z) + c)
    mu_g = (1 - g) * mu_b + g * mu_a
    hw_g = (1 - g) * hw_b + g * hw_a
    out = pd.DataFrame(index=common).reset_index()
    out["method"] = name
    out["true_mu"] = a["true_mu"].to_numpy()
    out["mu_hat"] = mu_g
    out["ci_low"] = mu_g - hw_g
    out["ci_high"] = mu_g + hw_g
    out["converged"] = conv
    return out[CELL_KEYS + ["rep", "method", "true_mu", "mu_hat", "ci_low",
                            "ci_high", "converged"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="v1")
    ap.add_argument("--c", type=float, default=1.0)
    ap.add_argument("--sweep", action="store_true",
                    help="sweep several gate constants and print domination counts")
    args = ap.parse_args()
    raw = pd.read_csv(OUT / f"field_{args.tag}_perrep.csv")

    cs = [0.25, 0.5, 1.0, 2.0, 4.0] if args.sweep else [args.c]
    for c in cs:
        gated = build_gated(raw, c)
        aug = pd.concat([raw, gated], ignore_index=True)
        score = F.score_tables(aug)
        pair = F.bootstrap_pairwise(aug, "adaptshrink_gated")
        dom = F.field_domination(score, pair, "adaptshrink_gated")
        nd = int(dom["dominates_field"].sum())
        nloss = int((dom["n_loss"] > 0).sum())
        sc_g = score[score.method == "adaptshrink_gated"]
        mean_cov = float(sc_g["raw_cov"].mean())
        under = int((sc_g["raw_cov"] < 0.80).sum())
        # tau split
        tau_lo = dom[dom.tau <= 0.1]["dominates_field"].sum()
        tau_hi = dom[dom.tau == 0.3]["dominates_field"].sum()
        print(f"c={c:<5} dominates {nd:>2}/54  (loss-cells {nloss:>2})  "
              f"tau<=.1: {tau_lo}/36  tau=.3: {tau_hi}/18  "
              f"raw_cov mean {mean_cov:.3f}  under(<.8) {under}")
        if not args.sweep:
            gated.to_csv(OUT / f"field_{args.tag}_gated_perrep.csv", index=False)
            dom.to_csv(OUT / f"field_{args.tag}_domination_adaptshrink_gated.csv", index=False)
            losses = dom[dom.n_loss > 0][["mu", "tau", "k", "mechanism", "raw_cov",
                                          "n_win", "n_tie", "n_loss", "loses_to"]]
            print("\nCells where gated still loses:")
            print(losses.to_string(index=False) if len(losses) else "  NONE")


if __name__ == "__main__":
    main()
