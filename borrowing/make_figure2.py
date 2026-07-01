"""Pilot-2 figure: (A) real GLP1 dose-response (modifier exists), (B) real LOO
MAE relevance vs nulls, (C) sim slope-sweep dMCIW0 (inert at beta=0, win at real
beta), (D) confident-wrong harm: AdaptShrink vs precision fusion."""
import json, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from borrowing_field2 import covariate_prior, borrow_estimate2, own_estimate

T = [t for t in json.load(open("probe_trials.json"))
     if t["active"] == "GLP1" and t.get("dose") is not None]
x = np.array([t["dose"] for t in T]); y = np.array([t["y"] for t in T]); s = np.array([t["se"] for t in T])
S = json.load(open("real_glp1_summary.json"))
rows = json.load(open("sim_gate_results.json"))

fig, ax = plt.subplots(2, 2, figsize=(11, 8))

# (A) dose-response
a = ax[0, 0]
a.errorbar(x, y, yerr=1.96 * s, fmt="o", ms=5, capsize=2, color="#1f77b4", alpha=.8)
xx = np.linspace(x.min(), x.max(), 50)
a.plot(xx, S["intercept"] + S["slope"] * xx, "-", color="#d62728", lw=2,
       label=f"slope={S['slope']:+.3f}/mg\n95%CI[{S['slope_ci'][0]:+.3f},{S['slope_ci'][1]:+.3f}]\nperm p={S['perm_p']:.3f}, R2={S['R2']:.2f}")
a.set_xlabel("GLP1 dose (mg)"); a.set_ylabel("HbA1c effect vs placebo (%)")
a.set_title("(A) REAL modifier exists: dose predicts effect\n(the signal pilot-1 lacked)")
a.legend(fontsize=8, loc="lower left"); a.grid(alpha=.3)

# (B) real LOO MAE
b = ax[0, 1]
bw = float(np.std(x))
def loo(mode, seed=1):
    rng = np.random.default_rng(seed); e = []
    for i in range(len(T)):
        m = np.ones(len(T), bool); m[i] = False
        mu_p, _, _ = covariate_prior(x[i], x[m], y[m], s[m], bw, mode=mode, rng=rng)
        e.append(abs(mu_p - y[i]))
    return np.mean(e)
maes = [loo("relevance"), loo("uniform"), loo("scrambled")]
cols = ["#2ca02c", "#7f7f7f", "#bcbd22"]
b.bar(["relevance\n(gravity)", "uniform\n(shrink-mean null)", "scrambled\n(null)"], maes, color=cols)
for i, v in enumerate(maes): b.text(i, v + .01, f"{v:.3f}", ha="center", fontsize=9)
b.set_ylabel("LOO mean abs error vs REAL held-out effect")
b.set_title("(B) REAL held-out test: relevance beats both nulls\n(robust, paired bootstrap CI<0)")
b.grid(alpha=.3, axis="y")

# (C) slope sweep, sparse off-center (avg of low+high) dMCIW0 rel vs uniform/scrambled
c = ax[1, 0]
slopes = ["flat(0)", "half", "real", "steep"]
betas = [next(r["beta"] for r in rows if r["slope"] == sl) for sl in slopes]
def avg_d(sl, key):
    vs = [r[key]["d"] for r in rows if r["slope"] == sl and r["pos"] in ("low", "high") and r["regime"] == "sparse"]
    return np.mean(vs)
du = [avg_d(sl, "rel_vs_uniform") for sl in slopes]
ds = [avg_d(sl, "rel_vs_scrambled") for sl in slopes]
c.plot(betas, du, "o-", color="#2ca02c", label="relevance - uniform")
c.plot(betas, ds, "s--", color="#bcbd22", label="relevance - scrambled")
c.axhline(0, color="k", lw=.8)
c.set_xlabel("DGP slope beta (effect per mg)"); c.set_ylabel("dMCIW0 (negative = relevance better)")
c.set_title("(C) Sim boundary map (sparse, off-centre): inert at beta=0\n(pilot-1), wins as covariate signal grows")
c.legend(fontsize=8); c.grid(alpha=.3)
c.annotate("real beta", (S["slope"], 0), xytext=(S["slope"], max(du) * .5),
           fontsize=8, ha="center", arrowprops=dict(arrowstyle="->"))

# (D) confident-wrong harm: AdaptShrink vs precision (rich regime)
d = ax[1, 1]
MU_T, M_F = -1.17, -0.55; N_SRC = 16
def cw_harm(fusion, reps=1200, seed=5):
    rng = np.random.default_rng(seed); eb, eo = [], []
    for _ in range(reps):
        ses = np.full(N_SRC, .10); ys = M_F + rng.normal(0, .30, N_SRC) + rng.normal(0, ses)
        xs = rng.uniform(0, 1, N_SRC)
        ose = rng.choice([.05, .06, .07, .08, .10, .13], 8); oy = MU_T + rng.normal(0, .05, 8) + rng.normal(0, ose)
        mu0, _ = own_estimate(oy, ose)
        bb = borrow_estimate2(oy, ose, .5, xs, ys, ses, 1e9, mode="uniform", rng=rng, fusion=fusion)
        eb.append(abs(bb["mu"] - MU_T)); eo.append(abs(mu0 - MU_T))
    eb = np.array(eb); eo = np.array(eo)
    half = lambda e: 2 * np.quantile(np.abs(e), .95)
    return half(eb) - half(eo)
harms = [cw_harm("adaptshrink"), cw_harm("precision")]
d.bar(["AdaptShrink\n(pilot-1)", "precision fusion\n(pilot-2)"], harms, color=["#d62728", "#2ca02c"])
for i, v in enumerate(harms): d.text(i, v + .003, f"{v:+.3f}", ha="center", fontsize=9)
d.axhline(0, color="k", lw=.8)
d.set_ylabel("dMCIW0 vs own (rich) -- positive = HARM")
d.set_title("(D) Confident-wrong prior (rich): fusion fix\nremoves the pilot-1 harm")
d.grid(alpha=.3, axis="y")

plt.tight_layout()
plt.savefig("fig_borrowing_pilot2.png", dpi=130)
print("wrote fig_borrowing_pilot2.png")
print(f"  (B) LOO MAE relevance/uniform/scrambled = {maes[0]:.3f}/{maes[1]:.3f}/{maes[2]:.3f}")
print(f"  (D) confident-wrong harm adaptshrink/precision = {harms[0]:+.3f}/{harms[1]:+.3f}")
