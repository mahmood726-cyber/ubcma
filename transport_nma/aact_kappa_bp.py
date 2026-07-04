"""FOURTH-DOMAIN external validation of the transport-NMA registry-severity model: antihypertensive
therapy / systolic blood-pressure (SBP) reduction. Chosen to fix the lipid limitation (only 2 classes
had registered-only support): antihypertensives span 6-7 drug classes with a mix of old (diuretic,
beta-blocker) and new agents, on a single standardised continuous unit (mmHg, like HbA1c) -- so a FORMAL
corr(kappa_MD, 1-lambda) over many classes should be testable, unlike publication-saturated lipids.

Primary measure = |MD| in mmHg (single-unit, as in the diabetes HbA1c analysis); scale-invariant z =
|MD|/SE reported as robustness. kappa_MD(c) = mean|MD|_published / mean|MD|_registered-only - 1. Split
published (PubMed-linked) vs registered-only exactly as the diabetes/antidepressant/lipid analyses.
Truth-first: honest whether corr(kappa, 1-lambda) reproduces the diabetes +0.50 or not.
"""
import duckdb, json, io, sys
import numpy as np
from pathlib import Path
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

A = r"F:\AACT-storage\AACT\2026-04-12"
HERE = Path(__file__).resolve().parent
Z975 = 1.959963984540054
con = duckdb.connect()


def t(n):
    return f"read_csv('{A}/{n}.txt', delim='|', header=true, quote='', ignore_errors=true, auto_detect=true, all_varchar=true)"


CLASSES = {
    'ACEi': ['pril'],                       # enalapril, lisinopril, ramipril, captopril, perindopril...
    'ARB': ['sartan'],                      # losartan, valsartan, candesartan, telmisartan...
    'CCB': ['dipine', 'diltiazem', 'verapamil'],
    'beta_blocker': ['olol', 'carvedilol', 'labetalol'],
    'diuretic': ['thiazide', 'chlorthalidone', 'indapamide', 'furosemide', 'amiloride', 'spironolactone'],
    'alpha_blocker': ['doxazosin', 'prazosin', 'terazosin'],
    'central': ['clonidine', 'methyldopa', 'moxonidine'],
    'renin_inhibitor': ['aliskiren'],
}

con.execute(f"""CREATE TEMP TABLE htn AS SELECT DISTINCT nct_id FROM {t('conditions')}
 WHERE lower(name) LIKE '%hypertension%' OR lower(name) LIKE '%high blood pressure%'
   OR lower(name) LIKE '%blood pressure%';""")
con.execute(f"""CREATE TEMP TABLE pub AS SELECT DISTINCT nct_id FROM {t('study_references')}
 WHERE reference_type IN ('DERIVED','RESULT') AND pmid IS NOT NULL AND pmid<>'';""")
pubset = set(r[0] for r in con.execute("SELECT nct_id FROM pub").fetchall())
con.execute(f"""CREATE TEMP TABLE iv AS SELECT i.nct_id, lower(i.name) nm,
   (s.results_first_posted_date IS NOT NULL AND s.results_first_posted_date<>'') posted
 FROM {t('interventions')} i JOIN htn d ON i.nct_id=d.nct_id JOIN {t('studies')} s ON i.nct_id=s.nct_id;""")
LAM = {}
for c, kws in CLASSES.items():
    cond = " OR ".join(f"nm LIKE '%{k}%'" for k in kws)
    tot, pos = con.execute(f"SELECT count(DISTINCT nct_id), count(DISTINCT CASE WHEN posted THEN nct_id END) FROM iv WHERE {cond}").fetchone()
    LAM[c] = (pos / tot) if tot else None

rows = con.execute(f"""SELECT o.nct_id, lower(coalesce(o.units,'')) units, TRY_CAST(a.param_value AS DOUBLE) md,
   TRY_CAST(a.ci_lower_limit AS DOUBLE) lo, TRY_CAST(a.ci_upper_limit AS DOUBLE) hi
 FROM {t('outcomes')} o JOIN {t('outcome_analyses')} a ON a.outcome_id=o.id JOIN htn d ON o.nct_id=d.nct_id
 WHERE (lower(o.title) LIKE '%systolic%' OR lower(o.title) LIKE '%sbp%')
   AND lower(coalesce(a.param_type,'')) LIKE '%mean difference%' AND a.param_value IS NOT NULL""").fetchall()

con.execute(f"""CREATE TEMP TABLE ivn AS SELECT nct_id, lower(name) nm FROM {t('interventions')} WHERE nct_id IN (SELECT nct_id FROM htn);""")
names = {}
for nct, nm in con.execute("SELECT nct_id, nm FROM ivn").fetchall():
    names.setdefault(nct, []).append(nm or "")


def classes_of(nct):
    s = " ".join(names.get(nct, []))
    return [c for c, kws in CLASSES.items() if any(k in s for k in kws)]


perM = {c: {'pub': [], 'reg': []} for c in CLASSES}   # |MD| mmHg (single-unit primary)
perZ = {c: {'pub': [], 'reg': []} for c in CLASSES}   # z = |MD|/SE (scale-invariant robustness)
nm_ = nz = 0
for nct, units, md, lo, hi in rows:
    if md is None or not np.isfinite(md):
        continue
    cs = classes_of(nct)
    if not cs:
        continue
    b = 'pub' if nct in pubset else 'reg'
    amd = abs(md)
    # single-unit mmHg subset (exclude %/other units); SBP diffs plausibly <=60 mmHg
    if amd <= 60 and ('mmhg' in units or 'mm hg' in units or units.strip() == ''):
        nm_ += 1
        for c in cs:
            perM[c][b].append(amd)
    if lo is not None and hi is not None and np.isfinite(lo) and np.isfinite(hi) and hi > lo:
        se = (hi - lo) / (2 * Z975)
        z = amd / se if se > 0 else None
        if z is not None and np.isfinite(z) and z <= 50:
            nz += 1
            for c in cs:
                perZ[c][b].append(z)


def boot_gap(p, r, B=4000, seed=3):
    rng = np.random.default_rng(seed)
    ks = []
    for _ in range(B):
        pb = p[rng.integers(0, len(p), len(p))]
        rb = r[rng.integers(0, len(r), len(r))]
        if rb.mean() > 0:
            ks.append(pb.mean() / rb.mean() - 1.0)
    return float(np.quantile(ks, 0.025)), float(np.quantile(ks, 0.975))


def gap_table(per, label, key):
    print(f"\n--- {label} ---")
    print(f"  {'class':16}{'1-lam':>7}{'n_pub':>7}{'n_reg':>7}{'m_pub':>9}{'m_reg':>9}{'kappa':>9}{'  95% CI (trial boot)':>22}")
    xs, ys, ws = [], [], []
    out = {}
    for c in CLASSES:
        p = np.array(per[c]['pub']); r = np.array(per[c]['reg']); lam = LAM[c]
        k = (p.mean() / r.mean() - 1.0) if (len(p) and len(r) and r.mean() > 0) else None
        ci = boot_gap(p, r) if (len(p) >= 8 and len(r) >= 8) else None
        out[c] = dict(n_pub=len(p), n_reg=len(r), m_pub=float(p.mean()) if len(p) else None,
                      m_reg=float(r.mean()) if len(r) else None, kappa=k, lam=lam, ci=list(ci) if ci else None)

        def f(x, w=9, d=3):
            return (f"{x:>{w}.{d}f}" if x is not None else " " * (w - 1) + "-")
        cistr = f"[{ci[0]:+.2f},{ci[1]:+.2f}]{'*' if ci and ci[0] > 0 else ''}" if ci else ""
        print(f"  {c:16}{f((1 - lam) if lam else None, 7)}{len(p):>7}{len(r):>7}{f(p.mean() if len(p) else None)}"
              f"{f(r.mean() if len(r) else None)}{f(k)}{cistr:>22}")
        if k is not None and lam is not None and min(len(p), len(r)) >= 8:
            xs.append(1 - lam); ys.append(k); ws.append(min(len(p), len(r)))
    if len(xs) >= 3:
        xs, ys, ws = map(np.array, (xs, ys, ws))
        corr = float(np.corrcoef(xs, ys)[0, 1]); slope = float(np.sum(ws * xs * ys) / np.sum(ws * xs ** 2))
        # bootstrap CI on the correlation (class-level, weighted resample)
        rng = np.random.default_rng(11); cs_b = []
        for _ in range(5000):
            idx = rng.integers(0, len(xs), len(xs))
            if len(set(idx.tolist())) < 2:
                continue
            cc = np.corrcoef(xs[idx], ys[idx])[0, 1]
            if np.isfinite(cc):
                cs_b.append(cc)
        clo, chi = (float(np.quantile(cs_b, 0.025)), float(np.quantile(cs_b, 0.975))) if cs_b else (None, None)
        # honest gate: a 3-point corr with CI spanning 0 is uninformative, not a reproduction
        n_pos = int(np.sum(ys > 0))
        if clo is not None and clo > 0 and corr > 0.3:
            v = "REPRODUCES (corr CI excludes 0)"
        elif n_pos <= len(ys) // 2:
            v = "does NOT reproduce (per-class gaps mostly <=0)"
        else:
            v = "UNINFORMATIVE (corr CI spans 0; too few classes)"
        print(f"  => classes used={len(xs)}  corr(kappa,1-lam)={corr:+.3f} [{clo:+.2f},{chi:+.2f}] "
              f"(diabetes +0.50)  slope={slope:+.3f}  [{v}]")
        out['_summary'] = dict(measure=key, corr=corr, corr_ci=[clo, chi], slope=slope,
                               n_classes=int(len(xs)), verdict=v)
    else:
        print(f"  => only {len(xs)} adequately-powered classes -- insufficient")
        out['_summary'] = dict(measure=key, corr=None, n_classes=int(len(xs)), verdict="insufficient")
    return out


print("=" * 92)
print("FOURTH-DOMAIN external validation (antihypertensives / systolic BP): registered-vs-published gap")
print("=" * 92)
print(f"  mmHg |MD| analyses kept: {nm_}   z-analyses kept: {nz}")
resM = gap_table(perM, "(MD) |MD| in mmHg  (single-unit primary, as in diabetes HbA1c)", "md_mmhg")
resZ = gap_table(perZ, "(Z) significance gap  z=|MD|/SE  (scale-invariant robustness)", "z")
json.dump({"md_mmhg": resM, "z": resZ}, open(HERE / "aact_kappa_bp.json", "w"), indent=1)
print("\nwrote aact_kappa_bp.json")
