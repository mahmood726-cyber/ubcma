"""5-way real leave-one-trial-out on ONE slice -- exact replication of the
pilot-2 GLP1-dose headline (real_glp1.py), generalised to any slice.

For each held-out real trial t (the target, ZERO own data -> pure transportability
prediction) we form a borrowing prior from the OTHER real trials four ways and
score against the trial's REAL observed effect y_t (the truth):
  * NMA       : random-effects (REML) pooled mean of the other trials   [textbook baseline]
  * uniform   : 1/se^2 precision-only field mean  (= no-relevance null)
  * relevance : Gaussian dose/covariate-distance kernel x precision      [the thesis]
  * scrambled : relevance kernel but covariates permuted                 [scrambled null]
TRUTH = real held-out y_t. Score |pred - y_t| (MAE), 95% PI coverage, and a paired
bootstrap of relevance MAE minus each null's MAE (want CI < 0 = relevance better).

Binding (per slice): relevance beats BOTH nulls (uniform AND scrambled), CIs<0;
beats-or-ties NMA; coverage near nominal. Run across bw in {SD/2, SD, 1.5*SD}.

Usage: python run_slice.py <label>   (label as in qualifying_slices_v2.json)
       python run_slice.py --all
"""
import json, sys, io, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))      # borrowing/
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src")) # ubcma
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from borrowing_field2 import covariate_prior, Z975
from ubcma.comparators import reml_estimator


def nma_prior(ys, ses):
    """Random-effects (REML) pooled estimate of the OTHER trials = textbook NMA baseline."""
    ys = np.asarray(ys, float); ses = np.asarray(ses, float)
    if len(ys) == 1:
        return float(ys[0]), float(ses[0])
    r = reml_estimator(ys, ses)
    return float(r["mu"]), float(r["se"])


def loo(trials, key, bw, mode, seed=1):
    x = np.array([t[key] for t in trials], float)
    y = np.array([t["y"] for t in trials], float)
    s = np.array([t["se"] for t in trials], float)
    errs, cov, preds = [], [], []
    rng = np.random.default_rng(seed)
    for i in range(len(trials)):
        m = np.ones(len(trials), bool); m[i] = False
        if mode == "nma":
            mu_p, se_p = nma_prior(y[m], s[m])
        else:
            mu_p, se_p, _ = covariate_prior(x[i], x[m], y[m], s[m], bw, mode=mode, rng=rng)
        if not np.isfinite(mu_p):
            continue
        errs.append(abs(mu_p - y[i]))
        half = Z975 * np.sqrt(se_p**2 + s[i]**2)
        cov.append(mu_p - half <= y[i] <= mu_p + half)
        preds.append(mu_p)
    return np.array(errs), np.array(cov), np.array(preds)


def paired_boot(ea, eb, n=4000, seed=7):
    rng = np.random.default_rng(seed)
    d = ea - eb  # relevance - null ; want < 0
    bi = rng.integers(0, len(d), size=(n, len(d)))
    md = d[bi].mean(axis=1)
    lo, hi = np.quantile(md, [0.025, 0.975])
    return float(d.mean()), float(lo), float(hi), bool(hi < 0)


def run_slice(label, trials, key):
    x = np.array([t[key] for t in trials], float)
    xsd = float(np.std(x))
    print(f"\n############ {label}  (modifier={key}, n={len(trials)}, "
          f"x in [{x.min():.3g},{x.max():.3g}], SD={xsd:.3g}) ############")
    print(f"{'bw':>8}{'rel MAE':>9}{'cover':>7}{'NMA':>8}{'unif':>8}{'scr':>8}"
          f"   rel-unif[CI]            rel-scr[CI]            rel-NMA[CI]")
    rows = []
    for bw in [round(xsd/2, 4), round(xsd, 4), round(1.5*xsd, 4)]:
        if bw <= 0:
            continue
        er_rel, cv_rel, _ = loo(trials, key, bw, "relevance")
        er_uni, cv_uni, _ = loo(trials, key, bw, "uniform")
        er_scr, cv_scr, _ = loo(trials, key, bw, "scrambled")
        er_nma, cv_nma, _ = loo(trials, key, bw, "nma")
        d_ru, lo_ru, hi_ru, win_ru = paired_boot(er_rel, er_uni)
        d_rs, lo_rs, hi_rs, win_rs = paired_boot(er_rel, er_scr)
        d_rn, lo_rn, hi_rn, win_rn = paired_boot(er_rel, er_nma)
        print(f"{bw:>8.3g}{er_rel.mean():>9.3f}{cv_rel.mean():>7.2f}{er_nma.mean():>8.3f}"
              f"{er_uni.mean():>8.3f}{er_scr.mean():>8.3f}   "
              f"{d_ru:+.3f}[{lo_ru:+.3f},{hi_ru:+.3f}]{'W' if win_ru else ' '}  "
              f"{d_rs:+.3f}[{lo_rs:+.3f},{hi_rs:+.3f}]{'W' if win_rs else ' '}  "
              f"{d_rn:+.3f}[{lo_rn:+.3f},{hi_rn:+.3f}]{'W' if win_rn else ' '}")
        rows.append(dict(bw=bw, mae_rel=float(er_rel.mean()), mae_uni=float(er_uni.mean()),
            mae_scr=float(er_scr.mean()), mae_nma=float(er_nma.mean()),
            cover_rel=float(cv_rel.mean()), cover_nma=float(cv_nma.mean()),
            cover_uni=float(cv_uni.mean()),
            d_rel_uni=d_ru, ci_rel_uni=[lo_ru, hi_ru], win_uni=win_ru,
            d_rel_scr=d_rs, ci_rel_scr=[lo_rs, hi_rs], win_scr=win_rs,
            d_rel_nma=d_rn, ci_rel_nma=[lo_rn, hi_rn], win_nma=win_rn))
    # slice verdict at central bandwidth (bw = SD)
    mid = rows[1] if len(rows) >= 2 else rows[0]
    verdict = bool(mid["win_uni"] and mid["win_scr"])
    print(f"  --> central-bw verdict: beats BOTH nulls = {verdict}  "
          f"(unif {'WIN' if mid['win_uni'] else 'n.s.'}, scr {'WIN' if mid['win_scr'] else 'n.s.'}, "
          f"NMA {'WIN' if mid['win_nma'] else 'n.s./tie'})")
    return dict(label=label, key=key, n=len(trials), rows=rows, beats_both=verdict,
                central=mid)


if __name__ == "__main__":
    allslices = json.load(open("all_slices_trials.json"))
    # curated LOO set: clean qualifiers + near-misses + a Simpson single-mol +
    # real-data FLAT negative controls (the in-data beta=0 inertia check).
    CURATED = [
        "T2DM_HbA1c_GLP1only:ALL:dose",     # CLEAN  -- anchor (reproduced)
        "Obesity_weight:ALL:baseline",      # CLEAN  -- new modifier (baseline severity)
        "Obesity_weight:tirzepatide:dose",  # NEARMISS single-molecule dose-response
        "Obesity_weight:ALL:dose",          # NEARMISS within-molecule strong
        "Depression:vortioxetine:dose",     # single-mol, R2=1 but permutation-conservative
        "T2DM_HbA1c:dapagliflozin:dose",    # FLAT control (SGLT2 dose plateaus)
        "T2DM_HbA1c:ALL:dose",              # FLAT control (cross-class mix)
    ]
    targets = list(allslices) if (len(sys.argv) > 1 and sys.argv[1] == "--all") \
        else ([sys.argv[1]] if len(sys.argv) > 1 else [c for c in CURATED if c in allslices])
    results = {}
    for label in targets:
        entry = allslices[label]
        r = run_slice(label, entry["trials"], entry["key"])
        r["tier"] = entry.get("tier")
        r["screen"] = {k: entry.get(k) for k in ("slope", "perm_p", "R2", "single_mol")}
        results[label] = r
    json.dump(results, open("loo_results_v2.json", "w"), indent=1, default=str)
    print(f"\nwrote loo_results_v2.json ({len(results)} slices)")
