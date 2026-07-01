"""PILOT-3 headline: REAL leave-one-trial-out on single-country targets.

For each held-out single-country trial t (the TARGET population; ZERO own data ->
a pure transportability prediction), build a borrowing prior from all OTHER trials
five ways and score |pred - y_t| against the REAL held-out effect, with paired
bootstrap. Split by regime (target FAR vs NEAR the donor pool on obesity) and run
the two new negative controls.

Methods:
  nma        : standard pooled (precision only)
  relevance  : class+baseline relevance x precision      (pilot-2 winner; no pop data)
  transport  : relevance x obesity-kernel x precision, donors standardised (THESIS)
  uniform    : precision only = no-relevance null            (== nma here; kept explicit)
  scrambled  : transport with obesity permuted               (standing null)

BINDING: transport must beat relevance AND nulls when target is FAR on obesity,
be inert when target = donor populations (new control) and when beta_ob = 0.
"""
from __future__ import annotations
import json
import numpy as np
from borrowing_transport import (transport_prior, within_class_obslope, Z975)

R = [r for r in json.load(open("trials_transport.json")) if r["pop_ob"] is not None]
TARGETS = [r for r in R if r["single_country"]]
DONOR_OB = np.array([r["pop_ob"] for r in R])
OB_SD = float(DONOR_OB.std())
OB_MED = float(np.median(DONOR_OB))
BASE_SD = float(np.nanstd([r["baseline"] for r in R if r["baseline"] is not None]))

print(f"donor obesity: median {OB_MED:.1f}%  SD {OB_SD:.1f}  | baseline SD {BASE_SD:.2f}")
print(f"{len(TARGETS)} single-country targets; bw_ob = OB_SD = {OB_SD:.1f}\n")


def predict(target, mode, bw_ob, beta_ob, override_ob=None, rng=None):
    donors = [d for d in R if d["nct_id"] != target["nct_id"]]
    tgt = dict(target)
    if override_ob is not None:
        tgt = dict(target); tgt["pop_ob"] = override_ob
    mu_p, se_p, ess = transport_prior(tgt, donors, bw_ob, mode=mode,
                                       bw_base=BASE_SD, beta_ob=beta_ob, rng=rng)
    return mu_p, se_p


def run(mode, bw_ob, override_ob_to_mean=False, beta_zero=False, seed=1):
    """Return per-target abs error + coverage arrays over all targets."""
    errs, cov, regime = [], [], []
    rng = np.random.default_rng(seed)
    for t in TARGETS:
        donors = [d for d in R if d["nct_id"] != t["nct_id"]]
        beta_ob = 0.0 if beta_zero else within_class_obslope(donors, None)
        ob_over = OB_MED if override_ob_to_mean else None
        mu_p, se_p = predict(t, mode, bw_ob, beta_ob, override_ob=ob_over, rng=rng)
        if not np.isfinite(mu_p):
            continue
        errs.append(abs(mu_p - t["y"]))
        half = Z975 * np.sqrt(se_p ** 2 + t["se"] ** 2)
        cov.append(float(mu_p - half <= t["y"] <= mu_p + half))
        regime.append("far" if abs(t["pop_ob"] - OB_MED) > OB_SD else "near")
    return np.array(errs), np.array(cov), np.array(regime)


def paired_boot(ea, eb, n=5000, seed=7):
    rng = np.random.default_rng(seed)
    d = ea - eb                       # want < 0 : first method smaller error
    if len(d) == 0:
        return 0.0, 0.0, 0.0, False
    bi = rng.integers(0, len(d), size=(n, len(d)))
    md = d[bi].mean(axis=1)
    lo, hi = np.quantile(md, [0.025, 0.975])
    return float(d.mean()), float(lo), float(hi), bool(hi < 0)


# ---- main comparison, by regime ----
bw = OB_SD
res = {m: run(m, bw) for m in ["nma", "relevance", "transport", "scrambled"]}
errs0, _, regime = res["nma"]
masks = {"ALL": np.ones(len(regime), bool),
         "FAR (Asian targets)": regime == "far",
         "NEAR (US targets)": regime == "near"}

print("=== REAL LOO: mean abs error by regime (pure-prior prediction of real y_t) ===")
hdr = f"{'regime':22}{'n':>3}{'nma':>7}{'releva':>8}{'transp':>8}{'scram':>7}"
print(hdr)
summary = {}
for label, m in masks.items():
    n = int(m.sum())
    if n == 0:
        continue
    row = f"{label:22}{n:>3}"
    for mth in ["nma", "relevance", "transport", "scrambled"]:
        row += f"{res[mth][0][m].mean():>8.3f}" if mth != "nma" else f"{res[mth][0][m].mean():>7.3f}"
    print(row)

print("\n=== KEY CONTRAST: transport vs relevance-only, and vs nulls (paired bootstrap) ===")
for label, m in masks.items():
    n = int(m.sum())
    if n < 2:
        print(f"{label}: n={n} too few for bootstrap"); continue
    et, er, en, es = (res["transport"][0][m], res["relevance"][0][m],
                      res["nma"][0][m], res["scrambled"][0][m])
    d_tr, lo_tr, hi_tr, win_tr = paired_boot(et, er)     # transport vs relevance
    d_tn, lo_tn, hi_tn, win_tn = paired_boot(et, en)     # transport vs nma
    d_ts, lo_ts, hi_ts, win_ts = paired_boot(et, es)     # transport vs scrambled
    d_rn, lo_rn, hi_rn, win_rn = paired_boot(er, en)     # relevance vs nma
    print(f"\n{label} (n={n}):")
    print(f"  transport - relevance = {d_tr:+.3f} [{lo_tr:+.3f},{hi_tr:+.3f}]"
          f"{'  *** TRANSPORT WINS' if win_tr else '   (n.s.)'}")
    print(f"  transport - nma       = {d_tn:+.3f} [{lo_tn:+.3f},{hi_tn:+.3f}]{'  WIN' if win_tn else '   n.s.'}")
    print(f"  transport - scrambled = {d_ts:+.3f} [{lo_ts:+.3f},{hi_ts:+.3f}]{'  WIN' if win_ts else '   n.s.'}")
    print(f"  relevance - nma       = {d_rn:+.3f} [{lo_rn:+.3f},{hi_rn:+.3f}]{'  WIN' if win_rn else '   n.s.'}")
    summary[label] = dict(n=n, transport_vs_relevance=[d_tr, lo_tr, hi_tr, win_tr],
                          transport_vs_nma=[d_tn, lo_tn, hi_tn, win_tn],
                          transport_vs_scrambled=[d_ts, lo_ts, hi_ts, win_ts],
                          relevance_vs_nma=[d_rn, lo_rn, hi_rn, win_rn])

# ---- NEGATIVE CONTROL 1 (new): target obesity = donor-pool mean -> transport must be inert ----
print("\n=== NEG CONTROL 1 (NEW): target population = donor pool (ob_t := median) ===")
et_ctrl, _, _ = run("transport", bw, override_ob_to_mean=True)
er_all = res["relevance"][0]
d, lo, hi, _ = paired_boot(et_ctrl, er_all)
print(f"  transport(ob_t=median) - relevance = {d:+.3f} [{lo:+.3f},{hi:+.3f}]  "
      f"{'INERT (good)' if not (hi < 0 or lo > 0) else 'NOT INERT (bad)'}")
summary["control_target_eq_pool"] = [d, lo, hi]

# ---- NEGATIVE CONTROL 2: beta_ob = 0 (standardisation off) ----
print("\n=== NEG CONTROL 2 (carry-over): beta_ob = 0 (no standardisation) ===")
et_b0, _, reg_b0 = run("transport", bw, beta_zero=True)
mfar = reg_b0 == "far"
d, lo, hi, _ = paired_boot(et_b0[mfar], res["relevance"][0][mfar])
print(f"  transport(beta=0) - relevance [FAR] = {d:+.3f} [{lo:+.3f},{hi:+.3f}]  "
      f"(down-weight half only)")
summary["control_beta0_far"] = [d, lo, hi]

# coverage
print("\n=== coverage (95% PI of real y_t) ===")
for mth in ["nma", "relevance", "transport", "scrambled"]:
    print(f"  {mth:10} {res[mth][1].mean():.2f}")

json.dump(dict(ob_sd=OB_SD, ob_median=OB_MED, n_targets=len(TARGETS),
               by_regime=summary), open("pilot3_loo_summary.json", "w"), indent=2)
print("\nwrote pilot3_loo_summary.json")
