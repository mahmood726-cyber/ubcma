"""Independent HSROC GLMM verification — agy seat (Gemini).

Bivariate binomial-normal GLMM fit by exact likelihood + product GH quadrature.
Does NOT import src/ubcma/dta.py.  Uses numpy/scipy only.
Parameterization: theta = (mu1, mu2, log_t1, log_t2, fisher_rho)
  logit(Se_i) = mu1 + t1*u1_i,   logit(Sp_i) = mu2 + t2*(rho*u1_i + sqrt(1-rho^2)*u2_i)
  (u1,u2) ~ N(0,I) independent.  Se=expit(mu1), Sp=expit(mu2).
"""

import json
import math
import numpy as np
from scipy.special import expit, roots_hermite, logsumexp, gammaln
from scipy.optimize import minimize

ROOT = "truth-recovery-dta"


def _log_binom(k, n):
    return gammaln(n + 1) - gammaln(k + 1) - gammaln(n - k + 1)


def _logpmf(k, n, eta):
    return k * eta - n * np.logaddexp(0.0, eta) + _log_binom(k, n)


def _build_grid(order):
    x, w = roots_hermite(order)
    z = math.sqrt(2.0) * x       # N(0,1) nodes
    v = w / math.sqrt(math.pi)   # N(0,1) weights (sum to 1)
    log_v = np.log(v)
    return z, log_v


def _nll(params, TP, n1, TN, n0, z, log_v):
    mu1, mu2, log_t1, log_t2, fisher_rho = params
    t1 = math.exp(log_t1)
    t2 = math.exp(log_t2)
    rho = math.tanh(fisher_rho)
    rho_perp = math.sqrt(max(1.0 - rho * rho, 1e-14))

    # GH nodes for Se and Sp random effects
    l1 = mu1 + t1 * z[:, None]                                          # (Q,1)
    l2 = mu2 + t2 * (rho * z[:, None] + rho_perp * z[None, :])         # (Q,Q)

    N = len(TP)
    lp1 = _logpmf(TP[:, None, None], n1[:, None, None], l1[None, :, :])  # (N,Q,1)
    lp2 = _logpmf(TN[:, None, None], n0[:, None, None], l2[None, :, :])  # (N,Q,Q)

    log_w2d = log_v[:, None] + log_v[None, :]     # (Q,Q)
    log_terms = log_w2d[None, :, :] + lp1 + lp2   # (N,Q,Q) by broadcast
    log_like = logsumexp(log_terms.reshape(N, -1), axis=1)
    return float(-np.sum(log_like))


def _starting_points(TP, FN, FP, TN, n1, n0, glmer):
    """Return a list of diverse starting parameter vectors."""
    # Pooled empirical logits
    total_pos = max(float(np.sum(TP + FN)), 1.0)
    total_neg = max(float(np.sum(TN + FP)), 1.0)
    mu1_emp = math.log((float(np.sum(TP)) + 0.5) / (float(np.sum(FN)) + 0.5 + 1e-9))
    mu2_emp = math.log((float(np.sum(TN)) + 0.5) / (float(np.sum(FP)) + 0.5 + 1e-9))

    # Estimate heterogeneity from study-level logits
    se_logits = np.log((TP + 0.5) / (FN + 0.5))
    sp_logits = np.log((TN + 0.5) / (FP + 0.5))
    sd1_emp = math.sqrt(max(float(np.var(se_logits)) - float(np.mean(4.0 / (n1 + 1e-9))), 0.04))
    sd2_emp = math.sqrt(max(float(np.var(sp_logits)) - float(np.mean(4.0 / (n0 + 1e-9))), 0.04))
    sd1_emp = min(max(sd1_emp, 0.1), 4.0)
    sd2_emp = min(max(sd2_emp, 0.1), 4.0)

    # Candidate mu pairs
    mu_pairs = [(mu1_emp, mu2_emp), (0.0, 0.0), (1.5, 1.5), (2.0, 2.0)]
    if glmer is not None:
        mu_pairs.insert(0, (glmer["m1_logit_sens"], glmer["m2_logit_spec"]))

    # Candidate (log_t1, log_t2) pairs
    sd_pairs = [
        (sd1_emp, sd2_emp),
        (0.15, 0.15), (0.35, 0.35), (0.75, 0.75), (1.5, 1.5),
        (sd1_emp, 0.35), (0.35, sd2_emp),
    ]
    lt_pairs = [(math.log(a), math.log(b)) for a, b in sd_pairs]

    # Candidate rho (fisher-transformed)
    rho_vals = [0.0, math.atanh(0.35), math.atanh(-0.35),
                math.atanh(0.70), math.atanh(-0.70),
                math.atanh(0.90), math.atanh(-0.90)]

    starts = []
    seen = set()
    for mu1, mu2 in mu_pairs:
        for lt1, lt2 in lt_pairs:
            for fr in rho_vals:
                key = (round(mu1, 6), round(mu2, 6), round(lt1, 6), round(lt2, 6), round(fr, 6))
                if key not in seen:
                    starts.append(np.array([mu1, mu2, lt1, lt2, fr], dtype=float))
                    seen.add(key)
    return starts


def _fit_dataset(ds_name, counts, glmer):
    TP = np.array(counts["TP"], dtype=float)
    FP = np.array(counts["FP"], dtype=float)
    FN = np.array(counts["FN"], dtype=float)
    TN = np.array(counts["TN"], dtype=float)

    # mada-style continuity correction
    if np.any(TP == 0) or np.any(FP == 0) or np.any(FN == 0) or np.any(TN == 0):
        TP += 0.5; FP += 0.5; FN += 0.5; TN += 0.5

    n1 = TP + FN
    n0 = TN + FP
    N = len(TP)

    # Two-phase optimization: coarse fit at order 25, polish at order 41
    z_fit, lv_fit = _build_grid(25)
    z_final, lv_final = _build_grid(41)

    bounds = [(-14.0, 14.0), (-14.0, 14.0), (-8.0, 3.0), (-8.0, 3.0), (-5.0, 5.0)]
    opts_fit   = {"maxiter": 2000, "ftol": 1e-10, "gtol": 1e-6, "maxls": 50}
    opts_final = {"maxiter": 2000, "ftol": 5e-11, "gtol": 5e-6, "maxls": 50}

    starts = _starting_points(TP, FN, FP, TN, n1, n0, glmer)

    # Score starts at coarse grid
    def f_fit(p):   return _nll(p, TP, n1, TN, n0, z_fit, lv_fit)
    def f_final(p): return _nll(p, TP, n1, TN, n0, z_final, lv_final)

    scored = sorted([(f_fit(s), s) for s in starts], key=lambda x: x[0])

    best_result = None
    for _, s0 in scored[:40]:
        r = minimize(f_fit, s0, method="L-BFGS-B", bounds=bounds, options=opts_fit)
        if best_result is None or r.fun < best_result.fun:
            best_result = r

    # Polish on fine grid
    polish = minimize(f_final, best_result.x, method="L-BFGS-B", bounds=bounds, options=opts_final)
    candidates = [best_result.x, polish.x]
    best_theta = min(candidates, key=lambda p: f_final(p))
    nll_mine = f_final(best_theta)

    mu1, mu2, lt1, lt2, fr = [float(x) for x in best_theta]
    se_opt = float(expit(mu1))
    sp_opt = float(expit(mu2))

    # Deviance check vs glmer
    mu1_g = glmer["m1_logit_sens"]
    mu2_g = glmer["m2_logit_spec"]
    lt1_g = math.log(max(glmer["tau_sens"], 1e-6))
    lt2_g = math.log(max(glmer["tau_spec"], 1e-6))
    fr_g  = math.atanh(max(min(glmer["rho"], 0.99999), -0.99999))
    nll_glmer = f_final([mu1_g, mu2_g, lt1_g, lt2_g, fr_g])

    dse = abs(se_opt - glmer["sens_summary"])
    dsp = abs(sp_opt - glmer["spec_summary"])
    mine_le_glmer = bool(nll_mine <= nll_glmer + 1e-4)

    return {
        "se": se_opt, "sp": sp_opt,
        "mu1": mu1, "mu2": mu2,
        "t1": math.exp(lt1), "t2": math.exp(lt2),
        "rho": math.tanh(fr),
        "dse_vs_glmer": dse, "dsp_vs_glmer": dsp,
        "nll_mine": nll_mine, "nll_glmer_params": nll_glmer,
        "mine_le_glmer": mine_le_glmer,
    }


def main():
    with open(f"{ROOT}/reference_fits.json") as f:
        ref_fits = json.load(f)
    with open(f"{ROOT}/reference_glmm.json") as f:
        ref_glmm = json.load(f)

    results = {"per_dataset": {}}
    worst = 0.0
    all_ok = True

    for ds_name, glmer in ref_glmm.items():
        if not glmer.get("ok", False):
            continue
        r = _fit_dataset(ds_name, ref_fits[ds_name]["counts"], glmer)
        results["per_dataset"][ds_name] = r
        worst = max(worst, r["dse_vs_glmer"], r["dsp_vs_glmer"])
        if not r["mine_le_glmer"]:
            all_ok = False
        print(f"  {ds_name}: se={r['se']:.4f} sp={r['sp']:.4f} "
              f"dse={r['dse_vs_glmer']:.2e} dsp={r['dsp_vs_glmer']:.2e} "
              f"ok={r['mine_le_glmer']}")

    results["worst_se_sp_vs_glmer"] = worst
    results["all_mine_le_glmer"] = all_ok
    results["seat_identifier"] = "agy"

    with open(f"{ROOT}/verify_hsroc_agy_result.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nseat=agy | all_mine_le_glmer={all_ok} | worst_se_sp={worst:.3e}")
    verdict = "PASS" if all_ok else "FAIL"
    print(f"VERDICT: {verdict}")


if __name__ == "__main__":
    main()
