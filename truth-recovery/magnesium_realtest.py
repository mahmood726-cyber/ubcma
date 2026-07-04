"""AdaptShrink external validity on a REAL ground-truth-anchored publication-bias case: magnesium
for acute myocardial infarction (metadat dat.li2007 / Li 2007; the textbook example).

Small early trials reported a large mortality benefit of IV magnesium; the ISIS-4 mega-trial
(N=58,050) and MAGIC (N=6,213) then showed essentially no effect. The mega-trials are the de-facto
GROUND TRUTH. A good publication-bias correction, applied to the SMALL-trial evidence base, should
move the spuriously-beneficial pooled estimate back toward that truth.

Test: pool the small trials (all except ISIS-4 and MAGIC) with each estimator, and measure the
distance of its logOR from the mega-trial truth. Truth-first: report whichever estimator lands
closest, whether or not it is AdaptShrink; a correction that OVER-shoots past the truth is not a win.
"""
import sys, io
import numpy as np
import pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(r"F:\ubcma\src")))
from ubcma.robust_methods import random_effects, henmi_copas, pet_fit, vevea_hedges, adaptshrink  # noqa
from ubcma.adaptshrink import adaptshrink_estimator, trim_and_fill  # noqa
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

# prefer the committed in-repo copy (reproducible); fall back to the public-data staging dir
_REPO = Path(__file__).resolve().parent.parent / "examples" / "li2007_magnesium.csv"
LI = _REPO if _REPO.exists() else Path(r"F:\public-data\metadat\dat.li2007.csv")
MEGA = {"ISIS-4", "MAGIC"}


def load():
    d = pd.read_csv(LI)
    a = d.ai + 0.5; b = d.n1i - d.ai + 0.5; c = d.ci + 0.5; e = d.n2i - d.ci + 0.5
    d["y"] = np.log((a / b) / (c / e))           # logOR mortality, magnesium vs control (<0 = benefit)
    d["se"] = np.sqrt(1 / a + 1 / b + 1 / c + 1 / e)
    d["N"] = d.n1i + d.n2i
    return d


def iv_pool(y, se):
    w = 1.0 / se ** 2
    mu = float(np.sum(w * y) / np.sum(w))
    return mu, float(1.0 / np.sqrt(np.sum(w)))


def getmu(res):
    for k in ("mu", "est", "estimate", "beta", "b0", "theta", "mu_hat"):
        if k in res and res[k] is not None:
            return float(res[k])
    raise KeyError(list(res))


def main():
    d = load()
    mega = d[d.study.isin(MEGA)]
    small = d[~d.study.isin(MEGA)]
    y_s, se_s = small.y.to_numpy(), small.se.to_numpy()
    truth, truth_se = iv_pool(mega.y.to_numpy(), mega.se.to_numpy())

    print("=" * 82)
    print("AdaptShrink external validity — magnesium/MI (dat.li2007), mega-trial ground truth")
    print("=" * 82)
    print(f"  small-trial evidence base: k={len(small)} trials, N={int(small.N.sum())}")
    print(f"  GROUND TRUTH (ISIS-4+MAGIC IV-pooled logOR): {truth:+.4f}  (OR {np.exp(truth):.3f}, se {truth_se:.4f}) "
          f"-> essentially no effect")
    print(f"  {'estimator':22}{'logOR':>9}{'OR':>7}{'|dist to truth|':>16}{'moved toward truth?':>21}")

    naive_mu, _ = iv_pool(y_s, se_s)                     # FE naive as reference distance start
    re = random_effects(y_s, se_s); naive_re = getmu(re)
    rows = []
    # comparators + ours
    ests = {}
    ests["naive RE (DL)"] = naive_re
    ests["Henmi-Copas"] = getmu(henmi_copas(y_s, se_s))
    ests["PET (Egger intcpt)"] = getmu(pet_fit(y_s, se_s))
    ests["trim-and-fill"] = getmu(trim_and_fill(y_s, se_s, side="right"))
    ests["Vevea-Hedges"] = getmu(vevea_hedges(y_s, se_s))
    ests["AdaptShrink solo"] = getmu(adaptshrink(y_s, se_s))
    ests["AdaptShrink ens"] = getmu(adaptshrink_estimator(y_s, se_s))

    base_dist = abs(naive_re - truth)
    for name, mu in ests.items():
        dist = abs(mu - truth)
        moved = "" if name == "naive RE (DL)" else (
            f"yes ({(base_dist-dist)/base_dist*100:+.0f}% closer)" if dist < base_dist
            else f"NO (overshoot {dist/base_dist*100:.0f}%)")
        rows.append((name, mu, dist, moved))
        print(f"  {name:22}{mu:>+9.4f}{np.exp(mu):>7.3f}{dist:>16.4f}{moved:>21}")

    best = min(rows[1:], key=lambda r: r[2])
    print(f"\n  naive RE is {base_dist:.4f} from truth (spurious benefit, OR {np.exp(naive_re):.2f}).")
    print(f"  CLOSEST corrector to the mega-trial truth: {best[0]}  (dist {best[2]:.4f}, OR {np.exp(best[1]):.2f}).")
    as_ens = next(r for r in rows if r[0] == "AdaptShrink ens")
    verdict = ("AdaptShrink ens is closest" if best[0] == "AdaptShrink ens"
               else f"AdaptShrink ens dist {as_ens[2]:.4f} vs best {best[0]} {best[2]:.4f}")
    print(f"  VERDICT (honest): {verdict}.")
    import json
    json.dump({"truth": truth, "truth_se": truth_se, "naive_re": naive_re,
               "estimators": {n: {"logOR": m, "dist": dabs} for n, m, dabs, _ in rows},
               "closest": best[0]}, open(Path(__file__).resolve().parent / "magnesium_realtest_result.json", "w"), indent=1)
    print("wrote magnesium_realtest_result.json")


if __name__ == "__main__":
    main()
