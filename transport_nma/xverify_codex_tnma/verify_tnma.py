from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


EXTERNAL_BIAS = 0.158
N_REPS = 400
N_BOOT = 5000
SEED = 20260704
BIAS_GRID = (0.0, 0.15, 0.30)

TREATMENT_TO_CLASS = {
    "metformin": "metformin",
    "sitagliptin": "DPP4",
    "vildagliptin": "DPP4",
    "sulfonylurea": "SU",
    "pioglitazone": "TZD",
    "rosiglitazone": "TZD",
    "acarbose": "AGI",
    "miglitol": "AGI",
    "benfluorex": None,
    "placebo": None,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def finite_float(value: object, name: str) -> float:
    out = float(value)
    require(math.isfinite(out), f"{name} must be finite")
    return out


def json_ready(obj):
    if isinstance(obj, dict):
        return {str(k): json_ready(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [json_ready(v) for v in obj]
    if isinstance(obj, tuple):
        return [json_ready(v) for v in obj]
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return [json_ready(v) for v in obj.tolist()]
    return obj


def load_inputs(base: Path):
    aact_path = base / "aact_hba1c_records.csv"
    lambda_path = base / "class_lambda.json"
    senn_path = base / "dat.senn2013.csv"
    for path in (aact_path, lambda_path, senn_path):
        require(path.exists(), f"missing required input: {path.name}")

    aact = pd.read_csv(aact_path)
    senn = pd.read_csv(senn_path)
    with lambda_path.open("r", encoding="utf-8") as fh:
        class_lambda = json.load(fh)

    require(
        {"nct_id", "drug_class", "published", "abs_md_pct"}.issubset(aact.columns),
        "aact_hba1c_records.csv is missing required columns",
    )
    require(
        {"study", "treatment", "mi", "sdi", "ni"}.issubset(senn.columns),
        "dat.senn2013.csv is missing required columns",
    )

    aact = aact.copy()
    aact["published"] = pd.to_numeric(aact["published"], errors="raise").astype(int)
    aact["abs_md_pct"] = pd.to_numeric(aact["abs_md_pct"], errors="raise")
    require(set(aact["published"].unique()).issubset({0, 1}), "published must be 0/1")
    require(np.isfinite(aact["abs_md_pct"]).all(), "abs_md_pct contains non-finite values")
    require((aact["abs_md_pct"] >= 0).all(), "abs_md_pct must be non-negative")
    require(aact["nct_id"].notna().all(), "nct_id contains missing values")
    require(aact["drug_class"].notna().all(), "drug_class contains missing values")

    class_lambda = {
        str(k): finite_float(v, f"lambda[{k}]") for k, v in class_lambda.items()
    }
    for cls, lam in class_lambda.items():
        require(0.0 <= lam <= 1.0, f"lambda[{cls}] must be in [0, 1]")

    senn = senn.copy()
    for col in ("mi", "sdi", "ni"):
        senn[col] = pd.to_numeric(senn[col], errors="raise")
        require(np.isfinite(senn[col]).all(), f"{col} contains non-finite values")
    require((senn["sdi"] > 0).all(), "sdi must be positive")
    require((senn["ni"] > 0).all(), "ni must be positive")
    require(senn["study"].notna().all(), "study contains missing values")
    require(senn["treatment"].notna().all(), "treatment contains missing values")

    dup = senn.duplicated(["study", "treatment"], keep=False)
    require(not bool(dup.any()), "duplicate study/treatment arms found")

    return aact, class_lambda, senn


def claim1_registry_gap(aact: pd.DataFrame, class_lambda: dict[str, float]) -> dict:
    rows = []
    for drug_class, grp in aact.groupby("drug_class", sort=True):
        published = grp.loc[grp["published"] == 1, "abs_md_pct"]
        registered = grp.loc[grp["published"] == 0, "abs_md_pct"]
        n_pub = int(published.shape[0])
        n_reg = int(registered.shape[0])
        if min(n_pub, n_reg) < 8:
            continue
        require(drug_class in class_lambda, f"class_lambda.json missing {drug_class}")
        mean_pub = float(published.mean())
        mean_reg = float(registered.mean())
        require(mean_reg > 0.0, f"registered-only mean is zero for {drug_class}")
        kappa = mean_pub / mean_reg - 1.0
        rows.append(
            {
                "drug_class": str(drug_class),
                "n_published": n_pub,
                "n_registered_only": n_reg,
                "weight": min(n_pub, n_reg),
                "mean_published_abs_md_pct": mean_pub,
                "mean_registered_only_abs_md_pct": mean_reg,
                "kappa_MD": kappa,
                "lambda": class_lambda[drug_class],
                "selection_severity": 1.0 - class_lambda[drug_class],
            }
        )

    require(len(rows) >= 2, "need at least two eligible classes for correlation")
    weights = np.array([row["weight"] for row in rows], dtype=float)
    kappas = np.array([row["kappa_MD"] for row in rows], dtype=float)
    severities = np.array([row["selection_severity"] for row in rows], dtype=float)
    require(float(weights.sum()) > 0.0, "eligible class weights sum to zero")
    require(np.std(kappas) > 0.0, "kappa values have zero variance")
    require(np.std(severities) > 0.0, "selection severities have zero variance")

    return {
        "kappa_pooled": float(np.sum(np.maximum(0.0, kappas) * weights) / np.sum(weights)),
        "corr": float(np.corrcoef(kappas, severities)[0, 1]),
        "classes_used": [row["drug_class"] for row in rows],
        "by_class": rows,
    }


def build_pairwise_contrasts(senn: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for study, grp in senn.groupby("study", sort=False):
        grp = grp.reset_index(drop=True)
        placebo_rows = grp.index[grp["treatment"] == "placebo"].tolist()
        if placebo_rows:
            require(len(placebo_rows) == 1, f"study {study} has multiple placebo arms")
            ref_idx = placebo_rows[0]
        else:
            ref_idx = 0
        ref = grp.loc[ref_idx]

        for idx, arm in grp.iterrows():
            if idx == ref_idx:
                continue
            te = float(arm["mi"] - ref["mi"])
            sete = math.sqrt(float(arm["sdi"] ** 2 / arm["ni"] + ref["sdi"] ** 2 / ref["ni"]))
            rows.append(
                {
                    "study": str(study),
                    "treatment": str(arm["treatment"]),
                    "reference": str(ref["treatment"]),
                    "TE": te,
                    "seTE": sete,
                    "variance": sete * sete,
                }
            )

    contrasts = pd.DataFrame(rows)
    require(not contrasts.empty, "no pairwise contrasts constructed")
    require(np.isfinite(contrasts["TE"]).all(), "contrast TE contains non-finite values")
    require((contrasts["seTE"] > 0).all(), "contrast seTE must be positive")
    return contrasts


def treatment_order(contrasts: pd.DataFrame) -> list[str]:
    treatments = set(contrasts["treatment"]).union(set(contrasts["reference"]))
    require("placebo" in treatments, "placebo is required as the NMA reference")
    active = sorted(treatments - {"placebo"})
    require(active, "no active treatments found")
    return active


def design_matrix(contrasts: pd.DataFrame, active: list[str]) -> np.ndarray:
    index = {name: idx for idx, name in enumerate(active)}
    x = np.zeros((contrasts.shape[0], len(active)), dtype=float)
    for i, row in enumerate(contrasts.itertuples(index=False)):
        if row.treatment != "placebo":
            require(row.treatment in index, f"unknown treatment {row.treatment}")
            x[i, index[row.treatment]] += 1.0
        if row.reference != "placebo":
            require(row.reference in index, f"unknown reference {row.reference}")
            x[i, index[row.reference]] -= 1.0
    return x


def solve_wls(x: np.ndarray, y: np.ndarray, variances: np.ndarray):
    require(np.all(variances > 0.0), "all variances must be positive")
    w = 1.0 / variances
    xtwx = x.T @ (x * w[:, None])
    rank = int(np.linalg.matrix_rank(xtwx))
    require(rank == xtwx.shape[0], "NMA design is rank deficient")
    xtwy = x.T @ (w * y)
    beta = np.linalg.solve(xtwx, xtwy)
    cov = np.linalg.inv(xtwx)
    resid = y - x @ beta
    return beta, cov, resid, w, xtwx


def fit_nma_arrays(x: np.ndarray, y: np.ndarray, se: np.ndarray) -> dict:
    base_var = se * se
    beta_fe, _cov_fe, resid_fe, w_fe, xtwx_fe = solve_wls(x, y, base_var)
    df = int(y.shape[0] - np.linalg.matrix_rank(x))
    require(df > 0, "not enough residual degrees of freedom for DL tau^2")
    q = float(np.sum(w_fe * resid_fe * resid_fe))
    xw2x = x.T @ (x * (w_fe * w_fe)[:, None])
    c = float(np.sum(w_fe) - np.trace(np.linalg.inv(xtwx_fe) @ xw2x))
    require(c > 0.0, "DL tau^2 denominator is non-positive")
    tau2 = max(0.0, (q - df) / c)

    beta, cov, resid, w_re, _xtwx_re = solve_wls(x, y, base_var + tau2)
    q_re = float(np.sum(w_re * resid * resid))
    return {
        "beta": beta,
        "se": np.sqrt(np.diag(cov)),
        "tau2": float(tau2),
        "q_fe": q,
        "q_re": q_re,
        "df": df,
    }


def fit_nma(contrasts: pd.DataFrame, active: list[str]) -> dict:
    x = design_matrix(contrasts, active)
    y = contrasts["TE"].to_numpy(dtype=float)
    se = contrasts["seTE"].to_numpy(dtype=float)
    fit = fit_nma_arrays(x, y, se)
    effects = {"placebo": 0.0}
    effects.update({name: float(value) for name, value in zip(active, fit["beta"])})
    ses = {name: float(value) for name, value in zip(active, fit["se"])}
    fit.update(
        {
            "effects": effects,
            "effect_se": ses,
            "n_contrasts": int(contrasts.shape[0]),
            "n_active_treatments": int(len(active)),
        }
    )
    return fit


def lambda_for_treatment(treatment: str, class_lambda: dict[str, float]) -> float:
    drug_class = TREATMENT_TO_CLASS.get(treatment)
    if drug_class is None:
        return 1.0
    return float(class_lambda.get(drug_class, 1.0))


def bootstrap_delta(
    estimator_abs: np.ndarray,
    unadjusted_abs: np.ndarray,
    rng: np.random.Generator,
) -> dict:
    est = estimator_abs.reshape(-1)
    unadj = unadjusted_abs.reshape(-1)
    require(est.shape == unadj.shape, "paired bootstrap arrays have different shapes")
    n = int(est.shape[0])
    point = float(2.0 * np.quantile(est, 0.95) - 2.0 * np.quantile(unadj, 0.95))

    boot = np.empty(N_BOOT, dtype=float)
    for b in range(N_BOOT):
        idx = rng.integers(0, n, size=n)
        boot[b] = 2.0 * np.quantile(est[idx], 0.95) - 2.0 * np.quantile(unadj[idx], 0.95)
    ci = np.quantile(boot, [0.025, 0.975])
    return {
        "dMCIW0": point,
        "ci95": [float(ci[0]), float(ci[1])],
        "mciw0": float(2.0 * np.quantile(est, 0.95)),
    }


def truth_gate(
    contrasts: pd.DataFrame,
    active: list[str],
    observed_fit: dict,
    class_lambda: dict[str, float],
) -> dict:
    rng = np.random.default_rng(SEED)
    x = design_matrix(contrasts, active)
    se = contrasts["seTE"].to_numpy(dtype=float)
    true_effects = observed_fit["effects"]
    true_active = np.array([true_effects[t] for t in active], dtype=float)
    lambda_active = np.array([lambda_for_treatment(t, class_lambda) for t in active], dtype=float)
    contrast_treat = contrasts["treatment"].astype(str).tolist()
    contrast_ref = contrasts["reference"].astype(str).tolist()

    out = {}
    for bias in BIAS_GRID:
        d_obs = {}
        for treatment in set(contrast_treat).union(contrast_ref):
            if treatment == "placebo":
                d_obs[treatment] = 0.0
            else:
                lam = lambda_for_treatment(treatment, class_lambda)
                d_obs[treatment] = true_effects[treatment] * (1.0 + bias * (1.0 - lam))
        mean_te = np.array([d_obs[t] - d_obs[r] for t, r in zip(contrast_treat, contrast_ref)])

        unadjusted_abs = np.empty((N_REPS, len(active)), dtype=float)
        oracle_abs = np.empty_like(unadjusted_abs)
        external_abs = np.empty_like(unadjusted_abs)

        for rep in range(N_REPS):
            y_sim = mean_te + rng.normal(loc=0.0, scale=se)
            beta = fit_nma_arrays(x, y_sim, se)["beta"]
            unadjusted = beta
            oracle = beta * (1.0 - bias * (1.0 - lambda_active))
            external = beta * (1.0 - EXTERNAL_BIAS * (1.0 - lambda_active))

            unadjusted_abs[rep, :] = np.abs(unadjusted - true_active)
            oracle_abs[rep, :] = np.abs(oracle - true_active)
            external_abs[rep, :] = np.abs(external - true_active)

        unadjusted_mciw0 = float(2.0 * np.quantile(unadjusted_abs.reshape(-1), 0.95))
        out[f"{bias:.1f}" if bias in (0.0,) else f"{bias:.2f}"] = {
            "unadjusted_mciw0": unadjusted_mciw0,
            "oracle": bootstrap_delta(oracle_abs, unadjusted_abs, rng),
            "external": bootstrap_delta(external_abs, unadjusted_abs, rng),
        }

    return out


def verdict_and_notes(kappa_pooled: float, corr: float, truthgate: dict) -> tuple[str, str]:
    failures = []
    if not (0.13 <= kappa_pooled <= 0.18):
        failures.append(f"kappa_pooled={kappa_pooled:.3f} outside 0.13-0.18")
    if not (corr > 0.3):
        failures.append(f"corr={corr:.3f} not clearly positive (>0.3)")

    b015 = truthgate["0.15"]
    oracle = float(b015["oracle"]["dMCIW0"])
    external = float(b015["external"]["dMCIW0"])
    gap = abs(external - oracle)
    if not (oracle < 0.0 and external < 0.0 and gap <= 0.03):
        failures.append(
            "B=0.15 truth-gate failed: "
            f"oracle dMCIW0={oracle:.3f}, external dMCIW0={external:.3f}, gap={gap:.3f}"
        )

    if failures:
        return "DIVERGES", "; ".join(failures)
    return (
        "CONFIRMS",
        "Claim 1 thresholds pass and the frozen external correction tracks the oracle at B=0.15.",
    )


def print_summary(result: dict) -> None:
    print("CLAIM 1")
    print(f"kappa_pooled: {result['kappa_pooled']:.6f}")
    print(f"corr:         {result['corr']:.6f}")
    print(f"classes_used: {', '.join(result['classes_used'])}")
    print()
    print("TRUTH-GATE dMCIW0")
    print("B      unadjusted_MCIW0  oracle dMCIW0 [95% CI]      external dMCIW0 [95% CI]")
    for bias, row in result["truthgate"].items():
        oracle = row["oracle"]
        external = row["external"]
        print(
            f"{bias:<5} "
            f"{row['unadjusted_mciw0']:.6f}          "
            f"{oracle['dMCIW0']:.6f} [{oracle['ci95'][0]:.6f}, {oracle['ci95'][1]:.6f}]   "
            f"{external['dMCIW0']:.6f} [{external['ci95'][0]:.6f}, {external['ci95'][1]:.6f}]"
        )
    print()
    print(f"VERDICT: {result['verdict']}")
    print(result["notes"])


def main() -> None:
    base = Path(__file__).resolve().parent
    aact, class_lambda, senn = load_inputs(base)
    claim1 = claim1_registry_gap(aact, class_lambda)
    contrasts = build_pairwise_contrasts(senn)
    active = treatment_order(contrasts)
    observed_fit = fit_nma(contrasts, active)
    truthgate = truth_gate(contrasts, active, observed_fit, class_lambda)
    verdict, notes = verdict_and_notes(claim1["kappa_pooled"], claim1["corr"], truthgate)

    result = {
        "kappa_pooled": claim1["kappa_pooled"],
        "corr": claim1["corr"],
        "classes_used": claim1["classes_used"],
        "claim1_by_class": claim1["by_class"],
        "nma": {
            "method": "standalone contrast-level graph/WLS NMA with DerSimonian-Laird tau^2",
            "reference": "placebo",
            "tau2": observed_fit["tau2"],
            "q_fe": observed_fit["q_fe"],
            "q_re": observed_fit["q_re"],
            "df": observed_fit["df"],
            "n_contrasts": observed_fit["n_contrasts"],
            "n_active_treatments": observed_fit["n_active_treatments"],
            "effects": observed_fit["effects"],
            "effect_se": observed_fit["effect_se"],
        },
        "truthgate": truthgate,
        "verdict": verdict,
        "notes": notes,
        "config": {
            "n_reps": N_REPS,
            "n_bootstrap": N_BOOT,
            "seed": SEED,
            "external_bias": EXTERNAL_BIAS,
            "bias_grid": list(BIAS_GRID),
        },
    }

    result = json_ready(result)
    print_summary(result)
    with (base / "verify_result.json").open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(result, fh, indent=2, sort_keys=False)
        fh.write("\n")


if __name__ == "__main__":
    main()
