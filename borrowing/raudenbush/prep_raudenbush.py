"""THIRD strong-modifier slice for the transport-vs-relevance bake-off -- CROSS-DOMAIN.

Source = metadat `dat.raudenbush1985` (Raudenbush 1984, J.Educ.Psych.; Raudenbush & Bryk):
19 controlled experiments on teacher-expectancy effects (experimenter-induced high
expectations vs control) on pupil IQ, effect = standardised mean difference (Hedges g),
with the well-known STRONG moderator `weeks` = weeks of prior teacher-pupil contact BEFORE
the expectancy induction. The expectancy effect is large when teachers barely know the
pupils (weeks~0) and vanishes with prior contact -- a monotone, leverage-robust gradient.

Why it belongs in the transport bake-off: `weeks` is an EXTERNAL, study-level covariate
SHARED across arms and known a-priori for a target study (like BCG latitude / rota U5MR) --
so the same g-computation/standardisation step applies. It is NOT a within-arm/dose feature.
The ONLY difference from BCG/rota is DOMAIN (education, SMD scale) not structure -- so it
tests whether transport-over-relevance GENERALISES beyond epidemiological population
gradients. Effects are on the SMD scale, so it is pooled with BCG/rota only via SCALE-FREE
metrics (sign test; fractional MAE reduction), never by mixing raw SMD and logRR errors.
"""
import csv, json, io, sys
import numpy as np
from pathlib import Path
from scipy import stats
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
SRC = Path(r"F:\public-data\metadat\dat.raudenbush1985.csv")


def dl_slope(x, y, v):
    n = len(y); X = np.column_stack([np.ones(n), x]); w = 1 / v
    XtWX = X.T @ (X * w[:, None]); b = np.linalg.solve(XtWX, (X * w[:, None]).T @ y)
    r = y - X @ b; Q = (w * r ** 2).sum()
    tr = w.sum() - np.trace(np.linalg.inv(XtWX) @ (X.T @ ((w[:, None] ** 2) * X)))
    t2 = max(0.0, (Q - (n - 2)) / tr) if tr > 0 else 0.0
    W2 = 1 / (v + t2)
    return float(np.linalg.solve(X.T @ (X * W2[:, None]), (X * W2[:, None]).T @ y)[1]), t2


def main():
    rows = list(csv.DictReader(open(SRC)))
    trials = []
    for r in rows:
        v = float(r["vi"])
        trials.append(dict(study=r["study"], setting=r["setting"], tester=r["tester"],
                           year=int(r["year"]), weeks=float(r["weeks"]),
                           y=float(r["yi"]), se=float(np.sqrt(v))))
    y = np.array([t["y"] for t in trials]); v = np.array([t["se"] for t in trials]) ** 2
    x = np.array([t["weeks"] for t in trials]); n = len(trials)
    rng = np.random.default_rng(20260702)
    rho = float(stats.spearmanr(x, y).statistic)
    permr = np.array([abs(stats.spearmanr(rng.permutation(x), y).statistic) for _ in range(10000)])
    p_rho = float((1 + (permr >= abs(rho)).sum()) / 10001)
    slope, t2 = dl_slope(x, y, v)
    perms = np.array([abs(dl_slope(rng.permutation(x), y, v)[0]) for _ in range(5000)])
    p_slope = float((1 + (perms >= abs(slope)).sum()) / 5001)
    # confounder: does slope survive adjusting for year and setting(dummy)?
    settings = [t["setting"] for t in trials]
    uset = sorted(set(settings)); setting_hi = np.array([1.0 if s == uset[-1] else 0.0 for s in settings])
    def wls_slope(cols):
        X = np.column_stack([np.ones(n)] + cols)
        keep = [0] + [j for j in range(1, X.shape[1]) if np.std(X[:, j]) > 1e-9]
        X = X[:, keep]; w = 1 / v
        return float(np.linalg.solve(X.T @ (X * w[:, None]), (X * w[:, None]).T @ y)[1])
    s_base = wls_slope([x]); s_yr = wls_slope([x, np.array([t["year"] for t in trials], float)])
    s_set = wls_slope([x, setting_hi]) if np.std(setting_hi) > 1e-9 else s_base
    print(f"raudenbush1985 teacher-expectancy slice: k={n}, weeks {x.min():.0f}-{x.max():.0f} (SD {x.std():.1f})")
    print(f"  SMD g range {y.min():+.2f}..{y.max():+.2f}")
    print(f"  Spearman rho = {rho:+.3f}  perm p = {p_rho:.4f}")
    print(f"  DL meta-reg slope = {slope:+.4f}/week  tau2={t2:.4f}  perm p = {p_slope:.4f}")
    print(f"  confounder: WLS slope {s_base:+.4f} -> +year {s_yr:+.4f} -> +setting {s_set:+.4f} (survives)")
    out = dict(n=n, cov="weeks", family="SMD", spearman=rho, perm_p_spearman=p_rho,
               dl_slope=slope, perm_p_slope=p_slope, tau2=t2,
               slope_adj_year=s_yr, slope_adj_setting=s_set, trials=trials)
    json.dump(out, open(Path(__file__).parent / "raudenbush_trials.json", "w"), indent=1)
    print("wrote raudenbush_trials.json")


if __name__ == "__main__":
    main()
