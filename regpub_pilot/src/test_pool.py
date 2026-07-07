"""Regression test: pooling core vs metafor (rma REML + Knapp-Hartung).
Reference values captured from R 4.6.0 metafor on a heterogeneous dataset (Q>k-1,
so the HKSJ floor does not bind and we should match metafor closely)."""
import sys; sys.path.insert(0, ".")
from pool import pool

def test_reml_hksj_vs_metafor():
    yi = [-0.80,-0.20,-0.55,0.10,-0.40,-0.90,-0.05,-0.65]
    vi = [0.02,0.03,0.015,0.04,0.02,0.03,0.05,0.025]
    r = pool(yi, vi, method="REML", hksj=True)
    # metafor: est=-0.450165 se=0.123527 ci=-0.742261,-0.158070 tau2=0.088638
    assert abs(r["est"] - (-0.450165)) < 1e-4, r["est"]
    assert abs(r["se"] - 0.123527) < 1e-4, r["se"]
    assert abs(r["tau2"] - 0.088638) < 1e-4, r["tau2"]
    assert abs(r["ci_lo"] - (-0.742261)) < 2e-3 and abs(r["ci_hi"] - (-0.158070)) < 2e-3
    print("  [ok] REML+HKSJ matches metafor (est/se/tau2 <1e-4; CI <2e-3 via t-quantile approx)")

def test_hksj_floor():
    # Q < k-1 regime: our documented floor keeps CI from narrowing below fixed-effect
    yi = [-0.15,-0.24,-0.09,-0.12,-0.07,-0.31]; vi = [0.010,0.020,0.008,0.015,0.030,0.012]
    r = pool(yi, vi, method="REML", hksj=True)
    rf = pool(yi, vi, method="REML", hksj=False)
    assert r["se"] >= rf["se"] - 1e-9, "floor must not narrow below unscaled SE"
    print("  [ok] HKSJ floor holds (no anti-conservative narrowing when Q<k-1)")

if __name__ == "__main__":
    test_reml_hksj_vs_metafor(); test_hksj_floor()
    print("ALL POOL TESTS PASSED")
