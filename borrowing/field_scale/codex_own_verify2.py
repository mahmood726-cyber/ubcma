import numpy as np
import pandas as pd


CSV_PATH = "corpus_nodes.csv"
EXPECT_A = 0.272
EXPECT_B = {
    "own_only": 0.384,
    "power_prior": 0.351,
    "precision_fuse": 0.372,
}
TOL = 0.005
REPS = 25
SEED = 11


def require_columns(df, columns):
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError("missing required columns: " + ", ".join(missing))


def add_derived_columns(df):
    out = df.copy()
    for col in ["yi", "se", "year"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    if out[["ma", "family", "specialty", "yi", "se"]].isna().any().any():
        raise ValueError("ma/family/specialty/yi/se must be non-missing")
    if (out["se"] <= 0).any():
        raise ValueError("all se values must be positive")

    out["precision"] = 1.0 / (out["se"] ** 2)
    out["yz"] = np.nan
    for _, idx in out.groupby("family", sort=False).groups.items():
        years = out.loc[idx, "year"].to_numpy(dtype=float)
        mean = np.nanmean(years)
        sd = np.nanstd(years, ddof=0)
        if np.isfinite(sd) and sd > 0:
            out.loc[idx, "yz"] = (years - mean) / sd
    return out.reset_index(drop=True)


def dl_re_mean(y, se):
    w = 1.0 / (se ** 2)
    w_sum = w.sum()
    mu = (w * y).sum() / w_sum
    q = (w * ((y - mu) ** 2)).sum()
    c = w_sum - ((w ** 2).sum() / w_sum)
    tau2 = max(0.0, (q - (len(y) - 1)) / c) if c > 0 else 0.0
    wr = 1.0 / ((se ** 2) + tau2)
    return (wr * y).sum() / wr.sum()


def year_kernel(z1, z2):
    if np.isnan(z1) or np.isnan(z2):
        return 1.0
    return float(np.exp(-0.5 * ((z1 - z2) ** 2)))


def robust_map_mae(df):
    errors = []
    for i, row in df.iterrows():
        siblings = df[(df["ma"] == row["ma"]) & (df.index != i)]
        if len(siblings) < 1:
            continue
        pred = dl_re_mean(
            siblings["yi"].to_numpy(dtype=float),
            siblings["se"].to_numpy(dtype=float),
        )
        errors.append(abs(pred - row["yi"]))
    if not errors:
        raise ValueError("no targets with same-MA siblings for robust-MAP")
    return float(np.mean(errors))


def cross_ma_prior(df, target):
    donors = df[(df["family"] == target["family"]) & (df["ma"] != target["ma"])]
    if len(donors) < 1:
        return None

    same_specialty = donors["specialty"].to_numpy() == target["specialty"]
    topic = np.where(same_specialty, 0.50, 0.15)
    donor_yz = donors["yz"].to_numpy(dtype=float)
    target_yz = float(target["yz"])
    if np.isnan(target_yz):
        kernel = np.ones(len(donors))
    else:
        kernel = np.where(
            np.isnan(donor_yz),
            1.0,
            np.exp(-0.5 * ((donor_yz - target_yz) ** 2)),
        )
    weights = donors["precision"].to_numpy(dtype=float) * topic * kernel
    weight_sum = weights.sum()
    if weight_sum <= 0:
        return None
    mu_p = (weights * donors["yi"].to_numpy(dtype=float)).sum() / weight_sum
    se_p = 1.0 / np.sqrt(weight_sum)
    return float(mu_p), float(se_p)


def dynamic_borrowing_mae(df):
    rng = np.random.default_rng(SEED)
    errors = {"own_only": [], "power_prior": [], "precision_fuse": []}

    for i, target in df.iterrows():
        sibling_idx = df.index[(df["ma"] == target["ma"]) & (df.index != i)].to_numpy()
        if len(sibling_idx) < 1:
            continue
        prior = cross_ma_prior(df, target)
        if prior is None:
            continue
        mu_p, se_p = prior

        for _ in range(REPS):
            sibling = df.loc[sibling_idx[rng.integers(0, len(sibling_idx))]]
            y0 = float(sibling["yi"])
            k = year_kernel(float(sibling["yz"]), float(target["yz"]))
            se0 = 1.0 / np.sqrt(float(sibling["precision"]) * k)
            q = ((y0 - mu_p) ** 2) / ((se0 ** 2) + (se_p ** 2))

            a0 = np.clip(np.exp(-0.5 * q), 0.0, 1.0)
            power_mu = ((y0 / (se0 ** 2)) + (a0 * mu_p / (se_p ** 2))) / (
                (1.0 / (se0 ** 2)) + (a0 / (se_p ** 2))
            )

            delta = np.clip(1.0 - (q / 4.0), 0.0, 1.0)
            if delta <= 0:
                precision_mu = y0
            else:
                precision_mu = (
                    (y0 / (se0 ** 2)) + (delta * mu_p / (se_p ** 2))
                ) / ((1.0 / (se0 ** 2)) + (delta / (se_p ** 2)))

            yi = float(target["yi"])
            errors["own_only"].append(abs(y0 - yi))
            errors["power_prior"].append(abs(power_mu - yi))
            errors["precision_fuse"].append(abs(precision_mu - yi))

    if not errors["own_only"]:
        raise ValueError("no targets available for dynamic borrowing")
    return {name: float(np.mean(vals)) for name, vals in errors.items()}


def ok(value, expected):
    return abs(value - expected) <= TOL


def main():
    df = pd.read_csv(CSV_PATH)
    require_columns(df, ["ma", "family", "specialty", "yi", "se", "year"])
    df = add_derived_columns(df)

    mae_a = robust_map_mae(df)
    maes_b = dynamic_borrowing_mae(df)
    ordering = (
        maes_b["power_prior"] < maes_b["precision_fuse"] < maes_b["own_only"]
    )

    print(f"A robust-MAP MAE: {mae_a:.6f} (EXPECT {EXPECT_A:.3f}) match={ok(mae_a, EXPECT_A)}")
    print("B m=1 MAEs:")
    for name in ["own_only", "power_prior", "precision_fuse"]:
        value = maes_b[name]
        print(f"  {name}: {value:.6f} (EXPECT {EXPECT_B[name]:.3f}) match={ok(value, EXPECT_B[name])}")
    print(f"ordering power_prior < precision_fuse < own_only: {ordering}")


if __name__ == "__main__":
    main()
