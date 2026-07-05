"""Cold out-of-corpus AACT LOR slice for the leave-one-MA-out transfer test.

WHAT THIS ANSWERS (the open question in AACT_SLICE_NEXTSTEP.md, still unrun):
the committed headline (`benchmark_learned.py`) shows the learned-kernel GP beats
within-MA borrowing INSIDE the 28-MA / 1177-node corpus, and the corpus-EXPANSION
test (`aact_run_ext.py`) shows it survives when AACT MAs are ADDED to the corpus and
scored by random k-fold -- but in that test an AACT trial's own same-MA siblings sit
in the training folds, so the GP's `ma`-match kernel term still fires. The genuinely
COLD probe -- predict a FRESH registry `ma` the kernel has NEVER trained on, so it must
generalise via specialty + precision + year alone -- is what `cold_transfer.py` runs on
THIS slice. An honest null is an acceptable outcome (it would bound the headline to
in-corpus reconstruction).

EXTRACTION (identical discipline to aact_lor_expand.py; NO arm-labeling, NO paper
transcription -- effects are sponsors' OWN reported Odds-Ratio estimates + their
2-sided 95% CIs from the AACT snapshot F:/AACT-storage/AACT/2026-04-12):
  logOR = log(OR),  se = (log(ci_hi) - log(ci_lo)) / (2 * 1.959964).
  Every row is self-verifying: reconstruct exp(logOR +- 1.96 se) and assert it matches
  the reported CI to <=5% (round-trip). Trials failing the round-trip are dropped.
  ONE node per trial = the MEDIAN-logOR analysis row (deterministic centrality; controls
  within-trial outcome multiplicity WITHOUT restricting to primary outcomes, matching the
  note's ~18k all-OR recipe). A "meta-analysis" = one (MeSH condition x first-MeSH
  intervention class) group with >= 8 contributing trials. family = LOR; year = trial
  start-date year; specialty mapped from the MeSH condition to the CORPUS's specialty
  vocabulary (corpus LOR family spans: alternative_med, cardiology, clinical_medicine,
  infectious_disease, oncology, pediatrics, psychiatry, pulmonology).

PRIMARY slice = only conditions that map to a specialty PRESENT in the corpus LOR family,
so the cold transfer has a same-specialty relevance signal to test. `health behavior`
(-> clinical_behavioral, absent from corpus LOR) is emitted but flagged corpus_specialty=0
and excluded from the primary cold test.

Outputs `aact_coldslice_nodes.csv` (schema: ma, family, specialty, yi, se, year, nct,
condition, intervention, prespecified, corpus_specialty).
"""
import csv, io, sys, math
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
AACT = Path("F:/AACT-storage/AACT/2026-04-12")
Z = 1.959963984540054
HERE = Path(__file__).resolve().parent

# MeSH condition (downcase) -> corpus specialty vocabulary. Only conditions whose
# specialty is PRESENT in the corpus LOR family are marked corpus_specialty=1 and used
# in the primary cold test. Kept small + auditable; anything unmapped is dropped (we
# never invent a specialty). Corpus LOR specialties (from corpus.load_corpus):
#   alternative_med cardiology clinical_medicine infectious_disease oncology
#   pediatrics psychiatry pulmonology
COND_SPECIALTY = {
    # clinical_medicine (corpus donor: li2007 = generic clinical-medicine LOR)
    "diabetes mellitus": ("clinical_medicine", 1),
    "spondylarthropathies": ("clinical_medicine", 1),   # rheumatology -> clinical_medicine
    # oncology (corpus donor: hackshaw1998 = lung-cancer LOR; bronchogenic = lung)
    "carcinoma, bronchogenic": ("oncology", 1),
    "neoplasms by site": ("oncology", 1),
    "intestinal neoplasms": ("oncology", 1),
    # infectious_disease (corpus donors: bcg, graves2010, nielweise2007)
    "hepatitis c": ("infectious_disease", 1),
    # psychiatry (corpus donors: linde2005, linde2015)
    "depressive disorder": ("psychiatry", 1),
    # emitted but NOT corpus-matched (no clinical_behavioral in corpus LOR) -> flagged 0
    "health behavior": ("clinical_behavioral", 0),
}


def col(fn):
    f = open(AACT / fn, encoding="utf-8", errors="replace")
    r = csv.reader(f, delimiter="|")
    h = next(r)
    return r, {c: i for i, c in enumerate(h)}


def build():
    # 1) pre-specified outcome ids (for the `prespecified` flag / sensitivity split only)
    r, ix = col("outcomes.txt")
    primary = set()
    for row in r:
        if len(row) <= ix["outcome_type"]:
            continue
        if row[ix["outcome_type"]].upper() in ("PRIMARY", "OTHER_PRE_SPECIFIED"):
            primary.add(row[ix["id"]])
    print(f"pre-specified outcomes: {len(primary)}", flush=True)

    # 2) ALL OR analyses with a valid 2-sided 95% CI (self-verifying). NO primary filter
    #    (median-per-trial controls multiplicity); track whether each row is pre-specified.
    r, ix = col("outcome_analyses.txt")
    per_nct = defaultdict(list)   # nct -> list of (logor, se, roundtrip_ok, is_prespec)
    kept = 0
    for row in r:
        if len(row) <= ix["ci_upper_limit"]:
            continue
        if row[ix["param_type"]] not in ("Odds Ratio (OR)", "Odds Ratio"):
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
        rt_lo = math.exp(logor - Z * se); rt_hi = math.exp(logor + Z * se)
        ok = (abs(rt_lo - lo) <= 0.05 * lo + 1e-6) and (abs(rt_hi - hi) <= 0.05 * hi + 1e-6)
        per_nct[row[ix["nct_id"]]].append((logor, se, ok, row[ix["outcome_id"]] in primary))
        kept += 1
    print(f"all-OR analyses kept (valid CI): {kept} across {len(per_nct)} NCTs", flush=True)

    # 3) nct -> first mesh condition / intervention, start-year
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
    r, ix = col("studies.txt"); year = {}; sd = ix["start_date"]
    for row in r:
        if len(row) <= sd:
            continue
        nct = row[ix["nct_id"]]
        if nct in per_nct:
            m = row[sd][:4]
            year[nct] = int(m) if m.isdigit() else None

    # 4) group by (cond, interv); one median-logOR node per trial (round-trip ok); k>=8
    groups = defaultdict(list)
    rt_fail = 0
    for nct, lst in per_nct.items():
        if nct not in cond or nct not in interv:
            continue
        c = cond[nct]
        if c not in COND_SPECIALTY:
            continue
        lst_sorted = sorted(lst, key=lambda t: t[0])
        med = lst_sorted[len(lst_sorted) // 2]     # median-logOR row (deterministic)
        if not med[2]:
            rt_fail += 1
            continue
        groups[(c, interv[nct])].append((nct, med[0], med[1], year.get(nct), med[3]))
    print(f"CI round-trip failures dropped: {rt_fail}", flush=True)

    rows = []
    kept_groups = 0
    dropped_small = 0
    for (c, i), members in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        if len(members) < 8:
            dropped_small += 1
            continue
        kept_groups += 1
        spec, corpus_spec = COND_SPECIALTY[c]
        ma = f"aact_{c.split(',')[0].replace(' ', '')[:10]}_{i.split(',')[0].replace(' ', '')[:10]}"
        for (nct, yi, se, yr, isp) in members:
            rows.append(dict(ma=ma, family="LOR", specialty=spec, yi=yi, se=se,
                             year=(yr if yr else ""), nct=nct, condition=c, intervention=i,
                             prespecified=int(bool(isp)), corpus_specialty=corpus_spec))
    print(f"kept MAs (k>=8): {kept_groups} ; dropped (k<8): {dropped_small} ; total nodes: {len(rows)}", flush=True)
    return rows


def main():
    rows = build()
    out = HERE / "aact_coldslice_nodes.csv"
    fields = ["ma", "family", "specialty", "yi", "se", "year", "nct",
              "condition", "intervention", "prespecified", "corpus_specialty"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)
    print(f"wrote {out}")

    import pandas as pd
    df = pd.DataFrame(rows)
    print("\nper-MA summary (corpus_specialty=1 rows are in the primary cold test):")
    for ma, sub in df.groupby("ma"):
        y = sub.yi.astype(float)
        print(f"  {ma:36} k={len(sub):3} spec={sub.specialty.iloc[0]:18} "
              f"cs={sub.corpus_specialty.iloc[0]} prespec={int(sub.prespecified.sum()):2}/{len(sub):2} "
              f"logOR {y.min():+.2f}..{y.max():+.2f} (mean {y.mean():+.2f})")
    prim = df[df.corpus_specialty == 1]
    print(f"\nPRIMARY cold slice (corpus_specialty=1): {len(prim)} nodes / {prim.ma.nunique()} MAs")
    print(f"  specialties: {sorted(prim.specialty.unique())}")
    print(f"  per specialty MAs: {prim.groupby('specialty').ma.nunique().to_dict()}")
    print(f"FULL slice: {len(df)} nodes / {df.ma.nunique()} MAs")


if __name__ == "__main__":
    main()
