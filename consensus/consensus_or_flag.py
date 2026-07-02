#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consensus_or_flag.py
====================
Truth-first simulation benchmark for the "consensus-or-flag" heterogeneous
verification primitive.

PRIMITIVE
---------
To verify a computational/statistical CLAIM, run N independent verifiers and
apply the decision rule:

    FLAG the claim  iff  NOT all N verifiers confirm it (>= 1 rejects).
    Otherwise output CONSENSUS (accept).

We compare three verifier banks holding N and the per-verifier operating point
fixed, and ask whether HETEROGENEOUS verifiers (diverse methods -> decorrelated
blind spots) beat HOMOGENEOUS verifiers (same verifier re-run N times ->
correlated blind spots) and SINGLE (N=1), *at a matched false-flag rate*.

FORMAL ERROR MODEL (latent-score / Gaussian-copula)
---------------------------------------------------
Each claim is TRUE (correct) or FALSE (contains a real error). A FALSE claim's
error is SYSTEMATIC with prob f_sys, else IDIOSYNCRATIC.

Verifier i emits a continuous suspicion score for a claim:

    Z_i = m_i + sqrt(rho) * G + sqrt(1 - rho) * E_i,      G, E_i ~ iid N(0,1)

  * G  = latent shared by all verifiers in the bank (common difficulty / shared
         method signal). Corr(Z_i, Z_j) = rho.
  * E_i = independent per-verifier noise.
  * rho = HIGH for a homogeneous bank (re-runs of one method are highly
          correlated); LOW for a heterogeneous bank (diverse methods lightly
          correlated); irrelevant for single (N=1).

The mean shift m_i encodes what the verifier "sees":
  * TRUE claim:                 m_i = 0            (nothing wrong)
  * FALSE, idiosyncratic error: m_i = delta_idio   (any verifier can notice)
  * FALSE, systematic error:    depends on BLIND SPOT.
        A verifier that SHARES the claim's method reproduces the bug and sees
        nothing:                m_i = 0  (blind, will confirm the wrong claim)
        A verifier with a DIFFERENT method disagrees:
                                m_i = delta_sys
    Blind-spot sharing indicator ~ Bernoulli(beta):
        HOMOGENEOUS: ONE shared draw -> all N verifiers blind together
                     (perfectly correlated systematic misses).
        HETEROGENEOUS: N INDEPENDENT draws -> P(all N blind) = beta^N.
        SINGLE: one draw.

DECISION STATISTIC
------------------
Verifier i rejects iff Z_i > tau. Consensus-or-flag => FLAG iff max_i Z_i > tau.
So the per-claim statistic is  S = max_i Z_i, and FLAG iff S > tau.

METRICS (all conditional -> prevalence-free)
--------------------------------------------
  catch rate (sensitivity) = P(FLAG | claim FALSE)      -> want high
  false-flag rate (1-spec) = P(FLAG | claim TRUE)       -> want low
  Youden J                 = catch - false_flag

MATCHED-FALSE-FLAG COMPARISON
-----------------------------
For each bank we tune tau on TRUE claims so the false-flag rate equals a common
target (e.g. 0.10), then read the catch rate. This neutralizes the false-flag
axis (adding verifiers inflates false alarms; a fair comparison must hold that
fixed) and isolates the systematic-blind-spot effect. Truth-gate: is
hetero_catch - homo_catch > 0 with a paired-bootstrap 95% CI excluding 0?

Everything is seeded.
"""

import numpy as np


# ----------------------------- configuration ------------------------------- #
MASTER_SEED   = 20260701
N_TRUE        = 200_000      # true claims (for tau tuning + false-flag est)
N_FALSE       = 200_000      # false claims (for catch-rate est)
TARGET_FF     = 0.10         # matched false-flag rate for the headline table

PARAMS = dict(
    beta      = 0.60,   # P(a verifier shares the claim's systematic blind spot)
    delta_idio= 2.5,    # suspicion shift from an idiosyncratic error
    delta_sys = 2.5,    # suspicion shift when a verifier does NOT share blind spot
    rho_high  = 0.90,   # score correlation within a homogeneous bank
    rho_low   = 0.15,   # score correlation within a heterogeneous bank
)


# --------------------------- claim-population gen --------------------------- #
def make_error_types(n_false, f_sys, rng):
    """Return boolean array: True => systematic error, False => idiosyncratic."""
    return rng.random(n_false) < f_sys


# --------------------------- score simulation ------------------------------- #
def sim_scores(n, means_mode, N, rho, error_is_sys, params, rng,
               blind_shared=False):
    """
    Simulate S = max_i Z_i for `n` claims under a bank of N verifiers.

    means_mode   : 'true' | 'false'
    error_is_sys : bool array length n (only used when means_mode=='false')
    blind_shared : True  -> all N verifiers share ONE blind-spot draw (homogeneous)
                   False -> each verifier draws its blind spot independently (heterogeneous)
    Returns S (length n).
    """
    beta       = params['beta']
    delta_idio = params['delta_idio']
    delta_sys  = params['delta_sys']

    # shared latent G (one per claim) and independent noise E (n x N)
    G = rng.standard_normal(n)
    E = rng.standard_normal((n, N))
    if N == 1:
        rho = 0.0  # single verifier: no shared/independent split needed
    Z = np.sqrt(rho) * G[:, None] + np.sqrt(1.0 - rho) * E   # marginal N(0,1)

    # mean shifts m_i (n x N)
    M = np.zeros((n, N))
    if means_mode == 'false':
        idio = ~error_is_sys
        # idiosyncratic-error claims: every verifier shifted up
        M[idio, :] = delta_idio

        sys_idx = np.where(error_is_sys)[0]
        if sys_idx.size:
            if N == 1:
                blind = rng.random(sys_idx.size) < beta            # (n_sys,)
                shifts = np.where(blind, 0.0, delta_sys)[:, None]
            elif blind_shared:
                # HOMOGENEOUS: one shared blind draw -> all N same
                blind = rng.random(sys_idx.size) < beta            # (n_sys,)
                shifts = np.where(blind[:, None], 0.0, delta_sys)   # (n_sys,1)->broadcast
                shifts = np.broadcast_to(shifts, (sys_idx.size, N))
            else:
                # HETEROGENEOUS: independent blind draw per verifier
                blind = rng.random((sys_idx.size, N)) < beta        # (n_sys,N)
                shifts = np.where(blind, 0.0, delta_sys)
            M[sys_idx, :] = shifts

    Z = Z + M
    return Z.max(axis=1)


# --------------------------- one experiment cell ---------------------------- #
def run_cell(f_sys, N, target_ff, params, seed, homo_rho=None):
    """
    Build the three banks (single/homo/hetero) on a COMMON claim population and
    return per-claim FLAG outcomes at matched false-flag rate `target_ff`, plus
    tuned thresholds and achieved rates.

    homo_rho : override the homogeneous bank's score correlation. Default =
               params['rho_high']. Set equal to rho_low for a "blind-spot-only"
               isolation run (both banks share noise correlation; the ONLY
               difference is whether the blind-spot draw is shared).
    """
    if homo_rho is None:
        homo_rho = params['rho_high']

    rng_pop = np.random.default_rng(seed)          # claim structure (shared)
    error_is_sys = make_error_types(N_FALSE, f_sys, rng_pop)

    banks = {
        'single': dict(N=1,  rho=0.0,             blind_shared=False),
        'homo'  : dict(N=N,  rho=homo_rho,        blind_shared=True),
        'hetero': dict(N=N,  rho=params['rho_low'], blind_shared=False),
    }

    out = {}
    for name, cfg in banks.items():
        # independent draw stream per bank, but same claim labels/error types
        rng_t = np.random.default_rng(seed + 1000 + {'single':0,'homo':1,'hetero':2}[name])
        rng_f = np.random.default_rng(seed + 2000 + {'single':0,'homo':1,'hetero':2}[name])

        S_true  = sim_scores(N_TRUE,  'true',  cfg['N'], cfg['rho'],
                             None, params, rng_t, blind_shared=cfg['blind_shared'])
        S_false = sim_scores(N_FALSE, 'false', cfg['N'], cfg['rho'],
                             error_is_sys, params, rng_f,
                             blind_shared=cfg['blind_shared'])

        # tune tau so false-flag rate == target: tau = (1-target) quantile of S_true
        tau = np.quantile(S_true, 1.0 - target_ff)
        flag_true  = S_true  > tau
        flag_false = S_false > tau

        out[name] = dict(
            tau=tau,
            ff=flag_true.mean(),
            catch=flag_false.mean(),
            flag_false=flag_false,          # per-claim, for paired bootstrap
            S_true=S_true,
        )
    out['error_is_sys'] = error_is_sys
    return out


# --------------------------- paired bootstrap ------------------------------- #
def paired_bootstrap_diff(flag_a, flag_b, n_boot, seed, subset=None):
    """
    Paired bootstrap over claims of  mean(flag_b) - mean(flag_a).
    Returns (point, lo, hi) for a 95% percentile CI.
    """
    if subset is not None:
        flag_a = flag_a[subset]
        flag_b = flag_b[subset]
    n = flag_a.size
    rng = np.random.default_rng(seed)
    point = flag_b.mean() - flag_a.mean()
    diffs = np.empty(n_boot)
    fa = flag_a.astype(np.float64)
    fb = flag_b.astype(np.float64)
    for b in range(n_boot):
        idx = rng.integers(0, n, n)
        diffs[b] = fb[idx].mean() - fa[idx].mean()
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return point, lo, hi


# --------------------------------- main ------------------------------------- #
def main():
    np.random.seed(MASTER_SEED)
    N_BOOT = 2000

    print("=" * 78)
    print("CONSENSUS-OR-FLAG heterogeneous-verification benchmark")
    print("=" * 78)
    print("Parameters:")
    for k, v in PARAMS.items():
        print(f"    {k:11s} = {v}")
    print(f"    N_true={N_TRUE:,}  N_false={N_FALSE:,}  target_false_flag={TARGET_FF}")
    print(f"    bootstrap resamples = {N_BOOT}   master_seed={MASTER_SEED}")
    print()

    # ---- headline table: N=3, sweep f_sys ---- #
    print("-" * 78)
    print("HEADLINE  (N=3 bank; matched false-flag = %.2f)" % TARGET_FF)
    print("-" * 78)
    header = (f"{'f_sys':>6} | {'bank':>7} | {'false_flag':>10} | {'catch':>7} | "
              f"{'Youden_J':>8}")
    fsys_grid = [0.0, 0.25, 0.50, 0.75, 1.0]

    headline_rows = {}
    for f_sys in fsys_grid:
        cell = run_cell(f_sys, N=3, target_ff=TARGET_FF, params=PARAMS,
                        seed=MASTER_SEED + int(f_sys * 100))
        headline_rows[f_sys] = cell
        print(header)
        for name in ['single', 'homo', 'hetero']:
            c = cell[name]
            J = c['catch'] - c['ff']
            print(f"{f_sys:6.2f} | {name:>7} | {c['ff']:10.4f} | "
                  f"{c['catch']:7.4f} | {J:8.4f}")
        print()

    # ---- truth-gate: hetero vs homo catch, paired bootstrap, per f_sys ---- #
    print("-" * 78)
    print("TRUTH-GATE  (N=3): hetero_catch - homo_catch at matched %.0f%% false-flag"
          % (TARGET_FF * 100))
    print("            paired bootstrap over claims, 95% percentile CI")
    print("-" * 78)
    print(f"{'f_sys':>6} | {'d_catch(all)':>22} | {'d_catch(SYS only)':>24} | verdict")
    for f_sys in fsys_grid:
        cell = headline_rows[f_sys]
        homo = cell['homo']['flag_false']
        het  = cell['hetero']['flag_false']
        sys_mask = cell['error_is_sys']

        pt, lo, hi = paired_bootstrap_diff(homo, het, N_BOOT,
                                           seed=MASTER_SEED + 7)
        if sys_mask.any():
            pts, los, his = paired_bootstrap_diff(homo, het, N_BOOT,
                                                  seed=MASTER_SEED + 9,
                                                  subset=sys_mask)
        else:
            pts = los = his = float('nan')

        verdict = "WIN " if lo > 0 else ("LOSS" if hi < 0 else "tie ")
        allstr = f"{pt:+.4f} [{lo:+.4f},{hi:+.4f}]"
        sysstr = (f"{pts:+.4f} [{los:+.4f},{his:+.4f}]"
                  if sys_mask.any() else "         n/a          ")
        print(f"{f_sys:6.2f} | {allstr:>22} | {sysstr:>24} | {verdict}")
    print()

    # ---- N-scaling at fixed f_sys=0.5 ---- #
    print("-" * 78)
    print("N-SCALING  (f_sys=0.50; matched false-flag = %.2f): catch rate by bank"
          % TARGET_FF)
    print("-" * 78)
    print(f"{'N':>3} | {'single':>8} | {'homo':>8} | {'hetero':>8} | "
          f"{'hetero-homo (95% CI)':>26}")
    for N in [1, 3, 5, 7]:
        cell = run_cell(0.50, N=N, target_ff=TARGET_FF, params=PARAMS,
                        seed=MASTER_SEED + 500 + N)
        s = cell['single']['catch']
        h = cell['homo']['catch']
        e = cell['hetero']['catch']
        if N == 1:
            # single==homo==hetero degenerate at N=1; report single only
            print(f"{N:3d} | {s:8.4f} | {'  --  ':>8} | {'  --  ':>8} | "
                  f"{'(N=1: no bank)':>26}")
            continue
        pt, lo, hi = paired_bootstrap_diff(cell['homo']['flag_false'],
                                           cell['hetero']['flag_false'],
                                           N_BOOT, seed=MASTER_SEED + 11)
        ci = f"{pt:+.4f} [{lo:+.4f},{hi:+.4f}]"
        print(f"{N:3d} | {s:8.4f} | {h:8.4f} | {e:8.4f} | {ci:>26}")
    print()

    # ---- sanity: matched false-flag achieved (should ~equal target) ---- #
    print("-" * 78)
    print("SANITY: achieved false-flag rates (should all ~= target %.2f)" % TARGET_FF)
    print("-" * 78)
    cell = headline_rows[0.50]
    for name in ['single', 'homo', 'hetero']:
        print(f"    {name:>7}: tau={cell[name]['tau']:.4f}  "
              f"false_flag={cell[name]['ff']:.4f}")
    print()

    # ---- ISOLATION: blind-spot-only (both banks share rho_low noise corr) ---- #
    # Removes the noise-decorrelation advantage; the ONLY difference between the
    # two N=3 banks is whether the systematic blind-spot draw is shared (homo) or
    # independent (hetero). This isolates the pure systematic-error mechanism.
    print("-" * 78)
    print("ISOLATION  (N=3, homo_rho = hetero_rho = %.2f): blind-spot effect ONLY"
          % PARAMS['rho_low'])
    print("           hetero_catch - homo_catch; if the win is truly about")
    print("           systematic blind spots it should VANISH at f_sys=0 and grow")
    print("           with f_sys. Paired-bootstrap 95%% CI.")
    print("-" * 78)
    print(f"{'f_sys':>6} | {'homo_catch':>10} | {'hetero_catch':>12} | "
          f"{'d_catch(all) 95% CI':>26} | verdict")
    for f_sys in fsys_grid:
        cell = run_cell(f_sys, N=3, target_ff=TARGET_FF, params=PARAMS,
                        seed=MASTER_SEED + 3000 + int(f_sys * 100),
                        homo_rho=PARAMS['rho_low'])
        homo = cell['homo']['flag_false']
        het  = cell['hetero']['flag_false']
        pt, lo, hi = paired_bootstrap_diff(homo, het, N_BOOT,
                                           seed=MASTER_SEED + 13)
        verdict = "WIN " if lo > 0 else ("LOSS" if hi < 0 else "tie ")
        ci = f"{pt:+.4f} [{lo:+.4f},{hi:+.4f}]"
        print(f"{f_sys:6.2f} | {cell['homo']['catch']:10.4f} | "
              f"{cell['hetero']['catch']:12.4f} | {ci:>26} | {verdict}")
    print()
    print("Done.")


if __name__ == "__main__":
    main()
