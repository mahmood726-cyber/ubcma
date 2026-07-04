"""THIRD-DOMAIN external validation of the transport-NMA registry-severity model: lipid-lowering
therapy / LDL-C reduction. Tests whether the AACT registered-vs-published effect gap ALSO grows with
registry selection severity (1-lambda) in a third, independent therapeutic domain — after diabetes
(HbA1c, corr +0.50, primary) and antidepressants (HAM-D z-gap, corr +0.64).

Same machinery as aact_kappa_depression_std.py. Endpoint = change in LDL cholesterol. LDL is reported
in mg/dL, mmol/L, and % change, so — as with the rating-scale antidepressant analysis — the primary
measure is the SCALE-INVARIANT significance gap z = |MD|/SE (SE from the 95% CI); a percent-change |MD|
subset is reported as a unit-clean secondary. kappa_z(c) = mean|z|_published / mean|z|_registered-only - 1.
Split published (PubMed-linked) vs registered-only exactly as in the diabetes/antidepressant analyses.
Truth-first: honest whether corr(kappa, 1-lambda) reproduces the positive sign or not.
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
    'statin': ['atorvastatin', 'rosuvastatin', 'simvastatin', 'pravastatin', 'lovastatin',
               'fluvastatin', 'pitavastatin', 'cerivastatin', 'statin'],
    'ezetimibe': ['ezetimibe'],
    'PCSK9': ['evolocumab', 'alirocumab', 'inclisiran', 'bococizumab'],
    'fibrate': ['fenofibrate', 'gemfibrozil', 'bezafibrate', 'ciprofibrate', 'fibrate'],
    'bile_acid': ['cholestyramine', 'colestipol', 'colesevelam'],
    'niacin': ['niacin', 'nicotinic acid'],
}

con.execute(f"""CREATE TEMP TABLE lip AS SELECT DISTINCT nct_id FROM {t('conditions')}
 WHERE lower(name) LIKE '%hypercholesterol%' OR lower(name) LIKE '%dyslipid%' OR lower(name) LIKE '%hyperlipid%'
   OR lower(name) LIKE '%lipoprotein%' OR lower(name) LIKE '%cholesterol%';""")
con.execute(f"""CREATE TEMP TABLE pub AS SELECT DISTINCT nct_id FROM {t('study_references')}
 WHERE reference_type IN ('DERIVED','RESULT') AND pmid IS NOT NULL AND pmid<>'';""")
pubset = set(r[0] for r in con.execute("SELECT nct_id FROM pub").fetchall())
con.execute(f"""CREATE TEMP TABLE iv AS SELECT i.nct_id, lower(i.name) nm,
   (s.results_first_posted_date IS NOT NULL AND s.results_first_posted_date<>'') posted
 FROM {t('interventions')} i JOIN lip d ON i.nct_id=d.nct_id JOIN {t('studies')} s ON i.nct_id=s.nct_id;""")
LAM = {}
for c, kws in CLASSES.items():
    cond = " OR ".join(f"nm LIKE '%{k}%'" for k in kws)
    tot, pos = con.execute(f"SELECT count(DISTINCT nct_id), count(DISTINCT CASE WHEN posted THEN nct_id END) FROM iv WHERE {cond}").fetchone()
    LAM[c] = (pos / tot) if tot else None

rows = con.execute(f"""SELECT o.nct_id, lower(coalesce(o.units,'')) units, TRY_CAST(a.param_value AS DOUBLE) md,
   TRY_CAST(a.ci_lower_limit AS DOUBLE) lo, TRY_CAST(a.ci_upper_limit AS DOUBLE) hi
 FROM {t('outcomes')} o JOIN {t('outcome_analyses')} a ON a.outcome_id=o.id JOIN lip d ON o.nct_id=d.nct_id
 WHERE (lower(o.title) LIKE '%ldl%' OR lower(o.title) LIKE '%low-density lipoprotein%' OR lower(o.title) LIKE '%low density lipoprotein%')
   AND lower(coalesce(a.param_type,'')) LIKE '%mean difference%' AND a.param_value IS NOT NULL""").fetchall()

con.execute(f"""CREATE TEMP TABLE ivn AS SELECT nct_id, lower(name) nm FROM {t('interventions')} WHERE nct_id IN (SELECT nct_id FROM lip);""")
names = {}
for nct, nm in con.execute("SELECT nct_id, nm FROM ivn").fetchall():
    names.setdefault(nct, []).append(nm or "")


def classes_of(nct):
    s = " ".join(names.get(nct, []))
    return [c for c, kws in CLASSES.items() if any(k in s for k in kws)]


perZ = {c: {'pub': [], 'reg': []} for c in CLASSES}
perP = {c: {'pub': [], 'reg': []} for c in CLASSES}   # percent-change |MD| (unit-clean secondary)
nz = npct = 0
for nct, units, md, lo, hi in rows:
    if md is None or not np.isfinite(md):
        continue
    cs = classes_of(nct)
    if not cs:
        continue
    b = 'pub' if nct in pubset else 'reg'
    # scale-invariant z
    if lo is not None and hi is not None and np.isfinite(lo) and np.isfinite(hi) and hi > lo:
        se = (hi - lo) / (2 * Z975)
        z = abs(md) / se if se > 0 else None
        if z is not None and np.isfinite(z) and z <= 50:
            nz += 1
            for c in cs:
                perZ[c][b].append(z)
    # percent-change |MD| subset (unit-clean)
    if ('percent' in units or '%' in units) and abs(md) <= 100:
        npct += 1
        for c in cs:
            perP[c][b].append(abs(md))


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
    print(f"  {'class':11}{'1-lam':>7}{'n_pub':>7}{'n_reg':>7}{'m_pub':>9}{'m_reg':>9}{'kappa':>9}{'  95% CI (trial boot)':>22}")
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
        print(f"  {c:11}{f((1 - lam) if lam else None, 7)}{len(p):>7}{len(r):>7}{f(p.mean() if len(p) else None)}"
              f"{f(r.mean() if len(r) else None)}{f(k)}{cistr:>22}")
        if k is not None and lam is not None and min(len(p), len(r)) >= 8:
            xs.append(1 - lam); ys.append(k); ws.append(min(len(p), len(r)))
    if len(xs) >= 3:
        xs, ys, ws = map(np.array, (xs, ys, ws))
        corr = float(np.corrcoef(xs, ys)[0, 1]); slope = float(np.sum(ws * xs * ys) / np.sum(ws * xs ** 2))
        v = ("REPRODUCES" if corr > 0.3 else "does NOT reproduce" if corr < 0.15 else "PARTIAL")
        print(f"  => classes used={len(xs)}  corr(kappa,1-lam)={corr:+.3f} (diabetes +0.50, antidep +0.64)  slope={slope:+.3f}  [{v}]")
        out['_summary'] = dict(measure=key, corr=corr, slope=slope, n_classes=int(len(xs)), verdict=v)
    else:
        print(f"  => only {len(xs)} adequately-powered classes -- insufficient")
        out['_summary'] = dict(measure=key, corr=None, n_classes=int(len(xs)), verdict="insufficient")
    return out


print("=" * 88)
print("THIRD-DOMAIN external validation (lipid-lowering / LDL-C): registered-vs-published gap")
print("=" * 88)
print(f"  z-analyses kept: {nz}   percent-change |MD| analyses: {npct}")
resZ = gap_table(perZ, "(Z) significance gap  z=|MD|/SE  (scale-invariant, primary)", "z")
resP = gap_table(perP, "(PCT) percent-change LDL |MD|  (unit-clean secondary)", "pct_md")
json.dump({"z": resZ, "pct_md": resP}, open(HERE / "aact_kappa_lipid.json", "w"), indent=1)
print("\nwrote aact_kappa_lipid.json")
