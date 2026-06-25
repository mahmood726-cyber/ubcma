#!/usr/bin/env python3
"""
Run agy (Antigravity/Gemini) to independently re-implement the HSROC GLMM.
"""
import sys, json, pathlib, re, subprocess

DRIVER = pathlib.Path.home() / "agy-driver" / "agy_driver.py"
REPO_ROOT = pathlib.Path("F:/ubcma-dta")
HARNESS_DIR = REPO_ROOT / "truth-recovery-dta"
OUTPUT_PY = HARNESS_DIR / "verify_hsroc_agy.py"

PROMPT = r"""You are an INDEPENDENT re-implementer. Do NOT read or import src/ubcma/dta.py. Implement the HSROC estimator yourself from this math spec using only numpy/scipy.

BACKGROUND: Rutter-Gatsonis HSROC = bivariate binomial-normal GLMM fit by exact binomial likelihood.

MATH SPEC:
Per study i: diseased arm n1=TP+FN, non-diseased n0=TN+FP.
Continuity correction (mada-style): if ANY study in the dataset has a zero cell, add 0.5 to EVERY cell of EVERY study in that dataset.
Random effects per study (b1_i, b2_i) ~ N(0, Sigma) where Sigma = [[t1^2, rho*t1*t2],[rho*t1*t2, t2^2]].
Conditional: logit(Se_i) = mu1 + b1_i,  logit(Sp_i) = mu2 + b2_i.
TP_i ~ Binomial(n1_i, Se_i),  TN_i ~ Binomial(n0_i, Sp_i).
Marginal log-likelihood: L_i = integral over (b1,b2) of Bin(TP_i;n1_i,expit(mu1+b1)) * Bin(TN_i;n0_i,expit(mu2+b2)) * N2((b1,b2);0,Sigma) db1 db2.
Maximize sum_i log L_i over (mu1, mu2, t1, t2, rho). Summary: Se = expit(mu1), Sp = expit(mu2).
Integration method: use a product Gauss-Hermite grid with >=60 nodes per dim (±6 SD range is safe). This is independent from any other implementation.

INPUT FILES (all in F:\ubcma-dta\truth-recovery-dta\):
- reference_fits.json: raw 2x2 counts under dataset name -> "counts" -> {"TP":[...], "FP":[...], "FN":[...], "TN":[...]}
- reference_glmm.json: glmer reference fits, dataset name -> {"ok":bool, "sens_summary":..., "spec_summary":..., "m1_logit_sens":..., "m2_logit_spec":..., "tau_sens":..., "tau_spec":..., "rho":...}

WHAT TO DO:
1. For each dataset in reference_glmm.json with ok=true, load raw counts from reference_fits.json.
2. Apply mada-style continuity correction.
3. Fit your HSROC estimator; record (sens_summary, spec_summary, mu1, mu2, t1, t2, rho).
4. Compute abs difference vs glmer reference for sens_summary and spec_summary.
5. Deviance check: evaluate your exact NLL at (a) your MLE and (b) glmer's reported params. Report mine_le_glmer = (your NLL <= glmer params NLL).
6. Write results to F:\ubcma-dta\truth-recovery-dta\verify_hsroc_agy_result.json with structure:
   {"per_dataset": {name: {"se":..., "sp":..., "mu1":..., "mu2":..., "t1":..., "t2":..., "rho":..., "dse_vs_glmer":..., "dsp_vs_glmer":..., "nll_mine":..., "nll_glmer_params":..., "mine_le_glmer":bool}}, "worst_se_sp_vs_glmer": float, "all_mine_le_glmer": bool, "seat_identifier": "agy"}

DELIVERABLE: Complete standalone Python script that runs from the directory F:\ubcma-dta with PYTHONPATH=src.
Output ONLY the Python code block (```python ... ```), nothing else."""

print(f"[run_agy_hsroc] calling agy driver, prompt length={len(PROMPT)}")
sys.stdout.flush()

result = subprocess.run(
    ["python", str(DRIVER), "--json", "--model", "pro", "--response-timeout", "300", PROMPT],
    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=360
)

print(f"[run_agy_hsroc] exit code: {result.returncode}")
if result.returncode != 0:
    print("[run_agy_hsroc] stderr:", result.stderr[:500])
    sys.exit(1)

try:
    data = json.loads(result.stdout)
    text = data.get("text", "")
except Exception:
    text = result.stdout

print(f"[run_agy_hsroc] response length: {len(text)} chars")
print("[run_agy_hsroc] first 300 chars:")
print(text[:300])

# Extract code
code_match = re.search(r"```python\s*(.*?)```", text, re.DOTALL)
if code_match:
    code = code_match.group(1)
    OUTPUT_PY.write_text(code, encoding="utf-8")
    print(f"[run_agy_hsroc] wrote {len(code)} chars to {OUTPUT_PY}")
else:
    print("[run_agy_hsroc] no python block found; saving raw")
    OUTPUT_PY.write_text(text, encoding="utf-8")

(HARNESS_DIR / "agy_hsroc_raw_response.txt").write_text(text, encoding="utf-8")
print("[run_agy_hsroc] done")
