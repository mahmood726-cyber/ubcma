"""Regression guard for the moderate-selection boundary extension (field_bakeoff2_modsel).

Reads the COMMITTED cm/lm domination CSVs (no grid re-run) and asserts the boundary
claims documented in REPORT_FIELD2.md section (d):
  * adaptshrink_auto leads every AdaptShrink variant on both moderate grids;
  * auto never loses to an EXTERNAL (published) comparator under moderate selection
    -- the only permitted non-domination is to a sibling adaptshrink_* variant;
  * moderate-selection domination is >= the strong-grid step+copas baseline
    (the win survives weaker selection).

These lock the finding: the field-domination is not a strong-selection artifact.
"""
import os

import pandas as pd
import pytest

HERE = os.path.dirname(__file__)
SIBLINGS = {"adaptshrink_ens", "adaptshrink_ens_calib", "adaptshrink_fast",
            "adaptshrink_petgate", "adaptshrink_auto"}
VARIANTS = ["adaptshrink_ens", "adaptshrink_ens_calib", "adaptshrink_fast",
            "adaptshrink_petgate", "adaptshrink_auto"]


def _dom(tag, headline):
    p = os.path.join(HERE, f"field2_{tag}_domination_{headline}.csv")
    if not os.path.exists(p):
        pytest.skip(f"missing committed artifact {p}")
    return pd.read_csv(p)


def _external_loss_cells(tag):
    """Cells where auto's loses_to names a non-sibling (external) comparator."""
    d = _dom(tag, "adaptshrink_auto")
    bad = []
    for _, r in d[d["n_loss"] > 0].iterrows():
        losers = str(r.get("loses_to", "") or "")
        names = {x.strip() for x in losers.split(",") if x.strip()}
        if names - SIBLINGS:
            bad.append((r["mu"], r["tau"], r["k"], r["mechanism"], sorted(names - SIBLINGS)))
    return bad


@pytest.mark.parametrize("tag", ["cm", "lm"])
def test_auto_leads_every_variant_moderate(tag):
    counts = {h: int(_dom(tag, h)["dominates_field"].sum()) for h in VARIANTS}
    assert counts["adaptshrink_auto"] == max(counts.values()), counts
    # strictly ahead of the next-best variant (not merely tied)
    others = sorted(v for h, v in counts.items() if h != "adaptshrink_auto")
    assert counts["adaptshrink_auto"] > others[-1], counts


@pytest.mark.parametrize("tag", ["cm", "lm"])
def test_no_external_comparator_beats_auto_moderate(tag):
    bad = _external_loss_cells(tag)
    assert bad == [], f"{tag}: external comparator beats auto in cells {bad}"


def test_moderate_domination_survives_vs_strong():
    # strong grid restricted to the SAME step+copas selection cells is the honest
    # comparison denominator; moderate must be >= it on both metrics.
    for strong_tag, mod_tag in [("c2", "cm"), ("l2", "lm")]:
        s = _dom(strong_tag, "adaptshrink_auto")
        s = s[s["mechanism"].isin(["step", "copas"])]
        m = _dom(mod_tag, "adaptshrink_auto")
        assert int(m["dominates_field"].sum()) >= int(s["dominates_field"].sum()), \
            (strong_tag, int(s["dominates_field"].sum()), mod_tag, int(m["dominates_field"].sum()))
        # and moderate has no MORE loss cells than strong
        assert int((m["n_loss"] > 0).sum()) <= int((s["n_loss"] > 0).sum())
