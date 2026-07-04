"""Studies-per-edge (m) axis for AdaptShrink-NMA — the most deployment-relevant sparsity dimension.
Phase-3 mapped network SIZE; topology_sweep mapped TOPOLOGY; this maps m = direct studies per contrast.
Real NMAs frequently have 1-2 studies per direct comparison, exactly where the common-DL per-contrast
estimate is most unstable. Does the matched-coverage win hold as m -> 1? Reuses topology_stress.run
(dense network, strong pre-declared small-study effect B=1.0).
"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import topology_stress as ts  # noqa: E402  (re-wraps stdout on import; do not re-wrap)

MS = [1, 2, 3, 4, 8]


def main():
    print("=" * 74)
    print("AdaptShrink-NMA: studies-per-edge (m) sweep, dense n=8, strong selection B=1.0")
    print("  dMCIW0 = auto - common-DL; negative + CI<0 = robust matched-coverage win; reps=400")
    print("=" * 74)
    print(f"  {'m/edge':>7}{'#studies':>10}{'MCIW0 DL':>11}{'MCIW0 auto':>12}{'dMCIW0':>9}{'  95% CI':>20}{'verdict':>9}")
    out = []
    for m in MS:
        r = ts.run(n=8, topology="dense", m=m, B=1.0, reps=400, seed=5, boot=2500)
        ci = f"[{r['ci'][0]:+.4f},{r['ci'][1]:+.4f}]"
        print(f"  {m:>7}{28*m:>10}{r['mciw0_dl']:>11.4f}{r['mciw0_as']:>12.4f}{r['dmciw0']:>+9.4f}{ci:>20}{r['verdict']:>9}")
        out.append({"m": m, **{k: r[k] for k in ("mciw0_dl", "mciw0_as", "dmciw0", "ci", "verdict")}})
    json.dump({"sweep": out}, open(Path(__file__).resolve().parent / "msweep_result.json", "w"), indent=1)
    print("\n  (does the win hold at the sparsest, most realistic per-edge counts m=1,2?)")
    print("wrote msweep_result.json")


if __name__ == "__main__":
    main()
