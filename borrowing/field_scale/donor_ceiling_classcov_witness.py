"""INDEPENDENT WITNESS for donor_ceiling_classcov (different model family, zero shared
estimator code). Corroborates the ONE decisive claim: does adding a leakage-free
drug-class match term let arm B (cold_sibling; ma-term does NOT fire) route the held-out
GLP1 level from its same-class donor -- moving the B posterior from the specialty/precision/
year-only value toward the sibling level, whereas a condition-grain term does not?

This engine is a GP-FREE Nadaraya-Watson kernel average (Rosenblatt 1956; Nadaraya 1964),
NOT a Gaussian process. It shares NO code with field_classcov / field_learned's GP. It reuses
only DATA PLUMBING (build_block, split_halves) -- deterministic partitioning, not the estimator
under test -- exactly as the committed donor_ceiling_witness_nw did for the original result.

Predictor for a test row t from a training set with outcomes y_i, se_i:
  w_it = exp(-0.5[(dyr/hyr)^2 + (dlp/hlp)^2]) * rho_sp^[sp mismatch] * rho_ma^[ma mismatch]
         * rho_cl^[cl mismatch] * (1/se_i^2)        (inverse-variance weighted)
  mu_t = sum_i w_it y_i / sum_i w_it
Mismatch penalties rho in (0,1) down-weight (not exclude) a mismatched categorical. Under the
'none' kernel rho_cl is dropped (no class term) -> reproduces the 4-group NW witness behaviour.
Fixed, pre-declared bandwidths/penalties (NOT fit to the outcome -> no tuning leakage).

Run:  python borrowing/field_scale/donor_ceiling_classcov_witness.py
"""
from __future__ import annotations
import sys, json, functools
from pathlib import Path
import numpy as np

print = functools.partial(print, flush=True)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))

from donor_ceiling import build_block, split_halves, SCRAMBLE_SEED  # noqa: E402  data plumbing only
import re

GLP = "aact_diabetesme_glucagon-l"
# fixed, pre-declared hyperparameters (no outcome tuning)
HYR, HLP = 1.0, 1.0            # bandwidths on standardised year / log-precision
RHO_SP, RHO_MA, RHO_CL = 0.30, 0.05, 0.08   # categorical mismatch down-weights

_AACT = re.compile(r"^aact_([^_]+)_(.+)$")


def _base(ma): return ma[:-5] if ma.endswith("__sib") else ma
def cls_of(ma, grain):
    m = _AACT.match(_base(ma))
    if not m: return _base(ma)
    return m.group(2) if grain == "drug" else m.group(1)


def stdz(x):
    x = np.asarray(x, float); s = x.std()
    return (x - x.mean()) / (s + 1e-9) if s > 1e-9 else x * 0.0


def features(blk):
    yr = stdz(blk["year"].fillna(blk["year"].median()).to_numpy())
    prec = 1.0 / blk["se"].to_numpy() ** 2
    lp = stdz(np.log(np.maximum(prec, 1e-12)))
    return yr, lp, blk["specialty"].to_numpy().astype(str), blk["ma"].to_numpy().astype(str)


def nw_predict(blk, tr, te, grain=None):
    """Nadaraya-Watson inverse-variance kernel average; grain in {None,'cond','drug'}."""
    yr, lp, sp, ma = features(blk)
    y = blk["yi"].to_numpy(float); ivw = 1.0 / blk["se"].to_numpy(float) ** 2
    cl = np.array([cls_of(m, grain) for m in ma]) if grain else None
    mu = np.full(len(blk), np.nan)
    for t in te:
        dyr = ((yr[tr] - yr[t]) / HYR) ** 2
        dlp = ((lp[tr] - lp[t]) / HLP) ** 2
        w = np.exp(-0.5 * (dyr + dlp))
        w = w * np.where(sp[tr] != sp[t], RHO_SP, 1.0)
        w = w * np.where(ma[tr] != ma[t], RHO_MA, 1.0)
        if grain:
            w = w * np.where(cl[tr] != cl[t], RHO_CL, 1.0)
        w = w * ivw[tr]
        s = w.sum()
        mu[t] = (w @ y[tr]) / s if s > 0 else np.nan
    return mu


def predict_arm(block, aact_mas, donor, test, mode, grain):
    blk = block.copy()
    if mode in ("B_sibling", "D_scrambled"):
        for m in aact_mas:
            blk.loc[donor[m], "ma"] = m + "__sib"
    if mode == "D_scrambled":
        d_all = np.concatenate([donor[m] for m in aact_mas])
        rng = np.random.default_rng(SCRAMBLE_SEED)
        blk.loc[d_all, "yi"] = block["yi"].to_numpy()[d_all][rng.permutation(len(d_all))]
    ma_now = blk["ma"].to_numpy(); n = len(blk)
    mu = np.full(n, np.nan)
    for m in aact_mas:
        te = test[m]
        if mode == "A_nodonor":
            tr = np.where((ma_now != m) & (ma_now != m + "__sib"))[0]
        elif mode == "C_warm":
            tr = np.setdiff1d(np.arange(n), te)
        else:
            tr = np.where(ma_now != m)[0]
        mm = nw_predict(blk, tr, te, grain)
        mu[te] = mm[te]
    return mu


def main():
    block, aact_mas = build_block()
    y = block["yi"].to_numpy(float)
    donor, test = split_halves(block, aact_mas)
    tglp = test[GLP]; yg = y[tglp]
    print(f"WITNESS (Nadaraya-Watson, GP-free). GLP1 test-half n={len(tglp)} true level={yg.mean():+.2f}")
    print(f"{'kernel':6} {'A_post':>8} {'B_post':>8} {'C_post':>8} {'D_post':>8}   "
          f"(B recovers toward true {yg.mean():+.2f}?)")
    out = {}
    for grain, name in [(None, "none"), ("cond", "cond"), ("drug", "drug")]:
        posts = {}
        for mode in ("A_nodonor", "B_sibling", "C_warm", "D_scrambled"):
            mu = predict_arm(block, aact_mas, donor, test, mode, grain)
            posts[mode] = float(mu[tglp].mean())
        out[name] = posts
        print(f"{name:6} {posts['A_nodonor']:+8.2f} {posts['B_sibling']:+8.2f} "
              f"{posts['C_warm']:+8.2f} {posts['D_scrambled']:+8.2f}")
    # decisive: does drug-grain move B toward the sibling level vs none / cond?
    print(f"\n  GLP1 B posterior: none={out['none']['B_sibling']:+.2f}  "
          f"cond={out['cond']['B_sibling']:+.2f}  drug={out['drug']['B_sibling']:+.2f}  "
          f"(true {yg.mean():+.2f})")
    print(f"  scrambled(D) drug={out['drug']['D_scrambled']:+.2f} must NOT approach true "
          f"(negative-control guard)")
    json.dump(out, open(HERE / "donor_ceiling_classcov_witness.json", "w"), indent=2)
    print(f"  wrote {HERE / 'donor_ceiling_classcov_witness.json'}")


if __name__ == "__main__":
    main()
