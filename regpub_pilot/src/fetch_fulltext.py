"""Acquire legally-open FULL TEXT for the pilot's confirmed-index PMIDs.

Phase 1 of the open-data roadmap. Two legal, no-paywall channels:
  1. Europe PMC ``fullTextXML`` — the OA-subset + author-manuscript full text hosted
     IN Europe PMC (machine-readable JATS, no OCR). Fetched by PMCID.
  2. OpenAlex/Unpaywall ``oa_url`` — a legal OA copy elsewhere (gold/green/hybrid/
     bronze) for articles NOT in Europe PMC. Publisher HTML/PDF; heavier, licence-
     limited (bronze = read-only, not redistributable). We fetch + text-strip HTML;
     PDFs are recorded as unparseable (honest bound, no OCR in the deterministic core).

SEAM: this is the ONLY networked module in the full-text path. Everything it pulls is
cached to ``data/fulltext/`` so extraction/pooling run fully offline. Fails closed on
error payloads (never treats an HTTP error page as article text).

Run:
    PILOT_AREA=t2d python src/fetch_fulltext.py fetch
    PILOT_AREA=onc python src/fetch_fulltext.py fetch
    python src/fetch_fulltext.py report        # coverage summary, both areas
"""
from __future__ import annotations
import sys, os, io, json, time, ssl, urllib.request, urllib.parse, urllib.error
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
from common import DATA, OUT, load_json, save_json, index_path, links_path
from llm_extract import build_items
import jats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FT_DIR = os.path.join(DATA, "fulltext")          # raw fetched documents (cache)
FT_PARSED = os.path.join(DATA, "fulltext_parsed")  # parsed section JSON (cache)
SCAN_OUT = os.path.join(ROOT, "opendata_scan", "out")
UPW_CACHE = os.path.join(ROOT, "opendata_scan", "cache_upw")
for d in (FT_DIR, FT_PARSED):
    os.makedirs(d, exist_ok=True)

# Europe PMC full-text XML endpoint. The path is /rest/{PMCID}/fullTextXML — the
# PMCID already carries its 'PMC' prefix; there is NO separate source path segment
# (a /rest/PMC/{PMCID}/... form 404s). Verified live 2026-07-07.
EPMC_FT = "https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"

_LAST = {"t": 0.0}
def _throttle(gap=0.34):
    dt = time.time() - _LAST["t"]
    if dt < gap:
        time.sleep(gap - dt)
    _LAST["t"] = time.time()

def http_get_bytes(url, retries=4, timeout=60, accept="application/xml", insecure_ok=False):
    """GET raw bytes with bounded backoff. Returns (bytes, content_type), or
    (None, reason) on a soft miss — NEVER raises, so one dead publisher/repository
    link cannot abort a whole fetch run (honest miss, recorded downstream).

    insecure_ok: for the OA-copy channel only, a CERTIFICATE_VERIFY_FAILED (common on
    bronze repository hosts with an incomplete chain / a Windows box lacking the CA)
    is retried once over an unverified TLS context. The content is PUBLIC, read-only
    open-access article text, so the residual risk is minimal; EPMC stays strict."""
    last = None
    for i in range(retries):
        _throttle()
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "ubcma-regpub-pilot/0.1 (research; open-access full text; contact via repo)",
                "Accept": accept})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                ct = r.headers.get("Content-Type", "")
                return r.read(), ct
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 404:
                return None, "http_404"
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(min(2 ** i, 8)); continue
            return None, f"http_{e.code}"   # 403/401 paywall -> soft miss, honest
        except urllib.error.URLError as e:
            last = e
            reason = getattr(e, "reason", None)
            if insecure_ok and isinstance(reason, ssl.SSLCertVerificationError):
                try:
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    req = urllib.request.Request(url, headers={"User-Agent": "ubcma-regpub-pilot/0.1"})
                    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                        return r.read(), r.headers.get("Content-Type", "") + "; tls_unverified"
                except Exception as e2:
                    return None, "ssl_verify_failed"
            time.sleep(min(2 ** i, 8))
        except TimeoutError as e:
            last = e; time.sleep(min(2 ** i, 8))
    return None, f"exhausted:{last}"

# ---------------------------------------------------------------------------
# OA map: pmid -> {inEPMC, pmcid, oa_status, oa_url, isOpenAccess}
# Reuses the read-only measurement caches so we do NOT re-query metadata.
# ---------------------------------------------------------------------------
def load_oa_map(area):
    recs = json.load(open(os.path.join(SCAN_OUT, "oa_index_records.json"), encoding="utf-8"))[area]
    # oa_url + oa_status live in the OpenAlex cache; rebuild {pmid: oa} from it.
    oax = {}
    import glob, hashlib
    for f in glob.glob(os.path.join(UPW_CACHE, "oax_*.json")):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        for w in d.get("results", []):
            pmid_url = (w.get("ids") or {}).get("pmid") or ""
            pmid = pmid_url.rstrip("/").split("/")[-1] if pmid_url else None
            if not pmid:
                continue
            oa = w.get("open_access") or {}
            oax[str(pmid)] = {"oa_status": oa.get("oa_status"), "oa_url": oa.get("oa_url"),
                              "is_oa": bool(oa.get("is_oa"))}
    out = {}
    for pmid, r in recs.items():
        u = oax.get(str(pmid), {})
        inepmc = r.get("inEPMC") == "Y"
        out[str(pmid)] = {
            "inEPMC": inepmc, "pmcid": r.get("pmcid"),
            "isOpenAccess": r.get("isOpenAccess") == "Y",
            "oa_status": u.get("oa_status"), "oa_url": u.get("oa_url"),
            "oa_elsewhere": bool(u.get("is_oa")) and not inepmc,
        }
    return out

# ---------------------------------------------------------------------------
def _raw_path(pmid, kind):
    return os.path.join(FT_DIR, f"{pmid}.{kind}")

def fetch_one(pmid, oa):
    """Fetch full text for one PMID. Returns a status dict; caches raw + parsed."""
    parsed_p = os.path.join(FT_PARSED, f"{pmid}.json")
    if os.path.exists(parsed_p):
        p = load_json(parsed_p)
        return {"pmid": pmid, "channel": p.get("_channel"), "status": p.get("_status"),
                "source_kind": p.get("source_kind"), "cached": True}

    channel = status = source_kind = None
    parsed = None

    # channel 1: Europe PMC JATS
    if oa.get("inEPMC") and oa.get("pmcid"):
        channel = "epmc_jats"
        xml_p = _raw_path(pmid, "xml")
        if os.path.exists(xml_p):
            raw = open(xml_p, "rb").read()
        else:
            url = EPMC_FT.format(pmcid=oa["pmcid"])
            raw, ct = http_get_bytes(url, accept="application/xml")
            if raw:
                open(xml_p, "wb").write(raw)
        if raw:
            parsed = jats.parse_jats(raw)
            status = "parsed" if parsed else "parse_failed"
        else:
            status = "fetch_miss"

    # channel 2: OpenAlex/Unpaywall OA copy elsewhere (bronze/green/gold/hybrid)
    elif oa.get("oa_elsewhere") and oa.get("oa_url"):
        channel = "oa_" + (oa.get("oa_status") or "unknown")
        oa_p = _raw_path(pmid, "oa")
        if os.path.exists(oa_p + ".meta"):
            meta = load_json(oa_p + ".meta")
            raw = open(oa_p, "rb").read() if os.path.exists(oa_p) else None
            ct = meta.get("ct", "")
        else:
            raw, ct = http_get_bytes(oa["oa_url"], accept="text/html,application/xhtml+xml,application/pdf",
                                     insecure_ok=True)
            if raw:
                open(oa_p, "wb").write(raw)
                save_json(oa_p + ".meta", {"ct": ct, "url": oa["oa_url"]})
        if not raw:
            status = "fetch_miss:" + str(ct)
        elif jats.is_pdf(raw) or "pdf" in (ct or "").lower():
            status = "pdf_unparseable"          # honest bound: no OCR in the core
            source_kind = "pdf"
        else:
            parsed = jats.parse_html(raw)
            status = "parsed" if parsed else "html_empty"
    else:
        channel = "none"; status = "no_oa_fulltext"

    if parsed is not None:
        source_kind = parsed.get("source_kind")
        parsed["_channel"] = channel; parsed["_status"] = status; parsed["_pmid"] = pmid
        save_json(parsed_p, parsed)
    else:
        # persist a stub so re-runs don't refetch a known miss
        save_json(parsed_p, {"_channel": channel, "_status": status, "_pmid": pmid,
                             "source_kind": source_kind, "results": "", "methods": "",
                             "abstract": "", "tables": []})
    return {"pmid": pmid, "channel": channel, "status": status,
            "source_kind": source_kind, "cached": False}

def fetch_area(area, only_gap=True):
    """Fetch full text for the confirmed-index denominator of an area.

    only_gap=True restricts fetching to trials that are NOT already poolable from the
    abstract+registry layer (the enriched fused_usable flag) — that's where the lift
    is and it avoids needless publisher hits. Set False to fetch the whole denominator.
    """
    idx = load_json(index_path(area)); links = load_json(links_path(area))
    items = build_items(idx["ncts"], links)          # exact 235/104 denominator
    oa_map = load_oa_map(area)
    fused = {}
    ep = os.path.join(OUT, f"enriched_{area}.jsonl")
    if os.path.exists(ep):
        for line in open(ep, encoding="utf-8"):
            r = json.loads(line); fused[str(r["pmid"])] = r["fused_usable"]

    targets = []
    for it in items:
        pmid = str(it["pmid"])
        if only_gap and fused.get(pmid):
            continue
        targets.append(pmid)

    results = []
    for i, pmid in enumerate(targets):
        oa = oa_map.get(pmid, {})
        res = fetch_one(pmid, oa)
        results.append(res)
        if (i + 1) % 20 == 0:
            print(f"  [{area}] {i+1}/{len(targets)} fetched")
    save_json(os.path.join(OUT, f"fulltext_fetch_{area}.json"),
              {"area": area, "only_gap": only_gap, "n_targets": len(targets), "results": results})
    _summarise(area, results)
    return results

def _summarise(area, results):
    from collections import Counter
    by_status = Counter(r["status"] for r in results)
    by_channel = Counter(r["channel"] for r in results)
    parsed = sum(1 for r in results if r["status"] == "parsed")
    print(f"[{area}] targets={len(results)} parsed={parsed}")
    print(f"   by_status : {dict(by_status)}")
    print(f"   by_channel: {dict(by_channel)}")

def report():
    for area in ("t2d", "onc"):
        p = os.path.join(OUT, f"fulltext_fetch_{area}.json")
        if not os.path.exists(p):
            print(f"[{area}] not fetched yet"); continue
        d = load_json(p)
        _summarise(area, d["results"])

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "fetch"
    area = os.environ.get("PILOT_AREA", "t2d")
    if cmd == "fetch":
        fetch_area(area, only_gap=(os.environ.get("FT_ALL") != "1"))
    elif cmd == "report":
        report()
