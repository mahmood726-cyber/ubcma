"""Stage 3c -- NONLINEAR (Emax) predicted-effect-at-target-dose bake-off.

Stage 3b proved the target-dose estimand under a LINEAR model reduces EXACTLY to the slope
null. The one setting where a shrinkage-win region could actually exist is a NONLINEAR truth,
where the predicted log-RR at a dose is not a rescaling of a single slope and per-study
curvature must be borrowed. This is that experiment.

TRUTH: each study's log-rate follows an Emax curve  logRR_s(d) = Emax_s * d/(ED50 + d),
Emax_s ~ N(Emax, tau^2), shared ED50; Poisson counts on person-years (same DGP family as the
linear sim). One-sided publication selection acts on the crude estimated trend (favouring
significant positive trends) -> biases the naive predicted effect UP, as in Stage 3.

ESTIMAND: the UNSELECTED population-mean log-RR at a target dose d* (interior, near ED50 where
curvature is strongest):  truth = Emax * d*/(ED50 + d*).

METHODS (all predict at d* via the VALIDATED restricted-cubic-spline DRMA, so the model is
correctly flexible / mildly misspecified vs the Emax truth -- realistic):
  two_stage_reml  : spline two-stage REML pooled prediction at d*        (BASELINE = "the field")
  two_stage_fixed : spline two-stage fixed-effect prediction at d*
  one_stage       : spline one-stage pooled GLS prediction at d*   (borrows the shape -> lower var)
  adaptshrink     : AdaptShrink kernel aggregate of the three predictions at d* (same kernel as
                    the NMA/DTA/borrowing threads); THIS is the candidate that could win if the
                    per-study spline predictions are noisy enough that shrinkage helps.

Scored with the SAME matched-coverage truth-gate as Stage 3 (`dr_bakeoff.matched_coverage_table`
+ paired-bootstrap `_bootstrap_mciw0`, BASELINE two_stage_reml). Honest win/null either way.
"""
import io, sys, argparse
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import drma  # noqa: E402
import dr_bakeoff as B  # noqa: E402
from ubcma.adaptshrink import adaptshrink_estimator  # noqa: E402
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DOSES = np.array([0.0, 1.0, 2.0, 4.0, 8.0])
KNOTS = np.array([1.0, 2.0, 4.0])       # RCS knots (3 -> 2 spline params; stable from 4 non-ref pts)
EMAX, ED50, TAU_EMAX = 0.7, 2.0, 0.15
DSTAR = 2.0                              # interior target dose, = ED50 (max curvature)
Z975 = 1.959963984540054
METHODS = ["two_stage_reml", "two_stage_fixed", "one_stage", "adaptshrink"]


def _truth():
    return EMAX * DSTAR / (ED50 + DSTAR)


def gen_emax_study(rng, sid, emax_s, base_rate=0.0025, py_scale=20000.0):
    J = len(DOSES)
    py = py_scale * (0.6 + 0.8 * rng.random(J))
    rate = base_rate * np.exp(emax_s * DOSES / (ED50 + DOSES))
    cases = np.maximum(rng.poisson(rate * py).astype(float), 1.0)
    lograte = np.log(cases / py)
    logrr = lograte - lograte[0]
    var = 1.0 / cases + 1.0 / cases[0]
    se = np.sqrt(var); se[0] = np.nan
    x = DOSES[1:]; w = 1.0 / var[1:]
    b_hat = float(np.sum(w * x * logrr[1:]) / np.sum(w * x * x))
    se_hat = float(np.sqrt(1.0 / np.sum(w * x * x)))
    rows = pd.DataFrame({"id": sid, "type": "ir", "dose": DOSES, "cases": cases,
                         "peryears": py, "logrr": logrr, "se": se})
    return rows, b_hat, se_hat


def gen_emax_published(seed, strength, k_target=14, max_studies=120):
    rng = np.random.default_rng(seed)
    kept = []; sid = 0
    while len(kept) < k_target and sid < max_studies:
        emax_s = EMAX + rng.normal(0, TAU_EMAX)
        rows, b_hat, se_hat = gen_emax_study(rng, f"S{sid}", emax_s)
        z = b_hat / se_hat if se_hat > 0 else 0.0
        if rng.random() <= B_publish(z, strength):
            kept.append(rows)
        sid += 1
    if not kept:
        return None
    return pd.concat(kept, ignore_index=True)


def B_publish(z, strength):
    import sim_doseresponse as S
    return S._publish_prob(z, strength)


def _predict_at_dstar(fit):
    yhat, se = drma.predict_logrr(fit, DSTAR, ref_dose=0.0)
    return float(yhat[0]), float(se[0])


def fit_all_emax(df):
    out = {}
    try:
        f_reml = drma.drma_two_stage(df, n_col="peryears", transform="rcs", knots=KNOTS, method="reml")
        mu_r, se_r = _predict_at_dstar(f_reml)
        out["two_stage_reml"] = (mu_r, mu_r - Z975 * se_r, mu_r + Z975 * se_r, True)
        f_fix = drma.drma_two_stage(df, n_col="peryears", transform="rcs", knots=KNOTS, method="fixed")
        mu_f, se_f = _predict_at_dstar(f_fix)
        out["two_stage_fixed"] = (mu_f, mu_f - Z975 * se_f, mu_f + Z975 * se_f, True)
        f_one = drma.drma_one_stage(df, n_col="peryears", transform="rcs", knots=KNOTS)
        mu_o, se_o = _predict_at_dstar(f_one)
        out["one_stage"] = (mu_o, mu_o - Z975 * se_o, mu_o + Z975 * se_o, True)
        pre = {"two_stage_reml": (mu_r, se_r), "two_stage_fixed": (mu_f, se_f),
               "one_stage": (mu_o, se_o)}
        as_res = adaptshrink_estimator(np.zeros(1), np.ones(1),
                                       members=("two_stage_reml", "two_stage_fixed", "one_stage"),
                                       precomputed=pre, kappa=1.0)
        out["adaptshrink"] = (as_res["mu"], as_res["ci_low"], as_res["ci_high"],
                              bool(as_res["converged"]))
    except Exception:
        for m in METHODS:
            out.setdefault(m, (float("nan"), float("nan"), float("nan"), False))
    for m in METHODS:
        out.setdefault(m, (float("nan"), float("nan"), float("nan"), False))
    return out


def run_replicates(strength, reps, seed0=54321):
    truth = _truth(); rows = []
    for r in range(reps):
        df = gen_emax_published(seed0 + r, strength)
        if df is None:
            continue
        res = fit_all_emax(df)
        for m in METHODS:
            mu, lo, hi, conv = res[m]
            rows.append({"strength": strength, "rep": r, "method": m, "true_mu": truth,
                         "mu_hat": mu, "ci_low": lo, "ci_high": hi, "converged": conv})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=300)
    args = ap.parse_args()
    print(f"Stage 3c: NONLINEAR Emax predicted-dose bake-off  (Emax={EMAX}, ED50={ED50}, "
          f"tau={TAU_EMAX}, d*={DSTAR}, truth logRR(d*)={_truth():.4f})")
    print(f"  spline RCS knots {KNOTS.tolist()}; estimand = unselected pop-mean logRR at d*.\n")
    frames = [run_replicates(s, args.reps) for s in ("moderate", "strong")]
    df = pd.concat(frames, ignore_index=True)
    conv = df.groupby(["strength", "method"])["converged"].mean().round(3)
    print("convergence by method:\n", conv.to_string(), "\n")

    tbl = B.matched_coverage_table(df)
    print("matched-coverage table (mciw0 = matched-coverage interval width at nominal target):")
    cols = ["strength", "method", "n", "bias", "rmse", "raw_cov", "mciw0", "mciw", "test_cov"]
    print(tbl[cols].to_string(index=False), "\n")

    boot = B._bootstrap_mciw0(df)
    print("paired-bootstrap MCIW0 diff vs two_stage_reml (robust_win = CI upper < 0 = beats baseline):")
    any_win = False
    for r in boot:
        tag = "  <-- ROBUST WIN" if r["robust_win"] else ""
        any_win = any_win or r["robust_win"]
        print(f"  {r['strength']:9} {r['method']:16} dMCIW0={r['mciw0_diff']:+.5f} "
              f"[{r['ci_lo']:+.5f},{r['ci_hi']:+.5f}] frac_better={r['frac_better']:.2f}{tag}")

    import json
    json.dump({"boot": boot, "truth": _truth(), "params": dict(Emax=EMAX, ED50=ED50, tau=TAU_EMAX, dstar=DSTAR)},
              open(Path(__file__).parent / "dr_emax_bakeoff_result.json", "w"), indent=1)
    print("\n" + "=" * 74)
    if any_win:
        print("VERDICT: a SHRINKAGE-WIN region EXISTS under the nonlinear Emax truth -- at least one")
        print("estimator robustly beats two-stage REML at matched coverage at the target dose.")
    else:
        print("VERDICT: HONEST NULL even under the nonlinear Emax truth -- no estimator robustly")
        print("beats two-stage REML at matched coverage at the target dose. The two-stage spline")
        print("field is not improved on by shrinkage/partial-pooling here either.")
    print("=" * 74)


if __name__ == "__main__":
    main()
