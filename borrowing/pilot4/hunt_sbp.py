"""PILOT-4 HUNT step 2: SBP (systolic blood pressure) antihypertensive slice +
IMMEDIATE multi-covariate modifier screen. Front-loads the qualifying gate
(is a population covariate a STRONG within-class effect modifier, beta>=~0.02?)
BEFORE building any borrowing machinery -- if nothing qualifies we stop here.

Slice: active-vs-placebo SBP CHANGE mean differences (mmHg, common scale) from
AACT, antihypertensive monotherapy classes. One representative (most precise)
analysis per trial.

Covariates (real, external, per recruiting country, latest year):
  WB adult obesity (SH.STA.OB18, mean M+F), WB log GDP/capita (NY.GDP.PCAP.CD),
  WB under-5 mortality (SH.DYN.MORT), IHME SDI.
For each covariate, fit effect ~ cov: (1) marginal, (2) +drug-class FE (the
pilot-3 Simpson guard), (3) within each class, with a label permutation p and a
SCALE-FREE standardized slope + partial correlation.
"""
from __future__ import annotations
import duckdb, csv, json, os, re
import numpy as np
from collections import defaultdict
from pathlib import Path

A = r"F:\AACT-storage\AACT\2026-04-12"
WB = Path("F:/WorldBankData/api_data")
_SDI_REL = ("data/bronze/gbd_covariates/"
            "gbd-2023-socio-demographic-index-sdi_SDI_Values__1950-2023_[CSV].csv")
def _resolve_sdi():
    # ihme-data-lakehouse is a sibling repo; resolve via env var or common
    # project roots (candidate-root discovery, no machine-specific literal).
    env = os.environ.get("IHME_DATA_LAKEHOUSE")
    cands = ([Path(env) / _SDI_REL] if env else []) + [
        Path(drive) / "Projects" / "ihme-data-lakehouse" / _SDI_REL for drive in ("C:/", "F:/")
    ]
    for c in cands:
        if c.exists():
            return c
    return cands[-1]  # best-effort; read fails loudly if truly absent
SDI = _resolve_sdi()
con = duckdb.connect()
def t(n): return (f"read_csv('{A}/{n}.txt', delim='|', header=true, quote='', "
                  f"ignore_errors=true, auto_detect=true, all_varchar=true)")

# ---- antihypertensive classes (active arm keyword -> class) -------------------
CLASSES = {
 'ACE':   ['lisinopril','enalapril','ramipril','perindopril','captopril','benazepril',
           'quinapril','fosinopril','trandolapril','zofenopril','imidapril','cilazapril',
           'moexipril','ace inhibitor','angiotensin-converting'],
 'ARB':   ['losartan','valsartan','candesartan','telmisartan','olmesartan','irbesartan',
           'azilsartan','eprosartan','fimasartan','sartan','angiotensin receptor'],
 'CCB':   ['amlodipine','nifedipine','felodipine','lercanidipine','nicardipine','lacidipine',
           'manidipine','benidipine','cilnidipine','nitrendipine','isradipine','clevidipine',
           'verapamil','diltiazem','calcium channel'],
 'thiazide':['hydrochlorothiazide','chlorthalidone','chlortalidone','indapamide',
           'bendroflumethiazide','metolazone','hctz','thiazide'],
 'BB':    ['atenolol','metoprolol','bisoprolol','nebivolol','carvedilol','propranolol',
           'labetalol','celiprolol','betaxolol','beta-blocker','beta blocker'],
 'MRA':   ['spironolactone','eplerenone','finerenone'],
 'renin': ['aliskiren'],
}
def classify(title):
    if not title: return None
    s = title.lower()
    hits = [c for c,kws in CLASSES.items() if any(k in s for k in kws)]
    if 'placebo' in s and not hits: return 'placebo'
    if len(hits) == 1: return hits[0]
    return None

# ---- SBP-change active-vs-placebo mean differences ---------------------------
con.execute(f"""CREATE TEMP TABLE sbp_out AS
 SELECT id AS outcome_id, nct_id FROM {t('outcomes')}
 WHERE (lower(title) LIKE '%systolic blood pressure%' OR lower(title) LIKE '%systolic bp%')
   AND (lower(title) LIKE '%chang%' OR lower(title) LIKE '%reduction%'
        OR lower(title) LIKE '%decreas%' OR lower(title) LIKE '%difference%'
        OR lower(title) LIKE '%from baseline%');""")
con.execute(f"""CREATE TEMP TABLE eff AS
 SELECT a.nct_id, a.id AS analysis_id,
        TRY_CAST(a.param_value AS DOUBLE) md, TRY_CAST(a.ci_lower_limit AS DOUBLE) lo,
        TRY_CAST(a.ci_upper_limit AS DOUBLE) hi, TRY_CAST(a.ci_percent AS DOUBLE) cipct
 FROM {t('outcome_analyses')} a JOIN sbp_out o ON a.outcome_id=o.outcome_id AND a.nct_id=o.nct_id
 WHERE lower(a.param_type) LIKE '%mean difference%'
   AND a.ci_lower_limit IS NOT NULL AND a.ci_upper_limit IS NOT NULL
   AND TRY_CAST(a.param_value AS DOUBLE) IS NOT NULL;""")
con.execute(f"""CREATE TEMP TABLE grp AS
 SELECT oag.outcome_analysis_id AS analysis_id, rg.title AS arm_title
 FROM {t('outcome_analysis_groups')} oag
 JOIN {t('result_groups')} rg ON oag.result_group_id=rg.id;""")
rows = con.execute("""SELECT e.nct_id, e.analysis_id, e.md, e.lo, e.hi, e.cipct,
   string_agg(g.arm_title,' ||| ') arms
 FROM eff e LEFT JOIN grp g ON e.analysis_id=g.analysis_id GROUP BY 1,2,3,4,5,6""").fetchall()

bytrial = {}  # nct -> best (smallest se) active-vs-placebo SBP row
for nct, aid, md, lo, hi, cip, arms in rows:
    if None in (md, lo, hi) or hi <= lo: continue
    cls = [classify(a) for a in (arms.split(' ||| ') if arms else [])]
    cls = set(c for c in cls if c)
    actives = [c for c in cls if c != 'placebo']
    if 'placebo' not in cls or len(actives) != 1: continue
    z = {90:1.6449,95:1.95996,99:2.5758}.get(int(round(cip or 95.0)), 1.95996)
    se = (hi - lo) / (2*z)
    if not (0 < se < 20) or abs(md) > 40: continue
    if nct not in bytrial or se < bytrial[nct]['se']:
        bytrial[nct] = dict(nct_id=nct, active=actives[0], y=float(md), se=float(se))
trials = list(bytrial.values())
print(f"active-vs-placebo SBP trials: {len(trials)}")
from collections import Counter
print("by class:", dict(Counter(r['active'] for r in trials)))

# ---- recruiting countries ----------------------------------------------------
ncts = sorted(bytrial)
nlist = "','".join(ncts)
tc = defaultdict(list)
for nct, name in con.execute(f"""SELECT nct_id, name FROM {t('countries')}
   WHERE removed='f' AND nct_id IN ('{nlist}')""").fetchall():
    tc[nct].append(name)

# ---- covariate loaders -------------------------------------------------------
def load_wb(path):
    best = {}
    for r in csv.DictReader(open(path, encoding="utf-8-sig")):
        v = r["value"]
        if not v: continue
        try: yr = int(r["date"]); val = float(v)
        except ValueError: continue
        nm = r["country_name"]
        if nm not in best or yr > best[nm][0]: best[nm] = (yr, val)
    return {k: v[1] for k, v in best.items()}

fe = load_wb(WB/"source_14_Gender Statistics/SH_STA_OB18_FE_ZS.csv")
ma = load_wb(WB/"source_14_Gender Statistics/SH_STA_OB18_MA_ZS.csv")
OBES = {k:(fe[k]+ma[k])/2 for k in fe if k in ma}
GDP  = load_wb(WB/"source_2_World Development Indicators/NY_GDP_PCAP_CD.csv")
MORT = load_wb(WB/"source_2_World Development Indicators/SH_DYN_MORT.csv")

# SDI: representative recent year 2019, location_name -> mean_value
SDIm = {}
for r in csv.DictReader(open(SDI, encoding="utf-8-sig")):
    try: yr = int(r["year_id"])
    except (ValueError, KeyError): continue
    if yr != 2019: continue
    try: SDIm[r["location_name"]] = float(r["mean_value"])
    except ValueError: pass

ALIAS_WB = {"South Korea":"Korea, Rep.","Russia":"Russian Federation","Slovakia":"Slovak Republic",
   "Taiwan":None,"Hong Kong":"Hong Kong SAR, China","Puerto Rico":None,"Czech Republic":"Czechia",
   "Turkey":"Turkiye","Egypt":"Egypt, Arab Rep.","Iran":"Iran, Islamic Rep.","Venezuela":"Venezuela, RB",
   "South Korea ":"Korea, Rep.","Korea, Republic of":"Korea, Rep.","Vietnam":"Viet Nam",
   "Russian Federation":"Russian Federation"}
ALIAS_SDI = {"South Korea":"Republic of Korea","Korea, Republic of":"Republic of Korea",
   "Russia":"Russian Federation","Czech Republic":"Czechia","Slovakia":"Slovakia",
   "United States":"United States of America","UK":"United Kingdom","Vietnam":"Viet Nam",
   "Taiwan":"Taiwan (Province of China)","Iran":"Iran (Islamic Republic of)",
   "Hong Kong":"China","Venezuela":"Venezuela (Bolivarian Republic of)","Turkey":"Turkiye",
   "Bolivia":"Bolivia (Plurinational State of)","Tanzania":"United Republic of Tanzania",
   "Moldova":"Republic of Moldova"}
def lk(d, country, alias):
    if country in d: return d[country]
    a = alias.get(country, country)
    if a and a in d: return d[a]
    return None

def trial_cov(nct, d, alias):
    vals = [lk(d, c, alias) for c in tc.get(nct, [])]
    vals = [v for v in vals if v is not None]
    return (sum(vals)/len(vals)) if vals else None

for r in trials:
    r["countries"] = tc.get(r["nct_id"], [])
    r["n_countries"] = len(r["countries"])
    r["pop_ob"]   = trial_cov(r["nct_id"], OBES, ALIAS_WB)
    g = trial_cov(r["nct_id"], GDP, ALIAS_WB);  r["pop_loggdp"] = (np.log(g) if g else None)
    r["pop_mort"] = trial_cov(r["nct_id"], MORT, ALIAS_WB)
    r["pop_sdi"]  = trial_cov(r["nct_id"], SDIm, ALIAS_SDI)
    r["single_country"] = (r["n_countries"] == 1)

json.dump(trials, open("sbp_trials.json","w"), indent=1)

# ---- modifier screen ---------------------------------------------------------
def wls_slope(y, x, w, cls=None):
    """WLS slope of y on x (optionally with class fixed effects). Returns (slope, se_slope)."""
    y, x, w = map(np.asarray, (y, x, w))
    cols = [np.ones_like(y), x]
    if cls is not None:
        uniq = sorted(set(cls))
        for c in uniq[1:]:
            cols.append(np.array([1.0 if k==c else 0.0 for k in cls]))
    X = np.column_stack(cols)
    W = np.diag(w)
    try:
        XtWX = X.T @ W @ X
        beta = np.linalg.solve(XtWX, X.T @ W @ y)
        cov = np.linalg.inv(XtWX)
    except np.linalg.LinAlgError:
        return float("nan"), float("nan")
    return float(beta[1]), float(np.sqrt(cov[1,1]))

def perm_p(y, x, w, cls, slope_obs, nperm=5000, seed=0):
    rng = np.random.default_rng(seed)
    cnt = 0
    for _ in range(nperm):
        xp = rng.permutation(x)
        s, _ = wls_slope(y, xp, w, cls)
        if abs(s) >= abs(slope_obs) - 1e-12: cnt += 1
    return (cnt + 1) / (nperm + 1)

print("\n=== MODIFIER SCREEN (effect = SBP MD mmHg vs placebo; w=1/se^2) ===")
COVS = [("obesity %","pop_ob"),("log GDPpc","pop_loggdp"),
        ("under-5 mort","pop_mort"),("SDI","pop_sdi")]
results = {}
for label, key in COVS:
    sub = [r for r in trials if r.get(key) is not None]
    if len(sub) < 12:
        print(f"\n{label:14}: only {len(sub)} trials with covariate -- skip"); continue
    y = np.array([r["y"] for r in sub]); se = np.array([r["se"] for r in sub])
    x = np.array([r[key] for r in sub]); w = 1.0/se**2; cls = [r["active"] for r in sub]
    xz = (x - x.mean())/x.std()  # standardized covariate -> slope is per-SD (scale-free in x)
    m_s, m_se = wls_slope(y, xz, w)
    c_s, c_se = wls_slope(y, xz, w, cls)
    pm = perm_p(y, xz, w, None, m_s)
    pc = perm_p(y, xz, w, cls, c_s)
    # within-class
    wc = {}
    for c in sorted(set(cls)):
        idx = [i for i,k in enumerate(cls) if k==c]
        if len(idx) >= 5 and x[idx].std() > 1e-6:
            s, sse = wls_slope(y[idx], (x[idx]-x[idx].mean())/x[idx].std(), w[idx])
            wc[c] = (round(s,3), round(sse,3), len(idx))
    ystd = y.std()
    results[key] = dict(label=label, n=len(sub), marg_perSD=round(m_s,3), marg_p=round(pm,4),
                        classadj_perSD=round(c_s,3), classadj_p=round(pc,4),
                        y_sd=round(ystd,2), within=wc)
    print(f"\n{label:14} (n={len(sub)}, y_sd={ystd:.1f} mmHg)")
    print(f"  marginal slope   : {m_s:+.2f} mmHg/SD  (perm p={pm:.3f})")
    print(f"  +class-FE slope  : {c_s:+.2f} mmHg/SD  (perm p={pc:.3f})  <- Simpson guard")
    print(f"  within-class     : " + "  ".join(f"{c}:{v[0]:+.2f}±{v[1]:.2f}(n{v[2]})" for c,v in wc.items()))

json.dump(results, open("sbp_modifier_screen.json","w"), indent=1)
print("\nwrote sbp_trials.json + sbp_modifier_screen.json")
