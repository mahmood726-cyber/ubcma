"""PILOT-3 data prep: join the real T2DM HbA1c trial slice to POPULATION
covariates, so we can test TRANSPORTABILITY (standardise borrowed evidence to a
target population + down-weight trials that don't transport).

Sources (all on-disk, real):
  * probe_trials.json     -- the pilot-2 effect slice (y, se, class, baseline, dose)
  * AACT countries.txt    -- trial -> set of recruiting countries (real)
  * World Bank            -- per-country ADULT OBESITY prevalence (SH.STA.OB18, BMI>30,
                            mean of male+female) = the mechanistic effect-modifier axis
                            (East-Asian low-adiposity T2DM phenotype) + diabetes prev.

Population covariate for a trial = mean of its recruiting countries' obesity
prevalence (over countries with WB coverage). Single-country trials give clean
population anchors (the transport-relevant targets). Writes trials_transport.json.
"""
from __future__ import annotations
import csv, json
from collections import defaultdict
from pathlib import Path

WB = Path("F:/WorldBankData/api_data")
AACT_COUNTRIES = Path("F:/AACT-storage/AACT/2026-04-12/countries.txt")


def load_wb(path):
    """Latest non-null value per country_name."""
    best = {}
    for r in csv.DictReader(open(path, encoding="utf-8-sig")):
        v = r["value"]
        if not v:
            continue
        try:
            yr = int(r["date"]); val = float(v)
        except ValueError:
            continue
        nm = r["country_name"]
        if nm not in best or yr > best[nm][0]:
            best[nm] = (yr, val)
    return {k: v[1] for k, v in best.items()}


# AACT country names use a few aliases vs World Bank names
ALIAS = {
    "South Korea": "Korea, Rep.", "Russia": "Russian Federation",
    "Slovakia": "Slovak Republic", "Taiwan": None, "Hong Kong": "Hong Kong SAR, China",
    "Puerto Rico": None, "Czech Republic": "Czechia", "Turkey": "Turkiye",
}


def wb_lookup(d, country):
    if country in d:
        return d[country]
    a = ALIAS.get(country, country)
    if a and a in d:
        return d[a]
    return None


def require_covariate_join(records):
    """Fail closed if the population-covariate join produced ZERO pop_ob values.

    A wholesale WB-obesity join failure (missing files, changed country keys)
    leaves every record's pop_ob None. Persisting that all-null
    trials_transport.json would silently corrupt every downstream consumer —
    sim_transport / the truthgate filter `pop_ob is not None` and then crash on
    the empty result. Validate BEFORE writing so the bad state never lands.
    """
    if not any(r.get("pop_ob") is not None for r in records):
        raise ValueError(
            "covariate join produced zero pop_ob values (WB obesity data "
            "missing/unjoined) — refusing to write an all-null "
            "trials_transport.json")


def _build_records(trials, tc, OBES, DIAB):
    out = []
    for nct, t in trials.items():
        countries = tc.get(nct, [])
        ob_vals = [v for v in (wb_lookup(OBES, c) for c in countries) if v is not None]
        db_vals = [v for v in (wb_lookup(DIAB, c) for c in countries) if v is not None]
        base = t.get("baseline")
        if base is not None and base < 4.0:   # 0.0 / <4 = missing-coded baseline HbA1c
            base = None
        out.append(dict(
            nct_id=nct, active=t["active"], y=t["y"], se=t["se"],
            baseline=base, dose=t.get("dose") if (t.get("dose") or 0) > 0 else None,
            enroll=t.get("enroll"), year=t.get("year"),
            countries=countries, n_countries=len(countries),
            pop_ob=(sum(ob_vals) / len(ob_vals)) if ob_vals else None,
            pop_db=(sum(db_vals) / len(db_vals)) if db_vals else None,
            single_country=(len(countries) == 1),
            target_country=countries[0] if len(countries) == 1 else None,
        ))
    return out


if __name__ == "__main__":
    # population covariates
    fe = load_wb(WB / "source_14_Gender Statistics/SH_STA_OB18_FE_ZS.csv")
    ma = load_wb(WB / "source_14_Gender Statistics/SH_STA_OB18_MA_ZS.csv")
    OBES = {k: (fe[k] + ma[k]) / 2 for k in fe if k in ma}
    DIAB = load_wb(WB / "source_2_World Development Indicators/SH_STA_DIAB_ZS.csv")

    # trial -> countries (rebuild straight from AACT for reproducibility)
    trials = {t["nct_id"]: t for t in json.load(open("probe_trials.json"))}
    tc = defaultdict(list)
    for line in open(AACT_COUNTRIES, encoding="utf-8", errors="replace"):
        parts = line.rstrip("\n").split("|")
        if len(parts) < 4:
            continue
        _id, nct, name, removed = parts[0], parts[1], parts[2], parts[3]
        if nct in trials and removed == "f":
            tc[nct].append(name)

    out = _build_records(trials, tc, OBES, DIAB)

    # Validate the covariate join BEFORE persisting (fail closed on total failure).
    require_covariate_join(out)

    json.dump(out, open("trials_transport.json", "w"), indent=2)
    have_ob = [r for r in out if r["pop_ob"] is not None]
    single = [r for r in out if r["single_country"] and r["pop_ob"] is not None]
    print(f"trials total          : {len(out)}")
    print(f"with pop_ob covariate : {len(have_ob)}")
    print(f"single-country anchors: {len(single)}")
    obs = sorted(r["pop_ob"] for r in have_ob)
    print(f"pop_ob range          : [{obs[0]:.1f}, {obs[-1]:.1f}] %  median {obs[len(obs)//2]:.1f}")
    print("single-country targets:")
    for r in sorted(single, key=lambda r: r["pop_ob"]):
        print(f"  {r['nct_id']:13} {r['target_country'][:14]:15} {r['active']:8} "
              f"ob={r['pop_ob']:5.1f}  y={r['y']:+.2f} se={r['se']:.3f} "
              f"dose={r['dose']}  base={r['baseline']}")
    print("wrote trials_transport.json")
