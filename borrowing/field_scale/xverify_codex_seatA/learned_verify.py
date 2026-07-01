import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import minimize


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "corpus_full_1177.csv"
OUT_PATH = ROOT / "learned_verify_result.json"

REQUIRED_COLUMNS = ["ma", "family", "specialty", "yi", "se", "year"]
CV_SEEDS = (1729, 2027, 31415)
N_FOLDS = 10
WITHIN_MA_YEAR_BW = 1.0
BOOTSTRAP_SEED = 8675309
BOOTSTRAP_REPS = 20000


def _require_finite(name, values):
    arr = np.asarray(values)
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains non-finite values")


def load_data():
    df = pd.read_csv(DATA_PATH)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"missing required columns: {missing}")
    df = df.loc[:, REQUIRED_COLUMNS].copy()
    if len(df) != 1177:
        raise ValueError(f"expected 1177 rows, found {len(df)}")
    for col in ["ma", "family", "specialty"]:
        if df[col].isna().any():
            raise ValueError(f"{col} contains missing values")
        df[col] = df[col].astype(str)
    for col in ["yi", "se", "year"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    _require_finite("yi", df["yi"].to_numpy())
    _require_finite("se", df["se"].to_numpy())
    if np.any(df["se"].to_numpy() <= 0):
        raise ValueError("se must be positive")
    families = set(df["family"].unique())
    if families != {"SMD", "COR", "LOR"}:
        raise ValueError(f"unexpected family labels: {sorted(families)}")
    return df


def standardize_train_test(train_df, test_df):
    train_year = train_df["year"].to_numpy(dtype=float)
    test_year = test_df["year"].to_numpy(dtype=float)

    observed = np.isfinite(train_year)
    if not np.any(observed):
        year_mean = 0.0
        year_sd = 1.0
    else:
        year_mean = float(np.mean(train_year[observed]))
        year_sd = float(np.std(train_year[observed]))
        if year_sd <= 0 or not np.isfinite(year_sd):
            year_sd = 1.0

    def transform_year(values):
        out = np.zeros(len(values), dtype=float)
        ok = np.isfinite(values)
        out[ok] = (values[ok] - year_mean) / year_sd
        return out

    train_log_precision = np.log(1.0 / np.square(train_df["se"].to_numpy(dtype=float)))
    test_log_precision = np.log(1.0 / np.square(test_df["se"].to_numpy(dtype=float)))
    lp_mean = float(np.mean(train_log_precision))
    lp_sd = float(np.std(train_log_precision))
    if lp_sd <= 0 or not np.isfinite(lp_sd):
        lp_sd = 1.0

    x_train = np.column_stack(
        [
            transform_year(train_year),
            (train_log_precision - lp_mean) / lp_sd,
        ]
    )
    x_test = np.column_stack(
        [
            transform_year(test_year),
            (test_log_precision - lp_mean) / lp_sd,
        ]
    )
    return x_train, x_test


def make_folds(n, seed):
    rng = np.random.default_rng(seed)
    order = rng.permutation(n)
    folds = np.array_split(order, N_FOLDS)
    if any(len(fold) == 0 for fold in folds):
        raise ValueError("empty CV fold")
    return folds


def pairwise_components(x, specialty, ma):
    x0 = x[:, 0]
    x1 = x[:, 1]
    comp_year = np.square(x0[:, None] - x0[None, :])
    comp_log_precision = np.square(x1[:, None] - x1[None, :])
    comp_specialty = (specialty[:, None] != specialty[None, :]).astype(float)
    comp_ma = (ma[:, None] != ma[None, :]).astype(float)
    return comp_year, comp_log_precision, comp_specialty, comp_ma


def kernel_from_components(theta, components):
    log_sf2, log_ly, log_llp, log_lspec, log_lma, log_nugget = theta
    sf2 = np.exp(log_sf2)
    ly2 = np.exp(2.0 * log_ly)
    llp2 = np.exp(2.0 * log_llp)
    lspec2 = np.exp(2.0 * log_lspec)
    lma2 = np.exp(2.0 * log_lma)
    comp_year, comp_log_precision, comp_specialty, comp_ma = components
    scaled = (
        comp_year / ly2
        + comp_log_precision / llp2
        + comp_specialty / lspec2
        + comp_ma / lma2
    )
    k_signal = sf2 * np.exp(-0.5 * scaled)
    scaled_parts = (
        comp_year / ly2,
        comp_log_precision / llp2,
        comp_specialty / lspec2,
        comp_ma / lma2,
    )
    nugget = np.exp(log_nugget)
    return k_signal, scaled_parts, nugget


def robust_cholesky(cov):
    base = max(1.0, float(np.mean(np.diag(cov))))
    jitter = 1e-10 * base
    last_error = None
    for _ in range(8):
        try:
            return cho_factor(cov + jitter * np.eye(cov.shape[0]), lower=True, check_finite=False)
        except Exception as exc:
            last_error = exc
            jitter *= 10.0
    raise np.linalg.LinAlgError(f"Cholesky failed after jitter escalation: {last_error}")


def nll_and_grad(theta, y, se2, components):
    n = len(y)
    try:
        k_signal, scaled_parts, nugget = kernel_from_components(theta, components)
        cov = k_signal.copy()
        cov[np.diag_indices_from(cov)] += se2 + nugget
        cf = robust_cholesky(cov)

        ones = np.ones(n)
        inv_y = cho_solve(cf, y, check_finite=False)
        inv_ones = cho_solve(cf, ones, check_finite=False)
        denom = float(ones @ inv_ones)
        if denom <= 0 or not np.isfinite(denom):
            return 1e100, np.zeros_like(theta)
        mu = float((ones @ inv_y) / denom)
        resid = y - mu
        alpha = cho_solve(cf, resid, check_finite=False)
        logdet = 2.0 * np.sum(np.log(np.diag(cf[0])))
        ll = -0.5 * float(resid @ alpha) - 0.5 * logdet - 0.5 * n * np.log(2.0 * np.pi)

        inv_cov = cho_solve(cf, np.eye(n), check_finite=False)
        score_matrix = np.outer(alpha, alpha) - inv_cov
        d_covs = [
            k_signal,
            k_signal * scaled_parts[0],
            k_signal * scaled_parts[1],
            k_signal * scaled_parts[2],
            k_signal * scaled_parts[3],
            nugget * np.eye(n),
        ]
        grad_ll = np.array(
            [0.5 * np.sum(score_matrix * d_cov) for d_cov in d_covs],
            dtype=float,
        )
        if not np.isfinite(ll) or not np.all(np.isfinite(grad_ll)):
            return 1e100, np.zeros_like(theta)
        return -ll, -grad_ll
    except Exception:
        return 1e100, np.zeros_like(theta)


def initial_thetas(y, se2):
    y_var = float(np.var(y))
    if y_var <= 1e-6 or not np.isfinite(y_var):
        y_var = 1.0
    nug0 = max(1e-7, 0.05 * float(np.median(se2)))
    base = np.array(
        [
            np.log(y_var),
            np.log(1.0),
            np.log(1.0),
            np.log(1.0),
            np.log(0.45),
            np.log(nug0),
        ],
        dtype=float,
    )
    broad = np.array(
        [
            np.log(y_var),
            np.log(2.0),
            np.log(2.0),
            np.log(2.0),
            np.log(0.75),
            np.log(nug0),
        ],
        dtype=float,
    )
    local = np.array(
        [
            np.log(y_var),
            np.log(0.5),
            np.log(0.5),
            np.log(0.7),
            np.log(0.30),
            np.log(nug0),
        ],
        dtype=float,
    )
    return [base, broad, local]


def fit_gp(y, se2, x, specialty, ma):
    components = pairwise_components(x, specialty, ma)
    y_var = max(float(np.var(y)), 1e-3)
    se_med = max(float(np.median(se2)), 1e-8)
    bounds = [
        (np.log(1e-5 * y_var), np.log(1e3 * y_var)),
        (np.log(0.08), np.log(25.0)),
        (np.log(0.08), np.log(25.0)),
        (np.log(0.08), np.log(25.0)),
        (np.log(0.08), np.log(25.0)),
        (np.log(1e-8), np.log(max(10.0 * y_var, 10.0 * se_med, 1e-4))),
    ]

    best = None
    for start in initial_thetas(y, se2):
        start = np.array(
            [min(max(v, lo), hi) for v, (lo, hi) in zip(start, bounds)],
            dtype=float,
        )
        res = minimize(
            nll_and_grad,
            start,
            args=(y, se2, components),
            method="L-BFGS-B",
            jac=True,
            bounds=bounds,
            options={"maxiter": 100, "ftol": 1e-7, "gtol": 1e-5, "maxls": 30},
        )
        candidate_value = float(res.fun) if np.isfinite(res.fun) else np.inf
        if best is None or candidate_value < best[0]:
            best = (candidate_value, res.x)

    if best is None or not np.isfinite(best[0]):
        raise RuntimeError("GP hyperparameter optimization failed")

    theta = best[1]
    k_signal, _, nugget = kernel_from_components(theta, components)
    cov = k_signal.copy()
    cov[np.diag_indices_from(cov)] += se2 + nugget
    cf = robust_cholesky(cov)
    ones = np.ones(len(y))
    inv_y = cho_solve(cf, y, check_finite=False)
    inv_ones = cho_solve(cf, ones, check_finite=False)
    mu = float((ones @ inv_y) / (ones @ inv_ones))
    alpha = cho_solve(cf, y - mu, check_finite=False)
    return {"theta": theta, "mu": mu, "alpha": alpha, "x": x, "specialty": specialty, "ma": ma}


def cross_kernel(theta, x_test, spec_test, ma_test, x_train, spec_train, ma_train):
    log_sf2, log_ly, log_llp, log_lspec, log_lma, _ = theta
    sf2 = np.exp(log_sf2)
    ly2 = np.exp(2.0 * log_ly)
    llp2 = np.exp(2.0 * log_llp)
    lspec2 = np.exp(2.0 * log_lspec)
    lma2 = np.exp(2.0 * log_lma)
    scaled = (
        np.square(x_test[:, [0]] - x_train[None, :, 0]) / ly2
        + np.square(x_test[:, [1]] - x_train[None, :, 1]) / llp2
        + (spec_test[:, None] != spec_train[None, :]).astype(float) / lspec2
        + (ma_test[:, None] != ma_train[None, :]).astype(float) / lma2
    )
    return sf2 * np.exp(-0.5 * scaled)


def predict_gp(model, x_test, specialty_test, ma_test):
    k_cross = cross_kernel(
        model["theta"],
        x_test,
        specialty_test,
        ma_test,
        model["x"],
        model["specialty"],
        model["ma"],
    )
    return model["mu"] + k_cross @ model["alpha"]


def learned_kernel_cv_family(family_df):
    family_df = family_df.copy().reset_index(drop=False).rename(columns={"index": "global_index"})
    n = len(family_df)
    y_all = family_df["yi"].to_numpy(dtype=float)
    abs_errors_by_seed = []

    for seed in CV_SEEDS:
        fold_errors = np.full(n, np.nan, dtype=float)
        folds = make_folds(n, seed)
        for fold_number, test_pos in enumerate(folds, start=1):
            train_mask = np.ones(n, dtype=bool)
            train_mask[test_pos] = False
            train_df = family_df.loc[train_mask].copy()
            test_df = family_df.iloc[test_pos].copy()
            x_train, x_test = standardize_train_test(train_df, test_df)
            y_train = train_df["yi"].to_numpy(dtype=float)
            se2_train = np.square(train_df["se"].to_numpy(dtype=float))
            model = fit_gp(
                y_train,
                se2_train,
                x_train,
                train_df["specialty"].to_numpy(dtype=str),
                train_df["ma"].to_numpy(dtype=str),
            )
            pred = predict_gp(
                model,
                x_test,
                test_df["specialty"].to_numpy(dtype=str),
                test_df["ma"].to_numpy(dtype=str),
            )
            fold_errors[test_pos] = np.abs(pred - test_df["yi"].to_numpy(dtype=float))
            print(
                f"{family_df['family'].iloc[0]} seed={seed} fold={fold_number}/{N_FOLDS} "
                f"mae={np.mean(fold_errors[test_pos]):.6f}",
                file=sys.stderr,
                flush=True,
            )
        if np.any(~np.isfinite(fold_errors)):
            raise RuntimeError("not all studies received a held-out prediction")
        abs_errors_by_seed.append(fold_errors)

    return family_df["global_index"].to_numpy(dtype=int), np.vstack(abs_errors_by_seed)


def standardize_year_family(family_df):
    years = family_df["year"].to_numpy(dtype=float)
    ok = np.isfinite(years)
    if not np.any(ok):
        return np.zeros(len(years), dtype=float)
    mean = float(np.mean(years[ok]))
    sd = float(np.std(years[ok]))
    if sd <= 0 or not np.isfinite(sd):
        sd = 1.0
    out = np.zeros(len(years), dtype=float)
    out[ok] = (years[ok] - mean) / sd
    return out


def within_ma_errors(df):
    errors = np.full(len(df), np.nan, dtype=float)
    for family in sorted(df["family"].unique()):
        fam = df[df["family"] == family].copy()
        positions = fam.index.to_numpy(dtype=int)
        y = fam["yi"].to_numpy(dtype=float)
        se = fam["se"].to_numpy(dtype=float)
        precision = 1.0 / np.square(se)
        year_std = standardize_year_family(fam)
        ma = fam["ma"].to_numpy(dtype=str)
        for local_i, global_i in enumerate(positions):
            donors = (ma == ma[local_i])
            donors[local_i] = False
            if not np.any(donors):
                raise ValueError(f"no within-MA donor for row {global_i}")
            distance = year_std[donors] - year_std[local_i]
            year_weight = np.exp(-0.5 * np.square(distance / WITHIN_MA_YEAR_BW))
            weights = precision[donors] * year_weight
            if np.sum(weights) <= 0 or not np.isfinite(np.sum(weights)):
                raise ValueError(f"invalid within-MA weights for row {global_i}")
            pred = float(np.sum(weights * y[donors]) / np.sum(weights))
            errors[global_i] = abs(pred - y[local_i])
    if np.any(~np.isfinite(errors)):
        raise RuntimeError("within-MA errors incomplete")
    return errors


def paired_bootstrap(diff):
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    n = len(diff)
    means = np.empty(BOOTSTRAP_REPS, dtype=float)
    for b in range(BOOTSTRAP_REPS):
        sample = rng.integers(0, n, size=n)
        means[b] = float(np.mean(diff[sample]))
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(np.mean(diff)), float(lo), float(hi)


def round_float(value):
    return float(np.round(float(value), 10))


def main():
    df = load_data()
    learned_errors = np.full((len(CV_SEEDS), len(df)), np.nan, dtype=float)
    per_family_learned = {}

    for family in sorted(df["family"].unique()):
        family_idx, family_seed_errors = learned_kernel_cv_family(df[df["family"] == family])
        learned_errors[:, family_idx] = family_seed_errors
        per_family_learned[family] = round_float(np.mean(family_seed_errors))

    if np.any(~np.isfinite(learned_errors)):
        raise RuntimeError("learned-kernel errors incomplete")

    learned_per_study = np.mean(learned_errors, axis=0)
    within_errors = within_ma_errors(df)
    diff = learned_per_study - within_errors
    delta, lo, hi = paired_bootstrap(diff)

    result = {
        "engine": "from_scratch_numpy_scipy_grouped_ard_gp_repeated_10fold_cv_3seeds",
        "nodes": int(len(df)),
        "MAs": int(df["ma"].nunique()),
        "learned_kernel_MAE": round_float(np.mean(learned_per_study)),
        "within_MA_MAE": round_float(np.mean(within_errors)),
        "per_family_learned_MAE": per_family_learned,
        "learned_minus_within": {
            "delta": round_float(delta),
            "lo": round_float(lo),
            "hi": round_float(hi),
            "n": int(len(diff)),
        },
    }

    encoded = json.dumps(result, indent=2, sort_keys=False)
    OUT_PATH.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
