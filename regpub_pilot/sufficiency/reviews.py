"""Review registry for the OPEN-DATA SUFFICIENCY study.

Each review is a REAL published meta-analysis, loaded into one common schema:

  Review(
    key, label, area, measure, scale,            # scale in {"log","raw"}
    trials=[Trial(label, year, n, yi, vi, poolable, prov), ...],
    published={est, ci_lo, ci_hi, direction, significant, cite, method},
  )

`yi`/`vi` are on the ANALYSIS scale (log for ratio measures, raw for MD).
`poolable` = would a NO-PAYWALL researcher be able to extract this trial's
primary effect from FREE sources (registry results / OA full text / usable
abstract)?  For the reconstruct-and-beat reviews this is measured (real
extraction succeeded from CT.gov + PubMed abstracts, so all True).  For the
historical metadat reviews it is an ESTIMATE from a transparent rule (see
`poolability_rule`) — deterministic, and swept in the sensitivity analysis.

TWO TIERS of evidence (stated plainly in the report):
  * reconstruct reviews  -> extraction fidelity IS tested (real open-data pull).
  * metadat reviews      -> per-trial data comes from the published dataset, so
                            only COVERAGE + INFLUENCE are tested, not extraction.
"""
from __future__ import annotations
import os, sys, csv, json, math
from dataclasses import dataclass, field

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "src")
sys.path.insert(0, SRC)

METADAT = os.environ.get("METADAT_DIR", r"F:\public-data\metadat")
OUT_RECON_T2D = os.path.join(HERE, "..", "out", "reconstruct_scorecard_t2d.json")
OUT_RECON_ONC = os.path.join(HERE, "..", "out", "reconstruct_scorecard_onc.json")

Z = 1.959963985

# ---- open-data poolability rule (ESTIMATE for historical trials) -------------
# A trial is deemed open-data-poolable if EITHER:
#   P1 registry-results era : first result reporting era (FDAAA 2007 / reg. 2005)
#                             -> year >= YEAR_THRESHOLD
#   P2 landmark / certainly-OA : very large trial, extractable regardless of era
#                             -> total N >= N_THRESHOLD
# Conservative by design (under-counts coverage -> makes "still robust" stronger).
YEAR_THRESHOLD = 2006
N_THRESHOLD = 5000

def is_poolable(year, n, year_thr=YEAR_THRESHOLD, n_thr=N_THRESHOLD):
    p1 = year is not None and year >= year_thr
    p2 = n is not None and n >= n_thr
    return bool(p1 or p2)

poolability_rule = (
    f"open-data-poolable := (year >= {YEAR_THRESHOLD}) OR (total N >= {N_THRESHOLD}); "
    "P1 = registry-results era, P2 = landmark/OA-certain mega-trial. "
    "Deterministic; ESTIMATE for pre-registry trials; swept in sensitivity."
)


@dataclass
class Trial:
    label: str
    year: int | None
    n: int | None
    yi: float          # effect on analysis scale
    vi: float          # variance on analysis scale
    poolable: bool
    prov: str = ""     # provenance / source note


@dataclass
class Review:
    key: str
    label: str
    area: str          # cardiometabolic | oncology | infectious | psychiatry | neuro
    measure: str       # HR | OR | RR | MD | SMD
    scale: str         # log | raw
    favorable: int = -1  # sign of yi that is the BENEFICIAL/positive conclusion
    #                      -1 = lower-is-better (HR/RR/OR of a bad event <1, or MD<0)
    #                      +1 = higher-is-better (OR of a GOOD outcome e.g. response)
    trials: list = field(default_factory=list)
    published: dict = field(default_factory=dict)
    tier: str = ""     # "extraction" (real open pull) | "coverage" (data from dataset)
    note: str = ""
    lit_note: str = ""  # literature context (esp. where model choice changes the verdict)


def conclusion_label(est, significant, favorable):
    """Human conclusion from a pooled estimate: benefit / harm / null."""
    null = 0.0
    if not significant:
        return "null"
    on_favorable_side = (est - null) * favorable > 0
    return "benefit" if on_favorable_side else "harm"


def _clean(s):
    # scrub cp1252 mojibake in reconstruct labels
    return (s.replace("â€”", " - ").replace("â€™", "'")
             .replace("â€", "-"))


def _se_logratio(point, lo, hi):
    if point and lo and hi and lo > 0 and hi > 0:
        return (math.log(hi) - math.log(lo)) / (2 * Z)
    if point and hi and point > 0 and hi > 0:
        return (math.log(hi) - math.log(point)) / Z
    if point and lo and point > 0 and lo > 0:
        return (math.log(point) - math.log(lo)) / Z
    return None


# ---------------------------------------------------------------------------
# TIER 1 — reconstruct-and-beat reviews (real open-data extraction, all poolable)
# ---------------------------------------------------------------------------
_RECON_AREA = {
    "sglt2_cvot": "cardiometabolic", "glp1_cvot": "cardiometabolic",
    "dpp4_cvot": "cardiometabolic", "io_nsclc_os": "oncology",
    "cdk46_pfs": "oncology", "parp_ovarian_pfs": "oncology",
}
# published-conclusion significance is read from the benchmark CI (excludes null?)
def _load_reconstruct():
    reviews = []
    for path in (OUT_RECON_T2D, OUT_RECON_ONC):
        if not os.path.exists(path):
            continue
        data = json.load(open(path, encoding="utf-8"))
        for r in data:
            b = r["benchmark"]
            trials = []
            for s in r["studies"]:
                hr = s.get("hr")
                ci = s.get("ci") or [None, None]
                if not hr:
                    continue
                se = _se_logratio(hr, ci[0], ci[1])
                if not se:
                    continue
                # every reconstruct trial was resolved from a FREE source
                # (registry results or PubMed abstract) -> poolable = True (measured)
                trials.append(Trial(
                    label=s["name"], year=None, n=None,
                    yi=math.log(hr), vi=se * se, poolable=True,
                    prov=s.get("source", "")))
            sig = not (b["ci_lo"] <= 1.0 <= b["ci_hi"])  # published CI excludes null?
            est_log = math.log(b["est"])
            fav = -1  # HR/OR<1 = benefit for MACE/OS/PFS events
            reviews.append(Review(
                key=r["key"], label=_clean(r["label"]),
                area=_RECON_AREA.get(r["key"], "?"),
                measure=b["measure"], scale="log", favorable=fav, trials=trials,
                published={"est": est_log,
                           "ci_lo": math.log(b["ci_lo"]), "ci_hi": math.log(b["ci_hi"]),
                           "significant": sig,
                           "conclusion": conclusion_label(est_log, sig, fav),
                           "cite": b["cite"], "method": b["method"], "k": b["k"]},
                tier="extraction",
                note="all trials resolved from FREE sources (registry results / PubMed abstract)"))
    return reviews


# ---------------------------------------------------------------------------
# TIER 2 — historical metadat reviews (real full trial data; coverage/influence)
# ---------------------------------------------------------------------------
def _read_csv(name):
    path = os.path.join(METADAT, name)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _logratio_2x2(a, b, c, d, kind="OR"):
    """2x2: a=events_trt, b=nonevents_trt, c=events_ctrl, d=nonevents_ctrl.
    Returns (yi, vi) for log OR or log RR, Haldane-Anscombe 0.5 only if a zero cell."""
    if 0 in (a, b, c, d):
        a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
    if kind == "OR":
        yi = math.log((a * d) / (b * c))
        vi = 1 / a + 1 / b + 1 / c + 1 / d
    else:  # RR
        n1, n2 = a + b, c + d
        yi = math.log((a / n1) / (c / n2))
        vi = 1 / a - 1 / n1 + 1 / c - 1 / n2
    return yi, vi


def _load_li2007():
    """IV magnesium in acute MI (Li 2007). log OR of death, Mg vs control.
    Includes ISIS-4 (n=58050) & MAGIC — the textbook weight-concentration case."""
    rows = _read_csv("dat.li2007.csv")
    trials = []
    for r in rows:
        ai, n1i, ci, n2i = int(r["ai"]), int(r["n1i"]), int(r["ci"]), int(r["n2i"])
        bi, di = n1i - ai, n2i - ci
        yi, vi = _logratio_2x2(ai, bi, ci, di, "OR")
        n = n1i + n2i
        yr = int(r["year"])
        trials.append(Trial(label=f"{r['study']} {yr}", year=yr, n=n,
                            yi=yi, vi=vi, poolable=is_poolable(yr, n),
                            prov=f"deaths {ai}/{n1i} vs {ci}/{n2i}"))
    fav = -1  # OR of death < 1 = benefit
    pub = _fullset_benchmark(trials, fav,
                             cite="metadat dat.li2007 (IV Mg in acute MI); RE full-set pooled")
    return Review("iv_mg_mi", "IV magnesium in acute MI (mortality)", "cardiometabolic",
                  "OR", "log", favorable=fav, trials=trials, published=pub, tier="coverage",
                  note="ISIS-4 + MAGIC hold most FIXED-effect weight; RE up-weights the small positive trials",
                  lit_note="Textbook controversy: RE pooling of all 22 trials is protective-significant "
                           "(the pre-ISIS-4 published conclusion); ISIS-4 mega-trial made the fixed/"
                           "large-trial view NULL. Model choice flips the answer.")


def _load_bcg():
    """BCG vaccine vs TB (Colditz/metadat bcg). log RR of TB, vaccine vs control.
    Effect strongly modified by latitude; big trials are low-latitude (near-null)."""
    rows = _read_csv("dat.bcg.csv")
    trials = []
    for r in rows:
        tpos, tneg, cpos, cneg = int(r["tpos"]), int(r["tneg"]), int(r["cpos"]), int(r["cneg"])
        yi, vi = _logratio_2x2(tpos, tneg, cpos, cneg, "RR")
        n = tpos + tneg + cpos + cneg
        yr = int(r["year"])
        trials.append(Trial(label=f"{r['author']} {yr}", year=yr, n=n,
                            yi=yi, vi=vi, poolable=is_poolable(yr, n),
                            prov=f"TB {tpos}/{tpos+tneg} vs {cpos}/{cpos+cneg}, lat={r['ablat']}"))
    fav = -1  # RR of TB < 1 = benefit
    pub = _fullset_benchmark(trials, fav,
                             cite="metadat dat.bcg (Colditz 1994 JAMA); RE full-set pooled")
    return Review("bcg_tb", "BCG vaccination vs tuberculosis", "infectious",
                  "RR", "log", favorable=fav, trials=trials, published=pub, tier="coverage",
                  note="latitude effect-modifier: large open trials are low-latitude (near-null) -> subset biased",
                  lit_note="Efficacy rises with distance from equator; the large (open) trials are "
                           "tropical/near-null, the strongly-protective trials are old high-latitude ones.")


def _load_linde2015_hyp():
    """St John's wort (hypericum) vs placebo for depression: response (log OR).
    linde2015 is a 3-arm network; we extract the hypericum-vs-placebo direct contrast."""
    rows = _read_csv("dat.linde2015.csv")
    trials = []
    for r in rows:
        arms = {}
        for i in (1, 2, 3):
            t = (r.get(f"treatment{i}") or "").strip()
            n = r.get(f"n{i}") or ""
            resp = r.get(f"resp{i}") or ""
            if t and n and resp:
                arms[t] = (int(n), int(resp))
        if "Hypericum" in arms and "Placebo" in arms:
            nh, rh = arms["Hypericum"]
            npl, rpl = arms["Placebo"]
            yi, vi = _logratio_2x2(rh, nh - rh, rpl, npl - rpl, "OR")
            yr = int(r["year"]); n = nh + npl
            trials.append(Trial(label=f"{r['author']} {yr}", year=yr, n=n,
                                yi=yi, vi=vi, poolable=is_poolable(yr, n),
                                prov=f"resp {rh}/{nh} vs {rpl}/{npl}"))
    fav = +1  # OR of RESPONSE > 1 = benefit (higher-is-better outcome)
    pub = _fullset_benchmark(trials, fav,
                             cite="metadat dat.linde2015 (Hypericum vs placebo direct contrast)")
    return Review("hypericum_dep", "St John's wort (hypericum) vs placebo, depression response",
                  "psychiatry", "OR", "log", favorable=fav, trials=trials, published=pub,
                  tier="coverage",
                  note="hypericum-vs-placebo direct contrast from the linde2015 network")


def _load_senn2013_metformin():
    """Diabetes: metformin vs placebo, HbA1c change (raw mean difference).
    senn2013 is an NMA dataset; we take the direct metformin-vs-placebo studies."""
    rows = _read_csv("dat.senn2013.csv")
    # group by study; keep studies that have BOTH metformin and placebo arms
    by_study = {}
    for r in rows:
        by_study.setdefault(r["study"], {})[r["treatment"]] = r
    trials = []
    for study, arms in by_study.items():
        if "metformin" in arms and "placebo" in arms:
            m = arms["metformin"]; p = arms["placebo"]
            n1, mm, s1 = int(m["ni"]), float(m["mi"]), float(m["sdi"])
            n2, mp, s2 = int(p["ni"]), float(p["mi"]), float(p["sdi"])
            yi = mm - mp
            vi = s1 * s1 / n1 + s2 * s2 / n2
            yr = None
            # extract year from "De Fronzo (1995)" style
            import re
            mt = re.search(r"\((\d{4})\)", study)
            if mt:
                yr = int(mt.group(1))
            n = n1 + n2
            trials.append(Trial(label=study, year=yr, n=n, yi=yi, vi=vi,
                                poolable=is_poolable(yr, n),
                                prov=f"HbA1c d {mm}({s1}) vs {mp}({s2})"))
    fav = -1  # MD of HbA1c < 0 = benefit (lower-is-better)
    pub = _fullset_benchmark(trials, fav,
                             cite="metadat dat.senn2013 (metformin vs placebo, HbA1c)")
    return Review("metformin_hba1c", "Metformin vs placebo, HbA1c reduction",
                  "cardiometabolic", "MD", "raw", favorable=fav, trials=trials, published=pub,
                  tier="coverage",
                  note="metformin-vs-placebo direct contrast from the senn2013 network")


def _fullset_benchmark(trials, favorable, cite=""):
    """PUBLISHED-truth pooled estimate = REML+HKSJ over the FULL trial set. For the
    metadat datasets the full-set RE pooled IS the canonical documented result
    (metafor examples reproduce these). NOTHING is hardcoded — the conclusion is
    computed, so where model choice matters (IV Mg: RE protective vs fixed null)
    the analysis surfaces it rather than us asserting an answer."""
    from pool import pool
    yi = [t.yi for t in trials]; vi = [t.vi for t in trials]
    p = pool(yi, vi, method="REML", hksj=True)
    sig = not (p["ci_lo"] <= 0.0 <= p["ci_hi"])
    return {"est": p["est"], "ci_lo": p["ci_lo"], "ci_hi": p["ci_hi"],
            "significant": sig, "conclusion": conclusion_label(p["est"], sig, favorable),
            "tau2": p["tau2"], "I2": p["I2"],
            "cite": cite, "method": "REML+HKSJ (full published set)", "k": len(trials)}


def all_reviews():
    reviews = _load_reconstruct()
    for loader in (_load_li2007, _load_bcg,
                   _load_linde2015_hyp, _load_senn2013_metformin):
        try:
            reviews.append(loader())
        except Exception as e:
            sys.stderr.write(f"[reviews] loader {loader.__name__} failed: {e}\n")
    return reviews


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    for r in all_reviews():
        npool = sum(1 for t in r.trials if t.poolable)
        bt = (lambda x: round(math.exp(x), 3)) if r.scale == "log" else (lambda x: round(x, 3))
        p = r.published
        print(f"{r.key:18s} {r.area:15s} k={len(r.trials):2d} pool={npool:2d} fav={r.favorable:+d} "
              f"tier={r.tier:10s} pub={p['conclusion']:8s} est={bt(p['est'])} sig={p['significant']}")
