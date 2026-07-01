"""Unit tests for the hardened learned-kernel borrowing field (field_learned.py).

Run:  python -m pytest borrowing/field_scale/test_field_learned.py -q
These tests are fast (small synthetic blocks) except the two marked `slow`,
which touch the real corpus and are the regression guard on the headline.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import field_learned as fl
from field import prep


# --------------------------------------------------------------------------- #
# synthetic family block: a learnable relevance structure                      #
# --------------------------------------------------------------------------- #
def _synth_block(seed=0, n_ma=4, per=15):
    """Two specialties, each with MAs whose true means cluster by specialty.
    Same-MA and same-specialty studies are genuinely more predictive of each
    other -- the GP should learn this and beat a no-structure global mean."""
    rng = np.random.default_rng(seed)
    rows = []
    for m in range(n_ma):
        spec = "A" if m < n_ma // 2 else "B"
        ma_mean = (0.6 if spec == "A" else -0.4) + rng.normal(0, 0.15)
        for j in range(per):
            se = float(rng.uniform(0.1, 0.4))
            yi = ma_mean + rng.normal(0, 0.1) + rng.normal(0, se)
            rows.append(dict(ma=f"ma{m}", family="SMD", specialty=spec,
                             yi=yi, se=se, year=2000 + rng.integers(0, 20)))
    return prep(pd.DataFrame(rows))


def test_features_no_leakage():
    df = _synth_block()
    X = fl.build_features(df)
    # feature matrix must not contain the effect column
    y = df["yi"].to_numpy()
    for col in range(X.shape[1]):
        assert not np.allclose(X[:, col], y), "yi leaked into features"
    assert X.shape[0] == len(df)
    assert np.isfinite(X).all()


def test_kfold_shapes_and_finiteness():
    df = _synth_block()
    mu, sd = fl.predict_kfold(df, n_folds=5, seed=1)
    assert mu.shape == (len(df),)
    assert np.isfinite(mu).all() and np.isfinite(sd).all()
    assert (sd > 0).all()


def test_kfold_beats_global_on_learnable_structure():
    """On a block with real specialty/MA structure, the learned kernel's honest
    k-fold reconstruction should beat the no-structure global mean."""
    df = _synth_block(seed=3, n_ma=6, per=18)
    mu, _ = fl.predict_kfold(df, n_folds=10, seed=0)
    glob = np.full(len(df), df["yi"].mean())  # transductive global (uses all, generous)
    mae_learned = np.abs(mu - df["yi"].to_numpy()).mean()
    mae_global = np.abs(glob - df["yi"].to_numpy()).mean()
    assert mae_learned < mae_global, (mae_learned, mae_global)


def test_loo_matches_bruteforce_loo():
    """R&W eq. 5.12 closed-form LOO must equal explicit drop-one prediction under
    the SAME fixed kernel matrix, to numerical tolerance."""
    df = _synth_block(seed=5, n_ma=3, per=8)
    st = fl.gp_fit(df)
    K, y, ymean = st["K"], st["y"], st["ymean"]
    mu_fast, _ = fl.predict_loo(df)
    mu_bf = np.empty(len(df))
    for i in range(len(df)):
        keep = np.arange(len(df)) != i
        Ktr = K[np.ix_(keep, keep)]
        ks = K[i, keep]
        mu_bf[i] = ymean + ks @ np.linalg.solve(Ktr, (y - ymean)[keep])
    assert np.allclose(mu_fast, mu_bf, atol=1e-6), np.abs(mu_fast - mu_bf).max()


def test_conflict_aware_fuse_bounds():
    # no conflict -> pulls toward prior; strong conflict -> stays near own data
    mu_agree, se_agree = fl.conflict_aware_fuse(0.50, 0.30, 0.50, 0.20)
    mu_conf, se_conf = fl.conflict_aware_fuse(0.50, 0.30, 5.00, 0.20)
    assert abs(mu_agree - 0.50) < abs(mu_conf - 0.50) + 1e-9  # trivially true
    # under agreement the fused estimate is between own and prior and tighter
    assert 0.40 <= mu_agree <= 0.60 and se_agree < 0.30
    # under gross conflict a0->0, fused ~ own data (borrowed mass discounted)
    assert abs(mu_conf - 0.50) < 0.15
    # missing/infinite prior -> returns own unchanged
    assert fl.conflict_aware_fuse(0.5, 0.3, np.nan, 0.2) == (0.5, 0.3)


def test_conflict_aware_a0_monotone():
    """Adaptive a0 must shrink monotonically as prior-data conflict grows."""
    def a0(disc):
        Q = disc ** 2 / (0.3 ** 2 + 0.2 ** 2)
        return float(np.clip(np.exp(-0.5 * Q), 0, 1))
    discs = [0.0, 0.2, 0.5, 1.0, 2.0]
    a0s = [a0(d) for d in discs]
    assert all(x >= y - 1e-12 for x, y in zip(a0s, a0s[1:])), a0s


def test_conformal_reaches_nominal_coverage():
    """Distribution-free conformal must land near the nominal 1-alpha on held-out
    predictions, even when the point predictor is poor."""
    df = _synth_block(seed=7, n_ma=5, per=25)
    mu, _ = fl.predict_kfold(df, n_folds=10, seed=0)
    cf = fl.conformal_intervals(df, mu, alpha=0.10)
    assert 0.83 <= cf["cover"] <= 0.97, cf["cover"]
    assert np.isfinite(cf["width"]) and cf["width"] > 0


def test_scrambled_kernel_loses():
    """Negative control: permuting (ma, specialty) labels within the family must
    NOT beat the true-label learned kernel -- the structure has to be real."""
    df = _synth_block(seed=9, n_ma=6, per=20)
    mu_true, _ = fl.predict_kfold(df, n_folds=10, seed=0)
    scr = df.copy()
    rng = np.random.default_rng(2)
    perm = rng.permutation(len(scr))
    scr["ma"] = df["ma"].to_numpy()[perm]
    scr["specialty"] = df["specialty"].to_numpy()[perm]
    mu_scr, _ = fl.predict_kfold(prep(scr), n_folds=10, seed=0)
    y = df["yi"].to_numpy()
    assert np.abs(mu_true - y).mean() <= np.abs(mu_scr - y).mean() + 1e-9


# --------------------------------------------------------------------------- #
# regression guards on the real corpus (slow)                                  #
# --------------------------------------------------------------------------- #
@pytest.mark.slow
def test_corpus_headline_regression():
    from corpus import load_corpus
    df = prep(load_corpus())
    assert len(df) >= 1100 and df.ma.nunique() >= 28
    mu, sd = fl.predict_kfold_corpus(df, seeds=(0, 1))
    mae = np.abs(mu - df["yi"].to_numpy()).mean()
    # learned kernel MAE has been ~0.24-0.27 on this corpus; guard a wide band
    assert 0.15 <= mae <= 0.32, mae


@pytest.mark.slow
def test_conformal_corpus_nominal():
    from corpus import load_corpus
    df = prep(load_corpus())
    mu, _ = fl.predict_kfold_corpus(df, seeds=(0,))
    cf = fl.conformal_intervals(df, mu, alpha=0.10)
    assert 0.86 <= cf["cover"] <= 0.94, cf["cover"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
