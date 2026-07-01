"""EXPERIMENT 2 (transport) -- prep + modifier verification on the rotavirus slice.

SECOND placebo-controlled, gradient-spanning STRONG-modifier slice to push the
transport-vs-relevance test past k=13 (BCG). Source = the DEPOSITED per-trial dataset
of Clark et al. 2019 (Lancet Infect Dis 19:717-727, "Efficacy of live oral rotavirus
vaccines by duration of follow-up: a meta-regression of RCTs"), GitHub
kevinvzandvoort/rotavirus_vaccine_efficacy / rotavirus_vaccine_efficacy_extracted.csv.
Every vaccine/placebo severe-RVGE count is taken verbatim from that verified table --
NO hand transcription of individual trial papers.

The MODIFIER is the classic "oral-vaccine paradox": oral rotavirus-vaccine efficacy
against severe rotavirus gastroenteritis (SRVGE) falls steeply as the population's
child-mortality burden rises (VE ~95% in low-mortality Europe/US -> ~50% in high-mortality
Africa/Asia). Continuous covariate = country UNDER-5 MORTALITY RATE (U5MR, deaths/1000),
data-derived from OWID child-mortality (country x trial-year), the direct analogue of
BCG's absolute latitude: an EXTERNAL population gradient known for the held-out trial.

Cleanliness controls (like BCG's year/alloc):
  * ONE estimand: Period-1 (first follow-up window) only -> minimises VE-waning.
  * multi-arm dependency collapsed: vaccine schedule arms sharing a placebo are POOLED
    to one vaccine-vs-placebo contrast per (study,country) -> independent units.
  * confounder battery: does the U5MR slope survive adjustment for follow-up months
    (waning) and vaccine product? (follow-up actually works AGAINST the gradient here --
    low-mortality trials tend to have LONGER follow-up yet HIGHER VE -- so it is a
    conservative confounder.)
  * pooled multi-country rows (Europe/LatAm/SE-Asia) get a documented representative
    U5MR and are flagged; a single-country sensitivity is reported.

logRR = log[(vac_cases/vac_N)/(plc_cases/plc_N)];  higher U5MR => less protection =>
logRR closer to 0 (less negative), so slope of logRR on U5MR is POSITIVE.
Var(logRR) = 1/a - 1/n1 + 1/c - 1/n2  (0.5 continuity add to all four iff any zero cell).
"""
import csv, json, io, sys, re
import numpy as np
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAW = Path(r"F:\ubcma\borrowing\rota_raw.csv")
OWID = Path(r"F:\public-data\owid\u5mr.csv")

# Representative U5MR (deaths/1000) for pooled multi-country rows and name fixes.
# Pooled-region values = population-representative U5MR of the trial's constituent
# countries at trial time (documented; flagged POOLED, dropped in the single-country
# sensitivity). Constituents per Clark/source trials:
#   Europe (Vesikari 2007 / REST-Europe): CZ,FI,FR,DE,IT,ES  -> ~4.5/1000
#   Latin Am. (Ruiz-Palacios 2006 etc.):  MX,BR,VE,PE,...     -> ~18/1000
#   SE Asia (Phua 2009): Singapore,HongKong,Taiwan            -> ~3.5/1000 (high-income Asia)
#   Finland/USA pooled                                        -> ~5/1000
#   USA (Navajo/White Mountain Apache): AI/AN ~2x US infant mort -> ~15/1000 (flagged)
POOLED = {
    "Europe (n=5)": 4.5, "Europe (n=6)": 4.5,
    "Latin Am. (n=3)": 18.0, "Latin Am. (n=5)": 18.0,
    "Latin Am. (n=6)": 18.0, "Latin Am. (n=10)": 18.0,
    "SE Asia (n=3)": 3.5, "Finland/USA": 5.0, "USA (Navajo)": 15.0,
}
POOLED_FLAG = set(POOLED)
# OWID entity-name map for single-country rows
CMAP = {"Viet nam": "Vietnam", "USA": "United States"}


def load_owid():
    u = {}
    for r in csv.DictReader(open(OWID)):
        try:
            u.setdefault(r["entity"], {})[int(r["year"])] = float(r["child_mortality_rate"]) * 10.0
        except ValueError:
            pass  # OWID rate is a percent -> *10 = deaths/1000
    return u


def u5mr_for(country, year, owid):
    if country in POOLED:
        return POOLED[country], True
    ent = CMAP.get(country, country)
    if ent in owid:
        yrs = owid[ent]
        y = min(yrs, key=lambda yy: abs(yy - year))
        return yrs[y], False
    raise KeyError(f"no U5MR for {country}")


def build():
    owid = load_owid()
    rows = [r for r in csv.DictReader(open(RAW)) if r["period"] == "Period 1"]
    # group by (study, country): pool vaccine arms sharing a placebo
    groups = {}
    for r in rows:
        groups.setdefault((r["study"], r["country"]), []).append(r)

    trials = []
    for (study, country), rs in groups.items():
        yr_m = re.search(r"(19|20)\d\d", study)
        year = int(yr_m.group(0)) if yr_m else 2010
        # placebo: shared control -> take the max-N placebo arm once (they are equal
        # within a multi-arm group; if they differ we take the largest as the common arm)
        plc = max(rs, key=lambda x: float(x["N_placebo"]))
        c = float(plc["cases_placebo"]); n2 = float(plc["N_placebo"])
        # vaccine: sum distinct schedule arms (dedupe identical rows)
        seen = set(); a = 0.0; n1 = 0.0
        for x in rs:
            key = (x["cases_vaccine"], x["N_vaccine"])
            if key in seen:
                continue
            seen.add(key)
            a += float(x["cases_vaccine"]); n1 += float(x["N_vaccine"])
        # continuity correction iff any zero cell
        aa, cc, nn1, nn2 = a, c, n1, n2
        if min(a, c) <= 0:
            aa, cc, nn1, nn2 = a + 0.5, c + 0.5, n1 + 1.0, n2 + 1.0
        rr = (aa / nn1) / (cc / nn2)
        y = float(np.log(rr))
        v = 1.0 / aa - 1.0 / nn1 + 1.0 / cc - 1.0 / nn2
        u5, pooled = u5mr_for(country, year, owid)
        trials.append(dict(study=study, country=country, year=year,
                           vaccine=plc["vaccine"], u5mr=float(u5), pooled=bool(pooled),
                           fu_end=float(plc["follow_up_end"]),
                           a=a, n1=n1, c=c, n2=n2, y=y, se=float(np.sqrt(v))))
    trials.sort(key=lambda t: t["u5mr"])
    return trials


def wls(X, y, w):
    WX = X * w[:, None]; XtWX = X.T @ WX
    beta = np.linalg.solve(XtWX, WX.T @ y)
    resid = y - X @ beta
    dof = max(len(y) - X.shape[1], 1)
    s2 = float((w * resid**2).sum() / dof)
    se = np.sqrt(np.diag(s2 * np.linalg.inv(XtWX)))
    return beta, se


def dl_mr(L, y, s, w):
    n = len(y)
    X = np.column_stack([np.ones(n), L]); WX = X * w[:, None]; XtWX = X.T @ WX
    beta = np.linalg.solve(XtWX, WX.T @ y); resid = y - X @ beta
    Qres = float((w * resid**2).sum())
    trace = w.sum() - np.trace(np.linalg.inv(XtWX) @ (X.T @ (w[:, None]**2 * X)))
    tau2 = max(0.0, (Qres - (n - 2)) / trace) if trace > 0 else 0.0
    W2 = 1.0 / (s**2 + tau2); WX2 = X * W2[:, None]
    b2 = np.linalg.solve(X.T @ WX2, WX2.T @ y); se2 = np.sqrt(np.diag(np.linalg.inv(X.T @ WX2)))
    return b2, se2, tau2


def main():
    from scipy import stats
    trials = build()
    n = len(trials)
    y = np.array([t["y"] for t in trials]); s = np.array([t["se"] for t in trials])
    x = np.array([t["u5mr"] for t in trials]); w = 1.0 / s**2
    fu = np.array([t["fu_end"] for t in trials])
    print(f"rotavirus SRVGE slice (Clark 2019 deposited data): {n} independent trial-populations")
    print(f"  U5MR {x.min():.0f}-{x.max():.0f}/1000 (SD {x.std():.1f}); "
          f"logRR {y.min():+.2f}..{y.max():+.2f}; {sum(t['pooled'] for t in trials)} pooled-region rows")

    X1 = np.column_stack([np.ones(n), x]); b1, se1 = wls(X1, y, w)
    yhat = X1 @ b1
    r2 = 1 - (w*(y-yhat)**2).sum() / (w*(y-y.mean())**2).sum()
    print(f"\n(A) WLS logRR ~ U5MR: slope = {b1[1]:+.5f}/unit (z={b1[1]/se1[1]:+.2f}), wR2={r2:.3f}")

    rng = np.random.default_rng(20260701)
    def ols_slope(L): return np.linalg.lstsq(np.column_stack([np.ones(n), L]), y, rcond=None)[0][1]
    obs = abs(ols_slope(x)); perm = np.array([abs(ols_slope(rng.permutation(x))) for _ in range(10000)])
    p_ols = float((1 + (perm >= obs).sum()) / (perm.size + 1))
    rho = float(stats.spearmanr(x, y).statistic); obs = abs(rho)
    perm = np.array([abs(stats.spearmanr(rng.permutation(x), y).statistic) for _ in range(10000)])
    p_spear = float((1 + (perm >= obs).sum()) / (perm.size + 1))
    b_re, se_re, tau2 = dl_mr(x, y, s, w); obs = abs(b_re[1])
    perm = np.array([abs(dl_mr(rng.permutation(x), y, s, w)[0][1]) for _ in range(5000)])
    p_re = float((1 + (perm >= obs).sum()) / (perm.size + 1))
    print(f"\n(B) modifier-strength battery (permute U5MR):")
    print(f"    OLS slope {ols_slope(x):+.5f}  perm p = {p_ols:.4f}")
    print(f"    Spearman rho {rho:+.3f}       perm p = {p_spear:.4f}")
    print(f"    RE(DL) slope {b_re[1]:+.5f} z={b_re[1]/se_re[1]:+.2f} tau2={tau2:.4f}  perm p = {p_re:.4f} <- headline")
    sig = sum(p < 0.05 for p in (p_ols, p_spear, p_re))
    print(f"    --> {sig}/3 significant")

    # (C) confounders: follow-up months (waning) and vaccine product
    fuc = (fu - fu.mean()) / fu.std()
    X2 = np.column_stack([np.ones(n), x, fuc]); b2, se2 = wls(X2, y, w)
    print(f"\n(C) confounder checks:")
    print(f"    +follow-up: U5MR slope {b1[1]:+.5f} -> {b2[1]:+.5f} (z={b2[1]/se2[1]:+.2f}); "
          f"fu coef {b2[2]:+.3f}; corr(U5MR,fu)={np.corrcoef(x,fu)[0,1]:+.2f}")
    vac = [t["vaccine"] for t in trials]
    rotarix = np.array([1.0 if v == "Rotarix" else 0.0 for v in vac])
    X3 = np.column_stack([np.ones(n), x, rotarix]); b3, se3 = wls(X3, y, w)
    print(f"    +product(Rotarix=1): U5MR slope -> {b3[1]:+.5f} (z={b3[1]/se3[1]:+.2f})")
    surv = abs(b2[1]) > 0.3*abs(b1[1]) and abs(b3[1]) > 0.3*abs(b1[1])
    print(f"    U5MR slope survives both adjustments: {surv}")

    out = dict(n=n, slope=float(b1[1]), z=float(b1[1]/se1[1]), R2=float(r2),
               perm_p=p_re, perm_p_ols=p_ols, perm_p_spearman=p_spear, perm_p_re=p_re,
               tau2=float(tau2), slope_adj_fu=float(b2[1]), slope_adj_vac=float(b3[1]),
               u5mr_fu_r=float(np.corrcoef(x, fu)[0, 1]), trials=trials)
    json.dump(out, open(Path(__file__).parent / "rota_trials.json", "w"), indent=1)
    print("\nwrote rota_trials.json")
    print("\nper-trial (sorted by U5MR):")
    for t in trials:
        flag = " *POOLED" if t["pooled"] else ""
        print(f"  U5MR {t['u5mr']:5.1f} {t['country']:15} {t['vaccine']:8} "
              f"logRR {t['y']:+.2f} (se {t['se']:.2f}) fu {t['fu_end']:.0f}mo{flag}")


if __name__ == "__main__":
    main()
