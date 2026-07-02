#!/usr/bin/env python
"""Render the finalized UBCMA E156 paper as an Insight-identity PDF galley.

Output: e156-submission/ubcma_insight.pdf
Includes masthead, structured 7-sentence body, visual abstract, results table,
references, and disclosure. No "preliminary" markers; DOI flagged not-yet-registered.
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, PageTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable,
)

ROOT = Path(__file__).resolve().parent.parent
SUB = ROOT / "e156-submission"
FIG = ROOT / "paper" / "figures"

ACCENT = colors.HexColor("#7A5A10")
INK = colors.HexColor("#1a1a1a")
INK2 = colors.HexColor("#555555")
CARD = colors.HexColor("#F5F3EE")
BORDER = colors.HexColor("#E5E0D6")
LINKC = colors.HexColor("#2E6B8A")

TITLE = "UBCMA: Unified Bias-Calibrated Meta-Analysis via Joint Heterogeneity-Selection Modeling"
AUTHOR = "Mahmood Ahmad"
AFFIL = "Tahir Heart Institute"
EMAIL = "mahmood.ahmad2@nhs.net"
ORCID = "0009-0003-7781-4478"
DATE = "26 March 2026"

SENTENCES = [
    ("Question", "Can a single meta-analytic model jointly correct heterogeneity, publication selection, and study-quality bias, rather than applying separate sequential corrections?"),
    ("Dataset", "We tested a unified mixture-normal selection likelihood against eight comparators on twelve simulated scenarios and a real six-trial aspirin secondary-prevention dataset."),
    ("Method", "Estimation used multi-start L-BFGS-B optimisation with profile-likelihood confidence intervals and BCa bootstrap, optionally with Bayesian inference via PyMC."),
    ("Primary result", "Across twelve scenarios (50 replicates, k=30) the unified model attained the highest coverage, 88.8% at RMSE 0.070, versus 59.7% (DerSimonian-Laird), 63.8% (REML-HKSJ), and 39.0% (trim-and-fill)."),
    ("Robustness", "With selection and quality bias combined, coverage held at 90.3% versus 31.3% for DerSimonian-Laird; on the aspirin data the model gave a pooled log-odds-ratio of +0.01 (95% CI -0.12 to 0.12), versus -0.07 uncorrected."),
    ("Interpretation", "Jointly modelling heterogeneity and selection bias yields less biased, better-calibrated pooled estimates than applying separate corrections sequentially."),
    ("Boundary", "The parametric logistic selection function may not capture every publication-bias mechanism, and the model is unsuited to small reviews (k below five)."),
]

ASPIRIN_TABLE = [
    ("Method", "Pooled estimate", "95% CI", "Sig."),
    ("DerSimonian-Laird", "-0.067", "-0.195 to 0.061", "No"),
    ("REML-HKSJ", "-0.072", "-0.208 to 0.064", "No"),
    ("Trim-and-fill", "-0.251", "-0.288 to -0.214", "Yes"),
    ("PET-PEESE", "-0.227", "-0.285 to -0.168", "Yes"),
    ("Copas", "-0.074", "-0.171 to 0.023", "No"),
    ("Quality-effects", "-0.156", "-0.200 to -0.111", "Yes"),
    ("UBCMA (profile)", "+0.011", "-0.125 to 0.117", "No"),
]

REFERENCES = [
    "DerSimonian R, Laird N. Meta-analysis in clinical trials. Control Clin Trials. 1986;7(3):177-188.",
    "Verde PE. A bias-corrected meta-analysis model for combining studies of different types and quality. Biom J. 2021;63(2):406-422.",
    "Copas JB, Shi JQ. A sensitivity analysis for publication bias in systematic reviews. Stat Methods Med Res. 2001;10(4):251-265.",
    "Doi SAR, Thalib L. A quality-effects model for meta-analysis. Epidemiology. 2008;19(1):94-100.",
    "Rover C, Knapp G, Friede T. Hartung-Knapp-Sidik-Jonkman approach and its modification for random-effects meta-analysis with few studies. BMC Med Res Methodol. 2015;15:99.",
]

DISCLOSURE = ("This work is a computational methods paper with AI assistance in code development and "
              "manuscript preparation. The UBCMA engine, simulation study, and all analyses were "
              "implemented in deterministic Python with fixed random seeds, enabling full "
              "reproducibility. AI was used as a constrained synthesis engine on structured inputs and "
              "predefined algorithms, not as an autonomous author. All results, text, and scientific "
              "claims were reviewed and verified by the author, who takes full responsibility.")

DATA_AVAIL = ("All code, data, and simulation scripts are available at "
              "https://github.com/mahmood726-cyber/ubcma under an MIT licence. The aspirin dataset is "
              "the classic six-trial secondary-prevention set (CDP, AMIS, ISIS-2, UK-TIA, SALT, ESPS-2) "
              "referenced by Verde (2021). Headline simulation results reproduce with "
              "ubcma study --tier pilot --seed 42. DOI: not yet registered (DOIs are currently "
              "suppressed site-wide).")

styles = getSampleStyleSheet()
S = {
    "label": ParagraphStyle("label", parent=styles["Normal"], fontName="Helvetica-Bold",
                            fontSize=7.5, textColor=ACCENT, leading=10, spaceAfter=2,
                            alignment=TA_CENTER),
    "title": ParagraphStyle("title", parent=styles["Title"], fontName="Times-Bold",
                            fontSize=17, textColor=INK, leading=21, alignment=TA_CENTER,
                            spaceAfter=6),
    "byline": ParagraphStyle("byline", parent=styles["Normal"], fontName="Helvetica",
                            fontSize=8.5, textColor=INK2, alignment=TA_CENTER, leading=12),
    "section": ParagraphStyle("section", parent=styles["Normal"], fontName="Helvetica-Bold",
                            fontSize=8, textColor=ACCENT, leading=12, spaceBefore=10, spaceAfter=4),
    "body": ParagraphStyle("body", parent=styles["Normal"], fontName="Times-Roman",
                            fontSize=10.5, textColor=INK, leading=16, alignment=TA_JUSTIFY,
                            spaceAfter=5),
    "sentence": ParagraphStyle("sentence", parent=styles["Normal"], fontName="Times-Roman",
                            fontSize=10, textColor=INK, leading=15, alignment=TA_JUSTIFY,
                            spaceAfter=4),
    "caption": ParagraphStyle("caption", parent=styles["Normal"], fontName="Times-Italic",
                            fontSize=8, textColor=INK2, leading=11, spaceBefore=3, spaceAfter=8),
    "ref": ParagraphStyle("ref", parent=styles["Normal"], fontName="Helvetica",
                            fontSize=7.8, textColor=INK2, leading=11, spaceAfter=3,
                            leftIndent=10, firstLineIndent=-10),
    "small": ParagraphStyle("small", parent=styles["Normal"], fontName="Helvetica",
                            fontSize=7.5, textColor=INK2, leading=10.5, alignment=TA_JUSTIFY,
                            spaceAfter=4),
}


def header_footer(canvas, doc):
    canvas.saveState()
    # top accent band
    canvas.setFillColor(ACCENT)
    canvas.rect(0, A4[1] - 14 * mm, A4[0], 14 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Times-Bold", 13)
    canvas.drawString(18 * mm, A4[1] - 9.5 * mm, "Insight")
    canvas.setFont("Helvetica", 7)
    canvas.drawString(34 * mm, A4[1] - 9.3 * mm, "Evidence micro-paper - synthesis-medicine.org")
    canvas.setFont("Helvetica", 7)
    canvas.drawRightString(A4[0] - 18 * mm, A4[1] - 9.3 * mm, "E156 micro-paper")
    # footer
    canvas.setStrokeColor(BORDER)
    canvas.line(18 * mm, 14 * mm, A4[0] - 18 * mm, 14 * mm)
    canvas.setFillColor(INK2)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(18 * mm, 10 * mm, "Ahmad M. UBCMA. Insight. 2026.")
    canvas.drawCentredString(A4[0] / 2, 10 * mm, "DOI: not yet registered")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, "Page %d" % doc.page)
    canvas.restoreState()


def build():
    doc = BaseDocTemplate(str(SUB / "ubcma_insight.pdf"), pagesize=A4,
                          leftMargin=18 * mm, rightMargin=18 * mm,
                          topMargin=20 * mm, bottomMargin=18 * mm,
                          title=TITLE, author=AUTHOR)
    frame = Frame(doc.leftMargin, doc.bottomMargin,
                  doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=header_footer)])

    story = []
    story.append(Paragraph("METHODS - META-ANALYSIS", S["label"]))
    story.append(Paragraph(TITLE, S["title"]))
    story.append(Paragraph(
        f'{AUTHOR} &middot; {AFFIL} &middot; '
        f'<font color="#2E6B8A">{EMAIL}</font> &middot; ORCID {ORCID} &middot; {DATE}',
        S["byline"]))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.2, color=BORDER,
                            spaceBefore=4, spaceAfter=8))

    # structured body
    story.append(Paragraph("STRUCTURED SUMMARY (E156)", S["section"]))
    for role, text in SENTENCES:
        story.append(Paragraph(f'<b><font color="#7A5A10">{role}.</font></b> {text}', S["sentence"]))

    # visual abstract
    va = FIG / "visual_abstract.png"
    if va.exists():
        story.append(Paragraph("VISUAL ABSTRACT", S["section"]))
        img = Image(str(va))
        maxw = doc.width
        ratio = img.imageHeight / img.imageWidth
        img.drawWidth = maxw
        img.drawHeight = maxw * ratio
        story.append(img)
        story.append(Paragraph(
            "Figure 1. UBCMA jointly models heterogeneity, publication selection, and study-quality "
            "bias in one likelihood; highest 95% CI coverage (88.8%) across 12 simulated scenarios, "
            "near-null bias-corrected pooled estimate on the aspirin data.", S["caption"]))

    # results table
    story.append(Paragraph("EMPIRICAL ILLUSTRATION - ASPIRIN (k=6)", S["section"]))
    tbl = Table(ASPIRIN_TABLE, colWidths=[doc.width * w for w in (0.34, 0.24, 0.30, 0.12)])
    style = TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 8),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CARD]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, ACCENT),
        ("LINEBELOW", (0, -1), (-1, -1), 0.6, BORDER),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        # highlight UBCMA row (last)
        ("FONT", (0, -1), (-1, -1), "Helvetica-Bold", 8),
        ("TEXTCOLOR", (0, -1), (-1, -1), ACCENT),
    ])
    tbl.setStyle(style)
    story.append(tbl)
    story.append(Paragraph(
        "Table 1. Aspirin secondary-prevention dataset (k=6): pooled effect on the log-odds-ratio "
        "scale with 95% CI. Classic six-trial set (CDP, AMIS, ISIS-2, UK-TIA, SALT, ESPS-2) "
        "referenced by Verde (2021). UBCMA's bias-corrected estimate is near-null; the dataset is "
        "dominated by the ISIS-2 outlier (I-squared = 82.6%).", S["caption"]))

    # references
    story.append(Paragraph("REFERENCES", S["section"]))
    for i, r in enumerate(REFERENCES, 1):
        story.append(Paragraph(f"{i}. {r}", S["ref"]))

    # disclosure + data availability
    story.append(Paragraph("AI DISCLOSURE", S["section"]))
    story.append(Paragraph(DISCLOSURE, S["small"]))
    story.append(Paragraph("DATA AVAILABILITY", S["section"]))
    story.append(Paragraph(DATA_AVAIL, S["small"]))

    doc.build(story)
    print(f"Wrote {SUB / 'ubcma_insight.pdf'}")


if __name__ == "__main__":
    build()
