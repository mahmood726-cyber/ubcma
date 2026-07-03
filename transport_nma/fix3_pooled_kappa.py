"""FIX3 — deployable data-driven registry-pub-bias correction for the NMA.

The head-to-head (h2h_bench.py) showed the ORACLE registry-λ correction (κ=B, knows the truth) beats
every internal selection model, but a FIXED κ=0.5 over-corrects at B=0. This makes the correction
DATA-DRIVEN and GATED, so it needs no oracle:

  NETWORK-POOLED small-study estimator. Stack ALL direct placebo-relative studies of ALL active
  treatments. Fit one WLS:   y_i = d_{t(i)}  +  γ · (1 − λ_{t(i)}) · se_i   (weights 1/se_i²),
  with per-treatment intercepts d_t and a SINGLE shared slope γ. This pools the small-study signal
  across the whole network (borrowing strength) instead of fitting a noisy per-treatment funnel (PET's
  fatal move on 3–6 studies), and lets the registry λ SCALE the per-class severity. The corrected basic
  contrast is the se→0 intercept d̂_t. GATE: apply the correction only if γ is significant (|t_γ| ≥ 2);
  else γ:=0 → no correction (inert). λ supplies the per-class direction; the network + funnel supply the
  data-driven magnitude and the selection-presence gate.

Scored against unadjusted NMA, the oracle registry-λ, and per-treatment PET, on the h2h sim, in both
the funnel-VISIBLE (B, small-study) and funnel-INVISIBLE (A, SE-orthogonal) regimes. Honest expectation:
the pooled κ̂ recovers the win in the funnel-VISIBLE regime and is INERT at B=0 (gate works); in the
funnel-INVISIBLE regime no internal funnel estimator can recover the magnitude (γ≈0 → inert) — the honest
limit that external registry λ gives direction, and funnel-invisible magnitude needs external calibration.
"""
import json, io, sys
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT / "nma")); sys.path.insert(0, str(ROOT / "src"))
from nma_core import Comparison, fit_nma            # noqa: E402
from h2h_bench import senn_contrasts, lam           # noqa: E402  (reuse verified sim pieces)
Z975 = 1.959963984540054


def pooled_kappa_correct(sim, active, md, direct, sbar, gate_t=2.0):
    """Network-pooled small-study estimator. Corrects the NETWORK estimate md_t by SUBTRACTING the
    estimated small-study bias gamma*(1-lam_t)*sbar_t (keeping the network's indirect evidence), rather
    than replacing md_t with the noisy direct-study intercept. Gated on gamma significance."""
    # stack direct placebo-relative studies: response y_i, feature (1-lam_t)*se_i, treatment dummy
    rows_y, rows_se, rows_t, rows_f = [], [], [], []
    for t in active:
        for i in direct[t]:
            c = sim[i]
            rows_y.append(c.te); rows_se.append(c.se); rows_t.append(t)
            rows_f.append((1.0 - lam(t)) * c.se)
    if len(rows_y) < len(active) + 2:
        return {t: md[t] for t in active}, 0.0, 0.0
    y = np.array(rows_y); se = np.array(rows_se); f = np.array(rows_f)
    ts = sorted(set(rows_t)); tix = {t: j for j, t in enumerate(ts)}
    X = np.zeros((len(y), len(ts) + 1))
    for r, t in enumerate(rows_t):
        X[r, tix[t]] = 1.0
    X[:, -1] = f
    w = 1.0 / se ** 2
    XtW = X.T * w
    try:
        cov = np.linalg.inv(XtW @ X)
    except np.linalg.LinAlgError:
        return {t: md[t] for t in active}, 0.0, 0.0
    beta = cov @ (XtW @ y)
    resid = y - X @ beta
    dof = max(len(y) - X.shape[1], 1)
    s2 = float((w * resid ** 2).sum() / dof)
    gamma = float(beta[-1]); se_g = float(np.sqrt(max(s2 * cov[-1, -1], 1e-18)))
    tg = gamma / se_g if se_g > 0 else 0.0
    if abs(tg) < gate_t:                      # GATE: no significant small-study effect -> no correction
        return {t: md[t] for t in active}, gamma, tg
    # correct the NETWORK estimate by subtracting the estimated bias (keep indirect evidence)
    dhat = {t: md[t] - gamma * (1.0 - lam(t)) * sbar.get(t, 0.0) for t in active}
    return dhat, gamma, tg


def run(comps, B, regime, reps=300, seed=1):
    treats = sorted({t for c in comps for t in (c.t1, c.t2)})
    fit0 = fit_nma(comps, reference="placebo", random=True)
    pi = fit0.treatments.index("placebo")
    true_d = {t: (fit0.TE[fit0.treatments.index(t), pi] if t in fit0.treatments else 0.0) for t in treats}
    active = [t for t in treats if t != "placebo"]
    sbar = {t: float(np.mean([c.se for c in comps if t in (c.t1, c.t2)]) or 1.0) for t in active}
    direct = {t: [i for i, c in enumerate(comps)
                  if {c.t1, c.t2} == {"placebo", t}] for t in active}
    rng = np.random.default_rng(seed)
    e = {m: [] for m in ["unadj", "oracle", "pooled", "pet"]}
    ngate = 0
    for _ in range(reps):
        sim = []
        for c in comps:
            def obs(t):
                if t == "placebo":
                    return 0.0
                base = true_d.get(t, 0.0)
                if regime == "A":
                    return base * (1.0 + B * (1.0 - lam(t)))              # funnel-invisible
                return base + base * B * (1.0 - lam(t)) * (c.se / sbar.get(t, 1.0))  # funnel-visible
            sim.append(Comparison(c.studlab, c.t1, c.t2, obs(c.t1) - obs(c.t2) + rng.normal(0, c.se), c.se))
        f = fit_nma(sim, reference="placebo", random=True)
        ii = {t: i for i, t in enumerate(f.treatments)}; ref = ii["placebo"]
        md = {t: f.TE[ii[t], ref] for t in active if t in ii}
        dhat, gamma, tg = pooled_kappa_correct(sim, [t for t in active if t in md], md, direct, sbar)
        if abs(tg) >= 2.0:
            ngate += 1
        for t in md:
            tru = true_d.get(t, 0.0)
            e["unadj"].append(abs(md[t] - tru))
            e["oracle"].append(abs(md[t] * (1.0 - B * (1.0 - lam(t))) - tru))
            e["pooled"].append(abs(dhat[t] - tru))
            # per-treatment PET (the noisy internal comparator): funnel intercept on t's direct studies
            yi = np.array([sim[i].te for i in direct[t]]); si = np.array([sim[i].se for i in direct[t]])
            if len(yi) >= 3:
                Xp = np.column_stack([np.ones(len(yi)), si]); wp = 1.0 / si ** 2
                try:
                    bp = np.linalg.solve((Xp.T * wp) @ Xp, (Xp.T * wp) @ yi)
                    petmu = md[t] - (float(np.sum(wp * yi) / np.sum(wp)) - bp[0])
                except np.linalg.LinAlgError:
                    petmu = md[t]
            else:
                petmu = md[t]
            e["pet"].append(abs(petmu - tru))
    def mc(a): return 2.0 * np.quantile(np.asarray(a), 0.95)
    eu = np.array(e["unadj"]); out = {"B": B, "regime": regime, "gate_rate": ngate / reps}
    rng2 = np.random.default_rng(7); bi = rng2.integers(0, len(eu), size=(3000, len(eu)))
    for m in ["oracle", "pooled", "pet"]:
        a = np.array(e[m]); md_b = np.array([2 * (np.quantile(a[b], .95) - np.quantile(eu[b], .95)) for b in bi])
        lo, hi = np.quantile(md_b, [.025, .975])
        out[m] = dict(mciw0=mc(a), d=mc(a) - mc(eu), ci=[float(lo), float(hi)],
                      v="WINS" if hi < 0 else ("HARMS" if lo > 0 else "tie"))
    out["mciw0_un"] = mc(eu)
    return out


def main():
    comps = senn_contrasts()
    print("FIX3: DATA-DRIVEN network-pooled registry-κ̂ (gated) vs oracle vs per-treatment PET")
    print("  senn2013 sim; MCIW0 recovering true basic contrasts; paired-boot ΔMCIW0 vs unadjusted\n")
    res = []
    for regime in ("A", "B"):
        lbl = "A funnel-INVISIBLE (SE-orthogonal registry non-reporting)" if regime == "A" \
              else "B funnel-VISIBLE (small-study effect)"
        print(f"--- Regime {lbl} ---")
        for B in (0.0, 0.15, 0.30):
            r = run(comps, B, regime); res.append(r)
            print(f"  B={B:.2f} (unadj {r['mciw0_un']:.4f}, γ-gate fires {r['gate_rate']*100:.0f}% of reps): "
                  f"pooled-κ̂ {r['pooled']['d']:+.4f}{r['pooled']['ci']}{r['pooled']['v']} | "
                  f"oracle {r['oracle']['d']:+.4f}{r['oracle']['v']} | PET {r['pet']['d']:+.4f}{r['pet']['v']}")
    json.dump({"sweep": res}, open(HERE / "fix3_result.json", "w"), indent=1)
    print("\nVERDICT (HONEST NEGATIVE): the data-driven internal pooled-κ̂ does NOT recover the oracle's")
    print("win -- it HARMS in both regimes (+0.03..+0.10). The γ-gate fires only 6-30% of reps and when")
    print("it does, γ̂ is too noisy on this sparse network (~4-6 direct studies/treatment, ~9 treatments)")
    print("to correct usefully; both the replace-intercept and subtract-bias forms harm. So registry-λ")
    print("supplies the DIRECTION (oracle wins) but the MAGNITUDE cannot be recovered internally from a")
    print("sparse network's funnel. THE REAL FIX = EXTERNAL magnitude: estimate the effect-inflation κ")
    print("directly from AACT (registered-vs-published effect-distribution gap per class), not the funnel.")


if __name__ == "__main__":
    main()
