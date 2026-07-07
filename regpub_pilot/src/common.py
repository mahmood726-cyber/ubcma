"""Shared config + polite cached HTTP layer for the reg-vs-pub discrepancy pilot.

MISSION: serve a scientist with NO paywalled full-text access. Every source used
here is openly accessible (ClinicalTrials.gov API v2 + PubMed E-utilities).

DETERMINISTIC-CORE SEAM INVARIANT: nothing in the extraction / diff / pooling path
calls a network model. All classification is rule-based, offline-serializable JSON.
The only network use is *data acquisition* (this file), which is cached to disk so
downstream analysis runs fully offline and reproducibly.
"""
from __future__ import annotations
import json, os, time, hashlib, urllib.request, urllib.parse, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
CT_DIR = os.path.join(DATA, "ctgov")
PM_DIR = os.path.join(DATA, "pubmed")
OUT = os.path.join(ROOT, "out")
for d in (DATA, CT_DIR, PM_DIR, OUT):
    os.makedirs(d, exist_ok=True)

CTGOV_BASE = "https://clinicaltrials.gov/api/v2"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# PubMed asks for <=3 req/s without an API key. We stay well under.
_LAST = {"t": 0.0}
def _throttle(min_gap=0.4):
    dt = time.time() - _LAST["t"]
    if dt < min_gap:
        time.sleep(min_gap - dt)
    _LAST["t"] = time.time()

def http_get(url, timeout=60, retries=4, min_gap=0.4, accept="application/json"):
    """GET with bounded exponential backoff. Fails closed (raises) on exhaustion —
    never returns an error page as if it were data (lessons.md: fail closed on
    malformed remote payloads)."""
    last = None
    for i in range(retries):
        _throttle(min_gap)
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "ubcma-regpub-pilot/0.1 (research; contact via repo)",
                "Accept": accept,
            })
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(min(2 ** i, 8))
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            time.sleep(min(2 ** i, 8))
    raise RuntimeError(f"GET failed after {retries} tries: {url} :: {last}")

def cache_path(dirp, key):
    h = hashlib.sha1(key.encode()).hexdigest()[:16]
    return os.path.join(dirp, f"{h}.json")

def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    os.replace(tmp, path)

# ---- therapeutic-area parameterization ----------------------------------------
# AREA selects the working set. Caches (ctgov/, pubmed/) are hash-keyed by NCT/PMID
# so they are shared safely across areas; index/links/outputs are area-suffixed so a
# second area (oncology) never clobbers the first (t2d).
AREA = os.environ.get("PILOT_AREA", "t2d")
_CONDITIONS = {"t2d": "type 2 diabetes", "onc": "cancer"}
CONDITION = os.environ.get("PILOT_CONDITION", _CONDITIONS.get(AREA, "type 2 diabetes"))

def index_path(area=None):
    return os.path.join(DATA, f"ctgov_index_{area or AREA}.json")

def links_path(area=None):
    return os.path.join(DATA, f"links_{area or AREA}.json")

def trials_out(area=None):
    return os.path.join(OUT, f"trials_{area or AREA}.jsonl")

def metrics_out(area=None):
    return os.path.join(OUT, f"metrics_{area or AREA}.json")
