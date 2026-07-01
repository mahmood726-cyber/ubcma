"""Bounded held-out probe: can the learned-kernel field predict real AACT LOR effects
better than within-MA borrowing, when the AACT MAs are appended to the corpus?

HONEST SCOPE: the truth-first extraction (`aact_lor_expand.py`) yields only 3 coherent
pre-specified OR meta-analyses at k>=6 (28 nodes) -- AACT is structurally thin for clean
OR-synthesis once the quality bar a meta-analyst would actually use is applied (valid
2-sided 95% CI, pre-specified outcome, one median effect per trial). 28 held-out nodes is
UNDERPOWERED for a paired-bootstrap verdict, so this is an EXPLORATORY sanity probe, not a
headline. It is reported win/null/negative exactly as it falls.

Reuses the committed field machinery unchanged (`benchmark_learned.build_predictions`);
no estimator is re-implemented here.
"""
import io, sys
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "src"))
import benchmark_learned as B  # noqa: E402
from corpus import load_corpus  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def main():
    base = B.prep(load_corpus())
    aact = pd.read_csv(HERE / "aact_lor_nodes.csv")
    aact["year"] = pd.to_numeric(aact["year"], errors="coerce")
    aact = aact[["ma", "family", "specialty", "yi", "se", "year"]].copy()
    n_aact_ma = aact.ma.nunique()
    print(f"base corpus: {len(base)} nodes / {base.ma.nunique()} MAs")
    print(f"AACT add-on: {len(aact)} nodes / {n_aact_ma} MAs "
          f"(specialties {sorted(aact.specialty.unique())})")

    df = B.prep(pd.concat([base, aact], ignore_index=True))
    aact_mask = df.ma.astype(str).str.startswith("aact_").to_numpy()
    print(f"expanded corpus: {len(df)} nodes / {df.ma.nunique()} MAs ; AACT rows = {aact_mask.sum()}")

    print("building predictions on the expanded corpus (learned = honest k-fold)...")
    P, S = B.build_predictions(df)
    y = df["yi"].to_numpy(float)

    def report(mask, label):
        w = np.abs(P["within_MA"] - y)
        for k in ["learned_kernel", "robust_map", "hier_bayes"]:
            e = np.abs(P[k] - y)
            m = mask & np.isfinite(e) & np.isfinite(w)
            d, lo, hi, npair = B.pboot(e[m], w[m])
            tag = " WINS" if hi < 0 else (" worse" if lo > 0 else " n.s.")
            print(f"  [{label}] {k:14} MAE={np.nanmean(e[m]):.4f} "
                  f"within={np.nanmean(w[m]):.4f}  delta={d:+.4f} [{lo:+.4f},{hi:+.4f}] n={npair}{tag}")

    print("\n(A) held-out AACT rows only (EXPLORATORY, underpowered n=28):")
    report(aact_mask, "AACT")
    print("\n(B) whole expanded corpus (does the headline survive adding real AACT MAs?):")
    report(np.ones(len(df), bool), "ALL")

    # conformal coverage on the AACT subset (nominal 0.90 target)
    print("\n(C) learned-kernel raw 90% interval coverage on the AACT subset:")
    z = 1.6448536269514722
    cov = []
    for i in np.where(aact_mask)[0]:
        mu, sd = P["learned_kernel"][i], S["learned_kernel"][i]
        if np.isfinite(mu) and np.isfinite(sd):
            cov.append(abs(y[i] - mu) <= z * np.sqrt(sd ** 2 + df["se"].to_numpy()[i] ** 2))
    print(f"  coverage = {np.mean(cov):.3f} on n={len(cov)} (nominal 0.90; conformal calibration is corpus-level)")

    print("\nHONEST NOTE: n=28 AACT nodes / 3 MAs is underpowered; treat (A) as exploratory.")


if __name__ == "__main__":
    main()
