# Field-bakeoff dropna selection artifact — resolution note (2026-07-06)

## What was wrong
`bootstrap_pairwise` (field_bakeoff.py) formed the paired-bootstrap rep set for a
cell with `gg.pivot_table(index="rep", columns="method", values="abserr").dropna()`
— the **intersection over ALL methods**. A replication was used only if *every*
method converged on it, and the whole cell was skipped when that intersection fell
below 16 reps.

Because low-convergence comparators (`p_uniform_star`, `p_curve`, `vevea_hedges`)
fail on null / small-k cells, they deleted reps — and entire cells — from
AdaptShrink's domination tally. Crucially, these are the *same* methods that
`field_domination` then **excludes** via `min_conv >= 0.8`: a comparator too
unreliable to be *judged* was nonetheless deleting the reps used to judge the
*reliable* comparators. That is a selection artifact biasing both numerator and
denominator.

Diagnostic (committed per-rep CSVs): 3 continuous + 6 log-OR cells were dropped
entirely; in all 9 the headline `adaptshrink_auto` converged on all 40 reps, and 7
of 9 were μ=0 null cells where p-value-based methods legitimately cannot run.

## The fix
`bootstrap_pairwise(..., aggregation=...)`:
- **`"pairwise"` (new default, corrected):** each headline-vs-comparator paired
  bootstrap uses the reps where *both* that comparator and the headline converged;
  a comparator is judged if it shares ≥16 paired reps with the headline. No third
  method can delete a comparison or a cell.
- **`"global"` (legacy, retained):** the original all-methods `dropna` intersection.
  Kept so the original headline is exactly reproducible. Both a `min_conv`-first
  variant and the pairwise variant give identical domination counts, so the fix is
  not sensitive to the specific clean-aggregation choice.

## Numbers (adaptshrink_auto), recomputed on the committed per-rep CSVs
| grid | legacy `global` (published) | corrected `pairwise` |
|---|---|---|
| continuous (c2) | **31/51**, 6 losses | **36/54**, 4 losses |
| log-OR (l2) | **20/30**, 9 losses | **23/36**, 12 losses |

Legacy mode reproduces the committed `field2_c2_summary.json` / `field2_l2_summary.json`
(31/51 loss6; 20/30 loss9) to the exact count. Full variant table and τ-strata are in
`C:\Projects\adaptshrink-dropna-resolution-2026-07-06.md`.

## Conclusion
The **domination conclusion survives**: `adaptshrink_auto` still leads every variant
on both grids and keeps the fewest losses on continuous. Continuous dominance
*strengthens* (60.8% → 66.7%); log-OR stays a clear win (66.7% → 63.9%) with more
loss cells (9 → 12). The manuscript should be **restated to 36/54 & 23/36**; the
old numbers remain reproducible via `aggregation="global"`.

Regression test: `test_field_bakeoff.py::test_dropna_selection_artifact`.
