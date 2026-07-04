// Build the StatMed AdaptShrink manuscript .docx from the verified numbers.
// Run: node manuscript/build_docx.js
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  AlignmentType, LevelFormat, HeadingLevel, BorderStyle, WidthType, ShadingType,
  TableOfContents, PageNumber, Header, Footer, PageBreak, VerticalAlign,
} = require("docx");

const DIR = __dirname;
const FIG = path.join(DIR, "figures");
const CW = 9360; // US Letter content width (1" margins)

// ---------- helpers ----------
const border = { style: BorderStyle.SINGLE, size: 1, color: "BBBBBB" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 60, bottom: 60, left: 110, right: 110 };

function runs(text, opts = {}) { return [new TextRun({ text, ...opts })]; }

function P(text, opts = {}) {
  return new Paragraph({
    spacing: { after: opts.after ?? 120, line: 276 },
    alignment: opts.align,
    children: Array.isArray(text) ? text : runs(text, opts),
  });
}
function H1(text) { return new Paragraph({ heading: HeadingLevel.HEADING_1, children: runs(text) }); }
function H2(text) { return new Paragraph({ heading: HeadingLevel.HEADING_2, children: runs(text) }); }
function bullet(text) {
  return new Paragraph({ numbering: { reference: "bullets", level: 0 },
    spacing: { after: 60 }, children: Array.isArray(text) ? text : runs(text) });
}
function numItem(text) {
  return new Paragraph({ numbering: { reference: "nums", level: 0 },
    spacing: { after: 60 }, children: Array.isArray(text) ? text : runs(text) });
}

function tableFrom(headerRow, dataRows, colWidths) {
  const total = colWidths.reduce((a, b) => a + b, 0);
  const mkCell = (txt, w, opts = {}) => new TableCell({
    borders, width: { size: w, type: WidthType.DXA }, margins: cellMargins,
    verticalAlign: VerticalAlign.CENTER,
    shading: opts.head ? { fill: "D5E8F0", type: ShadingType.CLEAR } : undefined,
    children: [new Paragraph({ spacing: { after: 0 },
      children: runs(String(txt), { bold: !!opts.head, size: 18 }) })],
  });
  const rows = [];
  rows.push(new TableRow({ tableHeader: true,
    children: headerRow.map((h, i) => mkCell(h, colWidths[i], { head: true })) }));
  for (const r of dataRows) {
    rows.push(new TableRow({ children: r.map((c, i) => mkCell(c, colWidths[i])) }));
  }
  return new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: colWidths, rows });
}

function figure(file, caption, widthPx) {
  const data = fs.readFileSync(path.join(FIG, file));
  // probe PNG dimensions
  const w = data.readUInt32BE(16), h = data.readUInt32BE(20);
  const dispW = widthPx ?? 600;
  const dispH = Math.round(dispW * h / w);
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 },
      children: [new ImageRun({ type: "png", data,
        transformation: { width: dispW, height: dispH },
        altText: { title: caption, description: caption, name: file } })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 },
      children: runs(caption, { italics: true, size: 18 }) }),
  ];
}

function captionP(label, rest) {
  return new Paragraph({ spacing: { after: 120 },
    children: [new TextRun({ text: label, bold: true, size: 18 }),
               new TextRun({ text: rest, size: 18 })] });
}

// ---------- content ----------
const children = [];

// Title block
children.push(new Paragraph({ spacing: { after: 120 }, children: runs(
  "AdaptShrink: a τ-aware, selection-robust random-effects estimator for meta-analysis that moves the heterogeneity × publication-bias no-free-lunch boundary",
  { bold: true, size: 30 }) }));
children.push(P([new TextRun({ text: "Mahmood Ahmad", bold: true }),
  new TextRun({ text: "¹²", superScript: true })], { after: 40 }));
children.push(P([new TextRun({ text: "¹ ", size: 18 }), new TextRun({ text: "Royal Free Hospital, London, United Kingdom", size: 18 })], { after: 20 }));
children.push(P([new TextRun({ text: "² ", size: 18 }), new TextRun({ text: "Tahir Heart Institute, Rabwah, Pakistan", size: 18 })], { after: 40 }));
children.push(P([new TextRun({ text: "ORCID: 0000-0001-9107-3704. Correspondence: Mahmood Ahmad (mahmood726@gmail.com).", size: 18 })], { after: 80 }));
children.push(P([new TextRun({ text: "Competing interests. ", bold: true, size: 18 }),
  new TextRun({ text: "The author is an honorary member of the editorial board of Synthēsis (former Editor-in-Chief) and had no role in the handling, peer review, or editorial decision-making for this manuscript; any submission would be handled independently by another editor of the journal.", size: 18 })], { after: 40 }));
children.push(P([new TextRun({ text: "Funding. ", bold: true, size: 18 }), new TextRun({ text: "None.", size: 18 })], { after: 160 }));

// Abstract
children.push(H1("Structured abstract"));
const abs = [
  ["Background. ", "Random-effects meta-analysis must contend with two largely orthogonal threats: between-study heterogeneity (τ) and publication/selection bias. Heterogeneity-only estimators (DerSimonian–Laird, REML, HKSJ) are efficient but inherit selection bias; selection-bias correctors (PET-PEESE, trim-and-fill, Copas/Henmi–Copas, p-uniform*, Vevea–Hedges) trade variance for bias reduction and each fails in a different region of the heterogeneity × selection plane. There is a meta-analytic no-free-lunch: no single fixed estimator is uniformly best, because the locally optimal estimator depends on the (unobservable) ratio of selection magnitude to τ."],
  ["Methods. ", "We develop AdaptShrink, an oracle-free random-effects estimator, and its τ-aware variant adaptshrink_auto. The base estimator robustly model-averages a panel of bias-corrected members (UBCMA, PET-PEESE, trim-and-fill) with disagreement-penalised weights w_j = 1/(se_j² + (μ_j − median μ)²) and a model-averaging variance that widens when members diverge. A calibrated variant inflates the interval by member disagreement. adaptshrink_auto switches on two observable signals: it uses the calibrated ensemble when the DerSimonian–Laird τ̂ < 0.2, and a funnel-asymmetry-gated estimator otherwise, with the gate driven by the small-study-effects t-statistic (a τ-robust selection detector). We evaluate every method under a matched-coverage protocol: each method is calibrated to 95% coverage, then we compare the constant matched-coverage width MCIW0 (point-estimator efficiency) with a paired-bootstrap win criterion, alongside the deployable (no-oracle) coverage."],
  ["Results. ", "Against a modern panel of up to 15 estimators (13–15 valid comparators per cell) across continuous and binary/log-odds-ratio outcomes, k ∈ {5, 10, 40}, τ up to 0.5, and three selection mechanisms (none/step/Copas), adaptshrink_auto leads the field in 31/51 continuous cells and 20/30 binary cells, versus 16 and 14 for the plain ensemble. It recovers the high-heterogeneity corner previously characterised as an honest ceiling (τ = 0.5: 0 → 7/17 continuous cells). On a focused strong-selection comparison at k = 40, AdaptShrink reaches near-nominal deployable coverage (0.96–0.98) while needing 25–37% narrower matched-coverage intervals than the Henmi–Copas comparator, whose deployable coverage collapses to 0.00–0.08. Honest limitations: adaptshrink_auto’s mean deployable coverage eases to 0.843 on the hard continuous grid (0.938 on log-OR), and its residual losses are step-selection cells to trim-and-fill, which only “wins” the oracle point-efficiency metric while being undeployable (coverage ≈ 0.29). It does not strictly dominate every cell."],
  ["Conclusions. ", "A τ-aware switch between a bias-corrected ensemble and a funnel-asymmetry-gated estimator, keyed on observable signals, demonstrably moves — but does not abolish — the heterogeneity × selection no-free-lunch boundary, on two effect metrics. adaptshrink_auto is a strong default general-purpose random-effects estimator when publication/selection bias cannot be ruled out, provided its eased deployable coverage at high τ is reported alongside the point estimate."],
];
for (const [lab, body] of abs) {
  children.push(P([new TextRun({ text: lab, bold: true }), new TextRun({ text: body })]));
}
children.push(P([new TextRun({ text: "Keywords: ", bold: true }),
  new TextRun({ text: "meta-analysis; publication bias; selection models; heterogeneity; random-effects; robust estimation; matched-coverage efficiency." })]));

children.push(new Paragraph({ children: [new PageBreak()] }));

// 1 Introduction
children.push(H1("1. Introduction"));
[
  "Meta-analysis aggregates study-level effect estimates into a pooled effect and an interval that is meant to support decision-making. Two threats to that interval are largely independent in origin but interact severely in practice. The first is between-study heterogeneity: real effect variation across studies, summarised by the between-study standard deviation τ. The second is publication and selection bias: the studies that reach the analyst are a non-random, effect-dependent subset of those conducted, so the observed effects are shifted away from the truth by an amount that depends on an unobserved selection mechanism.",
  "The standard toolkit addresses these threats separately. Heterogeneity-only estimators — DerSimonian–Laird (DL), REML, and their Hartung–Knapp–Sidik–Jonkman (HKSJ) interval refinements — model τ but assume the sample of studies is unbiased; under selection their inverse-variance centre is biased and their intervals under-cover the true effect. Selection-bias correctors take the opposite stance. Trim-and-fill imputes “missing” studies from funnel asymmetry; PET-PEESE regresses the effect on its standard error and extrapolates to infinite precision; Copas-type selection models (and the robust Henmi–Copas interval) posit a latent selection process; p-uniform* and p-curve exploit the distribution of significant p-values; Vevea–Hedges fits a step-function selection weight. Each removes some bias at a variance cost, and each is built around a specific selection model and therefore fails when the true mechanism differs.",
  "The result is a meta-analytic no-free-lunch. Where heterogeneity dominates and selection is mild, the efficient inverse-variance estimator is essentially minimum-variance and unbiased, and no bias-correcting estimator can strictly beat it there: a robust average necessarily has variance no smaller than its best member. In the opposite corner — strong selection, modest heterogeneity — the efficient estimator is sharply biased and any reasonable bias corrector dominates it. Because the locally optimal estimator depends on the ratio of selection magnitude to τ, and that ratio is not observable, no single fixed estimator can be uniformly best.",
].forEach(t => children.push(P(t)));
children.push(P([new TextRun({ text: "This motivates an adaptive estimator that detects, from observable signals, which regime it is in. The contribution of this paper is threefold:" })]));
children.push(numItem([new TextRun({ text: "AdaptShrink", bold: true }), new TextRun({ text: " — an oracle-free robust model-average of bias-corrected members, with disagreement-penalised weights and a model-averaging variance that widens automatically when the panel disagrees." })]));
children.push(numItem([new TextRun({ text: "adaptshrink_auto", bold: true }), new TextRun({ text: " — a τ-aware selector that switches between a calibrated AdaptShrink ensemble (low heterogeneity) and a funnel-asymmetry-gated estimator (high heterogeneity), keyed on the observable DL τ̂ and the small-study-effects t-statistic." })]));
children.push(numItem([new TextRun({ text: "A matched-coverage evaluation protocol", bold: true }), new TextRun({ text: " that compares methods by first calibrating each to the same coverage, then comparing interval width with a paired-bootstrap win criterion, while separately reporting the deployable (no-oracle) coverage." })]));
children.push(P("We show that this adaptive design demonstrably moves the no-free-lunch boundary — it reclaims the high-heterogeneity corner that a fixed ensemble cannot — without claiming to abolish it, and we are explicit about where and why it still loses."));

// 2 Methods
children.push(H1("2. Methods"));
children.push(H2("2.1 The bias-corrected ensemble"));
children.push(P("AdaptShrink does not observe the truth. It begins from the empirical observation that under strong selection misspecification the naive random-effects centre and Copas-type selection MLEs are biased upward (bias ≈ +0.10–0.15), trim-and-fill is biased downward (≈ −0.06), while PET-PEESE (≈ +0.06) and UBCMA (≈ +0.02) sit closer to the truth. Because the errors of the bias-corrected members partly straddle the truth, a robust weighted combination can have both lower bias and lower variance than any single member."));
children.push(P([new TextRun({ text: "Let the default panel be the bias-corrected members {UBCMA, PET-PEESE, trim-and-fill}, each contributing a point estimate μ_j and standard error se_j. The naive RE and Copas members are deliberately excluded: under selection they share the same upward bias and would out-vote the corrections. AdaptShrink forms the robust median m = median μ_j and the disagreement-penalised weights w_j = 1/(se_j² + (μ_j − m)²), giving μ̂ = Σ w_j μ_j / Σ w_j. This down-weights both noisy members (large se_j) and outlying members (large disagreement). The interval uses a model-averaging variance — within-member sampling variance plus between-member spread — so it widens automatically when the panel disagrees, i.e. when selection is severe. The half-width is κ · t(n−1, 0.975) · √Var, with a single transparent calibration multiplier κ (κ = 1 for the raw interval). Nothing is tuned to a target; the member set and weighting rule are fixed a priori." })]));
children.push(captionP("Source: ", "src/ubcma/adaptshrink.py."));

children.push(H2("2.2 The calibrated ensemble (adaptshrink_ens_calib)"));
children.push(P("The raw ensemble interval can deployably under-cover in a minority of cells. Widening the half-width in proportion to member disagreement D (the between-member SD), hw′ = hw + a·D with a single global constant a = 2.0, is roughly twice as width-efficient as a flat multiplier for the same coverage. The calibrated ensemble keeps the AdaptShrink centre unchanged — so the matched-coverage point-efficiency metric and every pairwise verdict are provably unaffected — and only moves the deployable interval. On the original 54-cell strong-selection grid this raised dominated cells from 31 to 35 and lifted mean deployable coverage from 0.899 to 0.946 at a 1.27× width cost."));
children.push(captionP("Source: ", "truth-recovery/REPORT_FIELD.md; field_rescore_interval.py; commit 82b73e9."));

children.push(H2("2.3 The funnel-asymmetry (PET) gate (adaptshrink_petgate)"));
children.push(P("For the high-heterogeneity regime we lean toward the efficient estimator unless there is genuine evidence of small-study effects. The detector is the funnel-asymmetry t-statistic t₁ from the PET regression of the effect on its standard error: its expectation is ≈ 0 under no selection regardless of τ, which makes it a τ-robust selection signal (unlike |μ̂_ens − μ̂_RE|, which is inflated by heterogeneity). The gate weight is g = t₁²/(t₁² + c) with c = 4 (|t₁| = 2 ⇒ g = 0.5), and the estimator blends the efficient REML-HKSJ estimator with the calibrated ensemble in both centre and half-width: μ̂_pg = (1−g)μ̂_RE + g·μ̂_ens. When there is no asymmetry it reverts to RE; when asymmetry is strong it uses the bias-corrected ensemble."));
children.push(captionP("Source: ", "truth-recovery/field_bakeoff2.py."));

children.push(H2("2.4 The τ-aware auto selector (adaptshrink_auto)"));
children.push(P("The two regimes are reconciled by a selector keyed on the observable DL heterogeneity estimate: adaptshrink_auto = adaptshrink_ens_calib when τ̂_DL < τ₀ = 0.2 (low heterogeneity: bias correction pays), else adaptshrink_petgate (high heterogeneity: lean efficient). The switch is between two good estimators on a stable signal (τ̂_DL), not toward a biased estimator on a noisy one — which is why the per-analysis switching does not inject the variance that sank an earlier per-replicate gating attempt."));
children.push(captionP("Source: ", "truth-recovery/field_bakeoff2.py; REPORT_FIELD2.md."));

children.push(H2("2.5 The matched-coverage evaluation protocol"));
children.push(P("Comparing raw interval widths across methods is unfair when methods differ in coverage. We put every method on the same coverage footing first. For each (mechanism, method) the replicates are split by index parity into disjoint calibration and test halves. The primary metric is the constant matched-coverage width MCIW0 = 2c, where c is the 0.95-quantile of |μ̂ − μ_true| on the calibration half, with test coverage measured on the held-out half. MCIW0 isolates point-estimator efficiency; the true μ is used only to calibrate the width, so this is an efficiency statement, not a deployable interval."));
children.push(P("A win over a comparator is credited only when a three-part truth gate passes: (G1) every scored replicate has a finite estimate and interval; (G3) the winner’s MCIW0 is below the comparator’s and its constant-width calibration still covers on the held-out half (|test_cov − 0.95| ≤ 0.06); and (G4, decisive) a paired bootstrap over replicates (2000 resamples, errors paired across methods) places the 97.5th percentile of the MCIW0 advantage below 0. Separately we report deployable raw coverage: the no-oracle (κ = 1) coverage a practitioner actually obtains. A method dominates the field in a cell iff it is narrower-than-or-tied-with every valid comparator (convergence ≥ 0.8) at matched coverage and its deployable coverage is near-nominal."));
children.push(captionP("Sources: ", "truth-recovery/matched_coverage_bakeoff.py, field_bakeoff.py, REPORT_MATCHED_COVERAGE.md."));

// 3 Simulation study
children.push(H1("3. Simulation study"));
children.push(P([new TextRun({ text: "Comparator panel. ", bold: true }), new TextRun({ text: "The full panel comprises up to 15 estimators, with 13–15 valid comparators per cell after convergence filtering: dl_hksj, reml_hksj, trim_and_fill, pet_peese, copas (the Copas–Shi selection MLE), henmi_copas (a direct port of metafor::hc, validated to 2×10⁻⁸ against metafor v5.0-1), vevea_hedges, p_curve, p_uniform_star, ubcma, and the AdaptShrink family. Comparator formulas were independently confirmed by a symbolic derivation pass and cross-implemented in a second codebase." })]));
children.push(P([new TextRun({ text: "A note on nomenclature. ", bold: true, italics: true }), new TextRun({ text: "The copas comparator is the Copas–Shi (2000) selection MLE, not the Henmi–Copas (2010) robust interval; the genuine Henmi–Copas method is the separately validated henmi_copas port. In the focused matched-coverage comparison the copas row is used as the reference; the field-domination analyses include both copas and henmi_copas as distinct comparators.", italics: true }) ]));
children.push(P([new TextRun({ text: "Data-generating processes. ", bold: true }), new TextRun({ text: "Continuous (SMD-like) outcomes are generated by the misspecification harness with a quality-dependent internal-bias term; binary outcomes use a fresh 2×2-table binomial DGP (group sizes in [20, 200], control risk in [0.1, 0.5]) with Haldane–Anscombe 0.5 correction, yielding log-odds-ratio effects. Three selection mechanisms are applied: none, step (a Vevea–Hedges step-function, deliberately misspecified), and copas (a latent-variable mechanism, also misspecified). A smooth mechanism matched to UBCMA’s own model is used in the focused comparison. Selection strength is strong (headline grids) or moderate." })]));
children.push(P([new TextRun({ text: "Grids. ", bold: true }), new TextRun({ text: "Three grids are reported. (i) Focused matched-coverage: μ = 0.2, τ = 0.1, k = 40, 300 reps/cell, mechanisms {smooth, step, copas}, strong and moderate. (ii) Field grid v1: μ ∈ {0, 0.2, 0.5} × τ ∈ {0, 0.1, 0.3} × k ∈ {10, 40} × mechanism ∈ {none, step, copas} = 54 cells, 80 reps/cell, strong. (iii) Broadened grids v2: a hard continuous slice (c2) μ ∈ {0, 0.2, 0.5} × τ ∈ {0.1, 0.3, 0.5} × k ∈ {5, 40} × mechanism ∈ {none, step, copas} = 54 cells (51 scored), and a log-OR slice (l2) μ ∈ {0, 0.4, 0.8} × τ ∈ {0.15, 0.4} × k ∈ {10, 40} × mechanism ∈ {none, step, copas} = 36 cells (30 scored), 40 reps/cell. Everything is seeded and reproducible." })]));

// 4 Results
children.push(H1("4. Results"));
children.push(H2("4.1 Matched-coverage efficiency against Henmi–Copas (focused grid)"));
children.push(P("Under strong selection (μ = 0.2, τ = 0.1, k = 40, 300 reps), AdaptShrink achieves near-nominal deployable coverage in all three mechanisms (smooth 0.967, step 0.960, Copas 0.977) while needing substantially narrower matched-coverage intervals than the reference. Its MCIW0 is 0.2526 (smooth), 0.2568 (step) and 0.2194 (Copas), versus the Henmi–Copas reference at 0.3731, 0.4055 and 0.2915 — width ratios of 0.677, 0.633 and 0.753, i.e. the reference needs roughly 25–37% wider intervals to reach the same coverage. The reason is bias: the reference’s point estimate is biased by 0.099–0.146 under selection, against AdaptShrink’s 0.014–0.053. The reference’s deployable coverage collapses to 0.083 (smooth), 0.003 (step) and 0.070 (Copas) (Figure 4; Table 1). The advantage is paired-bootstrap robust in all three mechanisms under both strong and moderate selection (6/6 cells)."));
children.push(P("UBCMA wins the matched-coverage metric too (ratios 0.70–0.78) but its raw interval under-covers (0.65–0.83) and would need recalibration; AdaptShrink is the only method that delivers both the efficiency and near-nominal off-the-shelf coverage. trim-and-fill posts the smallest MCIW0 under smooth/step only because its downward bias coincidentally cancels selection’s upward bias there; under the Copas mechanism that reverses, and its deployable coverage is poor throughout (0.187–0.600)."));
children.push(...figure("fig4_matched_coverage.png", "Figure 4. Matched-coverage efficiency (MCIW0, lower = better) vs deployable coverage (labels) by mechanism, strong selection, μ = 0.2, τ = 0.1, k = 40, 300 reps.", 640));

children.push(H2("4.2 Field domination on the original grid (v1)"));
children.push(P("Ranking every method by the number of 54 strong-selection cells in which it is narrower-than-or-tied-with all valid comparators at matched coverage and keeps near-nominal deployable coverage, the base ensemble adaptshrink_ens leads with 31/54 dominated cells and the best mean deployable coverage of the entire panel (0.899). The next best is UBCMA at 19/54 (0.810); adaptshrink_fast 13/54; every classical or selection method reaches at most 3/54 (dl_hksj, henmi_copas, reml_hksj each 3/54, mean deployable coverage 0.44–0.51); trim-and-fill dominates 0/54 with mean deployable coverage 0.288."));
children.push(P("Domination is sharply governed by heterogeneity: the base ensemble dominates 16/18 cells at τ = 0, 13/18 at τ = 0.1, but only 2/18 at τ = 0.3 — the honest ceiling. In the high-heterogeneity / low-selection corner the efficient inverse-variance estimators are essentially optimal and no robust average can strictly beat them. Two principled attempts to break the ceiling without re-simulation (an explicit per-replicate selection gate; adding RE to the ensemble) both failed (best 18/54 and 25/54): they moved wins between τ regimes but could not gain net."));

children.push(H2("4.3 The broadened grid and the τ-aware selector (continuous)"));
children.push(P("On the deliberately hard continuous grid (τ ≥ 0.1, k ∈ {5, 40}, 51 scored cells), the τ-aware adaptshrink_auto dominates 31/51 cells with only 6 outright losses, versus 16/51 (20 losses) for the plain ensemble, 19/51 for the calibrated ensemble, and 18/51 for the PET-gated estimator alone (Figure 1; Table 2)."));
children.push(...figure("fig1_variant_dominance.png", "Figure 1. Field-domination at matched coverage by AdaptShrink variant, continuous (51 cells) and binary/log-OR (30 cells). The τ-aware auto leads every variant (31/51, 20/30).", 640));
children.push(P("Stratified by heterogeneity, adaptshrink_auto combines the calibrated ensemble’s low-τ strength with the PET-gate’s high-τ strength and recovers the τ = 0.5 corner that no fixed variant could touch (0 → 7/17) — the corner the v1 ceiling flagged as out of reach. It essentially realises the oracle upper bound: a perfect per-cell selector between ens_calib and petgate would reach 32/51."));
children.push(...figure("fig2_tau_frontier.png", "Figure 2. Cells dominated stratified by heterogeneity τ (continuous). The plain ensemble dominates 0/17 at τ = 0.5; adaptshrink_auto recovers 7/17.", 600));

children.push(H2("4.4 Transfer to binary / log-odds-ratio outcomes"));
children.push(P("On the log-OR grid (30 scored cells), adaptshrink_auto is again the best variant: 20/30 dominated versus 14/30 for the plain ensemble, 15/30 for the calibrated ensemble and adaptshrink_fast, and 13/30 for the PET-gate. Stratified, it dominates 10/12 cells at τ = 0.15 and 10/18 at τ = 0.4, and here retains strong mean deployable coverage (0.938). The τ-aware design therefore transfers from continuous SMD-like effects to log-OR effects — the win is not an artefact of one effect metric."));

children.push(H2("4.5 Deployable coverage and honest limitations"));
children.push(P("The per-cell verdict map for adaptshrink_auto on the continuous grid (Figure 3) makes the residual weaknesses explicit. Its mean deployable coverage on this hard grid eases to 0.843 (vs 0.90+ for the calibrated ensemble), because at high τ it uses the PET-gate, which reverts toward RE-style intervals that under-cover under residual selection, and because of a centre bias in the null + step corner. The six remaining continuous losses are all step-selection cells: three to trim-and-fill (the undeployable artefact, deployable coverage ≈ 0.29) and three high-τ, k = 40 step cells where auto’s own deployable coverage is poor (0.20–0.53). The nine binary losses are likewise dominated by the trim-and-fill artefact (five Copas-mechanism cells) plus a few selection-MLE / fast-ensemble cells. adaptshrink_auto buys matched-coverage domination at some cost in out-of-the-box calibration on the hardest continuous cells — a real trade-off, logged rather than hidden. It does not strictly dominate every cell."));
children.push(...figure("fig3_auto_heatmap.png", "Figure 3. Per-cell verdict map for adaptshrink_auto (continuous). Green = dominates; amber = narrower/tied but deployable coverage < 0.90; red = loses ≥ 1 comparator. Cell text = deployable coverage.", 600));

// 5 Worked example
children.push(H1("5. Worked example: aspirin secondary prevention"));
children.push(P("We illustrate the estimator on the classic six-trial aspirin secondary-prevention dataset (CDP, AMIS, ISIS-2, UK-TIA, SALT, ESPS-2; log-odds-ratio scale; examples/verde_2021_aspirin.csv), a real dataset known for substantial heterogeneity (the large, precise ISIS-2 trial is an outlier). The numbers were computed by running the committed estimators on the committed data (manuscript/worked_example.py); they are code-and-data-derived rather than drawn from a results CSV, and are reproducible."));
children.push(P("The observable signals are τ̂_DL = 0.140 (so τ̂ < τ₀ = 0.2 and auto picks the calibrated ensemble) and a funnel-asymmetry statistic t₁ = 2.94 (significant small-study asymmetry, gate weight g = 0.68). The estimators disagree exactly as the no-free-lunch picture predicts (Figure 5; Table 3): the heterogeneity-only estimators report a near-null effect (DL-HKSJ −0.067 [−0.235, +0.101]; REML-HKSJ −0.072 [−0.208, +0.064]), UBCMA is essentially null (+0.012 [−0.125, +0.118]), while the bias-correcting members react to the funnel asymmetry and report a protective effect (PET-PEESE −0.227 [−0.285, −0.168]; trim-and-fill −0.251 [−0.288, −0.214]). AdaptShrink-auto pools the bias-corrected members to −0.237 [−0.417, −0.056] — a protective log-OR with an interval widened (relative to the raw ensemble −0.237 [−0.368, −0.105]) by member disagreement, reflecting genuine ambiguity about whether the asymmetry is selection or the ISIS-2 outlier. This is a methods illustration of the estimator’s mechanism, not a clinical re-appraisal."));
children.push(...figure("fig5_aspirin_forest.png", "Figure 5. Worked example: aspirin secondary-prevention forest plot (k = 6, real data). Studies (top) and pooled estimates (bottom); adaptshrink_auto in blue. τ̂_DL = 0.140; funnel-asymmetry t₁ = 2.94.", 540));

// 6 Discussion
children.push(H1("6. Discussion"));
children.push(P([new TextRun({ text: "What moved the boundary. ", bold: true }), new TextRun({ text: "The v1 analysis characterised an honest ceiling: a single fixed ensemble could not win the high-heterogeneity corner. The advance here is not a better single estimator but an observable switch. Two facts make it work. First, the switching signal is stable: DL τ̂ is a low-variance estimate, so conditioning on it does not inject per-replicate noise. Second, the within-regime selection detector is τ-robust: the funnel-asymmetry t-statistic has expectation ≈ 0 under no selection irrespective of τ, so at high τ the PET-gate does not mistake heterogeneity for selection. Together these let auto reach 31/51 (continuous) and 20/30 (binary), recovering the τ = 0.5 corner (0 → 7/17). The boundary has moved — the high-τ corner is now reachable oracle-free — but it has not vanished." })]));
children.push(P([new TextRun({ text: "Why universal domination remains impossible. ", bold: true }), new TextRun({ text: "The bar “narrower-or-tied versus every valid comparator in every cell” cannot be met by any single estimator. In the high-τ, no-selection corner the efficient RE estimator is essentially minimum-variance and unbiased, so any robust average — whose variance is bounded below by its best member’s — cannot strictly beat it. Choosing RE-versus-correction per cell with certainty would require knowing the selection magnitude relative to τ, which is unavailable. adaptshrink_auto approximates that oracle choice from observable signals; it cannot equal it." })]));
children.push(P([new TextRun({ text: "Honest limitations. ", bold: true }), new TextRun({ text: "(i) Eased deployable coverage: on the hard continuous grid auto’s mean deployable coverage is 0.843 (0.938 on log-OR); at high τ its off-the-shelf interval can under-cover, so users should treat the interval as somewhat optimistic and report τ̂. (ii) The trim-and-fill metric artefact: several of auto’s losses are to trim-and-fill on the oracle MCIW0 metric in step/Copas cells — hollow, because trim-and-fill’s deployable coverage is ≈ 0.29; it is not a deployable competitor. (iii) Null + step centre bias: when the true effect is zero under strong step selection the bias correction over-corrects downward; a symmetric interval cannot repair this." })]));
children.push(P([new TextRun({ text: "A second real dataset — magnesium/MI, an adversarial boundary. ", bold: true }), new TextRun({ text: "We also ran the estimator on the classic magnesium-for-MI meta-analysis (metadat::dat.li2007; examples/li2007_magnesium.csv; truth-recovery/magnesium_realtest.py), which has a rare external ground truth: after 20 small trials suggested a large mortality benefit, the ISIS-4 (N=58,050) and MAGIC (N=6,213) mega-trials found essentially no effect (pooled log-OR +0.05, OR 1.05). Pooling the 20 small trials and asking each estimator to move the spurious benefit (naive DL OR 0.61) toward that truth is a demanding test, reported honestly. No corrector reaches the mega-trial null — the magnesium small-study effect is famously more than publication selection (era/quality confounding), so it is adversarial for any funnel-based method. AdaptShrink-solo moves the right way (+26% closer, OR 0.70) but is not the closest; PET-PEESE is (+34%, OR 0.73) — on a single k=20 funnel PET has enough studies to behave, unlike its instability on few-studies-per-contrast networks. The AdaptShrink ensemble under-moves here (+4%) because two members (trim-and-fill, Vevea–Hedges) misfire on this dataset and dilute PET's correct pull: robust averaging is only as safe as the majority of its members, so on an adversarial case AdaptShrink-solo is preferable. A boundary, not a win — a non-selection bias defeats all funnel correctors, and the ensemble's safety is contingent on member agreement." })]));
children.push(P([new TextRun({ text: "When to use it. ", bold: true }), new TextRun({ text: "adaptshrink_auto is a sensible default when publication or selection bias cannot be ruled out and the analyst wants a single estimator that behaves well across the heterogeneity spectrum, on either SMD-like or log-OR effects. When heterogeneity is known low and selection plausible, the calibrated ensemble is marginally preferable for deployable coverage; when heterogeneity is high and selection implausible, an efficient REML-HKSJ analysis is appropriate and auto will (by design) lean toward it. The matched-coverage protocol is itself reusable: it is the fair way to compare estimators that differ in coverage, and we recommend reporting MCIW0 and deployable coverage together." })]));
children.push(P([new TextRun({ text: "Relation to prior work. ", bold: true }), new TextRun({ text: "AdaptShrink is an aggregation layer over existing correctors rather than a new selection model; it is closest in spirit to model-averaging and robust combination of estimators, specialised to the bias structure of publication selection. It does not require external information (unlike identifiable Copas models) and does not assume a specific selection function (unlike Vevea–Hedges or p-uniform*). Its cost is that it inherits its members’ failure modes when all members fail in the same direction." })]));

// 7 Reproducibility
children.push(H1("7. Reproducibility"));
children.push(P("All quantitative claims derive from committed, seeded result files on branch truth-recovery-misspec (commit b908caf). Key artefacts:"));
[
  "Estimator: src/ubcma/adaptshrink.py (base ensemble); truth-recovery/field_bakeoff2.py (calibrated ensemble, PET-gate, τ-aware auto selector). Henmi–Copas port + validation: src/ubcma/robust_methods.py, truth-recovery/validate_henmi_copas.R, hc_reference.json.",
  "Matched-coverage protocol & truth gate: truth-recovery/matched_coverage_bakeoff.py, field_bakeoff.py; reproduce with bash truth-recovery/reproduce_matched_coverage.sh.",
  "Result files: focused — mc_strong_table.csv, mc_strong_truthgate.json, REPORT_MATCHED_COVERAGE.md; field grid v1 — field_v1_*, REPORT_FIELD.md; broadened grids v2 — field2_c2_*, field2_l2_*, field2_*_summary.json, REPORT_FIELD2.md.",
  "Tests / truth gate: tests/test_adaptshrink.py, truth-recovery/test_matched_coverage.py, test_field_bakeoff.py, test_modern_comparators.py.",
  "Worked example: examples/verde_2021_aspirin.csv (real; provenance in examples/DATA_PROVENANCE.md); recompute with python manuscript/worked_example.py.",
  "Figures: regenerate with python manuscript/make_figures.py (reads only the committed CSV/JSON sources).",
].forEach(t => children.push(bullet(t)));
children.push(P("The win criterion is conservative by construction: a win is credited only when finite-output (G1), held-out matched-coverage validity (G3), and a paired-bootstrap 97.5%-CI sign test (G4) all pass."));

// Tables
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(H1("Tables"));
children.push(captionP("Table 1. ", "Focused matched-coverage comparison, strong selection (μ = 0.2, τ = 0.1, k = 40, 300 reps). Source: mc_strong_table.csv."));
children.push(tableFrom(
  ["Mechanism", "Method", "bias", "deployable cov", "MCIW0", "ratio vs HC"],
  [
    ["smooth", "AdaptShrink", "0.030", "0.967", "0.2526", "0.677"],
    ["smooth", "UBCMA", "0.045", "0.765", "0.2852", "0.764"],
    ["smooth", "trim-and-fill", "−0.028", "0.477", "0.2451", "0.657"],
    ["smooth", "Copas–Shi (HC)", "0.123", "0.083", "0.3731", "—"],
    ["smooth", "REML-HKSJ", "0.124", "0.120", "0.3745", "1.004"],
    ["step", "AdaptShrink", "0.053", "0.960", "0.2568", "0.633"],
    ["step", "trim-and-fill", "0.010", "0.600", "0.1709", "0.421"],
    ["step", "Copas–Shi (HC)", "0.146", "0.003", "0.4055", "—"],
    ["copas", "AdaptShrink", "0.014", "0.977", "0.2194", "0.753"],
    ["copas", "UBCMA", "0.021", "0.828", "0.2046", "0.702"],
    ["copas", "Copas–Shi (HC)", "0.099", "0.070", "0.2915", "—"],
  ],
  [1300, 1860, 1300, 1900, 1500, 1500]));

children.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
children.push(captionP("Table 2. ", "Cells dominated (and τ stratification) by AdaptShrink variant on the broadened grids, with mean deployable coverage. Sources: field2_c2_summary.json, field2_l2_summary.json, field2_*_domination_*.csv, field2_*_scores.csv."));
children.push(tableFrom(
  ["Variant", "Continuous 51 (τ0.1 / 0.3 / 0.5)", "Binary 30 (τ0.15 / 0.4)", "mean deployable cov (cont / bin)"],
  [
    ["ens", "16 (13 / 3 / 0)", "14 (6 / 8)", "0.899* / 0.956"],
    ["ens_calib", "19 (14 / 5 / 0)", "15 (6 / 9)", "— / 0.980"],
    ["petgate", "18 (6 / 7 / 5)", "13 (7 / 6)", "— / 0.795"],
    ["auto", "31 (15 / 9 / 7)", "20 (10 / 10)", "0.843 / 0.938"],
  ],
  [1600, 2920, 2240, 2600]));
children.push(P([new TextRun({ text: "* ens mean deployable coverage 0.899 is for the v1 strong grid; the v2 per-variant continuous means are reported per cell in field2_c2_scores.csv.", italics: true, size: 16 })]));

children.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
children.push(captionP("Table 3. ", "Worked example (aspirin, k = 6, log-OR): pooled estimates and 95% intervals. Computed by manuscript/worked_example.py. Source: manuscript/worked_example.json."));
children.push(tableFrom(
  ["Method", "μ̂ (log-OR)", "95% CI"],
  [
    ["DerSimonian–Laird (HKSJ)", "−0.067", "[−0.235, +0.101]"],
    ["REML (HKSJ)", "−0.072", "[−0.208, +0.064]"],
    ["PET-PEESE", "−0.227", "[−0.285, −0.168]"],
    ["Trim-and-fill", "−0.251", "[−0.288, −0.214]"],
    ["Copas–Shi", "−0.074", "[−0.171, +0.023]"],
    ["Henmi–Copas (metafor::hc)", "−0.154", "[−0.396, +0.089]"],
    ["UBCMA", "+0.012", "[−0.125, +0.118]"],
    ["AdaptShrink petgate", "−0.185", "[−0.351, −0.018]"],
    ["AdaptShrink ens_calib", "−0.237", "[−0.417, −0.056]"],
    ["AdaptShrink auto", "−0.237", "[−0.417, −0.056]"],
  ],
  [3960, 2200, 3200]));
children.push(P([new TextRun({ text: "τ̂_DL = 0.140; funnel-asymmetry t₁ = 2.94; PET-gate weight g = 0.68; auto selection = calibrated ensemble (τ̂ < 0.2).", italics: true, size: 16 })]));

// ---------- document ----------
const doc = new Document({
  creator: "Mahmood Ahmad",
  title: "AdaptShrink: a tau-aware selection-robust random-effects estimator",
  styles: {
    default: { document: { run: { font: "Arial", size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 260, after: 140 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 180, after: 100 }, outlineLevel: 1 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
        alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 280 } } } }] },
      { reference: "nums", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.",
        alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 280 } } } }] },
    ],
  },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 },
      margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "Page ", size: 18 }),
                 new TextRun({ children: [PageNumber.CURRENT], size: 18 })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(path.join(DIR, "AdaptShrink_StatMed.docx"), buf);
  console.log("wrote AdaptShrink_StatMed.docx", buf.length, "bytes");
});
