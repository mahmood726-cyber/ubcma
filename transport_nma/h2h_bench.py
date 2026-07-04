"""Head-to-head TRUTH-FIRST benchmark: EXTERNAL registry-lambda pub-bias correction
vs INTERNAL funnel-based selection models (PET/Egger, trim-and-fill, Henmi-Copas),
on the tnma senn2013 known-truth sim.

Read-only use of repo code:
  nma/nma_core.py            -> fit_nma (netmeta-parity engine)
  src/ubcma/robust_methods   -> pet_fit (PET/Egger WLS), henmi_copas (metafor::hc port)
  borrowing/class_lambda.json-> per-class registry integrity lambda

Two sim regimes are scored (see VERDICT in report):
  Sim A  (tnma AS-IS): registry non-reporting injects a UNIFORM multiplicative bias
         d_obs = d_true*(1 + B*(1-lam_t)) on active arms. This bias is ORTHOGONAL to
         study SE -> invisible to a funnel plot. Tests: can the internal funnel methods
         see registry non-reporting at all?
  Sim B  (fair funnel): SAME total per-treatment bias magnitude B*(1-lam_t)*|d_true|,
         but distributed as a classic SMALL-STUDY EFFECT (per-study bias proportional
         to that study's SE). Now the selection IS funnel-visible and PET is correctly
         specified. Tests: does external registry still beat/tie the internal funnel
         methods when the bias genuinely shows up as funnel asymmetry?

Scoring = MCIW0 (2 * 95th pct of |estimate - truth|) over all (rep x active-treatment)
cells; paired bootstrap CI on delta-MCIW0 vs the common UNADJUSTED NMA baseline.

All internal correctors are applied NETWORK-CONSISTENTLY: each estimates a per-treatment
bias from the DIRECT placebo-relative study contrasts, and that bias is subtracted from
the SAME NMA league estimate the registry method adjusts. So every method starts from the
identical network point estimate md_t and differs ONLY in how it estimates the bias
(external lambda vs internal funnel). This is the fair apples-to-apples comparison.
"""
import json, io, sys
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import rankdata

ROOT = Path(r"F:\ubcma")
sys.path.insert(0, str(ROOT / "nma"))
sys.path.insert(0, str(ROOT / "src"))
from nma_core import Comparison, fit_nma            # noqa: E402
from ubcma.robust_methods import pet_fit, henmi_copas  # noqa: E402
if "pytest" not in sys.modules:      # module-level stdout re-wrap kills pytest capture
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

SENN = Path(r"F:\public-data\metadat\dat.senn2013.csv")
LAMBDA = json.load(open(ROOT / "borrowing" / "class_lambda.json"))
# frozen deployable external magnitude (AACT registered-vs-published gap; aact_kappa_frozen.json)
try:
    K_POOL_EXT = float(json.load(open(Path(__file__).resolve().parent / "aact_kappa_frozen.json"))["kappa_pooled"])
except Exception:
    K_POOL_EXT = 0.158
TREAT_CLASS = {
    "metformin": "metformin", "sitagliptin": "DPP4", "vildagliptin": "DPP4",
    "sulfonylurea": "SU", "pioglitazone": "TZD", "rosiglitazone": "TZD",
    "acarbose": "AGI", "miglitol": "AGI", "benfluorex": None, "placebo": None,
}


def lam(t):
    c = TREAT_CLASS.get(t)
    return float(LAMBDA[c]) if c in LAMBDA else 1.0


def senn_contrasts():
    d = pd.read_csv(SENN); comps = []
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


# ---------------------------------------------------------------------------
# Internal funnel-based bias estimators (operate on direct placebo-relative
# study contrasts for one treatment; return an estimate of the bias in the
# naive direct RE/FE effect, to be subtracted from the network estimate).
# ---------------------------------------------------------------------------

def _re_mean(y, se):
    w = 1.0 / np.square(se)
    mu_fe = np.sum(w * y) / np.sum(w)
    Q = np.sum(w * (y - mu_fe) ** 2)
    c = np.sum(w) - np.sum(w ** 2) / np.sum(w)
    tau2 = max(0.0, (Q - (len(y) - 1)) / c) if c > 1e-12 else 0.0
    wr = 1.0 / (np.square(se) + tau2)
    return float(np.sum(wr * y) / np.sum(wr))


def _fe_mean(y, se):
    w = 1.0 / np.square(se)
    return float(np.sum(w * y) / np.sum(w))


def trimfill_mean(y, se):
    """Duval & Tweedie (2000) trim-and-fill, L0 estimator, FE center.
    Returns the funnel-symmetry-adjusted pooled mean. Robust to effect sign."""
    y = np.asarray(y, float); se = np.asarray(se, float)
    k = len(y)
    if k < 3:
        return _fe_mean(y, se)
    yy, ss = y.copy(), se.copy()
    mu = _fe_mean(yy, ss)
    L0 = 0
    for _ in range(30):
        d = yy - mu
        if np.allclose(d, 0):
            break
        r = rankdata(np.abs(d))
        signed = np.sign(d) * r
        # dominant (over-represented) side = sign of the signed-rank sum
        Tn_pos = signed[signed > 0].sum()
        Tn_neg = -signed[signed < 0].sum()
        side = 1.0 if Tn_pos >= Tn_neg else -1.0      # missing studies on the OTHER side
        Tn = Tn_pos if side > 0 else Tn_neg
        L0_new = (4.0 * Tn - k * (k + 1)) / (2.0 * k - 1.0)
        L0_new = int(max(0, round(L0_new)))
        if L0_new == L0:
            break
        L0 = L0_new
        # trim the L0 most extreme studies on the dominant side, recompute center
        idx = np.argsort(-side * d)          # most extreme on dominant side first
        keep = idx[L0:] if L0 < k else idx
        mu = _fe_mean(yy[keep], ss[keep])
    # fill: mirror the L0 dominant-side extremes about mu, recompute on full set
    if L0 > 0:
        d = y - mu
        r = rankdata(np.abs(d)); signed = np.sign(d) * r
        side = 1.0 if signed[signed > 0].sum() >= -signed[signed < 0].sum() else -1.0
        idx = np.argsort(-side * (y - mu))
        fill_src = idx[:L0]
        y_fill = 2.0 * mu - y[fill_src]
        se_fill = se[fill_src]
        yall = np.concatenate([y, y_fill]); sall = np.concatenate([se, se_fill])
        return _fe_mean(yall, sall)
    return mu


def internal_bias(y, se, method, min_k):
    """Estimate of the bias in the naive direct effect via an internal funnel model.
    bias = (naive direct RE mean) - (bias-corrected direct estimate).
    Returns (bias, applied?) where applied=False => not enough direct studies."""
    y = np.asarray(y, float); se = np.asarray(se, float)
    if len(y) < min_k:
        return 0.0, False
    naive = _re_mean(y, se)
    if method == "PET":
        b0 = pet_fit(y, se)["b0"]
    elif method == "TF":
        b0 = trimfill_mean(y, se)
    elif method == "HC":
        # Henmi-Copas point estimate IS the fixed-effect IV mean (down-weights the
        # small, most-selected studies) -- see henmi_copas() docstring; beta = FE mean.
        # The full metafor::hc integration only computes the CI multiplier u0, which we
        # do not score here (MCIW0 is a point-recovery metric), so we use the cheap
        # closed-form FE point directly (verified identical to henmi_copas()["mu"]).
        b0 = _fe_mean(y, se)
    else:
        raise ValueError(method)
    return float(naive - b0), True


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def run_sim(comps, B, regime, reps=400, seed=1, boot=3000):
    treats = sorted({t for c in comps for t in (c.t1, c.t2)})
    fit0 = fit_nma(comps, reference="placebo", random=True)
    pi = fit0.treatments.index("placebo")
    true_d = {t: (fit0.TE[fit0.treatments.index(t), pi] if t in fit0.treatments else 0.0)
              for t in treats}
    active = [t for t in treats if t != "placebo"]

    # direct placebo-relative study comparison indices per treatment
    direct = {t: [] for t in active}
    for i, c in enumerate(comps):
        pair = {c.t1, c.t2}
        if "placebo" in pair and len(pair) == 2:
            other = (pair - {"placebo"}).pop()
            if other in direct:
                direct[other].append(i)
    # mean se per treatment (over all comparisons it appears in) for Sim B shaping
    sbar = {}
    for t in active:
        ses = [c.se for c in comps if t in (c.t1, c.t2)]
        sbar[t] = float(np.mean(ses)) if ses else 1.0

    def bias_active(t, se_i):
        """per-study bias added to treatment t's contrast for the given regime."""
        if regime == "A":                      # uniform multiplicative (tnma as-is)
            return true_d.get(t, 0.0) * (B * (1.0 - lam(t)))
        # regime B: SAME signed per-treatment AVERAGE magnitude as A (true_d*B*(1-lam)),
        # but distributed as a small-study effect (proportional to that study's SE, so
        # smaller/higher-SE studies carry more of the benefit-inflating bias -> classic
        # funnel asymmetry). Uses signed true_d so the bias inflates benefit exactly as
        # in regime A; mean over the treatment's studies == regime-A additive bias.
        return true_d.get(t, 0.0) * B * (1.0 - lam(t)) * (se_i / sbar.get(t, 1.0))

    rng = np.random.default_rng(seed)
    methods = ["registry_oracle", "registry_ext0.158", "registry_fix0.5", "PET", "TF", "HC"]
    err = {m: [] for m in methods}
    err_un = []
    applied = {m: [0, 0] for m in ["PET", "TF", "HC"]}   # [applied, total]

    for _ in range(reps):
        sim = []
        for c in comps:
            def obs(t):
                base = true_d.get(t, 0.0)
                if t == "placebo":
                    return 0.0
                return base + bias_active(t, c.se)
            te = obs(c.t1) - obs(c.t2) + rng.normal(0, c.se)
            sim.append(Comparison(c.studlab, c.t1, c.t2, te, c.se))
        f = fit_nma(sim, reference="placebo", random=True)
        ii = {t: i for i, t in enumerate(f.treatments)}
        if "placebo" not in ii:
            continue
        ref = ii["placebo"]
        for t in active:
            if t not in ii:
                continue
            md = f.TE[ii[t], ref]; tru = true_d.get(t, 0.0)
            err_un.append(abs(md - tru))
            # registry (external) corrections
            err["registry_oracle"].append(abs(md * (1.0 - B * (1.0 - lam(t))) - tru))
            # DEPLOYABLE frozen external magnitude from the AACT registered-vs-published gap
            # (aact_kappa_frozen.json kappa_pooled=0.158) -- no oracle, no in-network funnel:
            err["registry_ext0.158"].append(abs(md * (1.0 - K_POOL_EXT * (1.0 - lam(t))) - tru))
            err["registry_fix0.5"].append(abs(md * (1.0 - 0.5 * (1.0 - lam(t))) - tru))
            # internal funnel corrections: subtract estimated bias from SAME md
            yd = np.array([sim[i].te for i in direct[t]])
            sd = np.array([sim[i].se for i in direct[t]])
            for m, mk in (("PET", 3), ("TF", 3), ("HC", 2)):
                b, ok = internal_bias(yd, sd, m, mk)
                applied[m][1] += 1
                if ok:
                    applied[m][0] += 1
                err[m].append(abs((md - b) - tru))

    eu = np.array(err_un)
    def mc(e): return 2.0 * np.quantile(np.asarray(e), 0.95)
    rows = {"unadjusted": {"mciw0": mc(eu), "dmciw0": 0.0, "ci": [0.0, 0.0], "verdict": "-"}}
    bi = rng.integers(0, len(eu), size=(boot, len(eu)))
    for m in methods:
        e = np.array(err[m]); d = e - eu
        md_b = np.array([2.0 * (np.quantile(e[b], .95) - np.quantile(eu[b], .95)) for b in bi])
        lo, hi = np.quantile(md_b, [.025, .975])
        v = "WINS" if hi < 0 else ("HARMS" if lo > 0 else "tie")
        rows[m] = {"mciw0": mc(e), "dmciw0": mc(e) - mc(eu),
                   "ci": [float(lo), float(hi)], "verdict": v}
    return {"B": B, "regime": regime, "mciw0_un": mc(eu), "rows": rows,
            "applied": applied, "n_cells": len(eu)}


def fmt(res):
    print(f"\n  Sim {res['regime']}  B={res['B']:.2f}   (unadjusted MCIW0 = {res['mciw0_un']:.4f}, "
          f"{res['n_cells']} cells)")
    print(f"  {'method':18}{'MCIW0':>9}{'dMCIW0':>10}{'  95% CI on dMCIW0':>22}{'verdict':>9}")
    order = ["unadjusted", "registry_oracle", "registry_ext0.158", "registry_fix0.5", "PET", "TF", "HC"]
    for m in order:
        r = res["rows"][m]
        ci = f"[{r['ci'][0]:+.4f},{r['ci'][1]:+.4f}]"
        print(f"  {m:18}{r['mciw0']:>9.4f}{r['dmciw0']:>+10.4f}{ci:>22}{r['verdict']:>9}")


def main():
    comps = senn_contrasts()
    fit = fit_nma(comps, reference="placebo", random=True)
    print("=" * 78)
    print("HEAD-TO-HEAD: external registry-lambda vs internal funnel selection models")
    print("=" * 78)
    print(f"  senn2013 network: {fit.n} treatments, {fit.k} studies, {fit.m} contrasts; "
          f"tau={fit.tau:.3f}, I2={fit.I2:.0f}%")
    active = [t for t in fit.treatments if t != "placebo"]
    direct = {t: 0 for t in active}
    for c in comps:
        pair = {c.t1, c.t2}
        if "placebo" in pair and len(pair) == 2:
            o = (pair - {"placebo"}).pop()
            if o in direct:
                direct[o] += 1
    print("  direct placebo-relative studies per active treatment (drives internal funnel fits):")
    print("   ", ", ".join(f"{t}:{n}" for t, n in sorted(direct.items(), key=lambda x: -x[1])))
    print("  (PET/TF need >=3, HC needs >=2 direct studies; else that treatment is unadjusted)")

    allres = []
    for regime in ("A", "B"):
        label = ("A = UNIFORM multiplicative registry bias (funnel-INVISIBLE, tnma as-is)"
                 if regime == "A" else
                 "B = SE-proportional small-study effect (funnel-VISIBLE, same avg magnitude)")
        print("\n" + "-" * 78)
        print(f"REGIME {label}")
        print("-" * 78)
        for B in (0.0, 0.15, 0.30):
            r = run_sim(comps, B, regime)
            fmt(r)
            allres.append(r)
        ap = allres[-1]["applied"]
        print("  internal-fit applicability (applied/total cells): "
              + ", ".join(f"{m}={v[0]}/{v[1]}" for m, v in ap.items()))

    out = Path(__file__).resolve().parent / "h2h_result.json"
    json.dump({"sweep": allres}, open(out, "w"), indent=1)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
