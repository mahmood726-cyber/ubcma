"""Stand-down (C_ANCHOR) sensitivity: is the m=1 help robust to C, and is there
ANY C that makes the field beat within-MA once >=2 siblings exist? (bounds the field)."""
from __future__ import annotations
import numpy as np
from corpus import load_corpus
from field import prep, _year_kernel
from downsample import cross_block, home_pool

REPS = 25
CS = [1.0, 2.0, 5.0, 10.0, 20.0]


def sweep(m):
    df = prep(load_corpus())
    rng = np.random.default_rng(11)
    cross = {i: cross_block(df, i) for i in range(len(df))}
    home_idx = {ma: df.index[df.ma == ma].values for ma in df.ma.unique()}
    W, F = [], {c: [] for c in CS}
    for i in range(len(df)):
        t = df.iloc[i]
        sibs = np.array([j for j in home_idx[t["ma"]] if j != i])
        if len(sibs) < m:
            continue
        Sc_wy, Sc_w = cross[i]
        for _ in range(REPS):
            pick = rng.choice(sibs, size=m, replace=False)
            Sh_wy, Sh_w = home_pool(df.loc[pick], t)
            if Sh_w <= 0:
                continue
            mu_w = Sh_wy / Sh_w
            W.append(abs(mu_w - t["yi"]))
            for c in CS:
                stand = c / (c + m)
                mu_f = (Sh_wy + stand * Sc_wy) / (Sh_w + stand * Sc_w)
                F[c].append(abs(mu_f - t["yi"]))
    return np.array(W), {c: np.array(F[c]) for c in CS}


def pboot(d, n=5000, seed=3):
    rng = np.random.default_rng(seed)
    bi = rng.integers(0, len(d), size=(n, len(d)))
    md = d[bi].mean(axis=1)
    return d.mean(), *np.quantile(md, [0.025, 0.975])


for m in [1, 2, 3]:
    W, F = sweep(m)
    print(f"\nm_home={m}  (delta = within - field ; >0 => field helps)")
    for c in CS:
        d = W - F[c]
        mean, lo, hi = pboot(d)
        v = "HELPS" if lo > 0 else ("HARMS" if hi < 0 else "inert")
        print(f"  C={c:>5}: within {W.mean():.4f}  field {F[c].mean():.4f}"
              f"  delta {mean:+.4f} [{lo:+.4f},{hi:+.4f}]  {v}")
