"""JATS / HTML full-text section parser (deterministic, model-free, offline).

Turns a Europe PMC ``fullTextXML`` (JATS) document — or a bronze/green OA HTML
page — into a small structured object the extraction layer can read:

    {abstract, methods, results, discussion, tables[], full_text, source_kind}

DETERMINISTIC-CORE INVARIANT: pure functions over bytes already on disk. No
network, no model. Section classification is title-keyword based; if the structure
is unrecognisable we fall back to a whole-document text strip so nothing silently
returns empty. Every returned span is a literal substring of the parsed document,
so downstream evidence_quote verification stays exact.
"""
from __future__ import annotations
import re
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _strip_ns(xml_text):
    """Remove XML namespaces so tag lookups are plain ('sec', 'table-wrap').

    JATS full text carries xlink:/mml: prefixes; once we drop the xmlns declarations
    those prefixes become 'unbound' and ET refuses to parse. So we strip every
    namespace prefix on BOTH tags and attributes (including xml:lang -> lang, which
    is harmless for text extraction)."""
    # drop xmlns / xmlns:x declarations
    xml_text = re.sub(r'\sxmlns(:[\w.-]+)?="[^"]*"', "", xml_text)
    # strip prefix on opening/closing tags:  <ns:tag ... </ns:tag  ->  <tag ... </tag
    xml_text = re.sub(r"(</?)[A-Za-z][\w.-]*:", r"\1", xml_text)
    # strip prefix on attributes:  xlink:href="..."  ->  href="..."
    xml_text = re.sub(r"(\s)[A-Za-z][\w.-]*:([\w.-]+=)", r"\1\2", xml_text)
    return xml_text

def _text_of(el):
    """All descendant text of an element, whitespace-normalised."""
    parts = []
    for t in el.itertext():
        if t:
            parts.append(t)
    return re.sub(r"\s+", " ", " ".join(parts)).strip()

# Stem/prefix match (NO trailing \b) — a trailing boundary fails on plural headings:
# \bresult\b does NOT match "RESULTS" (the 's' blocks the boundary). This silently
# left `results` empty for ~90% of articles. Prefix-match handles result/results,
# finding/findings, conclusion/conclusions, method/methods, etc.
_METHODS = re.compile(r"\b(method|material|procedure|statistical analys|design|intervention|protocol)", re.I)
_RESULTS = re.compile(r"\b(result|finding|outcome|efficacy|primary end|main end)", re.I)
_DISCUSS = re.compile(r"\b(discuss|conclusion|interpret|comment|limitation)", re.I)

def _classify(title):
    t = (title or "").lower()
    if _RESULTS.search(t):
        return "results"
    if _METHODS.search(t):
        return "methods"
    if _DISCUSS.search(t):
        return "discussion"
    return None

# ---------------------------------------------------------------------------
# JATS
# ---------------------------------------------------------------------------
def parse_jats(xml_bytes):
    """Parse a JATS fullTextXML document into sections. Returns dict or None on
    hard parse failure (caller falls back)."""
    try:
        xml_text = xml_bytes.decode("utf-8", errors="replace") if isinstance(xml_bytes, (bytes, bytearray)) else xml_bytes
        root = ET.fromstring(_strip_ns(xml_text))
    except ET.ParseError:
        return None

    out = {"abstract": "", "methods": "", "results": "", "discussion": "",
           "tables": [], "full_text": "", "source_kind": "jats"}

    # abstract (front matter)
    for ab in root.iter("abstract"):
        txt = _text_of(ab)
        if txt:
            out["abstract"] = (out["abstract"] + " " + txt).strip()

    body = root.find("body")
    scope = body if body is not None else root

    # section text by top-level (and nested) <sec> title. We accumulate the text of
    # a section and every descendant sec under the same top-level classification, so
    # "Results > Primary outcome" folds into results.
    def walk(el, inherited):
        for sec in el.findall("sec"):
            title_el = sec.find("title")
            title = _text_of(title_el) if title_el is not None else ""
            cls = _classify(title) or inherited
            # direct paragraph/text of this sec (excluding nested secs handled below)
            # simplest robust approach: take full sec text once at the shallowest
            # classified ancestor.
            if cls and inherited is None:
                out[cls] = (out[cls] + " " + _text_of(sec)).strip()
            walk(sec, cls)

    walk(scope, None)

    # tables (effect estimates frequently live here)
    for tw in scope.iter("table-wrap"):
        cap = ""
        cap_el = tw.find("caption")
        if cap_el is not None:
            cap = _text_of(cap_el)
        label_el = tw.find("label")
        label = _text_of(label_el) if label_el is not None else ""
        body_txt = _text_of(tw)
        if body_txt:
            out["tables"].append({"label": label, "caption": cap, "text": body_txt})

    out["full_text"] = _text_of(scope)
    # if section classification found nothing, fall back to full body text as results
    if not (out["results"] or out["methods"]) and out["full_text"]:
        out["results"] = out["full_text"]
        out["source_kind"] = "jats_unstructured"
    return out

# ---------------------------------------------------------------------------
# HTML (bronze/green publisher pages) — best-effort text strip
# ---------------------------------------------------------------------------
_SCRIPT_STYLE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.I | re.S)
_TAG = re.compile(r"<[^>]+>")

def parse_html(html_bytes):
    """Very defensive HTML→text. Publisher HTML varies wildly and carries no
    reliable section structure, so we return a single whole-page text blob under
    'results' (the extractor still requires a verbatim quote to emit anything).
    Returns None if the page has no meaningful text (e.g. a JS-only shell)."""
    try:
        html = html_bytes.decode("utf-8", errors="replace") if isinstance(html_bytes, (bytes, bytearray)) else html_bytes
    except Exception:
        return None
    html = _SCRIPT_STYLE.sub(" ", html)
    # unescape a few common entities relevant to CIs
    txt = _TAG.sub(" ", html)
    txt = (txt.replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">")
              .replace("&amp;", "&").replace("&#160;", " ").replace("&minus;", "-")
              .replace("&plusmn;", "±").replace("&thinsp;", " "))
    txt = re.sub(r"\s+", " ", txt).strip()
    if len(txt) < 400:            # a shell / paywall stub, not a readable article
        return None
    return {"abstract": "", "methods": "", "results": txt, "discussion": "",
            "tables": [], "full_text": txt, "source_kind": "html"}

def is_pdf(raw_bytes):
    return isinstance(raw_bytes, (bytes, bytearray)) and raw_bytes[:5] == b"%PDF-"
