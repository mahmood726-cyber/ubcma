import json
import numpy as np
from scipy.special import expit, logit
from scipy.optimize import minimize

def run_test():
    with open("truth-recovery-dta/reference_fits.json") as f:
        ref = json.load(f)

    for name, data in ref.items():
        print(f"\nDataset: {name}")
        counts = data["counts"]
        TP = np.array(counts["TP"], dtype=float)
        FP = np.array(counts["FP"], dtype=float)
        FN = np.array(counts["FN"], dtype=float)
        TN = np.array(counts["TN"], dtype=float)

        # Continuity correction
        any_zero = np.any(TP == 0) or np.any(FP == 0) or np.any(FN == 0) or np.any(TN == 0)
        if any_zero:
            TP += 0.5
            FP += 0.5
            FN += 0.5
            TN += 0.5

        # Se, Sp, y, S
        se = TP / (TP + FN)
        sp = TN / (TN + FP)
        y1 = logit(se)
        y2 = logit(sp)
        s1_sq = 1.0 / TP + 1.0 / FN
        s2_sq = 1.0 / TN + 1.0 / FP

        y = np.column_stack([y1, y2])
        S = [np.diag([s1_sq[i], s2_sq[i]]) for i in range(len(TP))]

        def nll(params):
            tau1, tau2, rho = params
            Sigma = np.array([[tau1**2, rho * tau1 * tau2],
                              [rho * tau1 * tau2, tau2**2]])
            k = len(y)
            sum_inv_V = np.zeros((2, 2))
            sum_inv_V_y = np.zeros(2)
            inv_Vs = []
            for i in range(k):
                V_i = Sigma + S[i]
                try:
                    inv_V_i = np.linalg.inv(V_i)
                except np.linalg.LinAlgError:
                    return 1e10
                inv_Vs.append(inv_V_i)
                sum_inv_V += inv_V_i
                sum_inv_V_y += inv_V_i @ y[i]
            
            try:
                M = np.linalg.solve(sum_inv_V, sum_inv_V_y)
            except np.linalg.LinAlgError:
                return 1e10
            
            val = 0.0
            for i in range(k):
                V_i = Sigma + S[i]
                diff = y[i] - M
                sign, logdet = np.linalg.slogdet(V_i)
                if sign <= 0:
                    return 1e10
                val += logdet + diff @ inv_Vs[i] @ diff
            return 0.5 * val

        # Try multiple starting points to avoid local minima
        best_fun = 1e10
        best_res = None
        
        # Grid search for initial values
        for init_tau1 in [0.1, 0.5, 1.0]:
            for init_tau2 in [0.1, 0.5, 1.0]:
                for init_rho in [-0.5, 0.0, 0.5]:
                    init_params = [init_tau1, init_tau2, init_rho]
                    res = minimize(
                        nll,
                        init_params,
                        bounds=[(0, None), (0, None), (-1.0 + 1e-9, 1.0 - 1e-9)],
                        method='L-BFGS-B'
                    )
                    if res.success and res.fun < best_fun:
                        best_fun = res.fun
                        best_res = res
        
        # Fit with best parameters
        if best_res is not None:
            tau1, tau2, rho = best_res.x
            Sigma = np.array([[tau1**2, rho * tau1 * tau2],
                              [rho * tau1 * tau2, tau2**2]])
            k = len(y)
            sum_inv_V = np.zeros((2, 2))
            sum_inv_V_y = np.zeros(2)
            for i in range(k):
                V_i = Sigma + S[i]
                inv_V_i = np.linalg.inv(V_i)
                sum_inv_V += inv_V_i
                sum_inv_V_y += inv_V_i @ y[i]
            M = np.linalg.solve(sum_inv_V, sum_inv_V_y)
            
            m1, m2 = M
            sens = expit(m1)
            spec = expit(m2)
            
            print(f"  Optimized: M1={m1:.10f}, M2={m2:.10f}, sens={sens:.10f}, spec={spec:.10f}")
            print(f"  Reference: M1={data['m1_logit_sens']:.10f}, M2={data['m2_logit_spec']:.10f}, sens={data['sens_summary']:.10f}, spec={data['spec_summary']:.10f}")
            diff_m1 = abs(m1 - data['m1_logit_sens'])
            diff_m2 = abs(m2 - data['m2_logit_spec'])
            diff_sens = abs(sens - data['sens_summary'])
            diff_spec = abs(spec - data['spec_summary'])
            print(f"  Absolute diffs: M1: {diff_m1:.2e}, M2: {diff_m2:.2e}, sens: {diff_sens:.2e}, spec: {diff_spec:.2e}")
            print(f"  Worst diff: {max(diff_m1, diff_m2, diff_sens, diff_spec):.2e}")

if __name__ == "__main__":
    run_test()
