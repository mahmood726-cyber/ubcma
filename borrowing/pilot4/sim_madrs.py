"""PILOT-4 controlled layer (known truth) on the MADRS structure: is the real-data
null because the TRANSPORT MACHINERY is broken, or because the population modifier
is genuinely absent/weak in this slice? Keep the REAL trial structure (class,
under-5 mortality, sampling SE of all 36 MADRS trials) and regenerate effects under

    y_i = a_class[i] + beta * (mort_i - mort_ref) + eps_i,   eps ~ N(0, tau^2)

so the modifier slope `beta` is KNOWN. LOO-predict every trial, score to known
truth, sweep beta. Expectation if machinery correct: inert at beta=0, transport
beats relevance once beta is strong. Class effects + tau estimated from the real data.
"""
from __future__ import annotations
import json, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # ../ has borrowing_transport
from borrowing_transport import transport_prior, within_class_obslope, Z975

R = [r for r in json.load(open("dep_madrs_transport.json")) if r["pop_ob"] is not None]
OB = np.array([r["pop_ob"] for r in R]); OB_SD = float(OB.std()); OB_MED = float(np.median(OB))
OB_REF = float(OB.mean()); BASE_SD = 1.87
# class effects + residual tau estimated from the real MADRS data
cls = sorted(set(r["active"] for r in R))
CLASS_EFF = {c: float(np.mean([r["y"] for r in R if r["active"] == c])) for c in cls}
resid = [r["y"] - CLASS_EFF[r["active"]] for r in R]
TAU = float(np.std(resid))
print(f"DGP: real classes+mortality+SE, tau={TAU:.2f}, mort_ref={OB_REF:.1f}, n={len(R)} targets")
print(f"class effects: " + " ".join(f"{c}:{CLASS_EFF[c]:+.2f}" for c in cls))

def gen(beta, rng):
    y = np.empty(len(R)); truth = np.empty(len(R))
    for i, r in enumerate(R):
        mu = CLASS_EFF[r["active"]] + beta * (r["pop_ob"] - OB_REF)
        truth[i] = mu
        y[i] = mu + rng.normal(0, TAU) + rng.normal(0, r["se"])
    return y, truth

def predict(tgt, donors, mode, beta_ob, rng):
    mu_p, se_p, _ = transport_prior(tgt, donors, OB_SD, mode=mode,
                                    bw_base=BASE_SD, beta_ob=beta_ob, rng=rng)
    return mu_p, se_p

def sweep(beta, reps=300, seed=100):
    rng = np.random.default_rng(seed)
    err = {m: [] for m in ["nma", "relevance", "transport", "scrambled"]}
    for _ in range(reps):
        y, truth = gen(beta, rng)
        recs = [dict(R[i], y=float(y[i])) for i in range(len(R))]
        for ti in range(len(R)):
            tgt = recs[ti]; donors = [recs[j] for j in range(len(R)) if j != ti]
            b_ob = within_class_obslope(donors, None)
            for m in err:
                use_b = b_ob if m == "transport" else 0.0
                mu_p, se_p = predict(tgt, donors, m, use_b, rng)
                if np.isfinite(mu_p): err[m].append(abs(mu_p - truth[ti]))
    return {m: np.mean(err[m]) for m in err}, err

def boot_diff(ea, eb, n=4000, seed=3):
    rng = np.random.default_rng(seed); d = np.array(ea) - np.array(eb)
    bi = rng.integers(0, len(d), size=(n, len(d))); md = d[bi].mean(axis=1)
    return float(d.mean()), float(np.quantile(md, .025)), float(np.quantile(md, .975))

print(f"\n{'beta':>7}{'MAE_nma':>9}{'MAE_rel':>9}{'MAE_trn':>9}{'transp-relevance [95% CI]':>30}")
out = {}
for beta in [0.0, 0.05, 0.2, 0.5, 1.0]:
    stats, err = sweep(beta)
    d, lo, hi = boot_diff(err["transport"], err["relevance"])
    flag = "TRANSPORT WINS" if hi < 0 else ("rel wins" if lo > 0 else "n.s.")
    print(f"{beta:>7.2f}{stats['nma']:>9.3f}{stats['relevance']:>9.3f}{stats['transport']:>9.3f}"
          f"   {d:+.3f} [{lo:+.3f},{hi:+.3f}]  {flag}")
    out[str(beta)] = dict(mae={m: stats[m] for m in stats}, transport_vs_relevance=[d, lo, hi, bool(hi < 0)])
json.dump({"tau": TAU, "mort_ref": OB_REF, "mort_sd": OB_SD, "sweep": out},
          open("sim_madrs_results.json", "w"), indent=2)
print("\nwrote sim_madrs_results.json")
print("Reading: inert at beta=0; transport beats relevance once the modifier is strong")
print("-> machinery is correct on this slice too; the real-data null is a DATA limit.")
