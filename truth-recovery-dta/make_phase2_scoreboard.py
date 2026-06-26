"""make_phase2_scoreboard.py -- synthesise Phase-2 DTA bake-off results.

Reads:
  dta_focus_table.csv / dta_focus_truthgate.json   (focus grid, 800 reps)
  dta_sparse_table.csv / dta_sparse_truthgate.json  (HSROC-tail grid, if present)

Writes:
  dta_phase2_scoreboard.csv      -- full method x cell x strength table
  dta_phase2_scoreboard.txt      -- human-readable regime summary
  dta_phase2_hsroc_tail.txt      -- HSROC-tail characterisation (sparse grid)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import io
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent

# Safe stdout for Windows cp1252 consoles
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

METHODS_ORDER = [
    "adaptshrink_dta", "reitsma", "reitsma_reml",
    "reitsma_indep", "sep_univariate", "hsroc",
]
HC = "reitsma"
OURS = "adaptshrink_dta"

METHOD_LABELS = {
    "adaptshrink_dta": "AdaptShrink-DTA",
    "reitsma":         "Reitsma (ML)",
    "reitsma_reml":    "Reitsma (REML)",
    "reitsma_indep":   "Reitsma (ρ=0)",
    "sep_univariate":  "Sep-Univariate",
    "hsroc":           "HSROC",
}
FIELD = [m for m in METHODS_ORDER if m not in (OURS, HC)]

SEL_ORDER = ["none", "moderate", "strong"]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def load_grid(prefix: str):
    """Return (table, gate) or (None, None)."""
    tp = HERE / f"{prefix}_table.csv"
    gp = HERE / f"{prefix}_truthgate.json"
    if not tp.exists():
        return None, None
    tbl = pd.read_csv(tp)
    gate = json.loads(gp.read_text()) if gp.exists() else {}
    return tbl, gate


def _robust_vs_hc(gate: dict) -> dict[tuple, bool]:
    """Map (cell, strength, method) -> robust_win_vs_HC."""
    out: dict[tuple, bool] = {}
    for b in gate.get("bootstrap_mciw0_vs_HC", []):
        out[(b["cell"], b["strength"], b["method"])] = b["robust_win"]
    return out


def _ours_robust_vs_field(gate: dict) -> dict[tuple, bool]:
    """Map (cell, strength, vs) -> ours_robust_beats."""
    out: dict[tuple, bool] = {}
    for b in gate.get("ours_vs_field", []):
        out[(b["cell"], b["strength"], b["vs"])] = b["ours_robust_beats"]
    return out


def _ours_frac(gate: dict) -> dict[tuple, float]:
    """Map (cell, strength, vs) -> frac_ours_better."""
    out: dict[tuple, float] = {}
    for b in gate.get("ours_vs_field", []):
        out[(b["cell"], b["strength"], b["vs"])] = b["frac_ours_better"]
    return out


# ---------------------------------------------------------------------------
# Build the composite scoreboard table
# ---------------------------------------------------------------------------

def build_scoreboard(tbl: pd.DataFrame, gate: dict) -> pd.DataFrame:
    rv_hc = _robust_vs_hc(gate)
    ov_field = _ours_robust_vs_field(gate)
    ov_frac = _ours_frac(gate)

    rows = []
    for (cell, strength, method), g in tbl.groupby(["cell", "strength", "method"]):
        r = g.iloc[0]
        rob = rv_hc.get((cell, strength, method), None)
        if method == OURS:
            field_wins = {vs: ov_field.get((cell, strength, vs), None) for vs in FIELD}
            field_fracs = {vs: ov_frac.get((cell, strength, vs), None) for vs in FIELD}
        else:
            field_wins = {vs: None for vs in FIELD}
            field_fracs = {vs: None for vs in FIELD}

        rows.append({
            "cell": cell,
            "strength": strength,
            "method": method,
            "n_reps": int(r["n"]),
            "bias1": float(r["bias1"]),
            "bias2": float(r["bias2"]),
            "rmse": float(r["rmse"]),
            "raw_cov": float(r["raw_cov"]),
            "raw_area": float(r["raw_area"]),
            "mciw0_area": float(r["mciw0_area"]),
            "mciw0_cov": float(r["mciw0_cov"]),
            "kappa": float(r["kappa"]),
            "robust_win_vs_HC": rob,
            **{f"ours_beats_{vs}": field_wins[vs] for vs in FIELD},
            **{f"frac_vs_{vs}": field_fracs[vs] for vs in FIELD},
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Human-readable summary text
# ---------------------------------------------------------------------------

def _regime_summary(tbl: pd.DataFrame, gate: dict, grid_name: str) -> str:
    rv_hc = _robust_vs_hc(gate)
    ov_field = _ours_robust_vs_field(gate)
    ov_frac = _ours_frac(gate)

    lines = [
        f"# AdaptShrink-DTA Phase-2 Scoreboard — {grid_name}",
        "=" * 72,
        "MCIW0-2D area = matched-coverage region area (PRIMARY, lower=better).",
        "Bootstrap(2000) 97.5th %ile of (method−HC) < 0 → robust_win.",
        "OURS = adaptshrink_dta; HC = reitsma (field-to-beat); field = rest.",
        "",
    ]

    cells = sorted(tbl["cell"].unique())
    for cell in cells:
        for strength in SEL_ORDER:
            sub = tbl[(tbl["cell"] == cell) & (tbl["strength"] == strength)]
            if sub.empty:
                continue
            sub = sub.copy().sort_values("mciw0_area")
            hc_row = sub[sub["method"] == HC]
            if hc_row.empty:
                continue
            hc_area = float(hc_row["mciw0_area"].iloc[0])
            our_row = sub[sub["method"] == OURS]
            our_area = float(our_row["mciw0_area"].iloc[0]) if not our_row.empty else None

            lines.append(f"## {cell}  selection={strength}")
            lines.append(
                f"{'method':<20} {'mciw0_area':>11} {'vs_HC':>7} "
                f"{'rob_HC':>8} {'raw_cov':>8} {'rmse':>7}"
            )
            for _, r in sub.iterrows():
                m = r["method"]
                area = r["mciw0_area"]
                delta = area - hc_area
                delta_str = f"{delta:+.4f}"
                rob = rv_hc.get((cell, strength, m))
                rob_str = "YES" if rob else ("no" if rob is False else "—")
                label = METHOD_LABELS.get(m, m)
                star = " *" if m == OURS else ("  " if m == HC else "  ")
                lines.append(
                    f"  {label:<18}{star}{area:>11.4f} {delta_str:>7} "
                    f"{rob_str:>8} {r['raw_cov']:>8.3f} {r['rmse']:>7.4f}"
                )

            # AdaptShrink vs field
            if our_area is not None:
                lines.append("")
                lines.append(f"  AdaptShrink-DTA vs field  (robust = 97.5th %ile < 0):")
                for vs in METHODS_ORDER:
                    if vs == OURS:
                        continue
                    rob_b = ov_field.get((cell, strength, vs))
                    frac = ov_frac.get((cell, strength, vs))
                    vs_row = sub[sub["method"] == vs]
                    if vs_row.empty:
                        continue
                    vs_area = float(vs_row["mciw0_area"].iloc[0])
                    diff = our_area - vs_area
                    rob_str = "BEATS" if rob_b else ("loses" if rob_b is False else "—")
                    frac_str = f"{frac:.3f}" if frac is not None else "—"
                    lines.append(
                        f"    vs {METHOD_LABELS.get(vs, vs):<18}: "
                        f"Δarea={diff:+.4f} robust={rob_str}  frac_better={frac_str}"
                    )
            lines.append("")

    # Overall summary
    ours_robust = gate.get("ours_robust_wins_vs_field", [])
    hc_robust = gate.get("robust_wins_vs_HC", [])
    lines.append("=" * 72)
    lines.append("OVERALL ROBUST WINS (bootstrap G4, 97.5th %ile < 0)")
    lines.append("")
    lines.append(f"AdaptShrink-DTA robustly beats HC (reitsma) in {sum(1 for b in hc_robust if b['method']==OURS)}/{sum(1 for b in gate.get('bootstrap_mciw0_vs_HC',[]) if b['method']==OURS)} cells (of those tested).")
    lines.append("")
    lines.append("AdaptShrink-DTA robustly beats each field member:")
    by_field: dict[str, list[str]] = {}
    for r in ours_robust:
        by_field.setdefault(r["vs"], []).append(f"{r['cell']}×{r['strength']}")
    total_cells = len(set((r["cell"], r["strength"]) for r in gate.get("ours_vs_field", [])))
    for vs in METHODS_ORDER:
        if vs == OURS:
            continue
        wins = by_field.get(vs, [])
        lines.append(f"  vs {METHOD_LABELS.get(vs, vs):<18}: {len(wins)}/{total_cells} cells: {', '.join(wins) if wins else '(none)'}")

    lines.append("")
    lines.append("Cells where OURS does NOT robustly beat HC:")
    for b in gate.get("bootstrap_mciw0_vs_HC", []):
        if b["method"] == OURS and not b["robust_win"]:
            lines.append(
                f"  {b['cell']}×{b['strength']}: "
                f"Δ={b['darea']:+.4f} [{b['ci_lo']:+.4f}, {b['ci_hi']:+.4f}]  "
                f"frac_better={b['frac_better']:.3f}"
            )

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# HSROC-tail characterisation text
# ---------------------------------------------------------------------------

def hsroc_tail_report(tbl: pd.DataFrame, gate: dict) -> str:
    lines = [
        "# HSROC Heavy-Tail / Sparse-Cell Characterisation",
        "=" * 72,
        "Sparse grid: k ∈ {6,10,20} × prev ∈ {0.1, 0.3}, small n",
        "(n_med=40, n_sigma=0.9, n_min=12 → frequent zero/near-zero cells)",
        "All methods including exact-binomial HSROC.",
        "",
    ]

    rv_hc = _robust_vs_hc(gate)
    ov_field = _ours_robust_vs_field(gate)

    cells = sorted(tbl["cell"].unique())
    for cell in cells:
        for strength in SEL_ORDER:
            sub = tbl[(tbl["cell"] == cell) & (tbl["strength"] == strength)]
            if sub.empty:
                continue
            sub = sub.copy().sort_values("mciw0_area")
            hc_row = sub[sub["method"] == HC]
            if hc_row.empty:
                continue
            hc_area = float(hc_row["mciw0_area"].iloc[0])

            lines.append(f"## {cell}  selection={strength}")
            lines.append(
                f"{'method':<20} {'mciw0_area':>11} {'Δ_vs_HC':>8} "
                f"{'rob_HC':>8} {'raw_cov':>8} {'bias1':>7} {'bias2':>7}"
            )
            for _, r in sub.iterrows():
                m = r["method"]
                area = r["mciw0_area"]
                delta = area - hc_area
                rob = rv_hc.get((cell, strength, m))
                rob_str = "YES" if rob else ("no" if rob is False else "—")
                label = METHOD_LABELS.get(m, m)
                marker = "* " if m == OURS else ("HC" if m == HC else "  ")
                lines.append(
                    f"  {label:<18}{marker}{area:>11.4f} {delta:>+8.4f} "
                    f"{rob_str:>8} {r['raw_cov']:>8.3f} {r['bias1']:>7.4f} {r['bias2']:>7.4f}"
                )
            lines.append("")

    # HSROC convergence / stability note
    hsroc_rows = tbl[tbl["method"] == "hsroc"]
    lines.append("## HSROC stability summary across sparse cells")
    if hsroc_rows.empty:
        lines.append("  (HSROC not in results — may have been excluded from this run)")
    else:
        for (cell, strength), g in hsroc_rows.groupby(["cell", "strength"]):
            n = int(g["n"].iloc[0])
            area = float(g["mciw0_area"].iloc[0])
            cov = float(g["raw_cov"].iloc[0])
            rob = rv_hc.get((cell, strength, "hsroc"), None)
            rob_str = "ROBUST-WIN" if rob else ("loses" if rob is False else "—")
            lines.append(
                f"  {cell}×{strength}: n_converged={n}  mciw0_area={area:.4f}"
                f"  raw_cov={cov:.3f}  vs_HC={rob_str}"
            )

    lines.append("")
    lines.append("## AdaptShrink-DTA vs HSROC in sparse regime")
    for r in gate.get("ours_vs_field", []):
        if r["vs"] == "hsroc":
            rob_str = "OURS_BEATS" if r["ours_robust_beats"] else "HSROC_BETTER_OR_TIE"
            lines.append(
                f"  {r['cell']}×{r['strength']}: "
                f"Δarea(ours-hsroc)={r['darea_ours_minus_x']:+.4f} "
                f"[{r['ours_better_ci_lo']:+.4f}, {r['ours_better_ci_hi']:+.4f}]  "
                f"{rob_str}"
            )

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    print("[scoreboard] Loading focus grid ...", flush=True)
    focus_tbl, focus_gate = load_grid("dta_focus")
    sparse_tbl, sparse_gate = load_grid("dta_sparse")

    if focus_tbl is not None:
        sb = build_scoreboard(focus_tbl, focus_gate)
        out_csv = HERE / "dta_phase2_scoreboard.csv"
        sb.to_csv(out_csv, index=False)
        print(f"[scoreboard] wrote {out_csv}", flush=True)

        txt = _regime_summary(focus_tbl, focus_gate, "focus grid (800 reps)")
        out_txt = HERE / "dta_phase2_scoreboard.txt"
        out_txt.write_text(txt, encoding="utf-8")
        print(f"[scoreboard] wrote {out_txt}", flush=True)
        print(txt)
    else:
        print("[scoreboard] focus table not found — nothing to do.", flush=True)

    if sparse_tbl is not None:
        # Add a 'grid' column so we can combine
        sparse_sb = build_scoreboard(sparse_tbl, sparse_gate)
        out_csv2 = HERE / "dta_phase2_scoreboard_sparse.csv"
        sparse_sb.to_csv(out_csv2, index=False)
        print(f"[scoreboard] wrote {out_csv2}", flush=True)

        tail_txt = hsroc_tail_report(sparse_tbl, sparse_gate)
        out_tail = HERE / "dta_phase2_hsroc_tail.txt"
        out_tail.write_text(tail_txt, encoding="utf-8")
        print(f"[scoreboard] wrote {out_tail}", flush=True)
        print(tail_txt)
    else:
        print("[scoreboard] sparse table not found — HSROC-tail characterisation pending.", flush=True)


if __name__ == "__main__":
    main()
