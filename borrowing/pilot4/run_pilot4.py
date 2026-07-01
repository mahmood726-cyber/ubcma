"""PILOT-4 headline 5-way: does TRANSPORTABILITY beat relevance-only on the
best-available REAL placebo-anchored slice (MADRS antidepressant-vs-placebo),
with the best-available candidate population modifier (WB under-5 mortality)?

Same pre-registered design as pilot-3 (carry-overs unchanged):
  nma / relevance / transport(=relevance x pop-kernel x precision, standardised)
  / scrambled, paired bootstrap, regime split (target FAR vs NEAR donor pool),
  two standing negative controls (target=pool, beta=0), matched coverage.

Targets = every trial held out in turn (zero own data -> pure transportability
prediction of the real held-out y_t). Reported overall + by regime + single-country.
"""
from __future__ import annotations
import json, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # ../ has borrowing_transport
from borrowing_transport import (transport_prior, within_class_obslope, Z975)

R = [r for r in json.load(open("dep_madrs_transport.json")) if r["pop_ob"] is not None]
OB = np.array([r["pop_ob"] for r in R]); OB_SD = float(OB.std()); OB_MED = float(np.median(OB))
BASE_SD = float(np.nanstd([r["baseline"] for r in R if r["baseline"] is not None]))
print(f"n={len(R)} MADRS trials | under-5-mort: median {OB_MED:.1f} SD {OB_SD:.2f} | baseline-sev SD {BASE_SD:.2f}\n")

def predict(target, mode, bw_ob, beta_ob, override_ob=None, rng=None):
    donors = [d for d in R if d["nct_id"] != target["nct_id"]]
    tgt = dict(target)
    if override_ob is not None: tgt["pop_ob"] = override_ob
    mu_p, se_p, ess = transport_prior(tgt, donors, bw_ob, mode=mode,
                                      bw_base=BASE_SD, beta_ob=beta_ob, rng=rng)
    return mu_p, se_p

def run(mode, bw_ob, override_ob_to_mean=False, beta_zero=False, seed=1):
    errs, cov, regime, sc = [], [], [], []
    rng = np.random.default_rng(seed)
    for t in R:
        donors = [d for d in R if d["nct_id"] != t["nct_id"]]
        beta_ob = 0.0 if beta_zero else within_class_obslope(donors, None)
        ob_over = OB_MED if override_ob_to_mean else None
        mu_p, se_p = predict(t, mode, bw_ob, beta_ob, override_ob=ob_over, rng=rng)
        if not np.isfinite(mu_p): continue
        errs.append(abs(mu_p - t["y"]))
        half = Z975 * np.sqrt(se_p**2 + t["se"]**2)
        cov.append(float(mu_p - half <= t["y"] <= mu_p + half))
        regime.append("far" if abs(t["pop_ob"] - OB_MED) > OB_SD else "near")
        sc.append(t["single_country"])
    return np.array(errs), np.array(cov), np.array(regime), np.array(sc)

def paired_boot(ea, eb, n=5000, seed=7):
    rng = np.random.default_rng(seed); d = ea - eb
    if len(d) == 0: return 0.0, 0.0, 0.0, False
    bi = rng.integers(0, len(d), size=(n, len(d))); md = d[bi].mean(axis=1)
    lo, hi = np.quantile(md, [0.025, 0.975])
    return float(d.mean()), float(lo), float(hi), bool(hi < 0)

bw = OB_SD
res = {m: run(m, bw) for m in ["nma", "relevance", "transport", "scrambled"]}
errs0, _, regime, sc = res["nma"]
masks = {"ALL": np.ones(len(regime), bool),
         "FAR (mort-distant target)": regime == "far",
         "NEAR (mort-central target)": regime == "near",
         "single-country targets": sc.astype(bool)}

print("=== REAL LOO: mean abs error (pure-prior prediction of real y_t, MADRS pts) ===")
print(f"{'regime':28}{'n':>3}{'nma':>8}{'releva':>8}{'transp':>8}{'scram':>8}")
for label, m in masks.items():
    n = int(m.sum())
    if n == 0: continue
    row = f"{label:28}{n:>3}"
    for mth in ["nma", "relevance", "transport", "scrambled"]:
        row += f"{res[mth][0][m].mean():>8.3f}"
    print(row)

print("\n=== KEY CONTRAST: transport vs relevance-only and vs nulls (paired bootstrap) ===")
summary = {}
for label, m in masks.items():
    n = int(m.sum())
    if n < 3: print(f"{label}: n={n} too few"); continue
    et, er, en, es = (res["transport"][0][m], res["relevance"][0][m],
                      res["nma"][0][m], res["scrambled"][0][m])
    d_tr = paired_boot(et, er); d_tn = paired_boot(et, en)
    d_ts = paired_boot(et, es); d_rn = paired_boot(er, en)
    print(f"\n{label} (n={n}):")
    print(f"  transport - relevance = {d_tr[0]:+.3f} [{d_tr[1]:+.3f},{d_tr[2]:+.3f}]"
          f"{'  *** TRANSPORT WINS' if d_tr[3] else '   (n.s.)'}")
    print(f"  transport - nma       = {d_tn[0]:+.3f} [{d_tn[1]:+.3f},{d_tn[2]:+.3f}]{'  WIN' if d_tn[3] else '   n.s.'}")
    print(f"  transport - scrambled = {d_ts[0]:+.3f} [{d_ts[1]:+.3f},{d_ts[2]:+.3f}]{'  WIN' if d_ts[3] else '   n.s.'}")
    print(f"  relevance - nma       = {d_rn[0]:+.3f} [{d_rn[1]:+.3f},{d_rn[2]:+.3f}]{'  WIN' if d_rn[3] else '   n.s.'}")
    summary[label] = dict(n=n, transport_vs_relevance=d_tr, transport_vs_nma=d_tn,
                          transport_vs_scrambled=d_ts, relevance_vs_nma=d_rn)

print("\n=== NEG CONTROL 1: target population = donor pool (ob_t := median) -> must be INERT ===")
et_ctrl = run("transport", bw, override_ob_to_mean=True)[0]
d = paired_boot(et_ctrl, res["relevance"][0])
print(f"  transport(ob_t=median) - relevance = {d[0]:+.3f} [{d[1]:+.3f},{d[2]:+.3f}]  "
      f"{'INERT (good)' if not (d[2] < 0 or d[1] > 0) else 'NOT INERT'}")
summary["control_target_eq_pool"] = d

print("\n=== NEG CONTROL 2: beta_ob = 0 (no standardisation) ===")
et_b0 = run("transport", bw, beta_zero=True)[0]
d = paired_boot(et_b0, res["relevance"][0])
print(f"  transport(beta=0) - relevance = {d[0]:+.3f} [{d[1]:+.3f},{d[2]:+.3f}]")
summary["control_beta0"] = d

print("\n=== coverage (95% PI of real y_t) ===")
for mth in ["nma", "relevance", "transport", "scrambled"]:
    print(f"  {mth:10} {res[mth][1].mean():.2f}")
    summary.setdefault("coverage", {})[mth] = float(res[mth][1].mean())

json.dump(dict(n=len(R), ob_sd=OB_SD, ob_median=OB_MED, summary=summary),
          open("pilot4_loo_summary.json", "w"), indent=2, default=str)
print("\nwrote pilot4_loo_summary.json")
