"""Bounded truth-first AACT field extractor -- TWO log-effect families.

Extends aact_lor_expand.py:
  * threshold lowered to k>=6 (still a plausible small MA);
  * ADDS a HAZARD-RATIO family 'LHR' (param_type 'Hazard Ratio (HR)'),
    logHR = log(HR), se = (log(hi)-log(lo))/(2*1.96), grouped into its OWN
    coherent (MeSH condition x intervention-class) meta-analyses -- kept as a
    SEPARATE family so the block-diagonal-by-family field never mixes LOR & LHR.

Same self-verifying, truth-first contract as the LOR extractor:
  - effects come from sponsors' OWN reported outcome_analyses estimate + 2-sided
    95% CI (no arm-labeling, no paper transcription);
  - PRE-SPECIFIED outcomes only (PRIMARY / OTHER_PRE_SPECIFIED);
  - ONE median-log-effect row per trial (deterministic centrality);
  - CI round-trip verified (reconstruct exp(eff +/- 1.96 se) == reported CI);
  - quality bar: |effect|<=5, 0.01<=se<=3, valid positive 2-sided 95% CI;
  - specialty mapped from the MeSH condition via an explicit, auditable dict
    (unmapped conditions are DROPPED -- never invent a specialty).

Writes `aact_nodes.csv` in the corpus schema (ma, family, specialty, yi, se, year, nct).
"""
import csv, io, sys, math
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
AACT = Path("F:/AACT-storage/AACT/2026-04-12")
Z = 1.959963984540054
HERE = Path(__file__).resolve().parent
K_MIN = 6

# MeSH condition (downcase) -> corpus specialty vocabulary. Explicit + auditable;
# any unmapped condition is DROPPED. Oncology bucket = all neoplasm/carcinoma/
# leukemia/lymphoma MeSH umbrellas (unambiguous); 'lung diseases, obstructive' is
# respiratory (COPD) -> clinical_medicine, NOT cancer.
COND_SPECIALTY = {
    # --- LOR-side conditions (from aact_lor_expand.py) ---
    "diabetes mellitus": "clinical_medicine",
    "hepatitis c": "infectious_disease",
    "depressive disorder": "psychiatry",
    "spondylarthropathies": "clinical_medicine",
    "health behavior": "clinical_behavioral",
    # --- oncology (survival HRs live here) ---
    "carcinoma, bronchogenic": "oncology",
    "neoplasms by site": "oncology",
    "neoplasms by histologic type": "oncology",
    "intestinal neoplasms": "oncology",
    "gastrointestinal neoplasms": "oncology",
    "genital neoplasms, male": "oncology",
    "endocrine gland neoplasms": "oncology",
    "adenocarcinoma": "oncology",
    "carcinoma": "oncology",
    "carcinoma, squamous cell": "oncology",
    "neuroendocrine tumors": "oncology",
    "neoplasms, plasma cell": "oncology",
    "leukemia, myeloid": "oncology",
    "leukemia, b-cell": "oncology",
    "lymphoma": "oncology",
    # --- respiratory (non-oncology HR trials) ---
    "lung diseases, obstructive": "clinical_medicine",
}

FAMILIES = {
    "LOR": {"Odds Ratio (OR)", "Odds Ratio"},
    "LHR": {"Hazard Ratio (HR)"},
}


def col(fn):
    f = open(AACT / fn, encoding="utf-8", errors="replace")
    r = csv.reader(f, delimiter="|")
    h = next(r)
    return r, {c: i for i, c in enumerate(h)}


def load_primary():
    r, ix = col("outcomes.txt")
    primary = set()
    for row in r:
        if len(row) <= ix["outcome_type"]:
            continue
        if row[ix["outcome_type"]].upper() in ("PRIMARY", "OTHER_PRE_SPECIFIED"):
            primary.add(row[ix["id"]])
    return primary


def load_effects(primary, param_types):
    """per (nct): list of (log-effect, se, roundtrip_ok) for the given param_types."""
    r, ix = col("outcome_analyses.txt")
    per_nct = defaultdict(list)
    kept = 0
    for row in r:
        if len(row) <= ix["ci_upper_limit"]:
            continue
        if row[ix["param_type"]] not in param_types:
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
        eff = math.log(pv)
        se = (math.log(hi) - math.log(lo)) / (2 * Z)
        if not (0.01 <= se <= 3.0) or abs(eff) > 5.0:
            continue
        rt_lo = math.exp(eff - Z * se); rt_hi = math.exp(eff + Z * se)
        ok = (abs(rt_lo - lo) <= 0.05 * lo + 1e-6) and (abs(rt_hi - hi) <= 0.05 * hi + 1e-6)
        per_nct[row[ix["nct_id"]]].append((eff, se, ok))
        kept += 1
    return per_nct, kept


def nct_meta(ncts):
    r, ix = col("browse_conditions.txt"); cond = {}
    for row in r:
        if len(row) <= ix["downcase_mesh_term"]:
            continue
        nct = row[ix["nct_id"]]
        if nct in ncts and nct not in cond:
            cond[nct] = row[ix["downcase_mesh_term"]]
    r, ix = col("browse_interventions.txt"); interv = {}
    for row in r:
        if len(row) <= ix["downcase_mesh_term"]:
            continue
        nct = row[ix["nct_id"]]
        if nct in ncts and nct not in interv:
            interv[nct] = row[ix["downcase_mesh_term"]]
    r, ix = col("studies.txt"); year = {}
    sd = ix["start_date"]
    for row in r:
        if len(row) <= sd:
            continue
        nct = row[ix["nct_id"]]
        if nct in ncts:
            m = row[sd][:4]
            year[nct] = int(m) if m.isdigit() else None
    return cond, interv, year


def build_family(family, param_types, primary):
    per_nct, kept = load_effects(primary, param_types)
    cond, interv, year = nct_meta(set(per_nct))
    groups = defaultdict(list)
    rt_fail = 0
    for nct, lst in per_nct.items():
        if nct not in cond or nct not in interv:
            continue
        c = cond[nct]
        if c not in COND_SPECIALTY:
            continue
        lst_sorted = sorted(lst, key=lambda t: t[0])
        med = lst_sorted[len(lst_sorted) // 2]
        if not med[2]:
            rt_fail += 1
            continue
        groups[(c, interv[nct])].append((nct, med[0], med[1], year.get(nct)))
    rows = []
    kept_groups = 0
    used = set()
    tag = "aacthr" if family == "LHR" else "aact"
    for (c, i), members in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        if len(members) < K_MIN:
            continue
        kept_groups += 1
        # collision-free ma label: distinct (condition x intervention) groups MUST
        # stay distinct MAs (truncated slugs alone collide, e.g. two 'neoplasms*'
        # conditions or two 'antibodies*' classes -> silent merge). Disambiguate.
        base = f"{tag}_{c.split(',')[0].replace(' ', '')[:10]}_{i.split(',')[0].replace(' ', '')[:10]}"
        ma = base
        n = 1
        while ma in used:
            n += 1
            ma = f"{base}{n}"
        used.add(ma)
        spec = COND_SPECIALTY[c]
        for (nct, eff, se, yr) in members:
            rows.append(dict(ma=ma, family=family, specialty=spec, yi=eff, se=se,
                             year=(yr if yr else ""), nct=nct))
    print(f"[{family}] primary analyses kept (valid CI): {kept} across {len(per_nct)} NCTs; "
          f"CI round-trip drops: {rt_fail}; MAs (k>={K_MIN}): {kept_groups}; nodes: {len(rows)}")
    return rows


def main():
    primary = load_primary()
    print(f"pre-specified outcomes: {len(primary)}")
    all_rows = []
    for fam, pts in FAMILIES.items():
        all_rows += build_family(fam, pts, primary)
    out = HERE / "aact_nodes.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["ma", "family", "specialty", "yi", "se", "year", "nct"])
        w.writeheader(); w.writerows(all_rows)
    print(f"wrote {out}")
    import pandas as pd
    df = pd.DataFrame(all_rows)
    print("\nper-family:")
    for fam, sub in df.groupby("family"):
        print(f"  {fam}: {len(sub)} nodes / {sub.ma.nunique()} MAs / specialties {sorted(sub.specialty.unique())}")
    print("\nper-MA summary:")
    for ma, sub in df.groupby("ma"):
        y = sub.yi.astype(float)
        print(f"  {ma:40} k={len(sub):3} {sub.family.iloc[0]} {sub.specialty.iloc[0]:16} "
              f"eff {y.min():+.2f}..{y.max():+.2f} (mean {y.mean():+.2f})")
    print(f"\nTOTAL: {len(df)} nodes / {df.ma.nunique()} MAs")


if __name__ == "__main__":
    main()
