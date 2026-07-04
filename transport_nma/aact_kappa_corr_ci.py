"""Inference for the PRIMARY external-validation number: is diabetes corr(kappa_MD, 1-lambda)=+0.50
(7 classes) significantly positive, or noise on 7 points? Adds a permutation test (permute the 1-lambda
labels across classes) and a class-level bootstrap CI. Reuses the committed per-analysis records; no re-query.
"""
import csv, json, io, sys
import numpy as np
from pathlib import Path
from collections import defaultdict
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LAM = json.load(open(ROOT / "borrowing" / "class_lambda.json"))
rows = list(csv.DictReader(open(HERE / "aact_hba1c_records.csv")))
per = defaultdict(lambda: {'1': [], '0': []})
for r in rows:
    per[r['drug_class']][r['published']].append(float(r['abs_md_pct']))

X, Y = [], []          # (1-lambda), kappa_MD  over adequately-powered classes
labels = []
for c, d in per.items():
    p, q = np.array(d['1']), np.array(d['0'])
    if len(p) >= 8 and len(q) >= 8 and c in LAM:
        X.append(1 - LAM[c]); Y.append(p.mean() / q.mean() - 1.0); labels.append(c)
X, Y = np.array(X), np.array(Y)
n = len(X)
corr = float(np.corrcoef(X, Y)[0, 1])

rng = np.random.default_rng(20260704)
# permutation test: permute (1-lambda) labels across classes; H0 = no association
NPERM = 20000
perm = np.array([np.corrcoef(rng.permutation(X), Y)[0, 1] for _ in range(NPERM)])
p_perm = float((np.sum(perm >= corr) + 1) / (NPERM + 1))     # one-sided (positive association)
# class-level bootstrap CI on corr
NB = 20000
bs = []
for _ in range(NB):
    idx = rng.integers(0, n, n)
    if len(set(idx.tolist())) < 2:
        continue
    cc = np.corrcoef(X[idx], Y[idx])[0, 1]
    if np.isfinite(cc):
        bs.append(cc)
bs = np.array(bs)
lo, hi = float(np.quantile(bs, .025)), float(np.quantile(bs, .975))
frac_pos = float(np.mean(bs > 0))

print("=" * 72)
print("Inference for diabetes corr(kappa_MD, 1-lambda) -- the primary external-validation number")
print("=" * 72)
print(f"  classes (n={n}): {labels}")
print(f"  observed corr           = {corr:+.3f}")
print(f"  permutation p (1-sided) = {p_perm:.4f}   (H0: no association; {NPERM} perms)")
print(f"  bootstrap 95% CI        = [{lo:+.3f}, {hi:+.3f}]   (fraction > 0: {frac_pos:.3f})")
verdict = ("SIGNIFICANT positive association (perm-p < 0.05)" if p_perm < 0.05
           else "suggestive but not significant at n=7 (perm-p >= 0.05)")
print(f"  VERDICT: {verdict}")
json.dump(dict(n_classes=n, corr=corr, perm_p=p_perm, boot_ci=[lo, hi], frac_pos=frac_pos,
               labels=labels), open(HERE / "aact_kappa_corr_ci_result.json", "w"), indent=1)
print("wrote aact_kappa_corr_ci_result.json")
