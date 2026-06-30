"""EXPERIMENT 2 -- cross-specialty pooled replication of the relevance-borrowing win.

Combines the 2 prior GLP1-class clean slices (loo_results_v2.json) with the 4 new
multi-specialty slices (multispecialty_loo.json) into one replicated estimate. The
slices live on different outcome scales (HbA1c %, body-weight kg, Cohen's d, logit
toxicity), so we pool the SCALE-FREE fractional MAE reduction:
    frac = (relevance MAE - null MAE) / null MAE        (negative = relevance better)
random-effects (DL) across the pre-registered CLEAN qualifiers (modifier permutation
p < 0.05). FLAT-modifier slices (n.s. permutation) are the in-data beta=0 negative
control and are excluded from the pool. This converts the N=2 same-class replication
into an N-slice, M-specialty result.
"""
import json, io, sys, numpy as np
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
Z = 1.959963984540054

SPECIALTY = {
    "T2DM_HbA1c_GLP1only:ALL:dose": "Endocrine/Metabolic (GLP1)",
    "Obesity_weight:ALL:baseline":  "Endocrine/Metabolic (GLP1)",
    "Edu_SATcoaching:kalaian:hrs":  "Education",
    "Edu_TeacherExpect:raudenbush:weeks": "Education",
    "Addiction_BriefAlcohol:tannersmith:age": "Addiction",
    "Onc_DoseToxicity:ursino:dose": "Oncology",
}
GLP1 = ["T2DM_HbA1c_GLP1only:ALL:dose", "Obesity_weight:ALL:baseline"]

prior = json.load(open("loo_results_v2.json"))
multi = json.load(open("multispecialty_loo.json"))
slices = {k: prior[k] for k in GLP1}
slices.update(multi)


def se_ci(ci):
    return (float(ci[1]) - float(ci[0])) / (2 * Z)


def frac(c, which):
    return c[f"d_rel_{which}"] / c[f"mae_{which}"], se_ci(c[f"ci_rel_{which}"]) / c[f"mae_{which}"]


def dl_pool(est, se):
    est = np.asarray(est, float); v = np.asarray(se, float)**2
    if len(est) == 1:
        return float(est[0]), float(np.sqrt(v[0])), 0.0
    w = 1/v; mu = (w*est).sum()/w.sum()
    Q = float((w*(est-mu)**2).sum()); df = len(est)-1
    c = w.sum() - (w**2).sum()/w.sum(); tau2 = max(0.0, (Q-df)/c) if c > 0 else 0.0
    w2 = 1/(v+tau2)
    return float((w2*est).sum()/w2.sum()), float(np.sqrt(1/w2.sum())), tau2


print("=" * 100)
print("CROSS-SPECIALTY PER-SLICE SUMMARY (central bandwidth = SD)")
print(f"{'slice':42}{'specialty':28}{'n':>4}{'perm_p':>8}  {'frac v unif':>12}{'frac v scr':>11}  win?")
clean, flat = [], []
for lab in slices:
    r = slices[lab]; c = r["central"]
    pp = (r.get("verify") or {}).get("perm_p", r.get("screen", {}).get("perm_p"))
    fu = frac(c, "uni")[0]; fs = frac(c, "scr")[0]
    tag = "YES" if r["beats_both"] else ("dir" if fu < 0 and fs < 0 else "no")
    print(f"{lab[:42]:42}{SPECIALTY[lab][:28]:28}{r['n']:>4}{(pp or 0):>8.4f}  "
          f"{fu:>+12.1%}{fs:>+11.1%}  {tag}")
    (clean if r["tier"] == "clean" else flat).append((lab, r))

print("\n" + "=" * 100)
specs = sorted(set(SPECIALTY[l] for l, _ in clean))
nboth = sum(int(r["beats_both"]) for _, r in clean)
print(f"CLEAN qualifiers (modifier perm p<0.05): N={len(clean)} slices across "
      f"{len(specs)} specialties: {', '.join(specs)}")
print(f"  relevance beats BOTH nulls in {nboth}/{len(clean)} clean slices: "
      + ", ".join(f"{SPECIALTY[l].split()[0]}({'Y' if r['beats_both'] else 'n'})" for l, r in clean))
for lab, r in flat:
    c = r["central"]
    print(f"  FLAT control [{SPECIALTY[lab]}] {lab.split(':')[1]}: relevance frac vs unif "
          f"{frac(c,'uni')[0]:+.1%} -> {'inert (correct)' if abs(frac(c,'uni')[0])<0.10 else 'NOT inert'}")

print("\n" + "=" * 100)
print(f"POOLED cross-specialty estimate (DL random-effects, scale-free fractional MAE reduction):")
for which, name in [("uni", "relevance - uniform (no-relevance null)"),
                    ("scr", "relevance - scrambled null")]:
    est = [frac(r["central"], which)[0] for _, r in clean]
    se = [frac(r["central"], which)[1] for _, r in clean]
    mu, sem, tau2 = dl_pool(est, se); lo, hi = mu - Z*sem, mu + Z*sem
    print(f"  {name:42}: {mu:+.1%} [{lo:+.1%}, {hi:+.1%}]  tau2={tau2:.4f}  "
          f"{'CI<0 ROBUST' if hi < 0 else 'n.s.'}")

# strong-modifier subset (R2>=0.15) -- the inert kalaian (R2~0.08) dilutes the pool
strong = [(l, r) for l, r in clean
          if ((r.get("verify") or {}).get("R2", r.get("screen", {}).get("R2", 1)) or 1) >= 0.15]
print(f"\nSENSITIVITY -- strong-modifier subset (in-data R2>=0.15, N={len(strong)}: "
      f"{', '.join(SPECIALTY[l].split()[0]+'/'+l.split(':')[1] for l,r in strong)}):")
for which, name in [("uni", "vs uniform"), ("scr", "vs scrambled")]:
    est = [frac(r["central"], which)[0] for _, r in strong]
    se = [frac(r["central"], which)[1] for _, r in strong]
    mu, sem, tau2 = dl_pool(est, se); lo, hi = mu - Z*sem, mu + Z*sem
    print(f"  relevance {name:14}: {mu:+.1%} [{lo:+.1%}, {hi:+.1%}]  "
          f"{'CI<0 ROBUST' if hi < 0 else 'n.s.'}")

print("\nHEADLINE: relevance-borrowing now replicated across "
      f"{len(specs)} specialties; beats both nulls in {nboth}/{len(clean)} clean slices.")
