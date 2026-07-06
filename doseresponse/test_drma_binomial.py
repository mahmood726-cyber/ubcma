"""test_drma_binomial.py -- validate the one-stage RE logistic dose-response against
lme4::glmer (adaptive Gauss-Hermite) on the REAL dose-toxicity slice dat.ursino2021.

Gold-standard reference values are from `xverify_binomial.R` (lme4 2.0.1, nAGQ=15):
    b0    = -3.5522665 (se 0.4824124)
    b1    =  0.4293139 (se 0.0885819)   [logit per 100 dose-units]
    sigma =  0.4724973                  (study random-intercept SD)
    logLik = -27.948900  (isSingular = FALSE)

GLMM AGQ-vs-AGQ agreement is not a closed-form identity, so the tolerance is 1e-4
(the two engines still agree to ~1e-6 in practice) -- far tighter than any Monte-Carlo
check and consistent with the >=1e-9 exactness bar being reserved for the closed-form
two-stage GL DRMA validated vs dosresmeta.

Run: PYTHONPATH=doseresponse:src python -m pytest doseresponse/test_drma_binomial.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import drma_binomial as DB  # noqa: E402

DATA = Path("F:/public-data/metadat/dat.ursino2021.csv")

# lme4::glmer nAGQ=15 gold standard (xverify_binomial.R)
GLMER = dict(b0=-3.5522665, se_b0=0.4824124,
             b1=0.4293139, se_b1=0.0885819,
             sigma=0.4724973)


@pytest.fixture(scope="module")
def fit():
    if not DATA.exists():
        pytest.skip(f"metadat slice not on disk: {DATA}")
    df = pd.read_csv(DATA)
    return DB.fit_logistic_dr(df, nAGQ=15, dose_scale=100.0)


def test_predict_logit_respects_dose_scale():
    """Regression (P0-1): the slope b1 is fit on the SCALED dose (dose/dose_scale),
    so predict_logit must scale its RAW-dose argument by dose_scale before
    applying b1. The old predict_logit ignored dose_scale entirely (the field
    didn't even exist), making a scaled-dose fit's prediction off by a factor of
    dose_scale — e.g. predict_logit(100) returned ~+39 instead of ~-3.12."""
    # ursino2021 glmer gold values, fit with dose/100.
    f = DB.BinomialDRFit(b0=GLMER["b0"], b1=GLMER["b1"], sigma=GLMER["sigma"],
                         se_b0=0.0, se_b1=0.0, se_logsigma=0.0, loglik=0.0,
                         nAGQ=15, n_studies=5, dose_scale=100.0)
    # raw dose 100 -> scaled 1.0 -> logit = b0 + b1
    got = float(f.predict_logit(100.0))
    assert abs(got - (f.b0 + f.b1)) < 1e-9, got
    assert got < 0.0, got                      # ~ -3.12, NOT the buggy +39
    # array + scaling consistency at raw dose 200 -> scaled 2.0
    import numpy as _np
    assert abs(float(f.predict_logit(200.0)) - (f.b0 + 2.0 * f.b1)) < 1e-9


def test_matches_glmer_fixed_effects(fit):
    assert abs(fit.b0 - GLMER["b0"]) < 1e-4
    assert abs(fit.b1 - GLMER["b1"]) < 1e-4


def test_matches_glmer_standard_errors(fit):
    assert abs(fit.se_b0 - GLMER["se_b0"]) < 1e-3   # finite-diff Hessian SE
    assert abs(fit.se_b1 - GLMER["se_b1"]) < 1e-3


def test_matches_glmer_random_effect_sd(fit):
    assert abs(fit.sigma - GLMER["sigma"]) < 1e-4


def test_real_positive_dose_toxicity_gradient(fit):
    """ursino2021 has a genuine strong positive dose->toxicity slope (z ~ 4.85)."""
    assert fit.b1 > 0
    assert fit.b1 / fit.se_b1 > 4.0


def test_agq_converges_and_beats_laplace():
    """AGQ stabilises by nAGQ>=7; single-node (Laplace) differs -> AGQ matters here."""
    df = pd.read_csv(DATA)
    f7 = DB.fit_logistic_dr(df, nAGQ=7, dose_scale=100.0)
    f15 = DB.fit_logistic_dr(df, nAGQ=15, dose_scale=100.0)
    f25 = DB.fit_logistic_dr(df, nAGQ=25, dose_scale=100.0)
    assert abs(f7.b1 - f15.b1) < 1e-4
    assert abs(f15.b1 - f25.b1) < 1e-5          # flat by 15
    f1 = DB.fit_logistic_dr(df, nAGQ=1, dose_scale=100.0)
    assert abs(f1.b1 - f15.b1) > 1e-5           # Laplace genuinely differs


def test_handles_zero_cells_natively():
    """20/49 rows have zero events; the exact binomial must fit without any
    continuity correction (a structural zero at the reference dose would break GL)."""
    df = pd.read_csv(DATA)
    assert (df["events"] == 0).sum() >= 15      # sanity: the sparsity is real
    f = DB.fit_logistic_dr(df, nAGQ=15, dose_scale=100.0)
    assert np.isfinite(f.b1) and np.isfinite(f.loglik)
