# AdaptShrink-DTA — Phase 2 report (DRAFT skeleton; numbers TBD from grids)

## Section ordering to append to REPORT_DTA.md after §5

## 6. Phase 2: broaden the field and map the design space

### 6.1 Two more standard comparators added to the field-to-beat
- `reitsma_reml` — REML small-sample-corrected bivariate (the +0.5 log det A
  penalty in the profile likelihood). Recognised small-sample correction.
- `hsroc` — Rutter-Gatsonis HSROC = the bivariate GLMM fit by the EXACT binomial
  likelihood (adaptive Laplace-centred Gauss-Hermite quadrature), as distinct
  from Reitsma's within-study normal approximation. The second standard DTA
  model. Validation: [from _phase2_verification_notes.md] — machine-precision
  integrator, matches lme4::glmer to 0.011, reaches a strictly lower exact-NLL
  than glmer's Laplace fit, corroborated by codex_main (clean) + codex_noreen
  (4/5).

The field-to-beat is now {reitsma (HC), reitsma_reml, reitsma_indep, hsroc} and
the naive sep_univariate lower bound.

### 6.2 Full grid [FILL: from dta_full_table.csv + dta_full_truthgate.json]
- grid: k in {6,10,20,40} x rho_true in {0,-0.4,-0.8} x prev in {0.1,0.3,0.5}
  x selection {none,moderate,strong} = 108 cells, 400 reps/cell.
- [FILL win/loss map: per strength, adaptshrink<reitsma fraction; robust wins]
- [FILL: where adaptshrink robustly beats reitsma; where it ties; where it loses]

### 6.3 Sparse / zero-cell axis [FILL: from dta_sparse_* if run]
- [FILL: HSROC's exact-binomial advantage on sparse cells]

### 6.4 Focus grid with HSROC: beats-both-models + k10/strong push [FILL]
- [FILL: ours_vs_field robust-beats matrix; k10_thr/strong bootstrap result]
- [FILL: deployable raw_cov per method]

### 6.5 Honest verdict — over the bar vs still a ceiling [FILL]
- [FILL: what is now bootstrap-robust; residual corners where adaptshrink does
  NOT robustly beat the field, esp. vs HSROC on sparse no-selection cells]

## Figures (make_dta_figures.py)
- fig_dta_winmap_full.png
- fig_dta_field_focus.png
- fig_dta_robust_matrix.png
