#!/usr/bin/env python
"""Generate JATS 1.3 XML for the finalized UBCMA E156 paper.

Produces a structured Journal Publishing DTD 1.3 article with:
  - full <front> metadata (no "preliminary" markers)
  - <body> carrying the 7-sentence E156 micro-paper
  - a <table-wrap> with the empirical results table (aspirin, method comparison)
  - a <fig> referencing the visual abstract
  - a <back> <ref-list> of real, topic-matched references

Output: e156-submission/jats.xml
"""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
SUB = ROOT / "e156-submission"

TITLE = "UBCMA: Unified Bias-Calibrated Meta-Analysis via Joint Heterogeneity-Selection Modeling"
AUTHOR_SURNAME = "Ahmad"
AUTHOR_GIVEN = "Mahmood"
AUTHOR_ORCID = "0009-0003-7781-4478"
AFFIL = "Tahir Heart Institute"
EMAIL = "mahmood.ahmad2@nhs.net"
JOURNAL = "Insight"
PUB_DATE = ("2026", "03", "26")

ABSTRACT = (
    "Standard meta-analytic methods treat heterogeneity, publication selection, and "
    "study-quality bias as separate problems, so sequential corrections can leave residual "
    "confounding when these biases co-occur. Unified Bias-Calibrated Meta-Analysis (UBCMA) "
    "estimates a pooled effect while jointly modelling heterogeneity (two-component normal "
    "mixture), publication selection (logistic selection function), and quality-dependent bias "
    "(risk-of-bias covariate shifts) in a single likelihood, with profile-likelihood confidence "
    "intervals. Across 12 simulated scenarios (50 replicates, k=30) UBCMA attained the highest "
    "interval coverage (88.8%) at low RMSE (0.070) against eight comparators, and held 90.3% "
    "coverage when selection and quality bias co-occurred (versus 31.3% for DerSimonian-Laird). "
    "On a real six-trial aspirin secondary-prevention dataset it returned a near-null "
    "bias-corrected pooled log-odds-ratio of +0.01 (95% CI -0.12 to 0.12), versus -0.07 "
    "uncorrected. Joint modelling yields less biased, better-calibrated estimates than separate "
    "sequential corrections."
)

SENTENCES = [
    ("Question", "Can a single meta-analytic model jointly correct heterogeneity, publication selection, and study-quality bias, rather than applying separate sequential corrections?"),
    ("Dataset", "We tested a unified mixture-normal selection likelihood against eight comparators on twelve simulated scenarios and a real six-trial aspirin secondary-prevention dataset."),
    ("Method", "Estimation used multi-start L-BFGS-B optimisation with profile-likelihood confidence intervals and BCa bootstrap, optionally with Bayesian inference via PyMC."),
    ("Primary result", "Across twelve scenarios (50 replicates, k=30) the unified model attained the highest coverage, 88.8% at RMSE 0.070, versus 59.7% (DerSimonian-Laird), 63.8% (REML-HKSJ), and 39.0% (trim-and-fill)."),
    ("Robustness", "With selection and quality bias combined, coverage held at 90.3% versus 31.3% for DerSimonian-Laird; on the aspirin data the model gave a pooled log-odds-ratio of +0.01 (95% CI -0.12 to 0.12), versus -0.07 uncorrected."),
    ("Interpretation", "Jointly modelling heterogeneity and selection bias yields less biased, better-calibrated pooled estimates than applying separate corrections sequentially."),
    ("Boundary", "The parametric logistic selection function may not capture every publication-bias mechanism, and the model is unsuited to small reviews (k below five)."),
]

# Empirical results table (aspirin, k=6) - method comparison. Verified values.
ASPIRIN_TABLE = [
    ("DerSimonian-Laird", "-0.067", "-0.195 to 0.061", "No"),
    ("REML-HKSJ", "-0.072", "-0.208 to 0.064", "No"),
    ("Trim-and-fill", "-0.251", "-0.288 to -0.214", "Yes"),
    ("PET-PEESE", "-0.227", "-0.285 to -0.168", "Yes"),
    ("Copas", "-0.074", "-0.171 to 0.023", "No"),
    ("Quality-effects", "-0.156", "-0.200 to -0.111", "Yes"),
    ("UBCMA (profile)", "+0.011", "-0.125 to 0.117", "No"),
]

# Real, topic-matched references as (surname-list, given-list, article-title, source, year, vol, issue, fpage, lpage)
REFERENCES = [
    ([("DerSimonian", "R"), ("Laird", "N")], "Meta-analysis in clinical trials", "Controlled Clinical Trials", "1986", "7", "3", "177", "188"),
    ([("Verde", "PE")], "A bias-corrected meta-analysis model for combining studies of different types and quality", "Biometrical Journal", "2021", "63", "2", "406", "422"),
    ([("Copas", "JB"), ("Shi", "JQ")], "A sensitivity analysis for publication bias in systematic reviews", "Statistical Methods in Medical Research", "2001", "10", "4", "251", "265"),
    ([("Doi", "SAR"), ("Thalib", "L")], "A quality-effects model for meta-analysis", "Epidemiology", "2008", "19", "1", "94", "100"),
    ([("Rover", "C"), ("Knapp", "G"), ("Friede", "T")], "Hartung-Knapp-Sidik-Jonkman approach and its modification for random-effects meta-analysis with few studies", "BMC Medical Research Methodology", "2015", "15", "", "99", ""),
]


def e(s: str) -> str:
    return escape(str(s))


def build() -> str:
    out: list[str] = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.3 20210610//EN" '
               '"https://jats.nlm.nih.gov/publishing/1.3/JATS-journalpublishing1-3.dtd">')
    out.append('<article xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:mml="http://www.w3.org/1998/Math/MathML" '
               'dtd-version="1.3" article-type="research-article" xml:lang="en">')

    # ---- front ----
    out.append("  <front>")
    out.append("    <journal-meta>")
    out.append('      <journal-id journal-id-type="publisher">insight</journal-id>')
    out.append("      <journal-title-group>")
    out.append(f"        <journal-title>{e(JOURNAL)}</journal-title>")
    out.append("      </journal-title-group>")
    out.append('      <issn pub-type="epub">0000-0000</issn>')
    out.append("      <publisher><publisher-name>Synthesis Medicine</publisher-name></publisher>")
    out.append("    </journal-meta>")
    out.append("    <article-meta>")
    out.append('      <!-- DOI not yet registered; DOIs are suppressed site-wide. -->')
    out.append("      <title-group>")
    out.append(f"        <article-title>{e(TITLE)}</article-title>")
    out.append("      </title-group>")
    out.append('      <contrib-group>')
    out.append('        <contrib contrib-type="author">')
    out.append(f'          <contrib-id contrib-id-type="orcid">https://orcid.org/{e(AUTHOR_ORCID)}</contrib-id>')
    out.append("          <name>")
    out.append(f"            <surname>{e(AUTHOR_SURNAME)}</surname>")
    out.append(f"            <given-names>{e(AUTHOR_GIVEN)}</given-names>")
    out.append("          </name>")
    out.append('          <xref ref-type="aff" rid="aff1"/>')
    out.append(f'          <email>{e(EMAIL)}</email>')
    out.append("        </contrib>")
    out.append("      </contrib-group>")
    out.append(f'      <aff id="aff1">{e(AFFIL)}</aff>')
    out.append('      <pub-date publication-format="electronic" date-type="pub">')
    out.append(f"        <day>{PUB_DATE[2]}</day><month>{PUB_DATE[1]}</month><year>{PUB_DATE[0]}</year>")
    out.append("      </pub-date>")
    out.append('      <permissions>')
    out.append('        <license license-type="open-access" xlink:href="https://creativecommons.org/licenses/by/4.0/">')
    out.append("          <license-p>This is an open-access article distributed under the terms of the Creative Commons Attribution 4.0 License.</license-p>")
    out.append("        </license>")
    out.append("      </permissions>")
    out.append("      <abstract>")
    out.append(f"        <p>{e(ABSTRACT)}</p>")
    out.append("      </abstract>")
    out.append("      <kwd-group>")
    for kw in ["meta-analysis", "publication bias", "selection model", "risk of bias",
               "heterogeneity", "quality-adjusted pooling"]:
        out.append(f"        <kwd>{e(kw)}</kwd>")
    out.append("      </kwd-group>")
    out.append("    </article-meta>")
    out.append("  </front>")

    # ---- body ----
    out.append("  <body>")
    out.append('    <sec id="s1">')
    out.append("      <title>Structured summary</title>")
    for role, text in SENTENCES:
        out.append(f"      <p><bold>{e(role)}.</bold> {e(text)}</p>")
    out.append("    </sec>")

    # figure
    out.append('    <sec id="s2">')
    out.append("      <title>Figure</title>")
    out.append('      <fig id="fig1" position="float">')
    out.append("        <label>Figure 1</label>")
    out.append("        <caption><title>Visual abstract.</title>"
               "<p>UBCMA jointly models heterogeneity, publication selection, and study-quality bias "
               "in one likelihood; it attains the highest 95% CI coverage (88.8%) across 12 simulated "
               "scenarios and gives a near-null bias-corrected pooled estimate on the aspirin data.</p></caption>")
    out.append('        <graphic xlink:href="assets/visual_abstract.png" mimetype="image" mime-subtype="png"/>')
    out.append("      </fig>")
    out.append("    </sec>")

    # table
    out.append('    <sec id="s3">')
    out.append("      <title>Empirical illustration</title>")
    out.append('      <table-wrap id="tbl1" position="float">')
    out.append("        <label>Table 1</label>")
    out.append("        <caption><title>Aspirin secondary-prevention dataset (k=6): method comparison.</title>"
               "<p>Pooled effect on the log-odds-ratio scale with 95% confidence interval. "
               "The classic six-trial aspirin dataset (CDP, AMIS, ISIS-2, UK-TIA, SALT, ESPS-2) referenced by Verde (2021).</p></caption>")
    out.append('        <table frame="hsides" rules="groups">')
    out.append("          <thead>")
    out.append("            <tr><th>Method</th><th>Pooled estimate</th><th>95% CI</th><th>Significant?</th></tr>")
    out.append("          </thead>")
    out.append("          <tbody>")
    for method, est, ci, sig in ASPIRIN_TABLE:
        out.append(f"            <tr><td>{e(method)}</td><td>{e(est)}</td><td>{e(ci)}</td><td>{e(sig)}</td></tr>")
    out.append("          </tbody>")
    out.append("        </table>")
    out.append("      </table-wrap>")
    out.append("    </sec>")
    out.append("  </body>")

    # ---- back ----
    out.append("  <back>")
    out.append('    <ref-list>')
    out.append("      <title>References</title>")
    for i, (names, atitle, source, year, vol, issue, fpage, lpage) in enumerate(REFERENCES, 1):
        out.append(f'      <ref id="r{i}">')
        out.append('        <element-citation publication-type="journal">')
        out.append("          <person-group person-group-type=\"author\">")
        for surname, given in names:
            out.append(f"            <name><surname>{e(surname)}</surname><given-names>{e(given)}</given-names></name>")
        out.append("          </person-group>")
        out.append(f"          <article-title>{e(atitle)}</article-title>")
        out.append(f"          <source>{e(source)}</source>")
        out.append(f"          <year>{e(year)}</year>")
        if vol:
            out.append(f"          <volume>{e(vol)}</volume>")
        if issue:
            out.append(f"          <issue>{e(issue)}</issue>")
        if fpage:
            out.append(f"          <fpage>{e(fpage)}</fpage>")
        if lpage:
            out.append(f"          <lpage>{e(lpage)}</lpage>")
        out.append("        </element-citation>")
        out.append("      </ref>")
    out.append("    </ref-list>")
    out.append("  </back>")
    out.append("</article>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    xml = build()
    (SUB / "jats.xml").write_text(xml, encoding="utf-8")
    print(f"Wrote {SUB / 'jats.xml'} ({len(xml)} bytes)")
