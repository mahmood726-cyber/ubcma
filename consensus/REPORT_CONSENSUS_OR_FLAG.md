# consensus-or-flag — a heterogeneous cross-vendor verification primitive

**Branch** `methods-borrowing` · dir `consensus/` · 2026-07-02 · truth-first, honest boundary.
Formalises + benchmarks the verification primitive used throughout this program (the Codex +
Fable + internal-engine cross-checks). Built by a Fable-model sub-agent; **independently re-run by
the writer — results reproduce to ≤0.001** (with the RNG-seeding nit fixed: per-bank streams keyed
by a fixed `{single:0,homo:1,hetero:2}` offset instead of a per-process-salted `hash(name)`).

## The primitive
To verify a claim, run a bank of `N` verifiers; **FLAG for human review iff not all `N` confirm**
(consensus ⇔ all agree). The question: do **heterogeneous** verifiers (diverse methods → decorrelated
blind spots) catch errors that **homogeneous** verification (the same verifier re-run `N` times →
correlated blind spots) and a **single** verifier miss — at a *matched* false-flag rate?

## Error model (latent-score / Gaussian-copula)
Each claim is TRUE or FALSE; a FALSE claim's error is SYSTEMATIC with prob `f_sys` (a shared bug any
verifier that shares the method reproduces and misses) else IDIOSYNCRATIC. Verifier score
`Z_i = m_i + √ρ·G + √(1−ρ)·E_i`; ρ high for homogeneous (correlated re-runs), low for heterogeneous.
A systematic error is missed by a verifier that shares its blind spot (Bernoulli `β`): **homogeneous
= one shared blind-spot draw (all N blind together); heterogeneous = N independent draws** (P(all
blind)=βᴺ). FLAG iff `max_i Z_i > τ`; τ tuned per bank on TRUE claims to a **matched** false-flag
(0.10). 200k TRUE + 200k FALSE claims/cell, seeded.

## Headline (N=3, matched false-flag = 0.10; writer re-run)
| f_sys | single catch | homo catch | hetero catch |
|---|---|---|---|
| 0.00 | 0.888 | 0.898 | **0.974** |
| 0.25 | 0.770 | 0.781 | **0.902** |
| 0.50 | 0.651 | 0.659 | **0.827** |
| 0.75 | 0.533 | 0.540 | **0.755** |
| 1.00 | 0.413 | 0.422 | **0.683** |

**Truth-gate (hetero − homo catch, paired-bootstrap 95% CI, all exclude 0):** +0.076 / +0.121 /
+0.168 / +0.216 / +0.261 across f_sys 0→1; **on systematic errors alone ≈ +0.26** stably.

## The decisive isolation test
Setting `homo_ρ = hetero_ρ = 0.15` (both banks share identical noise correlation, so the ONLY
remaining difference is whether the systematic blind-spot draw is shared):

| f_sys | hetero − homo catch [95% CI] | reading |
|---|---|---|
| 0.00 | **−0.001 [−0.002, −0.000]** | **≈ 0 — no benefit when there are no systematic errors** |
| 0.25 | +0.056 [+0.054, +0.058] | win |
| 0.50 | +0.117 [+0.115, +0.119] | win |
| 0.75 | +0.175 [+0.172, +0.177] | win |
| 1.00 | +0.234 [+0.230, +0.236] | win |

This is the honest crux: **heterogeneity's advantage is specifically a systematic-error-catching
effect** — it vanishes (≈0) when errors are purely idiosyncratic and grows monotonically with the
systematic fraction. **Homogeneous re-running is barely better than a single verifier** (the shared
blind spot caps it); N-scaling confirms homo catch is flat in N while hetero climbs toward 1 as βᴺ→0.

## Verdict
Heterogeneous consensus-or-flag decisively beats homogeneous and single verification **at matched
false-flag**, and the benefit is **provably about decorrelated systematic blind spots** (isolation
test ties at f_sys=0). This is the theoretical justification for the cross-vendor (Codex/Fable/
internal-engine) quorum used across this program: diverse verifiers catch systematic errors that
re-running one verifier cannot.

## Honest caveats
- **Modeling result, not empirical.** Magnitudes depend on (β=0.6, δ=2.5, ρ=0.90/0.15); the
  *direction* and the *tie at f_sys=0* are structural (they follow from βᴺ-vs-shared-draw), but the
  point magnitudes should be calibrated against a real labelled corpus of verified/refuted claims
  before quoting externally.
- Reproduced to ≤0.001 across two independent runs after fixing the seeding nit.

## Files
`consensus_or_flag.py` (primitive + benchmark, seeded) · `consensus_or_flag_result.txt` (full run).
