"""FALSIFICATION stress test for the transport-NMA external-kappa correction: scrambled-lambda control.

The registry correction shrinks each treatment by kappa*(1-lambda_t). If the win came from generic
shrinkage rather than the REAL registry signal, then replacing the true per-class lambda ordering with a
random PERMUTATION of the same lambda values (in the CORRECTION only; the injected bias still uses the
TRUE lambda) should win just as well. If instead the scrambled correction loses / stops winning, the
per-class registry ordering is doing real work -- the analogue of the scrambled-kernel control in the
borrowing-field program.

Design (senn2013 geometry, matched-coverage MCIW0, paired bootstrap; frozen kappa_pooled=0.158):
  inject   d_obs = d_true * (1 + B*(1 - lambda_true_t))     [always TRUE lambda]
  correct  real:      md * (1 - 0.158*(1 - lambda_true_t))
           scrambled: md * (1 - 0.158*(1 - lambda_perm_t))  [lambda values permuted across active treats]
Average the scrambled arm over many permutations. Truth-first: report honestly whether real beats scrambled.
"""
import json, io, sys
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(r"F:\ubcma\transport_nma")))
from h2h_bench import senn_contrasts, lam, fit_nma, Comparison, TREAT_CLASS  # noqa: E402
# NB: h2h_bench guards its stdout re-wrap behind pytest; safe to import.

HERE = Path(__file__).resolve().parent
K_POOL = float(json.load(open(HERE / "aact_kappa_frozen.json"))["kappa_pooled"])


def run(comps, B, n_perm=40, reps=300, seed=1, boot=3000):
    treats = sorted({t for c in comps for t in (c.t1, c.t2)})
    active = [t for t in treats if t != "placebo"]
    fit0 = fit_nma(comps, reference="placebo", random=True)
    pi = fit0.treatments.index("placebo")
    true_d = {t: (fit0.TE[fit0.treatments.index(t), pi] if t in fit0.treatments else 0.0) for t in treats}
    lam_true = {t: lam(t) for t in active}

    rng = np.random.default_rng(seed)
    # pre-draw permutations of the lambda VALUES across active treatments
    vals = np.array([lam_true[t] for t in active])
    perms = [rng.permutation(len(active)) for _ in range(n_perm)]

    err_un, err_real = [], []
    err_scr = [[] for _ in range(n_perm)]
    for _ in range(reps):
        sim = []
        for c in comps:
            def obs(t):
                return 0.0 if t == "placebo" else true_d.get(t, 0.0) * (1.0 + B * (1.0 - lam_true.get(t, 1.0)))
            sim.append(Comparison(c.studlab, c.t1, c.t2, obs(c.t1) - obs(c.t2) + rng.normal(0, c.se), c.se))
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
            err_real.append(abs(md * (1.0 - K_POOL * (1.0 - lam_true[t])) - tru))
            for j, p in enumerate(perms):
                lam_perm = {active[k]: vals[p[k]] for k in range(len(active))}
                err_scr[j].append(abs(md * (1.0 - K_POOL * (1.0 - lam_perm[t])) - tru))

    eu = np.array(err_un)
    mc = lambda e: 2.0 * np.quantile(np.asarray(e), 0.95)
    bi = rng.integers(0, len(eu), size=(boot, len(eu)))

    def dstat(e):
        e = np.array(e)
        mb = np.array([2.0 * (np.quantile(e[b], .95) - np.quantile(eu[b], .95)) for b in bi])
        return mc(e) - mc(eu), float(np.quantile(mb, .025)), float(np.quantile(mb, .975))

    d_real, lo_real, hi_real = dstat(err_real)
    scr_d = np.array([mc(e) - mc(eu) for e in err_scr])
    frac_win = float(np.mean(scr_d < 0))              # do scrambles win at all (generic-shrinkage floor)?
    # permutation position: fraction of scrambles as good as / better than real (one-sided p)
    perm_p = float(np.mean(scr_d <= d_real))
    return dict(B=B, mciw0_un=mc(eu), d_real=d_real, ci_real=[lo_real, hi_real],
                scr_mean=float(scr_d.mean()), scr_lo=float(np.quantile(scr_d, .025)),
                scr_hi=float(np.quantile(scr_d, .975)), scr_frac_win=frac_win,
                perm_p=perm_p, ordering_gain=float(scr_d.mean() - d_real), n_perm=n_perm)


def main():
    comps = senn_contrasts()
    print("=" * 82)
    print("FALSIFICATION: scrambled-lambda control for the external-kappa correction (kappa=0.158)")
    print("=" * 82)
    print("  real lambda ordering vs a permutation of the SAME lambda values (correction only);")
    print("  bias always injected with TRUE lambda. If the registry ORDERING matters, real should win")
    print("  and scrambled should not (or win far less often).")
    res = []
    for B in (0.15, 0.30):
        r = run(comps, B)
        print(f"\n  B={B:.2f}  (unadj MCIW0={r['mciw0_un']:.4f})")
        print(f"    real-lambda     dMCIW0 {r['d_real']:+.4f} [{r['ci_real'][0]:+.4f},{r['ci_real'][1]:+.4f}]"
              f"  {'WINS' if r['ci_real'][1] < 0 else 'tie/none'}")
        print(f"    scrambled(x{r['n_perm']}) dMCIW0 mean {r['scr_mean']:+.4f} "
              f"[{r['scr_lo']:+.4f},{r['scr_hi']:+.4f}]  win-fraction {r['scr_frac_win']:.2f}")
        verdict = ("REGISTRY ORDERING ADDS SIGNIFICANT VALUE (real beyond scrambled distribution)"
                   if r['perm_p'] <= 0.05 else
                   "ordering helps but within scrambled spread (generic shrinkage dominates here)")
        print(f"    => ordering gain {r['ordering_gain']:+.4f}; perm-p (scrambles as good as real) "
              f"{r['perm_p']:.3f}; generic-shrinkage floor: {r['scr_frac_win']*100:.0f}% of scrambles win")
        print(f"    => {verdict}")
        res.append(r)
    json.dump({"kappa": K_POOL, "sweep": res}, open(HERE / "aact_kappa_scramble_result.json", "w"), indent=1)
    print("\nwrote aact_kappa_scramble_result.json")


if __name__ == "__main__":
    main()
