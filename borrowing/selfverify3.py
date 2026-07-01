"""PILOT-3 independent re-derivation (NO shared functions with borrowing_transport).
Re-implements, from scratch, the two headline claims on the REAL slice:
  (1) relevance-only borrowing beats standard pooling (NMA);
  (2) adding the obesity transportability multiplicand does NOT beat relevance-only.
Different code path: explicit loops, a different (Epanechnikov) transport kernel,
hand-rolled standardisation and a hand-rolled jackknife CI. If the sign/decision
matches run_pilot3.py the headline is robust to implementation choices.
"""
import json
import numpy as np

R = [r for r in json.load(open("trials_transport.json")) if r["pop_ob"] is not None]
ob_all = [r["pop_ob"] for r in R]
ob_sd = (sum((o - sum(ob_all) / len(ob_all)) ** 2 for o in ob_all) / len(ob_all)) ** 0.5
GAMMA = 0.25


def class_obslope(donors):
    """independent: per-class demeaned LS slope, pooled by inverse-variance count."""
    num = den = 0.0
    for c in set(d["active"] for d in donors):
        sub = [d for d in donors if d["active"] == c]
        if len(sub) < 3:
            continue
        ob = np.array([d["pop_ob"] for d in sub]); y = np.array([d["y"] for d in sub])
        ob -= ob.mean(); y -= y.mean()
        if (ob ** 2).sum() > 1e-9:
            num += (ob * y).sum(); den += (ob ** 2).sum()
    return num / den if den > 1e-9 else 0.0


def prior(target, donors, mode, beta):
    ws, vals = [], []
    for d in donors:
        rel = 1.0 if d["active"] == target["active"] else GAMMA
        if target["baseline"] is not None and d["baseline"] is not None:
            rel *= np.exp(-((d["baseline"] - target["baseline"]) ** 2) / (2 * 0.27 ** 2))
        prec = 1.0 / d["se"] ** 2
        if mode == "nma":
            w = prec; v = d["y"]
        elif mode == "relevance":
            w = rel * prec; v = d["y"]
        else:  # transport: Epanechnikov kernel on obesity + standardise
            u = (d["pop_ob"] - target["pop_ob"]) / (2.0 * ob_sd)
            kern = max(0.0, 1 - u * u)
            w = rel * kern * prec
            v = d["y"] + beta * (target["pop_ob"] - d["pop_ob"])
        ws.append(w); vals.append(v)
    ws = np.array(ws); vals = np.array(vals)
    if ws.sum() <= 0:
        return np.nan
    return (ws * vals).sum() / ws.sum()


targets = [r for r in R if r["single_country"]]
e_nma, e_rel, e_trn = [], [], []
for t in targets:
    donors = [d for d in R if d["nct_id"] != t["nct_id"]]
    beta = class_obslope(donors)
    e_nma.append(abs(prior(t, donors, "nma", 0) - t["y"]))
    e_rel.append(abs(prior(t, donors, "relevance", 0) - t["y"]))
    e_trn.append(abs(prior(t, donors, "transport", beta) - t["y"]))
e_nma, e_rel, e_trn = map(np.array, (e_nma, e_rel, e_trn))


def jackknife(d):
    """independent CI: delete-one jackknife mean +/- 1.96*se (different from bootstrap)."""
    n = len(d); m = d.mean()
    loo = np.array([np.delete(d, i).mean() for i in range(n)])
    se = np.sqrt((n - 1) / n * ((loo - loo.mean()) ** 2).sum())
    return m, m - 1.96 * se, m + 1.96 * se


print(f"independent re-derivation (Epanechnikov kernel, jackknife CI); n={len(targets)}")
print(f"  MAE  nma={e_nma.mean():.3f}  relevance={e_rel.mean():.3f}  transport={e_trn.mean():.3f}")
for name, diff in [("relevance - nma   ", e_rel - e_nma),
                   ("transport - relevance", e_trn - e_rel)]:
    m, lo, hi = jackknife(diff)
    verdict = "WIN" if hi < 0 else ("worse" if lo > 0 else "n.s.")
    print(f"  {name} = {m:+.3f} [{lo:+.3f},{hi:+.3f}]  {verdict}")
print("MATCH expected: relevance beats nma (WIN); transport does NOT beat relevance (n.s.)")
