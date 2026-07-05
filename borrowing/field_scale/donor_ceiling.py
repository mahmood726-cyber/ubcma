"""DONOR-CEILING decomposition: is the cold-transfer negative a METHOD ceiling
(the deployed specialty+precision+year kernel structurally cannot route effect
LEVEL to a held-out MA) or a CORPUS-COVERAGE ceiling (the negative exists only
because no level-matched same-class donor is present in the corpus)?

Background (this session builds forward from two committed results):
  - am (`9b52b86`, cold_transfer.py): on a genuinely fresh registry `ma` held out
    ENTIRELY (leave-one-MA-out), the RAW learned-kernel field loses to within-MA
    pooling (Delta=+0.15153 [+0.050,+0.263], n=144). The pooled loss is dominated
    by ONE extreme-level MA -- GLP1 `aact_diabetesme_glucagon-l`, mean logOR +3.18,
    cold MAE 2.477 vs within 0.859 (Delta +1.618). Even same-specialty, same-
    CONDITION diabetes donors (insulin +0.19, purines +1.14, thiophenes +1.61) are
    in training, but NONE is at GLP1's +3.18 level.
  - pm (`420fac3`, conflict_discount.py): the SHIPPED conflict-aware power-prior
    discount makes the cold field deployable-SAFE (tie, +0.0254 [-0.010,+0.063]) by
    deferring to within-MA under conflict -- but it does NOT beat within cold. The
    residual +0.025 is the GLP1 leak. The pm report's explicit flagged open item:
    "the field currently has no in-corpus GLP1-level donor to recentre toward; that
    is the real ceiling, not the fusion rule. Re-run once a genuine same-specialty
    donor exists."

This script runs THAT decisive test by controlled donor injection. For each cold
AACT `ma` m (k_m nodes) we deterministically split its nodes into two DISJOINT
halves: a DONOR half and a TEST half (fixed seed; no row is ever both train and
test). We then predict the SAME test-half rows under four training regimes and
compare each to the SAME within-MA reference (each test node from its own full-MA
siblings -- the deployable within-MA the analyst would actually use):

  A. cold_nodonor  : hold out ALL of m (donor+test), predict test. == committed cold
                     LOMO restricted to the test-halves. No sibling in the corpus.
  B. cold_sibling  : relabel the donor half as `m__sib` (a DISTINCT ma-code) and keep
                     it in training; hold out only the test half (label m). A genuine
                     level-matched same-specialty donor is now present, but its
                     ma-match kernel term does NOT fire against the test rows (distinct
                     code) -- the field must route to it via specialty+log-precision+
                     year ALONE. This is the realistic "a second MA of the same drug
                     class exists in my corpus" deployment scenario.
  C. warm_sibling  : the donor half KEEPS label m, so its ma-match term DOES fire.
                     Upper bound (exact same-class identity available).
  D. cold_sibling_scrambled (NEGATIVE CONTROL): as B, but the donor rows' outcomes yi
                     are globally permuted across ALL donor rows -> the sibling is
                     present at the WRONG level. If B helps but D does not, the active
                     ingredient is genuine LEVEL matching, not merely extra neighbours.

Decision rule (pre-declared):
  - If Delta_B << Delta_A (sibling recovers the loss) and Delta_D ~ Delta_A (scrambled
    donor does not), the cold negative is a CORPUS-COVERAGE ceiling: the deployed
    kernel CAN route level to a held-out MA once a level-matched donor exists. This
    STRENGTHENS the crown-jewel's honest characterisation (the cold boundary is a
    property of corpus coverage shared by ALL borrowing methods, not a kernel flaw).
  - If Delta_B ~ Delta_A (sibling does not help) the ceiling is the METHOD -- the
    specialty+precision+year kernel cannot route level even when a donor exists; that
    is a concrete fix target (add an effect-level-informative covariate).
  Either outcome is a real, informative result. Truth-first: report what the numbers say.

Run:  python borrowing/field_scale/donor_ceiling.py
"""
from __future__ import annotations
import sys, json, functools
from pathlib import Path
import numpy as np
import pandas as pd

print = functools.partial(print, flush=True)

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from corpus import load_corpus            # noqa: E402  committed, unchanged
from field import prep                    # noqa: E402  committed, unchanged
import field_learned as fl                # noqa: E402  committed, unchanged
import cold_transfer as ct                # noqa: E402  reuse committed helpers

SPLIT_SEED = 20260705      # donor/test half split
SCRAMBLE_SEED = 424242     # negative-control donor-outcome permutation
Z90 = 1.6448536269514722


def build_block():
    """Exact same combined LOR block as cold_transfer.main()."""
    corpus = load_corpus()
    corpus_lor = corpus[corpus.family == "LOR"][["ma", "family", "specialty", "yi", "se", "year"]]
    slice_df = pd.read_csv(HERE / "aact_coldslice_nodes.csv")
    aact = slice_df[slice_df.corpus_specialty == 1][["ma", "family", "specialty", "yi", "se", "year"]].copy()
    aact["year"] = pd.to_numeric(aact["year"], errors="coerce")
    block = prep(pd.concat([corpus_lor, aact], ignore_index=True))
    aact_mas = sorted(aact.ma.unique())
    return block, aact_mas


def split_halves(block, aact_mas):
    """Deterministic disjoint donor/test split of each AACT ma's rows.
    Returns dict ma -> (donor_idx array, test_idx array). Balanced sizes; fixed seed."""
    rng = np.random.default_rng(SPLIT_SEED)
    ma_arr = block["ma"].to_numpy()
    donor, test = {}, {}
    for m in aact_mas:
        idx = np.where(ma_arr == m)[0]
        perm = rng.permutation(idx)
        h = len(perm) // 2                     # test half = floor(k/2); donor gets the rest
        test[m] = np.sort(perm[:h])
        donor[m] = np.sort(perm[h:])
    return donor, test


def predict_testhalves(block, aact_mas, donor, test, mode):
    """Predict every test-half row under one training regime. Returns mu aligned to block.
    mode in {'A_nodonor','B_sibling','C_warm','D_scrambled'}."""
    blk = block.copy()
    if mode in ("B_sibling", "D_scrambled"):
        for m in aact_mas:
            blk.loc[donor[m], "ma"] = m + "__sib"
    if mode == "D_scrambled":
        # global permutation of ALL donor-row outcomes -> siblings present at wrong level
        d_all = np.concatenate([donor[m] for m in aact_mas])
        rng = np.random.default_rng(SCRAMBLE_SEED)
        blk.loc[d_all, "yi"] = block["yi"].to_numpy()[d_all][rng.permutation(len(d_all))]
    X = fl.build_features(blk)
    ma_now = blk["ma"].to_numpy()
    n = len(blk)
    mu = np.full(n, np.nan)
    for m in aact_mas:
        te = test[m]
        if mode == "A_nodonor":
            tr = np.where((ma_now != m) & (ma_now != m + "__sib"))[0]     # hold out donor+test
        elif mode == "C_warm":
            tr = np.setdiff1d(np.arange(n), te)                            # everything but test half
        else:  # B_sibling / D_scrambled: donor relabelled m__sib is IN training
            tr = np.where(ma_now != m)[0]                                  # hold out test-half label m only
        mm, _ = ct.gp_cross_predict(blk, X, tr, te)
        mu[te] = mm
    return mu


def main():
    results = {}
    block, aact_mas = build_block()
    y = block["yi"].to_numpy(float)
    donor, test = split_halves(block, aact_mas)
    test_mask = np.zeros(len(block), bool)
    for m in aact_mas:
        test_mask[test[m]] = True
    print(f"combined LOR block: {len(block)} nodes / {block.ma.nunique()} MAs; "
          f"{len(aact_mas)} AACT cold MAs; test-half rows n={int(test_mask.sum())} "
          f"(donor-half n={int(sum(len(donor[m]) for m in aact_mas))})")

    # donor vs test half level balance (transparency: halves must be comparable)
    print("\nper-MA donor/test half balance (mean yi):")
    for m in aact_mas:
        dm = block['yi'].to_numpy()[donor[m]].mean(); tm = block['yi'].to_numpy()[test[m]].mean()
        print(f"  {m:34} donor(n={len(donor[m]):2}) mean={dm:+.2f}   test(n={len(test[m]):2}) mean={tm:+.2f}")

    # FIXED within-MA reference (each test node from its own full-MA siblings, block0 labels)
    within = ct.within_ma_pred(block)

    print("\n" + "=" * 82)
    print("DONOR-CEILING decomposition on the SAME test-half rows (Delta vs within-MA; +=loss)")
    print("=" * 82)
    arms = {}
    for mode, label in [("A_nodonor", "A cold_nodonor (== committed cold)"),
                        ("B_sibling", "B cold_sibling (level donor, spec/prec/yr routing)"),
                        ("C_warm", "C warm_sibling (ma-term fires; upper bound)"),
                        ("D_scrambled", "D cold_sibling_SCRAMBLED (neg control)")]:
        mu = predict_testhalves(block, aact_mas, donor, test, mode)
        el = np.abs(mu - y); ew = np.abs(within - y)
        m = test_mask & np.isfinite(el) & np.isfinite(ew)
        d, lo, hi, npair = ct.pboot(el[m], ew[m])
        tag = "LEARNED WINS" if hi < 0 else ("within better" if lo > 0 else "n.s. (tie)")
        print(f"  [{label:52}] learnMAE={np.nanmean(el[m]):.3f} withinMAE={np.nanmean(ew[m]):.3f} "
              f"Delta={d:+.4f} [{lo:+.4f},{hi:+.4f}] -> {tag}")
        arms[mode] = dict(label=label, learned_mae=float(np.nanmean(el[m])),
                          within_mae=float(np.nanmean(ew[m])), delta=d, lo=lo, hi=hi,
                          n=npair, verdict=tag, mu=mu)
    results["arms"] = {k: {kk: vv for kk, vv in v.items() if kk != "mu"} for k, v in arms.items()}

    # recovery fraction A->B relative to the C upper bound
    dA, dB, dC = arms["A_nodonor"]["delta"], arms["B_sibling"]["delta"], arms["C_warm"]["delta"]
    if abs(dA - dC) > 1e-9:
        rec = (dA - dB) / (dA - dC)
        print(f"\n  recovery fraction (dA-dB)/(dA-dC) = ({dA:+.4f}-{dB:+.4f})/({dA:+.4f}-{dC:+.4f}) = {rec:.2f}")
        results["recovery_fraction"] = float(rec)

    # paired test: does the sibling significantly reduce error vs no-donor? (B better than A)
    for a, b, name in [("A_nodonor", "B_sibling", "sibling_vs_nodonor"),
                       ("D_scrambled", "B_sibling", "sibling_vs_scrambled")]:
        ea = np.abs(arms[a]["mu"] - y)[test_mask]; eb = np.abs(arms[b]["mu"] - y)[test_mask]
        d, lo, hi, npair = ct.pboot(eb, ea)   # eb-ea; negative => B lower error than A
        tag = "B beats " + a if hi < 0 else ("B worse" if lo > 0 else "n.s.")
        print(f"  [{name:24}] (B_err - {a}_err) mean={d:+.4f} [{lo:+.4f},{hi:+.4f}] -> {tag}")
        results[name] = dict(delta=d, lo=lo, hi=hi, n=npair, verdict=tag)

    # GLP1 focus: the extreme-level driver
    print("\n" + "=" * 82)
    print("GLP1 focus (aact_diabetesme_glucagon-l, mean logOR +3.18 -- the pooled-loss driver)")
    print("=" * 82)
    glp = "aact_diabetesme_glucagon-l"
    tglp = test[glp]
    yg = y[tglp]
    print(f"  test-half rows n={len(tglp)}, true mean level={yg.mean():+.2f}")
    glp_out = {}
    for mode in ("A_nodonor", "B_sibling", "C_warm", "D_scrambled"):
        mu = arms[mode]["mu"][tglp]
        mae = float(np.mean(np.abs(mu - yg)))
        print(f"  {mode:14} field posterior mean={mu.mean():+.2f}  MAE={mae:.3f}")
        glp_out[mode] = dict(post_mean=float(mu.mean()), mae=mae)
    wg = float(np.mean(np.abs(within[tglp] - yg)))
    print(f"  within-MA reference MAE={wg:.3f}  (within posterior mean={within[tglp].mean():+.2f})")
    glp_out["within_mae"] = wg
    results["glp1"] = glp_out

    # per-MA A vs B (does the sibling help broadly or only GLP1?)
    print("\nper-MA cold MAE  A_nodonor -> B_sibling (test-half rows):")
    permac = []
    for m in aact_mas:
        tm = test[m]; ym = y[tm]
        a_mae = float(np.mean(np.abs(arms["A_nodonor"]["mu"][tm] - ym)))
        b_mae = float(np.mean(np.abs(arms["B_sibling"]["mu"][tm] - ym)))
        w_mae = float(np.mean(np.abs(within[tm] - ym)))
        permac.append(dict(ma=m, n=len(tm), a=a_mae, b=b_mae, within=w_mae))
        print(f"  {m:34} n={len(tm):2} A={a_mae:.3f} B={b_mae:.3f} within={w_mae:.3f} "
              f"dAB={b_mae-a_mae:+.3f}")
    results["per_ma"] = permac

    json.dump(results, open(HERE / "donor_ceiling_results.json", "w"), indent=2)
    print(f"\nwrote {HERE / 'donor_ceiling_results.json'}")


if __name__ == "__main__":
    main()
