"""Registry-scale borrowing FIELD -- corpus harmoniser.

Load every usable metadat CSV staged on disk and harmonise each meta-analysis
(MA) into a set of study NODES on a common per-family scale:

  family 'SMD'  : Hedges g (standardised mean difference)   -> vi
  family 'COR'  : Fisher z (correlation)                     -> vi = 1/(n-3)
  family 'LOR'  : log odds ratio (2x2 / response counts)     -> vi = sum 1/cell

Each node carries: ma (meta-analysis id), family, specialty (topic cluster),
yi (effect on family scale), se, year (continuous covariate, may be NaN).

NOTHING here uses the effect to build the borrowing distance -- only ma,
family, specialty, year. yi is the RECONSTRUCTION TARGET only.

Cross-family borrowing is a-priori stood down (weight 0): the scales are not
comparable, so the field is BLOCK-DIAGONAL by family -- which is also the
tractability story at N ~ thousands (block-sparse kernel).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from pathlib import Path

RAW = Path(r"F:\public-data\metadat")

# specialty (topic) tag per MA -- for related-topic relevance WITHIN a family.
SPECIALTY = {
    # SMD
    "assink2016": "psych_criminology",
    "kalaian1996": "education",
    "konstantopoulos2011": "education",
    "raudenbush1985": "education",
    "bangertdrowns2004": "education",
    "tannersmith2016": "clinical_behavioral",
    "gibson2002": "clinical_medicine",
    "normand1999": "clinical_medicine",
    "senn2013": "clinical_medicine",
    # COR
    "crede2010": "education",
    "molloy2014": "health_psych",
    "mcdaniel1994": "io_psych",
    "aloe2013": "education",
    # LOR
    "bcg": "infectious_disease",
    "li2007": "clinical_medicine",
    "linde2015": "psychiatry",
}


def _g_from_means(n1, m1, sd1, n2, m2, sd2):
    """Hedges g and its variance from two-arm means."""
    n1, m1, sd1, n2, m2, sd2 = map(np.asarray, (n1, m1, sd1, n2, m2, sd2))
    sp = np.sqrt(((n1 - 1) * sd1 ** 2 + (n2 - 1) * sd2 ** 2) / (n1 + n2 - 2))
    d = (m1 - m2) / sp
    J = 1.0 - 3.0 / (4 * (n1 + n2) - 9)
    g = J * d
    vg = (n1 + n2) / (n1 * n2) + g ** 2 / (2 * (n1 + n2))
    return g, vg


def _z_from_r(r, n):
    r = np.clip(np.asarray(r, float), -0.9999, 0.9999)
    n = np.asarray(n, float)
    z = np.arctanh(r)
    vz = 1.0 / np.maximum(n - 3, 1.0)
    return z, vz


def _lor_2x2(a, b, c, d):
    """log OR + var from cells a/b (arm1 event/non), c/d (arm2)."""
    a, b, c, d = (np.asarray(x, float) for x in (a, b, c, d))
    zero = (a == 0) | (b == 0) | (c == 0) | (d == 0)
    a = a + 0.5 * zero; b = b + 0.5 * zero
    c = c + 0.5 * zero; d = d + 0.5 * zero
    lor = np.log((a * d) / (b * c))
    v = 1 / a + 1 / b + 1 / c + 1 / d
    return lor, v


def _node(ma, family, yi, vi, year=np.nan):
    return dict(ma=ma, family=family, specialty=SPECIALTY[ma],
                yi=float(yi), se=float(np.sqrt(vi)), year=float(year))


def load_corpus(include_new=True):
    """Harmonise the metadat corpus into study nodes.

    include_new=True appends `corpus_nodes_new.csv` (14 additional real MAs
    harmonised via metafor::escalc in R -- 12 raw-2x2 -> log-OR and 2 raw
    correlations -> Fisher-z; see harmonize_new.R). This expands the LOR family
    from 3 to 15 meta-analyses (56 -> 409 nodes), the strongest test of whether
    the learned-kernel win holds as registry coverage grows.
    """
    nodes = []

    def add_precomputed(ma, family, yr_col=None):
        df = pd.read_csv(RAW / f"dat.{ma}.csv")
        for _, r in df.iterrows():
            if not np.isfinite(r["yi"]) or not np.isfinite(r["vi"]) or r["vi"] <= 0:
                continue
            yr = r[yr_col] if yr_col and yr_col in df.columns else np.nan
            nodes.append(_node(ma, family, r["yi"], r["vi"], yr))

    # --- SMD family: already-escalc sets ---
    add_precomputed("assink2016", "SMD", "year")
    add_precomputed("kalaian1996", "SMD", "year")
    add_precomputed("konstantopoulos2011", "SMD", "year")
    add_precomputed("raudenbush1985", "SMD", "year")
    add_precomputed("bangertdrowns2004", "SMD", "year")
    add_precomputed("tannersmith2016", "SMD")  # no year col

    # --- SMD family: from arm means ---
    for ma, yr in [("normand1999", None), ("gibson2002", "year")]:
        df = pd.read_csv(RAW / f"dat.{ma}.csv")
        g, vg = _g_from_means(df.n1i, df.m1i, df.sd1i, df.n2i, df.m2i, df.sd2i)
        for i in range(len(df)):
            if np.isfinite(g[i]) and np.isfinite(vg[i]) and vg[i] > 0:
                year = df[yr].iloc[i] if yr else np.nan
                nodes.append(_node(ma, "SMD", g[i], vg[i], year))

    # senn2013: multi-arm HbA1c; pair each active arm vs placebo within study
    df = pd.read_csv(RAW / "dat.senn2013.csv")
    for study, grp in df.groupby("study"):
        pl = grp[grp.treatment == "placebo"]
        if len(pl) == 0:
            continue
        p = pl.iloc[0]
        for _, a in grp[grp.treatment != "placebo"].iterrows():
            g, vg = _g_from_means(a.ni, a.mi, a.sdi, p.ni, p.mi, p.sdi)
            if np.isfinite(g) and np.isfinite(vg) and vg > 0:
                nodes.append(_node("senn2013", "SMD", g, vg, np.nan))

    # --- COR family (Fisher z) ---
    for ma in ["crede2010", "molloy2014"]:
        df = pd.read_csv(RAW / f"dat.{ma}.csv")
        z, vz = _z_from_r(df.ri, df.ni)
        yr = df.year if "year" in df.columns else [np.nan] * len(df)
        for i in range(len(df)):
            if np.isfinite(z[i]) and np.isfinite(vz[i]):
                nodes.append(_node(ma, "COR", z[i], vz[i], list(yr)[i]))

    df = pd.read_csv(RAW / "dat.mcdaniel1994.csv")   # ni, ri
    z, vz = _z_from_r(df.ri, df.ni)
    for i in range(len(df)):
        if np.isfinite(z[i]) and np.isfinite(vz[i]):
            nodes.append(_node("mcdaniel1994", "COR", z[i], vz[i], np.nan))

    df = pd.read_csv(RAW / "dat.aloe2013.csv")        # partial r from t
    dfree = df.n - df.preds - 1
    r = df.tval / np.sqrt(df.tval ** 2 + dfree)
    z = np.arctanh(np.clip(r, -0.9999, 0.9999))
    vz = 1.0 / np.maximum(df.n - df.preds - 3, 1.0)
    for i in range(len(df)):
        if np.isfinite(z[i]) and np.isfinite(vz[i]):
            nodes.append(_node("aloe2013", "COR", z[i], vz[i], np.nan))

    # --- LOR family (log odds ratio) ---
    df = pd.read_csv(RAW / "dat.bcg.csv")   # tpos,tneg,cpos,cneg
    lor, v = _lor_2x2(df.tpos, df.tneg, df.cpos, df.cneg)
    for i in range(len(df)):
        nodes.append(_node("bcg", "LOR", lor[i], v[i], df.year.iloc[i]))

    df = pd.read_csv(RAW / "dat.li2007.csv")  # ai,n1i,ci,n2i (events/total each arm)
    lor, v = _lor_2x2(df.ai, df.n1i - df.ai, df.ci, df.n2i - df.ci)
    for i in range(len(df)):
        if np.isfinite(lor[i]) and np.isfinite(v[i]):
            yr = df.year.iloc[i] if "year" in df.columns else np.nan
            nodes.append(_node("li2007", "LOR", lor[i], v[i], yr))

    # linde2015: network -> active-vs-placebo logOR per trial with a placebo arm
    df = pd.read_csv(RAW / "dat.linde2015.csv")
    for _, r in df.iterrows():
        arms = []
        for k in (1, 2, 3):
            t = r.get(f"treatment{k}")
            n = r.get(f"n{k}"); resp = r.get(f"resp{k}")
            if isinstance(t, str) and np.isfinite(n) and np.isfinite(resp):
                arms.append((t, float(n), float(resp)))
        pl = [x for x in arms if x[0] == "Placebo"]
        act = [x for x in arms if x[0] != "Placebo"]
        if not pl or not act:
            continue
        _, npl, rpl = pl[0]
        _, nac, rac = act[0]           # first active arm vs placebo
        lor, v = _lor_2x2(rac, nac - rac, rpl, npl - rpl)
        if np.isfinite(lor) and np.isfinite(v):
            nodes.append(_node("linde2015", "LOR", lor, v, r.get("year", np.nan)))

    df = pd.DataFrame(nodes)
    if include_new:
        newf = Path(__file__).resolve().parent / "corpus_nodes_new.csv"
        if newf.exists():
            extra = pd.read_csv(newf)[["ma", "family", "specialty", "yi", "se", "year"]]
            df = pd.concat([df, extra], ignore_index=True)
    return df


if __name__ == "__main__":
    df = load_corpus()
    print(f"TOTAL nodes: {len(df)}  |  MAs: {df.ma.nunique()}  |  families: {sorted(df.family.unique())}")
    print("\nper-MA summary:")
    g = df.groupby(["family", "specialty", "ma"]).agg(
        k=("yi", "size"), ybar=("yi", "mean"), se_med=("se", "median")).round(3)
    print(g.to_string())
    print("\nper-family node counts:")
    print(df.family.value_counts().to_string())
