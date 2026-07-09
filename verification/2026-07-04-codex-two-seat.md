# Cross-vendor verification run — two Codex seats — 2026-07-04

**Orchestrator:** Claude (Opus 4.8, thin orchestrator). **Intended second vendor:** OpenAI Codex CLI (`codex exec`, gpt-5.5).

## TL;DR

**Neither Codex seat ran. Cross-vendor witnessing was NOT achieved this session** — every reachable Codex path returned `401 Unauthorized / refresh token revoked`, and both SSH remotes denied publickey in this non-interactive session. No headline number was independently witnessed by a second vendor. As an honest, clearly-labelled *fallback only*, Claude re-executed the committed Seat-A artifacts to confirm **same-vendor reproducibility** (deterministic re-run reproduces the repo's own numbers exactly). This is reproducibility, not cross-vendor confirmation.

---

## What was attempted (all Codex paths dead)

| Path | Target | Result |
|---|---|---|
| Local profile `~/.codex` | pc1, account `mahmood726` (gpt-5.5) | **401 — refresh token revoked** |
| Local profile `~/.codex-noreen` | pc1, 2nd profile | **401 — refresh token revoked** |
| Local backup `~/.codex-backups/auth.mahmood726.latest.json` | pc1 (Jun 19 token) | **401 — refresh token revoked** (same account) |
| SSH → laptop `mahmo@100.80.183.43` | run `codex exec` remotely | **Permission denied (publickey)** — no key/password in non-interactive session |
| SSH → pc2 `User@100.127.107.46` | run `codex exec` remotely | **Permission denied (publickey)** |
| `OPENAI_API_KEY` / `CODEX_API_KEY` env, or key in `auth.json` | API-key fallback | **not set / not present** |

Root cause: the `mahmood726` ChatGPT-subscription auth (shared by all local profiles + backups) has had its refresh token revoked globally. Codex needs an **interactive** `codex login` (browser OAuth) to re-mint a token — not possible headlessly. The memory note that "laptop Codex Seat A authenticates headless over SSH" relied on SSH key auth that is **not** currently accepted from this host.

Both seats were dispatched exactly as specified (prompts saved in scratchpad `seatA_prompt.txt` / `seatB_prompt.txt`); both `codex exec` processes exited immediately with the 401 error above and produced no analysis.

---

## SEAT A — transport-NMA headline (cross-vendor witness NOT obtained)

**Requested:** independent Codex reproduction of (i) frozen external κ_pooled ≈ 0.158 matching oracle at B=0.15, (ii) sign of corr(κ, 1−λ), (iii) deployable κ beats PET / trim-and-fill / Henmi–Copas.

**Codex:** did not run (401).

**Fallback — Claude re-executed the committed scripts (SAME-vendor reproducibility, deterministic):**

- `python transport_nma/aact_kappa_freeze.py` →
  `kappa_pooled = 0.1576`, `corr(kappa_MD, 1-lambda) = +0.501` (positive), `nmin=8`, classes `[metformin, SGLT2, DPP4, GLP1, TZD, insulin, AGI]`. **Matches the frozen JSON / manuscript claim (0.158, +0.50) exactly.**
- `h2h_result.json` at **B=0.15, regime A**:
  - `registry_oracle`  dMCIW0 = **−0.1180**  WINS
  - `registry_ext0.158` dMCIW0 = **−0.1189**  WINS  ← deployable external κ tracks the oracle
  - `PET` dMCIW0 = **+0.6409**  HARMS (catastrophic, as claimed)
  - `TF` dMCIW0 = **+0.0213**  HARMS
  - `HC` dMCIW0 = **+0.0023**  tie
  - → deployable ext-κ beats PET / TF / HC; all three internal funnel models fail to correct. Reproduces §h2h / manuscript Table 3.

**Divergences found:** none — but note this is Claude re-running Claude/this-program's own deterministic code. It confirms the artifacts are internally reproducible and not stale; it does **not** provide the requested independent second-vendor witness.

---

## SEAT B — RapidMeta data-fix QA (cross-vendor witness NOT obtained)

**Requested:** Codex re-pools a random 25–30 of the ~432 apps fixed this session and confirms each displayed effect is finite and plausible.

**Codex:** did not run (401).

**Fallback — Claude ran only a crude finiteness screen (NOT a re-pool):**

- Session-changed frame = **433** `*.html` apps (git log of the last 18 commits) — consistent with the ~432 cohort.
- Grep screen of a 40-app sample for displayed `NaN / Infinity / undefined / null` inside result spans: **no genuine non-finite displayed effect surfaced.** The only matches were false positives — heterogeneity legend prose (">I² ≥ 50% or prediction interval crosses null<") and minified JS source, not numeric results.

**Important limitation:** this is a text screen, **not** the requested independent inverse-variance re-pool. It cannot confirm the displayed point estimates are *numerically correct* — only that no obvious `NaN`/`Infinity` token is rendered. The actual per-app re-pool-and-compare was the Codex job and remains **unverified by any second party.** No FLAG can be asserted or ruled out.

---

## Verdict

| Question | Answer |
|---|---|
| Did Seat A run (Codex)? | **No** — 401 revoked |
| Did Seat B run (Codex)? | **No** — 401 revoked |
| Cross-vendor confirmation obtained? | **No** (neither seat) |
| Divergences from headline numbers? | **None observed**, but only via same-vendor reproducibility (Seat A) and a crude finiteness screen (Seat B) — not independent witnessing |
| Seat-A artifacts internally reproducible? | **Yes** — κ=0.1576, corr=+0.50, ext0.158 −0.1189 vs oracle −0.1180, PET/TF/HC all fail to beat it — all reproduce exactly |

## To unblock a real cross-vendor run

1. On pc1, run **`codex login`** interactively (browser OAuth) to re-mint the `mahmood726` token — the revoked refresh token is the sole blocker; the account itself is not deleted. Then re-dispatch the two saved prompts.
2. Or restore SSH key/agent auth to `mahmo@100.80.183.43` (laptop) and/or `User@100.127.107.46` (pc2) so `codex exec` can be driven headlessly on a machine whose token is still valid.
3. Prompts are ready to re-fire verbatim: `scratchpad/seatA_prompt.txt`, `scratchpad/seatB_prompt.txt`.
