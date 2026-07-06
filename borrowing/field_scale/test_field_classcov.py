"""Regression tests for the class-covariate prototype GP (field_classcov). Guards the two
error-prone pieces the flagship result rests on: the 7-parameter analytic marginal-likelihood
gradient, and the leakage-freedom + grain of the class-label derivation."""
import numpy as np
import field_classcov as fc


def test_obj5_analytic_gradient_matches_numeric():
    rng = np.random.default_rng(0)
    n = 14
    X = np.column_stack([rng.normal(size=n), rng.normal(size=n),
                         rng.integers(0, 3, n).astype(float),
                         rng.integers(0, 5, n).astype(float),
                         rng.integers(0, 4, n).astype(float)])
    y = rng.normal(size=n)
    alpha = np.abs(rng.normal(0.3, 0.1, n)) + 0.05
    comps = fc._dist_components5(X)
    theta = np.array([0.2, 0.1, -0.3, 0.4, 0.0, -0.2, np.log(1e-2)])
    _, g = fc._obj5(theta, comps, y, alpha)
    eps = 1e-6
    gnum = np.zeros(7)
    for i in range(7):
        tp = theta.copy(); tp[i] += eps
        tm = theta.copy(); tm[i] -= eps
        fp, _ = fc._obj5(tp, comps, y, alpha)
        fm, _ = fc._obj5(tm, comps, y, alpha)
        gnum[i] = (fp - fm) / (2 * eps)
    assert np.max(np.abs(g - gnum)) < 1e-4, (g, gnum)


def test_class_label_grain_and_leakage_free():
    # parsed from the MA NAME metadata, never from an effect value
    assert fc.class_label("aact_diabetesme_glucagon-l", "drug") == "glucagon-l"
    assert fc.class_label("aact_diabetesme_glucagon-l", "cond") == "diabetesme"
    # the donor-injection alias shares the base class (so the sibling matches the test half)
    assert fc.class_label("aact_diabetesme_glucagon-l__sib", "drug") == "glucagon-l"
    # a non-aact / corpus MA gets its own singleton class (no artificial grouping)
    assert fc.class_label("corpus_trialX", "drug") == "corpus_trialX"


def test_build_features_cls_adds_one_column():
    import pandas as pd
    sub = pd.DataFrame(dict(
        ma=["aact_a_x", "aact_a_x", "aact_b_y"], specialty=["s", "s", "s"],
        yi=[0.1, 0.2, 0.3], se=[0.2, 0.2, 0.2], year=[2010, 2011, 2012]))
    X = fc.build_features_cls(sub, "drug")
    assert X.shape == (3, 5)         # committed 4 cols + 1 class col
    assert X[0, 4] == X[1, 4]        # same drug class x -> same code
    assert X[0, 4] != X[2, 4]        # different drug class y -> different code
