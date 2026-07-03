"""Benchmark the registry-scale field against the MODERN frontier -- truth-gated.

B1  transductive reconstruction : MAE + coverage/width, hand-field vs GP-learned
    kernel vs robust-MAP vs g-modeling vs hierarchical cross-MA Bayes.
B2  dynamic borrowing (down-sample): fuse own(m sibs) (+) cross-MA field prior via
    power / commensurate / SAM / robust-MAP-mixture / precision-fusion (mine).
B3  transportability : covariate g-computation (ML-NMR / IOSW analogue) on the
    covariate-bearing MAs.
CAL conformal / jackknife+ distribution-free intervals vs model-based PI.
"""
from __future__ import annotations
import json
import sys
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # borrowing/ for borrowing_transport
warnings.filterwarnings("ignore")
from corpus import load_corpus
from field import prep, predict as field_predict, Z975
from downsample import cross_block, home_pool
from field_modern import (dl_tau2, robust_map, mixture_posterior_mean,
                          power_prior_fuse, commensurate_fuse, sam_fuse,
                          gp_field_loo, npmle_g, gmodel_post_mean,
                          hier_crossMA_predict)


def pboot(a, b, n=5000, seed=7):
    m = np.isfinite(a) & np.isfinite(b)
    d = (a - b)[m]
    if len(d) < 2:
        return np.nan, np.nan, np.nan
    rng = np.random.default_rng(seed)
    bi = rng.integers(0, len(d), size=(n, len(d)))
    md = d[bi].mean(1)
    return float(d.mean()), *np.quantile(md, [0.025, 0.975])


# ============================================================ B1 transductive
def run_B1(df):
    df = prep(df)
    n = len(df)
    P = {k: np.full(n, np.nan) for k in
         ["global", "withinMA", "field_hand", "robust_map", "gp_field",
          "hier_crossMA", "gmodel"]}
    S = {k: np.full(n, np.nan) for k in P}       # predictive sd

    # field.py baselines
    for i in range(n):
        for key, mode in [("global", "global"), ("withinMA", "withinMA_rel"),
                          ("field_hand", "field_adapt")]:
            mu, se = field_predict(df, i, mode)
            P[key][i] = mu; S[key][i] = se

    # per-family modern methods
    for fam, sub in df.groupby("family"):
        idx = sub.index.values
        # GP learned kernel (one fit per family, exact LOO)
        try:
            mu_gp, sd_gp = gp_field_loo(sub)
            P["gp_field"][idx] = mu_gp; S["gp_field"][idx] = sd_gp
        except Exception as e:
            print(f"  [GP {fam} failed: {e}]")
        # g-modeling NPMLE prior (transductive prior mean; uses no own data)
        grid, pi = npmle_g(sub["yi"].values, sub["se"].values)
        P["gmodel"][idx] = float((grid * pi).sum())
        S["gmodel"][idx] = np.sqrt(((grid ** 2) * pi).sum() - (grid * pi).sum() ** 2)

    # robust-MAP (same-MA MAP mean) + hierarchical cross-MA (per target)
    for i in range(n):
        t = df.iloc[i]
        sib = df[(df.ma == t.ma) & (df.index != i)]
        if len(sib) >= 1:
            _, mu, se = dl_tau2(sib["yi"].values, sib["se"].values)
            P["robust_map"][i] = mu
            m_, s_, w_ = robust_map(sib["yi"].values, sib["se"].values)
            S["robust_map"][i] = float(np.sqrt((w_ * (s_ ** 2 + m_ ** 2)).sum() - (w_ * m_).sum() ** 2))
        try:
            mu_h, se_h = hier_crossMA_predict(df, i)
            P["hier_crossMA"][i] = mu_h; S["hier_crossMA"][i] = se_h
        except Exception:
            pass

    y = df["yi"].values; se_t = df["se"].values
    rows = []
    for k in P:
        err = np.abs(P[k] - y)
        half = Z975 * np.sqrt(S[k] ** 2 + se_t ** 2)
        cov = ((P[k] - half <= y) & (y <= P[k] + half)).astype(float)
        cov[~np.isfinite(P[k])] = np.nan
        rows.append(dict(method=k, n=int(np.isfinite(err).sum()),
                         MAE=np.nanmean(err), cover=np.nanmean(cov),
                         width=np.nanmean(2 * half)))
    return df, P, S, pd.DataFrame(rows)


# ============================================================ CAL conformal
def conformal_eval(df, P, alpha=0.10):
    """jackknife+ / split-conformal coverage within each family (Vovk 2005;
    Lei et al. 2018 JASA; Barber et al. 2021 AoS). q = (1-alpha) quantile of the
    OTHER studies' LOO abs-residuals; coverage = |y_t - pred_t| <= q."""
    y = df["yi"].values
    out = []
    for k, pred in P.items():
        cov, wid = [], []
        for fam, sub in df.groupby("family"):
            idx = sub.index.values
            res = np.abs(pred[idx] - y[idx])
            ok = np.isfinite(res)
            idx, res = idx[ok], res[ok]
            for j in range(len(idx)):
                others = np.delete(res, j)
                q = np.quantile(others, 1 - alpha, method="higher")
                cov.append(res[j] <= q); wid.append(2 * q)
        out.append(dict(method=k, conf_cover=np.mean(cov), conf_width=np.mean(wid)))
    return pd.DataFrame(out)


# ============================================================ B2 dynamic borrow
def run_B2(df, MS=(1, 2, 3, 5), REPS=25):
    df = prep(df)
    rng = np.random.default_rng(11)
    cross = {i: cross_block(df, i) for i in range(len(df))}
    home_idx = {ma: df.index[df.ma == ma].values for ma in df.ma.unique()}
    methods = ["own_only", "power_prior", "commensurate", "sam",
               "robust_map", "precision_fuse", "conflict_aware_fuse"]
    acc = {m: {mm: [] for mm in methods} for m in MS}

    from field_modern import mixture_posterior_mean, robust_map as rmap
    from borrowing_transport import precision_fuse
    from field_learned import conflict_aware_fuse   # our DEPLOYED adaptive-power-prior fusion

    for i in range(len(df)):
        t = df.iloc[i]
        sibs = np.array([j for j in home_idx[t.ma] if j != i])
        Sc_wy, Sc_w = cross[i]
        if Sc_w <= 0:
            continue
        mu_p = Sc_wy / Sc_w
        # crude prior se from the cross pool spread
        se_p = 1.0 / np.sqrt(Sc_w) if Sc_w > 0 else np.inf
        for m in MS:
            if len(sibs) < m:
                continue
            for _ in range(REPS):
                pick = rng.choice(sibs, size=m, replace=False)
                Sh_wy, Sh_w = home_pool(df.loc[pick], t)
                if Sh_w <= 0:
                    continue
                y0 = Sh_wy / Sh_w; se0 = 1.0 / np.sqrt(Sh_w)
                preds = {
                    "own_only": y0,
                    "power_prior": power_prior_fuse(y0, se0, mu_p, se_p)[0],
                    "commensurate": commensurate_fuse(y0, se0, mu_p, se_p)[0],
                    "sam": sam_fuse(y0, se0, mu_p, se_p)[0],
                    "robust_map": _rmap_fuse(mu_p, se_p, y0, se0),
                    "precision_fuse": precision_fuse(y0, se0, mu_p, se_p)[0],
                    "conflict_aware_fuse": conflict_aware_fuse(y0, se0, mu_p, se_p)[0],
                }
                for mm, pv in preds.items():
                    acc[m][mm].append(abs(pv - t.yi))
    return acc, methods


def _rmap_fuse(mu_p, se_p, y0, se0):
    """robust-MAP mixture fuse: informative field prior + vague, updated by own."""
    from field_modern import mixture_posterior_mean
    vague = 5.0 * (abs(mu_p) + se_p + 1.0)
    means = np.array([mu_p, mu_p]); sds = np.array([se_p, vague]); wts = np.array([0.8, 0.2])
    return mixture_posterior_mean(means, sds, wts, y0, se0)[0]


# ============================================================ B3 transportability
def run_B3(df):
    """Covariate g-computation / IOSW analogue (Dahabreh et al. 2020, Biometrics
    76:1035; ML-NMR: Phillippo et al. 2020 JRSS-A 183:1189). Standardise donor
    effects to the target's covariate via a within-family meta-regression slope,
    then LOO-predict. Only MAs with a usable continuous covariate qualify."""
    df = prep(df)
    covs = {"bcg": "year", "molloy2014": "year", "crede2010": "year",
            "tannersmith2016": None}  # most staged MAs expose only year/none
    # use `year` as the shared transport covariate where present & variable
    results = []
    for ma, sub in df.groupby("ma"):
        yr = sub["year"]
        if yr.notna().sum() < 5 or yr.std() < 1e-6:
            continue
        sub = sub[yr.notna()].copy()
        y = sub["yi"].values; se = sub["se"].values; x = sub["year"].values
        w = 1.0 / se ** 2
        no_t, tr_t = [], []
        for j in range(len(sub)):
            keep = np.arange(len(sub)) != j
            yj, sej, xj, wj = y[keep], se[keep], x[keep], w[keep]
            # meta-regression slope (WLS)
            X = np.column_stack([np.ones_like(xj), xj])
            WX = X * wj[:, None]
            try:
                beta = np.linalg.solve(X.T @ WX, WX.T @ yj)
            except np.linalg.LinAlgError:
                continue
            mu_plain = (wj * yj).sum() / wj.sum()
            y_std = yj + beta[1] * (x[j] - xj)          # transport to target x
            mu_tr = (wj * y_std).sum() / wj.sum()
            no_t.append(abs(mu_plain - y[j])); tr_t.append(abs(mu_tr - y[j]))
        if len(no_t) >= 5:
            d, lo, hi = pboot(np.array(no_t), np.array(tr_t))
            results.append(dict(ma=ma, k=len(no_t), no_transport=np.mean(no_t),
                                transport=np.mean(tr_t), delta=d, lo=lo, hi=hi))
    return pd.DataFrame(results)


if __name__ == "__main__":
    df0 = load_corpus()
    print("=" * 78, "\nB1  TRANSDUCTIVE reconstruction (modern comparators)\n" + "=" * 78)
    df, P, S, b1 = run_B1(df0)
    b1 = b1.sort_values("MAE")
    print(b1.to_string(index=False, float_format=lambda v: f"{v:.4f}"))

    # honest GP robustness: refit hyper-params per fold (no shared-hyperparam LOO optimism)
    from field_modern import gp_field_kfold
    gp_kf = np.full(len(df), np.nan)
    for fam, sub in df.groupby("family"):
        gp_kf[sub.index.values] = gp_field_kfold(sub)
    err_kf = np.abs(gp_kf - df.yi.values)
    print(f"\n GP honest 10-fold refit MAE = {np.nanmean(err_kf):.4f}  "
          f"(vs R&W-LOO {b1[b1.method=='gp_field'].MAE.values[0]:.4f}; "
          f"within-MA {b1[b1.method=='withinMA'].MAE.values[0]:.4f})")
    d, lo, hi = pboot(err_kf, np.abs(P["withinMA"] - df.yi.values))
    print(f"   GP(10-fold) - withinMA = {d:+.4f} [{lo:+.4f},{hi:+.4f}]"
          f"{'  GP beats within-MA' if hi < 0 else '  n.s./worse'}")

    print("\n key contrasts vs the HAND field (negative = other method better):")
    for k in ["gp_field", "robust_map", "hier_crossMA", "withinMA", "gmodel"]:
        d, lo, hi = pboot(np.abs(P[k] - df.yi.values), np.abs(P["field_hand"] - df.yi.values))
        v = "beats hand-field" if hi < 0 else ("worse" if lo > 0 else "tie")
        print(f"   {k:14} - field_hand  {d:+.4f} [{lo:+.4f},{hi:+.4f}]  {v}")

    print("\n" + "=" * 78, "\nCAL  conformal / jackknife+ vs model PI (target 90%)\n" + "=" * 78)
    cal = conformal_eval(df, P, alpha=0.10)
    mrg = b1.merge(cal, on="method")[["method", "cover", "width", "conf_cover", "conf_width"]]
    print(mrg.to_string(index=False, float_format=lambda v: f"{v:.3f}"))

    print("\n" + "=" * 78, "\nB2  DYNAMIC BORROWING: fuse own(m) (+) cross-MA field prior\n" + "=" * 78)
    acc, methods = run_B2(df0)
    print(f"{'m':>3}" + "".join(f"{mm[:12]:>14}" for mm in methods))
    b2json = {}
    for m in sorted(acc):
        row = f"{m:>3}"
        b2json[m] = {}
        for mm in methods:
            arr = np.array(acc[m][mm])
            row += f"{arr.mean():>14.4f}" if len(arr) else f"{'--':>14}"
            b2json[m][mm] = float(arr.mean()) if len(arr) else None
        print(row)
    # best vs precision_fuse at m=1
    print("\n paired vs precision_fuse (mine), m=1  (negative = other better):")
    for mm in methods:
        if mm == "precision_fuse":
            continue
        d, lo, hi = pboot(np.array(acc[1][mm]), np.array(acc[1]["precision_fuse"]))
        print(f"   {mm:14} {d:+.4f} [{lo:+.4f},{hi:+.4f}]")

    print("\n" + "=" * 78, "\nB3  TRANSPORTABILITY (covariate g-computation / ML-NMR analogue)\n" + "=" * 78)
    b3 = run_B3(df0)
    if len(b3):
        print(b3.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    else:
        print("  no MA had a usable variable continuous covariate at the node level")

    json.dump({"B1": b1.to_dict("records"),
               "conformal": cal.to_dict("records"),
               "B2": b2json,
               "B3": b3.to_dict("records") if len(b3) else []},
              open("benchmark_results.json", "w"), indent=2)
    print("\nwrote benchmark_results.json")
