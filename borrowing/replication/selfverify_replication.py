"""FROM-SCRATCH independent re-derivation of the replication headline.

NO imports of borrowing_field2 / ubcma / run_slice -- every number recomputed with
inline numpy only, to confirm the two CLEAN slices' relevance-vs-null LOO advantage
(vendor cross-check substitute; Codex pc1 401, pc2 publickey-denied, agy empty).

For each clean slice we redo the pure-prior LOO: held-out trial t, prior from the
OTHER trials via an inline Gaussian dose/covariate kernel x precision (relevance),
inline precision-only mean (uniform), inline permuted-kernel (scrambled). MAE vs the
real held-out effect; inline paired bootstrap. Must match run_slice.py to ~2 dp.
"""
import json, numpy as np, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
Z = 1.959963984540054
allslices = json.load(open("all_slices_trials.json"))

CLEAN = ["T2DM_HbA1c_GLP1only:ALL:dose", "Obesity_weight:ALL:baseline"]

def prior_inline(xt, xs, ys, ses, bw, mode, rng):
    prec = 1.0/np.maximum(ses**2, 1e-9)
    if mode == "uniform":
        w = prec
    else:
        xe = xs.copy()
        if mode == "scrambled":
            xe = rng.permutation(xe)
        w = np.exp(-0.5*((xe-xt)/bw)**2) * prec
    ws = w.sum()
    if ws <= 0:
        return np.nan, np.inf
    mu = (w*ys).sum()/ws
    within = (w**2*ses**2).sum()/ws**2
    between = (w*(ys-mu)**2).sum()/ws
    return mu, np.sqrt(max(within+between, 1e-9))

def loo_mae(x, y, s, bw, mode, seed=1):
    rng = np.random.default_rng(seed)
    errs = []
    for i in range(len(x)):
        m = np.ones(len(x), bool); m[i] = False
        mu, se = prior_inline(x[i], x[m], y[m], s[m], bw, mode, rng)
        if np.isfinite(mu):
            errs.append(abs(mu-y[i]))
    return np.array(errs)

def boot(ea, eb, n=4000, seed=7):
    rng = np.random.default_rng(seed); d = ea-eb
    bi = rng.integers(0, len(d), size=(n, len(d)))
    md = d[bi].mean(axis=1)
    return float(d.mean()), float(np.quantile(md,0.025)), float(np.quantile(md,0.975))

print("FROM-SCRATCH re-derivation (inline numpy only):\n")
for lab in CLEAN:
    e = allslices[lab]; key = e["key"]; ts = e["trials"]
    x = np.array([t[key] for t in ts], float)
    y = np.array([t["y"] for t in ts], float)
    s = np.array([t["se"] for t in ts], float)
    bw = float(np.std(x))  # central bandwidth = SD
    er = loo_mae(x, y, s, bw, "relevance")
    eu = loo_mae(x, y, s, bw, "uniform")
    es = loo_mae(x, y, s, bw, "scrambled")
    du, lou, hiu = boot(er, eu); ds, los, his = boot(er, es)
    print(f"{lab}  (n={len(ts)}, bw=SD={bw:.3g})")
    print(f"  MAE: relevance={er.mean():.3f}  uniform={eu.mean():.3f}  scrambled={es.mean():.3f}")
    print(f"  rel-uniform  {du:+.3f} [{lou:+.3f},{hiu:+.3f}]  {'WIN' if hiu<0 else 'n.s.'}")
    print(f"  rel-scramble {ds:+.3f} [{los:+.3f},{his:+.3f}]  {'WIN' if his<0 else 'n.s.'}\n")
