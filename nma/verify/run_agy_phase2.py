#!/usr/bin/env python3
"""
Run agy (Antigravity/Gemini) to independently re-implement NMA Phase 2 (B+C).
Saves the code response and then attempts to run it.
"""
import sys, json, pathlib, re, subprocess

DRIVER = pathlib.Path.home() / "agy-driver" / "agy_driver.py"
REPO_ROOT = pathlib.Path("F:/ubcma")
VERIFY_DIR = REPO_ROOT / "nma" / "verify"
OUTPUT_PY = VERIFY_DIR / "agy_phase2_nma.py"
OUTPUT_RESULT = VERIFY_DIR / "agy_phase2_RESULT.md"

PROMPT = r"""You are independently re-deriving two pieces of new NMA methodology to cross-check another implementation. Do NOT read nma/smallstudy_nma.py, nma/inconsistency_nma.py, or nma/adaptshrink_nma.py. Implement the math yourself from this spec. You MAY read and reuse nma/nma_core.py (already verified to ~1e-11 vs R netmeta) for the GLS engine.

INPUTS (all relative to repo root F:\ubcma, run with PYTHONPATH=.):
- nma/reference/smoking_input.csv, nma/reference/senn2013_input.csv
  columns: studlab,treat1,treat2,TE,seTE. TE = effect(treat1) - effect(treat2). Multi-arm.
- nma/reference/{smoking,senn2013}_TE_random.csv, _seTE_random.csv  netmeta RE league
- nma/reference/{smoking,senn2013}_scalars.csv  columns include tau2, Q, df.Q
- nma/verify/decomp_reference.csv  netmeta decomp.design reference for Part C

PART B  network small-study meta-regression (PET/PEESE):
Reference treatment r = first alphabetically. Basic parameters d_t = effect(t)-effect(r).
Weight matrix W = block-precision matrix from the engine (DL tau^2 from scalars; multi-arm blocks via pinv of contrast covariance).
B_basic = m x (n-1) incidence matrix (reference column dropped).
Augmented: X = [B_basic | s] where s_i = se_i (PET) or s_i = se_i^2 (PEESE).
WLS: coef = (X^T W X)^{+} X^T W y. First n-1 = bias-adjusted basic params d; last = slope beta, Var(beta) = [(X^T W X)^{+}]_{last,last}.

Checks for BOTH networks:
B1. No covariate (X=B_basic): reproduce netmeta RE league to < 1e-8.
B2. PET slope: beta, z=beta/sqrt(Var(beta)), two-sided p-value.
B3. PEESE-adjusted league entries d_t - d_r for all non-reference treatments.

PART C  design-by-treatment Q decomposition at tau^2=0 (common-effect weights):
Design = the set of treatments compared in a study. Group studies by their design.
Q_total = generalized Cochran Q of the consistency fit at common-effect weights.
df_total = (sum_studies (arms-1)) - (n-1).
Q_het = sum over designs of within-design Q (each design's studies pooled by themselves).
df_het = sum of within-design df.
Q_inc = Q_total - Q_het,  df_inc = df_total - df_het.

Check: Q_total, Q_het, Q_inc and df must match nma/verify/decomp_reference.csv to < 1e-6; df exact.

DELIVERABLE: Write a complete standalone Python script. Requirements:
- No ubcma imports; numpy/scipy only; may import from nma.nma_core
- Runs from F:\ubcma with PYTHONPATH=.
- Prints clearly labelled check results for B1, B2, B3, C for both networks
- At the end prints a summary: "PASS" if B1 max_diff < 1e-8 and C max_diff < 1e-6, else "FAIL"
Output ONLY the Python code block (```python ... ```), nothing else."""

print(f"[run_agy_phase2] calling agy driver with model=pro, prompt length={len(PROMPT)}")
sys.stdout.flush()

result = subprocess.run(
    ["python", str(DRIVER), "--json", "--model", "pro", "--response-timeout", "300", PROMPT],
    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=360
)

print(f"[run_agy_phase2] exit code: {result.returncode}")
if result.returncode != 0:
    print("[run_agy_phase2] stderr:", result.stderr[:500])
    sys.exit(1)

# Parse JSON response
try:
    data = json.loads(result.stdout)
    text = data.get("text", "")
except Exception:
    text = result.stdout

print(f"[run_agy_phase2] response length: {len(text)} chars")
print("[run_agy_phase2] first 300 chars of response:")
print(text[:300])

# Extract Python code block
code_match = re.search(r"```python\s*(.*?)```", text, re.DOTALL)
if not code_match:
    # Try without language specifier
    code_match = re.search(r"```\s*(import|#!/|from|#)\s*(.*?)```", text, re.DOTALL)
if code_match:
    code = code_match.group(1) if code_match.lastindex == 1 else code_match.group(0)
    # Strip the fences if present
    code = re.sub(r"^```python\s*", "", code)
    code = re.sub(r"```\s*$", "", code)
    OUTPUT_PY.write_text(code, encoding="utf-8")
    print(f"[run_agy_phase2] wrote {len(code)} chars to {OUTPUT_PY}")
else:
    print("[run_agy_phase2] no code block found in response; saving full text")
    OUTPUT_PY.write_text(text, encoding="utf-8")

# Save raw response
(VERIFY_DIR / "agy_phase2_raw_response.txt").write_text(text, encoding="utf-8")
print("[run_agy_phase2] done")
