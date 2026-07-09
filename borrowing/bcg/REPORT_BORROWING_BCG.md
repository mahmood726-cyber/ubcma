# Experiment 1 — Transportability on dat.bcg (the fair test the registry couldn't give us)

**Branch** `methods-borrowing` · **dir** `borrowing/bcg/` · 2026-06-30 · truth-first, honest negatives.

## Why this dataset
Pilot-4 proved the AACT registry *structurally separates* a wide population gradient from a
clean placebo-anchored effect: the gradient lives only in infectious binary-outcome domains
with no placebo anchor, while every placebo-anchored continuous effect is gradient-compressed
by trial-site selection. A decisive transportability test therefore needs all three in **one
slice**: a population gradient the trials sample, a clean placebo-anchored exchangeable effect,
and n. `dat.bcg` is exactly that slice.

**`dat.bcg`** = 13 **placebo-controlled** BCG-vaccine trials, absolute latitude **13°→55°**, full
2×2 cells. Latitude is the textbook **strong population effect-modifier**: BCG protection declines
toward the equator (the classic environmental-mycobacteria explanation). Source trials compiled by
**Colditz et al. 1994, *JAMA* 271(9):698–702** (efficacy meta-analysis) and curated as the canonical
multivariate-meta-analysis dataset by **Berkey, Hoaglin, Mosteller & Colditz 1995, *Stat Med*
14:395–411**; the latitude–efficacy gradient is discussed by **Fine 1995, *Lancet* 346:1339–1345**.
(Cited as the original publications, not "metadat", which is only the redistribution vehicle.)

Per-trial effect = log risk-ratio from the 2×2, `Var(logRR)=1/tpos−1/(tpos+tneg)+1/cpos−1/(cpos+cneg)`.

## Step 1 — the latitude modifier is REAL and STRONG (and why one test disagrees)
`prep_bcg.py`. logRR ranges −1.62…+0.45; latitude SD 13.9°.

| test | statistic | perm p |
|---|---|---|
| Fixed-weight WLS slope | −0.0292/deg (z=−6.59), R²=0.854 | **0.106** (leverage-conservative) |
| Unweighted OLS slope | −0.0264/deg | 0.054 |
| Spearman rank ρ | −0.564 | **0.049** |
| **RE (DL) meta-regression** | −0.0292/deg (z=−4.34), τ²=0.063 | **0.023** ← appropriate model |
| **metafor REML (external)** | −0.0291/deg (z=−4.04), p=5.2e-5, R²=75.6% | **0.0052** |

The lone non-significant test (fixed-weight WLS permutation, p=0.106) is an artifact: **2 of the 13
trials hold 65 % of the WLS weight** (max/min weight ratio 134), so permuting latitude occasionally
lands a giant-N trial at an extreme latitude and inflates the slope by leverage alone. The
random-effects model — which adds τ²=0.063 and de-concentrates the weights — is the correct one and
gives perm p = 0.023; the external metafor REML permutation test gives p = 0.0052. The modifier
**survives** adjustment for trial year (slope −0.0292→−0.0339) and allocation method (→−0.0303),
despite a latitude–year correlation of −0.66. **Verdict: latitude is a genuinely strong moderator.**

## Step 2 — 5-way real leave-one-trial-out (truth = real held-out logRR)
`run_bcg.py`. Each held-out trial gets ZERO own data → pure transportability prediction from the
other 12. Because latitude is the **only** covariate, relevance and transport share the *same*
Gaussian latitude kernel and differ **only** by the standardisation shift
`y_s→t = y_s + β_lat·(lat_t − lat_s)` (β_lat = LOO random-effects meta-regression slope from donors
only). So **(transport − relevance) isolates exactly the g-computation / transportability step.**

| bw | MAE nma | uni | rel | **tran** | scr | cover rel/tran | tran−rel | tran−nma | rel−unif |
|---|---|---|---|---|---|---|---|---|---|
| SD/2 (6.9) | 0.643 | 0.669 | 0.521 | **0.438** | 0.649 | .85/.92 | −0.083 [−0.130,−0.034] **W** | −0.205 [−0.354,−0.043] **W** | −0.149 n.s. |
| **SD (13.9)** | 0.643 | 0.669 | 0.494 | **0.445** | 0.519 | .92/.92 | −0.049 [−0.131,+0.035] n.s. | −0.198 [−0.344,−0.041] **W** | −0.175 [−0.306,−0.034] **W** |
| 1.5·SD (20.8) | 0.643 | 0.669 | 0.552 | **0.444** | 0.475 | .92/.92 | −0.108 [−0.237,+0.021] n.s. | −0.199 [−0.347,−0.042] **W** | −0.117 [−0.193,−0.036] **W** |

**Controls (central bw):**
- **β=0 inertia** — transport with the shift forced to 0 collapses *exactly* onto relevance
  (Δ = 0.0000): the machinery does nothing but standardise.
- **target=pool** — standardising to the donor **centroid** instead of the real held-out target
  significantly **hurts**: 0.632 vs 0.445, Δ +0.187 [+0.017, +0.347]. The transport gain genuinely
  comes from standardising to *the real target's latitude*, not from generic shrinkage.

## KEY VERDICT — does transportability beat relevance-only here?
**Directionally YES at every bandwidth and every method; not decisively significant at k=13.**
`transport − relevance` is negative in all three bandwidths (−0.083, −0.049, −0.108) and in all
three internal code paths, and is a significant win at the narrow bandwidth and under a jackknife
CI — but its 95 % bootstrap CI **crosses 0 at the pre-registered SD bandwidth**. With k=13 the
incremental margin of the standardisation step *over* relevance-down-weighting is underpowered.
**This is a strong second independent bound on the transport method, not a clean transport-beats-
relevance win.**

What **is** decisive: the **full transportability-weighted method robustly beats the textbook
random-effects (NMA) baseline** — `tran − nma ≈ −0.20 logRR MAE`, CI<0, in **all 3 bandwidths and
all 3 internal paths**. And, notably, **relevance-down-weighting on raw logRR barely beats the
scrambled-latitude null** here (tran−scr is the real signal, rel−scr is n.s. at central/wide bw): on
BCG it is the **standardisation**, not the kernel down-weight, that carries the borrowing gain.
Transport MAE is also strikingly *bandwidth-stable* (0.438/0.445/0.444) where relevance-only is not
(0.521/0.494/0.552) — the standardisation removes the kernel's bandwidth sensitivity.

This **mirrors and complements pilot-2** from the opposite corner: pilot-2 showed the relevance
kernel helps when the modifier is within-class and you *cannot* standardise (GLP1 dose→HbA1c);
BCG shows the standardisation helps when the modifier is a *strong external population gradient you
can g-compute* (latitude→logRR), where the kernel alone is weak. The two mechanisms are
complementary and each is now validated on real data in the regime it was designed for.

## Caveats
- **k = 13.** Coverage is near-nominal (0.92) but the transport-vs-relevance CI is wide; the
  marginal-step verdict is power-limited, not a structural null.
- Standardisation rides on an estimated, leverage-sensitive latitude slope (β_lat from 12 donors);
  its robustness comes from transport being bandwidth-stable and beating NMA despite slope noise.
- logRR is an observational moderator analysis (aggregate latitude), not individual-level transport.

## Cross-verification (vendor seats down → ≥3 internal + external + from-scratch)
SSH to both Codex seats (laptop `mahmo@100.80.183.43`, pc2 `user@100.127.107.46`) returned
publickey-denied in this non-interactive session; pc1 was already 401/agy-empty. Per the
standing rule the headline is confirmed:
1. `run_bcg.py` — Gaussian kernel, paired bootstrap, ubcma REML pooler.
2. `selfverify_bcg.py` — **from scratch**, recomputes logRR from the raw 2×2, inline kernel,
   independent Mandel-Paule REML; reproduces every number to ≤0.001 (tran−nma −0.197, tran−rel
   −0.049, target=pool +0.187, β=0 exact).
3. `xverify3_epan_jack.py` — **methodologically distinct**: Epanechnikov kernel + delete-1 jackknife
   CI + DerSimonian-Laird pooler; same signs (tran−nma −0.198 W; tran−rel −0.062 W).
4. `xverify_metafor.R` — **external engine (metafor)**: confirms the per-trial logRR/SE and the
   latitude meta-regression (slope −0.0291, REML permutest p=0.0052, R²=75.6 %).

## External cross-vendor confirmation (2026-07-01) — Codex Seat A, gpt-5.5
The laptop Codex Seat A now authenticates headless (verified: `codex exec` returns real gpt-5.5
completions over SSH, default `CODEX_HOME`). It was given the raw 13-trial 2×2 cells + the exact
estimand and told to **re-implement the whole LOO transport from scratch, no shared code, its own
DL/REML meta-regression slope**. Its independent result:

| quantity | committed | Codex Seat A (independent) | agreement |
|---|---|---|---|
| bw = latitude SD | 13.876 | 13.876 | exact |
| MAE_nma | 0.643 | 0.644 | ≤0.001 |
| MAE_rel | 0.494 | 0.494 | exact |
| MAE_tran | 0.445 | 0.445 | exact |
| **tran − nma (headline)** | **−0.198 [−0.344, −0.041]** | **−0.198 [−0.341, −0.035]** | **point exact (3 dp); CI matches (own bootstrap seed)** |
| **target = pool control** | **+0.187 [+0.017, +0.347]** | **+0.187** | **exact (3 dp)** |

This is **one genuine external vendor** (Codex gpt-5.5) alongside the ≥3 internal paths + metafor —
**not** a full two-vendor quorum. Seat B (`.codex-noreen`) is `401 token_invalidated` and agy returns
empty; running `codex login` in `.codex-noreen` on the laptop would add a second external vendor.

Exact invocation (prompt with embedded data piped on stdin; codex-cli 0.140.0, model gpt-5.5,
approval=never, sandbox=danger-full-access, reasoning=xhigh):
```
ssh -i ~\.ssh\node2_ed25519 mahmo@100.80.183.43 \
  "codex exec --skip-git-repo-check -s danger-full-access -C ~\codex-xverify \
   -o ~\codex-xverify\bcg_last.txt -"  < prompt_bcg.txt
```

## Files
`prep_bcg.py`, `bcg_trials.json`, `run_bcg.py`, `bcg_loo.json`, `selfverify_bcg.py`,
`xverify3_epan_jack.py`, `xverify_metafor.R`.
