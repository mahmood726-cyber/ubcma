import json
from pathlib import Path

import numpy as np
import pandas as pd


DATA_PATH = Path("data.csv")
OUT_PATH = Path("witness_out.json")
TARGET_MA = "aact_diabetesme_glucagon-l"

K_NEIGHBORS = 15
SPECIALTY_MISMATCH_PENALTY = 9.0
MA_MISMATCH_PENALTY = 1.0

REQUIRED_COLUMNS = {
    "ma",
    "specialty",
    "yi",
    "se",
    "year",
    "is_aact",
    "split_role",
}


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")

    if df.empty:
        raise ValueError("data.csv is empty")
    if df["se"].isna().any() or (df["se"] <= 0).any():
        raise ValueError("all standard errors must be positive and non-missing")
    if not set(df["is_aact"].unique()).issubset({0, 1}):
        raise ValueError("is_aact must contain only 0/1")
    if not set(df["split_role"].unique()).issubset({"donor", "test", "none"}):
        raise ValueError("split_role contains an unexpected value")
    if df[["ma", "specialty", "yi"]].isna().any().any():
        raise ValueError("ma, specialty, and yi must be non-missing")

    base_bad = df[(df["is_aact"] == 0) & (df["split_role"] != "none")]
    held_bad = df[(df["is_aact"] == 1) & (~df["split_role"].isin(["donor", "test"]))]
    if not base_bad.empty or not held_bad.empty:
        raise ValueError("split_role is inconsistent with is_aact")

    held_counts = df[df["is_aact"] == 1].groupby(["ma", "split_role"]).size().unstack(fill_value=0)
    if (held_counts.get("donor", 0) <= 0).any() or (held_counts.get("test", 0) <= 0).any():
        raise ValueError("each held-out MA must have donor and test rows")

    df = df.copy()
    df["_row_id"] = np.arange(len(df))
    df["log_precision"] = np.log(1.0 / np.square(df["se"].astype(float)))
    return df


def standardized_numeric(train: pd.DataFrame, test: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    cols = ["year", "log_precision"]
    train_raw = train[cols].astype(float)
    test_raw = test[cols].astype(float)
    mean = train_raw.mean(skipna=True)
    if mean.isna().any():
        raise ValueError("cannot standardize a numeric feature that is missing in all training rows")
    std = train_raw.std(ddof=0, skipna=True).replace(0.0, 1.0).fillna(1.0)
    train_x = ((train_raw.fillna(mean) - mean) / std).to_numpy(dtype=float)
    test_x = ((test_raw.fillna(mean) - mean) / std).to_numpy(dtype=float)
    return train_x, test_x


def local_kernel_predict(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    if train.empty:
        raise ValueError("training set is empty")
    if test.empty:
        return np.array([], dtype=float)

    train_x, test_x = standardized_numeric(train, test)
    train_y = train["yi"].to_numpy(dtype=float)
    train_specialty = train["specialty"].to_numpy()
    train_ma = train["ma"].to_numpy()
    train_row_id = train["_row_id"].to_numpy()

    predictions = []
    k = min(K_NEIGHBORS, len(train))

    for i, row in enumerate(test.itertuples(index=False)):
        numeric_d2 = np.square(train_x - test_x[i]).sum(axis=1)
        specialty_d2 = (train_specialty != row.specialty).astype(float) * SPECIALTY_MISMATCH_PENALTY
        ma_d2 = (train_ma != row.ma).astype(float) * MA_MISMATCH_PENALTY
        d2 = numeric_d2 + specialty_d2 + ma_d2

        nearest = np.lexsort((train_row_id, d2))[:k]
        bandwidth2 = max(float(d2[nearest].max()), 1e-12)
        weights = np.exp(-0.5 * d2[nearest] / bandwidth2)
        predictions.append(float(np.dot(weights, train_y[nearest]) / weights.sum()))

    return np.array(predictions, dtype=float)


def within_ma_baseline(df: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    predictions = []
    for _, row in test.iterrows():
        siblings = df[(df["ma"] == row["ma"]) & (df["_row_id"] != row["_row_id"])]
        if siblings.empty:
            raise ValueError(f"no within-MA siblings for row {row['_row_id']}")
        weights = 1.0 / np.square(siblings["se"].to_numpy(dtype=float))
        yi = siblings["yi"].to_numpy(dtype=float)
        predictions.append(float(np.dot(weights, yi) / weights.sum()))
    return np.array(predictions, dtype=float)


def predict_regimes(df: pd.DataFrame) -> dict[str, np.ndarray]:
    held_mas = sorted(df.loc[df["is_aact"] == 1, "ma"].unique())

    y_all = []
    within_all = []
    pred_a_all = []
    pred_b_all = []
    glp1_a = None
    glp1_b = None
    glp1_y = None

    for ma in held_mas:
        test = df[(df["ma"] == ma) & (df["split_role"] == "test")].copy()
        if test.empty:
            raise ValueError(f"held-out MA has no test rows: {ma}")

        train_a = df[df["ma"] != ma].copy()
        if ((train_a["ma"] == ma) & (train_a["split_role"].isin(["donor", "test"]))).any():
            raise AssertionError("regime A leaked rows from the held-out MA")
        pred_a = local_kernel_predict(train_a, test)

        train_b = df[~((df["ma"] == ma) & (df["split_role"] == "test"))].copy()
        donor_mask = (train_b["ma"] == ma) & (train_b["split_role"] == "donor")
        train_b.loc[donor_mask, "ma"] = f"{ma}__sib"
        if ((train_b["ma"] == ma) & (train_b["split_role"] == "test")).any():
            raise AssertionError("regime B leaked held-out test rows")
        if ((train_b["ma"] == ma) & (train_b["split_role"] == "donor")).any():
            raise AssertionError("regime B failed to relabel donor rows")
        pred_b = local_kernel_predict(train_b, test)

        y = test["yi"].to_numpy(dtype=float)
        within = within_ma_baseline(df, test)

        y_all.append(y)
        within_all.append(within)
        pred_a_all.append(pred_a)
        pred_b_all.append(pred_b)

        if ma == TARGET_MA:
            glp1_a = pred_a
            glp1_b = pred_b
            glp1_y = y

    if glp1_a is None or glp1_b is None or glp1_y is None:
        raise ValueError(f"target MA not found: {TARGET_MA}")

    return {
        "y": np.concatenate(y_all),
        "within": np.concatenate(within_all),
        "pred_a": np.concatenate(pred_a_all),
        "pred_b": np.concatenate(pred_b_all),
        "glp1_y": glp1_y,
        "glp1_a": glp1_a,
        "glp1_b": glp1_b,
    }


def mae(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.mean(np.abs(a - b)))


def main() -> None:
    df = load_data()
    preds = predict_regimes(df)

    within_mae = mae(preds["within"], preds["y"])
    a_delta = mae(preds["pred_a"], preds["y"]) - within_mae
    b_delta = mae(preds["pred_b"], preds["y"]) - within_mae
    glp1_true = float(np.mean(preds["glp1_y"]))
    glp1_a_post = float(np.mean(preds["glp1_a"]))
    glp1_b_post = float(np.mean(preds["glp1_b"]))

    donor_mean = float(
        df[(df["ma"] == TARGET_MA) & (df["split_role"] == "donor")]["yi"].mean()
    )
    verdict = (
        "No: adding the relabeled GLP1 donor "
        f"(mean {donor_mean:.2f}) shifts the GLP1 test mean prediction "
        f"from {glp1_a_post:.2f} to {glp1_b_post:.2f}, still far below "
        f"the true {glp1_true:.2f}, so specialty/year/precision proximity only partially routes the donor level."
    )

    out = {
        "A_delta": a_delta,
        "B_delta": b_delta,
        "glp1_true": glp1_true,
        "glp1_A_post": glp1_a_post,
        "glp1_B_post": glp1_b_post,
        "verdict": verdict,
    }
    text = json.dumps(out, indent=2)
    OUT_PATH.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
