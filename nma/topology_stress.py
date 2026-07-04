"""HONEST STRESS TEST for AdaptShrink-NMA: does the selection-robustness win hold across network
TOPOLOGIES? The finalized boundary map (REPORT_NMA_PHASE3) characterises the win on DENSE small
networks. Real networks are often sparse — star (all-vs-reference) or ladder (chain) shaped. This is a
SELF-CONTAINED, internally-consistent harness (fresh sim; it compares topologies RELATIVELY within one
protocol — it does NOT reproduce the committed dense absolute numbers, which use the Phase-3 generator).

Protocol: n treatments, true effects theta_t; each present edge carries m studies with heterogeneous SE.
Strong selection = a small-study effect (per-study bias proportional to that study's SE, benefit-inflating
-> network funnel asymmetry). Baseline = common-DL graph NMA (fit_nma); ours = adaptshrink_nma_auto.
Score MCIW0 = 2 x 95th pct of |est - truth| over (rep x basic-contrast-vs-reference); paired bootstrap
97.5% CI on dMCIW0 (auto - DL). Negative & CI<0 = robust matched-coverage win. Reported per topology.
"""
import sys, io, json
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from nma_core import Comparison, fit_nma            # noqa: E402
from adaptshrink_nma import adaptshrink_nma_auto     # noqa: E402
if "pytest" not in sys.modules:
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass


def edges_for(n, topology):
    T = [f"T{i}" for i in range(n)]
    e = []
    if topology == "dense":
        for i in range(n):
            for j in range(i + 1, n):
                e.append((T[i], T[j]))
    elif topology == "star":            # all vs reference T0
        for j in range(1, n):
            e.append((T[0], T[j]))
    elif topology == "ladder":          # chain T0-T1-T2-...
        for i in range(n - 1):
            e.append((T[i], T[i + 1]))
    return T, e


def run(n=8, topology="dense", m=4, B=1.0, tau=0.10, reps=500, seed=1, boot=3000):
    T, edges = edges_for(n, topology)
    rng = np.random.default_rng(seed)
    theta = {t: v for t, v in zip(T, np.linspace(0.0, 0.8, n))}   # true potentials
    ref = "T0"
    true_d = {t: theta[t] - theta[ref] for t in T}
    active = [t for t in T if t != ref]

    err_dl = {t: [] for t in active}
    err_as = {t: [] for t in active}
    for _ in range(reps):
        comps = []
        for (a, b) in edges:
            d_edge = theta[a] - theta[b]
            sgn = np.sign(d_edge) if d_edge != 0 else 0.0
            for _s in range(m):
                se = float(rng.uniform(0.05, 0.45))                  # heterogeneous precision -> funnel
                d0 = d_edge + rng.normal(0, tau)                     # random-effects heterogeneity
                # strong small-study effect: high-SE studies EXAGGERATE the edge effect (classic funnel
                # asymmetry). Additive per-SE inflation in the effect direction, magnitude B*se.
                bias = B * se * sgn
                te = d0 + bias + rng.normal(0, se)
                comps.append(Comparison(f"{a}{b}{_s}", a, b, te, se))
        try:
            fdl = fit_nma(comps, reference=ref, random=True)
            fas = adaptshrink_nma_auto(comps, reference=ref)
        except Exception:
            continue
        idl = {t: i for i, t in enumerate(fdl.treatments)}
        ias = {t: i for i, t in enumerate(fas.treatments)}
        if ref not in idl or ref not in ias:
            continue
        rdl, ras = idl[ref], ias[ref]
        for t in active:
            if t in idl:
                err_dl[t].append(abs(fdl.TE[idl[t], rdl] - true_d[t]))
            if t in ias:
                err_as[t].append(abs(fas.TE[ias[t], ras] - true_d[t]))

    edl = np.array([e for t in active for e in err_dl[t]])
    eas = np.array([e for t in active for e in err_as[t]])
    n_pair = min(len(edl), len(eas))
    edl, eas = edl[:n_pair], eas[:n_pair]
    mc = lambda e: 2.0 * np.quantile(e, 0.95)
    bi = rng.integers(0, n_pair, size=(boot, n_pair))
    mb = np.array([2.0 * (np.quantile(eas[b], .95) - np.quantile(edl[b], .95)) for b in bi])
    lo, hi = np.quantile(mb, [.025, .975])
    d = mc(eas) - mc(edl)
    v = "WINS" if hi < 0 else ("HARMS" if lo > 0 else "tie")
    return dict(topology=topology, n_edges=len(edges), mciw0_dl=mc(edl), mciw0_as=mc(eas),
                dmciw0=d, ci=[float(lo), float(hi)], verdict=v, n_cells=n_pair)


def main():
    print("=" * 84)
    print("AdaptShrink-NMA topology stress test (auto vs common-DL, strong small-study effect B=1.0 (pre-declared))")
    print("  fresh internally-consistent harness; RELATIVE topology comparison (not the Phase-3 absolutes)")
    print("=" * 84)
    print(f"  {'topology':10}{'#edges':>8}{'MCIW0 DL':>11}{'MCIW0 auto':>12}{'dMCIW0':>9}{'  95% CI':>20}{'verdict':>9}")
    out = []
    for topo in ("dense", "ladder", "star"):
        r = run(topology=topo)
        ci = f"[{r['ci'][0]:+.4f},{r['ci'][1]:+.4f}]"
        print(f"  {topo:10}{r['n_edges']:>8}{r['mciw0_dl']:>11.4f}{r['mciw0_as']:>12.4f}"
              f"{r['dmciw0']:>+9.4f}{ci:>20}{r['verdict']:>9}")
        out.append(r)
    json.dump({"sweep": out}, open(Path(__file__).resolve().parent / "topology_stress_result.json", "w"), indent=1)
    print("\n  (negative dMCIW0 with CI<0 = AdaptShrink-NMA robust matched-coverage win vs common-DL)")
    print("wrote topology_stress_result.json")


if __name__ == "__main__":
    main()
