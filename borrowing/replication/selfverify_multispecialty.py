"""FROM-SCRATCH re-derivation of the two NEW clean multi-specialty slices
(ursino dose-toxicity, raudenbush teacher-expectancy). NO imports of run_slice /
borrowing_field2 / ubcma -- effects recomputed from the raw metadat CSVs and the
relevance/uniform/scrambled LOO done with inline numpy only. Must reproduce
multispecialty.py central-bw rel-vs-null deltas to ~2dp. (Vendor cross-check
substitute; the GLP1 clean slices are covered by selfverify_replication.py.)
"""
import csv, io, sys, numpy as np
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
MET = Path(r"F:\public-data\metadat")


def ursino():
    x, y, s = [], [], []
    for r in csv.DictReader(open(MET / "dat.ursino2021.csv")):
        ev, tot = float(r["events"]), float(r["total"]); p = (ev+0.5)/(tot+1)
        y.append(np.log(p/(1-p))); s.append(np.sqrt(1/(ev+0.5)+1/(tot-ev+0.5)))
        x.append(float(r["dose"]))
    return np.array(x), np.array(y), np.array(s)


def raudenbush():
    x, y, s = [], [], []
    for r in csv.DictReader(open(MET / "dat.raudenbush1985.csv")):
        y.append(float(r["yi"])); s.append(np.sqrt(float(r["vi"]))); x.append(float(r["weeks"]))
    return np.array(x), np.array(y), np.array(s)


def prior(xt, xs, ys, ses, bw, mode, rng):
    prec = 1/np.maximum(ses**2, 1e-9)
    if mode == "uniform":
        w = prec
    else:
        xe = rng.permutation(xs) if mode == "scrambled" else xs.copy()
        w = np.exp(-0.5*((xe-xt)/bw)**2)*prec
    ws = w.sum()
    return (w*ys).sum()/ws if ws > 0 else np.nan


def loo(x, y, s, bw, mode, seed=1):
    rng = np.random.default_rng(seed); e = []
    for i in range(len(x)):
        m = np.ones(len(x), bool); m[i] = False
        mu = prior(x[i], x[m], y[m], s[m], bw, mode, rng)
        if np.isfinite(mu): e.append(abs(mu-y[i]))
    return np.array(e)


def boot(ea, eb, n=4000, seed=7):
    rng = np.random.default_rng(seed); d = ea-eb
    bi = rng.integers(0, len(d), size=(n, len(d))); md = d[bi].mean(axis=1)
    return d.mean(), np.quantile(md, .025), np.quantile(md, .975)


print("FROM-SCRATCH re-derivation of NEW clean slices (inline numpy, raw CSV):\n")
for name, loader in [("Onc_DoseToxicity:ursino:dose", ursino),
                     ("Edu_TeacherExpect:raudenbush:weeks", raudenbush)]:
    x, y, s = loader(); bw = float(x.std())
    er = loo(x, y, s, bw, "relevance"); eu = loo(x, y, s, bw, "uniform")
    es = loo(x, y, s, bw, "scrambled")
    du, lou, hiu = boot(er, eu); ds, los, his = boot(er, es)
    print(f"{name}  (n={len(x)}, bw=SD={bw:.3g})")
    print(f"  MAE relevance={er.mean():.3f} uniform={eu.mean():.3f} scrambled={es.mean():.3f}")
    print(f"  rel-uniform  {du:+.3f} [{lou:+.3f},{hiu:+.3f}]  {'WIN' if hiu<0 else 'n.s.'}")
    print(f"  rel-scramble {ds:+.3f} [{los:+.3f},{his:+.3f}]  {'WIN' if his<0 else 'n.s.'}\n")
