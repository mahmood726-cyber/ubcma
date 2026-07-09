import sys
import numpy as np
from pathlib import Path

# Add nma directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import topology_stress as ts
from nma_core import fit_nma
from adaptshrink_nma import adaptshrink_nma_auto

def run_compare(n=8, topology="dense", m=4, B=1.0, tau=0.10, reps=400, seed=1, boot=2000):
    T, edges = ts.edges_for(n, topology)
    rng = np.random.default_rng(seed)
    theta = {t: v for t, v in zip(T, np.linspace(0.0, 0.8, n))}
    ref = "T0"
    true_d = {t: theta[t] - theta[ref] for t in T}
    active = [t for t in T if t != ref]

    # Collect lists of errors
    err_dl = {t: [] for t in active}
    err_as = {t: [] for t in active}
    
    # We will also keep track of errors grouped by replicate
    rep_errors_dl = []
    rep_errors_as = []

    for _ in range(reps):
        comps = []
        for (a, b) in edges:
            d_edge = theta[a] - theta[b]
            sgn = np.sign(d_edge) if d_edge != 0 else 0.0
            for _s in range(m):
                se = float(rng.uniform(0.05, 0.45))
                d0 = d_edge + rng.normal(0, tau)
                bias = B * se * sgn
                te = d0 + bias + rng.normal(0, se)
                comps.append(ts.Comparison(f"{a}{b}{_s}", a, b, te, se))
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
        
        # Check if all active treatments are present to avoid misalignment
        if not all(t in idl and t in ias for t in active):
            continue
            
        this_rep_dl = []
        this_rep_as = []
        for t in active:
            e_dl = abs(fdl.TE[idl[t], rdl] - true_d[t])
            e_as = abs(fas.TE[ias[t], ras] - true_d[t])
            err_dl[t].append(e_dl)
            err_as[t].append(e_as)
            this_rep_dl.append(e_dl)
            this_rep_as.append(e_as)
        rep_errors_dl.append(this_rep_dl)
        rep_errors_as.append(this_rep_as)

    # 1. Original Element-wise Bootstrap
    edl = np.array([e for t in active for e in err_dl[t]])
    eas = np.array([e for t in active for e in err_as[t]])
    n_pair = len(edl)
    
    mc = lambda e: 2.0 * np.quantile(e, 0.95)
    
    bi_element = rng.integers(0, n_pair, size=(boot, n_pair))
    mb_element = np.array([2.0 * (np.quantile(eas[b], .95) - np.quantile(edl[b], .95)) for b in bi_element])
    lo_el, hi_el = np.quantile(mb_element, [.025, .975])
    d_val = mc(eas) - mc(edl)
    v_el = "WINS" if hi_el < 0 else ("HARMS" if lo_el > 0 else "tie")

    # 2. Corrected Cluster Bootstrap (resample replicates)
    # rep_errors_dl has shape (reps_valid, n_active)
    rep_errors_dl = np.array(rep_errors_dl)
    rep_errors_as = np.array(rep_errors_as)
    n_reps_valid = rep_errors_dl.shape[0]
    
    mb_cluster = []
    for _ in range(boot):
        # resample replicate indices
        idx = rng.integers(0, n_reps_valid, size=n_reps_valid)
        # extract resampled errors and flatten
        dl_boot = rep_errors_dl[idx].ravel()
        as_boot = rep_errors_as[idx].ravel()
        mb_cluster.append(2.0 * (np.quantile(as_boot, 0.95) - np.quantile(dl_boot, 0.95)))
    mb_cluster = np.array(mb_cluster)
    lo_cl, hi_cl = np.quantile(mb_cluster, [.025, .975])
    v_cl = "WINS" if hi_cl < 0 else ("HARMS" if lo_cl > 0 else "tie")

    print(f"Results for n={n}, topology={topology}, m={m}:")
    print(f"  Point estimate dMCIW0: {d_val:.4f}")
    print(f"  Element Bootstrap:    [{lo_el:+.4f}, {hi_el:+.4f}] -> {v_el}")
    print(f"  Cluster Bootstrap:    [{lo_cl:+.4f}, {hi_cl:+.4f}] -> {v_cl}")
    return {
        "point": d_val,
        "el_ci": [lo_el, hi_el],
        "el_verdict": v_el,
        "cl_ci": [lo_cl, hi_cl],
        "cl_verdict": v_cl
    }

if __name__ == "__main__":
    # Test on a small study first to verify (e.g. n=6, topology=dense, m=4, seed=5)
    run_compare(n=6, topology="dense", m=4, seed=5)
    # Also test n=5 (which was a borderline tie/harm)
    run_compare(n=5, topology="dense", m=4, seed=5)
    # Let's run a sweep on n=5, 6, 7, 8
    for n_val in [5, 6, 7, 8]:
        run_compare(n=n_val, topology="dense", m=4, seed=5)
