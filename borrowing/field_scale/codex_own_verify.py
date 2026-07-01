import numpy as np
import pandas as pd


REQUIRED_COLUMNS = ["ma", "family", "specialty", "yi", "se", "year"]
EXPECT = {
    "within_minus_global": -0.045,
    "m1_within": 0.381,
    "m1_field": 0.341,
    "m1_delta": 0.041,
    "m2_delta": -0.007,
}
TOL = 0.005
C = 5.0
REPS = 25
SEED = 11


def match_text(value, expected):
    return "MATCH" if abs(value - expected) <= TOL else "NO MATCH"


df = pd.read_csv("corpus_nodes.csv")
missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
if missing:
    raise SystemExit("Missing required columns: " + ", ".join(missing))

df = df[REQUIRED_COLUMNS].copy()
for col in ["yi", "se", "year"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

if df["yi"].isna().any() or df["se"].isna().any():
    raise SystemExit("yi and se must be numeric and non-missing")
if (df["se"] <= 0).any():
    raise SystemExit("se must be positive")

df["precision"] = 1.0 / (df["se"] ** 2)
df["yz"] = np.nan
for family_name, group in df.groupby("family"):
    years = group["year"].dropna()
    sd = years.std(ddof=1)
    if len(years) > 1 and sd > 0:
        df.loc[group.index, "yz"] = (group["year"] - years.mean()) / sd

idx_all = np.arange(len(df))
ma = df["ma"].to_numpy()
family = df["family"].to_numpy()
specialty = df["specialty"].to_numpy()
yi = df["yi"].to_numpy(dtype=float)
precision = df["precision"].to_numpy(dtype=float)
yz = df["yz"].to_numpy(dtype=float)


def year_kernel(donor_idx, target_idx):
    donor_idx = np.asarray(donor_idx)
    kernels = np.ones(len(donor_idx), dtype=float)
    target_yz = yz[target_idx]
    if np.isnan(target_yz):
        return kernels
    donor_yz = yz[donor_idx]
    valid = ~np.isnan(donor_yz)
    kernels[valid] = np.exp(-0.5 * (donor_yz[valid] - target_yz) ** 2)
    return kernels


def weighted_mean(values, weights):
    return np.sum(values * weights) / np.sum(weights)


def within_vs_global_delta():
    deltas = []
    for i in idx_all:
        same_family_other = (family == family[i]) & (idx_all != i)
        same_ma_other = same_family_other & (ma == ma[i])
        if not np.any(same_ma_other):
            continue

        global_pred = weighted_mean(yi[same_family_other], precision[same_family_other])
        within_pred = weighted_mean(yi[same_ma_other], precision[same_ma_other])
        deltas.append(abs(within_pred - yi[i]) - abs(global_pred - yi[i]))

    return float(np.mean(deltas))


def sparse_result(m):
    rng = np.random.default_rng(SEED)
    stand = C / (C + m)
    within_err = []
    field_err = []

    for i in idx_all:
        siblings = idx_all[(family == family[i]) & (ma == ma[i]) & (idx_all != i)]
        if len(siblings) < m:
            continue

        cross = idx_all[(family == family[i]) & (ma != ma[i])]
        topic = np.where(specialty[cross] == specialty[i], 0.50, 0.15)
        cross_w = precision[cross] * topic * year_kernel(cross, i)
        cross_wy = np.sum(cross_w * yi[cross])
        cross_w_sum = np.sum(cross_w)

        for _ in range(REPS):
            picked = rng.choice(siblings, size=m, replace=False)
            home_w = precision[picked] * year_kernel(picked, i)
            home_wy = np.sum(home_w * yi[picked])
            home_w_sum = np.sum(home_w)

            within_pred = home_wy / home_w_sum
            field_pred = (home_wy + stand * cross_wy) / (home_w_sum + stand * cross_w_sum)
            within_err.append(abs(within_pred - yi[i]))
            field_err.append(abs(field_pred - yi[i]))

    within_mean = float(np.mean(within_err))
    field_mean = float(np.mean(field_err))
    return within_mean, field_mean, within_mean - field_mean


d1 = within_vs_global_delta()
m1_within, m1_field, d2 = sparse_result(1)
_, _, d3 = sparse_result(2)

print(
    f"(1) within_minus_global_delta = {d1:.6f} "
    f"(EXPECT {EXPECT['within_minus_global']:+.3f}) "
    f"{match_text(d1, EXPECT['within_minus_global'])}"
)
print(
    f"(2) m=1 within_mean = {m1_within:.6f} "
    f"(EXPECT {EXPECT['m1_within']:.3f}) "
    f"{match_text(m1_within, EXPECT['m1_within'])}"
)
print(
    f"(2) m=1 field_mean  = {m1_field:.6f} "
    f"(EXPECT {EXPECT['m1_field']:.3f}) "
    f"{match_text(m1_field, EXPECT['m1_field'])}"
)
print(
    f"(2) m=1 delta       = {d2:.6f} "
    f"(EXPECT {EXPECT['m1_delta']:+.3f}) "
    f"{match_text(d2, EXPECT['m1_delta'])}"
)
print(
    f"(3) m=2 delta       = {d3:.6f} "
    f"(EXPECT {EXPECT['m2_delta']:+.3f}) "
    f"{match_text(d3, EXPECT['m2_delta'])}"
)
