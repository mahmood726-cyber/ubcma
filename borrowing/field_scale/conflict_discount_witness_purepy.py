"""THIRD independent witness for the conflict-aware fused delta -- pure Python stdlib,
NO numpy, manual loops + manual paired bootstrap. Shares no code path with the two numpy
implementations (primary conflict_discount.py, from-scratch conflict_discount_witness.py),
so it cannot share a numpy-vectorisation or broadcasting bug in the fusion/bootstrap.

Reads conflict_discount_rows.csv (already-verified per-row inputs: within, within_sd,
mu_cold, sd_cold, y on the 144 cold AACT rows) and re-derives:
  a0    = clip(exp(-Q/2),0,1),  Q=(within-mu_cold)^2/(within_sd^2+sd_cold^2)
  fused = (within/within_sd^2 + a0*mu_cold/sd_cold^2)/(1/within_sd^2 + a0/sd_cold^2)
  delta = paired-bootstrap mean(|fused-y| - |within-y|), 5000 reps, LCG-seeded (own RNG).
Consensus with the numpy engines on SIGN + verdict => fusion arithmetic cross-implementation
confirmed. Emits nothing; prints the result.
"""
import csv, math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def clip01(x):
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def main():
    rows = list(csv.DictReader(open(HERE / "conflict_discount_rows.csv")))
    ef, ew = [], []          # per-row |fused-y|, |within-y|
    a0_glp1 = []
    for r in rows:
        y = float(r["y"]); w = float(r["within"]); wsd = float(r["within_sd"])
        mc = float(r["mu_cold"]); csd = float(r["sd_cold"])
        Q = (w - mc) ** 2 / (wsd ** 2 + csd ** 2)
        a0 = clip01(math.exp(-0.5 * Q))
        p_own = 1.0 / wsd ** 2
        p_pri = a0 / csd ** 2
        fused = (p_own * w + p_pri * mc) / (p_own + p_pri)
        ef.append(abs(fused - y)); ew.append(abs(w - y))
        if "glucagon" in r["ma"]:
            a0_glp1.append(a0)
    n = len(ef)
    mae_f = sum(ef) / n
    mae_w = sum(ew) / n
    d = [ef[i] - ew[i] for i in range(n)]
    dmean = sum(d) / n

    # own paired bootstrap: a plain LCG (glibc constants), NOT numpy default_rng
    seed = 7
    def lcg():
        nonlocal seed
        seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
        return seed
    means = []
    for _ in range(5000):
        s = 0.0
        for _ in range(n):
            s += d[lcg() % n]
        means.append(s / n)
    means.sort()
    lo = means[int(0.025 * 5000)]
    hi = means[int(0.975 * 5000)]
    verdict = "BEATS within" if hi < 0 else ("worse than within" if lo > 0 else "TIE (safe)")
    print(f"PUREPY_WITNESS n={n} MAE_within={mae_w:.4f} MAE_fused={mae_f:.4f} "
          f"delta={dmean:+.4f} [{lo:+.4f},{hi:+.4f}] -> {verdict}")
    print(f"PUREPY_WITNESS GLP1 mean a0={sum(a0_glp1)/len(a0_glp1):.3f} (n={len(a0_glp1)})")


if __name__ == "__main__":
    main()
