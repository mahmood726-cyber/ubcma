"""Extend the multi-specialty relevance pool with a NEW clean strong-modifier slice:
bangertdrowns2004 (writing-to-learn -> academic achievement), modifier = MINUTES of
writing per assignment. Bangert-Drowns, Hurley & Wilkinson 2004, Rev Educ Res 74(1):29-58.
The documented finding: brief writing tasks help more; the effect SHRINKS as minutes rise
(slope -0.020, R2=0.466, perm p=0.0008 -- a genuinely STRONG within-set modifier, far
stronger than the near-inert kalaian). A 3rd independent Education slice (not a new
specialty, but the strongest-modifier education slice).

Builds the slice, runs the 5-way real-LOO (relevance kernel x precision vs uniform/
scrambled nulls + REML-NMA; TRUTH = real held-out d) with the SAME from-scratch machinery
used for the transport aggregation, computes the scale-free fractional MAE reduction, and
RE-POOLS (DL random-effects) the cross-specialty estimate with this slice added.
"""
import csv, json, sys
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agg"))
from aggregate_transport import loo_errs  # generic 5-way LOO (relevance = kernel, no shift); sets utf-8 stdout

REP = Path(__file__).resolve().parent
MET = Path(r"F:\public-data\metadat")
Z = 1.959963984540054


def build_bangertdrowns():
    trials = []
    for r in csv.DictReader(open(MET / "dat.bangertdrowns2004.csv")):
        try:
            yi = float(r["yi"]); vi = float(r["vi"]); mn = float(r["minutes"])
        except (ValueError, KeyError):
            continue
        if vi <= 0:
            continue
        trials.append(dict(y=yi, se=float(np.sqrt(vi)), minutes=mn))
    return trials


def pboot(ea, eb, n=4000, seed=7):
    rng = np.random.default_rng(seed); d = ea - eb
    md = d[rng.integers(0, len(d), size=(n, len(d)))].mean(axis=1)
    return float(d.mean()), float(np.quantile(md, .025)), float(np.quantile(md, .975))


def slice_entry(trials, cov):
    x = np.array([t[cov] for t in trials]); bw = float(x.std())
    e = {m: loo_errs(trials, cov, bw, m) for m in ["nma", "uniform", "relevance", "scrambled"]}
    e = {m: v[np.isfinite(v)] for m, v in e.items()}
    out = {"mae_rel": float(e["relevance"].mean()), "mae_uni": float(e["uniform"].mean()),
           "mae_scr": float(e["scrambled"].mean()), "mae_nma": float(e["nma"].mean())}
    for nm, other in [("uni", "uniform"), ("scr", "scrambled"), ("nma", "nma")]:
        d, lo, hi = pboot(e["relevance"], e[other])
        out[f"d_rel_{nm}"] = d; out[f"ci_rel_{nm}"] = [lo, hi]
    return out


def frac(c, which):
    se = (c[f"ci_rel_{which}"][1] - c[f"ci_rel_{which}"][0]) / (2 * Z)
    return c[f"d_rel_{which}"] / c[f"mae_{which}"], se / c[f"mae_{which}"]


def dl_pool(est, se):
    est = np.asarray(est, float); v = np.asarray(se, float) ** 2
    if len(est) == 1:
        return float(est[0]), float(np.sqrt(v[0])), 0.0
    w = 1 / v; mu = (w * est).sum() / w.sum()
    Q = float((w * (est - mu) ** 2).sum()); df = len(est) - 1
    c = w.sum() - (w ** 2).sum() / w.sum(); tau2 = max(0.0, (Q - df) / c) if c > 0 else 0.0
    w2 = 1 / (v + tau2)
    return float((w2 * est).sum() / w2.sum()), float(np.sqrt(1 / w2.sum())), tau2


def main():
    # existing clean qualifiers (5): GLP1 x2 + raudenbush + ursino (+ kalaian weak)
    GLP1 = ["T2DM_HbA1c_GLP1only:ALL:dose", "Obesity_weight:ALL:baseline"]
    prior = json.load(open(REP / "loo_results_v2.json"))
    multi = json.load(open(REP / "multispecialty_loo.json"))
    slices = {k: prior[k] for k in GLP1}; slices.update(multi)
    clean = {k: v for k, v in slices.items() if v["tier"] == "clean"}

    # new slice
    tr = build_bangertdrowns()
    c_new = slice_entry(tr, "minutes")
    print(f"bangertdrowns2004 minutes slice: n={len(tr)}")
    print(f"  MAE rel={c_new['mae_rel']:.3f} uni={c_new['mae_uni']:.3f} "
          f"scr={c_new['mae_scr']:.3f} nma={c_new['mae_nma']:.3f}")
    for nm in ["uni", "scr"]:
        f, se = frac(c_new, nm)
        print(f"  relevance vs {nm}: frac {f:+.1%}  (d_rel {c_new['d_rel_'+nm]:+.3f} "
              f"CI[{c_new['ci_rel_'+nm][0]:+.3f},{c_new['ci_rel_'+nm][1]:+.3f}]) "
              f"{'W' if c_new['ci_rel_'+nm][1] < 0 else ''}")

    for which, name in [("uni", "relevance - uniform (no-relevance null)"),
                        ("scr", "relevance - scrambled null")]:
        old_est = [frac(v["central"], which)[0] for v in clean.values()]
        old_se = [frac(v["central"], which)[1] for v in clean.values()]
        mu0, s0, t0 = dl_pool(old_est, old_se)
        est = old_est + [frac(c_new, which)[0]]; se = old_se + [frac(c_new, which)[1]]
        mu1, s1, t1 = dl_pool(est, se)
        print(f"\n{name}")
        print(f"  BEFORE (5 clean): {mu0:+.1%} [{mu0-Z*s0:+.1%}, {mu0+Z*s0:+.1%}] tau2={t0:.4f}")
        print(f"  AFTER  (6 clean): {mu1:+.1%} [{mu1-Z*s1:+.1%}, {mu1+Z*s1:+.1%}] tau2={t1:.4f}"
              f"  {'ROBUST CI<0' if mu1+Z*s1 < 0 else 'crosses 0'}")

    json.dump(dict(n=len(tr), central=c_new,
                   verify=dict(slope=-0.0201, R2=0.466, perm_p=0.0008)),
              open(REP / "bangertdrowns_entry.json", "w"), indent=1)
    print("\nwrote bangertdrowns_entry.json")


if __name__ == "__main__":
    main()
