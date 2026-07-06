"""Transportability layer for the senn2013 diabetes NMA -- KNOWN-TRUTH sim.

Extends transport_nma/tnma.py: the TRANSPORTABILITY layer that was only SCOPED there
is built and truth-gated here, on the validated netmeta-parity engine nma/nma_core.py.

REAL COVARIATE (country-level):
  X_c = Diabetes prevalence (% of population ages 20-79), World Bank WDI indicator
  SH.STA.DIAB.ZS, year 2024.
  Source file: F:/WorldBankData/api_data/source_2_World Development Indicators/SH_STA_DIAB_ZS.csv
  Country codes aligned via F:/Projects/who-data-lakehouse/src/who_data_lakehouse/crosswalk.py
  (iso2 -> iso3 -> ihme_id / wb_code). Real values (2024, %):
     France 6.5, S.Africa 7.2, UK 7.4, Australia 7.4, Canada 7.7, Germany 7.8, Japan 8.1,
     Korea 9.6, Thailand 10.2, India 10.5, Brazil 10.6, China 11.9, USA 13.7, Mexico 16.4,
     Egypt 22.4, Saudi 23.1, Pakistan 31.4.

WHY a sim (pilot-3 / pilot-4 discipline): senn2013 has NO per-trial population covariate
(the pilot-4 structural wall), so a real-data transport win CANNOT be asserted. We validate
the MACHINERY on a calibrated known-truth sim built on the real senn2013 network geometry,
using REAL diabetes-prevalence values as the target populations X*.

MODEL. Each active treatment t has a placebo-relative effect that depends linearly on the
population covariate:
    d_t(X) = d_t0 + beta * (X - X_ref)            (placebo: d = 0)
d_t0 = the fitted senn2013 basic contrast (real effect sizes). Trials are ASSIGNED a country
(documented round-robin over the real-covariate spread) so each study carries a real X_study;
X_ref := mean assigned X_study, so the network's pooled estimate corresponds to X_ref.

STANDARDISATION (transport to a target population with covariate X*):
    d_t^target = d_hat_t(NMA)  +  beta_hat * (X* - X_ref)
beta_hat is DATA-DRIVEN each rep: a precision-weighted meta-regression slope of the observed
placebo-anchored contrasts (active - placebo) on (X_study - X_ref). (An oracle variant using
the true beta is also reported to separate machinery-correctness from estimation noise.)
The unstandardised NMA simply predicts d_hat_t for every target (ignores X*).

TRUTH-GATE. Sweep true modifier strength beta. Score how well each predictor recovers the
TRUE target effect d_t(X*) = d_t0 + beta*(X*-X_ref) via matched-coverage interval width
MCIW0 = 2 * q95(|pred - true|) over active treatments x reps, with a paired-bootstrap CI on
MCIW0_transport - MCIW0_unstd. Two targets: (i) target = POOL (X* = X_ref) must be INERT for
all beta; (ii) a real FAR target (Pakistan, X*=31.4) where transport should start to win once
beta is strong enough. Honest boundary expected: inert at beta=0 (no spurious win) and at
target=pool; wins only when the covariate genuinely modifies the effect AND the target is far.
"""
import io, sys
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(r"F:\ubcma")
sys.path.insert(0, str(ROOT / "nma"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, r"F:\Projects\who-data-lakehouse\src")
from nma_core import Comparison, fit_nma  # noqa: E402
from who_data_lakehouse.crosswalk import iso3_to_ihme, iso3_to_wb, iso3_to_name  # noqa: E402
# Force UTF-8 stdout only when run as a script; doing this at IMPORT time
# reassigns sys.stdout and breaks pytest's output capture ("I/O operation on
# closed file") for any test that imports this module.
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SENN = Path(r"F:\public-data\metadat\dat.senn2013.csv")
WB_DIAB = Path(r"F:\WorldBankData\api_data\source_2_World Development Indicators\SH_STA_DIAB_ZS.csv")

# iso2 (World Bank WDI file) -> iso3 (crosswalk key). Documented, for the countries used.
ISO2_TO_ISO3 = {
    "FR": "FRA", "GB": "GBR", "DE": "DEU", "US": "USA", "CA": "CAN", "AU": "AUS",
    "JP": "JPN", "IN": "IND", "MX": "MEX", "ZA": "ZAF", "BR": "BRA", "TH": "THA",
    "KR": "KOR", "SA": "SAU", "EG": "EGY", "PK": "PAK", "CN": "CHN",
}


def load_covariate():
    """Real country-level covariate X_c = diabetes prevalence (%), WB WDI 2024,
    aligned to iso3/ihme_id/wb_code via crosswalk.py."""
    df = pd.read_csv(WB_DIAB)
    d = df[(df["date"] == 2024)].dropna(subset=["value"])
    cov = {}
    for iso2, iso3 in ISO2_TO_ISO3.items():
        sub = d[d["country_id"] == iso2]
        if len(sub):
            cov[iso3] = dict(
                iso3=iso3, name=iso3_to_name(iso3), ihme_id=iso3_to_ihme(iso3),
                wb_code=iso3_to_wb(iso3), X=float(sub.iloc[0]["value"]),
            )
    return cov


def senn_contrasts():
    d = pd.read_csv(SENN)
    comps = []
    for study, g in d.groupby("study"):
        rows = g.to_dict("records")
        ref = next((r for r in rows if r["treatment"] == "placebo"), rows[0])
        for r in rows:
            if r["treatment"] == ref["treatment"]:
                continue
            te = float(r["mi"]) - float(ref["mi"])
            se = float(np.sqrt(r["sdi"] ** 2 / r["ni"] + ref["sdi"] ** 2 / ref["ni"]))
            comps.append(Comparison(str(study), r["treatment"], ref["treatment"], te, se))
    return comps


def assign_study_X(comps, cov):
    """Assign each study a real country (documented round-robin over the covariate spread),
    giving it a real X_study. NOTE: senn2013's real per-trial countries are unknown (pilot-4
    wall); this is an explicit synthetic assignment for MACHINERY validation only."""
    # spread the real-covariate range across the studies
    order = sorted(cov.values(), key=lambda e: e["X"])
    studies = sorted({c.studlab for c in comps})
    Xs = {}
    for i, s in enumerate(studies):
        e = order[i % len(order)]
        Xs[s] = e["X"]
    return Xs


def true_base_effects(comps):
    """d_t0 = fitted senn2013 basic contrast (real effect sizes)."""
    fit = fit_nma(comps, reference="placebo", random=True)
    pi = fit.treatments.index("placebo")
    d0 = {t: float(fit.TE[fit.treatments.index(t), pi]) for t in fit.treatments}
    return d0, fit


def estimate_beta(sim, Xstudy, Xref):
    """Data-driven beta_hat: precision-weighted WITHIN-TREATMENT regression of
    observed placebo-anchored (active - placebo) contrasts on (X_study - X_ref).

    The effect-modification slope must be estimated WITHIN each active treatment
    (absorbing that treatment's own placebo-relative baseline d0[t]). A single
    pooled regression across all treatments confounds between-treatment effect
    differences with the covariate slope: two treatments with different d0 that
    happen to sit at low- vs high-X studies manufacture a large beta_hat even
    when the true modifier is 0 (e.g. d0=[-2,0] over dX=1 -> beta_hat=2). The
    fixed-effects (within) estimator demeans (x, y) by each treatment's own
    precision-weighted means before pooling the cross-products, so d0[t] cancels.
    """
    by_t: dict[str, list[tuple[float, float, float]]] = {}
    for c in sim:
        # orient as active - placebo
        if c.t2 == "placebo" and c.t1 != "placebo":
            t, te = c.t1, c.te
        elif c.t1 == "placebo" and c.t2 != "placebo":
            t, te = c.t2, -c.te
        else:
            continue
        by_t.setdefault(t, []).append(
            (Xstudy[c.studlab] - Xref, te, 1.0 / c.se ** 2))
    num = 0.0
    den = 0.0
    for rows in by_t.values():
        if len(rows) < 2:
            continue  # no within-treatment X spread -> this treatment can't
            # inform the slope (its d0 would otherwise leak into it)
        x = np.array([r[0] for r in rows])
        y = np.array([r[1] for r in rows])
        w = np.array([r[2] for r in rows])
        xm = np.sum(w * x) / np.sum(w)
        ym = np.sum(w * y) / np.sum(w)   # absorbs this treatment's baseline d0[t]
        num += float(np.sum(w * (x - xm) * (y - ym)))
        den += float(np.sum(w * (x - xm) ** 2))
    if den < 1e-9:
        return 0.0
    return float(num / den)


def mciw0(errs):
    return 2.0 * float(np.quantile(np.asarray(errs), 0.95))


def truthgate(comps, d0, Xstudy, Xref, cov, beta, Xstar, reps=500, seed=1):
    """One (beta, Xstar) cell. Returns unstd/transport/oracle MCIW0 and paired-bootstrap CI
    of (transport - unstd) and (oracle - unstd)."""
    active = sorted({t for c in comps for t in (c.t1, c.t2)} - {"placebo"})
    rng = np.random.default_rng(seed)

    def dtrue(t, X):  # true placebo-relative effect at covariate X
        return (d0.get(t, 0.0) + beta * (X - Xref)) if t != "placebo" else 0.0

    e_un, e_tr, e_or = [], [], []
    for _ in range(reps):
        sim = []
        for c in comps:
            X = Xstudy[c.studlab]
            te = dtrue(c.t1, X) - dtrue(c.t2, X) + rng.normal(0, c.se)
            sim.append(Comparison(c.studlab, c.t1, c.t2, te, c.se))
        f = fit_nma(sim, reference="placebo", random=True)
        ii = {t: i for i, t in enumerate(f.treatments)}
        pi = ii["placebo"]
        beta_hat = estimate_beta(sim, Xstudy, Xref)
        for t in active:
            if t not in ii:
                continue
            d_hat = f.TE[ii[t], pi]
            true_target = d0[t] + beta * (Xstar - Xref)
            pred_un = d_hat                                   # unstandardised
            pred_tr = d_hat + beta_hat * (Xstar - Xref)       # transport (data-driven beta_hat)
            pred_or = d_hat + beta * (Xstar - Xref)           # transport (oracle beta)
            e_un.append(abs(pred_un - true_target))
            e_tr.append(abs(pred_tr - true_target))
            e_or.append(abs(pred_or - true_target))
    e_un = np.array(e_un); e_tr = np.array(e_tr); e_or = np.array(e_or)

    def paired_ci(e_alt):
        d = e_alt - e_un
        bi = rng.integers(0, len(d), size=(3000, len(d)))
        boot = np.array([2 * (np.quantile(e_alt[b], .95) - np.quantile(e_un[b], .95)) for b in bi])
        return np.quantile(boot, [.025, .975])

    lo_t, hi_t = paired_ci(e_tr)
    lo_o, hi_o = paired_ci(e_or)
    verdict = lambda lo, hi: "WINS" if hi < 0 else ("HARMS" if lo > 0 else "inert/tie")
    return dict(
        beta=beta, Xstar=Xstar, mciw0_un=mciw0(e_un),
        mciw0_tr=mciw0(e_tr), d_tr=mciw0(e_tr) - mciw0(e_un), ci_tr=(float(lo_t), float(hi_t)),
        verdict_tr=verdict(lo_t, hi_t),
        mciw0_or=mciw0(e_or), d_or=mciw0(e_or) - mciw0(e_un), ci_or=(float(lo_o), float(hi_o)),
        verdict_or=verdict(lo_o, hi_o),
    )


def main():
    cov = load_covariate()
    comps = senn_contrasts()
    d0, fit = true_base_effects(comps)
    Xstudy = assign_study_X(comps, cov)
    Xref = float(np.mean(list(Xstudy.values())))
    Xstar_pool = Xref
    Xstar_far = cov["PAK"]["X"]   # Pakistan 31.4%, real far target

    print("=" * 92)
    print("REAL COVARIATE: WB WDI SH.STA.DIAB.ZS (Diabetes prevalence %, 2024); crosswalk-aligned")
    print("=" * 92)
    print(f"  {'iso3':4}{'name':22}{'ihme_id':>8}{'wb':>5}{'diab%':>8}")
    for e in sorted(cov.values(), key=lambda e: e["X"]):
        print(f"  {e['iso3']:4}{e['name']:22}{e['ihme_id']!s:>8}{e['wb_code']:>5}{e['X']:>8.1f}")
    print(f"\n  senn2013 network: {fit.n} treatments, {fit.k} studies, tau={fit.tau:.3f}, I2={fit.I2:.0f}%")
    print(f"  assigned trial X spread: min={min(Xstudy.values()):.1f} max={max(Xstudy.values()):.1f} "
          f"X_ref(mean)={Xref:.2f}")
    print(f"  targets: POOL X*={Xstar_pool:.2f} (inert control) | FAR X*={Xstar_far:.1f} (Pakistan)")
    print("  fitted base placebo-relative effects d_t0 (MD HbA1c):")
    for t in sorted(d0, key=lambda t: d0[t]):
        if t != "placebo":
            print(f"    {t:14}{d0[t]:+.3f}")

    print("\n" + "=" * 92)
    print("TRUTH-GATE: transport-standardised vs unstandardised NMA at matched coverage (MCIW0)")
    print("  d_t^target = d_hat_t + beta_hat*(X* - X_ref);  MCIW0=2*q95(|pred-true|); paired-boot 95% CI")
    print("=" * 92)
    betas = [0.0, 0.02, 0.05, 0.10, 0.20]
    for label, Xstar in [("POOL", Xstar_pool), ("FAR ", Xstar_far)]:
        print(f"\n  --- target = {label} (X*={Xstar:.2f}) ---")
        print(f"  {'beta':>5}{'un MCIW0':>10}{'tr MCIW0':>10}{'d(tr-un)':>10}{'  95% CI':>20}{'verdict':>11}"
              f"{'  | oracle d':>12}{'oracle CI':>20}{'ver':>10}")
        for b in betas:
            r = truthgate(comps, d0, Xstudy, Xref, cov, beta=b, Xstar=Xstar, reps=500, seed=7)
            print(f"  {b:>5.2f}{r['mciw0_un']:>10.4f}{r['mciw0_tr']:>10.4f}{r['d_tr']:>+10.4f}"
                  f"  [{r['ci_tr'][0]:+.4f},{r['ci_tr'][1]:+.4f}]{r['verdict_tr']:>11}"
                  f"  |{r['d_or']:>+10.4f}  [{r['ci_or'][0]:+.4f},{r['ci_or'][1]:+.4f}]{r['verdict_or']:>10}")


if __name__ == "__main__":
    main()
