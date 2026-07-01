"""PILOT-2 decisive matched-coverage gate with CONTROLLED GROUND TRUTH.

The real LOO test (real_glp1.py) already shows relevance beats both nulls on real
held-out effects, but real effects are a NOISY truth and there are only n=12. To
run the program's matched-coverage MCIW0 + paired-bootstrap gate we need a known
truth. So we SIMULATE -- but the data-generating process is CALIBRATED TO THE REAL
GLP1 DOSE-RESPONSE measured in real_glp1.py (intercept, slope, residual tau, dose
distribution, and the real SE distribution). This is a method-validation vehicle
in the same spirit as the repo's truth-recovery sims; it is clearly labelled
simulation, and the headline real-data claim rests on real_glp1.py.

Estimand: the conditional mean effect at the target's dose, mu*(x_t)=alpha+beta*x_t.
DGP: source field of N trials with doses ~ real distribution; theta=alpha+beta*x+eps,
eps~N(0,tau^2); y~N(theta, se^2), se ~ real SE distribution. Target: k own trials
at x_t (sparse k=2 / rich k=8).

Four methods (paired within a replicate):
  own       : REML pool of own k trials only          (= NMA TE[spoke,placebo])
  relevance : own (+) dose-relevance prior + hardened stand-down + AdaptShrink
  uniform   : own (+) field-MEAN prior (no relevance)            -- null #1
  scrambled : own (+) relevance prior, doses permuted            -- null #2

SLOPE SWEEP beta in {0, real/2, real, 1.6*real}: at beta=0 the covariate carries
NO signal -> relevance must collapse to the nulls (reproducing pilot-1's inertia);
at real beta with an OFF-CENTRE target -> relevance must beat BOTH nulls.
TARGET POSITION in {low, center, high}: at center mu*(x_t)=field mean so the
uniform null is unbiased and relevance should only TIE; the win must come from
off-centre targets, where shrink-to-mean is biased.
"""
import json, numpy as np
from borrowing_field2 import borrow_estimate2, own_estimate, Z975

S = json.load(open("real_glp1_summary.json"))
ALPHA = S["intercept"]; BETA_REAL = S["slope"]; TAU = S["tau2_cond"] ** 0.5
DMIN, DMAX = S["dose_range"]; XSD = S["dose_sd"]
# real SE distribution (GLP1 dose trials) to draw realistic precisions from
REAL_SE = np.array([t["se"] for t in json.load(open("probe_trials.json"))
                    if t["active"] == "GLP1" and t.get("dose") is not None])
REAL_DOSE = np.array([t["dose"] for t in json.load(open("probe_trials.json"))
                      if t["active"] == "GLP1" and t.get("dose") is not None])
BW = round(XSD, 2)            # a-priori bandwidth (Silverman-ish on dose), fixed
N_SRC = 20                    # field size (sources to borrow from)
REPS = 500
POSITIONS = {"low": DMIN + 0.10 * (DMAX - DMIN),
             "center": float(np.mean(REAL_DOSE)),
             "high": DMIN + 0.90 * (DMAX - DMIN)}
REGIMES = {"sparse": 2, "rich": 8}
SLOPES = {"flat(0)": 0.0, "half": BETA_REAL / 2, "real": BETA_REAL,
          "steep": 1.6 * BETA_REAL}
METHODS = ["own", "relevance", "uniform", "scrambled"]


def gen_sources(rng, beta):
    xs = rng.choice(REAL_DOSE, size=N_SRC, replace=True) + rng.normal(0, 0.3, N_SRC)
    xs = np.clip(xs, DMIN, DMAX)
    se = rng.choice(REAL_SE, size=N_SRC, replace=True)
    theta = ALPHA + beta * xs + rng.normal(0, TAU, N_SRC)
    y = theta + rng.normal(0, se)
    return xs, y, se


def gen_own(rng, beta, x_t, k):
    se = rng.choice(REAL_SE, size=k, replace=True)
    theta = ALPHA + beta * x_t + rng.normal(0, TAU, k)
    y = theta + rng.normal(0, se)
    return y, se


def one_cell(beta, x_t, k, reps, seed):
    rng = np.random.default_rng(seed)
    mu_star = ALPHA + beta * x_t
    rec = {m: dict(err=[], lo=[], hi=[]) for m in METHODS}
    for _ in range(reps):
        xs, ys, ses = gen_sources(rng, beta)
        oy, ose = gen_own(rng, beta, x_t, k)
        # own / NMA
        mu0, se0 = own_estimate(oy, ose)
        rec["own"]["err"].append(mu0 - mu_star)
        rec["own"]["lo"].append(mu0 - Z975 * se0); rec["own"]["hi"].append(mu0 + Z975 * se0)
        for mode in ("relevance", "uniform", "scrambled"):
            b = borrow_estimate2(oy, ose, x_t, xs, ys, ses, BW, mode=mode, rng=rng)
            rec[mode]["err"].append(b["mu"] - mu_star)
            rec[mode]["lo"].append(b["ci_low"] if "ci_low" in b else b["mu"] - Z975 * b["se"])
            rec[mode]["hi"].append(b["ci_high"] if "ci_high" in b else b["mu"] + Z975 * b["se"])
    return mu_star, {m: {kk: np.array(vv) for kk, vv in d.items()} for m, d in rec.items()}


def mciw0(err, target=0.95):
    """matched-coverage width: calib=even idx, test=odd; constant half-width at
    the target quantile of |err| on calib, MCIW0 = 2*half; + test coverage."""
    n = len(err); idx = np.arange(n); calib = idx % 2 == 0; test = ~calib
    ae = np.abs(err)
    half = float(np.quantile(ae[calib], target))
    return 2 * half, float(np.mean(ae[test] <= half))


def paired_boot(err_m, err_b, target=0.95, n=3000, seed=7):
    """paired bootstrap of MCIW0(method) - MCIW0(base); win if 97.5% CI < 0."""
    rng = np.random.default_rng(seed)
    am, ab = np.abs(err_m), np.abs(err_b)
    bi = rng.integers(0, len(am), size=(n, len(am)))
    d = 2 * (np.quantile(am[bi], target, axis=1) - np.quantile(ab[bi], target, axis=1))
    lo, hi = np.quantile(d, [0.025, 0.975])
    point = 2 * (np.quantile(am, target) - np.quantile(ab, target))
    return dict(d=float(point), lo=float(lo), hi=float(hi),
                win=bool(hi < 0), harm=bool(lo > 0))


def main():
    rows = []
    seed = 100
    for sl_name, beta in SLOPES.items():
        for pos_name, x_t in POSITIONS.items():
            for rg, k in REGIMES.items():
                seed += 1
                mu_star, rec = one_cell(beta, x_t, k, REPS, seed)
                cell = dict(slope=sl_name, beta=round(beta, 4), pos=pos_name,
                            x_t=round(x_t, 2), regime=rg, mu_star=round(mu_star, 3))
                for m in METHODS:
                    w, cov = mciw0(rec[m]["err"])
                    lo = rec[m]["lo"]; hi = rec[m]["hi"]; tm = mu_star
                    raw_cov = float(np.mean((lo <= tm) & (tm <= hi)))
                    cell[f"{m}_mciw0"] = round(w, 4)
                    cell[f"{m}_bias"] = round(float(np.mean(rec[m]["err"])), 4)
                    cell[f"{m}_rawcov"] = round(raw_cov, 3)
                # contrasts vs own (NMA), and the two nulls
                for base in ("own", "uniform", "scrambled"):
                    r = paired_boot(rec["relevance"]["err"], rec[base]["err"])
                    cell[f"rel_vs_{base}"] = r
                rows.append(cell)
    json.dump(rows, open("sim_gate_results.json", "w"), indent=2)

    print(f"# CALIBRATED-DGP MCIW0 GATE  (alpha={ALPHA:+.3f}, beta_real={BETA_REAL:+.4f}, "
          f"tau={TAU:.3f}, bw={BW}, N_src={N_SRC}, reps={REPS})")
    print(f"# estimand mu*(x_t)=alpha+beta*x_t ; MCIW0 lower=better\n")
    for sl_name in SLOPES:
        print(f"=== slope {sl_name} (beta={round(SLOPES[sl_name],4)}) ===")
        print(f"{'pos':7}{'reg':7}{'own':>8}{'relev':>8}{'unif':>8}{'scram':>8}"
              f"   relevance vs: own / uniform / scrambled")
        for pos_name in POSITIONS:
            for rg in REGIMES:
                c = next(x for x in rows if x["slope"] == sl_name and x["pos"] == pos_name and x["regime"] == rg)
                def tag(d):
                    return "W" if d["win"] else ("H" if d["harm"] else ".")
                print(f"{pos_name:7}{rg:7}{c['own_mciw0']:>8.3f}{c['relevance_mciw0']:>8.3f}"
                      f"{c['uniform_mciw0']:>8.3f}{c['scrambled_mciw0']:>8.3f}   "
                      f"{c['rel_vs_own']['d']:+.3f}{tag(c['rel_vs_own'])} / "
                      f"{c['rel_vs_uniform']['d']:+.3f}{tag(c['rel_vs_uniform'])} / "
                      f"{c['rel_vs_scrambled']['d']:+.3f}{tag(c['rel_vs_scrambled'])}")
        print()
    print("legend: W=robust win (97.5%CI<0), H=robust harm (2.5%CI>0), .=n.s.")
    print("wrote sim_gate_results.json")


if __name__ == "__main__":
    main()
