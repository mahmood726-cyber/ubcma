"""AGGREGATE transport-over-relevance across every qualifying strong-modifier slice.

Priority-2 of the expansion job: is the INCREMENTAL transport gain OVER relevance-only
robust once k grows past BCG's 13? Pools the per-trial paired LOO errors across all
slices (BCG latitude k=13 + rotavirus U5MR k=29 = 42 real held-out trials) and reports
the pooled transport-minus-relevance honestly, win or null. Also pools the (already
robust) transport-minus-NMA and relevance-minus-uniform headlines.

Design (matches the per-slice gate; vendor-independent from-scratch pooler):
  * generic 5-way real-LOO on any slice = (trials.json, covariate key). TRUTH = real
    held-out logRR. transport - relevance isolates the g-computation / standardisation step
    because relevance & transport share ONE kernel and differ only by the shift.
  * per-trial paired error d_i = |mu_tran_i - y_i| - |mu_rel_i - y_i|  (negative = transport better)
  * per-slice delta = mean(d_i); SE = sd(d_i)/sqrt(n_slice).
  * POOL two ways, honestly: inverse-variance fixed-effect (standard meta; favours the
    bigger/tighter slice) AND equal-weight (each slice = one exchangeable test of the method).
  * stratified bootstrap CI: resample d_i WITHIN each slice, recompute slice deltas, pool
    -> percentile CI. Also Q/I^2 heterogeneity across slices.
  * reported at the pre-registered central bw (SD) [primary] and narrow bw (SD/2) [secondary],
    plus an Epanechnikov-kernel robustness pass (methodologically-distinct 3rd witness).
"""
import json, io, sys
import numpy as np
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent  # borrowing/

SLICES = [
    dict(name="BCG (latitude)", path=ROOT / "bcg" / "bcg_trials.json", cov="ablat"),
    dict(name="Rotavirus (U5MR)", path=ROOT / "rota" / "rota_trials.json", cov="u5mr"),
]


def mp_reml(y, s):
    y = np.asarray(y, float); v = np.asarray(s, float) ** 2
    if len(y) == 1:
        return float(y[0]), float(np.sqrt(v[0]))
    tau2 = 0.0
    for _ in range(100):
        w = 1.0 / (v + tau2); mu = (w * y).sum() / w.sum()
        Q = (w * (y - mu) ** 2).sum(); denom = w.sum() - (w ** 2).sum() / w.sum()
        if Q <= len(y) - 1 or denom <= 0:
            break
        newt = tau2 + (Q - (len(y) - 1)) / denom
        if abs(newt - tau2) < 1e-8:
            tau2 = max(newt, 0.0); break
        tau2 = max(newt, 0.0)
    w = 1.0 / (v + tau2); mu = (w * y).sum() / w.sum()
    return float(mu), float(np.sqrt(1.0 / w.sum()))


def re_slope(x, y, s):
    n = len(y)
    if n < 4 or np.std(x) < 1e-9:
        return 0.0
    X = np.column_stack([np.ones(n), x]); w = 1.0 / np.maximum(np.asarray(s) ** 2, 1e-12)
    WX = X * w[:, None]; XtWX = X.T @ WX
    beta = np.linalg.solve(XtWX, WX.T @ y); resid = y - X @ beta
    Qres = float((w * resid ** 2).sum())
    trace = w.sum() - np.trace(np.linalg.inv(XtWX) @ (X.T @ (w[:, None] ** 2 * X)))
    tau2 = max(0.0, (Qres - (n - 2)) / trace) if trace > 0 else 0.0
    W2 = 1.0 / (np.asarray(s) ** 2 + tau2); WX2 = X * W2[:, None]
    return float(np.linalg.solve(X.T @ WX2, WX2.T @ y)[1])


def kern(xe, xt, bw, shape):
    u = (xe - xt) / bw
    if shape == "epan":
        k = np.maximum(0.0, 1.0 - u ** 2)
        return np.where(k > 0, k, 1e-9)  # tiny floor so far donors never fully vanish
    return np.exp(-0.5 * u ** 2)


def prior(xt, xs, ys, ses, bw, mode, rng, shape="gauss"):
    prec = 1.0 / np.maximum(ses ** 2, 1e-12)
    if mode == "nma":
        return mp_reml(ys, ses)
    if mode == "uniform":
        w = prec; yeff = ys
    else:
        xe = xs.copy()
        if mode == "scrambled":
            xe = rng.permutation(xe)
        w = kern(xe, xt, bw, shape) * prec
        if mode == "relevance":
            yeff = ys
        else:
            b = re_slope(xs, ys, ses)
            yeff = ys + b * (xt - xe)
    ws = float(w.sum())
    if ws <= 0:
        return np.nan, np.inf
    mu = float((w * yeff).sum() / ws)
    within = float((w ** 2 * ses ** 2).sum() / ws ** 2)
    between = float((w * (yeff - mu) ** 2).sum() / ws)
    return mu, float(np.sqrt(max(within + between, 1e-9)))


def loo_errs(TRS, cov, bw, mode, shape="gauss", seed=1):
    Y = np.array([t["y"] for t in TRS]); S = np.array([t["se"] for t in TRS])
    X = np.array([t[cov] for t in TRS]); N = len(TRS)
    rng = np.random.default_rng(seed); e = np.full(N, np.nan)
    for i in range(N):
        m = np.ones(N, bool); m[i] = False
        mu, _ = prior(X[i], X[m], Y[m], S[m], bw, mode, rng, shape=shape)
        if np.isfinite(mu):
            e[i] = abs(mu - Y[i])
    return e


def slice_deltas(sl, bw_mult, shape="gauss"):
    TRS = json.load(open(sl["path"]))["trials"]
    x = np.array([t[sl["cov"]] for t in TRS]); bw = float(x.std()) * bw_mult
    out = {}
    e = {m: loo_errs(TRS, sl["cov"], bw, m, shape=shape) for m in
         ["nma", "uniform", "relevance", "transport"]}
    for pair, (a, b) in {"tran_rel": ("transport", "relevance"),
                         "tran_nma": ("transport", "nma"),
                         "rel_unif": ("relevance", "uniform")}.items():
        d = e[a] - e[b]
        d = d[np.isfinite(d)]
        out[pair] = d
    out["n"] = len(TRS)
    return out


def iv_pool(deltas, weights):
    d = np.array(deltas); w = np.array(weights)
    mu = float((w * d).sum() / w.sum()); se = float(np.sqrt(1.0 / w.sum()))
    return mu, se


def het(deltas, ses):
    d = np.array(deltas); w = 1.0 / np.array(ses) ** 2
    mu = (w * d).sum() / w.sum(); Q = float((w * (d - mu) ** 2).sum())
    dfree = len(d) - 1; I2 = max(0.0, (Q - dfree) / Q) * 100 if Q > 0 else 0.0
    return Q, dfree, I2


def aggregate(bw_mult, shape="gauss", B=8000, seed=11):
    per = [(sl["name"], slice_deltas(sl, bw_mult, shape=shape)) for sl in SLICES]
    rng = np.random.default_rng(seed)
    res = {}
    for pair in ["tran_rel", "tran_nma", "rel_unif"]:
        arrs = [d[pair] for _, d in per]
        means = [float(a.mean()) for a in arrs]
        ses = [float(a.std(ddof=1) / np.sqrt(len(a))) for a in arrs]
        ns = [len(a) for a in arrs]
        # inverse-variance fixed-effect
        iv_mu, iv_se = iv_pool(means, [1.0 / s ** 2 for s in ses])
        # equal-weight
        eq_mu = float(np.mean(means)); eq_se = float(np.sqrt(np.mean([s ** 2 for s in ses])) / np.sqrt(len(means)))
        # stratified bootstrap (resample d_i within each slice), IV-pool with fixed weights
        wfix = np.array([1.0 / s ** 2 for s in ses])
        boot_iv = np.empty(B); boot_eq = np.empty(B)
        for b in range(B):
            bm = []
            for a in arrs:
                idx = rng.integers(0, len(a), len(a)); bm.append(a[idx].mean())
            bm = np.array(bm)
            boot_iv[b] = (wfix * bm).sum() / wfix.sum()
            boot_eq[b] = bm.mean()
        Q, dfree, I2 = het(means, ses)
        res[pair] = dict(per_slice=list(zip([n for n, _ in per], means, ses, ns)),
                         iv=(iv_mu, iv_se, float(np.quantile(boot_iv, .025)), float(np.quantile(boot_iv, .975))),
                         eq=(eq_mu, float(np.quantile(boot_eq, .025)), float(np.quantile(boot_eq, .975))),
                         het=(Q, dfree, I2))
    return res


def show(tag, res):
    print(f"\n===== {tag} =====")
    for pair, lbl in [("tran_rel", "TRANSPORT - RELEVANCE (the binding incremental step)"),
                      ("tran_nma", "transport - NMA (full method vs textbook)"),
                      ("rel_unif", "relevance - uniform (kernel vs no-relevance)")]:
        r = res[pair]
        print(f"\n  {lbl}")
        for name, m, se, n in r["per_slice"]:
            print(f"    {name:20} k={n:2}  delta {m:+.3f}  (SE {se:.3f})  95%CI[{m-1.96*se:+.3f},{m+1.96*se:+.3f}]")
        iv_mu, iv_se, iv_lo, iv_hi = r["iv"]
        eq_mu, eq_lo, eq_hi = r["eq"]
        Q, dfree, I2 = r["het"]
        w = "  <-- WIN (CI<0)" if iv_hi < 0 else ""
        print(f"    POOLED inv-var : {iv_mu:+.3f}  boot95%[{iv_lo:+.3f},{iv_hi:+.3f}] (analytic SE {iv_se:.3f}){w}")
        w2 = "  <-- WIN" if eq_hi < 0 else ""
        print(f"    POOLED equal-wt: {eq_mu:+.3f}  boot95%[{eq_lo:+.3f},{eq_hi:+.3f}]{w2}")
        print(f"    heterogeneity  : Q={Q:.2f} (df={dfree}) I^2={I2:.0f}%")


def main():
    print("AGGREGATE transport-over-relevance across strong-modifier slices")
    print(f"slices: {', '.join(sl['name'] for sl in SLICES)}  (total held-out trials = "
          f"{sum(len(json.load(open(sl['path']))['trials']) for sl in SLICES)})")
    r_c = aggregate(1.0, "gauss"); show("PRIMARY: central bandwidth (SD), Gaussian kernel", r_c)
    r_n = aggregate(0.5, "gauss"); show("SECONDARY: narrow bandwidth (SD/2), Gaussian kernel", r_n)
    r_e = aggregate(1.0, "epan"); show("ROBUSTNESS: central bw, Epanechnikov kernel (distinct 3rd witness)", r_e)
    json.dump(dict(central=jsonify(r_c), narrow=jsonify(r_n), epan=jsonify(r_e)),
              open(HERE / "aggregate_results.json", "w"), indent=1)
    print("\nwrote aggregate_results.json")


def jsonify(res):
    return {p: dict(per_slice=[[n, m, se, k] for n, m, se, k in r["per_slice"]],
                    iv=list(r["iv"]), eq=list(r["eq"]), het=list(r["het"]))
            for p, r in res.items()}


if __name__ == "__main__":
    main()
