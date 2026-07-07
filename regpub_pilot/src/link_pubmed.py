"""Link each NCT to candidate PMIDs and cache parsed PubMed abstracts.

Two independent linkage channels (each covers the other's gaps):
  (1) CT.gov referencesModule.references -> type RESULT (author-submitted) / DERIVED
      (PubMed-databank auto-link).
  (2) PubMed esearch  NCT[si]  -> the reverse databank link.
The UNION is the candidate set; per-trial we cap the number of abstracts fetched
(bound network cost) preferring RESULT-type then RCT/Clinical-Trial pubtypes.

Output: data/links.json          {nct: {pmids_ctgov_result, pmids_ctgov_derived,
                                        pmids_si, union, fetched}}
        data/pubmed/<hash>.json  parsed abstract per PMID.
"""
from __future__ import annotations
import json, urllib.parse
import xml.etree.ElementTree as ET
from common import (EUTILS, PM_DIR, DATA, CT_DIR, http_get, cache_path,
                    load_json, save_json, index_path, links_path)

PER_TRIAL_CAP = 6  # bound abstract fetches per trial (reported honestly in metrics)

def ctgov_refs(nct):
    rec = load_json(cache_path(CT_DIR, nct)) or {}
    refs = rec.get("protocolSection", {}).get("referencesModule", {}).get("references", []) or []
    result, derived = [], []
    for r in refs:
        pmid = r.get("pmid")
        if not pmid:
            continue
        (result if r.get("type") == "RESULT" else derived).append(str(pmid))
    return result, derived

def si_search(nct):
    """Reverse databank link: PubMed records tagged with this NCT."""
    term = urllib.parse.quote(f"{nct}[si]")
    url = f"{EUTILS}/esearch.fcgi?db=pubmed&term={term}&retmode=json&retmax=50"
    try:
        d = json.loads(http_get(url, min_gap=0.4))
        return [str(x) for x in d.get("esearchresult", {}).get("idlist", [])]
    except Exception:
        return []

def fetch_abstract(pmid):
    p = cache_path(PM_DIR, pmid)
    cached = load_json(p)
    if cached is not None:
        return cached
    url = f"{EUTILS}/efetch.fcgi?db=pubmed&id={pmid}&retmode=xml"
    xml = http_get(url, min_gap=0.4, accept="application/xml")
    rec = parse_pubmed(xml, pmid)
    save_json(p, rec)
    return rec

def parse_pubmed(xml, pmid):
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return {"pmid": pmid, "parse_error": True, "title": "", "abstract_sections": [],
                "abstract": "", "pubtypes": [], "year": None, "nct_accessions": []}
    art = root.find(".//PubmedArticle")
    if art is None:
        return {"pmid": pmid, "not_found": True, "title": "", "abstract_sections": [],
                "abstract": "", "pubtypes": [], "year": None, "nct_accessions": []}
    title = "".join(art.find(".//ArticleTitle").itertext()) if art.find(".//ArticleTitle") is not None else ""
    year = art.findtext(".//JournalIssue/PubDate/Year") or art.findtext(".//ArticleDate/Year")
    pubtypes = [pt.text for pt in art.findall(".//PublicationType") if pt.text]
    sections = []
    for a in art.findall(".//Abstract/AbstractText"):
        txt = "".join(a.itertext())
        sections.append({"label": a.get("Label"), "text": txt})
    abstract = " ".join(s["text"] for s in sections).strip()
    ncts = [acc.text for acc in art.findall(".//DataBankList/DataBank/AccessionNumberList/AccessionNumber") if acc.text and acc.text.upper().startswith("NCT")]
    return {"pmid": pmid, "title": title, "abstract_sections": sections,
            "abstract": abstract, "pubtypes": pubtypes,
            "year": int(year) if (year and year.isdigit()) else None,
            "nct_accessions": ncts}

def rank_pmids(result, derived, si):
    """Order candidates so the PER_TRIAL_CAP keeps the TRUSTWORTHY links first:
    RESULT-type (sponsor-submitted results) and si (reverse-databank confirmed = the
    paper declares this NCT) BEFORE generic DERIVED refs, which are frequently
    pre-registration background citations. Dedup, preserve order."""
    seen, ordered = set(), []
    for grp in (result, si, derived):
        for pid in grp:
            if pid not in seen:
                seen.add(pid); ordered.append(pid)
    return ordered

def main():
    idx = load_json(index_path())
    ncts = idx["ncts"]
    print(f"[link] linking {len(ncts)} NCTs ...")
    links = {}
    for i, nct in enumerate(ncts, 1):
        res, der = ctgov_refs(nct)
        si = si_search(nct)
        union = rank_pmids(res, der, si)
        fetched = []
        for pmid in union[:PER_TRIAL_CAP]:
            try:
                rec = fetch_abstract(pmid)
                fetched.append(pmid)
            except Exception as e:
                print(f"  ! {nct}/{pmid} abstract fail: {e}")
        links[nct] = {
            "pmids_ctgov_result": res, "pmids_ctgov_derived": der,
            "pmids_si": si, "union": union, "fetched": fetched,
            "capped": len(union) > PER_TRIAL_CAP,
        }
        if i % 50 == 0:
            print(f"  ... {i}/{len(ncts)}")
    save_json(links_path(), links)
    n_withpub = sum(1 for v in links.values() if v["union"])
    print(f"[link] done. {n_withpub}/{len(ncts)} trials have >=1 linked PMID. links.json written.")

if __name__ == "__main__":
    main()
