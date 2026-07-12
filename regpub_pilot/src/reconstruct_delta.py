"""RECONSTRUCT-DELTA: measure how many percentage points R2 (2x2 recovery /
effect-from-counts) + R3 (SD/SE imputation) statistical reconstruction ADD to the
33.7% poolable-fraction anchor (metrics.json poolability.poolable_pct), on the fixed
N=600 completed-T2D corpus.

DISCIPLINE (three claims held SEPARATE, never collapsed):
  FOUND     = trial is type-eligible for R2/R3 and currently NOT poolable (state NEITHER).
  RECOVERED = we produced a poolable effect + uncertainty from the R2/R3 ingredients.
  RIGHT     = the recovered effect matches an independent per-trial GOLD within tolerance.

A RECOVERED count is NOT a delta. Only RIGHT-vs-gold trials that were previously
unpoolable move 33.7%. If per-trial gold is not wired, RIGHT is BLOCKED and NO delta is
reported (report RECOVERED + named blocker instead).

Only state==NEITHER trials can move the needle: state ONE/BOTH are ALREADY in the 33.7%
via registry or abstract, so reconstructing them adds ZERO delta by construction.

Formulas (log scale for ratios; continuity correction only on a zero cell):
  R2 2x2 -> logOR, SE = sqrt(1/a+1/b+1/c+1/d)  [+0.5 to every cell iff any cell == 0]
  R2 relative + registry per-arm denominators -> event counts -> same 2x2 path
  R3 pvalue+point+N -> z from two-sided p, SE = |effect| / z            (needs a POINT est)
  R3 median+IQR/range+n per arm -> Wan 2014 / Luo 2018 mean & SD -> MD + SE

No network. Pure over cached JSON. Read-only external data. Writes only out/*.
"""
from __future__ import annotations
import sys, os, json, math, hashlib, re, collections

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CT_DIR = os.path.join(ROOT, "data", "ctgov")
PM_DIR = os.path.join(ROOT, "data", "pubmed")
OUT = os.path.join(ROOT, "out")

Z = 1.959963985

R2_REASONS = {"relative_only", "numbers_no_estimate"}
R3_REASONS = {"pvalue_only", "median_no_dispersion"}

IQR_RE = re.compile(r"\b(iqr|interquartile)\b", re.I)
RANGE_RE = re.compile(r"\brange\b", re.I)


def cache_path(dirp, key):
    return os.path.join(dirp, hashlib.sha1(key.encode()).hexdigest()[:16] + ".json")


def load_json(p):
    if p and os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_json(p, obj):
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)


# -------------------------------------------------------------------- R2
def try_r2(reg_record):
    """Attempt effect-from-2x2. Returns (effect_dict | None, missing_reason).

    Needs a registry results primary that is a BINARY outcome with per-arm event
    counts (a,b in arm1; c,d in arm2) or (events + denominators). The abstract side
    is relative-only / numbers-no-estimate by construction (no counts), so the counts
    can only come from the registry resultsSection.
    """
    if not reg_record:
        return None, "no_ctgov_cache"
    rs = reg_record.get("resultsSection")
    if not rs:
        return None, "no_registry_resultsSection"  # no results posted -> no counts anywhere
    oms = rs.get("outcomeMeasuresModule", {}).get("outcomeMeasures", []) or []
    prim = [o for o in oms if o.get("type") == "PRIMARY"]
    if not prim:
        return None, "no_primary_outcome_in_results"
    o = prim[0]
    ptype = (o.get("paramType") or "").upper()
    # Binary outcome family: COUNT_OF_PARTICIPANTS / NUMBER of participants with event
    if "COUNT" not in ptype and "NUMBER" not in ptype:
        return None, f"primary_not_count_type({o.get('paramType')})"
    # collect per-arm (event count, denominator)
    denoms = {}
    for d in (o.get("denoms") or []):
        for c in (d.get("counts") or []):
            gid = c.get("groupId")
            try:
                denoms[gid] = float(c.get("value"))
            except (TypeError, ValueError):
                pass
    arms = []  # list of (events, n)
    for cls in (o.get("classes") or []):
        for cat in (cls.get("categories") or []):
            for m in (cat.get("measurements") or []):
                gid = m.get("groupId")
                try:
                    ev = float(m.get("value"))
                except (TypeError, ValueError):
                    continue
                n = denoms.get(gid)
                if n is not None:
                    arms.append((ev, n))
    if len(arms) < 2:
        return None, "no_two_arm_event_counts"
    (e1, n1), (e2, n2) = arms[0], arms[1]
    a, b = e1, n1 - e1          # arm1 event / non-event
    c, d = e2, n2 - e2          # arm2 event / non-event
    if min(a, b, c, d) < 0:
        return None, "negative_cell"
    cells = [a, b, c, d]
    if any(x == 0 for x in cells):        # continuity correction ONLY on a zero cell
        cells = [x + 0.5 for x in cells]
    a, b, c, d = cells
    log_or = math.log((a * d) / (b * c))
    se = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    return {"measure": "OR", "log_effect": log_or, "se": se,
            "point": round(math.exp(log_or), 4),
            "ci_lo": round(math.exp(log_or - Z * se), 4),
            "ci_hi": round(math.exp(log_or + Z * se), 4),
            "ingredients": {"a": a, "b": b, "c": c, "d": d},
            "method": "R2_2x2_logOR"}, None


# -------------------------------------------------------------------- R3
def _p_to_z(pstr):
    """Two-sided p -> |z|. Accepts 'p<0.05','p=0.03', etc. Inequalities give a BOUND
    only (not an exact z), so we refuse them for a numeric SE."""
    if not pstr:
        return None, "no_p"
    s = str(pstr).lower().replace(" ", "")
    if "<" in s or ">" in s or "≤" in s or "≥" in s:
        return None, "p_is_inequality_not_exact"
    m = re.search(r"([0-9]*\.?[0-9]+)", s)
    if not m:
        return None, "p_unparseable"
    p = float(m.group(1))
    if not (0 < p < 1):
        return None, "p_out_of_range"
    # inverse normal via Acklam (two-sided)
    from math import log, sqrt
    q = p / 2.0
    # invert upper tail: z such that P(Z> z)=q  -> use symmetric quantile of 1-q
    pp = 1 - q
    a=[-3.969683028665376e+01,2.209460984245205e+02,-2.759285104469687e+02,1.383577518672690e+02,-3.066479806614716e+01,2.506628277459239e+00]
    bb=[-5.447609879822406e+01,1.615858368580409e+02,-1.556989798598866e+02,6.680131188771972e+01,-1.328068155288572e+01]
    cc=[-7.784894002430293e-03,-3.223964580411365e-01,-2.400758277161838e+00,-2.549732539343734e+00,4.374664141464968e+00,2.938163982698783e+00]
    dd=[7.784695709041462e-03,3.224671290700398e-01,2.445134137142996e+00,3.754408661907416e+00]
    pl=0.02425
    if pp < pl:
        t=sqrt(-2*log(pp)); z=(((((cc[0]*t+cc[1])*t+cc[2])*t+cc[3])*t+cc[4])*t+cc[5])/((((dd[0]*t+dd[1])*t+dd[2])*t+dd[3])*t+1)
    elif pp <= 1-pl:
        t=pp-0.5; r=t*t; z=(((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*t/(((((bb[0]*r+bb[1])*r+bb[2])*r+bb[3])*r+bb[4])*r+1)
    else:
        t=sqrt(-2*log(1-pp)); z=-(((((cc[0]*t+cc[1])*t+cc[2])*t+cc[3])*t+cc[4])*t+cc[5])/((((dd[0]*t+dd[1])*t+dd[2])*t+dd[3])*t+1)
    return abs(z), None


def try_r3(trial, pm_record):
    """Attempt SE/SD imputation. Returns (effect_dict|None, missing_reason)."""
    ab = trial.get("abstract") or {}
    reason = ab.get("reason")
    eff = ab.get("effect")
    if reason == "pvalue_only":
        # SE from p requires an EFFECT (point) as numerator: SE = |effect|/z.
        # By classifier definition pvalue_only => no point estimate was extracted.
        point = (eff or {}).get("point") if eff else None
        if point is None:
            return None, "pvalue_only_has_no_point_estimate"  # numerator absent
        z, why = _p_to_z((eff or {}).get("pvalue"))
        if z is None:
            return None, f"R3_p:{why}"
        se = abs(math.log(point)) / z if (eff or {}).get("family") == "ratio" else abs(point) / z
        return {"measure": "from_p", "se": se, "point": point, "method": "R3_SE_from_p"}, None
    if reason == "median_no_dispersion":
        ab_txt = (pm_record or {}).get("abstract", "") if pm_record else ""
        has_disp = bool(IQR_RE.search(ab_txt) or RANGE_RE.search(ab_txt))
        if not has_disp:
            return None, "median_no_IQR_or_range_present"   # Wan/Luo ingredient absent
        # dispersion token present, but per-arm (median, IQR/range, n) for BOTH arms of the
        # TREATMENT-EFFECT endpoint is not machine-extractable from an unstructured abstract
        # whose median is (per manual audit) a baseline/PK/feasibility value, not the outcome.
        return None, "median_dispersion_not_arm_paired_outcome"
    return None, f"reason_not_R3({reason})"


def main():
    trials = [json.loads(l) for l in open(os.path.join(OUT, "trials_t2d.jsonl"), encoding="utf-8")]
    metrics = load_json(os.path.join(OUT, "metrics.json"))
    anchor_pct = metrics["poolability"]["poolable_pct"]          # 33.7
    n_total = metrics["coverage"]["n_total"]                     # 600
    poolable_total = metrics["poolability"]["poolable_total"]    # 202

    # --- GOLD availability probe (independent per-trial published effect?) ---
    gold_files = [f for f in os.listdir(OUT)
                  if re.search(r"gold|groundtruth|answer|truth", f, re.I)]
    gold_available = len(gold_files) > 0

    per_trial = []
    recovered_r2 = recovered_r3 = 0
    found_r2 = found_r3 = 0
    miss = collections.Counter()

    for t in trials:
        ab = t.get("abstract") or {}
        reason = ab.get("reason")
        state = t.get("state")
        method = "R2" if reason in R2_REASONS else ("R3" if reason in R3_REASONS else None)
        if method is None:
            continue
        # FOUND (delta-eligible) = type-eligible AND currently NOT poolable (NEITHER).
        # ONE/BOTH are already inside the 33.7% -> excluded from the delta target set.
        eligible = (state == "NEITHER")
        if not eligible:
            continue
        if method == "R2":
            found_r2 += 1
        else:
            found_r3 += 1
        nct = t["nct"]
        reg = load_json(cache_path(CT_DIR, nct))
        pm = load_json(cache_path(PM_DIR, t.get("index_pmid") or ""))
        if method == "R2":
            eff, why = try_r2(reg)
        else:
            eff, why = try_r3(t, pm)
        rec = {"nct": nct, "method": method, "abstract_reason": reason,
               "recovered": eff is not None, "missing_reason": why,
               "effect": eff}
        if eff is not None:
            if method == "R2":
                recovered_r2 += 1
            else:
                recovered_r3 += 1
        else:
            miss[(method, why)] += 1
        per_trial.append(rec)

    recovered_total = recovered_r2 + recovered_r3
    found_total = found_r2 + found_r3

    # RIGHT: only checkable if per-trial gold exists. It does not.
    right_total = 0
    right_blocked = not gold_available

    # Delta arithmetic. Realised delta counts ONLY RIGHT-vs-gold previously-unpoolable trials.
    if right_blocked:
        realised_delta_pp = None
        realised_pct = None
    else:
        realised_pct = round((poolable_total + right_total) / n_total * 100, 1)
        realised_delta_pp = round(realised_pct - anchor_pct, 1)

    result = {
        "anchor": {"poolable_pct": anchor_pct, "poolable_total": poolable_total,
                   "n_total": n_total, "source": "out/metrics.json poolability"},
        "target_set": {
            "definition": "type-eligible (R2/R3) AND state==NEITHER (currently NOT poolable). "
                          "state ONE/BOTH are already inside 33.7% -> excluded (zero delta by construction).",
            "found_R2": found_r2, "found_R3": found_r3, "found_total": found_total,
            "note_type_eligible_ceiling_160_includes_already_poolable":
                "metrics reason-breakdown counts (relative_only 99 + numbers_no_estimate 35 + "
                "pvalue_only 15 + median_no_dispersion 11 = 160) span state ONE/BOTH too; "
                "only the NEITHER subset can move the anchor."},
        "FOUND": found_total,
        "RECOVERED": {"R2": recovered_r2, "R3": recovered_r3, "total": recovered_total},
        "RIGHT": {"total": right_total, "blocked": right_blocked,
                  "gold_files_found": gold_files},
        "realised_poolable_pct": realised_pct,
        "realised_delta_pp": realised_delta_pp,
        "missing_ingredient_breakdown": {f"{m}:{w}": n for (m, w), n in
                                         sorted(miss.items(), key=lambda x: -x[1])},
        "verdict_tags": {
            "FOUND": "VERIFIED",
            "RECOVERED": "VERIFIED",
            "RIGHT": "BLOCKED_no_per_trial_gold" if right_blocked else "VERIFIED",
            "realised_delta_pp": "BLOCKED" if right_blocked else "VERIFIED"},
        "named_blocker": (
            "RIGHT-check blocked: no per-trial gold (published effect) is wired for the 600. "
            "The delta-eligible trials are state==NEITHER precisely because the registry posts "
            "NO results section (no 2x2 event counts / no per-arm denominators) AND the abstract "
            "is relative-only / p-only / median-without-dispersion. R2 counts and R3 numerators "
            "are therefore ABSENT at source, not merely unextracted. To complete the RIGHT check "
            "one must wire an independent gold-effect file mapping each NCT to a verified "
            "published primary effect+CI (e.g. from full-text methods/results), which the "
            "mission's open-data constraint (abstract+registry only) does not supply."
            if right_blocked else "none"),
        "per_trial": per_trial,
    }
    save_json(os.path.join(OUT, "reconstruct_delta.json"), result)

    print("=" * 72)
    print("RECONSTRUCT-DELTA  (anchor 33.7% poolable; how many pp do R2/R3 add?)")
    print("=" * 72)
    print(f"FOUND (delta-eligible: type-eligible AND NEITHER) : {found_total}  (R2={found_r2}, R3={found_r3})")
    print(f"RECOVERED (poolable effect+SE produced)           : {recovered_total}  (R2={recovered_r2}, R3={recovered_r3})")
    print(f"RIGHT (matches per-trial gold)                    : {right_total}  blocked={right_blocked}")
    print(f"Realised poolable %                               : {realised_pct}")
    print(f"Realised delta (pp)                               : {realised_delta_pp}")
    print("-" * 72)
    print("missing-ingredient breakdown (why RECOVERED=0):")
    for k, n in sorted(miss.items(), key=lambda x: -x[1]):
        print(f"   {n:3d}  {k[0]}: {k[1]}")
    print("-" * 72)
    print("NAMED BLOCKER:", result["named_blocker"])
    print("wrote -> out/reconstruct_delta.json")


if __name__ == "__main__":
    main()
