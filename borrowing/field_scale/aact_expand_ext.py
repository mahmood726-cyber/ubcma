"""Extended bounded truth-first AACT field extractor -- THREE log-effect families.

Extends borrowing/field_scale/aact_expand.py (unchanged contract) with:
  * a NEW RISK-RATIO family 'LRR' (param_type 'Risk Ratio (RR)' + exact
    case-variant synonyms discovered by scanning outcome_analyses.txt);
  * SAME-ESTIMAND synonym folding to enlarge the held-out slice truthfully:
      LHR now also admits Cox-model / adjusted / stratified HAZARD RATIOS
      ('Cox Proportional Hazard', 'Adjusted Hazard Ratio', ...) -- all
      ratio-scale HRs, guarded by the CI round-trip so any accidental
      log-scale entry is rejected;
      LOR now also admits adjusted / unadjusted / stratified / common ODDS
      RATIOS -- all ratio-scale ORs.
    EXPLICITLY log-scale param_types ('Hazard Ratio, log', 'Odds Ratio, log',
    'Risk Ratio, log') and Bayesian posterior medians are NOT folded (different
    transform / estimand) -- truth-first, no quality-bar drop.
  * an auditable report of any k>=6 (condition x intervention) group whose MeSH
    condition is UNMAPPED, so specialty-map growth is data-driven not invented.

All other machinery is identical to the committed extractor: pre-specified
outcomes only, ONE median-log-effect row per trial, |eff|<=5 & 0.01<=se<=3,
positive 2-sided 95% CI, CI round-trip, explicit COND_SPECIALTY, k>=6 per
(condition x intervention) group, block-diagonal-by-family, collision-free MA
labels. Writes aact_nodes_ext.csv (corpus schema).
"""
import csv, io, sys, math
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
AACT = Path("F:/AACT-storage/AACT/2026-04-12")
Z = 1.959963984540054
HERE = Path(__file__).resolve().parent
K_MIN = 6

# --- auditable MeSH condition (downcase) -> corpus specialty. Never invented. ---
COND_SPECIALTY = {
    # LOR-side
    "diabetes mellitus": "clinical_medicine",
    "hepatitis c": "infectious_disease",
    "depressive disorder": "psychiatry",
    "spondylarthropathies": "clinical_medicine",
    "health behavior": "clinical_behavioral",
    # oncology umbrellas (survival HRs)
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
    "lung diseases, obstructive": "clinical_medicine",
}
NEW_UMBRELLAS = {
    # The ONLY unmapped condition that surfaces as a k>=6 (cond x interv) group
    # under the enlarged HR-synonym set (AUDIT_ONLY=1 revealed it). Astrocytoma is
    # an unambiguous CNS glioma -> oncology. No other candidate umbrella reaches
    # k>=6, so none are added (adding them would be inventing dead mappings).
    "astrocytoma": "oncology",
}
import os as _os
AUDIT_ONLY = _os.environ.get("AUDIT_ONLY", "0") == "1"
if not AUDIT_ONLY:
    COND_SPECIALTY.update(NEW_UMBRELLAS)

FAMILIES = {
    # ratio-scale ODDS ratios (NOT 'Odds Ratio, log', NOT posterior medians)
    "LOR": {"Odds Ratio (OR)", "Odds Ratio", "Adjusted Odds Ratio",
            "Adjusted odds ratio", "Unadjusted Odds Ratio", "Crude Odds Ratio",
            "Common Odds Ratio", "Stratified Odds Ratio", "Ratio of odds"},
    # ratio-scale HAZARD ratios (NOT 'Hazard Ratio, log', NOT posterior medians,
    # NOT Wilcoxon Z)
    "LHR": {"Hazard Ratio (HR)", "Cox Proportional Hazard", "Adjusted Hazard Ratio",
            "Stratified Hazard Ratio", "Weighted Hazard Ratio", "Unstratified Hazard Ratio",
            "Cox proportional hazard ratio", "Cox Proportional Hazard Ratio",
            "Cox hazard ratio", "Hazard Ratio (stratified)", "Stratified Hazard Ratio (HR)",
            "Cause specific Hazard ratio", "adjusted cause-specific hazard ratio",
            "Subdistribution hazard ratio"},
    # ratio-scale RISK ratios (NOT 'Risk Ratio, log', NOT 'Relative Risk Reduction',
    # NOT 'Rate Ratio' which is a person-time incidence-rate ratio)
    "LRR": {"Risk Ratio (RR)", "Relative Risk (RR)", "Relative risk (RR)",
            "Risk Ratio", "Relative Risk", "Relative risk", "Risk ratio", "relative risk"},
}


def col(fn):
    f = open(AACT / fn, encoding="utf-8", errors="replace")
    r = csv.reader(f, delimiter="|"); h = next(r)
    return r, {c: i for i, c in enumerate(h)}


def load_primary():
    r, ix = col("outcomes.txt"); primary = set()
    for row in r:
        if len(row) <= ix["outcome_type"]:
            continue
        if row[ix["outcome_type"]].upper() in ("PRIMARY", "OTHER_PRE_SPECIFIED"):
            primary.add(row[ix["id"]])
    return primary


def load_effects(primary, param_types):
    r, ix = col("outcome_analyses.txt")
    per_nct = defaultdict(list); kept = 0
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
    r, ix = col("studies.txt"); year = {}; sd = ix["start_date"]
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
    groups = defaultdict(list); rt_fail = 0
    for nct, lst in per_nct.items():
        if nct not in cond or nct not in interv:
            continue
        lst_sorted = sorted(lst, key=lambda t: t[0])
        med = lst_sorted[len(lst_sorted) // 2]
        if not med[2]:
            rt_fail += 1
            continue
        groups[(cond[nct], interv[nct])].append((nct, med[0], med[1], year.get(nct)))
    # audit: which k>=6 (cond x interv) groups are being DROPPED for an unmapped MeSH condition
    unmapped = defaultdict(lambda: [0, 0])
    for (c, i), members in groups.items():
        if len(members) >= K_MIN and c not in COND_SPECIALTY:
            unmapped[c][0] += 1; unmapped[c][1] += len(members)
    if unmapped:
        print(f"  [{family}] UNMAPPED k>={K_MIN} conditions (DROPPED -- audit before mapping):")
        for c, (ng, nn) in sorted(unmapped.items(), key=lambda kv: -kv[1][1]):
            print(f"      {nn:4d} nodes / {ng} grp   {c!r}")
    rows = []; kept_groups = 0; used = set()
    tag = {"LHR": "aacthr", "LRR": "aactrr", "LOR": "aact"}[family]
    for (c, i), members in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        if len(members) < K_MIN or c not in COND_SPECIALTY:
            continue
        kept_groups += 1
        base = f"{tag}_{c.split(',')[0].replace(' ', '')[:10]}_{i.split(',')[0].replace(' ', '')[:10]}"
        ma = base; n = 1
        while ma in used:
            n += 1; ma = f"{base}{n}"
        used.add(ma)
        spec = COND_SPECIALTY[c]
        for (nct, eff, se, yr) in members:
            rows.append(dict(ma=ma, family=family, specialty=spec, yi=eff, se=se,
                             year=(yr if yr else ""), nct=nct))
    print(f"  [{family}] valid analyses: {kept} across {len(per_nct)} NCTs; "
          f"round-trip drops: {rt_fail}; MAs(k>={K_MIN}): {kept_groups}; nodes: {len(rows)}")
    return rows


def main():
    primary = load_primary()
    print(f"pre-specified outcomes: {len(primary)}")
    all_rows = []
    for fam, pts in FAMILIES.items():
        all_rows += build_family(fam, pts, primary)
    out = HERE / "aact_nodes_ext.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["ma", "family", "specialty", "yi", "se", "year", "nct"])
        w.writeheader(); w.writerows(all_rows)
    print(f"wrote {out}")
    import pandas as pd
    df = pd.DataFrame(all_rows)
    print("\nper-family:")
    for fam in ["LOR", "LHR", "LRR"]:
        sub = df[df.family == fam] if len(df) else df
        if len(sub):
            print(f"  {fam}: {len(sub)} nodes / {sub.ma.nunique()} MAs / specialties {sorted(sub.specialty.unique())}")
        else:
            print(f"  {fam}: 0 nodes / 0 MAs  (NULL under strict k>={K_MIN} cond x interv bar)")
    print(f"\nTOTAL: {len(df)} nodes / {df.ma.nunique() if len(df) else 0} MAs")


if __name__ == "__main__":
    main()
