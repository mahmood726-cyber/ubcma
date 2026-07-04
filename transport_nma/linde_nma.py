"""SECOND REAL NETWORK — generalisation test of the transportable-NMA + registry-pub-bias method.

The head-to-head and external-magnitude results were established on the diabetes HbA1c network
(dat.senn2013). This applies the SAME method end-to-end to a second, independent real network in a
different domain and on a different effect scale:

  dat.linde2015 (metadat) — 66 antidepressant RCTs for major depression, arms already grouped by
  CLASS (SSRI / SNRI / TCA / NaSSa+SARI=atypical / rMAO-A=MAOI / NRI / Hypericum / Placebo).
  Outcome = treatment RESPONSE (responders / n) -> pairwise log-ODDS-RATIO contrasts -> fit_nma
  (netmeta-parity engine; multi-arm handled by the study-block covariance).

Registry overlay: per-class results-reporting integrity lambda for DEPRESSION trials (loaded from
aact_kappa_depression_std.json, computed on the AACT 2026-04-12 snapshot). Correction shrinks each
active class's placebo-relative log-OR toward the null by kappa*(1-lambda_t).

Truth-gate (linde geometry, injected bias B*(1-lambda) on active arms): does the registry correction
recover the true log-ORs better than the unadjusted NMA at matched coverage, and does the DIABETES-
frozen external magnitude (kappa_pooled=0.158) TRANSFER to correct a second domain? Head-to-head vs
the internal funnel selection models, exactly as on senn2013. Truth-first: honest verdict.
"""
import json, io, sys
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "nma"))
sys.path.insert(0, str(ROOT / "src"))
from nma_core import Comparison, fit_nma, p_score  # noqa: E402
from ubcma.robust_methods import pet_fit  # noqa: E402
from scipy.stats import rankdata  # noqa: E402
if "pytest" not in sys.modules:
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

LINDE = Path(r"F:\public-data\metadat\dat.linde2015.csv")
Z975 = 1.959963984540054
DEP = json.load(open(HERE / "aact_kappa_depression_std.json"))["z"]   # per-class lam (+ kappa)
K_DIAB = float(json.load(open(HERE / "aact_kappa_frozen.json"))["kappa_pooled"])  # 0.158, domain-1 frozen

# linde treatment label -> our AACT antidepressant class (None = leave unadjusted)
TREAT_CLASS = {
    "SSRI": "SSRI", "SNRI": "SNRI", "TCA": "TCA",
    "NaSSa": "atypical", "Low-dose SARI": "atypical", "rMAO-A": "MAOI",
    "NRI": None, "Hypericum": None, "Placebo": None,
}


def lam(t):
    c = TREAT_CLASS.get(t)
    if c is None or c not in DEP:
        return 1.0
    v = DEP[c].get("lam")
    return float(v) if v else 1.0


def linde_contrasts():
    """All pairwise response log-OR contrasts per study (0.5 continuity correction on zero cells)."""
    d = pd.read_csv(LINDE)
    comps = []
    for _, row in d.iterrows():
        arms = []
        for k in (1, 2, 3):
            tr = row.get(f"treatment{k}")
            n = row.get(f"n{k}")
            r = row.get(f"resp{k}")
            if isinstance(tr, str) and pd.notna(n) and pd.notna(r):
                arms.append((tr, float(n), float(r)))
        if len(arms) < 2:
            continue
        # continuity correction if any zero/one-boundary cell in this study
        cc = 0.0
        for _, n, r in arms:
            if r <= 0 or r >= n:
                cc = 0.5
                break
        logit = {}
        for tr, n, r in arms:
            a = r + cc
            b = (n - r) + cc
            logit[tr] = (np.log(a / b), 1.0 / a + 1.0 / b)  # (log-odds, var)
        ref = arms[0][0]
        for tr, _, _ in arms[1:]:
            te = logit[tr][0] - logit[ref][0]
            se = float(np.sqrt(logit[tr][1] + logit[ref][1]))
            comps.append(Comparison(str(row["id"]), tr, ref, te, se))
    return comps


def real_demo():
    print("=" * 78)
    print("(A) REAL depression NMA on dat.linde2015 (response log-OR) + registry lambda overlay")
    print("=" * 78)
    comps = linde_contrasts()
    fit = fit_nma(comps, reference="Placebo", random=True)
    ps = p_score(fit, small_values="undesirable")   # higher log-OR (more response) = desirable
    ti = {t: i for i, t in enumerate(fit.treatments)}
    ref = ti["Placebo"]
    print(f"  network: {fit.n} treatments, {fit.k} studies, {fit.m} contrasts; tau={fit.tau:.3f}, I2={fit.I2:.0f}%")
    print(f"  {'treatment':14}{'lnOR vs plac':>13}{'seTE':>7}{'OR':>7}{'pscore':>8}{'class':>10}{'lambda':>7}{'reg-adj OR':>11}")
    for t in sorted(fit.treatments, key=lambda x: -fit.TE[ti[x], ref]):
        if t == "Placebo":
            continue
        lo = fit.TE[ti[t], ref]; se = fit.seTE[ti[t], ref]
        lo_adj = lo * (1.0 - 0.5 * (1.0 - lam(t)))
        print(f"  {t:14}{lo:>+13.3f}{se:>7.3f}{np.exp(lo):>7.2f}{ps[t]:>8.3f}"
              f"{str(TREAT_CLASS.get(t)):>10}{lam(t):>7.2f}{np.exp(lo_adj):>11.2f}")
    print("  (higher OR = more responders vs placebo; reg-adj shrinks low-lambda classes toward OR=1)")
    return comps


# ---- internal funnel bias estimators (same as h2h_bench, condensed) ----
def _re_mean(y, se):
    w = 1.0 / np.square(se); mu = np.sum(w * y) / np.sum(w)
    Q = np.sum(w * (y - mu) ** 2); c = np.sum(w) - np.sum(w ** 2) / np.sum(w)
    tau2 = max(0.0, (Q - (len(y) - 1)) / c) if c > 1e-12 else 0.0
    wr = 1.0 / (np.square(se) + tau2); return float(np.sum(wr * y) / np.sum(wr))


def _fe_mean(y, se):
    w = 1.0 / np.square(se); return float(np.sum(w * y) / np.sum(w))


def _trimfill(y, se):
    y = np.asarray(y, float); se = np.asarray(se, float); k = len(y)
    if k < 3:
        return _fe_mean(y, se)
    mu = _fe_mean(y, se); L0 = 0
    for _ in range(30):
        d = y - mu
        if np.allclose(d, 0):
            break
        r = rankdata(np.abs(d)); s = np.sign(d) * r
        Tp = s[s > 0].sum(); Tn = -s[s < 0].sum()
        side = 1.0 if Tp >= Tn else -1.0; Tn_ = Tp if side > 0 else Tn
        L = int(max(0, round((4 * Tn_ - k * (k + 1)) / (2 * k - 1.0))))
        if L == L0:
            break
        L0 = L; idx = np.argsort(-side * d); mu = _fe_mean(y[idx[L0:]], se[idx[L0:]]) if L0 < k else mu
    if L0 > 0:
        d = y - mu; r = rankdata(np.abs(d)); s = np.sign(d) * r
        side = 1.0 if s[s > 0].sum() >= -s[s < 0].sum() else -1.0
        idx = np.argsort(-side * (y - mu))[:L0]
        yf = 2 * mu - y[idx]
        return _fe_mean(np.concatenate([y, yf]), np.concatenate([se, se[idx]]))
    return mu


def internal_bias(y, se, method, mk):
    y = np.asarray(y, float); se = np.asarray(se, float)
    if len(y) < mk:
        return 0.0, False
    naive = _re_mean(y, se)
    b0 = pet_fit(y, se)["b0"] if method == "PET" else (_trimfill(y, se) if method == "TF" else _fe_mean(y, se))
    return float(naive - b0), True


def truthgate(comps, B, reps=400, seed=1, boot=3000):
    treats = sorted({t for c in comps for t in (c.t1, c.t2)})
    fit0 = fit_nma(comps, reference="Placebo", random=True)
    pi = fit0.treatments.index("Placebo")
    true_d = {t: (fit0.TE[fit0.treatments.index(t), pi] if t in fit0.treatments else 0.0) for t in treats}
    active = [t for t in treats if t != "Placebo"]
    direct = {t: [] for t in active}
    for i, c in enumerate(comps):
        pr = {c.t1, c.t2}
        if "Placebo" in pr and len(pr) == 2:
            o = (pr - {"Placebo"}).pop()
            if o in direct:
                direct[o].append(i)
    rng = np.random.default_rng(seed)
    meth = ["registry_oracle", "registry_extdiab0.158", "registry_fix0.5", "PET", "TF", "HC"]
    err = {m: [] for m in meth}; eu = []
    for _ in range(reps):
        sim = []
        for c in comps:
            def obs(t):
                return 0.0 if t == "Placebo" else true_d.get(t, 0.0) * (1.0 + B * (1.0 - lam(t)))
            sim.append(Comparison(c.studlab, c.t1, c.t2, obs(c.t1) - obs(c.t2) + rng.normal(0, c.se), c.se))
        f = fit_nma(sim, reference="Placebo", random=True)
        ii = {t: i for i, t in enumerate(f.treatments)}
        if "Placebo" not in ii:
            continue
        ref = ii["Placebo"]
        for t in active:
            if t not in ii:
                continue
            md = f.TE[ii[t], ref]; tru = true_d.get(t, 0.0); s = 1.0 - lam(t)
            eu.append(abs(md - tru))
            err["registry_oracle"].append(abs(md * (1.0 - B * s) - tru))
            err["registry_extdiab0.158"].append(abs(md * (1.0 - K_DIAB * s) - tru))
            err["registry_fix0.5"].append(abs(md * (1.0 - 0.5 * s) - tru))
            yd = np.array([sim[i].te for i in direct[t]]); sd = np.array([sim[i].se for i in direct[t]])
            for m, mk in (("PET", 3), ("TF", 3), ("HC", 2)):
                b, _ = internal_bias(yd, sd, m, mk)
                err[m].append(abs((md - b) - tru))
    eu = np.array(eu)
    mc = lambda e: 2.0 * np.quantile(np.asarray(e), 0.95)
    bi = rng.integers(0, len(eu), size=(boot, len(eu)))
    rows = {"unadjusted": dict(mciw0=mc(eu), dmciw0=0.0, ci=[0.0, 0.0], verdict="-")}
    for m in meth:
        e = np.array(err[m])
        mb = np.array([2.0 * (np.quantile(e[b], .95) - np.quantile(eu[b], .95)) for b in bi])
        loq, hiq = np.quantile(mb, [.025, .975])
        v = "WINS" if hiq < 0 else ("HARMS" if loq > 0 else "tie")
        rows[m] = dict(mciw0=mc(e), dmciw0=mc(e) - mc(eu), ci=[float(loq), float(hiq)], verdict=v)
    return dict(B=B, mciw0_un=mc(eu), rows=rows, n_cells=len(eu))


def main():
    comps = real_demo()
    print("\n" + "=" * 78)
    print("(B) TRUTH-GATE on the linde2015 geometry (2nd real network; injected B*(1-lambda))")
    print("=" * 78)
    print(f"  registry correction vs unadjusted NMA at matched coverage (MCIW0). Deployable magnitudes:")
    print(f"  registry_extdiab0.158 = the DIABETES-frozen external kappa applied to a DEPRESSION network")
    print(f"  (cross-domain transfer test); oracle=upper bound; fixed 0.5=naive.")
    res = []
    for B in (0.0, 0.15, 0.30):
        r = truthgate(comps, B)
        print(f"\n  B={B:.2f}  (unadj MCIW0={r['mciw0_un']:.4f}, {r['n_cells']} cells)")
        print(f"  {'method':22}{'MCIW0':>9}{'dMCIW0':>10}{'  95% CI':>22}{'verdict':>9}")
        for m in ["unadjusted", "registry_oracle", "registry_extdiab0.158", "registry_fix0.5", "PET", "TF", "HC"]:
            x = r["rows"][m]; ci = f"[{x['ci'][0]:+.4f},{x['ci'][1]:+.4f}]"
            print(f"  {m:22}{x['mciw0']:>9.4f}{x['dmciw0']:>+10.4f}{ci:>22}{x['verdict']:>9}")
        res.append(r)
    json.dump({"network": "linde2015", "sweep": res, "k_diab": K_DIAB}, open(HERE / "linde_nma_result.json", "w"), indent=1)
    print("\nwrote linde_nma_result.json")


if __name__ == "__main__":
    main()
