"""STANDARDISED 2nd-domain replication (antidepressants), scale-invariant measures.

Raw HAM-D mean differences failed (aact_kappa_depression.py: heterogeneous scale versions).
Here we use two SCALE-INVARIANT effect measures for the published-vs-registered gap, so that
17/21/24-item HAM-D and MADRS become comparable:
  (Z)  z = |MD| / SE  (SE from the reported 95% CI): the standardised signal-to-noise on which
       publication selection acts directly. kappa_z(c) = mean|z|_pub / mean|z|_reg - 1.
  (OR) response/remission log-odds-ratio: kappa_lnOR(c) = mean|lnOR|_pub / mean|lnOR|_reg - 1,
       a treatment-effect magnitude comparable across trials.
Split published (PubMed-linked) vs registered-only exactly as the diabetes analysis. Question:
does corr(gap, 1-lambda) reproduce the diabetes/HbA1c +0.50? Honest verdict, no manufactured win.
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
    'SSRI': ['fluoxetine', 'sertraline', 'paroxetine', 'citalopram', 'escitalopram', 'fluvoxamine'],
    'SNRI': ['venlafaxine', 'desvenlafaxine', 'duloxetine', 'milnacipran', 'levomilnacipran'],
    'TCA': ['amitriptyline', 'nortriptyline', 'imipramine', 'clomipramine', 'desipramine', 'doxepin'],
    'atypical': ['bupropion', 'mirtazapine', 'trazodone', 'vortioxetine', 'vilazodone', 'agomelatine', 'nefazodone'],
    'MAOI': ['phenelzine', 'tranylcypromine', 'moclobemide', 'isocarboxazid'],
}

con.execute(f"""CREATE TEMP TABLE dep AS SELECT DISTINCT nct_id FROM {t('conditions')}
 WHERE lower(name) LIKE '%major depress%' OR lower(name) LIKE '%depressive disorder%' OR lower(name)='depression';""")
con.execute(f"""CREATE TEMP TABLE pub AS SELECT DISTINCT nct_id FROM {t('study_references')}
 WHERE reference_type IN ('DERIVED','RESULT') AND pmid IS NOT NULL AND pmid<>'';""")
pubset = set(r[0] for r in con.execute("SELECT nct_id FROM pub").fetchall())
con.execute(f"""CREATE TEMP TABLE iv AS SELECT i.nct_id, lower(i.name) nm,
   (s.results_first_posted_date IS NOT NULL AND s.results_first_posted_date<>'') posted
 FROM {t('interventions')} i JOIN dep d ON i.nct_id=d.nct_id JOIN {t('studies')} s ON i.nct_id=s.nct_id;""")
LAM = {}
for c, kws in CLASSES.items():
    cond = " OR ".join(f"nm LIKE '%{k}%'" for k in kws)
    tot, pos = con.execute(f"SELECT count(DISTINCT nct_id), count(DISTINCT CASE WHEN posted THEN nct_id END) FROM iv WHERE {cond}").fetchone()
    LAM[c] = (pos / tot) if tot else None

zrows = con.execute(f"""SELECT o.nct_id, TRY_CAST(a.param_value AS DOUBLE) md,
   TRY_CAST(a.ci_lower_limit AS DOUBLE) lo, TRY_CAST(a.ci_upper_limit AS DOUBLE) hi
 FROM {t('outcomes')} o JOIN {t('outcome_analyses')} a ON a.outcome_id=o.id JOIN dep d ON o.nct_id=d.nct_id
 WHERE (lower(o.title) LIKE '%ham%d%' OR lower(o.title) LIKE '%hamilton depression%' OR lower(o.title) LIKE '%hdrs%'
        OR lower(o.title) LIKE '%madrs%' OR lower(o.title) LIKE '%montgomery%')
   AND lower(coalesce(a.param_type,'')) LIKE '%mean difference%'
   AND a.param_value IS NOT NULL AND a.ci_lower_limit IS NOT NULL AND a.ci_upper_limit IS NOT NULL""").fetchall()
orrows = con.execute(f"""SELECT o.nct_id, TRY_CAST(a.param_value AS DOUBLE) orr
 FROM {t('outcomes')} o JOIN {t('outcome_analyses')} a ON a.outcome_id=o.id JOIN dep d ON o.nct_id=d.nct_id
 WHERE (lower(o.title) LIKE '%response%' OR lower(o.title) LIKE '%remission%' OR lower(o.title) LIKE '%responder%')
   AND lower(coalesce(a.param_type,'')) LIKE '%odds ratio%' AND a.param_value IS NOT NULL""").fetchall()

con.execute(f"""CREATE TEMP TABLE ivn AS SELECT nct_id, lower(name) nm FROM {t('interventions')} WHERE nct_id IN (SELECT nct_id FROM dep);""")
names = {}
for nct, nm in con.execute("SELECT nct_id, nm FROM ivn").fetchall():
    names.setdefault(nct, []).append(nm or "")


def classes_of(nct):
    s = " ".join(names.get(nct, []))
    return [c for c, kws in CLASSES.items() if any(k in s for k in kws)]


perZ = {c: {'pub': [], 'reg': []} for c in CLASSES}
perO = {c: {'pub': [], 'reg': []} for c in CLASSES}
nz = no = 0
for nct, md, lo, hi in zrows:
    if None in (md, lo, hi) or not (hi > lo):
        continue
    se = (hi - lo) / (2 * Z975)
    if se <= 0:
        continue
    z = abs(md) / se
    if not np.isfinite(z) or z > 50:
        continue
    cs = classes_of(nct)
    if not cs:
        continue
    nz += 1
    b = 'pub' if nct in pubset else 'reg'
    for c in cs:
        perZ[c][b].append(z)
for nct, orr in orrows:
    if orr is None or orr <= 0:
        continue
    l = abs(np.log(orr))
    if not np.isfinite(l) or l > 5:
        continue
    cs = classes_of(nct)
    if not cs:
        continue
    no += 1
    b = 'pub' if nct in pubset else 'reg'
    for c in cs:
        perO[c][b].append(l)


def boot_gap(p, r, B=4000, seed=3):
    """Trial-level paired bootstrap CI on kappa = mean(p)/mean(r) - 1 (grounds the per-class
    gap in inference rather than the fragile few-class correlation)."""
    rng = np.random.default_rng(seed)
    ks = []
    for _ in range(B):
        pb = p[rng.integers(0, len(p), len(p))]
        rb = r[rng.integers(0, len(r), len(r))]
        if rb.mean() > 0:
            ks.append(pb.mean() / rb.mean() - 1.0)
    lo, hi = np.quantile(ks, [0.025, 0.975])
    return float(lo), float(hi)


def gap_table(per, label, key):
    print(f"\n--- {label} ---")
    print(f"  {'class':10}{'1-lam':>7}{'n_pub':>7}{'n_reg':>7}{'m_pub':>9}{'m_reg':>9}{'kappa':>9}{'  95% CI (trial boot)':>22}")
    xs, ys, ws = [], [], []
    out = {}
    for c in CLASSES:
        p = np.array(per[c]['pub'])
        r = np.array(per[c]['reg'])
        lam = LAM[c]
        k = (p.mean() / r.mean() - 1.0) if (len(p) and len(r) and r.mean() > 0) else None
        ci = boot_gap(p, r) if (len(p) >= 8 and len(r) >= 8) else None
        out[c] = dict(n_pub=len(p), n_reg=len(r), m_pub=float(p.mean()) if len(p) else None,
                      m_reg=float(r.mean()) if len(r) else None, kappa=k, lam=lam,
                      ci=list(ci) if ci else None)

        def f(x, w=9, d=3):
            return (f"{x:>{w}.{d}f}" if x is not None else " " * (w - 1) + "-")
        cistr = f"[{ci[0]:+.2f},{ci[1]:+.2f}]{'*' if ci and ci[0] > 0 else ''}" if ci else ""
        print(f"  {c:10}{f((1 - lam) if lam else None, 7)}{len(p):>7}{len(r):>7}{f(p.mean() if len(p) else None)}"
              f"{f(r.mean() if len(r) else None)}{f(k)}{cistr:>22}")
        if k is not None and lam is not None and min(len(p), len(r)) >= 8:
            xs.append(1 - lam)
            ys.append(k)
            ws.append(min(len(p), len(r)))
    if len(xs) >= 3:
        xs, ys, ws = map(np.array, (xs, ys, ws))
        corr = float(np.corrcoef(xs, ys)[0, 1])
        slope = float(np.sum(ws * xs * ys) / np.sum(ws * xs ** 2))
        v = ("REPRODUCES" if corr > 0.3 else "does NOT reproduce" if corr < 0.15 else "PARTIAL")
        print(f"  => classes used={len(xs)}  corr(kappa,1-lam)={corr:+.3f} (diabetes ref +0.50)  slope={slope:+.3f}  [{v}]")
        out['_summary'] = dict(measure=key, corr=corr, slope=slope, n_classes=int(len(xs)), verdict=v)
    else:
        print(f"  => only {len(xs)} adequately-powered classes -- insufficient")
        out['_summary'] = dict(measure=key, corr=None, n_classes=int(len(xs)), verdict="insufficient")
    return out


print("=" * 84)
print("STANDARDISED 2nd-domain replication (antidepressants): scale-invariant gaps")
print("=" * 84)
print(f"  z-analyses kept: {nz}   logOR-analyses kept: {no}")
resZ = gap_table(perZ, "(Z) significance gap  z=|MD|/SE  (HAM-D + MADRS, scale-invariant)", "z")
resO = gap_table(perO, "(OR) response/remission |ln OR|  (treatment-effect magnitude)", "lnOR")
json.dump({"z": resZ, "lnOR": resO}, open(HERE / "aact_kappa_depression_std.json", "w"), indent=1)
print("\nwrote aact_kappa_depression_std.json")
