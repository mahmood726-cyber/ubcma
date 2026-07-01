"""Validate the Python bivariate estimator (ubcma.dta.reitsma) against
mada::reitsma reference fits on canonical DTA datasets.

mada models (logit sens, logit FPR); ubcma.dta models (logit sens, logit spec)
with spec = 1 - FPR, i.e. logit(spec) = -logit(FPR). The ML fit is invariant to
this sign flip of the second coordinate, so the summary points and marginal
variances must match; only the between-study/GLS off-diagonal sign flips.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ubcma.dta import from_counts, reitsma  # noqa: E402

REF = Path(__file__).resolve().parent / "reference_fits.json"


def main() -> int:
    ref = json.loads(REF.read_text())
    print(f"{'dataset':<12}{'k':>4}  {'m1 py/R':>20}  {'m2 py/R':>20}  "
          f"{'sens':>16}{'spec':>16}  max|d|")
    worst = 0.0
    for name, o in ref.items():
        c = o["counts"]
        st = from_counts(c["TP"], c["FP"], c["FN"], c["TN"])
        r = reitsma(st)
        d_m1 = abs(r["M1"] - o["m1_logit_sens"])
        d_m2 = abs(r["M2"] - o["m2_logit_spec"])
        d_se = abs(r["se_summary"] - o["sens_summary"])
        d_sp = abs(r["sp_summary"] - o["spec_summary"])
        dmax = max(d_m1, d_m2, d_se, d_sp)
        worst = max(worst, dmax)
        print(f"{name:<12}{st.k:>4}  {r['M1']:.5f}/{o['m1_logit_sens']:.5f}  "
              f"{r['M2']:.5f}/{o['m2_logit_spec']:.5f}  "
              f"{r['se_summary']:.5f}/{o['sens_summary']:.5f} "
              f"{r['sp_summary']:.5f}/{o['spec_summary']:.5f}  {dmax:.2e}")
    print(f"\nworst abs disagreement vs mada::reitsma (ML): {worst:.2e}")
    tol = 1e-3
    ok = worst < tol
    print(f"PASS (< {tol})" if ok else f"FAIL (>= {tol})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
