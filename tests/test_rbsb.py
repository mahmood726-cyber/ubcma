"""RBSB (Robust Bayesian Sequential Borrowing) pilot — sanity-limit tests.

Truth-first validation gate for arXiv:2604.22431. These assert the estimator
reduces to KNOWN quantities in the limits the pilot brief requires, and that its
mixture is proper. No headline number from the paper is asserted.

Gates:
  * k=1               -> conjugate unit-information posterior (no borrowing).
  * all w_j = 0       -> each population's estimate is its own conjugate
                         unit-information update, independent of order (reduces
                         to existing no-borrowing shrinkage).
  * K=2               -> EXACTLY the two-component robust-MAP posterior
                         (independent Schmidli-style reference).
  * path weights      -> sum to 1 over P_{1:j} for every j (proper mixture).
  * prior-data conflict -> w*_K decreases monotonically to 0 as the last study
                         diverges from upstream (automatic attenuation).
  * w* in [0, 1]; borrowing tightens the posterior when studies are concordant.
"""

from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

import numpy as np
import pytest

from ubcma.rbsb import (
    _conjugate, _pool_path, rbsb_estimator, robust_map_2component,
)

TOL = 1e-9


# -- k = 1: pure unit-information conjugate posterior ----------------------

def test_k1_reduces_to_conjugate_unit_information_posterior():
    mu0, s0 = 0.0, 1.0
    res = rbsb_estimator([0.42], [0.20], mu0=mu0, s0=s0)
    step = res.final
    assert step.w_star == 0.0                    # w*_1 := 0, no borrowing
    pm, pv = _conjugate(mu0, s0, 0.42, 0.20)
    assert abs(step.post_mean - pm) < TOL
    assert abs(step.post_sd - math.sqrt(pv)) < TOL


# -- uninformative ordering: all w_j = 0 -> no borrowing, order-invariant --

def test_all_weights_zero_is_no_borrowing_and_order_invariant():
    mu0, s0 = 0.0, 1.5
    mus = [0.10, 0.55, -0.20, 0.33]
    ses = [0.22, 0.18, 0.30, 0.25]
    res = rbsb_estimator(mus, ses, w=[0, 0, 0, 0], mu0=mu0, s0=s0)

    # Each population's estimate is exactly its own conjugate unit-info update.
    for j, step in enumerate(res.steps):
        assert step.w_star == 0.0
        pm, pv = _conjugate(mu0, s0, mus[j], ses[j])
        assert abs(step.post_mean - pm) < TOL
        assert abs(step.post_sd - math.sqrt(pv)) < TOL

    # Order-invariance: shuffling the programme leaves each population's estimate
    # unchanged (no cross-population information flows when w = 0).
    perm = [2, 0, 3, 1]
    res2 = rbsb_estimator([mus[i] for i in perm], [ses[i] for i in perm],
                          w=[0, 0, 0, 0], mu0=mu0, s0=s0)
    by_input = {round(s.mu_hat, 12): (s.post_mean, s.post_sd) for s in res.steps}
    for s in res2.steps:
        pm, pv = by_input[round(s.mu_hat, 12)]
        assert abs(s.post_mean - pm) < TOL
        assert abs(s.post_sd - pv) < TOL


# -- K = 2: reduces EXACTLY to two-component robust-MAP --------------------

@pytest.mark.parametrize("w2", [0.2, 0.5, 0.8])
@pytest.mark.parametrize("mu2", [0.40, 0.05, -0.60])
def test_k2_reduces_to_robust_map(w2, mu2):
    mu0, s0 = 0.0, 1.0
    mu1, se1 = 0.45, 0.20
    se2 = 0.22

    res = rbsb_estimator([mu1, mu2], [se1, se2], w=[0.0, w2], mu0=mu0, s0=s0)
    step = res.final

    # RBSB informative component for study 2 is the pooled path {1} (prior + s1).
    mu_S1, s_S1 = _pool_path(mu0, s0, [mu1], [se1])
    ref = robust_map_2component(mu_S1, s_S1, mu0, s0, w2, mu2, se2)

    assert abs(step.w_star - ref["w_star"]) < TOL
    assert abs(step.post_mean - ref["post_mean"]) < TOL
    assert abs(step.post_sd - ref["post_sd"]) < TOL


# -- proper mixture: path weights sum to 1 over P_{1:j} --------------------

def test_path_weights_sum_to_one_each_step():
    res = rbsb_estimator([0.1, 0.3, 0.25, 0.4, 0.2],
                         [0.2, 0.18, 0.22, 0.25, 0.3],
                         w=[0, 0.6, 0.6, 0.6, 0.6], mu0=0.0, s0=1.0)
    for step in res.steps:
        total = sum(step.path_weights.values())
        assert abs(total - 1.0) < 1e-9, (step.index, step.path_weights)
        # Number of paths ending at j equals j.
        assert len(step.path_weights) == step.index


# -- prior-data conflict: automatic attenuation of borrowing ---------------

def test_prior_data_conflict_attenuates_borrowing_monotonically():
    # Three concordant upstream studies near 0.5, then a final study pushed
    # progressively far away. w*_K must fall monotonically toward 0.
    upstream_mu = [0.50, 0.48, 0.52]
    upstream_se = [0.15, 0.15, 0.15]
    se_last = 0.15
    w = [0, 0.7, 0.7, 0.7]

    w_stars = []
    for mu_last in [0.50, 0.9, 1.5, 2.5, 4.0]:
        res = rbsb_estimator(upstream_mu + [mu_last], upstream_se + [se_last],
                             w=w, mu0=0.0, s0=1.0)
        w_stars.append(res.final.w_star)

    # Strictly decreasing as the conflict grows; converging to ~0.
    for a, b in zip(w_stars, w_stars[1:]):
        assert b < a, w_stars
    assert w_stars[-1] < 0.05
    # Concordant case still borrows meaningfully.
    assert w_stars[0] > 0.4


# -- basic invariants ------------------------------------------------------

def test_w_star_in_unit_interval_and_finite():
    rng = np.random.default_rng(0)
    for _ in range(50):
        K = int(rng.integers(1, 7))
        mus = rng.normal(0.3, 0.5, K).tolist()
        ses = (0.1 + rng.random(K) * 0.4).tolist()
        ws = [0.0] + rng.random(K - 1).tolist()
        res = rbsb_estimator(mus, ses, w=ws, mu0=0.0, s0=1.0)
        for s in res.steps:
            assert 0.0 <= s.w_star <= 1.0
            assert math.isfinite(s.post_mean)
            assert s.post_sd >= 0.0 and math.isfinite(s.post_sd)


def test_concordant_borrowing_tightens_posterior():
    # With concordant neighbours and real borrowing, the final population's
    # posterior sd should be no wider than the no-borrowing (w=0) posterior.
    mus = [0.50, 0.52, 0.49]
    ses = [0.20, 0.20, 0.20]
    borrowed = rbsb_estimator(mus, ses, w=[0, 0.8, 0.8], mu0=0.0, s0=1.0).final
    none = rbsb_estimator(mus, ses, w=[0, 0.0, 0.0], mu0=0.0, s0=1.0).final
    assert borrowed.post_sd <= none.post_sd + 1e-12
    assert borrowed.w_star > 0.5      # concordant -> heavy borrowing
