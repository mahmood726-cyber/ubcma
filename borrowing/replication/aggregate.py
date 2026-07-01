"""AGGREGATE the per-slice relevance-vs-null advantages into a replication verdict.

Reads loo_results_v2.json (curated slices, each tagged tier=clean/nearmiss/flat).
The slices live on different outcome scales (HbA1c % vs body-weight kg), so a raw
MAE delta is not poolable. We pool the SCALE-FREE fractional MAE reduction:
    frac = (relevance MAE - null MAE) / null MAE      (negative = relevance better)
with SE_frac = SE_raw / null_MAE (raw bootstrap CI half-width / 1.96). Random-
effects (DL) pool across the CLEAN qualifying slices -> overall replicated estimate.
We also tally N-of-M "beats both nulls" per tier and confirm flat slices are inert.
"""
import json, sys, io, numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
Z = 1.959963984540054
res = json.load(open("loo_results_v2.json"))

def se_from_ci(ci):
    return (float(ci[1]) - float(ci[0])) / (2 * Z)

def dl_pool(est, se):
    est = np.asarray(est, float); se = np.asarray(se, float); v = se**2
    if len(est) == 1:
        return float(est[0]), float(se[0]), 0.0, 0.0, 0
    w = 1/v; mu = (w*est).sum()/w.sum()
    Q = float((w*(est-mu)**2).sum()); df = len(est)-1
    c = w.sum() - (w**2).sum()/w.sum(); tau2 = max(0.0,(Q-df)/c) if c>0 else 0.0
    w2 = 1/(v+tau2); return float((w2*est).sum()/w2.sum()), float(np.sqrt(1/w2.sum())), tau2, Q, df

def frac(c, which):
    d = c[f"d_rel_{which}"]; mae_null = c[f"mae_{which}"]
    se = se_from_ci(c[f"ci_rel_{which}"])
    return d/mae_null, se/mae_null

tiers = {}
for lab, r in res.items():
    tiers.setdefault(r.get("tier","?"), []).append((lab, r))

print("="*92)
print("PER-SLICE SUMMARY (central bandwidth = SD)")
print(f"{'slice':40}{'tier':9}{'n':>3}  {'relMAE/uniMAE':>13} {'frac vs unif':>13}{'frac vs scr':>13}  both?")
for lab, r in sorted(res.items()):
    c = r["central"]; fu = frac(c,"uni")[0]; fs = frac(c,"scr")[0]
    print(f"{lab[:40]:40}{r.get('tier','?'):9}{r['n']:>3}  "
          f"{c['mae_rel']/c['mae_uni']:>13.2f} {fu:>+13.1%}{fs:>+13.1%}  "
          f"{'YES' if r['beats_both'] else 'no'}")

print("\n" + "="*92)
print("REPLICATION VERDICT BY TIER")
for tier in ("clean","nearmiss","flat"):
    items = tiers.get(tier, [])
    if not items: continue
    nboth = sum(int(r["beats_both"]) for _, r in items)
    print(f"\n[{tier}]  beats BOTH nulls in {nboth}/{len(items)} slices: "
          + ", ".join(f"{lab.split(':')[0]}{'/'+lab.split(':')[1] if lab.split(':')[1]!='ALL' else ''}"
                      f"({'Y' if r['beats_both'] else 'n'})" for lab,r in items))
    if tier == "flat":
        # inertia check: |fractional advantage| small and CI spans 0 for both nulls
        inert = sum(1 for _,r in items
                    if not r["beats_both"] and abs(frac(r["central"],"uni")[0]) < 0.10)
        print(f"        inert (|frac vs unif|<10% & not a win) in {inert}/{len(items)} "
              f"-- in-data beta=0 negative control")

clean = tiers.get("clean", [])
print("\n" + "="*92)
print(f"POOLED ESTIMATE across CLEAN qualifying slices (N={len(clean)}), scale-free fractional MAE reduction:")
for which, name in [("uni","relevance - uniform (no-relevance null)"), ("scr","relevance - scrambled null")]:
    est = [frac(r["central"], which)[0] for _,r in clean]
    se  = [frac(r["central"], which)[1] for _,r in clean]
    mu, sem, tau2, Q, df = dl_pool(est, se)
    lo, hi = mu - Z*sem, mu + Z*sem
    print(f"  {name:42}: {mu:+.1%} [{lo:+.1%}, {hi:+.1%}]  tau2={tau2:.4f}  "
          f"{'CI<0 ROBUST' if hi < 0 else 'n.s.'}")
nboth_clean = sum(int(r['beats_both']) for _,r in clean)
print(f"\nHEADLINE: relevance beats BOTH nulls in {nboth_clean}/{len(clean)} clean qualifying slices.")
print("  -> " + ("REPLICATED (>=2 independent slices, anchor + new modifier)"
      if nboth_clean >= 2 else "NOT replicated beyond the anchor"))
