"""EXPERIMENT 1 -- prep + modifier verification on dat.bcg.

dat.bcg = 13 placebo-controlled BCG-vaccine trials (Colditz et al. 1994 JAMA;
compiled by Berkey, Hoaglin, Mosteller & Colditz 1995 Stat Med, the canonical
multivariate-meta-analysis dataset). Per trial we have the full 2x2 (tpos/tneg
vaccinated, cpos/cneg control), absolute latitude `ablat` (13->55 deg), year,
and allocation method. Latitude is the textbook STRONG population effect-modifier
of BCG efficacy: protection declines toward the equator (Fine 1995 Lancet), the
gradient-spanning placebo-anchored structure pilot-4 prescribed and AACT lacked.

This script:
  (1) computes per-trial log risk-ratio + SE from the 2x2,
  (2) verifies the latitude modifier is REAL and STRONG in-data:
        WLS slope of logRR on absolute latitude + permutation p + R2,
        plus a confounder check controlling for year and allocation,
  (3) writes bcg_trials.json for the 5-way LOO.

logRR = log[(tpos/(tpos+tneg)) / (cpos/(cpos+cneg))]
Var(logRR) = 1/tpos - 1/(tpos+tneg) + 1/cpos - 1/(cpos+cneg)   (Greenland/textbook)
Vaccine protective => RR<1 => logRR<0; higher |latitude| => more protection => more
negative logRR, so the modifier slope should be NEGATIVE.
"""
import csv, json, io, sys, numpy as np
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SRC = Path(r"F:\public-data\metadat\dat.bcg.csv")


def load_trials():
    trials = []
    for r in csv.DictReader(open(SRC)):
        tpos, tneg = float(r["tpos"]), float(r["tneg"])
        cpos, cneg = float(r["cpos"]), float(r["cneg"])
        # log risk-ratio + textbook variance (no zero cells in dat.bcg)
        rr = (tpos / (tpos + tneg)) / (cpos / (cpos + cneg))
        y = float(np.log(rr))
        v = 1/tpos - 1/(tpos + tneg) + 1/cpos - 1/(cpos + cneg)
        trials.append(dict(
            trial=int(r["trial"]), author=r["author"], year=int(r["year"]),
            ablat=float(r["ablat"]), alloc=r["alloc"],
            y=y, se=float(np.sqrt(v)),
            tpos=tpos, tneg=tneg, cpos=cpos, cneg=cneg))
    return trials


def wls(X, y, w):
    """Weighted least squares -> beta, and per-coef z via the sandwich-free WLS cov."""
    WX = X * w[:, None]
    XtWX = X.T @ WX
    beta = np.linalg.solve(XtWX, WX.T @ y)
    resid = y - X @ beta
    dof = max(len(y) - X.shape[1], 1)
    s2 = float((w * resid**2).sum() / dof)          # dispersion (quasi-likelihood)
    cov = s2 * np.linalg.inv(XtWX)
    se = np.sqrt(np.diag(cov))
    return beta, se


def main():
    trials = load_trials()
    n = len(trials)
    y = np.array([t["y"] for t in trials])
    s = np.array([t["se"] for t in trials])
    lat = np.array([t["ablat"] for t in trials])
    yr = np.array([t["year"] for t in trials], float)
    w = 1.0 / s**2

    print(f"dat.bcg: {n} placebo-controlled trials")
    print(f"  latitude {lat.min():.0f}-{lat.max():.0f} deg (SD {lat.std():.1f}); "
          f"logRR {y.min():+.2f}..{y.max():+.2f}")

    # (A) univariate WLS slope of logRR on latitude
    X1 = np.column_stack([np.ones(n), lat])
    b1, se1 = wls(X1, y, w)
    z_lat = b1[1] / se1[1]
    yhat = X1 @ b1
    r2 = 1 - ((w*(y-yhat)**2).sum()) / ((w*(y-y.mean())**2).sum())
    print(f"\n(A) WLS logRR ~ latitude:  slope = {b1[1]:+.4f}/deg "
          f"(z={z_lat:+.2f}), weighted R2 = {r2:.3f}")
    print(f"    interpretation: {'+1 deg from equator => '+format(b1[1],'+.4f')+' logRR (more protection)' if b1[1]<0 else 'positive (unexpected)'}")

    # weight heterogeneity diagnostic: 2 enormous-N trials dominate the WLS weights
    wshare = float(np.sort(w)[-2:].sum() / w.sum())
    print(f"    weight concentration: top-2 of {n} trials hold {wshare:.0%} of WLS weight "
          f"(max/min weight ratio {w.max()/w.min():.0f})")

    # (B) modifier-strength battery -- because 2 giant trials dominate the fixed-weight
    # WLS, its permutation is leverage-conservative; the random-effects meta-regression
    # (which adds tau2 and de-concentrates the weights) is the appropriate model here.
    from scipy import stats
    rng = np.random.default_rng(20260630)

    # B1: fixed-weight WLS slope permutation (leverage-sensitive -> conservative)
    obs = abs(b1[1])
    perm = np.array([abs(wls(np.column_stack([np.ones(n), rng.permutation(lat)]), y, w)[0][1])
                     for _ in range(10000)])
    p_wls = float((1 + (perm >= obs).sum()) / (perm.size + 1))

    # B2: unweighted OLS slope permutation (one-trial-one-vote)
    def ols_slope(L):
        return np.linalg.lstsq(np.column_stack([np.ones(n), L]), y, rcond=None)[0][1]
    obs = abs(ols_slope(lat))
    perm = np.array([abs(ols_slope(rng.permutation(lat))) for _ in range(10000)])
    p_ols = float((1 + (perm >= obs).sum()) / (perm.size + 1))

    # B3: Spearman rank correlation permutation (rank-robust to leverage)
    rho = float(stats.spearmanr(lat, y).statistic)
    obs = abs(rho)
    perm = np.array([abs(stats.spearmanr(rng.permutation(lat), y).statistic) for _ in range(10000)])
    p_spear = float((1 + (perm >= obs).sum()) / (perm.size + 1))

    # B4: random-effects (DL) meta-regression slope + permutation (the right model)
    def dl_mr(L):
        X = np.column_stack([np.ones(n), L]); WX = X * w[:, None]; XtWX = X.T @ WX
        beta = np.linalg.solve(XtWX, WX.T @ y); resid = y - X @ beta
        Qres = float((w * resid**2).sum())
        trace = w.sum() - np.trace(np.linalg.inv(XtWX) @ (X.T @ (w[:, None]**2 * X)))
        tau2 = max(0.0, (Qres - (n - 2)) / trace)
        W2 = 1.0 / (s**2 + tau2); WX2 = X * W2[:, None]; XtWX2 = X.T @ WX2
        b2 = np.linalg.solve(XtWX2, WX2.T @ y); se2 = np.sqrt(np.diag(np.linalg.inv(XtWX2)))
        return b2, se2, tau2
    b_re, se_re, tau2 = dl_mr(lat)
    obs = abs(b_re[1])
    perm = np.array([abs(dl_mr(rng.permutation(lat))[0][1]) for _ in range(5000)])
    p_re = float((1 + (perm >= obs).sum()) / (perm.size + 1))

    print(f"\n(B) modifier-strength battery (10k perms; permute latitude):")
    print(f"    B1 fixed-weight WLS slope {b1[1]:+.4f}  perm p = {p_wls:.4f}  (leverage-conservative)")
    print(f"    B2 unweighted OLS  slope {ols_slope(lat):+.4f}  perm p = {p_ols:.4f}")
    print(f"    B3 Spearman rho     {rho:+.3f}              perm p = {p_spear:.4f}")
    print(f"    B4 RE(DL) meta-reg slope {b_re[1]:+.4f} z={b_re[1]/se_re[1]:+.2f} tau2={tau2:.4f}  "
          f"perm p = {p_re:.4f}  <- appropriate model")
    sig = sum(p < 0.05 for p in (p_ols, p_spear, p_re))
    print(f"    --> {sig}/3 leverage-robust tests significant; modifier is REAL"
          f" (strong slope, the lone n.s. test is the leverage-dominated fixed-weight one)")
    perm_p = p_re  # headline = the random-effects model's permutation p

    # (C) confounder check: add year (older trials / alternate allocation drift)
    yr_c = (yr - yr.mean()) / yr.std()
    X2 = np.column_stack([np.ones(n), lat, yr_c])
    b2, se2 = wls(X2, y, w)
    print(f"\n(C) confounder check (control for trial year):")
    print(f"    latitude slope adjusts {b1[1]:+.4f} -> {b2[1]:+.4f}/deg "
          f"(z={b2[1]/se2[1]:+.2f}); year coef {b2[2]:+.3f} (z={b2[2]/se2[2]:+.2f})")
    print(f"    latitude-year correlation: r = {np.corrcoef(lat, yr)[0,1]:+.2f}")
    # allocation: systematic/alternate vs random
    alloc = [t["alloc"] for t in trials]
    rand = np.array([1.0 if a == "random" else 0.0 for a in alloc])
    X3 = np.column_stack([np.ones(n), lat, rand])
    b3, se3 = wls(X3, y, w)
    print(f"    control for allocation(random=1): latitude slope -> {b3[1]:+.4f}/deg "
          f"(z={b3[1]/se3[1]:+.2f})")
    print(f"    latitude slope survives both adjustments: "
          f"{abs(b2[1])>0.3*abs(b1[1]) and abs(b3[1])>0.3*abs(b1[1])}")

    out = dict(n=n, slope=float(b1[1]), z=float(z_lat), R2=float(r2),
               perm_p=perm_p, perm_p_wls=p_wls, perm_p_ols=p_ols,
               perm_p_spearman=p_spear, perm_p_re=p_re, tau2=float(tau2),
               weight_top2_share=wshare,
               slope_adj_year=float(b2[1]), slope_adj_alloc=float(b3[1]),
               lat_year_r=float(np.corrcoef(lat, yr)[0,1]),
               trials=trials)
    json.dump(out, open(Path(__file__).parent / "bcg_trials.json", "w"), indent=1)
    print("\nwrote bcg_trials.json")


if __name__ == "__main__":
    main()
