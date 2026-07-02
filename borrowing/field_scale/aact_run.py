"""Bounded real-AACT demonstration of the learned-kernel + conformal registry field.

Reuses the VALIDATED committed machinery unchanged:
  * learned kernel = field_learned.predict_kfold_corpus (honest 10-fold, 5-seed avg);
  * within-MA baseline = field.predict(..., 'withinMA_rel');
  * conformal = field_learned.conformal_intervals (per-family split/CV+ conformal).

Two settings:
  (A) AACT-only self-contained field  -- can the learned kernel beat within-MA
      using ONLY AACT records (LOR + LHR families)?
  (B) corpus (1177/28) + AACT expanded -- does the metadat headline survive, and
      does the field help predict the cold AACT rows?

Task 3: learned-kernel 90% interval coverage on the AACT rows BEFORE conformal
(raw model PI) and AFTER split-conformal that INCLUDES AACT-regime residuals.
"""
import io, sys
from pathlib import Path
import numpy as np
import pandas as pd

FS = Path(__file__).resolve().parent
sys.path.insert(0, str(FS))
sys.path.insert(0, str(FS.parent))  # borrowing_transport, etc.
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

from corpus import load_corpus            # noqa: E402
from field import prep, predict as field_predict  # noqa: E402
import field_learned as fl                # noqa: E402

HERE = Path(__file__).resolve().parent
SEEDS = (0, 1, 2, 3, 4)
Z90 = 1.6448536269514722


def pboot(a, b, n=5000, seed=7):
    m = np.isfinite(a) & np.isfinite(b)
    d = (a - b)[m]
    if len(d) < 2:
        return np.nan, np.nan, np.nan, 0
    rng = np.random.default_rng(seed)
    bi = rng.integers(0, len(d), size=(n, len(d)))
    md = d[bi].mean(1)
    return float(d.mean()), float(np.quantile(md, 0.025)), float(np.quantile(md, 0.975)), int(len(d))


def within_ma(df):
    out = np.full(len(df), np.nan)
    for i in range(len(df)):
        mu, _ = field_predict(df, i, "withinMA_rel")
        out[i] = mu
    return out


def delta(mask, learned, within, y, label):
    el = np.abs(learned - y); ew = np.abs(within - y)
    m = mask & np.isfinite(el) & np.isfinite(ew)
    d, lo, hi, npair = pboot(el[m], ew[m])
    tag = "LEARNED WINS" if hi < 0 else ("within better" if lo > 0 else "n.s. (tie)")
    print(f"  [{label:26}] learned MAE={np.nanmean(el[m]):.4f}  within MAE={np.nanmean(ew[m]):.4f}  "
          f"delta={d:+.4f} [{lo:+.4f},{hi:+.4f}] n={npair}  -> {tag}")
    return d, lo, hi, npair


def coverage_raw(mask, mu, sd, se, y):
    half = Z90 * np.sqrt(sd ** 2 + se ** 2)
    cov = ((mu - half <= y) & (y <= mu + half)).astype(float)
    cov[~np.isfinite(mu)] = np.nan
    return float(np.nanmean(cov[mask])), float(np.nanmean((2 * half)[mask]))


def main():
    # ------------------------------------------------------------------ load
    aact = pd.read_csv(HERE / "aact_nodes.csv")
    aact["year"] = pd.to_numeric(aact["year"], errors="coerce")
    aact = aact[["ma", "family", "specialty", "yi", "se", "year"]].copy()
    print("AACT slice by family:")
    for fam, sub in aact.groupby("family"):
        print(f"  {fam}: {len(sub)} nodes / {sub.ma.nunique()} MAs")

    # ============================================================= SETTING A
    print("\n" + "=" * 74)
    print("(A) AACT-ONLY self-contained field (learned vs within-MA)")
    print("=" * 74)
    dfa = prep(aact.copy())
    ya = dfa["yi"].to_numpy(float)
    mu_a, sd_a = fl.predict_kfold_corpus(dfa, seeds=SEEDS)
    wa = within_ma(dfa)
    delta(np.ones(len(dfa), bool), mu_a, wa, ya, "AACT-only ALL")
    for fam in ["LOR", "LHR"]:
        delta((dfa.family == fam).to_numpy(), mu_a, wa, ya, f"AACT-only {fam}")

    # conformal on AACT-only (calibration = AACT residuals within family)
    cf_a = fl.conformal_intervals(dfa, mu_a, alpha=0.10)
    craw_a, wraw_a = coverage_raw(np.ones(len(dfa), bool), mu_a, sd_a, dfa["se"].to_numpy(), ya)
    print(f"  coverage@90 raw={craw_a:.3f} (w={wraw_a:.3f})  conformal={cf_a['cover']:.3f} (w={cf_a['width']:.3f})")

    # ============================================================= SETTING B
    print("\n" + "=" * 74)
    print("(B) CORPUS + AACT expanded (headline survival + cold-AACT prediction)")
    print("=" * 74)
    base = prep(load_corpus())
    print(f"  base corpus: {len(base)} nodes / {base.ma.nunique()} MAs / families {sorted(base.family.unique())}")
    df = prep(pd.concat([base[["ma", "family", "specialty", "yi", "se", "year"]], aact],
                        ignore_index=True))
    aact_mask = df.ma.astype(str).str.startswith(("aact_", "aacthr_")).to_numpy()
    print(f"  expanded: {len(df)} nodes / {df.ma.nunique()} MAs / families {sorted(df.family.unique())}"
          f" ; AACT rows={aact_mask.sum()}")
    y = df["yi"].to_numpy(float)
    mu, sd = fl.predict_kfold_corpus(df, seeds=SEEDS)
    w = within_ma(df)
    delta(np.ones(len(df), bool), mu, w, y, "expanded ALL (headline)")
    delta(~aact_mask, mu, w, y, "corpus-only rows")
    delta(aact_mask, mu, w, y, "held-out AACT rows")
    for fam in ["LOR", "LHR"]:
        m = aact_mask & (df.family == fam).to_numpy()
        delta(m, mu, w, y, f"AACT {fam} rows")

    # ================================================= TASK 3: CONFORMAL on AACT
    print("\n" + "=" * 74)
    print("(3) Learned-kernel 90% coverage on AACT rows: RAW vs CONFORMAL")
    print("=" * 74)
    se = df["se"].to_numpy(float)
    craw, wraw = coverage_raw(aact_mask, mu, sd, se, y)
    cf = fl.conformal_intervals(df, mu, alpha=0.10)   # per-family; includes AACT residuals
    ccov = float(np.nanmean(cf["covered"][aact_mask]))
    cwid = float(np.nanmean(cf["half"][aact_mask] * 2))
    print(f"  AACT rows (n={int(aact_mask.sum())}):  raw cover={craw:.3f} (width={wraw:.3f})  ->  "
          f"conformal cover={ccov:.3f} (width={cwid:.3f})   [nominal 0.90]")
    for fam in ["LOR", "LHR"]:
        m = aact_mask & (df.family == fam).to_numpy()
        cr, _ = coverage_raw(m, mu, sd, se, y)
        cc = float(np.nanmean(cf["covered"][m]))
        print(f"    {fam}: raw={cr:.3f} -> conformal={cc:.3f} (n={int(m.sum())})")
    print(f"  whole-corpus conformal cover={cf['cover']:.3f} (nominal 0.90)")


if __name__ == "__main__":
    main()
