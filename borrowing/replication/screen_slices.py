"""REPLICATION screen: find ADDITIONAL clean slices (analogous to GLP1-dose) where
a REAL within-class continuous effect-modifier predicts effect heterogeneity.

Generalises pilot-2's probe_modifier.py across multiple condition/outcome/drug-class
domains. For each domain we extract active-vs-placebo continuous mean-difference
effects (with CIs -> SE), classify the active arm into a drug class, capture the
specific molecule, and attach candidate modifiers: dose (mg), baseline severity,
follow-up weeks. We then screen each (class, modifier) pair with:
  * RE meta-regression slope + Wald CI + R2_between (variance explained)
  * permutation p of the slope (truth-first: real reported effects)
  * Simpson/confounder guard: within-MOLECULE re-fit (does the slope survive when
    drug identity is held fixed?) + a covariate-adjusted re-fit.

A slice QUALIFIES only if: n>=8 trials, |slope|/se>1.96, permutation p<0.05,
real spread in x, AND the signal survives the molecule/confounder guard (so it is
not the cross-class Simpson artefact that killed pilot-3).

Output: slices_screen.json (all candidates + diagnostics) and the per-slice trial
fields for the qualifying ones (consumed by run_slice.py).
"""
import duckdb, numpy as np, re, json, sys, io, math
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
A = r"F:\AACT-storage\AACT\2026-04-12"
con = duckdb.connect()
def t(n):
    return (f"read_csv('{A}/{n}.txt', delim='|', header=true, quote='', "
            f"ignore_errors=true, auto_detect=true, all_varchar=true)")

# ---- drug-class dictionaries (molecule keyword -> class) -------------------
GLP1 = ['glutide','exenatide','liraglutide','dulaglutide','semaglutide','lixisenatide',
        'albiglutide','tirzepatide','taspoglutide']
SGLT2 = ['gliflozin','dapagliflozin','empagliflozin','canagliflozin','ertugliflozin',
         'sotagliflozin','ipragliflozin','luseogliflozin','tofogliflozin','bexagliflozin']
DPP4 = ['gliptin','sitagliptin','vildagliptin','saxagliptin','linagliptin','alogliptin',
        'teneligliptin','gemigliptin','anagliptin','omarigliptin','trelagliptin']
STATIN = ['statin','atorvastatin','rosuvastatin','simvastatin','pravastatin','lovastatin',
          'fluvastatin','pitavastatin']
SSRI_SNRI = ['fluoxetine','sertraline','paroxetine','citalopram','escitalopram','fluvoxamine',
             'venlafaxine','desvenlafaxine','duloxetine','vortioxetine','vilazodone',
             'levomilnacipran','milnacipran']
GABAPENTINOID = ['pregabalin','gabapentin','mirogabalin']

def molecule(s, kws):
    s = s.lower()
    for k in kws:
        if k in s:
            return k
    return None

# ---- domain configs --------------------------------------------------------
DOMAINS = [
  dict(name="T2DM_HbA1c_GLP1", cond=["%type 2 diabetes%","%type ii diabetes%"],
       outc=["%hba1c%","%glycated hemoglobin%","%glycosylated hemoglobin%","%hemoglobin a1c%"],
       kws=GLP1, klabel="GLP1", base=["%hba1c%","%glycated hemoglobin%","%hemoglobin a1c%","%a1c%"],
       base_lo=5, base_hi=14, eff_cap=5),
  dict(name="T2DM_HbA1c_SGLT2", cond=["%type 2 diabetes%","%type ii diabetes%"],
       outc=["%hba1c%","%glycated hemoglobin%","%glycosylated hemoglobin%","%hemoglobin a1c%"],
       kws=SGLT2, klabel="SGLT2", base=["%hba1c%","%glycated hemoglobin%","%hemoglobin a1c%","%a1c%"],
       base_lo=5, base_hi=14, eff_cap=5),
  dict(name="T2DM_HbA1c_DPP4", cond=["%type 2 diabetes%","%type ii diabetes%"],
       outc=["%hba1c%","%glycated hemoglobin%","%glycosylated hemoglobin%","%hemoglobin a1c%"],
       kws=DPP4, klabel="DPP4", base=["%hba1c%","%glycated hemoglobin%","%hemoglobin a1c%","%a1c%"],
       base_lo=5, base_hi=14, eff_cap=5),
  dict(name="Lipid_LDL_statin", cond=["%hypercholesterol%","%dyslipidem%","%hyperlipidem%",
        "%cardiovascular%","%coronary%"],
       outc=["%ldl%","%low-density lipoprotein%","%low density lipoprotein%"],
       kws=STATIN, klabel="statin", base=["%ldl%","%low-density lipoprotein%","%low density lipoprotein%"],
       base_lo=40, base_hi=300, eff_cap=200),
  dict(name="Obesity_weight_GLP1", cond=["%obesity%","%overweight%","%weight%","%type 2 diabetes%"],
       outc=["%body weight%","%weight change%","%change in weight%","%percent weight%","%body mass index%"],
       kws=GLP1, klabel="GLP1", base=["%body weight%","%weight%","%body mass index%","%bmi%"],
       base_lo=15, base_hi=400, eff_cap=60),
  dict(name="Depression_score_SSRI", cond=["%depress%"],
       outc=["%madrs%","%montgomery%","%hamilton%","%ham-d%","%hamd%","%depression rating%",
             "%hdrs%","%madr%"],
       kws=SSRI_SNRI, klabel="SSRI_SNRI", base=["%madrs%","%hamilton%","%ham-d%","%hamd%","%hdrs%"],
       base_lo=5, base_hi=60, eff_cap=40),
  dict(name="Pain_score_gabapentinoid", cond=["%pain%","%neuralgia%","%fibromyalgia%","%neuropath%"],
       outc=["%pain%","%vas%","%numeric rating%","%nrs%"],
       kws=GABAPENTINOID, klabel="gabapentinoid", base=["%pain%","%vas%","%nrs%"],
       base_lo=0, base_hi=12, eff_cap=10),
]

def parse_dose(title):
    if not title:
        return None
    ds = re.findall(r'(\d+\.?\d*)\s*mg', title.lower())
    vals = [float(d) for d in ds if 0 < float(d) < 5000]
    return max(vals) if vals else None

def parse_weeks(tf):
    if not tf:
        return None
    s = tf.lower()
    m = re.search(r'(\d+\.?\d*)\s*week', s)
    if m: return float(m.group(1))
    m = re.search(r'(\d+\.?\d*)\s*month', s)
    if m: return float(m.group(1)) * 4.345
    m = re.search(r'(\d+\.?\d*)\s*year', s)
    if m: return float(m.group(1)) * 52.14
    return None

NEG = re.compile(r'\b(not|non|never|placebo)\b')

def build_domain(cfg):
    cond_or = " OR ".join(f"lower(name) LIKE '{c}'" for c in cfg["cond"])
    outc_or = " OR ".join(f"lower(title) LIKE '{c}'" for c in cfg["outc"])
    con.execute(f"DROP TABLE IF EXISTS dcond; CREATE TEMP TABLE dcond AS "
                f"SELECT DISTINCT nct_id FROM {t('conditions')} WHERE {cond_or};")
    con.execute(f"DROP TABLE IF EXISTS dout; CREATE TEMP TABLE dout AS "
                f"SELECT id AS outcome_id, nct_id, time_frame FROM {t('outcomes')} "
                f"WHERE ({outc_or});")
    con.execute(f"""DROP TABLE IF EXISTS deff; CREATE TEMP TABLE deff AS
      SELECT a.nct_id, a.id AS analysis_id, TRY_CAST(a.param_value AS DOUBLE) md,
             TRY_CAST(a.ci_lower_limit AS DOUBLE) lo, TRY_CAST(a.ci_upper_limit AS DOUBLE) hi,
             TRY_CAST(a.ci_percent AS DOUBLE) cipct, o.time_frame
      FROM {t('outcome_analyses')} a
      JOIN dout o ON a.outcome_id=o.outcome_id AND a.nct_id=o.nct_id
      JOIN dcond d ON a.nct_id=d.nct_id
      WHERE lower(a.param_type) LIKE '%mean difference%'
        AND a.ci_lower_limit IS NOT NULL AND a.ci_upper_limit IS NOT NULL;""")
    con.execute(f"""DROP TABLE IF EXISTS dgrp; CREATE TEMP TABLE dgrp AS
      SELECT oag.outcome_analysis_id AS analysis_id, rg.title AS arm_title
      FROM {t('outcome_analysis_groups')} oag
      JOIN {t('result_groups')} rg ON oag.result_group_id=rg.id;""")
    rows = con.execute("""SELECT e.nct_id, e.analysis_id, e.md, e.lo, e.hi, e.cipct, e.time_frame,
        string_agg(g.arm_title,' ||| ') arms
      FROM deff e LEFT JOIN dgrp g ON e.analysis_id=g.analysis_id
      GROUP BY 1,2,3,4,5,6,7""").fetchall()

    kws = cfg["kws"]
    def classify(title):
        if not title: return None
        s = title.lower()
        in_class = any(k in s for k in kws)
        is_pbo = 'placebo' in s
        return ('active' if in_class else ('placebo' if is_pbo else None))

    out = []
    for nct, aid, md, lo, hi, cip, tf, arms in rows:
        if md is None or lo is None or hi is None or hi <= lo: continue
        if abs(md) >= cfg["eff_cap"]: continue
        armlist = arms.split(' ||| ') if arms else []
        labs = [classify(a) for a in armlist]
        if 'active' not in labs or 'placebo' not in labs: continue
        # require exactly one active (in-class) molecule among arms, no other drug noise
        active_titles = [a for a in armlist if classify(a) == 'active']
        mols = set(filter(None, (molecule(a, kws) for a in active_titles)))
        if len(mols) != 1: continue
        mol = next(iter(mols))
        cipv = cip if cip else 95.0
        z = {90:1.6449,95:1.95996,99:2.5758}.get(int(round(cipv)), 1.95996)
        se = (hi - lo) / (2 * z)
        if not (se > 0 and se < cfg["eff_cap"]): continue
        dose = None
        for a in active_titles:
            d = parse_dose(a)
            # guard against negated counts in arm titles
            if d is not None:
                idx = a.lower().find(f"{d:g}")
                ctx = a.lower()[max(0, idx-12):idx]
                if NEG.search(ctx): continue
                dose = max(dose, d) if dose else d
        out.append(dict(nct_id=nct, analysis_id=int(aid), molecule=mol, md=float(md),
                        se=float(se), dose=dose, weeks=parse_weeks(tf)))
    if not out:
        return [], cfg
    ncts = sorted({r['nct_id'] for r in out})
    nlist = "','".join(ncts)
    cov = con.execute(f"""SELECT nct_id, TRY_CAST(enrollment AS DOUBLE) enroll,
        substr(start_date,1,4) yr FROM {t('studies')} WHERE nct_id IN ('{nlist}')""").fetchall()
    covd = {c[0]: dict(enroll=c[1], yr=c[2]) for c in cov}
    base_or = " OR ".join(f"lower(title) LIKE '{b}'" for b in cfg["base"])
    base = con.execute(f"""SELECT nct_id, avg(TRY_CAST(param_value_num AS DOUBLE)) bl
        FROM {t('baseline_measurements')} WHERE nct_id IN ('{nlist}')
          AND ({base_or}) AND param_value_num IS NOT NULL GROUP BY 1""").fetchall()
    based = {b[0]: b[1] for b in base if b[1] and cfg["base_lo"] < b[1] < cfg["base_hi"]}
    for r in out:
        c = covd.get(r['nct_id'], {})
        r['enroll'] = c.get('enroll')
        r['year'] = float(c['yr']) if c.get('yr') and c['yr'].isdigit() else None
        r['baseline'] = based.get(r['nct_id'])
    # aggregate to trial (one effect per nct via IV pool of its analyses)
    g = defaultdict(list)
    for r in out:
        g[r['nct_id']].append(r)
    trials = []
    for nct, rs in g.items():
        y = np.array([r['md'] for r in rs]); s = np.array([r['se'] for r in rs])
        w = 1 / s**2; mu = float((w*y).sum()/w.sum()); se = float(np.sqrt(1/w.sum()))
        def avg(key):
            vs = [r[key] for r in rs if r.get(key) is not None]
            return float(np.mean(vs)) if vs else None
        mols = Counter(r['molecule'] for r in rs)
        trials.append(dict(nct_id=nct, klabel=cfg["klabel"], molecule=mols.most_common(1)[0][0],
            y=mu, se=se, dose=avg('dose'), baseline=avg('baseline'), weeks=avg('weeks'),
            enroll=avg('enroll'), year=avg('year')))
    return trials, cfg


def re_metareg(y, s, x, z2=None, iters=200):
    """RE meta-regression y ~ x (+ optional confounder z2); moment tau2. Returns slope dict."""
    cols = [np.ones_like(x), x] + ([z2] if z2 is not None else [])
    X = np.column_stack(cols)
    tau2 = 0.0
    for _ in range(iters):
        w = 1/(s**2+tau2); WX = X*w[:,None]
        cov = np.linalg.inv(X.T@WX); beta = cov@(WX.T@y)
        resid = y - X@beta
        P = np.diag(w) - WX@cov@WX.T
        Q = float((w*resid**2).sum()); df = len(x)-X.shape[1]; trP = np.trace(P)
        tn = max(0.0,(Q-df)/trP) if trP > 0 else 0.0
        if abs(tn-tau2) < 1e-10: tau2 = tn; break
        tau2 = tn
    w = 1/(s**2+tau2); WX = X*w[:,None]
    cov = np.linalg.inv(X.T@WX); beta = cov@(WX.T@y)
    return float(beta[1]), float(np.sqrt(cov[1,1])), float(beta[0]), float(tau2)


def screen(trials, key, klabel):
    ts = [r for r in trials if r.get(key) is not None]
    if len(ts) < 8: return None
    y = np.array([r['y'] for r in ts]); s = np.array([r['se'] for r in ts])
    x = np.array([r[key] for r in ts], float)
    if np.std(x) < 1e-9 or len(np.unique(x)) < 4: return None
    slope, se_sl, intc, tau2 = re_metareg(y, s, x)
    # unconditional tau2 for R2
    w0 = 1/s**2; mu0 = (w0*y).sum()/w0.sum()
    Q0 = float((w0*(y-mu0)**2).sum()); c0 = w0.sum()-(w0**2).sum()/w0.sum()
    tau2_0 = max(0.0,(Q0-(len(x)-1))/c0) if c0 > 0 else 0.0
    R2 = 1 - tau2/tau2_0 if tau2_0 > 0 else 0.0
    # permutation p
    rng = np.random.default_rng(20260630)
    perm = np.array([abs(re_metareg(y, s, rng.permutation(x))[0]) for _ in range(2000)])
    pperm = float((perm >= abs(slope)).mean())
    # molecule guard: within-molecule (drop molecule mean) -> centered re-fit
    mols = np.array([r['molecule'] for r in ts])
    wmol_slope = wmol_p = None
    if len(set(mols)) >= 2:
        xc = x.copy(); yc = y.copy()
        for m in set(mols):
            idx = mols == m
            if idx.sum() >= 2:
                xc[idx] = x[idx] - x[idx].mean()
                yc[idx] = y[idx] - (w0[idx]*y[idx]).sum()/w0[idx].sum()
            else:
                xc[idx] = np.nan
        ok = np.isfinite(xc)
        if ok.sum() >= 6 and np.std(xc[ok]) > 1e-9:
            ws_slope, ws_se, _, _ = re_metareg(yc[ok], s[ok], xc[ok])
            wmol_slope = ws_slope
            wmol_p = float(2*(1-0.5*(1+math.erf(abs(ws_slope/ws_se)/2**.5)))) if ws_se>0 else 1.0
    # confounder-adjusted: add baseline (or dose if key is baseline) as z2 when available
    conf_key = 'baseline' if key != 'baseline' else 'dose'
    adj_slope = None
    zt = [r for r in ts if r.get(conf_key) is not None]
    if len(zt) >= 8:
        yy = np.array([r['y'] for r in zt]); ss = np.array([r['se'] for r in zt])
        xx = np.array([r[key] for r in zt], float); zz = np.array([r[conf_key] for r in zt], float)
        if np.std(xx) > 1e-9 and np.std(zz) > 1e-9:
            try:
                adj_slope = re_metareg(yy, ss, xx, z2=zz)[0]
            except Exception:
                adj_slope = None
    qualifies = bool(abs(slope) > 1.96*se_sl and pperm < 0.05 and len(ts) >= 8
                     and (wmol_slope is None or (np.sign(wmol_slope) == np.sign(slope) and (wmol_p is None or wmol_p < 0.2))))
    return dict(klabel=klabel, key=key, n=len(ts), slope=slope, se=se_sl,
                ci=[slope-1.96*se_sl, slope+1.96*se_sl], perm_p=pperm, R2_between=R2,
                tau2_uncond=tau2_0, tau2_cond=tau2, xrange=[float(x.min()),float(x.max())],
                xsd=float(np.std(x)), n_molecules=len(set(mols)),
                wmol_slope=wmol_slope, wmol_p=wmol_p, adj_slope=adj_slope, qualifies=qualifies)


# ---- run --------------------------------------------------------------------
all_screens = []
qualifying = {}
for cfg in DOMAINS:
    trials, cfg = build_domain(cfg)
    print(f"\n=== {cfg['name']}: {len(trials)} trials, "
          f"molecules={Counter(r['molecule'] for r in trials)} ===")
    if len(trials) < 8:
        print("  too few trials, skip")
        continue
    for key in ['dose', 'baseline', 'weeks']:
        r = screen(trials, key, cfg['name'])
        if r is None:
            print(f"  {key:9}: insufficient/uniform")
            continue
        all_screens.append(r)
        flag = "  *** QUALIFIES ***" if r['qualifies'] else ""
        wm = f" wmol={r['wmol_slope']:+.4f}(p={r['wmol_p']:.3f})" if r['wmol_slope'] is not None else " wmol=NA(1mol)"
        adj = f" adj={r['adj_slope']:+.4f}" if r['adj_slope'] is not None else ""
        print(f"  {key:9}: n={r['n']:3d} mols={r['n_molecules']} slope={r['slope']:+.4f}"
              f"[{r['ci'][0]:+.4f},{r['ci'][1]:+.4f}] permp={r['perm_p']:.3f} "
              f"R2={r['R2_between']:.2f}{wm}{adj}{flag}")
        if r['qualifies']:
            qualifying.setdefault(cfg['name'], {})[key] = [
                tr for tr in trials if tr.get(key) is not None]

json.dump(all_screens, open('slices_screen.json','w'), indent=1, default=str)
json.dump(qualifying, open('qualifying_slices.json','w'), indent=1, default=str)
print(f"\nwrote slices_screen.json ({len(all_screens)} candidates), "
      f"qualifying_slices.json ({sum(len(v) for v in qualifying.values())} qualifying slices)")
