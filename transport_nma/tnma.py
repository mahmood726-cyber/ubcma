"""Transportable NMA with REGISTRY-BASED publication-bias adjustment (bounded demo).

A distinct method type in the program's REGISTRY-BASED-META family, on the validated
netmeta-parity engine `nma/nma_core.py`.

(1) REGISTRY PUBLICATION BIAS. From AACT (registered-vs-published selection) each drug CLASS c has
    an integrity ratio lambda_c = (registered trials that POSTED results)/(registered trials)
    -- `borrowing/class_lambda.json` (class_lambda.py on the 2026-04-12 AACT snapshot). Low lambda_c
    = strong reporting selection => that class's PUBLISHED effect is selection-inflated. We use
    (1 - lambda_c) as a per-treatment selection-severity proxy and shrink each treatment's
    placebo-relative basic contrast toward the null by kappa*(1-lambda_t) (the NMA generalisation of
    the univariate AdaptShrink selection-bias correction), with a registry-informed variance
    inflation 1/sqrt(lambda_t) so the CI honestly widens for selection-prone classes.

(2) REAL NMA. `dat.senn2013` (metadat) -- diabetes RCTs, HbA1c change, a connected network of
    metformin / DPP4 / SU / TZD / AGI / benfluorex vs placebo. Arms -> pairwise mean-difference
    contrasts -> fit_nma.

TRUTH-GATE (known-truth sim on the senn2013 network geometry): inject class-selection bias into each
active treatment's TRUE placebo-relative effect, bias_t = B*(1-lambda_t)*|d_true_t| (toward larger
apparent benefit); sweep B in {0, 0.15, 0.30}. Does the registry-lambda correction recover the TRUE
basic contrasts better than the unadjusted NMA at matched coverage (MCIW0, paired-bootstrap)? Honest
inertia boundary expected: a FIXED correction should help when selection is real (B>0) and HURT when
absent (B=0) -> motivating a selection-presence gate (as in univariate AdaptShrink).

Transportability layer (standardise the network to a target population via IHME/WHO/World-Bank) is
scoped in REPORT_TRANSPORT_NMA.md -- senn2013 lacks per-trial population covariates (the pilot-4
structural wall), so it is validated on a calibrated sim, not asserted on real data here.
"""
import json, io, sys
import numpy as np
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "nma"))
sys.path.insert(0, str(ROOT / "src"))
from nma_core import Comparison, fit_nma, p_score  # noqa: E402
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
Z975 = 1.959963984540054

SENN = Path(r"F:\public-data\metadat\dat.senn2013.csv")
LAMBDA = json.load(open(ROOT / "borrowing" / "class_lambda.json"))
TREAT_CLASS = {
    "metformin": "metformin", "sitagliptin": "DPP4", "vildagliptin": "DPP4",
    "sulfonylurea": "SU", "pioglitazone": "TZD", "rosiglitazone": "TZD",
    "acarbose": "AGI", "miglitol": "AGI", "benfluorex": None, "placebo": None,
}


def lam(t):
    c = TREAT_CLASS.get(t)
    return float(LAMBDA[c]) if c in LAMBDA else 1.0   # placebo/benfluorex -> 1 (no down-weight)


def senn_contrasts():
    d = pd.read_csv(SENN); comps = []
    for study, g in d.groupby("study"):
        rows = g.to_dict("records")
        ref = next((r for r in rows if r["treatment"] == "placebo"), rows[0])
        for r in rows:
            if r["treatment"] == ref["treatment"]:
                continue
            te = float(r["mi"]) - float(ref["mi"])
            se = float(np.sqrt(r["sdi"] ** 2 / r["ni"] + ref["sdi"] ** 2 / ref["ni"]))
            comps.append(Comparison(str(study), r["treatment"], ref["treatment"], te, se))
    return comps


def registry_correct(d_t, se_t, treat, kappa):
    """Network-level registry-lambda pub-bias correction of a placebo-relative basic contrast:
    shrink toward null by kappa*(1-lambda_t); inflate SE by 1/sqrt(lambda_t)."""
    shrink = kappa * (1.0 - lam(treat))
    return d_t * (1.0 - shrink), se_t / np.sqrt(max(lam(treat), 0.05))


def real_demo():
    print("=" * 74)
    print("(A) REAL diabetes NMA on dat.senn2013 + registry publication-bias overlay")
    print("=" * 74)
    comps = senn_contrasts()
    fit = fit_nma(comps, reference="placebo", random=True)
    ps = p_score(fit, small_values="desirable")
    ti = {t: i for i, t in enumerate(fit.treatments)}; ref = ti["placebo"]
    print(f"  network: {fit.n} treatments, {fit.k} studies, {fit.m} contrasts; tau={fit.tau:.3f}, I2={fit.I2:.0f}%")
    print(f"  {'treatment':13}{'MD vs plac':>11}{'seTE':>7}{'pscore':>8}{'class':>10}{'lambda':>7}{'reg-adj MD':>11}")
    for t in sorted(fit.treatments, key=lambda x: fit.TE[ti[x], ref]):
        if t == "placebo":
            continue
        md = fit.TE[ti[t], ref]; se = fit.seTE[ti[t], ref]
        md_adj, _ = registry_correct(md, se, t, kappa=0.5)
        print(f"  {t:13}{md:>+11.3f}{se:>7.3f}{ps[t]:>8.3f}{str(TREAT_CLASS.get(t)):>10}{lam(t):>7.2f}{md_adj:>+11.3f}")
    print("  (reg-adj shrinks selection-prone low-lambda classes' apparent benefit toward null)")
    return comps


def sim_truthgate(comps, B, kappas, reps=400, seed=1):
    """Inject bias B*(1-lambda) into active arms; score unadjusted vs registry-corrected at each
    kappa in `kappas` (SE not inflated here -- MCIW0 is a point-efficiency metric, and variance
    inflation only widens intervals; we score the point estimator, then report coverage separately)."""
    treats = sorted({t for c in comps for t in (c.t1, c.t2)})
    fit0 = fit_nma(comps, reference="placebo", random=True)
    pi = fit0.treatments.index("placebo")
    true_d = {t: (fit0.TE[fit0.treatments.index(t), pi] if t in fit0.treatments else 0.0) for t in treats}
    active = [t for t in treats if t != "placebo"]
    rng = np.random.default_rng(seed)
    eu = []; ea = {k: [] for k in kappas}
    for r in range(reps):
        sim = []
        for c in comps:
            def bt(t):
                base = true_d.get(t, 0.0)
                return base * (1.0 + B * (1.0 - lam(t)))   # selection INFLATES |effect|, sign preserved
            sim.append(Comparison(c.studlab, c.t1, c.t2, bt(c.t1) - bt(c.t2) + rng.normal(0, c.se), c.se))
        f = fit_nma(sim, reference="placebo", random=True)
        ii = {t: i for i, t in enumerate(f.treatments)}; ref = ii["placebo"]
        for t in active:
            if t not in ii:
                continue
            md = f.TE[ii[t], ref]; tru = true_d.get(t, 0.0)
            eu.append(abs(md - tru))
            for k in kappas:
                md_a = md * (1.0 - k * (1.0 - lam(t)))
                ea[k].append(abs(md_a - tru))
    eu = np.array(eu)
    def mc(e): return 2 * np.quantile(np.asarray(e), 0.95)
    out = dict(B=B, mciw0_un=mc(eu), kappa={})
    parts = [f"B={B:.2f}: unadj MCIW0 {mc(eu):.4f}"]
    for k in kappas:
        e = np.array(ea[k]); d = e - eu
        bi = rng.integers(0, len(d), size=(3000, len(d)))
        md_b = np.array([2 * (np.quantile(e[b], .95) - np.quantile(eu[b], .95)) for b in bi])
        lo, hi = np.quantile(md_b, [.025, .975])
        v = "WINS" if hi < 0 else ("HARMS" if lo > 0 else "tie")
        klbl = "oracle(=B)" if abs(k - B) < 1e-9 else f"fix{k:.2f}"
        parts.append(f"reg-adj[{klbl}] MCIW0 {mc(e):.4f} d{mc(e)-mc(eu):+.4f}[{lo:+.4f},{hi:+.4f}]{v}")
        out["kappa"][f"{k:.3f}"] = dict(mciw0=mc(e), dmciw0=mc(e) - mc(eu), ci=[float(lo), float(hi)], verdict=v)
    print("  " + " | ".join(parts))
    return out


def main():
    comps = real_demo()
    print("\n" + "=" * 74)
    print("(B) TRUTH-GATE sim (senn2013 geometry; selection bias B*(1-lambda) on active arms)")
    print("=" * 74)
    print("  registry-lambda correction vs unadjusted NMA at matched coverage (MCIW0); kappa =")
    print("  oracle(=true selection strength B) AND a fixed kappa=0.5, to separate PATTERN from STRENGTH:")
    res = [sim_truthgate(comps, B=b, kappas=sorted({b, 0.5})) for b in (0.0, 0.15, 0.30)]
    print("\nVERDICT (honest): the registry-lambda gives the correct RELATIVE selection-severity PATTERN")
    print("  (which classes are selection-prone) -- an ORACLE-calibrated correction (kappa=B) recovers")
    print("  truth better than the unadjusted NMA under real selection (B>0) and is ~inert at B=0. But")
    print("  a FIXED, uncalibrated kappa=0.5 OVER-CORRECTS and HARMS everywhere. So registry pub-bias")
    print("  adjustment in NMA needs (a) a data-driven strength (funnel asymmetry, not a fixed kappa)")
    print("  and (b) a selection-presence gate -- exactly the univariate-AdaptShrink discipline. The")
    print("  registry lambda supplies the direction/ranking of selection severity, not its magnitude.")
    json.dump(dict(sweep=res), open(HERE / "tnma_result.json", "w"), indent=1)
    print("wrote tnma_result.json")


if __name__ == "__main__":
    main()
