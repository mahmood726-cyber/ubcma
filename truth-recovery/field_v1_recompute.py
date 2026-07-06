"""field_v1_recompute.py -- restate the v1 field-domination grid (manuscript S4.2)
under the corrected pairwise-complete aggregation, reproducibly from COMMITTED data.

Motivation: field_bakeoff.py::main --combine reads uncommitted per-shard CSVs. The
committed reproducible source is field_v1_perrep.csv (all 54 cells x 80 reps x 13
methods). This script rebuilds every v1 headline number the manuscript S4.2 and
REPORT_FIELD.md cite, from that committed per-rep table, under BOTH aggregations:

  global   = legacy pivot_table().dropna() intersection-over-all-methods (the
             selection artifact). MUST reproduce the committed field_v1_summary.json
             + REPORT_FIELD.md ranking -> validates the recompute path.
  pairwise = corrected per-comparator both-converged rep set (the fix, 8a9aea7).

Same artifact, same fix, same per-rep regeneration path as field2 (field_bakeoff2).

What it recomputes (all from field_v1_perrep.csv, mean deployable coverage is
aggregation-INDEPENDENT since it comes from score_tables raw_cov):
  1. Per-method dominated-cell ranking (every panel method as headline).
  2. tau-strata for adaptshrink_ens (16/13/2 legacy).
  3. Ceiling stats: ens loses-to counts, ens-vs-trim_and_fill head-to-head.
  4. Avenue (a) interval inflation a=2.0: adaptshrink_ens_infl 31->35 (legacy).

Usage:  PYTHONPATH=src python truth-recovery/field_v1_recompute.py [--write]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import field_bakeoff as F  # noqa: E402
import field_rescore_interval as FRI  # noqa: E402

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT = Path("truth-recovery")
CELL_KEYS = F.CELL_KEYS
# every method scored in the v1 panel (as it appears in the committed per-rep table)
RANK_METHODS = ["adaptshrink_ens", "ubcma", "adaptshrink_fast", "dl_hksj",
                "henmi_copas", "reml_hksj", "p_uniform_star", "adaptshrink_solo",
                "vevea_hedges", "copas", "p_curve", "pet_peese", "trim_and_fill"]


def dom_count(raw, score, headline, aggregation):
    pair = F.bootstrap_pairwise(raw, headline, aggregation=aggregation)
    dom = F.field_domination(score, pair, headline)
    n = int(dom["dominates_field"].sum()) if len(dom) else 0
    return n, len(dom), dom, pair


def mean_cov(score, method):
    s = score[score.method == method]
    return round(float(s["raw_cov"].mean()), 3) if len(s) else float("nan")


def tau_strata(dom):
    out = {}
    for tau, g in dom.groupby("tau"):
        out[tau] = (int(g["dominates_field"].sum()), int(len(g)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="v1")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    raw = pd.read_csv(OUT / f"field_{args.tag}_perrep.csv")
    score = F.score_tables(raw)  # aggregation-independent

    print(f"# v1 recompute from committed field_{args.tag}_perrep.csv "
          f"({raw.groupby(CELL_KEYS).ngroups} cells, {raw['rep'].max()+1} reps)\n")

    # 1. per-method ranking, both aggregations ------------------------------
    rows = []
    ens_dom = {}
    for m in RANK_METHODS:
        gn, gt, gdom, _ = dom_count(raw, score, m, "global")
        pn, pt, pdom, _ = dom_count(raw, score, m, "pairwise")
        rows.append((m, gn, gt, pn, pt, mean_cov(score, m)))
        if m == "adaptshrink_ens":
            ens_dom = {"global": gdom, "pairwise": pdom}
    print("## Per-method dominated cells (global=legacy -> pairwise=corrected); "
          "mean deployable cov is aggregation-independent\n")
    print(f"{'method':<24} {'global':>8} {'pairwise':>9} {'mean_cov':>9}")
    for m, gn, gt, pn, pt, cov in rows:
        print(f"{m:<24} {f'{gn}/{gt}':>8} {f'{pn}/{pt}':>9} {cov:>9.3f}")

    # 2. tau-strata for adaptshrink_ens -------------------------------------
    print("\n## adaptshrink_ens tau-strata (dominated/total)")
    for mode in ("global", "pairwise"):
        st = tau_strata(ens_dom[mode])
        s = "  ".join(f"tau={t}: {n}/{tot}" for t, (n, tot) in sorted(st.items()))
        print(f"  {mode:<9}: {s}")

    # 3. ceiling stats (pairwise verdicts change with aggregation) ----------
    print("\n## Ceiling stats: adaptshrink_ens loses-to (valid comparators, "
          "conv>=0.8), both modes")
    for mode in ("global", "pairwise"):
        pair = F.bootstrap_pairwise(raw, "adaptshrink_ens", aggregation=mode)
        valid = pair[pair["comp_conv"] >= 0.8]
        losses = valid[valid["verdict"] == "as_loss"]
        lose_by_comp = losses["comparator"].value_counts().to_dict()
        # ens vs trim_and_fill head-to-head across ALL cells where judged
        tf = valid[valid["comparator"] == "trim_and_fill"]["verdict"].value_counts().to_dict()
        # tau=0.3 losses to the efficient estimators
        eff = losses[(losses["tau"] == 0.3) &
                     (losses["comparator"].isin(["reml_hksj", "dl_hksj",
                                                 "henmi_copas", "copas"]))]
        print(f"  {mode:<9}: total losses={len(losses)}; by comparator={lose_by_comp}")
        print(f"             ens-vs-trim_and_fill verdicts={tf}; "
              f"tau=0.3 losses to efficient estimators={len(eff)}")

    # 4. avenue (a) interval inflation a=2.0 --------------------------------
    print("\n## Avenue (a): adaptshrink_ens_infl (disagreement inflation a=2.0)")
    inf = FRI.make_inflated(raw, 2.0, mode="disagree")
    aug = pd.concat([raw, inf], ignore_index=True)
    score_aug = F.score_tables(aug)
    infl_res = {}
    for mode in ("global", "pairwise"):
        n, tot, dom, _ = dom_count(aug, score_aug, "adaptshrink_ens_infl", mode)
        infl_res[mode] = dom
        cov = mean_cov(score_aug, "adaptshrink_ens_infl")
        w = float(score_aug[score_aug.method == "adaptshrink_ens_infl"]["raw_width"].mean())
        print(f"  {mode:<9}: dominates {n}/{tot}  overall mean deployable cov={cov:.3f}  "
              f"mean raw width={w:.4f}")

    if args.write:
        # regenerate the corrected (pairwise) domination CSVs from committed data
        for m in ["adaptshrink_ens", "adaptshrink_fast", "adaptshrink_solo"]:
            _, _, dom, _ = dom_count(raw, score, m, "pairwise")
            dom.to_csv(OUT / f"field_{args.tag}_domination_{m}.csv", index=False)
        infl_res["pairwise"].to_csv(
            OUT / f"field_{args.tag}_domination_adaptshrink_ens_infl.csv", index=False)
        inf.to_csv(OUT / f"field_{args.tag}_ens_infl_perrep.csv", index=False)
        # rebuild summary.json (headlines only, matching field_bakeoff main)
        import json
        summ = {"tag": args.tag, "target": 0.95,
                "n_cells": int(raw.groupby(CELL_KEYS).ngroups),
                "reps": int(raw["rep"].max()) + 1,
                "aggregation": "pairwise", "headlines": {}}
        for m in ["adaptshrink_ens", "adaptshrink_fast", "adaptshrink_solo"]:
            n, tot, dom, _ = dom_count(raw, score, m, "pairwise")
            summ["headlines"][m] = {
                "cells_dominated": n, "cells_total": tot,
                "cells_with_loss": int((dom["n_loss"] > 0).sum()) if len(dom) else 0}
        json.dump(summ, open(OUT / f"field_{args.tag}_summary.json", "w"), indent=2)
        # corrected pairwise table CSV (all methods, for the manuscript)
        pd.DataFrame([{"method": m, "dominated_global": gn, "dominated_pairwise": pn,
                       "cells_total": pt, "mean_deployable_cov": cov}
                      for m, gn, gt, pn, pt, cov in rows]).to_csv(
            OUT / f"field_{args.tag}_ranking.csv", index=False)
        print("\nwrote corrected pairwise domination CSVs + summary + ranking")


if __name__ == "__main__":
    main()
