"""Build clean real-AACT LOR meta-analyses to stress-test the learned-kernel headline.

Question: does the learned-kernel-beats-within-MA result survive expanding the
1177-node / 28-MA corpus with GENUINELY NEW real meta-analyses from a different
source (ClinicalTrials.gov / AACT)?  If the advantage is a metadat artefact it should
vanish; if it is a real property of cross-MA structure it should persist.

Truth-first extraction (NO arm-labeling, NO paper transcription):
- Effects come from sponsors' OWN reported `outcome_analyses` Odds-Ratio estimates + their
  2-sided 95% CIs (AACT snapshot F:/AACT-storage/AACT/2026-04-12).  logOR = log(OR),
  se = (log(ci_hi) - log(ci_lo)) / (2 * 1.959964).  Every row is self-verifying: we
  round-trip exp(logOR +- 1.96 se) back to the reported CI and assert agreement.
- PRIMARY outcomes only (join outcome_id -> outcomes.outcome_type == 'Primary') to cut
  multiplicity; if a trial still reports several primary ORs within a group, take the
  MEDIAN-logOR row (deterministic centrality, no extreme cherry-pick).
- A "meta-analysis" = one (MeSH condition x MeSH intervention-class) group with >= 8
  contributing trials -> a coherent, poolable unit (same disease, same drug class).
- family = LOR (matches the corpus LOR family); year = trial start-date year; specialty
  mapped from the MeSH condition to the corpus's specialty vocabulary.

Outputs `aact_lor_nodes.csv` in the corpus schema (ma, family, specialty, yi, se, year).
"""
import csv, io, sys, math
from collections import defaultdict
from pathlib import Path
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
AACT = Path("F:/AACT-storage/AACT/2026-04-12")
Z = 1.959963984540054
HERE = Path(__file__).resolve().parent

# MeSH condition (downcase) -> corpus specialty vocabulary. Anything unmapped is dropped
# (we never invent a specialty). Kept deliberately small + auditable.
COND_SPECIALTY = {
    "diabetes mellitus": "clinical_medicine",
    "hepatitis c": "infectious_disease",
    "depressive disorder": "psychiatry",
    "spondylarthropathies": "clinical_medicine",
    "intestinal neoplasms": "oncology",
    "carcinoma, bronchogenic": "oncology",
    "neoplasms by site": "oncology",
    "neuroendocrine tumors": "oncology",
    "health behavior": "clinical_behavioral",
}


def col(fn):
    f = open(AACT / fn, encoding="utf-8", errors="replace")
    r = csv.reader(f, delimiter="|")
    h = next(r)
    return r, {c: i for i, c in enumerate(h)}


def build():
    # 1) primary outcome_ids
    r, ix = col("outcomes.txt")
    primary = set()
    for row in r:
        if len(row) <= ix["outcome_type"]:
            continue
        if row[ix["outcome_type"]].upper() in ("PRIMARY", "OTHER_PRE_SPECIFIED"):
            primary.add(row[ix["id"]])          # pre-specified only (exclude SECONDARY/POST_HOC)
    print(f"pre-specified outcomes: {len(primary)}")

    # 2) OR analyses on primary outcomes with a valid 2-sided 95% CI
    r, ix = col("outcome_analyses.txt")
    # per (nct): list of (logor, se, roundtrip_ok)
    per_nct = defaultdict(list)
    kept = 0
    for row in r:
        if len(row) <= ix["ci_upper_limit"]:
            continue
        if row[ix["param_type"]] not in ("Odds Ratio (OR)", "Odds Ratio"):
            continue
        if row[ix["outcome_id"]] not in primary:
            continue
        cp = row[ix["ci_percent"]]
        try:
            pv = float(row[ix["param_value"]]); lo = float(row[ix["ci_lower_limit"]]); hi = float(row[ix["ci_upper_limit"]])
            if not (cp and abs(float(cp) - 95) < 1e-6):
                continue
            if pv <= 0 or lo <= 0 or hi <= 0 or hi <= lo:
                continue
        except (ValueError, TypeError):
            continue
        logor = math.log(pv)
        se = (math.log(hi) - math.log(lo)) / (2 * Z)
        if not (0.0 < se < 3.0) or abs(logor) > 5.0:
            continue
        # CI round-trip check: reconstruct CI from logor +- 1.96 se, compare to reported (rel 5%)
        rt_lo = math.exp(logor - Z * se); rt_hi = math.exp(logor + Z * se)
        ok = (abs(rt_lo - lo) <= 0.05 * lo + 1e-6) and (abs(rt_hi - hi) <= 0.05 * hi + 1e-6)
        per_nct[row[ix["nct_id"]]].append((logor, se, ok))
        kept += 1
    print(f"primary-OR analyses kept (valid CI): {kept} across {len(per_nct)} NCTs")

    # 3) nct -> condition, intervention (first mesh term), year
    r, ix = col("browse_conditions.txt"); cond = {}
    for row in r:
        if len(row) <= ix["downcase_mesh_term"]:
            continue
        nct = row[ix["nct_id"]]
        if nct in per_nct and nct not in cond:
            cond[nct] = row[ix["downcase_mesh_term"]]
    r, ix = col("browse_interventions.txt"); interv = {}
    for row in r:
        if len(row) <= ix["downcase_mesh_term"]:
            continue
        nct = row[ix["nct_id"]]
        if nct in per_nct and nct not in interv:
            interv[nct] = row[ix["downcase_mesh_term"]]
    r, ix = col("studies.txt"); year = {}
    sd = ix["start_date"]
    for row in r:
        if len(row) <= sd:
            continue
        nct = row[ix["nct_id"]]
        if nct in per_nct:
            m = row[sd][:4]
            year[nct] = int(m) if m.isdigit() else None

    # 4) group by (cond, interv); one median-logOR node per trial; keep groups k>=8
    groups = defaultdict(list)
    rt_fail = 0
    for nct, lst in per_nct.items():
        if nct not in cond or nct not in interv:
            continue
        c = cond[nct]
        if c not in COND_SPECIALTY:
            continue
        lst_sorted = sorted(lst, key=lambda t: t[0])
        med = lst_sorted[len(lst_sorted) // 2]        # median-logOR row (deterministic)
        if not med[2]:
            rt_fail += 1
            continue                                    # drop trials whose CI fails round-trip
        groups[(c, interv[nct])].append((nct, med[0], med[1], year.get(nct)))
    print(f"CI round-trip failures dropped: {rt_fail}")

    rows = []
    kept_groups = 0
    for (c, i), members in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        if len(members) < 8:
            continue
        kept_groups += 1
        ma = f"aact_{c.split(',')[0].replace(' ', '')[:10]}_{i.split(',')[0].replace(' ', '')[:10]}"
        spec = COND_SPECIALTY[c]
        for (nct, yi, se, yr) in members:
            rows.append(dict(ma=ma, family="LOR", specialty=spec, yi=yi, se=se,
                             year=(yr if yr else ""), nct=nct))
    print(f"kept MAs (k>=8): {kept_groups} ; total AACT nodes: {len(rows)}")
    return rows


def main():
    rows = build()
    out = HERE / "aact_lor_nodes.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["ma", "family", "specialty", "yi", "se", "year", "nct"])
        w.writeheader(); w.writerows(rows)
    print(f"wrote {out}")
    # summary
    import pandas as pd
    df = pd.DataFrame(rows)
    print("\nper-MA summary:")
    for ma, sub in df.groupby("ma"):
        y = sub.yi.astype(float)
        print(f"  {ma:34} k={len(sub):3} spec={sub.specialty.iloc[0]:18} "
              f"logOR {y.min():+.2f}..{y.max():+.2f} (mean {y.mean():+.2f})")
    print(f"\nspecialties: {sorted(df.specialty.unique())}")
    print(f"total: {len(df)} nodes / {df.ma.nunique()} MAs")


if __name__ == "__main__":
    main()
