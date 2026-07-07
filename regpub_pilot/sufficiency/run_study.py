"""Run the OPEN-DATA SUFFICIENCY study end-to-end and emit deliverables:

  out/sufficiency_table.csv     — per-review table (weight coverage, reproduce, verdict)
  out/sufficiency_headline.json — the headline counts (by tier + overall) + sensitivity
  out/sufficiency_full.json     — full machine-readable results

Headline question: of N real published meta-analyses, how many can be REPRODUCED to
the same clinical conclusion from OPEN DATA ALONE *and* shown ROBUST to the evidence
we could not pool (worst-case one-directional / publication-bias-style missingness)?
"""
from __future__ import annotations
import os, sys, csv, json, math, copy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "src"))

import reviews as RV
from analysis import verdict
OUT = os.path.join(HERE, "..", "out")


def reclassify(review, year_thr, n_thr, abstract_era=None):
    """Return a copy of `review` with poolable flags recomputed under a different
    open-data rule (coverage-tier only; extraction-tier flags are MEASURED, kept)."""
    r = copy.deepcopy(review)
    if r.tier == "extraction":
        return r
    for t in r.trials:
        if abstract_era is not None:
            t.poolable = bool((t.year is not None and t.year >= abstract_era)
                              or (t.n is not None and t.n >= n_thr))
        else:
            t.poolable = RV.is_poolable(t.year, t.n, year_thr, n_thr)
    return r


def summarize(vs):
    """Count reproduced/robust/fragile/not-reproduced over a list of verdict dicts."""
    c = {"n": len(vs), "reproduced": 0, "robust": 0, "fragile": 0,
         "not_reproduced": 0, "insufficient": 0}
    for v in vs:
        vd = v["verdict"]
        if vd == "ROBUST":
            c["reproduced"] += 1; c["robust"] += 1
        elif vd == "FRAGILE" and v["rep"]["ok"] and v["rep"]["reproduced"]:
            c["reproduced"] += 1; c["fragile"] += 1
        elif vd == "NOT_REPRODUCED":
            c["not_reproduced"] += 1
        elif vd == "INSUFFICIENT":
            c["insufficient"] += 1
    c["reproduced_and_robust"] = c["robust"]
    return c


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    revs = RV.all_reviews()
    rows, full = [], []
    verds = []
    for r in revs:
        v = verdict(r)
        verds.append(v)
        cov, rep = v["cov"], v["rep"]
        bt = math.exp if r.scale == "log" else (lambda x: x)
        row = {
            "key": r.key, "area": r.area, "tier": r.tier, "measure": r.measure,
            "k_total": cov["k_total"], "k_pool": cov["k_pool"],
            "cov_fixed_pct": round(cov["cov_fixed"] * 100, 1),
            "cov_re_pct": round(cov["cov_re"] * 100, 1),
            "pub_conclusion": r.published["conclusion"],
            "pub_est": round(bt(r.published["est"]), 3),
            "repro_std_conclusion": rep.get("conclusion") if rep["ok"] else "-",
            "repro_std_est": round(rep["est_nat"], 3) if rep["ok"] else None,
            "reproduced": rep["reproduced"] if rep["ok"] else False,
            "house_conclusion": rep.get("house_conclusion") if rep["ok"] else "-",
            "house_agrees_pub": rep.get("house_agrees_pub") if rep["ok"] else None,
            "r_star": round(v["r_star"], 2) if "r_star" in v else None,
            "rho_missing_fixed": round(v["rho_fixed"], 2) if "rho_fixed" in v else None,
            "rho_missing_re": round(v["rho_re"], 2) if "rho_re" in v else None,
            "verdict": v["verdict"],
            "why": v["why"],
        }
        rows.append(row)
        full.append({"row": row, "cov": cov,
                     "bf": v.get("bf"), "lit_note": r.lit_note, "note": r.note})

    # ---- tier + overall summaries -----------------------------------------
    tier1 = [v for v, r in zip(verds, revs) if r.tier == "extraction"]
    tier2 = [v for v, r in zip(verds, revs) if r.tier == "coverage"]
    headline = {
        "N": len(revs),
        "overall": summarize(verds),
        "tier1_allopen_reconstruct": summarize(tier1),
        "tier2_historical_longtail": summarize(tier2),
        "poolability_rule": RV.poolability_rule,
        "notes": {
            "tier1": "modern registered-trial CLASS meta-analyses; open data fidelity IS tested "
                     "(real CT.gov + PubMed extraction). All trials free -> coverage ~100%.",
            "tier2": "historical mixed-era meta-analyses (metadat); per-trial data from the "
                     "published dataset, so only COVERAGE + INFLUENCE are tested, not extraction. "
                     "Poolability is an ESTIMATE from the rule; see sensitivity sweep.",
            "iv_mg_mi": "NOT_REPRODUCED vs the published RE-protective result — but the open-data "
                        "mega-trial subset (null) is the modern-consensus CORRECT answer; the "
                        "published RE conclusion was itself a small-study-effect artifact. Open data "
                        "RESISTS the artifact rather than being 'wrong'.",
        },
    }

    # ---- poolability sensitivity sweep (tier-2 only) ----------------------
    sweep = {}
    scenarios = [
        ("base (year>=2006 | N>=5000)", dict(year_thr=2006, n_thr=5000)),
        ("strict (year>=2010 | N>=5000)", dict(year_thr=2010, n_thr=5000)),
        ("lenient (year>=2000 | N>=5000)", dict(year_thr=2000, n_thr=5000)),
        ("abstract-era (year>=1995 | N>=5000)", dict(year_thr=2006, n_thr=5000, abstract_era=1995)),
    ]
    for name, kw in scenarios:
        vs2 = [verdict(reclassify(r, **kw)) for r in revs if r.tier == "coverage"]
        sweep[name] = {"summary": summarize(vs2),
                       "per_review": {r.key: verdict(reclassify(r, **kw))["verdict"]
                                      for r in revs if r.tier == "coverage"}}
    headline["sensitivity_sweep_tier2"] = sweep

    # ---- write artifacts --------------------------------------------------
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "sufficiency_table.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    json.dump(headline, open(os.path.join(OUT, "sufficiency_headline.json"), "w", encoding="utf-8"),
              indent=2)
    json.dump(full, open(os.path.join(OUT, "sufficiency_full.json"), "w", encoding="utf-8"),
              indent=2, default=str)

    # ---- console summary --------------------------------------------------
    print("=" * 90)
    print("OPEN-DATA SUFFICIENCY — per-review")
    print("=" * 90)
    hdr = f"{'review':18s} {'tier':11s} {'k(p/T)':7s} {'cov_fx':6s} {'cov_RE':6s} {'pub':8s} {'repro':8s} {'verdict':14s}"
    print(hdr); print("-" * len(hdr))
    for row in rows:
        print(f"{row['key']:18s} {row['tier']:11s} "
              f"{str(row['k_pool'])+'/'+str(row['k_total']):7s} "
              f"{row['cov_fixed_pct']:5.1f}% {row['cov_re_pct']:5.1f}% "
              f"{row['pub_conclusion']:8s} {str(row['repro_std_conclusion']):8s} {row['verdict']:14s}")
    print("\nHEADLINE")
    o, t1, t2 = headline["overall"], headline["tier1_allopen_reconstruct"], headline["tier2_historical_longtail"]
    print(f"  Overall N={o['n']}: reproduced&robust={o['robust']}  reproduced-but-fragile={o['fragile']}  "
          f"not-reproduced={o['not_reproduced']}  insufficient={o['insufficient']}")
    print(f"  Tier-1 (all-open class MAs) N={t1['n']}: robust={t1['robust']} fragile={t1['fragile']} "
          f"not-repro={t1['not_reproduced']}")
    print(f"  Tier-2 (historical long-tail) N={t2['n']}: robust={t2['robust']} fragile={t2['fragile']} "
          f"not-repro={t2['not_reproduced']} insufficient={t2['insufficient']}")
    print("\n  Tier-2 poolability sensitivity (verdict counts robust/fragile/not-repro):")
    for name, s in sweep.items():
        ss = s["summary"]
        print(f"    {name:36s} robust={ss['robust']} fragile={ss['fragile']} "
              f"not-repro={ss['not_reproduced']} insuff={ss['insufficient']}")
    print(f"\n  artifacts -> out/sufficiency_table.csv, sufficiency_headline.json, sufficiency_full.json")


if __name__ == "__main__":
    main()
