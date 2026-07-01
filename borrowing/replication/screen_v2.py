"""REPLICATION screen v2 -- Simpson-PROOF within-single-molecule dose slices.

v1 (screen_slices.py) found that pooled cross-molecule dose slopes are mostly flat
or Simpson-confounded (depression SSRI: pooled +0.005 n.s. but within-molecule
-0.055 p<.001). The clean, defensible modifier is dose WITHIN A SINGLE MOLECULE
(atorvastatin 10/20/40/80, tirzepatide 5/10/15, pregabalin 150/300/600 ...): drug
identity is held fixed, so the slope cannot be a cross-drug potency artefact -- it
is the regime pilot-3 needed and lacked.

For each domain we extract active-vs-placebo continuous mean-difference effects,
resolve the SPECIFIC molecule, require exactly one molecule per trial, then:
  * per-molecule DOSE slices: molecules with >=8 trials, >=4 unique doses, spread
    -> RE meta-regression slope + permutation p + R2_between. Single-molecule =>
    Simpson-proof. Confounder guard: re-fit adding baseline + weeks.
  * class-level BASELINE-severity slices (across molecules within class), with a
    within-molecule guard.

Qualify (pre-registered): n>=8, |slope|/se>1.96, permutation p<0.05, >=4 unique x,
and (dose) confounder-adjusted slope keeps sign, or (baseline) within-molecule
guard keeps sign.
"""
import duckdb, numpy as np, re, json, sys, io, math
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
A = r"F:\AACT-storage\AACT\2026-04-12"
con = duckdb.connect()
def t(n):
    return (f"read_csv('{A}/{n}.txt', delim='|', header=true, quote='', "
            f"ignore_errors=true, auto_detect=true, all_varchar=true)")

# class membership keywords (broad) ; specific molecule names (fine resolution)
CLASSES = {
 'GLP1':   ['glutide','exenatide','tirzepatide','glp-1','glp1'],
 'SGLT2':  ['gliflozin'],
 'DPP4':   ['gliptin'],
 'statin': ['statin'],
 'CCB':    ['amlodipine','nifedipine','felodipine','lercanidipine','nitrendipine','cilnidipine','azelnidipine','benidipine'],
 'ARB':    ['sartan'],
 'SSRI_SNRI': ['fluoxetine','sertraline','paroxetine','citalopram','escitalopram','fluvoxamine',
               'venlafaxine','desvenlafaxine','duloxetine','vortioxetine','vilazodone',
               'levomilnacipran','milnacipran'],
 'gabapentinoid': ['pregabalin','gabapentin','mirogabalin'],
 'GLP1only': ['glutide','exenatide','tirzepatide','glp-1','glp1'],
 'antipsychotic': ['risperidone','paliperidone','olanzapine','quetiapine','aripiprazole',
        'lurasidone','cariprazine','brexpiprazole','ziprasidone','asenapine','iloperidone',
        'lumateperone'],
 'stimulant': ['methylphenidate','lisdexamfetamine','atomoxetine','guanfacine','dexmethylphenidate',
        'viloxazine','amphetamine'],
 'AChEI': ['donepezil','galantamine','rivastigmine','memantine'],
}
SPECIFIC = ['semaglutide','liraglutide','dulaglutide','albiglutide','taspoglutide','tirzepatide',
            'exenatide','lixisenatide',
            'dapagliflozin','empagliflozin','canagliflozin','ertugliflozin','sotagliflozin',
            'ipragliflozin','luseogliflozin','tofogliflozin','bexagliflozin',
            'sitagliptin','vildagliptin','saxagliptin','linagliptin','alogliptin','teneligliptin',
            'gemigliptin','anagliptin','omarigliptin','trelagliptin',
            'atorvastatin','rosuvastatin','simvastatin','pravastatin','lovastatin','fluvastatin','pitavastatin',
            'amlodipine','nifedipine','felodipine','lercanidipine','nitrendipine','cilnidipine','azelnidipine','benidipine',
            'losartan','valsartan','olmesartan','telmisartan','candesartan','irbesartan','azilsartan','eprosartan',
            'fluoxetine','sertraline','paroxetine','citalopram','escitalopram','fluvoxamine',
            'venlafaxine','desvenlafaxine','duloxetine','vortioxetine','vilazodone',
            'levomilnacipran','milnacipran',
            'pregabalin','gabapentin','mirogabalin',
            'risperidone','paliperidone','olanzapine','quetiapine','aripiprazole','lurasidone',
            'cariprazine','brexpiprazole','ziprasidone','asenapine','iloperidone','lumateperone',
            'methylphenidate','lisdexamfetamine','atomoxetine','guanfacine','dexmethylphenidate',
            'viloxazine','amphetamine',
            'donepezil','galantamine','rivastigmine','memantine']

def molecule(s):
    s = (s or "").lower()
    for m in SPECIFIC:
        if m in s:
            return m
    return None

DOMAINS = [
  dict(name="T2DM_HbA1c", cond=["%type 2 diabetes%","%type ii diabetes%"],
       outc=["%hba1c%","%glycated hemoglobin%","%glycosylated hemoglobin%","%hemoglobin a1c%"],
       cls=['GLP1','SGLT2','DPP4'], base=["%hba1c%","%glycated hemoglobin%","%hemoglobin a1c%","%a1c%"],
       base_lo=5, base_hi=14, eff_cap=5),
  dict(name="T2DM_HbA1c_GLP1only", cond=["%type 2 diabetes%","%type ii diabetes%"],
       outc=["%hba1c%","%glycated hemoglobin%","%glycosylated hemoglobin%","%hemoglobin a1c%"],
       cls=['GLP1only'], base=["%hba1c%","%glycated hemoglobin%","%hemoglobin a1c%","%a1c%"],
       base_lo=5, base_hi=14, eff_cap=5),
  dict(name="Obesity_weight", cond=["%obesity%","%overweight%","%weight%","%type 2 diabetes%"],
       outc=["%body weight%","%weight change%","%change in weight%","%percent weight%","%body mass index%"],
       cls=['GLP1'], base=["%body weight%","%weight%","%body mass index%","%bmi%"],
       base_lo=15, base_hi=400, eff_cap=60),
  dict(name="Lipid_LDL", cond=["%cholesterol%","%dyslipidem%","%hyperlipidem%","%cardiovascular%",
        "%coronary%","%lipid%"],
       outc=["%ldl%","%low-density lipoprotein%","%low density lipoprotein%"],
       cls=['statin'], base=["%ldl%","%low-density lipoprotein%","%low density lipoprotein%"],
       base_lo=40, base_hi=300, eff_cap=250),
  dict(name="HTN_SBP", cond=["%hypertension%","%blood pressure%"],
       outc=["%systolic%"],
       cls=['CCB','ARB'], base=["%systolic%"], base_lo=110, base_hi=220, eff_cap=60),
  dict(name="HTN_DBP", cond=["%hypertension%","%blood pressure%"],
       outc=["%diastolic%"],
       cls=['CCB','ARB'], base=["%diastolic%"], base_lo=60, base_hi=130, eff_cap=40),
  dict(name="Depression", cond=["%depress%"],
       outc=["%madrs%","%montgomery%","%hamilton%","%ham-d%","%hamd%","%hdrs%","%depression rating%"],
       cls=['SSRI_SNRI'], base=["%madrs%","%hamilton%","%ham-d%","%hamd%","%hdrs%"],
       base_lo=5, base_hi=60, eff_cap=40),
  dict(name="Pain", cond=["%pain%","%neuralgia%","%fibromyalgia%","%neuropath%"],
       outc=["%pain%","%vas%","%numeric rating%","%nrs%"],
       cls=['gabapentinoid'], base=["%pain%","%vas%","%nrs%"], base_lo=0, base_hi=12, eff_cap=10),
  dict(name="Schizophrenia_PANSS", cond=["%schizophren%"],
       outc=["%panss%","%positive and negative syndrome%","%bprs%","%brief psychiatric%"],
       cls=['antipsychotic'], base=["%panss%","%bprs%"], base_lo=40, base_hi=160, eff_cap=60),
  dict(name="ADHD", cond=["%adhd%","%attention deficit%"],
       outc=["%adhd%","%adhd-rs%","%conners%","%attention deficit%"],
       cls=['stimulant'], base=["%adhd%","%adhd-rs%"], base_lo=10, base_hi=70, eff_cap=80),
  dict(name="Alzheimer_cog", cond=["%alzheimer%","%dementia%","%cognitive impairment%"],
       outc=["%adas%","%adas-cog%","%mmse%","%mini-mental%","%cognition%"],
       cls=['AChEI'], base=["%adas%","%mmse%"], base_lo=0, base_hi=80, eff_cap=40),
]

NEG = re.compile(r'\b(not|non|never|placebo)\b')
def parse_dose(title):
    if not title: return None
    out = []
    for m in re.finditer(r'(\d+\.?\d*)\s*mg', title.lower()):
        v = float(m.group(1))
        if not (0 < v < 5000): continue
        ctx = title.lower()[max(0, m.start()-12):m.start()]
        if NEG.search(ctx): continue
        out.append(v)
    return max(out) if out else None

def parse_weeks(tf):
    if not tf: return None
    s = tf.lower()
    for pat, mul in [(r'(\d+\.?\d*)\s*week',1),(r'(\d+\.?\d*)\s*month',4.345),(r'(\d+\.?\d*)\s*year',52.14)]:
        m = re.search(pat, s)
        if m: return float(m.group(1))*mul
    return None

def build_domain(cfg):
    cond_or = " OR ".join(f"lower(name) LIKE '{c}'" for c in cfg["cond"])
    outc_or = " OR ".join(f"lower(title) LIKE '{c}'" for c in cfg["outc"])
    classkws = [kw for c in cfg["cls"] for kw in CLASSES[c]]
    con.execute(f"DROP TABLE IF EXISTS dcond; CREATE TEMP TABLE dcond AS "
                f"SELECT DISTINCT nct_id FROM {t('conditions')} WHERE {cond_or};")
    con.execute(f"DROP TABLE IF EXISTS dout; CREATE TEMP TABLE dout AS "
                f"SELECT id AS outcome_id, nct_id, time_frame FROM {t('outcomes')} WHERE ({outc_or});")
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
      FROM deff e LEFT JOIN dgrp g ON e.analysis_id=g.analysis_id GROUP BY 1,2,3,4,5,6,7""").fetchall()

    def in_class(s):
        s = (s or "").lower(); return any(k in s for k in classkws)
    out = []
    for nct, aid, md, lo, hi, cip, tf, arms in rows:
        if md is None or lo is None or hi is None or hi <= lo: continue
        if abs(md) >= cfg["eff_cap"]: continue
        armlist = arms.split(' ||| ') if arms else []
        has_pbo = any('placebo' in (a or '').lower() for a in armlist)
        active_titles = [a for a in armlist if in_class(a) and 'placebo' not in (a or '').lower()]
        if not has_pbo or not active_titles: continue
        mols = set(filter(None, (molecule(a) for a in active_titles)))
        if len(mols) != 1: continue
        mol = next(iter(mols))
        cipv = cip if cip else 95.0
        z = {90:1.6449,95:1.95996,99:2.5758}.get(int(round(cipv)), 1.95996)
        se = (hi - lo) / (2 * z)
        if not (se > 0 and se < cfg["eff_cap"]): continue
        dose = None
        for a in active_titles:
            if molecule(a) != mol: continue
            d = parse_dose(a)
            if d is not None: dose = max(dose, d) if dose else d
        out.append(dict(nct_id=nct, molecule=mol, md=float(md), se=float(se),
                        dose=dose, weeks=parse_weeks(tf)))
    if not out: return []
    ncts = sorted({r['nct_id'] for r in out}); nlist = "','".join(ncts)
    base_or = " OR ".join(f"lower(title) LIKE '{b}'" for b in cfg["base"])
    base = con.execute(f"""SELECT nct_id, avg(TRY_CAST(param_value_num AS DOUBLE)) bl
        FROM {t('baseline_measurements')} WHERE nct_id IN ('{nlist}')
          AND ({base_or}) AND param_value_num IS NOT NULL GROUP BY 1""").fetchall()
    based = {b[0]: b[1] for b in base if b[1] and cfg["base_lo"] < b[1] < cfg["base_hi"]}
    g = defaultdict(list)
    for r in out: g[r['nct_id']].append(r)
    trials = []
    for nct, rs in g.items():
        y = np.array([r['md'] for r in rs]); s = np.array([r['se'] for r in rs])
        w = 1/s**2; mu = float((w*y).sum()/w.sum()); se = float(np.sqrt(1/w.sum()))
        def avg(key):
            vs = [r[key] for r in rs if r.get(key) is not None]
            return float(np.mean(vs)) if vs else None
        mols = Counter(r['molecule'] for r in rs)
        trials.append(dict(nct_id=nct, domain=cfg['name'], molecule=mols.most_common(1)[0][0],
            y=mu, se=se, dose=avg('dose'), baseline=based.get(nct), weeks=avg('weeks')))
    return trials

def re_metareg(y, s, x, extra=None, iters=200):
    cols = [np.ones_like(x), x] + (list(extra) if extra is not None else [])
    X = np.column_stack(cols); tau2 = 0.0
    for _ in range(iters):
        w = 1/(s**2+tau2); WX = X*w[:,None]
        cov = np.linalg.inv(X.T@WX); beta = cov@(WX.T@y); resid = y-X@beta
        P = np.diag(w)-WX@cov@WX.T; Q = float((w*resid**2).sum()); df = len(x)-X.shape[1]; trP = np.trace(P)
        tn = max(0.0,(Q-df)/trP) if trP > 0 else 0.0
        if abs(tn-tau2) < 1e-10: tau2 = tn; break
        tau2 = tn
    w = 1/(s**2+tau2); WX = X*w[:,None]; cov = np.linalg.inv(X.T@WX); beta = cov@(WX.T@y)
    return float(beta[1]), float(np.sqrt(cov[1,1])), float(beta[0]), float(tau2)

def screen(ts, key, label, conf_keys=('baseline','weeks')):
    ts = [r for r in ts if r.get(key) is not None]
    if len(ts) < 8: return None
    y = np.array([r['y'] for r in ts]); s = np.array([r['se'] for r in ts]); x = np.array([r[key] for r in ts], float)
    if len(np.unique(x)) < 4 or np.std(x) < 1e-9: return None
    slope, se_sl, intc, tau2 = re_metareg(y, s, x)
    w0 = 1/s**2; mu0 = (w0*y).sum()/w0.sum(); Q0 = float((w0*(y-mu0)**2).sum())
    c0 = w0.sum()-(w0**2).sum()/w0.sum(); tau2_0 = max(0.0,(Q0-(len(x)-1))/c0) if c0>0 else 0.0
    R2 = 1-tau2/tau2_0 if tau2_0>0 else 0.0
    rng = np.random.default_rng(20260630)
    perm = np.array([abs(re_metareg(y, s, rng.permutation(x))[0]) for _ in range(2000)])
    pperm = float((perm >= abs(slope)).mean())
    # confounder-adjusted slope (add available confounders held fixed)
    adj_slope = None
    zt = [r for r in ts if all(r.get(c) is not None for c in conf_keys)]
    if len(zt) >= max(8, 3+len(conf_keys)):
        yy = np.array([r['y'] for r in zt]); ss = np.array([r['se'] for r in zt])
        xx = np.array([r[key] for r in zt], float)
        extra = [np.array([r[c] for r in zt], float) for c in conf_keys]
        extra = [e for e in extra if np.std(e) > 1e-9]
        if np.std(xx) > 1e-9:
            try: adj_slope = re_metareg(yy, ss, xx, extra=extra)[0]
            except Exception: adj_slope = None
    # within-molecule guard (only meaningful for multi-molecule, e.g. baseline slices)
    mols = np.array([r['molecule'] for r in ts]); wmol_slope = wmol_p = None
    if len(set(mols)) >= 2:
        xc = x.astype(float).copy(); yc = y.astype(float).copy()
        for m in set(mols):
            idx = mols == m
            if idx.sum() >= 2:
                xc[idx] = x[idx]-x[idx].mean()
                yc[idx] = y[idx]-(w0[idx]*y[idx]).sum()/w0[idx].sum()
            else: xc[idx] = np.nan
        ok = np.isfinite(xc)
        if ok.sum() >= 6 and np.std(xc[ok]) > 1e-9:
            ws, wse, _, _ = re_metareg(yc[ok], s[ok], xc[ok]); wmol_slope = ws
            wmol_p = float(2*(1-0.5*(1+math.erf(abs(ws/wse)/2**.5)))) if wse>0 else 1.0
    single_mol = len(set(mols)) == 1
    qual = bool(abs(slope) > 1.96*se_sl and pperm < 0.05 and len(np.unique(x)) >= 4)
    if qual and key == 'dose':
        # dose must survive confounder adjustment (sign kept) when adjustable
        if adj_slope is not None and np.sign(adj_slope) != np.sign(slope): qual = False
        # multi-molecule dose must also survive within-molecule guard
        if not single_mol and (wmol_slope is None or np.sign(wmol_slope) != np.sign(slope)
                               or (wmol_p is not None and wmol_p >= 0.2)): qual = False
    if qual and key == 'baseline' and not single_mol:
        if wmol_slope is None or np.sign(wmol_slope) != np.sign(slope) or (wmol_p is not None and wmol_p >= 0.2):
            qual = False
    return dict(label=label, key=key, n=len(ts), single_mol=single_mol, n_mol=len(set(mols)),
                slope=slope, se=se_sl, ci=[slope-1.96*se_sl, slope+1.96*se_sl], perm_p=pperm,
                R2_between=R2, xrange=[float(x.min()),float(x.max())], xsd=float(np.std(x)),
                n_unique=int(len(np.unique(x))), wmol_slope=wmol_slope, wmol_p=wmol_p,
                adj_slope=adj_slope, qualifies=qual, trials=ts)

def tier_of(r):
    if r['qualifies']:
        return 'clean'
    sig = abs(r['slope']) > 1.96*r['se']
    if sig and r['perm_p'] < 0.15 and r['R2_between'] >= 0.3:
        return 'nearmiss'
    return 'flat'

allscreen = []; qualifying = {}; all_slices = {}
for cfg in DOMAINS:
    trials = build_domain(cfg)
    bymol = Counter(r['molecule'] for r in trials)
    print(f"\n=== {cfg['name']}: {len(trials)} trials  molecules={dict(bymol)} ===")
    if len(trials) < 8: print("  too few trials"); continue
    # (a) per-single-molecule DOSE slices (Simpson-proof)
    for mol, cnt in bymol.items():
        if cnt < 8: continue
        ts = [r for r in trials if r['molecule'] == mol]
        r = screen(ts, 'dose', f"{cfg['name']}:{mol}:dose")
        if r is None: continue
        allscreen.append({k:v for k,v in r.items() if k!='trials'})
        all_slices[r['label']] = dict(tier=tier_of(r), key=r['key'], n=r['n'],
            slope=r['slope'], perm_p=r['perm_p'], R2=r['R2_between'], single_mol=r['single_mol'],
            trials=r['trials'])
        flag = "  *** QUALIFIES ***" if r['qualifies'] else ""
        print(f"  [dose 1mol] {mol:14} n={r['n']:3d} uniq={r['n_unique']} slope={r['slope']:+.4f}"
              f"[{r['ci'][0]:+.4f},{r['ci'][1]:+.4f}] permp={r['perm_p']:.3f} R2={r['R2_between']:.2f}"
              f" adj={r['adj_slope']}{flag}")
        if r['qualifies']: qualifying[r['label']] = r['trials']
    # (b) class-level DOSE (multi-molecule, needs within-mol guard)
    r = screen(trials, 'dose', f"{cfg['name']}:ALL:dose")
    if r is not None:
        allscreen.append({k:v for k,v in r.items() if k!='trials'})
        all_slices[r['label']] = dict(tier=tier_of(r), key=r['key'], n=r['n'],
            slope=r['slope'], perm_p=r['perm_p'], R2=r['R2_between'], single_mol=r['single_mol'],
            trials=r['trials'])
        flag = "  *** QUALIFIES ***" if r['qualifies'] else ""
        wm = f" wmol={r['wmol_slope']:+.4f}(p={r['wmol_p']:.3f})" if r['wmol_slope'] is not None else ""
        print(f"  [dose ALL ] nmol={r['n_mol']} n={r['n']:3d} uniq={r['n_unique']} slope={r['slope']:+.4f}"
              f"[{r['ci'][0]:+.4f},{r['ci'][1]:+.4f}] permp={r['perm_p']:.3f} R2={r['R2_between']:.2f}{wm}{flag}")
        if r['qualifies']: qualifying[r['label']] = r['trials']
    # (c) class-level BASELINE-severity
    r = screen(trials, 'baseline', f"{cfg['name']}:ALL:baseline")
    if r is not None:
        allscreen.append({k:v for k,v in r.items() if k!='trials'})
        all_slices[r['label']] = dict(tier=tier_of(r), key=r['key'], n=r['n'],
            slope=r['slope'], perm_p=r['perm_p'], R2=r['R2_between'], single_mol=r['single_mol'],
            trials=r['trials'])
        flag = "  *** QUALIFIES ***" if r['qualifies'] else ""
        wm = f" wmol={r['wmol_slope']:+.4f}(p={r['wmol_p']:.3f})" if r['wmol_slope'] is not None else ""
        print(f"  [baseline ] nmol={r['n_mol']} n={r['n']:3d} uniq={r['n_unique']} slope={r['slope']:+.4f}"
              f"[{r['ci'][0]:+.4f},{r['ci'][1]:+.4f}] permp={r['perm_p']:.3f} R2={r['R2_between']:.2f}{wm}{flag}")
        if r['qualifies']: qualifying[r['label']] = r['trials']

json.dump(allscreen, open('slices_screen_v2.json','w'), indent=1, default=str)
json.dump(qualifying, open('qualifying_slices_v2.json','w'), indent=1, default=str)
json.dump(all_slices, open('all_slices_trials.json','w'), indent=1, default=str)
from collections import Counter as _C
tiers = _C(v['tier'] for v in all_slices.values())
print(f"\n=== {len(allscreen)} candidates screened; tiers={dict(tiers)}; {len(qualifying)} QUALIFY (clean) ===")
for k in qualifying: print("  CLEAN:", k, f"(n={len(qualifying[k])})")
for k, v in all_slices.items():
    if v['tier'] == 'nearmiss': print("  NEARMISS:", k, f"(n={v['n']}, permp={v['perm_p']:.3f}, R2={v['R2']:.2f})")
