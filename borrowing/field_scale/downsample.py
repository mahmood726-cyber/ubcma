"""Powered SPARSE-REGIME test: does the field fill starved home MAs?

Natural data has few genuinely-sparse studies (only 14 with <=8 siblings), so we
STARVE each home MA on purpose: for target t, keep only m random same-MA siblings
and ask whether reaching into the cross-MA field beats within-MA(m alone).

For each target and each m in {1,2,3,5,10}, over REPS random sibling draws:
  within(m)      : precision x year-kernel pool of the m kept siblings
  field_adapt(m) : m kept siblings (full) + ALL cross-MA donors scaled by C/(C+m)

Paired over (target, rep). If the field helps when starved and fades to inert as
m grows, that is the honest 'gravity fills sparse regions' result; if it stays
inert/harmful even at m=1, that BOUNDS the field on this corpus.
"""
from __future__ import annotations
import numpy as np
from corpus import load_corpus
from field import prep, _topic, _year_kernel, C_ANCHOR

REPS = 25
MS = [1, 2, 3, 5, 10]


def cross_block(df, i):
    """Fixed cross-MA (same-family, different-MA) weighted contribution for target i."""
    t = df.iloc[i]
    fam = (df["family"].values == t["family"]) & (df["ma"].values != t["ma"])
    d = df[fam]
    if len(d) == 0:
        return 0.0, 0.0
    w = (d["prec"].values
         * _topic(d["ma"].values, d["specialty"].values, t["ma"], t["specialty"])
         * _year_kernel(d["yz"].values, t["yz"]))
    return float((w * d["yi"].values).sum()), float(w.sum())


def home_pool(sib, t):
    """within-MA weighted mean of a set of sibling rows."""
    w = sib["prec"].values * _year_kernel(sib["yz"].values, t["yz"])
    return float((w * sib["yi"].values).sum()), float(w.sum())


def run():
    df = prep(load_corpus())
    rng = np.random.default_rng(11)
    # per-target cross contribution (fixed)
    cross = {i: cross_block(df, i) for i in range(len(df))}
    home_idx = {ma: df.index[df.ma == ma].values for ma in df.ma.unique()}

    out = {m: {"win": [], "field": []} for m in MS}
    for i in range(len(df)):
        t = df.iloc[i]
        sibs = np.array([j for j in home_idx[t["ma"]] if j != i])
        Sc_wy, Sc_w = cross[i]
        for m in MS:
            if len(sibs) < m:
                continue
            stand = C_ANCHOR / (C_ANCHOR + m)
            for _ in range(REPS):
                pick = rng.choice(sibs, size=m, replace=False)
                sib = df.loc[pick]
                Sh_wy, Sh_w = home_pool(sib, t)
                if Sh_w <= 0:
                    continue
                mu_w = Sh_wy / Sh_w
                den = Sh_w + stand * Sc_w
                mu_f = (Sh_wy + stand * Sc_wy) / den if den > 0 else mu_w
                out[m]["win"].append(abs(mu_w - t["yi"]))
                out[m]["field"].append(abs(mu_f - t["yi"]))
    return out


def pboot(a, b, n=5000, seed=3):
    a, b = np.array(a), np.array(b)
    d = a - b                 # >0 => field (b) better
    rng = np.random.default_rng(seed)
    bi = rng.integers(0, len(d), size=(n, len(d)))
    md = d[bi].mean(axis=1)
    lo, hi = np.quantile(md, [0.025, 0.975])
    return d.mean(), lo, hi


if __name__ == "__main__":
    out = run()
    print("SPARSE down-sampling: within(m) vs field_adapt(m + cross).  REPS=", REPS)
    print(f"{'m_home':>7}{'n_pairs':>9}{'within':>10}{'field':>10}{'delta(w-f)':>12}{'95% CI':>22}{'verdict':>14}")
    res = {}
    for m in MS:
        w = np.array(out[m]["win"]); f = np.array(out[m]["field"])
        if len(w) == 0:
            continue
        d, lo, hi = pboot(out[m]["win"], out[m]["field"])
        verdict = "FIELD HELPS" if lo > 0 else ("FIELD HARMS" if hi < 0 else "inert")
        print(f"{m:>7}{len(w):>9}{w.mean():>10.4f}{f.mean():>10.4f}{d:>+12.4f}"
              f"   [{lo:+.4f},{hi:+.4f}]{verdict:>14}")
        res[m] = dict(n=len(w), within=float(w.mean()), field=float(f.mean()),
                      delta=float(d), lo=float(lo), hi=float(hi), verdict=verdict)
    import json
    json.dump(res, open("downsample_results.json", "w"), indent=2)
    print("\nwrote downsample_results.json")
