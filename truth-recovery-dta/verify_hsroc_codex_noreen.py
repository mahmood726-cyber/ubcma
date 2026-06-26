#!/usr/bin/env python3
"""Independent HSROC/GLMM verification for the codex_noreen seat.

This script intentionally does not read or import ``src/ubcma/dta.py``.  It
uses only NumPy/SciPy for the statistical calculation.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.polynomial.hermite import hermgauss
from scipy.optimize import minimize
from scipy.special import expit, gammaln, logsumexp


ROOT = Path(__file__).resolve().parent
DEFAULT_COUNTS_PATH = ROOT / "reference_fits.json"
DEFAULT_GLMER_PATH = ROOT / "reference_glmm.json"
DEFAULT_RESULT_PATH = ROOT / "verify_hsroc_codex_noreen_result.json"


TP_ALIASES = {
    "tp",
    "tpos",
    "truepositive",
    "truepositives",
    "true_positive",
    "true_positives",
}
FN_ALIASES = {
    "fn",
    "fneg",
    "falsenegative",
    "falsenegatives",
    "false_negative",
    "false_negatives",
}
FP_ALIASES = {
    "fp",
    "fpos",
    "falsepositive",
    "falsepositives",
    "false_positive",
    "false_positives",
}
TN_ALIASES = {
    "tn",
    "tneg",
    "truenegative",
    "truenegatives",
    "true_negative",
    "true_negatives",
}
SENS_ALIASES = {
    "se",
    "sens",
    "sensitivity",
    "summarysensitivity",
    "summary_se",
    "summarysens",
}
SPEC_ALIASES = {
    "sp",
    "spec",
    "specificity",
    "summaryspecificity",
    "summary_sp",
    "summaryspec",
}
NLL_ALIASES = {
    "nll",
    "negloglik",
    "negativeloglikelihood",
    "negative_log_likelihood",
    "minusloglik",
    "minusloglikelihood",
    "minus_log_likelihood",
    "exactnll",
    "exact_nll",
}
LOGLIK_ALIASES = {"loglik", "loglikelihood", "log_likelihood", "logLik"}


@dataclass(frozen=True)
class Counts:
    name: str
    tp: np.ndarray
    fn: np.ndarray
    fp: np.ndarray
    tn: np.ndarray
    source_path: str


@dataclass(frozen=True)
class GlmerReference:
    name: str
    sensitivity: float | None
    specificity: float | None
    nll: float | None
    source_path: str


@dataclass(frozen=True)
class GHGrid:
    order: int
    z1: np.ndarray
    z2: np.ndarray
    log_weight: np.ndarray


def normalize_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def is_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float, np.integer, np.floating)):
        return math.isfinite(float(value))
    return False


def as_vector(value: Any) -> np.ndarray | None:
    try:
        arr = np.asarray(value, dtype=float)
    except (TypeError, ValueError):
        return None
    if arr.ndim != 1 or arr.size == 0 or not np.all(np.isfinite(arr)):
        return None
    return arr


def checked_counts(
    name: str,
    tp: Any,
    fn: Any,
    fp: Any,
    tn: Any,
    source_path: str,
) -> Counts | None:
    arrays = [as_vector(x) for x in (tp, fn, fp, tn)]
    if any(x is None for x in arrays):
        return None
    tp_arr, fn_arr, fp_arr, tn_arr = [np.asarray(x, dtype=float) for x in arrays]
    sizes = {x.size for x in (tp_arr, fn_arr, fp_arr, tn_arr)}
    if len(sizes) != 1:
        return None
    stacked = np.vstack([tp_arr, fn_arr, fp_arr, tn_arr])
    if np.any(stacked < 0):
        return None
    if np.max(np.abs(stacked - np.rint(stacked))) > 1e-8:
        return None
    tp_i, fn_i, fp_i, tn_i = [np.rint(x).astype(int) for x in (tp_arr, fn_arr, fp_arr, tn_arr)]
    if np.any(tp_i + fn_i <= 0) or np.any(fp_i + tn_i <= 0):
        return None
    return Counts(
        name=name,
        tp=tp_i,
        fn=fn_i,
        fp=fp_i,
        tn=tn_i,
        source_path=source_path,
    )


def get_by_alias(mapping: dict[str, Any], aliases: set[str]) -> Any | None:
    normalized = {normalize_key(k): v for k, v in mapping.items()}
    for alias in aliases:
        key = normalize_key(alias)
        if key in normalized:
            return normalized[key]
    return None


def name_from_entry(default: str, entry: Any) -> str:
    if isinstance(entry, dict):
        for key in ("name", "dataset", "dataset_name", "id", "label"):
            value = get_by_alias(entry, {key})
            if isinstance(value, str) and value.strip():
                return value.strip()
    return default


def counts_from_table_with_columns(name: str, entry: dict[str, Any], source_path: str) -> Counts | None:
    columns = None
    for key in ("columns", "colnames", "names", "header"):
        value = get_by_alias(entry, {key})
        if isinstance(value, list) and all(isinstance(x, str) for x in value):
            columns = value
            break
    if columns is None:
        return None

    rows = None
    for key in ("data", "rows", "counts", "studies"):
        value = get_by_alias(entry, {key})
        if isinstance(value, list):
            rows = value
            break
    if rows is None:
        return None

    col_map = {normalize_key(col): idx for idx, col in enumerate(columns)}

    def column(aliases: set[str]) -> list[float] | None:
        idx = None
        for alias in aliases:
            alias_key = normalize_key(alias)
            if alias_key in col_map:
                idx = col_map[alias_key]
                break
        if idx is None:
            return None
        out = []
        for row in rows:
            if not isinstance(row, (list, tuple)) or idx >= len(row) or not is_number(row[idx]):
                return None
            out.append(float(row[idx]))
        return out

    return checked_counts(
        name,
        column(TP_ALIASES),
        column(FN_ALIASES),
        column(FP_ALIASES),
        column(TN_ALIASES),
        source_path,
    )


def counts_from_rows(name: str, rows: list[Any], source_path: str) -> Counts | None:
    if not rows:
        return None
    if all(isinstance(row, dict) for row in rows):
        tp = [get_by_alias(row, TP_ALIASES) for row in rows]
        fn = [get_by_alias(row, FN_ALIASES) for row in rows]
        fp = [get_by_alias(row, FP_ALIASES) for row in rows]
        tn = [get_by_alias(row, TN_ALIASES) for row in rows]
        return checked_counts(name, tp, fn, fp, tn, source_path)

    try:
        arr = np.asarray(rows, dtype=float)
    except (TypeError, ValueError):
        return None
    if arr.ndim == 2 and arr.shape[1] >= 4 and np.all(np.isfinite(arr)):
        # Fallback for bare numeric count matrices: TP, FN, FP, TN.
        return checked_counts(name, arr[:, 0], arr[:, 1], arr[:, 2], arr[:, 3], source_path)
    return None


def extract_counts(name: str, entry: Any, source_path: str) -> Counts | None:
    if isinstance(entry, dict):
        name = name_from_entry(name, entry)
        direct = checked_counts(
            name,
            get_by_alias(entry, TP_ALIASES),
            get_by_alias(entry, FN_ALIASES),
            get_by_alias(entry, FP_ALIASES),
            get_by_alias(entry, TN_ALIASES),
            source_path,
        )
        if direct is not None:
            return direct

        with_columns = counts_from_table_with_columns(name, entry, source_path)
        if with_columns is not None:
            return with_columns

        for key in ("counts", "data", "rows", "studies", "table"):
            child = get_by_alias(entry, {key})
            if isinstance(child, list):
                from_rows = counts_from_rows(name, child, f"{source_path}.{key}")
                if from_rows is not None:
                    return from_rows
            if isinstance(child, dict):
                nested = extract_counts(name, child, f"{source_path}.{key}")
                if nested is not None:
                    return nested

        for key, value in entry.items():
            if isinstance(value, (dict, list)):
                nested = extract_counts(name, value, f"{source_path}.{key}")
                if nested is not None:
                    return nested

    if isinstance(entry, list):
        return counts_from_rows(name, entry, source_path)

    return None


def extract_counts_shallow(name: str, entry: Any, source_path: str) -> Counts | None:
    """Extract only if this object itself is a count table.

    This avoids treating a top-level mapping of many datasets as a single
    dataset merely because a recursive search can find the first child table.
    """
    if isinstance(entry, dict):
        name = name_from_entry(name, entry)
        direct = checked_counts(
            name,
            get_by_alias(entry, TP_ALIASES),
            get_by_alias(entry, FN_ALIASES),
            get_by_alias(entry, FP_ALIASES),
            get_by_alias(entry, TN_ALIASES),
            source_path,
        )
        if direct is not None:
            return direct

        with_columns = counts_from_table_with_columns(name, entry, source_path)
        if with_columns is not None:
            return with_columns

        for key in ("counts", "data", "rows", "studies", "table"):
            child = get_by_alias(entry, {key})
            if isinstance(child, list):
                from_rows = counts_from_rows(name, child, f"{source_path}.{key}")
                if from_rows is not None:
                    return from_rows
            if isinstance(child, dict):
                direct_child = extract_counts_shallow(name, child, f"{source_path}.{key}")
                if direct_child is not None:
                    return direct_child

    if isinstance(entry, list):
        return counts_from_rows(name, entry, source_path)

    return None


def load_count_sets(path: Path) -> list[Counts]:
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    out: list[Counts] = []
    if isinstance(raw, dict):
        whole = extract_counts_shallow(path.stem, raw, "$")
        if whole is not None:
            out.append(whole)
        else:
            parsed_container = False
            for key in ("datasets", "dataset", "reference_fits", "fits"):
                container = get_by_alias(raw, {key})
                if isinstance(container, dict):
                    for child_key, child_value in container.items():
                        found = extract_counts(str(child_key), child_value, f"$.{key}.{child_key}")
                        if found is not None:
                            out.append(found)
                    parsed_container = bool(out)
                elif isinstance(container, list):
                    for idx, child_value in enumerate(container):
                        found = extract_counts(f"dataset_{idx + 1}", child_value, f"$.{key}[{idx}]")
                        if found is not None:
                            out.append(found)
                    parsed_container = bool(out)
                if parsed_container:
                    break

            if not parsed_container:
                for key, value in raw.items():
                    found = extract_counts(str(key), value, f"$.{key}")
                    if found is not None:
                        out.append(found)
    elif isinstance(raw, list):
        for idx, value in enumerate(raw):
            found = extract_counts(f"dataset_{idx + 1}", value, f"$[{idx}]")
            if found is not None:
                out.append(found)

    if not out:
        raise ValueError(f"No TP/FN/FP/TN count sets found in {path}")

    seen: set[str] = set()
    unique: list[Counts] = []
    for counts in out:
        key = normalize_key(counts.name)
        if key in seen:
            raise ValueError(f"Duplicate dataset name after normalization: {counts.name!r}")
        seen.add(key)
        unique.append(counts)
    return unique


def flatten_numbers(entry: Any, prefix: str = "") -> list[tuple[str, str, float]]:
    values: list[tuple[str, str, float]] = []
    if isinstance(entry, dict):
        for key, value in entry.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if is_number(value):
                values.append((path, str(key), float(value)))
            else:
                values.extend(flatten_numbers(value, path))
    elif isinstance(entry, list):
        for idx, value in enumerate(entry):
            path = f"{prefix}[{idx}]"
            if is_number(value):
                values.append((path, str(idx), float(value)))
            elif isinstance(value, (dict, list)):
                values.extend(flatten_numbers(value, path))
    return values


def choose_scalar(
    numbers: list[tuple[str, str, float]],
    aliases: set[str],
    *,
    reject_path_parts: tuple[str, ...] = (),
) -> float | None:
    candidates: list[tuple[int, int, float]] = []
    alias_keys = {normalize_key(x) for x in aliases}
    reject_keys = tuple(normalize_key(x) for x in reject_path_parts)
    for path, leaf, value in numbers:
        path_key = normalize_key(path)
        leaf_key = normalize_key(leaf)
        if any(part in path_key for part in reject_keys):
            continue
        if leaf_key in alias_keys or path_key in alias_keys:
            candidates.append((0, len(path), value))
        elif any(path_key.endswith(alias) for alias in alias_keys):
            candidates.append((1, len(path), value))
    if not candidates:
        return None
    candidates.sort()
    return candidates[0][2]


def extract_reference(name: str, entry: Any, source_path: str) -> GlmerReference | None:
    if not isinstance(entry, (dict, list)):
        return None
    numbers = flatten_numbers(entry)
    if not numbers:
        return None

    sensitivity = choose_scalar(numbers, SENS_ALIASES, reject_path_parts=("stderr", "std_error", "standarderror"))
    specificity = choose_scalar(numbers, SPEC_ALIASES, reject_path_parts=("stderr", "std_error", "standarderror"))
    nll = choose_scalar(numbers, NLL_ALIASES)
    if nll is None:
        loglik = choose_scalar(numbers, LOGLIK_ALIASES)
        if loglik is not None:
            nll = -loglik

    if sensitivity is None and specificity is None and nll is None:
        return None
    if sensitivity is not None and not (0.0 < sensitivity < 1.0):
        sensitivity = None
    if specificity is not None and not (0.0 < specificity < 1.0):
        specificity = None
    return GlmerReference(
        name=name_from_entry(name, entry),
        sensitivity=sensitivity,
        specificity=specificity,
        nll=nll,
        source_path=source_path,
    )


def load_glmer_references(path: Path) -> list[GlmerReference]:
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    out: list[GlmerReference] = []
    whole = extract_reference(path.stem, raw, "$")
    if whole is not None and isinstance(raw, dict):
        # Treat as a single-dataset reference only when the top level itself has
        # scalar estimates. Otherwise parse the top-level mapping/list below.
        top_level_numbers = [
            (key, key, float(value)) for key, value in raw.items() if is_number(value)
        ]
        if top_level_numbers:
            out.append(whole)

    if not out:
        if isinstance(raw, dict):
            parsed_container = False
            for key in ("datasets", "dataset", "reference_glmm", "glmm", "glmer", "fits"):
                container = get_by_alias(raw, {key})
                if isinstance(container, dict):
                    for child_key, child_value in container.items():
                        found = extract_reference(str(child_key), child_value, f"$.{key}.{child_key}")
                        if found is not None:
                            out.append(found)
                    parsed_container = bool(out)
                elif isinstance(container, list):
                    for idx, child_value in enumerate(container):
                        found = extract_reference(f"dataset_{idx + 1}", child_value, f"$.{key}[{idx}]")
                        if found is not None:
                            out.append(found)
                    parsed_container = bool(out)
                if parsed_container:
                    break

            if not parsed_container:
                for key, value in raw.items():
                    found = extract_reference(str(key), value, f"$.{key}")
                    if found is not None:
                        out.append(found)
        elif isinstance(raw, list):
            for idx, value in enumerate(raw):
                found = extract_reference(f"dataset_{idx + 1}", value, f"$[{idx}]")
                if found is not None:
                    out.append(found)

    if not out:
        raise ValueError(f"No glmer reference estimates found in {path}")

    seen: set[str] = set()
    unique: list[GlmerReference] = []
    for ref in out:
        key = normalize_key(ref.name)
        if key in seen:
            raise ValueError(f"Duplicate glmer reference name after normalization: {ref.name!r}")
        seen.add(key)
        unique.append(ref)
    return unique


def match_references(counts: list[Counts], refs: list[GlmerReference]) -> dict[str, GlmerReference]:
    refs_by_name = {normalize_key(ref.name): ref for ref in refs}
    matches: dict[str, GlmerReference] = {}
    missing: list[str] = []
    for count_set in counts:
        key = normalize_key(count_set.name)
        if key in refs_by_name:
            matches[count_set.name] = refs_by_name[key]
        else:
            missing.append(count_set.name)

    if not missing:
        return matches

    if len(counts) == len(refs):
        return {count_set.name: ref for count_set, ref in zip(counts, refs)}

    raise ValueError(
        "Could not match count sets to glmer references by normalized name; "
        f"missing={missing!r}, count_names={[x.name for x in counts]!r}, "
        f"reference_names={[x.name for x in refs]!r}"
    )


def logit(prob: float) -> float:
    prob = min(max(float(prob), 1e-9), 1.0 - 1e-9)
    return math.log(prob / (1.0 - prob))


def gh_grid(order: int) -> GHGrid:
    x, w = hermgauss(order)
    x1, x2 = np.meshgrid(x, x, indexing="ij")
    w1, w2 = np.meshgrid(w, w, indexing="ij")
    return GHGrid(
        order=order,
        z1=(math.sqrt(2.0) * x1).ravel(),
        z2=(math.sqrt(2.0) * x2).ravel(),
        log_weight=(np.log(w1) + np.log(w2) - math.log(math.pi)).ravel(),
    )


def binom_logpmf_from_logit(k: np.ndarray, n: np.ndarray, eta: np.ndarray) -> np.ndarray:
    return (
        gammaln(n + 1.0)
        - gammaln(k + 1.0)
        - gammaln(n - k + 1.0)
        - k * np.logaddexp(0.0, -eta)
        - (n - k) * np.logaddexp(0.0, eta)
    )


def exact_nll(theta: np.ndarray, counts: Counts, grid: GHGrid) -> float:
    mu_sens, mu_fpr, log_sd_sens, log_sd_fpr, z_rho = theta
    sd_sens = math.exp(float(log_sd_sens))
    sd_fpr = math.exp(float(log_sd_fpr))
    rho = math.tanh(float(z_rho))
    rho_scale = math.sqrt(max(1.0 - rho * rho, 1e-14))

    eta_sens = mu_sens + sd_sens * grid.z1
    eta_fpr = mu_fpr + sd_fpr * (rho * grid.z1 + rho_scale * grid.z2)

    diseased = counts.tp + counts.fn
    non_diseased = counts.fp + counts.tn
    total = 0.0
    for tp, dis, fp, nondis in zip(counts.tp, diseased, counts.fp, non_diseased):
        log_terms = (
            grid.log_weight
            + binom_logpmf_from_logit(float(tp), float(dis), eta_sens)
            + binom_logpmf_from_logit(float(fp), float(nondis), eta_fpr)
        )
        total -= float(logsumexp(log_terms))
    if not math.isfinite(total):
        return float("inf")
    return total


def estimate_initial_sds(counts: Counts) -> tuple[float, float]:
    diseased = counts.tp + counts.fn
    non_diseased = counts.fp + counts.tn
    sens_logits = np.log((counts.tp + 0.5) / (counts.fn + 0.5))
    fpr_logits = np.log((counts.fp + 0.5) / (counts.tn + 0.5))
    sens_var = float(np.var(sens_logits, ddof=1)) if sens_logits.size > 1 else 0.25
    fpr_var = float(np.var(fpr_logits, ddof=1)) if fpr_logits.size > 1 else 0.25
    mean_dis = max(float(np.mean(diseased)), 1.0)
    mean_nondis = max(float(np.mean(non_diseased)), 1.0)
    sens_sd = math.sqrt(max(sens_var - 4.0 / mean_dis, 0.03))
    fpr_sd = math.sqrt(max(fpr_var - 4.0 / mean_nondis, 0.03))
    return min(max(sens_sd, 0.05), 4.0), min(max(fpr_sd, 0.05), 4.0)


def starting_points(counts: Counts, ref: GlmerReference | None) -> list[np.ndarray]:
    diseased = counts.tp + counts.fn
    non_diseased = counts.fp + counts.tn
    mu_sens = logit((float(np.sum(counts.tp)) + 0.5) / (float(np.sum(diseased)) + 1.0))
    mu_fpr = logit((float(np.sum(counts.fp)) + 0.5) / (float(np.sum(non_diseased)) + 1.0))
    sd_sens, sd_fpr = estimate_initial_sds(counts)

    means = [(mu_sens, mu_fpr)]
    if ref is not None and ref.sensitivity is not None and ref.specificity is not None:
        means.append((logit(ref.sensitivity), logit(1.0 - ref.specificity)))

    sd_pairs = [
        (sd_sens, sd_fpr),
        (0.15, 0.15),
        (0.35, 0.35),
        (0.75, 0.75),
        (1.5, 1.5),
        (sd_sens, 0.35),
        (0.35, sd_fpr),
    ]
    rhos = [0.0, math.atanh(0.35), math.atanh(-0.35), math.atanh(0.70), math.atanh(-0.70)]

    starts: list[np.ndarray] = []
    seen: set[tuple[float, ...]] = set()
    for mean_sens, mean_fpr in means:
        for sens_sd, fpr_sd in sd_pairs:
            for rho_start in rhos:
                theta = np.array(
                    [
                        mean_sens,
                        mean_fpr,
                        math.log(sens_sd),
                        math.log(fpr_sd),
                        rho_start,
                    ],
                    dtype=float,
                )
                key = tuple(np.round(theta, 8))
                if key not in seen:
                    starts.append(theta)
                    seen.add(key)
    return starts


def local_fit(
    counts: Counts,
    ref: GlmerReference | None,
    *,
    fit_order: int,
    final_order: int,
    max_starts: int,
) -> dict[str, Any]:
    bounds = [(-14.0, 14.0), (-14.0, 14.0), (-8.0, 3.0), (-8.0, 3.0), (-5.0, 5.0)]
    fit_grid = gh_grid(fit_order)

    starts = starting_points(counts, ref)[:max_starts]
    start_scores = [(exact_nll(theta, counts, fit_grid), theta) for theta in starts]
    start_scores.sort(key=lambda item: item[0])

    runs = []
    best_result = None
    for _, start in start_scores:
        result = minimize(
            lambda theta: exact_nll(np.asarray(theta, dtype=float), counts, fit_grid),
            start,
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": 2000, "ftol": 1e-10, "gtol": 1e-6, "maxls": 50},
        )
        runs.append(
            {
                "success": bool(result.success),
                "message": str(result.message),
                "fit_order_nll": float(result.fun),
                "parameters": [float(x) for x in result.x],
            }
        )
        if best_result is None or float(result.fun) < float(best_result.fun):
            best_result = result

    if best_result is None:
        raise RuntimeError(f"No optimizer runs completed for {counts.name}")

    final_grid = gh_grid(final_order)
    polish = minimize(
        lambda theta: exact_nll(np.asarray(theta, dtype=float), counts, final_grid),
        np.asarray(best_result.x, dtype=float),
        method="L-BFGS-B",
        bounds=bounds,
        options={"maxiter": 1500, "ftol": 5e-11, "gtol": 5e-6, "maxls": 50},
    )
    candidates = [np.asarray(best_result.x, dtype=float), np.asarray(polish.x, dtype=float)]
    candidate_scores = [(exact_nll(theta, counts, final_grid), theta) for theta in candidates]
    candidate_scores.sort(key=lambda item: item[0])
    best_theta = candidate_scores[0][1]
    final_nll = exact_nll(best_theta, counts, final_grid)

    mu_sens, mu_fpr, log_sd_sens, log_sd_fpr, z_rho = [float(x) for x in best_theta]
    return {
        "dataset": counts.name,
        "n_studies": int(counts.tp.size),
        "n_diseased": int(np.sum(counts.tp + counts.fn)),
        "n_non_diseased": int(np.sum(counts.fp + counts.tn)),
        "sensitivity": float(expit(mu_sens)),
        "specificity": float(expit(-mu_fpr)),
        "false_positive_rate": float(expit(mu_fpr)),
        "exact_nll": float(final_nll),
        "parameters": {
            "mu_sensitivity_logit": mu_sens,
            "mu_fpr_logit": mu_fpr,
            "sd_sensitivity_logit": float(math.exp(log_sd_sens)),
            "sd_fpr_logit": float(math.exp(log_sd_fpr)),
            "rho": float(math.tanh(z_rho)),
        },
        "optimizer": {
            "fit_order": fit_order,
            "final_order": final_order,
            "polish_success": bool(polish.success),
            "polish_message": str(polish.message),
            "runs": runs,
        },
    }


def build_result(
    counts_path: Path,
    glmer_path: Path,
    *,
    fit_order: int,
    final_order: int,
    max_starts: int,
    tolerance: float,
) -> dict[str, Any]:
    count_sets = load_count_sets(counts_path)
    glmer_refs = load_glmer_references(glmer_path)
    matches = match_references(count_sets, glmer_refs)

    per_dataset = []
    worst_agreement = 0.0
    exact_nll_flags = []
    for count_set in count_sets:
        ref = matches[count_set.name]
        fit = local_fit(
            count_set,
            ref,
            fit_order=fit_order,
            final_order=final_order,
            max_starts=max_starts,
        )

        se_diff = None if ref.sensitivity is None else abs(fit["sensitivity"] - ref.sensitivity)
        sp_diff = None if ref.specificity is None else abs(fit["specificity"] - ref.specificity)
        pair_worst = max([x for x in (se_diff, sp_diff) if x is not None], default=None)
        if pair_worst is not None:
            worst_agreement = max(worst_agreement, float(pair_worst))

        nll_margin = None if ref.nll is None else fit["exact_nll"] - ref.nll
        nll_ok = None if nll_margin is None else bool(nll_margin <= tolerance)
        if nll_ok is not None:
            exact_nll_flags.append(nll_ok)

        per_dataset.append(
            {
                **fit,
                "glmer_reference": {
                    "dataset": ref.name,
                    "sensitivity": ref.sensitivity,
                    "specificity": ref.specificity,
                    "nll": ref.nll,
                    "source_path": ref.source_path,
                },
                "comparison": {
                    "abs_sensitivity_diff": se_diff,
                    "abs_specificity_diff": sp_diff,
                    "worst_abs_se_sp_diff": pair_worst,
                    "exact_nll_minus_glmer_nll": nll_margin,
                    "exact_nll_le_glmer": nll_ok,
                },
                "counts_source_path": count_set.source_path,
            }
        )

    return {
        "seat_identifier": "codex_noreen",
        "status": "computed",
        "model": "bivariate binomial-normal GLMM fit by product Gauss-Hermite quadrature",
        "constraints": {
            "did_not_read_or_import": "src/ubcma/dta.py",
            "numerical_libraries": ["numpy", "scipy"],
        },
        "inputs": {
            "counts": str(counts_path),
            "glmer_reference": str(glmer_path),
        },
        "settings": {
            "fit_order": fit_order,
            "final_order": final_order,
            "max_starts": max_starts,
            "nll_tolerance": tolerance,
        },
        "summary": {
            "datasets": len(per_dataset),
            "worst_se_sp_agreement_vs_glmer": worst_agreement,
            "exact_nll_le_glmer_at_every_dataset": bool(exact_nll_flags and all(exact_nll_flags)),
        },
        "per_dataset": per_dataset,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--counts", type=Path, default=DEFAULT_COUNTS_PATH)
    parser.add_argument("--glmer", type=Path, default=DEFAULT_GLMER_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_RESULT_PATH)
    parser.add_argument("--fit-order", type=int, default=25)
    parser.add_argument("--final-order", type=int, default=41)
    parser.add_argument("--max-starts", type=int, default=35)
    parser.add_argument("--nll-tolerance", type=float, default=1e-5)
    args = parser.parse_args()

    result = build_result(
        args.counts,
        args.glmer,
        fit_order=args.fit_order,
        final_order=args.final_order,
        max_starts=args.max_starts,
        tolerance=args.nll_tolerance,
    )
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = result["summary"]
    print(
        "codex_noreen verification: "
        f"worst Se/Sp agreement={summary['worst_se_sp_agreement_vs_glmer']:.12g}; "
        f"exact-NLL <= glmer at every dataset="
        f"{summary['exact_nll_le_glmer_at_every_dataset']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
