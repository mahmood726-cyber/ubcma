"""EXPERIMENT 2 -- multi-specialty relevance-borrowing replication.

Extends the GLP1-class replication (N=2 same-class slices) to FOUR new slices, each
a DIFFERENT specialty, each with a real within-set CONTINUOUS effect-modifier:

  * kalaian1996   (education / SAT coaching)  modifier = coaching HOURS   k=67
        Kalaian & Raudenbush (1996), Psychol Methods 1(3):227-235.
  * raudenbush1985(education / teacher expectancy) modifier = WEEKS of prior contact  k=19
        Raudenbush (1984), J Educ Psychol 76(1):85-97 (Pygmalion meta-analysis).
  * tannersmith2016(addiction / brief alcohol intervention) modifier = mean AGE  k=113
        Tanner-Smith & Lipsey (2015), J Subst Abuse Treat 51:1-18.
  * ursino2021    (oncology / phase-I dose-toxicity) modifier = DOSE   k=49
        Ursino et al. (2021), as compiled in metadat dat.ursino2021.

For each slice we (1) build per-effect (y, se, modifier), (2) verify the modifier is
real in-data (WLS slope + 10k permutation p + R2), tiering clean (perm p<0.05) vs
flat (n.s. -> in-data beta=0 honest control), then (3) run the SAME pre-registered
5-way real LOO as the GLP1 replication (relevance kernel vs uniform/scrambled nulls
and the REML-NMA baseline; truth = real held-out effect). Clean slices feed the
cross-specialty pooled estimate in aggregate_multispecialty.py.

NOTE on clustering: kalaian (verbal+math per study) and tannersmith (up to 12 effects
per study) are effect-level, not study-independent; the LOO is a prediction exercise so
this is admissible, but we flag it as a caveat (no independence claim).
"""
import csv, io, sys, json, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_slice import run_slice  # NOTE: run_slice reassigns sys.stdout at import (utf-8 wrapper)

MET = Path(r"F:\public-data\metadat")


def _ok(*vals):
    return all(v.strip() not in ("", "NA") for v in vals)


def build_kalaian():
    trials = []
    for r in csv.DictReader(open(MET / "dat.kalaian1996.csv")):
        if not _ok(r["yi"], r["vi"], r["hrs"]):
            continue
        trials.append(dict(study=r["study"], outcome=r["outcome"],
                           y=float(r["yi"]), se=float(np.sqrt(float(r["vi"]))),
                           hrs=float(r["hrs"])))
    return "Edu_SATcoaching:kalaian:hrs", trials, "hrs"


def build_raudenbush():
    trials = []
    for r in csv.DictReader(open(MET / "dat.raudenbush1985.csv")):
        trials.append(dict(author=r["author"], y=float(r["yi"]),
                           se=float(np.sqrt(float(r["vi"]))), weeks=float(r["weeks"])))
    return "Edu_TeacherExpect:raudenbush:weeks", trials, "weeks"


def build_tannersmith():
    trials = []
    for r in csv.DictReader(open(MET / "dat.tannersmith2016.csv")):
        trials.append(dict(studyid=r["studyid"], y=float(r["yi"]),
                           se=float(r["sei"]), age=float(r["aget1"])))
    return "Addiction_BriefAlcohol:tannersmith:age", trials, "age"


def build_ursino():
    # phase-I dose-toxicity: single-arm proportions -> logit toxicity with 0.5 continuity
    trials = []
    for r in csv.DictReader(open(MET / "dat.ursino2021.csv")):
        ev, tot = float(r["events"]), float(r["total"])
        p = (ev + 0.5) / (tot + 1.0)
        y = float(np.log(p / (1 - p)))
        se = float(np.sqrt(1/(ev + 0.5) + 1/(tot - ev + 0.5)))
        trials.append(dict(study=r["study"], y=y, se=se, dose=float(r["dose"])))
    return "Onc_DoseToxicity:ursino:dose", trials, "dose"


def verify_modifier(trials, key, seed=20260630):
    """WLS slope of y on modifier + 10k permutation p + weighted R2."""
    x = np.array([t[key] for t in trials], float)
    y = np.array([t["y"] for t in trials], float)
    s = np.array([t["se"] for t in trials], float)
    n = len(x); w = 1.0 / s**2
    X = np.column_stack([np.ones(n), x]); WX = X * w[:, None]
    beta = np.linalg.solve(X.T @ WX, WX.T @ y)
    yhat = X @ beta
    r2 = 1 - (w*(y-yhat)**2).sum() / (w*(y-y.mean())**2).sum()

    def slope(xp):
        Xp = np.column_stack([np.ones(n), xp]); WXp = Xp * w[:, None]
        return np.linalg.solve(Xp.T @ WXp, WXp.T @ y)[1]
    rng = np.random.default_rng(seed); obs = abs(beta[1])
    perm = np.array([abs(slope(rng.permutation(x))) for _ in range(10000)])
    perm_p = float((1 + (perm >= obs).sum()) / 10001)
    return dict(slope=float(beta[1]), R2=float(r2), perm_p=perm_p,
                n=n, x_uniq=int(len(set(x))), xrange=[float(x.min()), float(x.max())])


def main():
    builders = [build_kalaian, build_raudenbush, build_tannersmith, build_ursino]
    out = {}
    print("=" * 96)
    print("MODIFIER VERIFICATION (WLS slope of effect on modifier; 10k permutation)")
    print(f"{'slice':46}{'n':>4}{'uniq':>5}  {'slope':>10}{'R2':>8}{'perm_p':>9}  tier")
    slices = {}
    for b in builders:
        label, trials, key = b()
        v = verify_modifier(trials, key)
        tier = "clean" if v["perm_p"] < 0.05 else "flat"
        print(f"{label[:46]:46}{v['n']:>4}{v['x_uniq']:>5}  {v['slope']:>+10.4f}"
              f"{v['R2']:>8.3f}{v['perm_p']:>9.4f}  {tier}")
        slices[label] = dict(trials=trials, key=key, tier=tier, verify=v)

    print("\n" + "=" * 96)
    print("5-WAY REAL LOO PER SLICE (truth = real held-out effect)")
    for label, sl in slices.items():
        r = run_slice(label, sl["trials"], sl["key"])
        r["tier"] = sl["tier"]; r["verify"] = sl["verify"]
        out[label] = r
    json.dump(out, open(Path(__file__).parent / "multispecialty_loo.json", "w"),
              indent=1, default=str)
    print(f"\nwrote multispecialty_loo.json ({len(out)} slices)")


if __name__ == "__main__":
    main()
