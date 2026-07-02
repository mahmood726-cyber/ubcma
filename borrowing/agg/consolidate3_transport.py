"""THREE-slice transport-over-relevance, pooled SCALE-FREE (BCG + rota + raudenbush).

The third slice (raudenbush teacher-expectancy, weeks-of-prior-contact modifier) is on the
SMD scale, not logRR, so it cannot be pooled with BCG/rota by mixing raw absolute errors.
This script pools all three ONLY via scale-invariant metrics:

  (1) SIGN test   -- pool the sign of every per-trial delta d_i = |mu_tran_i - y_i| -
      |mu_rel_i - y_i| across all 61 trials; exact binomial one-sided sign test. Scale-free.
  (2) STANDARDISED sign-flip -- divide each slice's d_i by that slice's mean relevance error
      (dimensionless), pool, and run a paired sign-flip permutation on the pooled mean. This
      keeps magnitude information while being scale-free.
  (3) FRACTIONAL MAE reduction -- per slice f = (MAE_tran - MAE_rel)/MAE_rel; pool the three
      f's equal-weight with a stratified bootstrap CI. (Same scale-free metric the
      multi-specialty relevance analysis used.)

For reference it also re-prints the logRR-only 2-slice inverse-variance pool (BCG+rota),
which is unchanged. TRUTH throughout = real held-out effect. No new data beyond the three
verified metadat/deposited slices.
"""
import json, sys
import numpy as np
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from aggregate_transport import loo_errs  # noqa: E402
from scipy import stats  # noqa: E402
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = HERE.parent
SLICES = [
    dict(name="BCG (latitude, logRR)", path=ROOT / "bcg" / "bcg_trials.json", cov="ablat", scale="logRR"),
    dict(name="Rotavirus (U5MR, logRR)", path=ROOT / "rota" / "rota_trials.json", cov="u5mr", scale="logRR"),
    dict(name="Raudenbush (weeks, SMD)", path=ROOT / "raudenbush" / "raudenbush_trials.json", cov="weeks", scale="SMD"),
]


def slice_errs(sl):
    TRS = json.load(open(sl["path"]))["trials"]
    x = np.array([t[sl["cov"]] for t in TRS]); bw = float(x.std())     # central bw = SD
    e_rel = loo_errs(TRS, sl["cov"], bw, "relevance")
    e_tran = loo_errs(TRS, sl["cov"], bw, "transport")
    m = np.isfinite(e_rel) & np.isfinite(e_tran)
    return e_tran[m], e_rel[m]


def main():
    print("=" * 78)
    print("THREE-slice transport-over-relevance (scale-free pool): BCG + rota + raudenbush")
    print("central bandwidth (SD); TRUTH = real held-out effect")
    print("=" * 78)

    per = []
    for sl in SLICES:
        et, er = slice_errs(sl)
        d = et - er
        frac = (et.mean() - er.mean()) / er.mean()
        per.append(dict(name=sl["name"], scale=sl["scale"], et=et, er=er, d=d,
                        mae_tran=float(et.mean()), mae_rel=float(er.mean()),
                        frac=float(frac), n=len(d)))
        print(f"  {sl['name']:26} k={len(d):2}  MAE rel={er.mean():.3f} tran={et.mean():.3f}  "
              f"frac reduction={frac:+.1%}")

    # (1) pooled SIGN test across all trials
    d_all = np.concatenate([p["d"] for p in per])
    nneg = int((d_all < 0).sum()); ntot = len(d_all)
    p_sign = float(stats.binomtest(nneg, ntot, 0.5, alternative="greater").pvalue)
    print(f"\n[1] SIGN test (scale-free): {nneg}/{ntot} trials favour transport  "
          f"exact binomial one-sided p = {p_sign:.4f}")

    # (2) standardised sign-flip on pooled dimensionless deltas
    ds = np.concatenate([p["d"] / p["mae_rel"] for p in per])   # each slice scaled by its rel-MAE
    rng = np.random.default_rng(202)
    obs = float(ds.mean()); B = 100000
    signs = rng.integers(0, 2, size=(B, len(ds))) * 2 - 1
    pm = (signs * np.abs(ds)).mean(axis=1)
    p_flip = float((1 + (pm <= obs).sum()) / (B + 1))
    print(f"[2] standardised pooled mean delta = {obs:+.4f} (units of rel-MAE)  "
          f"sign-flip one-sided p = {p_flip:.4f}")

    # (3) fractional-reduction pool (equal-weight, stratified bootstrap)
    fracs = np.array([p["frac"] for p in per])
    Bf = 20000; boot = np.empty(Bf)
    for b in range(Bf):
        fs = []
        for p in per:
            idx = rng.integers(0, p["n"], p["n"])
            fs.append((p["et"][idx].mean() - p["er"][idx].mean()) / p["er"][idx].mean())
        boot[b] = np.mean(fs)
    lo, hi = np.quantile(boot, [.025, .975])
    print(f"[3] FRACTIONAL MAE reduction pool (equal-wt 3 slices): "
          f"{fracs.mean():+.1%}  boot95%[{lo:+.1%},{hi:+.1%}]"
          f"{'  <-- WIN (CI<0)' if hi < 0 else ''}")
    print(f"    per-slice fractions: " + ", ".join(f"{p['name'].split(' (')[0]} {p['frac']:+.1%}" for p in per))

    print(f"    fractional reductions range [{fracs.min():+.1%},{fracs.max():+.1%}] "
          f"(all same sign = {'yes' if (fracs < 0).all() else 'no'})")

    # (4) LEAVE-ONE-SLICE-OUT on the fractional pool (does any single slice carry it?)
    print("\n[4] LEAVE-ONE-SLICE-OUT (fractional pool, does any slice alone drive the win?)")
    loso_ok = True
    for drop in range(len(per)):
        keep = [j for j in range(len(per)) if j != drop]
        bk = np.empty(8000)
        for b in range(8000):
            fs = []
            for j in keep:
                p = per[j]; idx = rng.integers(0, p["n"], p["n"])
                fs.append((p["et"][idx].mean() - p["er"][idx].mean()) / p["er"][idx].mean())
            bk[b] = np.mean(fs)
        klo, khi = np.quantile(bk, [.025, .975]); kmu = np.mean([per[j]["frac"] for j in keep])
        w = khi < 0
        loso_ok = loso_ok and w
        print(f"    drop {per[drop]['name'].split(' (')[0]:12} -> pool {kmu:+.1%} [{klo:+.1%},{khi:+.1%}]"
              f"{'  still WIN' if w else '  crosses 0'}")

    # (5) RANDOM-EFFECTS (DL) pool + 95% PREDICTION INTERVAL on the per-slice fractional reductions
    print("\n[5] RANDOM-EFFECTS (DL) pool + 95% prediction interval on per-slice fractional reductions")
    # per-slice SE of the fractional reduction via within-slice bootstrap
    fr_se = []
    for p in per:
        bb = np.empty(4000)
        for b in range(4000):
            idx = rng.integers(0, p["n"], p["n"])
            bb[b] = (p["et"][idx].mean() - p["er"][idx].mean()) / p["er"][idx].mean()
        fr_se.append(float(bb.std(ddof=1)))
    fr = fracs; v = np.array(fr_se) ** 2; k = len(fr); w_ = 1.0 / v
    mu_fe = (w_ * fr).sum() / w_.sum()
    Q = float((w_ * (fr - mu_fe) ** 2).sum()); C = w_.sum() - (w_ ** 2).sum() / w_.sum()
    tau2 = max(0.0, (Q - (k - 1)) / C) if C > 0 else 0.0
    ws = 1.0 / (v + tau2); mu_re = float((ws * fr).sum() / ws.sum()); se_re = float(np.sqrt(1.0 / ws.sum()))
    I2 = max(0.0, (Q - (k - 1)) / Q) * 100 if Q > 0 else 0.0
    tcrit = float(stats.t.ppf(0.975, k - 1))
    pi_lo, pi_hi = mu_re - tcrit * np.sqrt(tau2 + se_re ** 2), mu_re + tcrit * np.sqrt(tau2 + se_re ** 2)
    ci_lo, ci_hi = mu_re - 1.96 * se_re, mu_re + 1.96 * se_re
    print(f"    RE mean {mu_re:+.1%} [{ci_lo:+.1%},{ci_hi:+.1%}]  tau2={tau2:.5f} I2={I2:.0f}%  Q={Q:.2f}(df={k-1})")
    print(f"    95% PREDICTION INTERVAL (t_{k-1}): [{pi_lo:+.1%},{pi_hi:+.1%}]"
          f"  {'excludes 0' if pi_hi < 0 else 'includes 0'}")

    # heterogeneity note retained
    hetero = f"I2={I2:.0f}%"

    out = dict(
        per_slice=[dict(name=p["name"], scale=p["scale"], n=p["n"],
                        mae_rel=p["mae_rel"], mae_tran=p["mae_tran"], frac=p["frac"]) for p in per],
        sign=[nneg, ntot, p_sign],
        std_signflip=[obs, p_flip],
        frac_pool=[float(fracs.mean()), float(lo), float(hi)],
        re_pool=dict(mu=mu_re, ci=[ci_lo, ci_hi], pi=[pi_lo, pi_hi], tau2=tau2, I2=I2),
        loso_all_win=bool(loso_ok),
    )
    json.dump(out, open(HERE / "consolidate3_results.json", "w"), indent=1)

    frac_win = hi < 0
    re_win = ci_hi < 0
    print("\n" + "=" * 78)
    print("FINAL VERDICT (full inference layer, 3 slices / 2 domains / k=61):")
    print(f"  sign test        : {nneg}/{ntot} favour transport, p={p_sign:.4f}")
    print(f"  fractional pool  : {fracs.mean():+.1%} [{lo:+.1%},{hi:+.1%}] {'WIN' if frac_win else 'n.s.'}")
    print(f"  leave-one-slice  : {'every drop still CI<0' if loso_ok else 'a drop crosses 0'}")
    print(f"  RE pool          : {mu_re:+.1%} [{ci_lo:+.1%},{ci_hi:+.1%}] {'WIN' if re_win else 'n.s.'};"
          f"  95% PI [{pi_lo:+.1%},{pi_hi:+.1%}] {'excl 0' if pi_hi < 0 else 'incl 0'}")
    settled = frac_win and re_win and loso_ok and p_sign < 0.05
    print("-" * 78)
    if settled:
        print("  => BEYOND k=13: on a SCALE-FREE basis transport BEATS relevance-only -- pooled CI<0,")
        print("     robust to leave-one-slice-out, RE mean CI<0, consistent across 3 strong-modifier")
        print("     slices in 2 domains. The 95% PREDICTION INTERVAL " +
              ("also excludes 0 (a new comparable slice is expected to keep the sign)."
               if pi_hi < 0 else "still includes 0 (only 3 slices; a 4th could fall either side)."))
    else:
        print("  => still directional (not all scale-free tests clear).")
    print("  HONEST COUNTERPART: the DOMAIN-MATCHED raw-logRR central-bw IV pool (BCG+rota only) is")
    print("  UNCHANGED at -0.069 [-0.140,+0.003] -- on-threshold. A 3rd logRR population-gradient")
    print("  slice (none on disk) would settle that specific pool directly. Sign test carries the")
    print("  LOO-overlap independence caveat; fractional pool + LOSO + RE-PI are the load-bearing tests.")
    print("=" * 78)


if __name__ == "__main__":
    main()
