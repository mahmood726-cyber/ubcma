"""Regression tests for the full-text layer (jats parser + candidate windows + gate).

Run: python -m pytest src/test_fulltext.py -q   (from regpub_pilot/)
"""
import jats
from fulltext_extract import candidate_text
from llm_extract import verify_extraction

# A minimal JATS document exercising the plural-heading bug + table extraction.
JATS = b"""<?xml version="1.0"?>
<article xmlns:xlink="http://www.w3.org/1999/xlink">
<front><article-meta><abstract><p>We tested drug X.</p></abstract></article-meta></front>
<body>
<sec><title>RESEARCH DESIGN AND METHODS</title><p>Randomised 1:1.</p>
  <sec><title>Statistical analysis</title><p>ANCOVA.</p></sec></sec>
<sec><title>RESULTS</title>
  <p>The between-group difference in HbA1c was -0.53% (95% CI -0.69 to -0.37; p&lt;0.001).</p>
  <sec><title>Safety</title><p>AEs were balanced.</p></sec></sec>
<sec><title>CONCLUSIONS</title><p>Drug X works.</p></sec>
<table-wrap><label>Table 1</label><caption><p>Outcomes</p></caption>
  <table><tr><td>HbA1c</td><td>-0.53</td></tr></table></table-wrap>
</body></article>"""


def test_plural_headings_classified():
    """RESULTS / METHODS / CONCLUSIONS (all plural) must classify — the \\bresult\\b
    trailing-boundary bug silently emptied `results` for plural headings."""
    p = jats.parse_jats(JATS)
    assert p is not None
    assert "between-group difference in HbA1c" in p["results"]
    assert "Randomised 1:1" in p["methods"]
    assert "AEs were balanced" in p["results"]        # nested subsec folds into parent
    assert p["source_kind"] == "jats"                  # structured, not the fallback


def test_xlink_namespace_parses():
    """Undeclared xlink:/mml: prefixes must not break the parse (ns strip)."""
    xml = JATS.replace(b"<p>Randomised 1:1.</p>",
                       b'<p>See <xref xlink:href="b1">ref</xref>.</p>')
    p = jats.parse_jats(xml)
    assert p is not None and "See" in p["methods"]


def test_table_extracted():
    p = jats.parse_jats(JATS)
    assert p["tables"] and "-0.53" in p["tables"][0]["text"]


def test_candidate_window_contains_ci():
    """The pre-filter must surface the CI-bearing sentence as a verbatim window."""
    p = jats.parse_jats(JATS)
    excerpt, stats = candidate_text(p, ["Change in HbA1c"])
    assert "-0.53% (95% CI -0.69 to -0.37" in excerpt
    assert stats["n_windows"] >= 1


def test_gate_rejects_quote_not_in_excerpt():
    excerpt = "The between-group difference in HbA1c was -0.53% (95% CI -0.69 to -0.37)."
    good = {"abstain": False, "point": -0.53, "ci_lo": -0.69, "ci_hi": -0.37,
            "evidence_quote": "difference in HbA1c was -0.53% (95% CI -0.69 to -0.37)"}
    ok, note, _ = verify_extraction(good, excerpt)
    assert ok, note
    # a quote that is not a substring must be rejected (no source span -> no emit)
    bad = dict(good, evidence_quote="difference in HbA1c was -0.99% (95% CI -1.2 to -0.7)")
    ok2, note2, _ = verify_extraction(bad, excerpt)
    assert not ok2 and note2 == "quote_not_in_abstract"


def test_gate_rejects_point_outside_ci():
    excerpt = "primary effect 2.0 (95% CI -0.69 to -0.37) as reported"
    item = {"abstain": False, "point": 2.0, "ci_lo": -0.69, "ci_hi": -0.37,
            "evidence_quote": "primary effect 2.0 (95% CI -0.69 to -0.37)"}
    ok, note, _ = verify_extraction(item, excerpt)
    assert not ok and note == "point_outside_ci"


if __name__ == "__main__":
    import sys
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print("ok", fn.__name__)
    print(f"{len(fns)} passed")
