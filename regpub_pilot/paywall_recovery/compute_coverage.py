"""Step 4 — consolidate COVERAGE (%) and CONTENT-YIELD (%) by legitimate open channel,
and compute the honest recovery-rate estimate for the paywalled loss pocket.

Denominator = the 108 paywalled-pocket papers (main text NOT parsed under the
no-paywall premise). Channels are the ONLY legitimate open ones:
  A  Europe PMC supplementaryFiles API  (OA-subset redistribution)
  B  NCBI PMC OA Web Service            (OA-subset redistribution)
  C  publisher/repository open-license  (gold/hybrid/diamond/green, CC-licensed)
  D  preprint server supplement         (bioRxiv/medRxiv)
Run:  python compute_coverage.py
"""
from __future__ import annotations
import sys, os, json, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
HERE = os.path.dirname(os.path.abspath(__file__)); OUTD = os.path.join(HERE, "out")

def oa_status_map():
    oax = {}
    for f in glob.glob(os.path.join(HERE, "..", "opendata_scan", "cache_upw", "oax_*.json")):
        try: d = json.load(open(f, encoding="utf-8"))
        except Exception: continue
        for w in d.get("results", []):
            pu = (w.get("ids") or {}).get("pmid") or ""
            pmid = pu.rstrip("/").split("/")[-1] if pu else None
            if pmid:
                oa = w.get("open_access") or {}
                oax[str(pmid)] = oa.get("oa_status")
    return oax

def main():
    rows = json.load(open(os.path.join(OUTD, "paywalled_set.json"), encoding="utf-8"))
    supp = {x["pmid"]: x for x in json.load(open(os.path.join(OUTD, "supp_probe.json"), encoding="utf-8"))}
    chC = {x["pmid"]: x for x in json.load(open(os.path.join(OUTD, "channelC_probe.json"), encoding="utf-8"))}
    oax = oa_status_map()
    N = len(rows)
    OPEN_LIC = {"gold", "hybrid", "diamond", "green"}

    # per-paper channel resolution
    for r in rows:
        r["oa_status"] = oax.get(r["pmid"])

    # Channel A/B candidates = has PMCID
    a_cand = [r for r in rows if r["pmcid"]]
    a_open = [r for r in a_cand if supp.get(r["pmid"], {}).get("epmc_supp") == "OPEN"]
    b_open = [r for r in a_cand if supp.get(r["pmid"], {}).get("ncbi_oa") == "OPEN_LINKS"]
    has_suppl_bundle = [r for r in a_cand if r["hasSuppl"] == "Y"]  # EPMC HOLDS a bundle (but gated)

    # Channel C candidates = open-license, no PMCID
    c_cand = [r for r in rows if not r["pmcid"] and r["oa_status"] in OPEN_LIC]
    c_retrieved = [r for r in c_cand if str(chC.get(r["pmid"], {}).get("status", "")).startswith(("open", "cached", "prefetched"))]

    # truly closed (no OA anywhere)
    closed = [r for r in rows if r["oa_status"] in (None, "closed") and not r["pmcid"]]
    bronze = [r for r in rows if r["oa_status"] == "bronze" and not r["pmcid"]]

    def pct(n): return round(100.0 * n / N, 1)

    cov = {
        "denominator_paywalled_pocket": N,
        "by_area": {"onc": sum(1 for r in rows if r["area"] == "onc"),
                    "t2d": sum(1 for r in rows if r["area"] == "t2d")},
        "channel_A_epmc_supp": {
            "candidates_have_pmcid": len(a_cand),
            "epmc_HOLDS_supp_bundle(hasSuppl=Y)": len(has_suppl_bundle),
            "genuinely_open_and_served": len(a_open),
            "all_refused_reason": "every in-PMC paper is isOpenAccess=N (author-manuscript, NOT OA-subset) -> EPMC refuses",
            "coverage_pct": pct(len(a_open))},
        "channel_B_ncbi_oa": {
            "candidates_have_pmcid": len(a_cand),
            "genuinely_open_and_served": len(b_open),
            "coverage_pct": pct(len(b_open))},
        "channel_C_publisher_repo_openlicense": {
            "open_license_candidates": len(c_cand),
            "cleanly_retrieved_200": len(c_retrieved),
            "blocked_or_absent(recorded_not_routed)": len(c_cand) - len(c_retrieved),
            "coverage_pct_of_pocket": pct(len(c_retrieved)),
            "candidate_pmids": [r["pmid"] for r in c_cand]},
        "channel_D_preprint": {
            "candidates": 0,
            "note": "no bioRxiv/medRxiv preprint surfaced (OpenAlex green locations are figshare/inst-repos/journal PDFs, not preprint servers)"},
        "context_no_open_route": {
            "in_PMC_but_gated(author-MS,non-OA-subset)": len(a_cand),
            "truly_closed_no_OA": len(closed),
            "bronze_free-read_not_redistributable": len(bronze)},
    }

    # CONTENT YIELD (of docs actually retrieved via a clean open channel)
    retrieved = c_retrieved  # channel C is the only one that served anything
    yields = {"structured_tables": 0, "km_plus_atrisk": 0, "narrative_only": 0}
    detail = []
    for r in retrieved:
        y = chC.get(r["pmid"], {}).get("yield", [])
        for k in yields:
            if k in y: yields[k] += 1
        detail.append({"pmid": r["pmid"], "oa_status": r["oa_status"], "journal": r["journal"],
                       "yield": y, "kind": chC.get(r["pmid"], {}).get("kind")})

    # RECOVERY buckets (honest split)
    recoveries = {
        "true_open_supplement_of_paywalled_article": [
            {"pmid": "24552155", "channel": "C/green-figshare(CC BY 4.0)",
             "article_access": "subscription (Curr Med Res Opin)",
             "supplement": "icmo_a_896327_sm0001.pdf",
             "content": "Supplemental table 1: HbA1c change from baseline wk16 by dose x prior therapy (LS mean diff vs placebo + 95% CI)",
             "poolable": True, "km": False}],
        "open_license_article_tooling_gap_not_paywall": [
            {"pmid": "25186922", "channel": "C/diamond-J-STAGE",
             "note": "diamond OA (free) main-text PDF; was in pocket only for lack of a PDF parser, not a paywall",
             "content": "structured result tables", "poolable": True, "km": False}],
        "km_plus_atrisk_reconstructions": [],
        "pivotal_survival_HRs_newly_recovered": 0,
    }

    n_true = len(recoveries["true_open_supplement_of_paywalled_article"])
    n_incl_tooling = n_true + len(recoveries["open_license_article_tooling_gap_not_paywall"])
    est = {
        "genuine_open_supplement_recovery_of_poolable_data": {
            "n": n_true, "rate_of_pocket_pct": pct(n_true)},
        "incl_open_license_article_recoverable_with_pdf_parser": {
            "n": n_incl_tooling, "rate_of_pocket_pct": pct(n_incl_tooling)},
        "pivotal_survival_HRs_newly_recovered": 0,
        "km_reconstruction_candidates_in_open_supplements": 0,
    }

    out = {"coverage": cov, "content_yield_of_retrieved": {"n_retrieved": len(retrieved),
            "counts": yields, "detail": detail}, "recoveries": recoveries,
           "recovery_rate_estimate": est}
    json.dump(out, open(os.path.join(OUTD, "coverage_summary.json"), "w", encoding="utf-8"), indent=1)

    print(f"DENOMINATOR (paywalled pocket): {N}  (onc {cov['by_area']['onc']}, t2d {cov['by_area']['t2d']})")
    print(f"\nChannel A  EPMC supp     : {len(a_cand)} pmcid-cands, {len(has_suppl_bundle)} HOLD a bundle, "
          f"{len(a_open)} OPEN  ({pct(len(a_open))}%)")
    print(f"Channel B  NCBI OA       : {len(a_cand)} pmcid-cands, {len(b_open)} OPEN  ({pct(len(b_open))}%)")
    print(f"Channel C  open-license  : {len(c_cand)} cands, {len(c_retrieved)} retrieved  ({pct(len(c_retrieved))}%)")
    print(f"Channel D  preprint      : 0")
    print(f"\nCONTEXT (no open route): PMC-gated {len(a_cand)}, closed {len(closed)}, bronze {len(bronze)}")
    print(f"\nCONTENT YIELD of {len(retrieved)} retrieved: {yields}")
    print(f"\nRECOVERY ESTIMATE:")
    print(f"  genuine open-supplement recovery : {n_true}/{N} = {pct(n_true)}% of pocket")
    print(f"  + open-license article (tooling) : {n_incl_tooling}/{N} = {pct(n_incl_tooling)}% of pocket")
    print(f"  pivotal survival HRs recovered   : 0")
    print(f"  KM+at-risk in any open supplement: 0")

if __name__ == "__main__":
    main()
