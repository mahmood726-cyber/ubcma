"""CLASS-COVARIATE PROTOTYPE test: does a leakage-free class-match covariate let the
committed field route a novel MA's effect LEVEL from a same-class donor WITHOUT the
ma-identity match -- the concrete fix target named by donor_ceiling (recovery 0.37)?

Design (pre-declared; builds on donor_ceiling.py's SAME deterministic donor/test split
and the SAME within-MA reference). For each cold AACT `ma` m we predict its TEST half
under four training regimes A/B/C/D (exactly as donor_ceiling) crossed with THREE kernels:

  KERNELS
    none : committed 4-group GP [yr, lp, spec, ma]           (reproduces donor_ceiling)
    cond : + condition-token class-match term (therapeutic-area grain)
    drug : + drug-class-token class-match term (the grain that isolates the sibling)

  REGIMES (donor half of each MA relabelled `m__sib`, a DISTINCT ma-code)
    A cold_nodonor : hold out donor+test of m; no sibling in train.  (== committed cold)
    B cold_sibling : sibling `m__sib` IN train; predict test (label m). ma-term does NOT
                     fire; under cond/drug the CLASS term CAN fire (sibling shares class).
    C warm_sibling : sibling keeps label m; ma-term fires. upper bound.
    D scrambled    : as B but donor outcomes globally permuted (sibling at WRONG level).

Pre-declared decision rule
  Primary: recovery fraction rec = (dA - dB)/(dA - dC) and the GLP1 test-half posterior
  mean (true +2.90) under each kernel.
  H1 (drug-class is the fix mechanism): rec_drug >> rec_none(=0.37) and GLP1 B-posterior
     moves from ~+1.1 toward the sibling level (~+2.9). This CONFIRMS the GP CAN route
     level via a leakage-free class term -- the original ceiling was the ABSENCE of the
     covariate, not a GP-structural inability.
  H2 (grain matters): rec_cond stays near baseline (condition averages insulin +0.19 ...
     glucagon +3.18, so a therapeutic-area match cannot recentre the extreme MA). If so,
     the actionable fix is a DRUG-CLASS/mechanism grain, not a therapeutic-area grain.
  Guard: negative-control D must NOT recover under any kernel (else the term is just
     adding neighbours, not matching level).
  Regression: corpus-wide honest 10-fold MAE with the added feature must not worsen the
     committed MAE by >2% (lessons.md rollback rule) -- checked in corpus_regression().

Truth-first caveat (reported): the injected sibling is the SAME MA split in half, so it
sits at the test half's EXACT level -> this is an UPPER BOUND on the class-covariate
benefit (a mechanism check: 'can the GP use the term at all?'). Real deployment payoff is
bounded by how close a genuine same-class donor's level is, and by corpus coverage.

Run:  python borrowing/field_scale/donor_ceiling_classcov.py
"""
from __future__ import annotations
import sys, json, functools
from pathlib import Path
import numpy as np
import pandas as pd

print = functools.partial(print, flush=True)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))

from corpus import load_corpus            # noqa: E402
from field import prep                    # noqa: E402
import field_learned as fl                # noqa: E402
import cold_transfer as ct                # noqa: E402  committed 4-group cross-predict + pboot
import field_classcov as fc               # noqa: E402  5-group class-augmented GP (prototype)
from donor_ceiling import build_block, split_halves, SCRAMBLE_SEED  # noqa: E402  reuse EXACT setup

GLP = "aact_diabetesme_glucagon-l"


def predict_arm(block, aact_mas, donor, test, mode, kernel, grain=None):
    """Predict every test-half row under one regime x one kernel. Returns mu aligned to block."""
    blk = block.copy()
    if mode in ("B_sibling", "D_scrambled"):
        for m in aact_mas:
            blk.loc[donor[m], "ma"] = m + "__sib"
    if mode == "D_scrambled":
        d_all = np.concatenate([donor[m] for m in aact_mas])
        rng = np.random.default_rng(SCRAMBLE_SEED)
        blk.loc[d_all, "yi"] = block["yi"].to_numpy()[d_all][rng.permutation(len(d_all))]

    if kernel == "none":
        X = fl.build_features(blk)
        cross = lambda tr, te: ct.gp_cross_predict(blk, X, tr, te)
    else:
        X = fc.build_features_cls(blk, grain)
        cross = lambda tr, te: fc.gp_cross_predict5(blk, X, tr, te)

    ma_now = blk["ma"].to_numpy()
    n = len(blk)
    mu = np.full(n, np.nan)
    for m in aact_mas:
        te = test[m]
        if mode == "A_nodonor":
            tr = np.where((ma_now != m) & (ma_now != m + "__sib"))[0]
        elif mode == "C_warm":
            tr = np.setdiff1d(np.arange(n), te)
        else:
            tr = np.where(ma_now != m)[0]
        mm, _ = cross(tr, te)
        mu[te] = mm
    return mu


def run_kernel(block, aact_mas, donor, test, within, y, test_mask, kernel, grain=None):
    arms = {}
    for mode in ("A_nodonor", "B_sibling", "C_warm", "D_scrambled"):
        mu = predict_arm(block, aact_mas, donor, test, mode, kernel, grain)
        el = np.abs(mu - y); ew = np.abs(within - y)
        m = test_mask & np.isfinite(el) & np.isfinite(ew)
        d, lo, hi, npair = ct.pboot(el[m], ew[m])
        arms[mode] = dict(delta=d, lo=lo, hi=hi, n=npair,
                          learned_mae=float(np.nanmean(el[m])),
                          within_mae=float(np.nanmean(ew[m])), mu=mu)
    dA, dB, dC = arms["A_nodonor"]["delta"], arms["B_sibling"]["delta"], arms["C_warm"]["delta"]
    rec = (dA - dB) / (dA - dC) if abs(dA - dC) > 1e-9 else float("nan")
    # GLP1 focus
    tglp = test[GLP]; yg = y[tglp]
    glp = {mode: dict(post_mean=float(arms[mode]["mu"][tglp].mean()),
                      mae=float(np.mean(np.abs(arms[mode]["mu"][tglp] - yg))))
           for mode in arms}
    glp["true_mean"] = float(yg.mean())
    glp["within_mae"] = float(np.mean(np.abs(within[tglp] - yg)))
    glp["within_post"] = float(within[tglp].mean())
    return dict(arms={k: {kk: vv for kk, vv in v.items() if kk != "mu"} for k, v in arms.items()},
                recovery_fraction=rec, glp1=glp,
                _mu={k: v["mu"] for k, v in arms.items()})


def corpus_regression(seeds=(0, 1, 2)):
    """Committed 4-group vs 5-group (cond/drug) honest k-fold MAE on the FULL corpus.
    Rollback rule: added feature must not worsen committed MAE by >2%."""
    df = prep(load_corpus())
    y = df["yi"].to_numpy(float)
    out = {}
    # committed
    mus = []
    for s in seeds:
        m = np.full(len(df), np.nan)
        for _, sub in df.groupby("family"):
            idx = sub.index.to_numpy()
            mm, _ = fl.predict_kfold(sub, seed=s)
            m[idx] = mm
        mus.append(m)
    base = np.nanmean([np.nanmean(np.abs(mm - y)) for mm in mus])
    out["committed_mae"] = float(base)
    for grain in ("cond", "drug"):
        mus = []
        for s in seeds:
            m = np.full(len(df), np.nan)
            for _, sub in df.groupby("family"):
                idx = sub.index.to_numpy()
                m[idx] = fc.predict_kfold5(sub, grain, seed=s)
            mus.append(m)
        mae = float(np.nanmean([np.nanmean(np.abs(mm - y)) for mm in mus]))
        out[f"classcov_{grain}_mae"] = mae
        out[f"classcov_{grain}_pct_change"] = float((mae - base) / base * 100.0)
    return out


def main():
    block, aact_mas = build_block()
    y = block["yi"].to_numpy(float)
    donor, test = split_halves(block, aact_mas)
    test_mask = np.zeros(len(block), bool)
    for m in aact_mas:
        test_mask[test[m]] = True
    within = ct.within_ma_pred(block)

    print(f"combined LOR block: {len(block)} nodes / {block.ma.nunique()} MAs; "
          f"{len(aact_mas)} AACT cold MAs; test-half n={int(test_mask.sum())}")
    # show the class groupings that will actually fire (transparency)
    for grain in ("cond", "drug"):
        groups = {}
        for m in aact_mas:
            groups.setdefault(fc.class_label(m, grain), []).append(m.split("_")[-1])
        multi = {k: v for k, v in groups.items() if len(v) > 1}
        print(f"  grain={grain:4} multi-MA classes: {multi if multi else '(all singletons)'}")

    results = {"kernels": {}}
    print("\n" + "=" * 92)
    print("recovery of the cold gap by kernel (Delta vs within-MA on test halves; rec=(dA-dB)/(dA-dC))")
    print("=" * 92)
    print(f"{'kernel':10} {'dA(cold)':>9} {'dB(sib)':>9} {'dC(warm)':>9} {'dD(scr)':>9} "
          f"{'rec':>6}  {'GLP1 B-post':>11} {'GLP1 C-post':>11}")
    for kernel, grain in [("none", None), ("cond", "cond"), ("drug", "drug")]:
        r = run_kernel(block, aact_mas, donor, test, within, y, test_mask, kernel, grain)
        results["kernels"][kernel] = {k: v for k, v in r.items() if k != "_mu"}
        a = r["arms"]; g = r["glp1"]
        print(f"{kernel:10} {a['A_nodonor']['delta']:+9.4f} {a['B_sibling']['delta']:+9.4f} "
              f"{a['C_warm']['delta']:+9.4f} {a['D_scrambled']['delta']:+9.4f} "
              f"{r['recovery_fraction']:6.2f}  {g['B_sibling']['post_mean']:+11.2f} "
              f"{g['C_warm']['post_mean']:+11.2f}")
    g0 = results["kernels"]["none"]["glp1"]
    print(f"\nGLP1 test-half: true level={g0['true_mean']:+.2f}, "
          f"within-MA posterior={g0['within_post']:+.2f} (MAE {g0['within_mae']:.3f}), "
          f"A_nodonor posterior={g0['A_nodonor']['post_mean']:+.2f}")

    print("\n" + "=" * 92)
    print("CORPUS REGRESSION CHECK (committed 4-group vs +class; honest 10-fold, 3-seed avg)")
    print("=" * 92)
    reg = corpus_regression()
    results["corpus_regression"] = reg
    print(f"  committed MAE = {reg['committed_mae']:.4f}")
    for grain in ("cond", "drug"):
        print(f"  +class[{grain}] MAE = {reg[f'classcov_{grain}_mae']:.4f}  "
              f"({reg[f'classcov_{grain}_pct_change']:+.2f}%  "
              f"{'OK' if reg[f'classcov_{grain}_pct_change'] <= 2.0 else 'REGRESSION>2%'})")

    # pre-declared verdict
    rn = results["kernels"]["none"]["recovery_fraction"]
    rd = results["kernels"]["drug"]["recovery_fraction"]
    rc = results["kernels"]["cond"]["recovery_fraction"]
    gb_none = results["kernels"]["none"]["glp1"]["B_sibling"]["post_mean"]
    gb_drug = results["kernels"]["drug"]["glp1"]["B_sibling"]["post_mean"]
    dD_drug = results["kernels"]["drug"]["arms"]["D_scrambled"]["delta"]
    dA_drug = results["kernels"]["drug"]["arms"]["A_nodonor"]["delta"]
    verdict = dict(
        H1_drug_recovers=bool(rd > rn + 0.15 and gb_drug > gb_none + 0.5),
        H2_grain_matters=bool(rd > rc + 0.15),
        guard_scrambled_no_recover=bool(dD_drug >= dA_drug - 0.05),
        rec_none=rn, rec_cond=rc, rec_drug=rd,
        glp1_B_none=gb_none, glp1_B_drug=gb_drug,
    )
    results["verdict"] = verdict
    print("\nPRE-DECLARED VERDICT:")
    print(f"  H1 drug-class covariate recovers cold level : {verdict['H1_drug_recovers']} "
          f"(rec {rn:.2f}->{rd:.2f}, GLP1 B-post {gb_none:+.2f}->{gb_drug:+.2f})")
    print(f"  H2 grain matters (drug >> cond)             : {verdict['H2_grain_matters']} "
          f"(rec_cond {rc:.2f} vs rec_drug {rd:.2f})")
    print(f"  guard: scrambled donor does NOT recover     : {verdict['guard_scrambled_no_recover']} "
          f"(dD {dD_drug:+.4f} vs dA {dA_drug:+.4f})")

    json.dump(results, open(HERE / "donor_ceiling_classcov_results.json", "w"), indent=2)
    print(f"\nwrote {HERE / 'donor_ceiling_classcov_results.json'}")


if __name__ == "__main__":
    main()
