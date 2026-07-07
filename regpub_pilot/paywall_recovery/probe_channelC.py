"""Step 3 — probe genuinely-open-LICENSE non-PMC papers (gold/hybrid/diamond/green)
for an openly-retrievable article/supplement, and classify content yield.

Ethical rule enforced: we accept ONLY a clean HTTP 200 with real content from the
open location. A 403/blocked fetch is recorded 'blocked, not used' and we do NOT
retry via any mirror or alternate access path. Repository/OA-platform hosts
(figshare, institutional repos, J-STAGE, BMC) are legitimate open sources.

Content classification (per retrieved doc):
  structured_tables : text PDF whose pages contain result tables (HbA1c/OR/HR/CI grids)
  km_plus_atrisk    : a Kaplan-Meier figure PLUS a 'No. at risk' / 'Number at risk' row
  narrative_only    : open but no poolable structured content
Run:  python probe_channelC.py
"""
from __future__ import annotations
import sys, os, json, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
from fetch_fulltext import http_get_bytes
import fitz  # PyMuPDF — for open-doc inspection only (outside the deterministic core)

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache"); OUTD = os.path.join(HERE, "out")
SUPP = os.path.join(HERE, "supp"); os.makedirs(SUPP, exist_ok=True)

# genuinely-open-license non-PMC candidates + their open location(s).
# 'kind': repo/platform we treat as legitimately open.
CANDS = [
    {"pmid": "24552155", "kind": "figshare", "note": "albiglutide T2D RCT (already recovered)",
     "url": "PREFETCHED", "file": "24552155_figshare_sm0001.pdf"},
    {"pmid": "29320312", "kind": "ucl_repo_green",
     "url": "https://discovery.ucl.ac.uk/10063847/1/REF_targeted%20therapy%20for%20advanced%20solid%20tumors....clinical%20oncology.pdf"},
    {"pmid": "25186922", "kind": "jstage_diamond",
     "url": "https://www.jstage.jst.go.jp/article/circj/78/10/78_CJ-14-0810/_pdf"},
    {"pmid": "34737187", "kind": "diabetesjournals_green",
     "url": "https://diabetesjournals.org/diabetes/article-pdf/71/2/315/640899/db210688.pdf"},
]

KM_RE = re.compile(r"(no\.?\s*at\s*risk|number\s*at\s*risk|patients\s*at\s*risk)", re.I)
TAB_RE = re.compile(r"(hba1c|hazard ratio|\bHR\b|odds ratio|\bOR\b|95%\s*CI|change from baseline|"
                    r"progression-free|overall survival)", re.I)

def classify_pdf(raw):
    try:
        d = fitz.open(stream=raw, filetype="pdf")
    except Exception as e:
        return {"parse": f"fail:{e}"}
    full = "".join(d[i].get_text() for i in range(d.page_count))
    n_tab = len(TAB_RE.findall(full))
    km = bool(KM_RE.search(full))
    # a KM figure w/ at-risk row: at-risk phrase present AND survival vocabulary
    surv = bool(re.search(r"(overall survival|progression-free|kaplan|median .*survival)", full, re.I))
    yields = []
    if n_tab >= 3:
        yields.append("structured_tables")
    if km and surv:
        yields.append("km_plus_atrisk")
    if not yields:
        yields = ["narrative_only"]
    return {"parse": "ok", "pages": d.page_count, "chars": len(full),
            "table_signal": n_tab, "at_risk_row": km, "survival_vocab": surv,
            "yield": yields}

def main():
    out = []
    for c in CANDS:
        pmid = c["pmid"]
        if c["url"] == "PREFETCHED":
            raw = open(os.path.join(SUPP, c["file"]), "rb").read()
            status = "prefetched_open"
        else:
            cache_f = os.path.join(SUPP, f"{pmid}_channelC.pdf")
            if os.path.exists(cache_f):
                raw = open(cache_f, "rb").read(); status = "cached"
            else:
                raw, ct = http_get_bytes(c["url"], accept="application/pdf", insecure_ok=True)
                if raw is None:
                    status = f"BLOCKED:{ct}"        # record, do not route around
                elif raw[:5] != b"%PDF-" and b"PDF" not in raw[:1024]:
                    status = "not_pdf"
                else:
                    open(cache_f, "wb").write(raw); status = "open_200"
        rec = {"pmid": pmid, "kind": c["kind"], "note": c.get("note", ""), "status": status}
        if raw and str(status).startswith(("open", "cached", "prefetched")):
            rec.update(classify_pdf(raw))
        out.append(rec)
        print(f"{pmid} {c['kind']:<22} {status:<22} "
              f"{rec.get('yield','-')} tabsig={rec.get('table_signal','-')} "
              f"atrisk={rec.get('at_risk_row','-')}")
    json.dump(out, open(os.path.join(OUTD, "channelC_probe.json"), "w", encoding="utf-8"), indent=1)
    print("\nwrote channelC_probe.json")

if __name__ == "__main__":
    main()
