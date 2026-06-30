import numpy as np
import pandas as pd
import json
import os

def main():
    cells = [
        "t05_strong_n6",
        "t10_moderate_n12",
        "t10_none_n8",
        "t10_strong_n10",
        "t10_strong_n5",
        "t10_strong_n6",
        "t20_strong_n8",
        "t30_strong_n12"
    ]

    results = {"cells": {}, "verifier": "agy"}

    for cell in cells:
        file_path = f"gridcell_{cell}_perrep.csv"
        if not os.path.exists(file_path):
            continue

        df = pd.read_csv(file_path)
        df['error'] = np.abs(df['d_hat'] - df['d_true'])

        # Calculate point estimate metrics
        mciw0_points = {}
        for method in ['common_DL', 'adaptshrink_auto']:
            m_df = df[df['method'] == method]
            contrasts = m_df['contrast'].unique()
            c_mciw0 = []
            for c in contrasts:
                e = m_df[m_df['contrast'] == c]
                calib_e = e[e['rep'] % 2 == 0]['error'].dropna()
                if len(calib_e) > 0:
                    c_half = np.quantile(calib_e, 0.95)
                    c_mciw0.append(2 * c_half)
            mciw0_points[method] = np.mean(c_mciw0) if c_mciw0 else np.nan

        mciw0_method = mciw0_points['adaptshrink_auto']
        mciw0_baseline = mciw0_points['common_DL']
        dMCIW0 = mciw0_method - mciw0_baseline

        # Paired-Bootstrap robust-win
        m_err = df[df['method'] == 'adaptshrink_auto'].pivot(index='rep', columns='contrast', values='error')
        b_err = df[df['method'] == 'common_DL'].pivot(index='rep', columns='contrast', values='error')

        valid_reps_m = m_err.dropna().index
        valid_reps_b = b_err.dropna().index
        valid_reps = valid_reps_m.intersection(valid_reps_b)

        n_paired_reps = len(valid_reps)

        if n_paired_reps > 0:
            m_err_mat = m_err.loc[valid_reps].values
            b_err_mat = b_err.loc[valid_reps].values

            R = n_paired_reps
            B = 2000
            rng = np.random.default_rng(7)
            idx = rng.integers(0, R, size=(B, R))

            m_samples = m_err_mat[idx]
            b_samples = b_err_mat[idx]

            m_q = np.quantile(m_samples, 0.95, axis=1)
            b_q = np.quantile(b_samples, 0.95, axis=1)

            m_mciw_bs = 2 * np.mean(m_q, axis=1)
            b_mciw_bs = 2 * np.mean(b_q, axis=1)

            d0 = m_mciw_bs - b_mciw_bs

            ci_low = np.percentile(d0, 2.5)
            ci_high = np.percentile(d0, 97.5)
            robust_win = bool(ci_high < 0)
        else:
            ci_low, ci_high, robust_win = np.nan, np.nan, False

        results["cells"][cell] = {
            "n_paired_reps": int(n_paired_reps),
            "mciw0_method": float(mciw0_method),
            "mciw0_baseline": float(mciw0_baseline),
            "dMCIW0": float(dMCIW0),
            "ci_low": float(ci_low),
            "ci_high": float(ci_high),
            "robust_win": robust_win
        }

        print(f"{cell}: dMCIW0={dMCIW0:.5f}, CI=[{ci_low:.5f}, {ci_high:.5f}], robust_win={robust_win}")

    output_path = "F:/ubcma/nma/verify/result_agy_grid.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
