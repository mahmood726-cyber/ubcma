"""EXPERIMENT 1 -- 5-way real leave-one-trial-out on rotavirus (the fair transport test).

For each held-out real BCG trial t (ZERO own data -> pure transportability prediction)
we form a borrowing prior from the OTHER 12 trials FIVE ways and score against the
trial's REAL observed logRR y_t (the truth):

  1. nma        : random-effects (REML) pooled mean of other trials      [textbook baseline]
  2. uniform    : 1/se^2 precision-only field mean        (= NO-RELEVANCE null)
  3. relevance  : Gaussian U5MR-distance kernel x precision, RAW donor logRR
                  (down-weight far-U5MR donors; NO standardisation)   [pilot-2 relevance]
  4. transport  : relevance kernel x precision, donor logRR STANDARDISED to the target
                  U5MR:  y_s->t = y_s + beta_lat (lat_t - lat_s)      [relevance x transportability]
                  beta_lat = LOO random-effects meta-regression slope from the 12 donors only.
  5. scrambled  : transport but donor U5MRs PERMUTED (kernel + shift broken)  [scrambled null]

Because U5MR is the ONLY covariate, relevance and transport share the SAME kernel and
differ ONLY by the standardisation shift -- so (transport - relevance) isolates exactly the
g-computation / transportability step. THE BINDING QUESTION: does transport BEAT
relevance-only on real held-out trials, where the modifier is genuinely strong?

Controls: beta=0 (transport with shift forced 0 -> must collapse onto relevance = inertia);
target=pool (standardise to the donor centroid not the real target -> shift should add noise).
TRUTH = real held-out y_t throughout.
"""
import json, io, sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from ubcma.comparators import reml_estimator

Z975 = 1.959963984540054
D = json.load(open(Path(__file__).parent / "rota_trials.json"))
TR = D["trials"]
Y = np.array([t["y"] for t in TR]); S = np.array([t["se"] for t in TR])
LAT = np.array([t["u5mr"] for t in TR]); N = len(TR)


def re_slope(lat, y, s):
    """LOO-safe random-effects (DL) meta-regression slope of y on U5MR (donors only)."""
    n = len(y)
    if n < 4 or np.std(lat) < 1e-9:
        return 0.0
    X = np.column_stack([np.ones(n), lat]); w = 1.0 / np.maximum(s**2, 1e-12)
    WX = X * w[:, None]; XtWX = X.T @ WX
    beta = np.linalg.solve(XtWX, WX.T @ y); resid = y - X @ beta
    Qres = float((w * resid**2).sum())
    trace = w.sum() - np.trace(np.linalg.inv(XtWX) @ (X.T @ (w[:, None]**2 * X)))
    tau2 = max(0.0, (Qres - (n - 2)) / trace) if trace > 0 else 0.0
    W2 = 1.0 / (s**2 + tau2); WX2 = X * W2[:, None]
    return float(np.linalg.solve(X.T @ WX2, WX2.T @ y)[1])


def prior(xt, xs, ys, ses, bw, mode, rng, beta_override=None, target_for_shift=None):
    prec = 1.0 / np.maximum(ses**2, 1e-12)
    if mode == "nma":
        if len(ys) == 1:
            return float(ys[0]), float(ses[0])
        r = reml_estimator(ys, ses); return float(r["mu"]), float(r["se"])
    if mode == "uniform":
        w = prec; yeff = ys
    else:
        xeff = xs.copy()
        if mode == "scrambled":
            xeff = rng.permutation(xeff)
        k = np.exp(-0.5 * ((xeff - xt) / bw) ** 2)
        w = k * prec
        if mode in ("relevance",):
            yeff = ys
        else:  # transport / scrambled / target=pool variants -> standardise
            if beta_override is not None:
                b = beta_override
            else:
                b = re_slope(xs, ys, ses)        # estimated from donors only (LOO-safe)
            tgt = xt if target_for_shift is None else target_for_shift
            yeff = ys + b * (tgt - xeff)
    wsum = float(w.sum())
    if wsum <= 0:
        return np.nan, np.inf
    mu = float((w * yeff).sum() / wsum)
    within = float((w**2 * ses**2).sum() / wsum**2)
    between = float((w * (yeff - mu)**2).sum() / wsum)
    return mu, float(np.sqrt(max(within + between, 1e-9)))


def loo(bw, mode, beta_override=None, target_pool=False, seed=1):
    rng = np.random.default_rng(seed)
    errs, cov, betas = [], [], []
    for i in range(N):
        m = np.ones(N, bool); m[i] = False
        tgt = float(LAT[m].mean()) if target_pool else None
        mu, se = prior(LAT[i], LAT[m], Y[m], S[m], bw, mode, rng,
                       beta_override=beta_override, target_for_shift=tgt)
        if not np.isfinite(mu):
            continue
        errs.append(abs(mu - Y[i]))
        half = Z975 * np.sqrt(se**2 + S[i]**2)
        cov.append(mu - half <= Y[i] <= mu + half)
    return np.array(errs), np.array(cov)


def paired_boot(ea, eb, n=4000, seed=7):
    rng = np.random.default_rng(seed); d = ea - eb
    bi = rng.integers(0, len(d), size=(n, len(d)))
    md = d[bi].mean(axis=1)
    return float(d.mean()), float(np.quantile(md, .025)), float(np.quantile(md, .975))


def fmt(tag, ea, eb):
    d, lo, hi = paired_boot(ea, eb)
    return f"{tag} {d:+.3f}[{lo:+.3f},{hi:+.3f}]{'W' if hi < 0 else ' '}"


def main():
    xsd = float(LAT.std())
    print(f"rotavirus 5-way LOO  (n={N}, U5MR SD={xsd:.1f}, RE meta-reg slope on full set="
          f"{re_slope(LAT, Y, S):+.4f}/deg)")
    print(f"  TRUTH = real held-out logRR.  Binding: does TRANSPORT beat RELEVANCE-only?\n")
    print(f"{'bw':>6} | {'MAE: nma':>9}{'unif':>7}{'rel':>7}{'tran':>7}{'scr':>7} | "
          f"{'cover(rel/tran)':>16} | key paired deltas (CI<0 = better)")
    rows = []
    for bw in [round(xsd/2, 3), round(xsd, 3), round(1.5*xsd, 3)]:
        e_nma, c_nma = loo(bw, "nma")
        e_uni, c_uni = loo(bw, "uniform")
        e_rel, c_rel = loo(bw, "relevance")
        e_tra, c_tra = loo(bw, "transport")
        e_scr, c_scr = loo(bw, "scrambled")
        d_tr, lo_tr, hi_tr = paired_boot(e_tra, e_rel)   # THE binding delta
        print(f"{bw:>6.1f} | {e_nma.mean():>9.3f}{e_uni.mean():>7.3f}{e_rel.mean():>7.3f}"
              f"{e_tra.mean():>7.3f}{e_scr.mean():>7.3f} | "
              f"{c_rel.mean():>7.2f}/{c_tra.mean():<8.2f} | "
              f"{fmt('tran-rel', e_tra, e_rel)}  {fmt('tran-scr', e_tra, e_scr)}  "
              f"{fmt('rel-unif', e_rel, e_uni)}  {fmt('tran-nma', e_tra, e_nma)}")
        rows.append(dict(bw=bw,
            mae=dict(nma=e_nma.mean(), uni=e_uni.mean(), rel=e_rel.mean(),
                     tran=e_tra.mean(), scr=e_scr.mean()),
            cover=dict(nma=c_nma.mean(), uni=c_uni.mean(), rel=c_rel.mean(),
                       tran=c_tra.mean(), scr=c_scr.mean()),
            d_tran_rel=[d_tr, lo_tr, hi_tr],
            d_tran_scr=list(paired_boot(e_tra, e_scr)),
            d_tran_uni=list(paired_boot(e_tra, e_uni)),
            d_rel_uni=list(paired_boot(e_rel, e_uni)),
            d_rel_scr=list(paired_boot(e_rel, e_scr)),
            d_tran_nma=list(paired_boot(e_tra, e_nma)),
            d_rel_nma=list(paired_boot(e_rel, e_nma))))

    bw = round(xsd, 3)
    print(f"\nCONTROLS (central bw={bw}):")
    e_rel, _ = loo(bw, "relevance")
    e_b0, _ = loo(bw, "transport", beta_override=0.0)
    d, lo, hi = paired_boot(e_b0, e_rel)
    print(f"  beta=0 inertia (transport shift forced 0 vs relevance): "
          f"MAE {e_b0.mean():.3f} vs {e_rel.mean():.3f}  delta {d:+.4f}[{lo:+.4f},{hi:+.4f}] "
          f"-> {'INERT (collapses onto relevance)' if abs(d) < 0.02 else 'NOT inert (BUG)'}")
    e_tp, _ = loo(bw, "transport", target_pool=True)
    e_tra, _ = loo(bw, "transport")
    d, lo, hi = paired_boot(e_tp, e_tra)
    print(f"  target=pool (standardise to donor centroid not real target): "
          f"MAE {e_tp.mean():.3f} vs real-target {e_tra.mean():.3f}  delta {d:+.3f}[{lo:+.3f},{hi:+.3f}]")

    central = rows[1]
    dtr = central["d_tran_rel"]
    verdict = "YES -- transport beats relevance-only" if dtr[2] < 0 else \
              ("NO -- transport does NOT beat relevance-only (CI includes 0)"
               if dtr[0] >= -1e-9 or dtr[2] >= 0 else "?")
    print(f"\n=== KEY VERDICT (central bw) ===")
    print(f"  transport - relevance MAE = {dtr[0]:+.3f} [{dtr[1]:+.3f}, {dtr[2]:+.3f}]")
    print(f"  --> {verdict}")
    json.dump(dict(n=N, x_sd=xsd, rows=rows, verdict=verdict,
                   d_tran_rel_central=dtr), open(Path(__file__).parent / "rota_loo.json", "w"), indent=1)
    print("  wrote rota_loo.json")


if __name__ == "__main__":
    main()
