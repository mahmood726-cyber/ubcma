"""sim_doseresponse.py -- dose-response datasets with known truth + selection.

Generates incidence-rate (ir) cohort dose-response studies whose true within-
study trend is linear with slope beta_i = beta + N(0, tau_slope^2). Each study
has J dose categories; counts are Poisson, so the log-RRs and their GL covariance
are exactly what drma.first_stage consumes.

Publication selection acts on the study's ESTIMATED trend (one-sided, favouring
significant positive trends) -- the dose-response analogue of small-study /
selection bias. This biases the naive pooled slope UPWARD; the question Stage 3
asks is whether an AdaptShrink aggregate recovers efficiency at matched coverage.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

DOSES = np.array([0.0, 1.0, 2.0, 4.0, 8.0])   # category 0 = reference


def gen_study(rng, sid, beta_study, base_rate=0.0025, py_scale=20000.0):
    """One ir cohort study. Returns (rows_df, b_hat, se_hat) where b_hat is the
    crude per-study linear slope estimate (used by the selection rule)."""
    J = len(DOSES)
    py = py_scale * (0.6 + 0.8 * rng.random(J))
    rate = base_rate * np.exp(beta_study * DOSES)
    cases = rng.poisson(rate * py).astype(float)
    cases = np.maximum(cases, 1.0)                 # avoid empty cells
    lograte = np.log(cases / py)
    logrr = lograte - lograte[0]
    var = 1.0 / cases + 1.0 / cases[0]             # Poisson log-rate-ratio var
    se = np.sqrt(var)
    se[0] = np.nan                                 # reference row
    # crude weighted slope through origin (for the selection rule only)
    x = DOSES[1:]
    w = 1.0 / var[1:]
    b_hat = float(np.sum(w * x * logrr[1:]) / np.sum(w * x * x))
    se_hat = float(np.sqrt(1.0 / np.sum(w * x * x)))
    rows = pd.DataFrame({
        "id": sid, "type": "ir", "dose": DOSES, "cases": cases,
        "peryears": py, "logrr": logrr, "se": se,
    })
    return rows, b_hat, se_hat


def _publish_prob(z, strength):
    if strength == "none":
        return 1.0
    if strength == "moderate":
        if z > 1.645:
            return 1.0
        return 0.40
    if strength == "strong":
        if z > 1.96:
            return 1.0
        if z > 1.0:
            return 0.50
        return 0.15
    raise ValueError(strength)


def gen_published(seed, strength, beta=0.045, tau_slope=0.02, k_target=14,
                  max_pool=400):
    """Generate a published dose-response dataset under one-sided selection.

    Returns (long_df, true_beta). Selection favours significant POSITIVE trends,
    biasing the naive pooled slope upward under 'moderate'/'strong'.
    """
    rng = np.random.default_rng(seed)
    kept = []
    sid = 0
    pool = 0
    while len(kept) < k_target and pool < max_pool:
        pool += 1
        beta_study = beta + rng.normal(0, tau_slope)
        rows, b_hat, se_hat = gen_study(rng, f"S{sid}", beta_study)
        z = b_hat / se_hat if se_hat > 0 else 0.0
        if rng.random() < _publish_prob(z, strength):
            rows = rows.copy()
            rows["id"] = f"P{len(kept)}"
            kept.append(rows)
            sid += 1
        else:
            sid += 1
    if not kept:
        return None, beta
    return pd.concat(kept, ignore_index=True), beta


def naive_pool_bias_check(strength, n=200, **kw):
    """Quick diagnostic: mean published per-study slope vs truth (selection bite)."""
    sl = []
    for s in range(n):
        df, beta = gen_published(s, strength, **kw)
        if df is None:
            continue
        for sid, g in df.groupby("id"):
            x = g["dose"].to_numpy()[1:]
            y = g["logrr"].to_numpy()[1:]
            v = g["se"].to_numpy()[1:] ** 2
            w = 1.0 / v
            sl.append(np.sum(w * x * y) / np.sum(w * x * x))
    return float(np.mean(sl)), beta
