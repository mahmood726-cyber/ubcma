"""STAGE-4 dose-response <-> borrowing link, on the REAL GLP1 dose slice.

The dose-response thread models effect as a parametric function of dose f(dose) (DRMA /
MBNMA); the borrowing thread borrows across trials with a dose-DISTANCE relevance kernel
(pilot-2). Both "borrow across dose" -- this is a head-to-head on the SAME real GLP1 slice
(n=12 trials, dose 1.1-14 mg, HbA1c effect; the modifier is real: slope -0.092 %/mg, R2=0.94,
perm p=0.01) to answer WHICH borrows dose better at held-out prediction, and to make the
unification concrete.

Leave-one-trial-out (target gets ZERO own data -> pure transportability):
  kernel_relevance : borrowing-field Gaussian dose-distance kernel x precision (pilot-2's
                     `borrowing_field2.covariate_prior`, mode='relevance') -- IDENTICAL code.
  dose_metareg     : the dose-response MODEL -- RE (DL) meta-regression of effect on dose fit
                     to the OTHER trials, predicting mu = a + b*dose_t at the held-out dose
                     (the linear MBNMA/DRMA prediction; a saturated linear f(dose)).
  uniform          : precision-weighted field mean (NO dose borrowing) -- the null.
TRUTH = the trial's REAL observed effect y_t. Score LOO MAE + prediction-interval coverage +
paired bootstrap. Honest win/tie/null. Expectation to test: when the true dose-response is
~linear (GLP1, R2=0.94) the correctly-specified parametric model should borrow dose at least
as efficiently as the nonparametric kernel -- if so, that tells you WHICH tool to use when.
"""
import json, io, sys
import numpy as np
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from borrowing_field2 import covariate_prior, Z975  # noqa: E402
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = __import__("pathlib").Path(__file__).resolve().parent
GLP1 = [t for t in json.load(open(HERE / "probe_trials.json"))
        if t["active"] == "GLP1" and t.get("dose") is not None]
X = np.array([t["dose"] for t in GLP1]); Y = np.array([t["y"] for t in GLP1])
S = np.array([t["se"] for t in GLP1]); N = len(GLP1)


def metareg_predict(xs, ys, ses, x_t, iters=100):
    """RE(DL) meta-regression fit to donors; predict effect at dose x_t with a
    predictive SE (coeff uncertainty + between-trial tau2). = linear MBNMA/DRMA prediction."""
    Xd = np.column_stack([np.ones_like(xs), xs]); tau2 = 0.0
    for _ in range(iters):
        w = 1.0 / (ses ** 2 + tau2); WX = Xd * w[:, None]
        cov = np.linalg.inv(Xd.T @ WX); beta = cov @ (WX.T @ ys)
        resid = ys - Xd @ beta
        P = np.diag(w) - WX @ cov @ WX.T
        Q = float((w * resid ** 2).sum()); dfree = len(xs) - 2; trP = np.trace(P)
        tn = max(0.0, (Q - dfree) / trP) if trP > 0 else 0.0
        if abs(tn - tau2) < 1e-10:
            tau2 = tn; break
        tau2 = tn
    w = 1.0 / (ses ** 2 + tau2); WX = Xd * w[:, None]
    cov = np.linalg.inv(Xd.T @ WX); beta = cov @ (WX.T @ ys)
    g = np.array([1.0, x_t])
    mu = float(g @ beta)
    se = float(np.sqrt(g @ cov @ g + tau2))   # predictive SE for a new trial at x_t
    return mu, se


def loo(mode, bw=None, seed=1):
    rng = np.random.default_rng(seed); errs, cov = [], []
    for i in range(N):
        m = np.ones(N, bool); m[i] = False
        if mode == "dose_metareg":
            mu, se = metareg_predict(X[m], Y[m], S[m], X[i])
        else:
            mu, se, _ = covariate_prior(X[i], X[m], Y[m], S[m], bw, mode=mode, rng=rng)
        if not np.isfinite(mu):
            continue
        errs.append(abs(mu - Y[i]))
        half = Z975 * np.sqrt(se ** 2 + S[i] ** 2)
        cov.append(mu - half <= Y[i] <= mu + half)
    return np.array(errs), np.array(cov)


def pboot(ea, eb, n=5000, seed=7):
    rng = np.random.default_rng(seed); d = ea - eb
    bi = rng.integers(0, len(d), size=(n, len(d))); md = d[bi].mean(axis=1)
    lo, hi = np.quantile(md, [0.025, 0.975])
    return float(d.mean()), float(lo), float(hi), bool(hi < 0)


def main():
    xsd = float(np.std(X))
    print(f"STAGE-4 dose-link on real GLP1 (n={N}, dose SD={xsd:.2f} mg). TRUTH = real held-out effect.")
    print("kernel (borrowing-field dose-distance) vs dose_metareg (linear DRMA/MBNMA) vs uniform (null)\n")
    e_reg, c_reg = loo("dose_metareg")
    e_uni, c_uni = loo("uniform", bw=xsd)
    print(f"{'bw(mg)':>7} {'method':>14} {'MAE':>7} {'cover':>6} | key paired deltas (CI<0 = better)")
    print(f"{'--':>7} {'dose_metareg':>14} {e_reg.mean():>7.3f} {c_reg.mean():>6.2f} | ", end="")
    d, lo, hi, win = pboot(e_reg, e_uni)
    print(f"metareg-uniform {d:+.3f}[{lo:+.3f},{hi:+.3f}]{'  WIN' if win else ''}")
    print(f"{'--':>7} {'uniform':>14} {e_uni.mean():>7.3f} {c_uni.mean():>6.2f} |")
    rows = {}
    for bw in [round(xsd / 2, 2), round(xsd, 2), round(1.5 * xsd, 2)]:
        e_ker, c_ker = loo("relevance", bw=bw)
        d_ku, lo_ku, hi_ku, win_ku = pboot(e_ker, e_uni)       # kernel vs uniform
        d_rk, lo_rk, hi_rk, win_rk = pboot(e_reg, e_ker)       # metareg vs kernel (CI<0 => metareg better)
        print(f"{bw:>7} {'kernel_relev':>14} {e_ker.mean():>7.3f} {c_ker.mean():>6.2f} | "
              f"kernel-uniform {d_ku:+.3f}[{lo_ku:+.3f},{hi_ku:+.3f}]{'  WIN' if win_ku else ''}  ||  "
              f"metareg-kernel {d_rk:+.3f}[{lo_rk:+.3f},{hi_rk:+.3f}]"
              f"{'  metaregWIN' if win_rk else ('  kernelWIN' if lo_rk > 0 else '  tie')}")
        rows[bw] = dict(mae_kernel=float(e_ker.mean()), cover_kernel=float(c_ker.mean()),
                        kernel_vs_uniform=[d_ku, lo_ku, hi_ku],
                        metareg_vs_kernel=[d_rk, lo_rk, hi_rk])
    out = dict(n=N, dose_sd=xsd, mae_dose_metareg=float(e_reg.mean()),
               cover_dose_metareg=float(c_reg.mean()), mae_uniform=float(e_uni.mean()),
               metareg_vs_uniform=list(pboot(e_reg, e_uni)[:3]), rows=rows)
    json.dump(out, open(HERE / "stage4_doselink_result.json", "w"), indent=1)

    # verdict at central bw
    e_ker, _ = loo("relevance", bw=round(xsd, 2))
    d_rk, lo_rk, hi_rk, _ = pboot(e_reg, e_ker)
    print("\n" + "=" * 74)
    print("VERDICT (central bw):")
    if hi_rk < 0:
        v = "the PARAMETRIC dose-response model (linear DRMA/MBNMA) borrows dose SIGNIFICANTLY better"
    elif lo_rk > 0:
        v = "the NONPARAMETRIC dose-distance kernel borrows dose significantly better"
    else:
        v = "parametric dose-response model and dose-distance kernel are STATISTICALLY TIED"
    print(f"  metareg - kernel MAE = {d_rk:+.3f} [{lo_rk:+.3f},{hi_rk:+.3f}]  -> {v}.")
    print("  Both are real dose-borrowing; on the ~linear GLP1 field this quantifies which tool wins.")
    print("=" * 74)


if __name__ == "__main__":
    main()
