"""PILOT-2 confident-wrong-prior negative control for the HARDENED stand-down.

Replicates pilot-1's exact failure mode (the rich-regime GLP1 harm, dMCIW0 +0.256):
the target is an OUTLIER (truth far from the field), its OWN data is RICH and
precise, and the borrowing prior is the field consensus -- which is CONFIDENTLY
WRONG (the sources mutually agree with each other, just not with the target). The
1-df conflict statistic Q detects it, but pilot-1's SMOOTH discount never reaches
0, leaving ~20% prior weight -> robust harm.

We compare, on the SAME data, the borrow with:
  smooth-only (harden=False, q_max=inf) = pilot-1 stand-down
  hardened    (harden=True,  q_max=9)   = pilot-2 stand-down  (delta:=0 if Q>9)
A pass requires the hardened rule to ELIMINATE the rich-regime harm (relevance no
worse than own), while leaving the legitimate sparse-regime borrow intact.
"""
import numpy as np
from borrowing_field2 import borrow_estimate2, own_estimate, Z975

# confident-wrong setup: target outlier truth, field consensus = WRONG, low spread
M_FIELD = -0.55          # field-consensus truth (e.g. mixed T2DM classes)
DELTA = 0.62             # outlier gap: target truth = M_FIELD - DELTA (like GLP1 -1.17)
MU_TARGET = M_FIELD - DELTA
N_SRC = 16               # sources
# pilot-1's harm came from a heterogeneous field: the prior was WRONG but had a
# MODERATE se_p (between-source spread ~0.3 across classes), so Q ~ 4-7 and the
# smooth discount left delta ~ 0.20. We reproduce that here (NOT a tiny-se_p prior,
# which would self-extinguish even smoothly). SRC_TAU sets the between-source spread.
SRC_SE = 0.10            # per-source sampling se
SRC_TAU = 0.30           # between-source heterogeneity -> se_p ~ 0.3 (the P1 regime)
REAL_SE = np.array([0.05, 0.06, 0.07, 0.08, 0.10, 0.13])  # own-trial precisions
REPS = 1500
BW = 1e9                 # kernel ~flat over sources (x irrelevant here) -> uniform-ish prior


def gen(rng, k):
    # confident-wrong prior comes from sources clustered at M_FIELD
    xs = rng.uniform(0, 1, N_SRC)            # covariate irrelevant in this control
    ses = np.full(N_SRC, SRC_SE)
    ys = M_FIELD + rng.normal(0, SRC_TAU, N_SRC) + rng.normal(0, ses)
    # own (target) data: rich & precise, around the TRUE outlier value
    ose = rng.choice(REAL_SE, size=k, replace=True)
    oy = MU_TARGET + rng.normal(0, 0.05, k) + rng.normal(0, ose)
    return xs, ys, ses, oy, ose


def run(k, harden, fusion, seed):
    rng = np.random.default_rng(seed)
    err_b, err_o, deltas, Qs, dropped = [], [], [], [], 0
    for _ in range(REPS):
        xs, ys, ses, oy, ose = gen(rng, k)
        mu0, se0 = own_estimate(oy, ose)
        b = borrow_estimate2(oy, ose, 0.5, xs, ys, ses, BW, mode="uniform",
                             rng=rng, harden=harden, q_max=4.0, fusion=fusion)
        err_b.append(b["mu"] - MU_TARGET); err_o.append(mu0 - MU_TARGET)
        deltas.append(b["delta"]); Qs.append(b["Q"]); dropped += (b["delta"] <= 1e-6)
    err_b = np.array(err_b); err_o = np.array(err_o)
    return err_b, err_o, np.array(deltas), np.array(Qs), dropped / REPS


def mciw0(err, t=0.95):
    idx = np.arange(len(err)); c = idx % 2 == 0; te = ~c; ae = np.abs(err)
    half = np.quantile(ae[c], t)
    return 2 * half


def boot(em, eo, t=0.95, n=4000, seed=7):
    rng = np.random.default_rng(seed); am, ao = np.abs(em), np.abs(eo)
    bi = rng.integers(0, len(am), size=(n, len(am)))
    d = 2 * (np.quantile(am[bi], t, axis=1) - np.quantile(ao[bi], t, axis=1))
    lo, hi = np.quantile(d, [0.025, 0.975])
    return float(2 * (np.quantile(am, t) - np.quantile(ao, t))), float(lo), float(hi), bool(lo > 0)


print(f"# CONFIDENT-WRONG-PRIOR control: target truth={MU_TARGET:+.2f}, "
      f"field(prior)={M_FIELD:+.2f}, gap={DELTA}")
print(f"# configs: P1 = AdaptShrink fusion + smooth stand-down (pilot-1)")
print(f"#          P2 = precision fusion + hardened stand-down (pilot-2)")
print(f"#          mixed rows isolate which change matters\n")
print(f"{'regime':8}{'config':28}{'meanQ':>7}{'mDelta':>8}{'bias_b':>8}"
      f"{'bMCIW0':>8}{'oMCIW0':>8}{'  dMCIW0 vs own [95%CI]'}")
CONFIGS = [
    ("adaptshrink", False, "P1: adaptshrink+smooth"),
    ("adaptshrink", True,  "  adaptshrink+hardened"),
    ("precision",   False, "  precision+smooth"),
    ("precision",   True,  "P2: precision+hardened"),
]
for k, regime in [(8, "rich"), (2, "sparse")]:
    for fusion, harden, name in CONFIGS:
        eb, eo, dl, Qs, drop = run(k, harden, fusion, seed=42 + k + int(harden))
        d, lo, hi, harm = boot(eb, eo)
        flag = "  <-- HARM" if harm else ("  ok" if hi < 0 else "  n.s.")
        print(f"{regime:8}{name:28}{np.median(Qs):>7.2f}{dl.mean():>8.3f}"
              f"{eb.mean():>8.3f}{mciw0(eb):>8.3f}{mciw0(eo):>8.3f}"
              f"   {d:+.3f}[{lo:+.3f},{hi:+.3f}]{flag}")
