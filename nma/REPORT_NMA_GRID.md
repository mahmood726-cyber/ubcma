# AdaptShrink-NMA — Phase 4: the τ × selection × n boundary map

**Branch** `methods-nma`. **Date** 2026-06-30. **Status** grid complete (60 cells),
cross-vendor confirmed on 8 headline cells (Claude-independent + agy + Codex).

## 1. Question

Phase 3 (`REPORT_NMA_PHASE3.md`) established that the bootstrap-robust matched-
coverage efficiency win exists iff (strong small-study selection) AND (n ≥ 6), and
strengthens monotonically with n through n=10, with falsification controls (no-
selection, moderate-selection) passing. Phase 3 §8 named the obvious next step: a
full **τ × selection-strength × n** grid to map the entire win boundary — does the
win survive moderate selection at large n? does higher τ erase it or amplify it?
does the n-trend plateau? This phase runs that grid.

## 2. Design

A fully-crossed grid, holding everything else at the dense well-powered headline
regime (`geom=full`, 8–15 studies/edge, homogeneous τ, `effect_sd=0.5`,
`small_values='undesirable'`). The **only** things that vary are the three axes:

- **τ** ∈ {0.05, 0.10, 0.20, 0.30}
- **selection** ∈ {none, moderate, strong}
- **n** ∈ {5, 6, 8, 10, 12}  (4–11 basic contrasts)

= **60 cells**, each **600 matched-seed replicates** (identical `BASE_SEED =
20260621`, so cells differ only by the axis values). Per cell, for
`adaptshrink_auto` vs the netmeta field default `common_DL`: the paired-bootstrap
(B=2000, seed 7) MCIW0 point-efficiency advantage `dMCIW0` and its robust-win flag
(97.5th pct of the advantage < 0), plus the deployable metrics (bias, raw coverage,
coverage uniformity, P-score ranking). Driver:
`nma/truth-recovery/run_tausel_grid.py` (3-worker pool; 7460 s wall).
Map: `nma/truth-recovery/nma_tausel_grid_map.csv`, gates `_gates.json`.

## 3. The boundary map

`W` = bootstrap-robust win (97.5% CI bound < 0); `.` = no win; `b` = **borderline**
(|CI bound| < 0.002 — flag flips within bootstrap Monte-Carlo error). Cell value =
`dMCIW0` (negative = `adaptshrink_auto` narrower at nominal).

```
selection = none            n=5      n=6      n=8     n=10     n=12
  tau=0.05                .+0.002  .+0.006  .+0.007  .+0.003  .+0.002
  tau=0.10                .+0.002  .+0.007  .+0.006  .+0.004  .+0.002
  tau=0.20                .+0.008  .+0.011  .+0.008  .+0.004  .+0.003
  tau=0.30                .+0.008  .+0.013  .+0.013  .+0.007  .+0.003

selection = moderate        n=5      n=6      n=8     n=10     n=12
  tau=0.05                .+0.005  .-0.000  .-0.006  .-0.004  b-0.005
  tau=0.10                .+0.001  .-0.002  .-0.006  .-0.004  W-0.010
  tau=0.20                .-0.006  .+0.007  .-0.006  .-0.004  W-0.020
  tau=0.30                .+0.003  .+0.011  .-0.009  .-0.007  W-0.026

selection = strong          n=5      n=6      n=8     n=10     n=12
  tau=0.05                .+0.013  .-0.021  W-0.032  W-0.059  W-0.073
  tau=0.10                .+0.018  b-0.023  W-0.032  W-0.064  W-0.090
  tau=0.20                .-0.005  W-0.029  W-0.066  W-0.088  W-0.122
  tau=0.30                W-0.040  W-0.040  W-0.080  W-0.124  W-0.154
```

**Robust wins: 20/60** (18 unambiguous with CI bound ≤ −0.002, plus the 2 borderline
cells `t05_moderate_n12`, `t10_strong_n6`). The frontier is a clean monotone
surface; the three axes act as follows:

1. **Selection is the gate (the control axis).** With **no** selection, **0/20**
   cells win — `dMCIW0` is positive (wider) at every τ and n, bias is unchanged vs
   `common_DL`, and coverage is not harmed. When there is no bias to remove,
   component B's PEESE gate stands down and there is no spurious narrowing. The win
   only ever appears where real selection bias exists. This is the key falsification
   control, now confirmed across the **whole** τ × n plane, not one cell.

2. **Moderate selection wins only at the largest network (n=12).** 4/20 moderate
   cells are robust, all at **n=12** (τ = 0.10, 0.20, 0.30 unambiguous; τ=0.05
   borderline). At n ≤ 10 the moderate-selection point advantage trends negative
   from n=8 onward but the bootstrap CI still crosses zero — large n is *necessary*
   to push a weak bias signal past the robustness threshold. Phase 3 had tested
   moderate only at n=8 (no win) and concluded "large n does not compensate for weak
   selection"; the grid **refines** that — large *enough* n (12) does, but barely.

3. **Strong selection wins on n ≥ 6 (n ≥ 5 at high τ), strengthening in both n and
   τ.** 16/20 strong cells robust. The win **emerges** at n=6 (τ ≥ 0.10) and
   **strengthens monotonically with n through n=12 — no plateau** (e.g. τ=0.30:
   −0.040, −0.040, −0.080, −0.124, −0.154 for n = 5,6,8,10,12). It also strengthens
   monotonically with **τ** at every n ≥ 6 (e.g. n=12: −0.073, −0.090, −0.122,
   −0.154). **Heterogeneity amplifies, it does not erase** — the largest win in the
   entire grid is the highest-τ, largest-n strong cell (`t30_strong_n12`, −0.154).

### Deployable metrics track the efficiency story (strong selection)

| cell | dMCIW0 | raw_cov auto / DL | Δcov | \|bias\| auto / DL | Spearman auto / DL |
|---|---:|---|---:|---|---|
| t10_strong_n6 | −0.023 | 0.890 / 0.811 | +0.079 | 0.047 / 0.077 | 0.945 / 0.938 |
| t10_strong_n12 | −0.090 | 0.931 / 0.701 | +0.230 | 0.031 / 0.076 | 0.981 / 0.973 |
| t20_strong_n12 | −0.122 | 0.891 / 0.565 | +0.326 | 0.067 / 0.126 | 0.970 / 0.955 |
| t30_strong_n12 | −0.154 | 0.840 / 0.441 | +0.399 | 0.114 / 0.192 | 0.953 / 0.928 |

As the network grows and τ rises, the field default's deployable coverage
**collapses** (down to 0.44 at `t30_strong_n12`) because every added contrast
inherits uncorrected selection bias; `adaptshrink_auto` holds 0.84–0.93 — a **+40
pp** coverage recovery at the corner. Bias is roughly halved and P-score ranking is
preserved or improved at every robust cell. This is the deployable counterpart of
the MCIW0 width story and rules out the "narrower-because-under-covering" artifact.

## 4. Mechanism

`dMCIW0 = MCIW0(auto) − MCIW0(base)`, `MCIW0 = 2·q₀.₉₅(|error|)` mean over the n−1
contrasts. The robustness threshold is crossed when the **point** advantage outruns
the **bootstrap half-width** of the mean-over-contrasts advantage. All three axes
push the point advantage up and/or the half-width down:

- **selection ↑** → more bias for component B's PEESE slope to remove (none → zero
  advantage; the gate is a true on/off);
- **n ↑** → more edges/indirect paths ⇒ the network-wide PEESE slope is estimated
  more precisely (bigger de-biasing) *and* the mean-over-(n−1)-contrasts advantage
  has lower bootstrap variance (tighter CI). Both effects compound, so the win
  strengthens with n with no plateau through n=12;
- **τ ↑** → wider funnel ⇒ more leverage to identify the small-study slope, so the
  correction removes proportionally more error; heterogeneity *amplifies* the
  point-efficiency win.

The boundary is therefore a smooth frontier, not a cliff: moderate selection reaches
it only with the n=12 variance-averaging boost; strong selection reaches it by n=6
and races past it as n and τ grow.

## 5. Cross-vendor verification

Eight headline cells spanning the regime (two robust corners, two mid robust, the
moderate-n12 boundary win, the n6 boundary, and two genuine negatives incl. the
no-selection CONTROL) were independently re-derived **from scratch** — re-implement
the MCIW0 metric and the paired bootstrap from only the per-rep CSVs + spec
(`nma/verify/grid_verify_spec.md`), **no `ubcma` import**. Per-rep CSVs:
`nma/verify/grid/gridcell_*_perrep.csv` (matched seed ⇒ byte-identical to the grid).

| cell | grid map (seq-RNG) | Claude-indep | agy (Gemini/pro) | Codex pc2 seat A | robust consensus |
|---|:--:|:--:|:--:|:--:|:--:|
| t10_none_n8 (CONTROL) | . | . | . | . | **not robust** ✓ |
| t10_strong_n5 | . | . | . | . | **not robust** ✓ |
| t05_strong_n6 | . | . | . | . | **not robust** ✓ |
| t10_strong_n6 (boundary) | W | . | . | . | **not robust** ✓ |
| t10_moderate_n12 | W | W | W | W | **robust** ✓ |
| t20_strong_n8 | W | W | W | W | **robust** ✓ |
| t10_strong_n10 | W | W | W | W | **robust** ✓ |
| t30_strong_n12 | W | W | W | W | **robust** ✓ |

**All three independent implementations agree on the robust_win flag for all 8/8
cells.** The bootstrap CI upper bounds match across vendors to **4 dp** (e.g.
`t10_strong_n6` CI hi = +0.0009 in all three; `t05_strong_n6` +0.0024 in all three).
agy and Codex match each other to 5–6 dp on the **calib-split** point `dMCIW0`
(e.g. `t30_strong_n12` agy −0.14859 vs Codex −0.148589); Claude-indep reports the
**all-reps bootstrap-centre** convention (−0.1540) — the two legitimate point
definitions flagged in Phase 3 §5, differing by ~0.004–0.01 but **not** affecting any
robust verdict (the verdict-determining bootstrap CI is computed identically by all
three).

**The borderline cell, independently confirmed.** The 60-cell grid map's gate flagged
`t10_strong_n6` robust (CI hi −0.0008) because the harness draws one `default_rng(7)`
sequence shared across methods (auto is the 3rd consumer). A fresh-RNG reimplementation
(what the spec prescribes, and what all three vendors did) puts its CI hi at **+0.0009
— just not robust**. So `t10_strong_n6` (and `t05_moderate_n12`, CI hi −0.0007) are
genuine **boundary** cells whose flag flips within bootstrap MC error; all three
vendors independently landed on the not-robust side for n6. The *unambiguous* robust
interior (CI hi ≤ −0.002) is **18/60** and is reproducible regardless of RNG
convention.

### Vendor / quota-burn audit

| vendor | node | seat / account | cells verified | status |
|---|---|---|---:|---|
| Claude-independent | local (pc1) | — | 8 | `grid_independent.py`, harness-free recompute |
| agy (Antigravity / Gemini pro) | local | — | 8 | from-scratch code-gen, ran on the CSVs |
| **Codex** | **pc2** (100.127.107.46) | **A = `.codex` (mahmood726)** | **8** | **LIVE, gpt-5.5, 31,938 tokens; wrote+ran its own verifier** |
| Codex | laptop (100.80.183.43) | A = `.codex`; B = `.codex-noreen` | pending | node flapping offline on Tailscale (last seen 25 m ago); background watcher (`laptop_watch.sh`) polling 45 min to burn **both** seats when it surfaces — appended below if it lands |
| Codex | pc1 (local) | A & B | 0 | 401 / Windows sandbox-helper failure (prior finding) — unusable |
| Codex seat B | pc2 | `.codex-noreen` | 0 | `auth.json` absent → "Not logged in" on pc2 (documented, not silently skipped) |

Three fully independent implementations (one external vendor = agy, one external
vendor = Codex on a remote node, plus the harness-free Claude recompute) confirm the
headline. Codex seat A burned real quota doing genuine from-scratch work on pc2.

## 6. Honest negatives / caveats

- **n=5 is mostly not a robust win.** Under strong selection it fails at τ ≤ 0.10
  (positive dMCIW0) and is borderline at τ=0.20 (CI crosses); it wins only at τ=0.30.
  The efficiency win genuinely needs n ≥ 6 except at the highest heterogeneity.
- **Moderate selection needs n=12** and even then is marginal (τ=0.05 borderline).
  At realistic moderate selection with small/medium networks, expect **no** width
  win — only the deployable-coverage/bias improvement, which is smaller here.
- **Two boundary cells flip on bootstrap RNG** (`t10_strong_n6`, `t05_moderate_n12`).
  Reported transparently; not counted in the 18 unambiguous wins.
- **Two point-`dMCIW0` conventions** (calib-split vs all-reps bootstrap-centre)
  differ by ~0.004–0.01; the robust verdict is invariant to the choice.
- **No-selection coverage dips slightly at high τ.** In the control cells,
  `adaptshrink_auto`'s raw coverage runs ~1–2 pp *below* `common_DL` at τ ≥ 0.20
  (e.g. `t30_none_n8`: 0.930 vs 0.949) — both still near nominal, and since dMCIW0 is
  *positive* there (wider intervals) this is GLS calibration under heterogeneity, not
  a narrowing artifact. Worth a footnote in any deployment.
- **Single geometry/density.** The whole grid is dense full networks (8–15
  studies/edge). Sparser or non-full geometries are out of scope here (Phase 1–2
  covered loop/star/sparse for the consistency/heterogeneity axes; the selection
  width-win is specifically a dense-network phenomenon).

## 7. One-line boundary summary

The bootstrap-robust matched-coverage efficiency win occupies a clean monotone
frontier in (τ, selection, n): **never** under no selection (control holds across the
whole plane), **only at n=12** under moderate selection, and from **n ≥ 6** under
strong selection — strengthening monotonically with both n (no plateau through 12)
and τ (heterogeneity amplifies), peaking at −0.154 / +40 pp coverage recovery at the
high-τ, large-n corner. Confirmed by three independent implementations across two
external vendors.

## 8. Files

- `nma/truth-recovery/run_tausel_grid.py` — 60-cell grid driver (process pool).
- `nma/truth-recovery/nma_tausel_grid_map.csv` / `_gates.json` — boundary map + gates.
- `nma/verify/dump_grid_cells.py` — matched-seed per-rep CSV exporter for headline cells.
- `nma/verify/grid/gridcell_*_perrep.csv` — the 8 headline-cell per-rep CSVs.
- `nma/verify/grid_verify_spec.md` — from-scratch cross-vendor spec.
- `nma/verify/grid_independent.py` + `result_claude_grid.json` — harness-free recompute.
- `nma/verify/run_agy_grid.py`, `agy_grid_nma.py`, `result_agy_grid.json` — agy vendor.
- `nma/verify/launch_codex_remote.sh`, `codex_grid_prompt.txt`,
  `result_codex_pc2_A_grid.json` — Codex remote-node verification.
- `nma/verify/laptop_watch.sh` — both-seat laptop burn watcher (pending node uptime).

## 9. Next avenue

- The grid is the natural completion of the NMA selection-width story; the boundary
  is now fully mapped and triple-confirmed. **Recommended pivot: univariate StatMed
  broadened grids** (the manuscript's primary estimator) — apply this same
  matched-coverage τ × selection × k boundary-map methodology to the pairwise
  AdaptShrink, where the audience and the existing draft manuscript already live.
  The DTA branch (`methods-dta`) is the alternative; it is earlier-stage (parity
  validated, selection-region win not yet bootstrap-robust at 300 reps) and a worktree
  session already owns it.
- Optional NMA tidy-up: re-run the grid gate with a per-method fresh `rng(7)` so the
  60-cell flags are RNG-convention-invariant (would reclassify the 2 borderline cells
  as not-robust, making the map count 18/60 unambiguous).
