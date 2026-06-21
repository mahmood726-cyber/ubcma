"""dta_bakeoff.py -- matched-coverage region bake-off for AdaptShrink-DTA.

Generalizes the univariate matched-coverage protocol (MCIW0) to the bivariate
DTA summary operating point (M1, M2) = (logit Se, logit Sp). The efficiency
analogue of "interval width" is the **confidence-region AREA**.

For each (cell, method) we split replicates calib/test by rep-parity:

  MCIW0-2D (PRIMARY -- point-estimator efficiency, constant region):
     e_i = (M1_hat - M1, M2_hat - M2)
     W   = cov(e) on calib;  d2_i = e_i' W^-1 e_i;  q = T-quantile(d2) on calib
     region = {e: e' W^-1 e <= q};  AREA = pi * q * sqrt(det W)
     test_cov = frac of test e inside.  (isolates the error cloud, no width model)

  MCIW-2D (secondary): scale each method's OWN 95% ellipse by kappa to hit T on
     calib; compare ellipse area on test (rewards difficulty-tracking uncertainty).

  raw (deployable, kappa=1): the method's actual joint coverage + ellipse area.

Truth-gate (same spine as the univariate bake-off):
  G1  every scored row has finite (M1,M2) and a finite PD region.
  G2/G3  a win requires MCIW0-2D area below Reitsma's AND the winner's constant-
         region calibration to generalize on test (|test_cov - T| <= tol).
  G4 (decisive) paired bootstrap: 97.5th percentile of (method - Reitsma) area
         advantage < 0.

Reitsma (bivariate REML/ML) is the ground-truth comparator -- the DTA analogue
of Henmi-Copas.

Run:
  PYTHONPATH=src python truth-recovery-dta/dta_bakeoff.py --reps 300 --grid pilot
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import dta_sim as G  # noqa: E402
from ubcma.dta import (  # noqa: E402
    from_counts, reitsma, reitsma_indep, sep_univariate, adaptshrink_dta,
)

METHODS = {
    "reitsma": reitsma,
    "reitsma_indep": reitsma_indep,
    "sep_univariate": sep_univariate,
    "adaptshrink_dta": adaptshrink_dta,
}
HC = "reitsma"  # ground-truth comparator
CHI2_2 = chi2.ppf(0.95, df=2)


# ---------------------------------------------------------------------------
# Simulation grid
# ---------------------------------------------------------------------------
def build_grid(name: str) -> list[dict]:
    """Return a list of cell dicts: {label, spec, strength}."""
    cells = []
    if name == "pilot":
        specs = [
            ("k10_thr", G.DTASpec(k=10, rho=-0.6, tau1=0.6, tau2=0.6, prev=0.3)),
            ("k20_thr", G.DTASpec(k=20, rho=-0.6, tau1=0.6, tau2=0.6, prev=0.3)),
        ]
        strengths = ["none", "strong"]
    elif name == "full":
        specs = []
        for k in (6, 10, 20, 40):
            for rho in (0.0, -0.4, -0.8):
                for prev in (0.1, 0.3, 0.5):
                    specs.append((f"k{k}_rho{rho}_p{prev}",
                                  G.DTASpec(k=k, rho=rho, tau1=0.6, tau2=0.6,
                                            prev=prev)))
        strengths = ["none", "moderate", "strong"]
    elif name == "smallk":
        specs = [
            ("k6_thr",  G.DTASpec(k=6, rho=-0.6, tau1=0.6, tau2=0.6, prev=0.3)),
            ("k10_thr", G.DTASpec(k=10, rho=-0.6, tau1=0.6, tau2=0.6, prev=0.3)),
            ("k6_hi",   G.DTASpec(k=6, rho=-0.4, tau1=0.8, tau2=0.8, prev=0.2)),
        ]
        strengths = ["none", "moderate", "strong"]
    else:
        raise ValueError(name)
    for label, spec in specs:
        for s in strengths:
            cells.append({"label": label, "spec": spec, "strength": s})
    return cells


# ---------------------------------------------------------------------------
# Replicates
# ---------------------------------------------------------------------------
def run_cell(cell: dict, reps: int, seed0: int) -> pd.DataFrame:
    spec, strength, label = cell["spec"], cell["strength"], cell["label"]
    rows = []
    for r in range(reps):
        tp, fp, fn, tn, M = G.generate(spec, strength, seed0 + r)
        studies = from_counts(tp, fp, fn, tn)
        for mname, fn_m in METHODS.items():
            try:
                res = fn_m(studies)
            except Exception:
                res = {"converged": False}
            conv = bool(res.get("converged", False))
            V = res.get("V")
            row = {
                "cell": label, "strength": strength, "rep": r, "method": mname,
                "true_m1": float(M[0]), "true_m2": float(M[1]),
                "m1": res.get("M1", np.nan), "m2": res.get("M2", np.nan),
                "converged": conv,
                "area_raw": res.get("region_area", np.nan),
                "v00": np.nan, "v01": np.nan, "v11": np.nan,
                "k_eff": int(studies.k),
            }
            if conv and V is not None:
                Va = np.asarray(V, float)
                row["v00"], row["v01"], row["v11"] = (
                    float(Va[0, 0]), float(Va[0, 1]), float(Va[1, 1]))
            rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Region helpers
# ---------------------------------------------------------------------------
def _joint_covered(row) -> bool:
    """Is the true point inside the method's raw 95% ellipse (deployable)?"""
    V = np.array([[row["v00"], row["v01"]], [row["v01"], row["v11"]]])
    if not np.all(np.isfinite(V)):
        return False
    try:
        Vinv = np.linalg.inv(V)
    except np.linalg.LinAlgError:
        return False
    e = np.array([row["m1"] - row["true_m1"], row["m2"] - row["true_m2"]])
    return bool(e @ Vinv @ e <= CHI2_2)


def matched_coverage_table(df: pd.DataFrame, target: float = 0.95) -> pd.DataFrame:
    out = []
    for (cell, strength, method), g in df.groupby(["cell", "strength", "method"]):
        g = g[g["converged"] & np.isfinite(g["m1"]) & np.isfinite(g["m2"])
              & np.isfinite(g["v00"]) & np.isfinite(g["v11"])].copy()
        n = len(g)
        if n < 16:
            continue
        e = np.column_stack([g["m1"] - g["true_m1"], g["m2"] - g["true_m2"]])
        reps = g["rep"].to_numpy()
        bias1 = float(np.mean(e[:, 0]))
        bias2 = float(np.mean(e[:, 1]))
        rmse = float(np.sqrt(np.mean(np.sum(e ** 2, axis=1))))

        # deployable joint coverage + raw ellipse area
        raw_cov = float(np.mean([_joint_covered(r) for _, r in g.iterrows()]))
        raw_area = float(np.nanmean(g["area_raw"].to_numpy()))

        calib = reps % 2 == 0
        test = ~calib
        if calib.sum() < 8 or test.sum() < 8:
            continue

        # --- MCIW0-2D: constant Mahalanobis region from the calib error cloud ---
        Ec = e[calib]
        W = np.cov(Ec, rowvar=False)
        try:
            Winv = np.linalg.inv(W)
            detW = np.linalg.det(W)
        except np.linalg.LinAlgError:
            continue
        if not np.isfinite(detW) or detW <= 0:
            continue
        d2c = np.einsum("ij,jk,ik->i", Ec, Winv, Ec)
        q = float(np.quantile(d2c, target))
        Et = e[test]
        d2t = np.einsum("ij,jk,ik->i", Et, Winv, Et)
        mciw0_cov = float(np.mean(d2t <= q))
        mciw0_area = float(np.pi * q * np.sqrt(detW))

        # --- MCIW-2D: scale the method's OWN ellipse to target on calib ---
        # per-rep Mahalanobis of the true point under the method's own V
        maha = np.full(n, np.nan)
        Vs = g[["v00", "v01", "v11"]].to_numpy()
        for i in range(n):
            Vi = np.array([[Vs[i, 0], Vs[i, 1]], [Vs[i, 1], Vs[i, 2]]])
            try:
                Vinv = np.linalg.inv(Vi)
            except np.linalg.LinAlgError:
                continue
            maha[i] = e[i] @ Vinv @ e[i]
        ok = np.isfinite(maha)
        c_ok = ok & calib
        t_ok = ok & test
        if c_ok.sum() >= 8 and t_ok.sum() >= 8:
            # scale factor s on the ELLIPSE so that s * CHI2_2 covers target:
            # need P(maha <= s*CHI2_2)=target -> s = quantile(maha)/CHI2_2.
            s = float(np.quantile(maha[c_ok], target) / CHI2_2)
            mciw_cov = float(np.mean(maha[t_ok] <= s * CHI2_2))
            # mean area on test of the scaled ellipse: area_i * s (area ∝ s)
            mciw_area = float(np.nanmean(g["area_raw"].to_numpy()[t_ok]) * s)
        else:
            s = mciw_cov = mciw_area = float("nan")

        out.append({
            "cell": cell, "strength": strength, "method": method, "n": n,
            "bias1": round(bias1, 4), "bias2": round(bias2, 4),
            "rmse": round(rmse, 4),
            "raw_cov": round(raw_cov, 3), "raw_area": round(raw_area, 4),
            "mciw0_area": round(mciw0_area, 4), "mciw0_cov": round(mciw0_cov, 3),
            "kappa": round(s, 3), "mciw_area": round(mciw_area, 4),
            "mciw_cov": round(mciw_cov, 3),
        })
    return pd.DataFrame(out)


def _bootstrap_mciw0(df: pd.DataFrame, target: float, n_boot: int = 2000,
                     seed: int = 7) -> list[dict]:
    """Paired bootstrap of the MCIW0-2D AREA advantage (method - HC) per cell.

    Errors paired across methods within a (cell, strength, rep). Resample reps;
    recompute each method's constant-region area = pi * q * sqrt(det W) where W
    and q come from the resampled error cloud. Robust win iff 97.5th pct < 0.
    """
    rng = np.random.default_rng(seed)
    out = []
    for (cell, strength), g in df.groupby(["cell", "strength"]):
        g = g[g["converged"] & np.isfinite(g["m1"]) & np.isfinite(g["m2"])].copy()
        g["e1"] = g["m1"] - g["true_m1"]
        g["e2"] = g["m2"] - g["true_m2"]
        # pivot to reps x method for paired resampling
        piv1 = g.pivot_table(index="rep", columns="method", values="e1")
        piv2 = g.pivot_table(index="rep", columns="method", values="e2")
        common = piv1.dropna().index.intersection(piv2.dropna().index)
        if HC not in piv1.columns or len(common) < 24:
            continue
        piv1 = piv1.loc[common]
        piv2 = piv2.loc[common]
        reps = np.arange(len(common))
        methods = [m for m in piv1.columns if m != HC]

        def area_of(e1, e2):
            E = np.column_stack([e1, e2])
            W = np.cov(E, rowvar=False)
            detW = np.linalg.det(W)
            if not np.isfinite(detW) or detW <= 0:
                return np.nan
            Winv = np.linalg.inv(W)
            d2 = np.einsum("ij,jk,ik->i", E, Winv, E)
            q = np.quantile(d2, target)
            return np.pi * q * np.sqrt(detW)

        boot_idx = rng.integers(0, len(reps), size=(n_boot, len(reps)))
        hc1 = piv1[HC].to_numpy()
        hc2 = piv2[HC].to_numpy()
        hc_area_b = np.array([area_of(hc1[bi], hc2[bi]) for bi in boot_idx])
        for m in methods:
            m1 = piv1[m].to_numpy()
            m2 = piv2[m].to_numpy()
            m_area_b = np.array([area_of(m1[bi], m2[bi]) for bi in boot_idx])
            diff = m_area_b - hc_area_b
            diff = diff[np.isfinite(diff)]
            if len(diff) < 100:
                continue
            lo, hi = np.quantile(diff, [0.025, 0.975])
            point = area_of(m1, m2) - area_of(hc1, hc2)
            out.append({
                "cell": cell, "strength": strength, "method": m,
                "darea": round(float(point), 4),
                "ci_lo": round(float(lo), 4), "ci_hi": round(float(hi), 4),
                "robust_win": bool(hi < 0.0),
                "frac_better": round(float(np.mean(diff < 0.0)), 3),
            })
    return out


def truth_gate(df: pd.DataFrame, table: pd.DataFrame, target: float,
               cov_tol: float = 0.06) -> dict:
    gate = {"target": target, "cov_tol": cov_tol, "pass": True, "notes": []}
    scored = df[df["method"].isin(METHODS)]
    conv = scored[scored["converged"]]
    bad_point = conv[~(np.isfinite(conv["m1"]) & np.isfinite(conv["m2"]))]
    npd = conv[np.isfinite(conv["m1"]) & np.isfinite(conv["m2"]) &
               ~(np.isfinite(conv["v00"]) & np.isfinite(conv["v11"]) &
                 np.isfinite(conv["v01"]))]
    gate["G1_finite_point_ok"] = bool(len(bad_point) == 0)
    gate["npd_region_excluded"] = int(len(npd))
    if len(bad_point):
        gate["pass"] = False
        gate["notes"].append(
            f"G1 FAIL: {len(bad_point)} converged rows with non-finite point")

    wins = []
    for (cell, strength), g in table.groupby(["cell", "strength"]):
        g = g.set_index("method")
        if HC not in g.index:
            continue
        hc = g.loc[HC]
        for method, row in g.iterrows():
            if method == HC:
                continue
            cov_ok = abs(row["mciw0_cov"] - target) <= cov_tol
            beats = (row["mciw0_area"] < hc["mciw0_area"] - 1e-9) and cov_ok
            if beats:
                wins.append({
                    "cell": cell, "strength": strength, "method": method,
                    "mciw0_area": float(row["mciw0_area"]),
                    "hc_area": float(hc["mciw0_area"]),
                    "ratio": round(float(row["mciw0_area"] / hc["mciw0_area"]), 3),
                    "test_cov": float(row["mciw0_cov"]),
                })
    gate["verified_wins_vs_HC"] = wins
    boot = _bootstrap_mciw0(df, target)
    gate["bootstrap_mciw0_vs_HC"] = boot
    gate["robust_wins_vs_HC"] = [b for b in boot if b["robust_win"]]
    return gate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=300)
    ap.add_argument("--grid", default="pilot", choices=["pilot", "smallk", "full"])
    ap.add_argument("--target", type=float, default=0.95)
    ap.add_argument("--out-prefix", default="truth-recovery-dta/dta")
    ap.add_argument("--from-csv", default=None)
    args = ap.parse_args()

    t0 = time.time()
    raw_path = f"{args.out_prefix}_{args.grid}_perrep.csv"
    if args.from_csv:
        raw = pd.read_csv(args.from_csv)
        raw_path = args.from_csv
        print(f"[dta] recompute from {args.from_csv} (no re-sim)", flush=True)
    else:
        cells = build_grid(args.grid)
        frames = []
        for c in cells:
            print(f"[dta] cell={c['label']} strength={c['strength']} "
                  f"reps={args.reps} ...", flush=True)
            frames.append(run_cell(c, args.reps, G.BASE_SEED))
        raw = pd.concat(frames, ignore_index=True)
        raw.to_csv(raw_path, index=False)

    table = matched_coverage_table(raw, target=args.target)
    table_path = f"{args.out_prefix}_{args.grid}_table.csv"
    table.to_csv(table_path, index=False)
    gate = truth_gate(raw, table, target=args.target)
    gate_path = f"{args.out_prefix}_{args.grid}_truthgate.json"
    Path(gate_path).write_text(json.dumps(gate, indent=2))

    secs = round(time.time() - t0, 1)
    print(f"\n# AdaptShrink-DTA matched-coverage bake-off (grid={args.grid}, "
          f"target={args.target})")
    print("MCIW0-2D area = matched-coverage region AREA (PRIMARY; lower=better).")
    print("raw_cov/raw_area = deployable (kappa=1). HC = reitsma.\n")
    for (cell, strength), sub in table.groupby(["cell", "strength"]):
        sub = sub.sort_values("mciw0_area")
        print(f"-- cell={cell} strength={strength} --")
        print(f"{'method':<16}{'bias1':>8}{'bias2':>8}{'rmse':>8}"
              f"{'raw_cov':>9}{'MCIW0a':>9}{'mc0cov':>8}{'MCIWa':>9}{'mccov':>7}")
        hc_area = sub[sub.method == HC]["mciw0_area"]
        hc_area = float(hc_area.iloc[0]) if len(hc_area) else None
        for _, r in sub.iterrows():
            star = ""
            if hc_area and r["method"] != HC and r["mciw0_area"] < hc_area:
                star = "  <-- smaller than HC"
            print(f"{r['method']:<16}{r['bias1']:>8.3f}{r['bias2']:>8.3f}"
                  f"{r['rmse']:>8.3f}{r['raw_cov']:>9.3f}{r['mciw0_area']:>9.4f}"
                  f"{r['mciw0_cov']:>8.3f}{r['mciw_area']:>9.4f}"
                  f"{r['mciw_cov']:>7.3f}{star}")
        print()

    print("# TRUTH-GATE")
    print(f"  G1 finite points ok: {gate['G1_finite_point_ok']}  "
          f"(NPD-region rows excluded: {gate['npd_region_excluded']})")
    print("  Paired-bootstrap MCIW0-2D area advantage vs HC (robust win = 97.5% CI < 0):")
    for b in gate["bootstrap_mciw0_vs_HC"]:
        flag = "  ROBUST WIN" if b["robust_win"] else ""
        print(f"    [{b['cell']:<8} {b['strength']:<8}] {b['method']:<16} "
              f"dArea={b['darea']:+.4f} CI[{b['ci_lo']:+.4f},{b['ci_hi']:+.4f}] "
              f"P(better)={b['frac_better']:.3f}{flag}")
    print(f"\nWrote {raw_path}\n      {table_path}\n      {gate_path}  ({secs}s)")


if __name__ == "__main__":
    main()
