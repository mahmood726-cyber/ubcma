"""Registry-scale borrowing FIELD engine + REAL leave-one-out reconstruction.

The field: for a held-out target study t, its borrowing prior is a
relevance-weighted precision pool over OTHER studies. The weight reuses the
validated per-slice machinery (weight = relevance x precision; weighted mean
with within+between variance, exactly as borrowing_transport.transport_prior):

    weight(s -> t) = precision(s)
                   x [family(s)==family(t)]          # a-priori STAND-DOWN (block-diag)
                   x topic(s,t)                       # 1 same-MA / gS same-spec / gF far
                   x year_kernel(s,t)                 # Gaussian gravity, neutral if NaN

Gravity decays with distance: same MA (closest) > same specialty > far
specialty; and with year distance. Cross-family = 0 (scales incomparable).

Predictors of the held-out effect y_t (t's own y REMOVED from every pool):
  global        : family precision-mean, no topic structure      (no-locality floor)
  withinMA_prec : same-MA precision pool                         (classic pooled)
  withinMA_rel  : same-MA, year-kernel x precision               (per-slice relevance)
  field         : whole family, topic x year x precision         (CROSS-MA FIELD)
  field_cross   : field EXCLUDING same MA                        (pure cross-MA signal)
  scrambled     : field with (ma,specialty) labels permuted      (negative control)

All hyper-params are A-PRIORI (not tuned to the outcome).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from corpus import load_corpus

# ---- a-priori field hyper-parameters (NOT tuned) ----
GAMMA_SPEC = 0.50   # related topic, different MA
GAMMA_FAR = 0.15    # same family, distant specialty
BW_YEAR = 1.0       # gravity bandwidth in SD units of standardised year
C_ANCHOR = 5.0      # a-priori STAND-DOWN: "~5 good siblings is enough" -> cross-MA
                    # weight is scaled by C/(C+n_home); rich home => field~within-MA.
Z975 = 1.959963984540054


def prep(df):
    """Standardise year within family; precompute precision."""
    df = df.reset_index(drop=True).copy()
    df["prec"] = 1.0 / np.maximum(df["se"] ** 2, 1e-9)
    df["yz"] = np.nan
    for fam, idx in df.groupby("family").groups.items():
        yr = df.loc[idx, "year"]
        mu, sd = yr.mean(), yr.std()
        if np.isfinite(sd) and sd > 1e-9:
            df.loc[idx, "yz"] = (yr - mu) / sd
    return df


def _pool(y, se, w):
    """Weighted-mean prior with within+between variance (transport_prior form)."""
    wsum = w.sum()
    if wsum <= 0:
        return np.nan, np.inf
    mu = (w * y).sum() / wsum
    within = (w ** 2 * se ** 2).sum() / wsum ** 2
    between = (w * (y - mu) ** 2).sum() / wsum
    return float(mu), float(np.sqrt(max(within + between, 1e-12)))


def _topic(ma_s, spec_s, ma_t, spec_t):
    same_ma = (ma_s == ma_t)
    same_spec = (spec_s == spec_t)
    m = np.where(same_ma, 1.0, np.where(same_spec, GAMMA_SPEC, GAMMA_FAR))
    return m


def _year_kernel(yz_s, yz_t):
    if not np.isfinite(yz_t):
        return np.ones(len(yz_s))
    d = (yz_s - yz_t) / BW_YEAR
    k = np.exp(-0.5 * d ** 2)
    return np.where(np.isfinite(yz_s), k, 1.0)   # neutral when donor year missing


def predict(df, i, mode, ma_perm=None, spec_perm=None):
    """Pure-prior prediction of study i's effect from the others."""
    t = df.iloc[i]
    fam = df["family"].values == t["family"]
    fam[i] = False                                   # leave-one-out
    donors = df[fam]
    if len(donors) == 0:
        return np.nan, np.inf
    y = donors["yi"].values; se = donors["se"].values; prec = donors["prec"].values
    ma = donors["ma"].values; spec = donors["specialty"].values
    if ma_perm is not None:                          # scramble: permuted labels
        ma = ma_perm[donors.index.values]
        spec = spec_perm[donors.index.values]

    if mode == "global":
        w = prec
    elif mode in ("withinMA_prec", "withinMA_rel"):
        same = ma == t["ma"]
        if same.sum() == 0:
            return np.nan, np.inf
        y, se, prec = y[same], se[same], prec[same]
        yzs = donors["yz"].values[same]
        w = prec if mode == "withinMA_prec" else prec * _year_kernel(yzs, t["yz"])
    elif mode == "field_adapt":
        # HOME-ANCHORED field with a-priori stand-down: same-MA donors at full
        # relevance; cross-MA mass scaled by C/(C+n_home) so a rich home MA makes
        # the field defer to within-MA (inert, no harm), a starved home reaches out.
        yzs = donors["yz"].values
        home = ma == t["ma"]
        n_home = int(home.sum())
        topic = _topic(ma, spec, t["ma"], t["specialty"])
        stand = C_ANCHOR / (C_ANCHOR + n_home)
        topic = np.where(home, 1.0, topic * stand)
        w = prec * topic * _year_kernel(yzs, t["yz"])
    else:  # field / field_cross / scrambled
        if mode == "field_cross":
            keep = ma != t["ma"]
            if keep.sum() == 0:
                return np.nan, np.inf
            y, se, prec = y[keep], se[keep], prec[keep]
            ma, spec = ma[keep], spec[keep]
            yzs = donors["yz"].values[keep]
        else:
            yzs = donors["yz"].values
        w = prec * _topic(ma, spec, t["ma"], t["specialty"]) * _year_kernel(yzs, t["yz"])
    return _pool(y, se, w)


MODES = ["global", "withinMA_prec", "withinMA_rel", "field", "field_adapt",
         "field_cross", "scrambled"]


def run_loo(df, seed=1):
    df = prep(df)
    rng = np.random.default_rng(seed)
    # scramble permutation: shuffle (ma,specialty) jointly WITHIN family
    ma_perm = df["ma"].values.copy()
    spec_perm = df["specialty"].values.copy()
    for fam, idx in df.groupby("family").groups.items():
        idx = np.array(idx)
        p = rng.permutation(idx)
        ma_perm[idx] = df["ma"].values[p]
        spec_perm[idx] = df["specialty"].values[p]

    rows = []
    for i in range(len(df)):
        t = df.iloc[i]
        rec = dict(ma=t["ma"], family=t["family"], specialty=t["specialty"],
                   y=t["yi"], se=t["se"], prec=t["prec"])
        for m in MODES:
            perm = (ma_perm, spec_perm) if m == "scrambled" else (None, None)
            mu, sep = predict(df, i, m, ma_perm=perm[0], spec_perm=perm[1])
            rec[f"pred_{m}"] = mu
            rec[f"err_{m}"] = abs(mu - t["yi"]) if np.isfinite(mu) else np.nan
            rec[f"cov_{m}"] = (float(mu - Z975 * np.sqrt(sep ** 2 + t["se"] ** 2) <= t["yi"]
                                     <= mu + Z975 * np.sqrt(sep ** 2 + t["se"] ** 2))
                               if np.isfinite(mu) else np.nan)
        # k = number of same-MA siblings available as donors (sparsity axis)
        rec["k_sibs"] = int((df["ma"].values == t["ma"]).sum() - 1)
        rows.append(rec)
    return pd.DataFrame(rows)


def paired_boot(ea, eb, n=5000, seed=7):
    """mean(ea-eb) with paired bootstrap CI; <0 => first method smaller error."""
    m = np.isfinite(ea) & np.isfinite(eb)
    d = (ea - eb)[m]
    if len(d) < 2:
        return np.nan, np.nan, np.nan, 0
    rng = np.random.default_rng(seed)
    bi = rng.integers(0, len(d), size=(n, len(d)))
    md = d[bi].mean(axis=1)
    lo, hi = np.quantile(md, [0.025, 0.975])
    return float(d.mean()), float(lo), float(hi), int(len(d))


if __name__ == "__main__":
    df = load_corpus()
    res = run_loo(df)
    res.to_csv("loo_perstudy.csv", index=False)
    print(f"scored {len(res)} studies\n")
    print("=== MEAN ABSOLUTE held-out reconstruction error (lower=better) ===")
    hdr = f"{'stratum':26}{'n':>4}" + "".join(f"{m[:9]:>11}" for m in MODES)
    print(hdr)

    def line(label, sub):
        row = f"{label:26}{len(sub):>4}"
        for m in MODES:
            row += f"{sub[f'err_{m}'].mean():>11.4f}"
        print(row)

    line("ALL", res)
    for fam in ["SMD", "COR", "LOR"]:
        line(f"family={fam}", res[res.family == fam])
    print("\n  by sibling sparsity (k_sibs = same-MA donors):")
    line("  k_sibs<=8 (sparse)", res[res.k_sibs <= 8])
    line("  k_sibs 9-40 (mid)", res[(res.k_sibs > 8) & (res.k_sibs <= 40)])
    line("  k_sibs>40 (rich)", res[res.k_sibs > 40])

    print("\n=== KEY CONTRASTS (paired bootstrap, negative = field better) ===")
    def contrast(label, sub, a, b):
        d, lo, hi, n = paired_boot(sub[f"err_{a}"].values, sub[f"err_{b}"].values)
        tag = "  FIELD WINS" if hi < 0 else ("  HARM" if lo > 0 else "  n.s.")
        print(f"  {label:34} {a:>12}-{b:<12} {d:+.4f} [{lo:+.4f},{hi:+.4f}] n={n}{tag}")

    for label, sub in [("ALL", res)] + [(f"fam={f}", res[res.family == f]) for f in ["SMD","COR","LOR"]]:
        contrast(label, sub, "field", "withinMA_rel")
    print("  -- adaptive (home-anchored, stand-down) field --")
    for label, sub in [("ALL", res)] + [(f"fam={f}", res[res.family == f]) for f in ["SMD","COR","LOR"]]:
        contrast(label, sub, "field_adapt", "withinMA_rel")
    print()
    contrast("sparse k<=8: field_adapt vs withinMA", res[res.k_sibs <= 8], "field_adapt", "withinMA_rel")
    contrast("rich k>40: field_adapt vs withinMA", res[res.k_sibs > 40], "field_adapt", "withinMA_rel")
    print()
    contrast("field vs SCRAMBLED (must win)", res, "field", "scrambled")
    contrast("field_adapt vs SCRAMBLED", res, "field_adapt", "scrambled")
    contrast("withinMA_rel vs global", res, "withinMA_rel", "global")

    print("\n=== coverage (95% held-out PI) ===")
    for m in MODES:
        print(f"  {m:16} {res[f'cov_{m}'].mean():.3f}")
