"""PILOT-3 engine: TRANSPORTABILITY as a multiplicand on the borrowing weight.

borrowing weight(s -> target t) = relevance(s,t) x transportability(s,t) x precision(s)

  relevance(s,t)        : clinical/pharmacological similarity using WITHIN-TRIAL
                          covariates only (drug-class match [soft kernel] x baseline
                          HbA1c distance). NO population data. This is the pilot-2
                          notion of relevance, generalised across classes. The
                          'relevance-only' comparator is the pilot-2 winner.

  transportability(s,t) : population similarity using EXTERNAL data (WB adult
                          obesity prevalence of recruiting countries). Two effects,
                          both absent from relevance:
                            (a) DOWN-WEIGHT donor trials whose population obesity is
                                far from the target's  (Gaussian kernel on |ob_s-ob_t|);
                            (b) STANDARDISE / transport each donor's effect to the
                                target population:  y_s->t = y_s + beta_ob (ob_t - ob_s)
                                using the within-class obesity slope beta_ob (g-computation).

This is design-brief Gap-2: standardise borrowed evidence to a target population
AND down-weight trials that don't transport. The thesis is that (a)+(b) beat
relevance-only when the target is FAR from the donor pool on obesity.

Pre-registered carry-overs from pilot-2 (NOT re-tuned):
  * own (+) prior fusion = conflict-discounted PRECISION fusion (power-prior), not
    2-member AdaptShrink. (Used only in the own+borrow regime.)
  * beta_ob = 0 must make transport inert (standing negative control).
"""
from __future__ import annotations
import numpy as np

Z975 = 1.959963984540054
CLASS_GAMMA = 0.25   # soft cross-class relevance: different class keeps 25% weight


def within_class_obslope(donors, classes_present):
    """Pooled within-class obesity slope beta_ob from donors (fixed-effect WLS with
    class fixed effects). Returns the single shared obesity slope. LOO-safe: only
    donors are passed in. Falls back to 0.0 if not estimable."""
    y = np.array([d["y"] for d in donors], float)
    s = np.array([d["se"] for d in donors], float)
    ob = np.array([d["pop_ob"] for d in donors], float)
    cls = [d["active"] for d in donors]
    uniq = sorted(set(cls))
    if len(y) < len(uniq) + 2 or ob.std() < 1e-6:
        return 0.0
    # design: class dummies (drop first) + obesity
    cols = [np.ones_like(y)]
    for c in uniq[1:]:
        cols.append(np.array([1.0 if k == c else 0.0 for k in cls]))
    cols.append(ob)
    X = np.column_stack(cols)
    w = 1.0 / np.maximum(s ** 2, 1e-9)
    WX = X * w[:, None]
    try:
        beta = np.linalg.solve(X.T @ WX, WX.T @ y)
    except np.linalg.LinAlgError:
        return 0.0
    return float(beta[-1])


def transport_prior(target, donors, bw_ob, mode="transport",
                    bw_base=1.0, beta_ob=None, rng=None):
    """Form (mu_p, se_p, ess) for a target from donor trials.

    mode:
      'nma'        : precision only (standard pooled prior; no covariates).
      'relevance'  : relevance(class,baseline) x precision. RAW donor y. (pilot-2 winner)
      'transport'  : relevance x transport-kernel(obesity) x precision, with donor y
                     STANDARDISED to the target obesity via beta_ob.
      'scrambled'  : like transport but donor obesity permuted (kernel+shift broken).
      'transport_noshift' : transport kernel down-weight only, beta_ob forced 0
                     (isolates the down-weight half from the standardisation half).
    """
    donors = list(donors)
    ys = np.array([d["y"] for d in donors], float)
    ses = np.array([d["se"] for d in donors], float)
    obs = np.array([d["pop_ob"] for d in donors], float)
    cls = [d["active"] for d in donors]
    bases = np.array([d["baseline"] if d["baseline"] is not None else np.nan for d in donors])
    prec = 1.0 / np.maximum(ses ** 2, 1e-9)

    # relevance: soft class match x baseline-distance kernel
    rel = np.array([1.0 if c == target["active"] else CLASS_GAMMA for c in cls])
    if target["baseline"] is not None:
        bd = np.where(np.isnan(bases), 0.0,
                      np.exp(-0.5 * ((bases - target["baseline"]) / bw_base) ** 2))
        bd = np.where(np.isnan(bases), 1.0, bd)  # missing baseline -> neutral
        rel = rel * bd

    if mode == "nma":
        w = prec
        yeff = ys
    elif mode == "relevance":
        w = rel * prec
        yeff = ys
    else:
        obeff = obs.copy()
        if mode == "scrambled":
            r = rng if rng is not None else np.random.default_rng(0)
            obeff = r.permutation(obeff)
        k = np.exp(-0.5 * ((obeff - target["pop_ob"]) / bw_ob) ** 2)
        w = rel * k * prec
        b = 0.0 if (mode == "transport_noshift" or beta_ob is None) else beta_ob
        yeff = ys + b * (target["pop_ob"] - obeff)   # standardise to target population

    wsum = float(w.sum())
    # Fail closed on a non-positive OR non-finite weight sum. A zero bandwidth or
    # a missing/at-target covariate makes a kernel weight NaN (0/0), and `wsum
    # <= 0` is False for NaN — so the guard was bypassed and the prior proceeded
    # with NaN weights. `not (wsum > 0)` catches NaN, 0, and negatives.
    if not (wsum > 0):
        return float("nan"), float("inf"), 0.0
    mu_p = float((w * yeff).sum() / wsum)
    within = float((w ** 2 * ses ** 2).sum() / wsum ** 2)
    between = float((w * (yeff - mu_p) ** 2).sum() / wsum)
    se_p = float(np.sqrt(max(within + between, 1e-9)))
    ess = float(wsum ** 2 / (w ** 2).sum())
    return mu_p, se_p, ess


def precision_fuse(mu0, se0, mu_p, se_p, q_max=4.0):
    """Conflict-discounted PRECISION fusion (pilot-2 pre-registered own(+)prior).
    delta in [0,1] discounts the prior when it conflicts with own data."""
    Q = (mu0 - mu_p) ** 2 / max(se0 ** 2 + se_p ** 2, 1e-12)
    delta = float(np.clip(1.0 - Q / q_max, 0.0, 1.0))
    if delta <= 1e-6 or not np.isfinite(mu_p):
        return mu0, se0, delta
    p_own = 1.0 / max(se0 ** 2, 1e-12)
    p_pri = delta / max(se_p ** 2, 1e-12)
    mu = (p_own * mu0 + p_pri * mu_p) / (p_own + p_pri)
    se = float(np.sqrt(1.0 / (p_own + p_pri)))
    return float(mu), se, delta
