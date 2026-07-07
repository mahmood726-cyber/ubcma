"""Second-vendor (agy / Antigravity) cross-check of the full-text extractions.

Decorrelated-blind-spot check (the program's consensus-or-flag primitive): a DIFFERENT
vendor re-extracts the SAME primary outcome from the SAME verbatim excerpt. Agreement
on the point estimate (within tolerance) is independent corroboration; a disagreement is
FLAGGED for human adjudication. This does not gate the pipeline — it audits precision.

Deterministic seam preserved: agy only PROPOSES; the comparison here is model-free.

Usage:
  python src/agy_crosscheck.py prep      # sample emitted datapoints -> agy prompt files
  # (orchestrator runs: agy -p "$(cat prompt)" > result, or this script shells it)
  python src/agy_crosscheck.py run        # shell agy on each prompt, save raw
  python src/agy_crosscheck.py compare    # diff agy vs claude, write report
"""
from __future__ import annotations
import sys, os, io, json, re, glob, subprocess
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
from common import OUT

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
XC = os.path.join(ROOT, "data", "agy_xcheck")
os.makedirs(XC, exist_ok=True)

def _excerpt_for(pmid, area):
    for f in glob.glob(os.path.join(ROOT, "data", "ft_batches", f"{area}_*.json")):
        b = json.load(open(f, encoding="utf-8"))
        for it in b["items"]:
            if str(it["pmid"]) == str(pmid):
                return it
    return None

def _emitted(area):
    p = os.path.join(OUT, f"fulltext_enriched_{area}.jsonl")
    rows = [json.loads(l) for l in open(p, encoding="utf-8")] if os.path.exists(p) else []
    return [r for r in rows if r.get("datapoint")]

PROMPT = """You are a clinical-trial data extractor. Below is a trial's REGISTERED PRIMARY ENDPOINT and verbatim excerpts from its open-access full text. Extract ONLY the registered primary outcome's between-group effect (or single-arm proportion/means if that is the registered primary). Do NOT compute or convert. If the primary outcome's number is not present, abstain.

Return ONLY one JSON object, no prose:
{{"abstain": true|false, "effect_type": "HR|OR|RR|mean_difference|group_means|proportion|null", "point": <number|null>, "ci_lo": <number|null>, "ci_hi": <number|null>, "evidence_quote": "<verbatim substring or null>"}}

REGISTERED PRIMARY ENDPOINT: {endpoint}

FULL-TEXT EXCERPTS:
{excerpt}

Return the JSON object now."""

def prep(k_per_area=6):
    manifest = []
    for area in ("t2d", "onc"):
        em = _emitted(area)
        # spread across effect types + channels
        em.sort(key=lambda r: (r["datapoint"].get("effect_type") or "", r["pmid"]))
        step = max(1, len(em) // k_per_area)
        sample = em[::step][:k_per_area] if em else []
        for r in sample:
            it = _excerpt_for(r["pmid"], area)
            if not it:
                continue
            prompt = PROMPT.format(endpoint=it["primary_endpoint_name"], excerpt=it["extraction_text"][:7000])
            pid = f"{area}_{r['pmid']}"
            open(os.path.join(XC, pid + ".prompt.txt"), "w", encoding="utf-8").write(prompt)
            manifest.append({"id": pid, "area": area, "pmid": r["pmid"],
                             "claude": {k: r["datapoint"].get(k) for k in ("effect_type", "point", "ci_lo", "ci_hi")}})
    json.dump(manifest, open(os.path.join(XC, "_manifest.json"), "w", encoding="utf-8"), indent=2)
    print(f"[prep] wrote {len(manifest)} agy cross-check prompts to {XC}")
    return manifest

def run(model=None, timeout=240):
    man = json.load(open(os.path.join(XC, "_manifest.json"), encoding="utf-8"))
    for e in man:
        outp = os.path.join(XC, e["id"] + ".agy.txt")
        if os.path.exists(outp) and os.path.getsize(outp) > 0:
            print(f"  [cached] {e['id']}"); continue
        prompt = open(os.path.join(XC, e["id"] + ".prompt.txt"), encoding="utf-8").read()
        cmd = ["agy", "-p", prompt] + (["--model", model] if model else [])
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                               encoding="utf-8", errors="replace")
            open(outp, "w", encoding="utf-8").write(r.stdout or "")
            print(f"  [ran] {e['id']} ({len(r.stdout or '')} chars)")
        except subprocess.TimeoutExpired:
            print(f"  [timeout] {e['id']}")

def _parse_obj(txt):
    for m in re.finditer(r"\{", txt):
        depth, i = 0, m.start()
        while i < len(txt):
            if txt[i] == "{": depth += 1
            elif txt[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(txt[m.start():i+1])
                    except Exception:
                        break
            i += 1
    return None

def compare(tol=0.06):
    man = json.load(open(os.path.join(XC, "_manifest.json"), encoding="utf-8"))
    results = []
    for e in man:
        outp = os.path.join(XC, e["id"] + ".agy.txt")
        agy = _parse_obj(open(outp, encoding="utf-8").read()) if os.path.exists(outp) else None
        cl = e["claude"]; verdict = "no_agy_output"
        if agy is not None:
            if agy.get("abstain"):
                verdict = "agy_abstained"
            elif agy.get("point") is not None and cl.get("point") is not None:
                d = abs(float(agy["point"]) - float(cl["point"]))
                rel = d / (abs(float(cl["point"])) + 1e-9)
                verdict = "AGREE" if (d <= tol or rel <= 0.05) else "DISAGREE"
            elif cl.get("point") is None and agy.get("point") is None:
                verdict = "AGREE(means)"
            else:
                verdict = "partial"
        results.append({**e, "agy": agy, "verdict": verdict})
    agree = sum(1 for r in results if r["verdict"].startswith("AGREE"))
    dis = sum(1 for r in results if r["verdict"] == "DISAGREE")
    ab = sum(1 for r in results if r["verdict"] == "agy_abstained")
    summ = {"n": len(results), "agree": agree, "disagree": dis, "agy_abstained": ab,
            "no_output": sum(1 for r in results if r["verdict"] == "no_agy_output"),
            "results": results}
    json.dump(summ, open(os.path.join(OUT, "agy_crosscheck.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(json.dumps({k: summ[k] for k in ("n", "agree", "disagree", "agy_abstained", "no_output")}, indent=2))
    for r in results:
        c = r["claude"]; a = r["agy"] or {}
        print(f"  {r['verdict']:16} {r['id']:16} claude={c.get('point')} [{c.get('ci_lo')},{c.get('ci_hi')}]  agy={a.get('point')}")
    return summ

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "prep"
    if cmd == "prep": prep()
    elif cmd == "run": run(model=(sys.argv[2] if len(sys.argv) > 2 else None))
    elif cmd == "compare": compare()
