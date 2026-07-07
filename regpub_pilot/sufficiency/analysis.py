"""Analysis engine for the OPEN-DATA SUFFICIENCY study.

Three questions per review:
  1. WEIGHT COVERAGE — what fraction of the published MA's inverse-variance WEIGHT
     does the open-data-poolable subset hold? (fixed-effect AND random-effects.)
  2. REPRODUCE — pool the poolable subset with the full house stack (REML+HKSJ+PI)
     and compare direction / significance / magnitude to the published estimate.
  3. ROBUSTNESS / INFLUENCE — under worst-case-but-plausible assumptions about the
     NON-poolable trials (one-directional / publication-bias-style missingness), can
     the missing evidence overturn the reproduced conclusion?  Verdict ROBUST/FRAGILE.

The load-bearing robustness metric is the BREAKDOWN FRACTION r* — the minimum
missing-weight ratio (missing weight / poolable weight) that flips the conclusion.
r* is assumption-free algebra on the subset; only the comparison to the ACTUAL
missing ratio uses the (estimated) poolability classification.
"""
from __future__ import annotations
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from pool import pool, _qnorm  # noqa: E402
from reviews import conclusion_label  # noqa: E402

Z = 1.959963985


def _fe(yi, vi):
    """Fixed-effect pooled mean, total weight, SE, z."""
    w = [1.0 / v for v in vi]
    W = sum(w)
    mu = sum(wi * y for wi, y in zip(w, yi)) / W
    se = math.sqrt(1.0 / W)
    return {"mu": mu, "W": W, "se": se, "z": mu / se if se > 0 else 0.0}


def weight_coverage(review):
    """Fraction of published IV weight held by the poolable subset (fixed & RE)."""
    pool_v = [t.vi for t in review.trials if t.poolable]
    all_v = [t.vi for t in review.trials]
    if not all_v:
        return None
    # fixed-effect weights
    wf_pool = sum(1.0 / v for v in pool_v)
    wf_all = sum(1.0 / v for v in all_v)
    cov_fixed = wf_pool / wf_all if wf_all > 0 else 0.0
    # random-effects weights at the FULL-set tau^2 (the model the published MA used)
    tau2 = review.published.get("tau2")
    if tau2 is None:
        # recompute from full set
        from pool import _tau2_reml
        tau2 = _tau2_reml([t.yi for t in review.trials], all_v)
    wr_pool = sum(1.0 / (v + tau2) for v in pool_v)
    wr_all = sum(1.0 / (v + tau2) for v in all_v)
    cov_re = wr_pool / wr_all if wr_all > 0 else 0.0
    return {"cov_fixed": cov_fixed, "cov_re": cov_re, "tau2_full": tau2,
            "k_pool": len(pool_v), "k_total": len(all_v),
            "wf_pool": wf_pool, "wf_missing": wf_all - wf_pool}


def _concl_of(p, favorable):
    sig = not (p["ci_lo"] <= 0.0 <= p["ci_hi"])
    return conclusion_label(p["est"], sig, favorable), sig


def reproduce(review):
    """Pool the poolable subset two ways and compare to published:
      STANDARD (DL + normal z) — mimics the typical published RE method; this
        isolates the DATA/COVERAGE question ('is the open data enough?').
      HOUSE (REML+HKSJ+PI)     — the rigorous overlay ('does it survive proper
        small-sample methods?'). More conservative; can differ at small k.
    'reproduced' uses STANDARD so a like-for-like method comparison isolates
    coverage; house-stack disagreements are reported separately as a rigor flag."""
    sub = [t for t in review.trials if t.poolable]
    if not sub:
        return {"ok": False, "reason": "no poolable trials (0% coverage)"}
    yi = [t.yi for t in sub]; vi = [t.vi for t in sub]
    ps = pool(yi, vi, method="DL", hksj=False)            # standard, published-style
    ph = pool(yi, vi, method="REML", hksj=True)           # house rigorous stack
    pub = review.published
    bt = math.exp if review.scale == "log" else (lambda x: x)
    cs, sig_s = _concl_of(ps, review.favorable)
    ch, sig_h = _concl_of(ph, review.favorable)
    return {"ok": True, "k": ps["k"],
            # standard (data-sufficiency) view
            "est": ps["est"], "ci_lo": ps["ci_lo"], "ci_hi": ps["ci_hi"],
            "significant": sig_s, "conclusion": cs,
            "est_nat": bt(ps["est"]), "ci_nat": [bt(ps["ci_lo"]), bt(ps["ci_hi"])],
            "reproduced": (cs == pub["conclusion"]),
            "direction_match": (ps["est"]) * (pub["est"]) >= 0,
            "mag_ratio": (abs(ps["est"]) / abs(pub["est"])) if pub["est"] != 0 else None,
            # house-stack overlay
            "house_conclusion": ch, "house_significant": sig_h,
            "house_est_nat": bt(ph["est"]), "house_ci_nat": [bt(ph["ci_lo"]), bt(ph["ci_hi"])],
            "house_agrees_pub": (ch == pub["conclusion"]),
            "house_pi_nat": ([bt(ph["pi_lo"]), bt(ph["pi_hi"])] if ph.get("pi_lo") is not None else None),
            "tau2": ph["tau2"], "I2": ph["I2"]}


# --------------------------------------------------------------------------
# BREAKDOWN FRACTION (influence threshold) — assumption-free algebra on subset
# --------------------------------------------------------------------------
def _z_after_missing(z0, se, rho, mu_m):
    """z of the fixed-effect pooled mean after adding a missing block of weight
    rho*W at effect mu_m. Derivation in module docstring / report §3."""
    # mu' = (mu + rho*mu_m)/(1+rho); se' = se/sqrt(1+rho); z' = mu'/se'
    # z' = (z + rho*mu_m/se) / sqrt(1+rho)
    return (z0 + rho * mu_m / se) / math.sqrt(1.0 + rho)


def breakdown_fraction(review, rep):
    """Minimum missing-weight ratio r* that flips the reproduced conclusion, under
    two one-directional (publication-bias-style) missingness scenarios:

      DILUTION   : hidden trials are NULL (mu_m = 0). Erodes a significant finding.
      REVERSAL   : hidden trials sit at the worst plausible OPPOSING effect M_opp,
                   bounded by the most extreme opposing per-trial effect observed
                   (empirically grounded), else |mu_subset| (symmetric reflection).

    For a reproduced NULL conclusion the threat is inverted: hidden trials at a
    plausible real effect M creating significance -> r* = min ratio to reach p<0.05.
    """
    sub = [t for t in review.trials if t.poolable]
    yi = [t.yi for t in sub]; vi = [t.vi for t in sub]
    fe = _fe(yi, vi)
    mu, se, z = fe["mu"], fe["se"], fe["z"]
    fav = review.favorable
    concl = rep["conclusion"]

    # worst plausible opposing magnitude from observed dispersion (all trials)
    all_eff = [t.yi for t in review.trials]
    # opposing side = sign opposite to the favorable finding's estimate
    if mu != 0:
        opp = [-math.copysign(1, mu) * e for e in all_eff]  # projection onto opposing dir
        m_obs = max([o for o in opp if o > 0], default=0.0)
    else:
        m_obs = 0.0
    M_opp = max(m_obs, abs(mu))  # at least a symmetric reflection

    out = {"z_subset": z, "se_subset": se, "mu_subset": mu, "M_opp": M_opp}

    if concl in ("benefit", "harm"):
        # DILUTION: |z'|<1.96 ; z'=z/sqrt(1+r) -> r = (|z|/1.96)^2 - 1
        r_dilute = (abs(z) / Z) ** 2 - 1.0 if abs(z) > Z else 0.0
        # REVERSAL: hidden block at opposing M_opp until conclusion no longer holds
        # (loses significance on the favorable side). Solve numerically.
        r_rev = _solve_flip(z, se, mu, fav, M_opp, want="lose_sig")
        out.update({"scenario": "dilution/reversal", "r_dilute": r_dilute,
                    "r_reversal": r_rev, "r_star": min(r_dilute, r_rev)})
    else:  # reproduced NULL — threat is hidden REAL effect manufacturing significance
        # place hidden block at a plausible favorable effect M (use published |est| or M_opp)
        M = max(abs(review.published["est"]), M_opp, 1e-6)
        r_make = _solve_flip(z, se, mu, fav, M, want="gain_sig")
        out.update({"scenario": "manufacture-effect", "M_effect": M, "r_star": r_make})
    return out


def _solve_flip(z, se, mu, fav, M, want, hi=1e6):
    """Bisection for the smallest rho where the conclusion changes.
    want='lose_sig': significant favorable finding becomes NS (hidden at opposing -M_dir).
    want='gain_sig': NS becomes significant (hidden at favorable effect)."""
    # opposing direction for a favorable finding = -sign(mu); for gain_sig use favorable dir
    if want == "lose_sig":
        mu_m = -math.copysign(M, mu)  # push against the finding

        def flips(rho):
            return abs(_z_after_missing(z, se, rho, mu_m)) < Z
    else:  # gain_sig
        mu_m = fav * M  # push toward a favorable significant effect

        def flips(rho):
            zp = _z_after_missing(z, se, rho, mu_m)
            return abs(zp) >= Z and (zp * fav > 0)

    if flips(0.0):
        return 0.0
    lo, h = 0.0, hi
    if not flips(h):
        return float("inf")  # cannot flip within bound
    for _ in range(80):
        mid = (lo + h) / 2
        if flips(mid):
            h = mid
        else:
            lo = mid
    return h


def actual_missing_ratio(review, model="fixed"):
    """Real missing-weight ratio rho_actual = W_missing / W_poolable (same weight model)."""
    pool_v = [t.vi for t in review.trials if t.poolable]
    miss_v = [t.vi for t in review.trials if not t.poolable]
    if not pool_v:
        return float("inf")
    if model == "fixed":
        wp = sum(1.0 / v for v in pool_v); wm = sum(1.0 / v for v in miss_v)
    else:
        tau2 = review.published.get("tau2", 0.0) or 0.0
        wp = sum(1.0 / (v + tau2) for v in pool_v)
        wm = sum(1.0 / (v + tau2) for v in miss_v)
    return wm / wp if wp > 0 else float("inf")


def verdict(review):
    """Full per-review verdict: reproduce + robustness -> ROBUST / FRAGILE / INSUFFICIENT."""
    cov = weight_coverage(review)
    rep = reproduce(review)
    if not rep["ok"]:
        return {"cov": cov, "rep": rep, "verdict": "INSUFFICIENT",
                "why": "0% weight coverage — open data yields no poolable trial"}
    HIGH_COV = 0.90  # >=90% weight open -> non-reproduction cannot be a coverage problem
    if not rep["reproduced"]:
        # classify the cause: coverage gap vs (rare) same-data method disagreement
        if cov["cov_fixed"] >= HIGH_COV:
            cause = "method (data fully open; standard-method conclusion differs — investigate)"
        else:
            cause = f"coverage ({cov['cov_re']*100:.0f}% of RE weight open; missing trials carry the signal)"
        return {"cov": cov, "rep": rep, "verdict": "NOT_REPRODUCED",
                "why": f"open-subset '{rep['conclusion']}' != published "
                       f"'{review.published['conclusion']}' — cause: {cause}"}
    bf = breakdown_fraction(review, rep)
    rho_fixed = actual_missing_ratio(review, "fixed")
    rho_re = actual_missing_ratio(review, "re")
    r_star = bf["r_star"]
    # ROBUST if the real missing weight (even if fully adversarial one-directional)
    # cannot flip the conclusion. Influence algebra is fixed-effect -> use rho_fixed.
    robust = rho_fixed < r_star
    # house-stack rigor note (does the rigorous stack also keep the conclusion?)
    house_flag = "" if rep["house_agrees_pub"] else \
        f" [house REML+HKSJ is more conservative: {rep['house_conclusion']}]"
    return {"cov": cov, "rep": rep, "bf": bf, "rho_fixed": rho_fixed, "rho_re": rho_re,
            "r_star": r_star, "verdict": "ROBUST" if robust else "FRAGILE",
            "why": (f"reproduced; missing/poolable weight rho={rho_fixed:.2f} "
                    f"{'<' if robust else '>='} breakdown r*={r_star:.2f} "
                    f"({bf['scenario']}) -> {'cannot' if robust else 'could'} overturn{house_flag}")}


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    from reviews import all_reviews
    for r in all_reviews():
        v = verdict(r)
        cov = v["cov"]
        print(f"\n=== {r.key} ({r.area}, tier={r.tier}) ===")
        print(f"  weight coverage: fixed={cov['cov_fixed']*100:.1f}%  RE={cov['cov_re']*100:.1f}%  "
              f"(k_pool={cov['k_pool']}/{cov['k_total']})")
        rep = v["rep"]
        if rep["ok"]:
            print(f"  reproduce[std]: {rep['conclusion']:8s} est={rep['est_nat']:.3f} "
                  f"CI[{rep['ci_nat'][0]:.3f},{rep['ci_nat'][1]:.3f}] "
                  f"| published {r.published['conclusion']} -> match={rep['reproduced']}")
            print(f"  house[REML+HKSJ]: {rep['house_conclusion']:8s} est={rep['house_est_nat']:.3f} "
                  f"CI[{rep['house_ci_nat'][0]:.3f},{rep['house_ci_nat'][1]:.3f}] "
                  f"agrees_pub={rep['house_agrees_pub']}")
        print(f"  VERDICT: {v['verdict']}  — {v['why']}")
