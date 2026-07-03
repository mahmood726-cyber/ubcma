"""TRUTH-GATE for the EXTERNAL AACT magnitude (FIX3-external).

Frozen (no sim tuning) external estimates from aact_kappa_frozen.json:
  kappa_slope  = 0.263  (deployable external B est. from published-vs-registered gap ~ (1-lambda))
  kappa_pooled = 0.158  (absolute effect-inflation scale)
  per-class m_c (clamped kappa_MD)

senn2013 known-truth sim (same geometry / bias model as tnma & h2h_bench):
  true bias per active treatment = B*(1-lambda_t)*d_true_t (registry model).
Correctors scored at matched coverage (MCIW0, paired bootstrap vs the common unadjusted NMA):
  oracle(kappa=B)      -- upper bound (uses the injected B; not deployable)
  ext_slope(0.263)     -- FROZEN AACT external magnitude (DEPLOYABLE, no oracle)   <-- the fix
  ext_pooled(0.158)    -- FROZEN absolute-scale variant
  ext_perclass         -- FROZEN per-class m_c (clamped kappa_MD), correction d*(1-m_c)
  fixed(0.5)           -- naive un-calibrated baseline (the FIX3-internal-negative comparator)

Question (verbatim): does the EXTERNAL kappa now RECOVER the correct magnitude -- converting FIX3
from 'direction-only' to a full win -- or not? Honest verdict from the numbers, no manufacturing.
Regimes A (funnel-invisible uniform) and B (funnel-visible small-study) as in h2h_bench.
"""
import json, io, sys
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(r"F:\ubcma\transport_nma")))
from h2h_bench import senn_contrasts, lam, fit_nma, Comparison   # noqa: E402
# NB: h2h_bench already re-wraps sys.stdout on import; do NOT re-wrap (closes the buffer).

HERE = Path(__file__).resolve().parent
FR = json.load(open(HERE/"aact_kappa_frozen.json"))
K_SLOPE = FR["kappa_slope"]; K_POOL = FR["kappa_pooled"]; MC = FR["per_class_clamped"]

# map treatment -> class for per-class corrector
TREAT_CLASS = {"metformin":"metformin","sitagliptin":"DPP4","vildagliptin":"DPP4",
 "sulfonylurea":"SU","pioglitazone":"TZD","rosiglitazone":"TZD",
 "acarbose":"AGI","miglitol":"AGI","benfluorex":None,"placebo":None}
def mc_of(t): return float(MC.get(TREAT_CLASS.get(t) or "", 0.0))


def run(comps, B, regime, reps=400, seed=1, boot=3000):
    treats = sorted({t for c in comps for t in (c.t1, c.t2)})
    fit0 = fit_nma(comps, reference="placebo", random=True)
    pi = fit0.treatments.index("placebo")
    true_d = {t: (fit0.TE[fit0.treatments.index(t), pi] if t in fit0.treatments else 0.0) for t in treats}
    active = [t for t in treats if t != "placebo"]
    sbar = {t: float(np.mean([c.se for c in comps if t in (c.t1,c.t2)]) or 1.0) for t in active}

    def bias(t, se_i):
        base = true_d.get(t, 0.0)
        if regime == "A":
            return base * (B*(1.0-lam(t)))
        return base * B*(1.0-lam(t)) * (se_i/sbar.get(t,1.0))

    # placebo-relative direct study contrasts (for the pooled-network Egger presence gate)
    plac_idx = [i for i,c in enumerate(comps)
                if "placebo" in (c.t1,c.t2) and c.t1 != c.t2]

    def egger_t(sim):
        """Pooled-network Egger radial regression across ALL placebo-relative direct
        study contrasts (signed toward benefit): |t| on the SE slope = funnel-asymmetry
        presence. Returns |t| (0 if <3 studies)."""
        y = np.array([ (sim[i].te if sim[i].t2=="placebo" else -sim[i].te) for i in plac_idx ])
        se = np.array([ sim[i].se for i in plac_idx ])
        if len(y) < 3: return 0.0
        prec = 1.0/se; z = y*prec
        X = np.column_stack([prec, np.ones_like(prec)])   # radial: z ~ prec (slope) + intercept
        try:
            beta, *_ = np.linalg.lstsq(X, z, rcond=None)
            resid = z - X@beta; dof = len(y)-2
            if dof < 1: return 0.0
            s2 = float(resid@resid)/dof
            cov = s2*np.linalg.inv(X.T@X)
            se_int = float(np.sqrt(cov[1,1]))
            return abs(beta[1]/se_int) if se_int>0 else 0.0
        except Exception:
            return 0.0

    rng = np.random.default_rng(seed)
    meth = ["oracle","ext_slope","ext_pooled","ext_pooled_gated","ext_perclass","fixed0.5"]
    err = {m: [] for m in meth}; eu = []
    GATE = 1.64
    gate_fired = 0; gate_total = 0
    for _ in range(reps):
        sim = []
        for c in comps:
            def obs(t): return 0.0 if t=="placebo" else true_d.get(t,0.0)+bias(t,c.se)
            sim.append(Comparison(c.studlab, c.t1, c.t2, obs(c.t1)-obs(c.t2)+rng.normal(0,c.se), c.se))
        f = fit_nma(sim, reference="placebo", random=True)
        ii = {t:i for i,t in enumerate(f.treatments)}
        if "placebo" not in ii: continue
        ref = ii["placebo"]
        fire = egger_t(sim) >= GATE
        gate_total += 1; gate_fired += int(fire)
        for t in active:
            if t not in ii: continue
            md = f.TE[ii[t], ref]; tru = true_d.get(t,0.0); s = 1.0-lam(t)
            eu.append(abs(md-tru))
            err["oracle"].append(abs(md*(1.0-B*s)-tru))
            err["ext_slope"].append(abs(md*(1.0-K_SLOPE*s)-tru))
            err["ext_pooled"].append(abs(md*(1.0-K_POOL*s)-tru))
            err["ext_pooled_gated"].append(abs(md*(1.0-(K_POOL if fire else 0.0)*s)-tru))
            err["ext_perclass"].append(abs(md*(1.0-mc_of(t))-tru))
            err["fixed0.5"].append(abs(md*(1.0-0.5*s)-tru))
    eu = np.array(eu)
    mc = lambda e: 2.0*np.quantile(np.asarray(e),0.95)
    bi = rng.integers(0, len(eu), size=(boot, len(eu)))
    rows = {"unadjusted": dict(mciw0=mc(eu), dmciw0=0.0, ci=[0.0,0.0], verdict="-")}
    for m in meth:
        e = np.array(err[m])
        mb = np.array([2.0*(np.quantile(e[b],.95)-np.quantile(eu[b],.95)) for b in bi])
        lo,hi = np.quantile(mb,[.025,.975])
        v = "WINS" if hi<0 else ("HARMS" if lo>0 else "tie")
        rows[m]=dict(mciw0=mc(e), dmciw0=mc(e)-mc(eu), ci=[float(lo),float(hi)], verdict=v)
    return dict(B=B, regime=regime, mciw0_un=mc(eu), rows=rows, n_cells=len(eu),
                gate_fire_rate=(gate_fired/gate_total if gate_total else 0.0))


def fmt(r):
    print(f"\n  Sim {r['regime']}  B={r['B']:.3f}   (unadj MCIW0={r['mciw0_un']:.4f}, {r['n_cells']} cells; "
          f"Egger-gate fire-rate={r['gate_fire_rate']:.2f})")
    print(f"  {'method':16}{'MCIW0':>9}{'dMCIW0':>10}{'  95% CI dMCIW0':>22}{'verdict':>9}")
    for m in ["unadjusted","oracle","ext_slope","ext_pooled","ext_pooled_gated","ext_perclass","fixed0.5"]:
        x=r["rows"][m]; ci=f"[{x['ci'][0]:+.4f},{x['ci'][1]:+.4f}]"
        print(f"  {m:16}{x['mciw0']:>9.4f}{x['dmciw0']:>+10.4f}{ci:>22}{x['verdict']:>9}")


def main():
    comps = senn_contrasts()
    print("="*80)
    print("TRUTH-GATE: EXTERNAL AACT kappa (FROZEN) vs oracle / fixed / unadjusted")
    print("="*80)
    print(f"  frozen external: kappa_slope={K_SLOPE:.3f}  kappa_pooled={K_POOL:.3f}")
    print(f"  per-class m_c: " + ", ".join(f"{c}:{MC[c]:.2f}" for c in ['metformin','SGLT2','DPP4','AGI'] if c in MC))
    allr=[]
    for regime in ("A","B"):
        print("\n"+"-"*80)
        print(f"REGIME {regime}: "+("uniform (funnel-invisible)" if regime=="A" else "small-study (funnel-visible)"))
        print("-"*80)
        for B in (0.0, 0.15, K_SLOPE, 0.30):
            r = run(comps, B, regime); fmt(r); allr.append(r)
    json.dump({"frozen":FR, "sweep":allr}, open(HERE/"aact_kappa_truthgate_result.json","w"), indent=1)
    print("\nwrote aact_kappa_truthgate_result.json")


if __name__ == "__main__":
    main()
