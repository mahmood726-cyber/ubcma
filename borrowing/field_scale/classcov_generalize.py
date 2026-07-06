"""HONEST cross-MA generalization test for the drug-class covariate (addresses the adversarial
review of donor_ceiling_classcov): the donor-injection recovery is near-TAUTOLOGICAL for a
SINGLETON class (e.g. 'glucagon-l' tags only GLP1, so the class term just re-creates the held-out
MA identity under an alias). A genuine cold-start test needs a NON-SINGLETON drug class held out
ENTIRELY (zero same-MA rows anywhere), predicted from CHEMICALLY-DISTINCT same-class donors.

The ONLY non-singleton drug class in this corpus is 'antibodies' (3 distinct condition-MAs:
carcinoma / intestinal / neoplasmsb). For each, we do TRUE leave-one-MA-out (no split, no alias):
train on everything except that MA's rows, predict its rows under the committed 'none' kernel and
the drug-class kernel, vs the within-MA reference.

IMPORTANT confound to report: all 3 antibodies MAs are specialty='oncology' with similar levels
(+0.24..+0.46), so the committed kernel's SPECIALTY-match term already groups them -> the drug-class
term is largely REDUNDANT with specialty here. This test therefore establishes whether the class
term adds anything BEYOND specialty when same-class MAs are genuinely distinct; if it does not (here),
the deployment-relevant claim is NOT_PROVEN on this corpus and needs a broader slice with same-drug-
class MAs spanning DIFFERENT specialties.

Run:  python borrowing/field_scale/classcov_generalize.py
"""
from __future__ import annotations
import sys, json, functools
from pathlib import Path
import numpy as np

print = functools.partial(print, flush=True)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))

import cold_transfer as ct
import field_classcov as fc
from donor_ceiling import build_block

ANTI = ["aact_carcinoma_antibodies", "aact_intestinal_antibodies", "aact_neoplasmsb_antibodies"]


def main():
    block, aact_mas = build_block()
    y = block["yi"].to_numpy(float)
    within = ct.within_ma_pred(block)
    ma = block["ma"].to_numpy()

    Xnone = None  # built inside gp_cross_predict via fl.build_features on the frozen block
    from field_learned import build_features as bf4
    X4 = bf4(block)
    Xdrug = fc.build_features_cls(block, "drug")

    print("TRUE leave-one-MA-out on the non-singleton 'antibodies' class (zero same-MA rows in train):")
    print(f"{'held-out MA':32} {'n':>3} {'true':>6} {'none-post':>9} {'drug-post':>9} "
          f"{'within':>7} {'noneMAE':>7} {'drugMAE':>7} {'withinMAE':>9}")
    rows = []
    for m in ANTI:
        te = np.where(ma == m)[0]
        tr = np.where(ma != m)[0]                    # TRUE LOMO: no same-MA rows, no alias
        mu_none, _ = ct.gp_cross_predict(block, X4, tr, te)
        mu_drug, _ = fc.gp_cross_predict5(block, Xdrug, tr, te)
        ym = y[te]
        r = dict(ma=m, n=int(len(te)), true=float(ym.mean()),
                 none_post=float(mu_none.mean()), drug_post=float(mu_drug.mean()),
                 within_post=float(within[te].mean()),
                 none_mae=float(np.mean(np.abs(mu_none - ym))),
                 drug_mae=float(np.mean(np.abs(mu_drug - ym))),
                 within_mae=float(np.mean(np.abs(within[te] - ym))))
        rows.append(r)
        print(f"{m:32} {r['n']:3} {r['true']:+6.2f} {r['none_post']:+9.2f} {r['drug_post']:+9.2f} "
              f"{r['within_post']:+7.2f} {r['none_mae']:7.3f} {r['drug_mae']:7.3f} {r['within_mae']:9.3f}")

    dn = np.mean([r["none_mae"] for r in rows]); dd = np.mean([r["drug_mae"] for r in rows])
    print(f"\n  mean cold MAE  none={dn:.3f}  drug-class={dd:.3f}  (delta drug-none = {dd-dn:+.3f})")
    print("  interpretation: all 3 antibodies MAs are specialty='oncology' -> specialty term already")
    print("  groups them; the drug-class term is redundant here. A |delta|~0 => class adds nothing")
    print("  BEYOND specialty on this (confounded) slice => cross-MA drug-class generalization is")
    print("  NOT_PROVEN on this corpus; needs same-class MAs spanning DIFFERENT specialties.")
    json.dump(dict(rows=rows, none_mae=dn, drug_mae=dd, delta=dd - dn),
              open(HERE / "classcov_generalize_results.json", "w"), indent=2)
    print(f"\n  wrote {HERE / 'classcov_generalize_results.json'}")


if __name__ == "__main__":
    main()
