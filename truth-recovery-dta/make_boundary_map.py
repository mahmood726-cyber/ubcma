"""make_boundary_map.py -- render the AdaptShrink-DTA win-frontier boundary map.

Reads the `boundary` grid truth-gate (adaptshrink_dta vs reitsma=HC, paired
bootstrap of MCIW0-2D area) and prints a k x selection-strength grid showing
the point dArea, the bootstrap robustness verdict, and the frontier (the k at
which the robust win turns off) for each selection regime. NMA-analogue of the
tau x selection x n boundary map.

Run:  python truth-recovery-dta/make_boundary_map.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
GATE = HERE / "dta_boundary_truthgate.json"


def kof(cell: str) -> int:
    m = re.search(r"k(\d+)_", cell)
    return int(m.group(1)) if m else -1


def main() -> None:
    gate = json.loads(GATE.read_text())
    boot = [b for b in gate["bootstrap_mciw0_vs_HC"]
            if b["method"] == "adaptshrink_dta"]
    ks = sorted({kof(b["cell"]) for b in boot})
    strengths = ["none", "moderate", "strong"]
    by = {(kof(b["cell"]), b["strength"]): b for b in boot}

    print("# AdaptShrink-DTA vs Reitsma (HC) -- WIN-FRONTIER boundary map")
    print("# fixed threshold-het regime rho=-0.6 tau=0.6 prev=0.3; 800 reps/cell")
    print("# cell value = dArea (ours-HC; negative=ours smaller/better);"
          " *=bootstrap-robust (97.5% CI<0)\n")
    head = "k \\ sel".ljust(9) + "".join(s.center(16) for s in strengths)
    print(head)
    print("-" * len(head))
    for k in ks:
        row = f"k={k}".ljust(9)
        for s in strengths:
            b = by.get((k, s))
            if b is None:
                cell = "n/a"
            else:
                star = "*" if b["robust_win"] else " "
                cell = f"{b['darea']:+.4f}{star}(P{b['frac_better']:.2f})"
            row += cell.center(16)
        print(row)

    print("\n# Frontier per selection regime (smallest k that is NOT robust):")
    for s in strengths:
        robust_ks = [k for k in ks if by.get((k, s), {}).get("robust_win")]
        nonrobust = [k for k in ks if (k, s) in by
                     and not by[(k, s)]["robust_win"]]
        if robust_ks:
            edge = min([k for k in nonrobust if k > max(robust_ks)],
                       default=None)
            msg = (f"robust for k in {robust_ks}; "
                   + (f"turns off by k={edge}" if edge else "robust to k_max"))
        else:
            msg = "no robust win at any k"
        print(f"  {s:<9}: {msg}")


if __name__ == "__main__":
    main()
