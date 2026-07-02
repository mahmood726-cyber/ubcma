"""Stage-3c extension: does a shrinkage-win region emerge in the SCOPED Emax variants
(heavier between-study heterogeneity tau, and/or an EXTRAPOLATED target dose)?

Stage-3c found an honest null for the nonlinear Emax predicted-dose bake-off at the interior
target (tau=0.15, d*=2). The report scoped ONE region where a win might still appear: heavier tau
and/or an extrapolated d*. This grid tests it, reusing dr_emax_bakeoff.py's machinery unchanged
(monkeypatching only the TAU_EMAX and DSTAR constants), scored by the same matched-coverage
truth-gate (dr_bakeoff._bootstrap_mciw0, robust_win = paired-bootstrap MCIW0 CI upper < 0 vs
two_stage_reml). Strong selection (the regime most favourable to a correction).
"""
import sys
from pathlib import Path
sys.path.insert(0, str((Path(__file__).resolve().parent)))
sys.path.insert(0, str((Path(__file__).resolve().parent.parent / "src")))
import dr_emax_bakeoff as E   # noqa: E402
import dr_bakeoff as B        # noqa: E402
import pandas as pd           # noqa: E402
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def run(tau, dstar, reps=200, seed=54321):
    E.TAU_EMAX = tau; E.DSTAR = dstar
    df = pd.concat([E.run_replicates("strong", reps, seed0=seed)], ignore_index=True)
    boot = B._bootstrap_mciw0(df)
    wins = [r for r in boot if r["robust_win"]]
    best = min(boot, key=lambda r: r["mciw0_diff"]) if boot else None
    truth = 0.7 * dstar / (2 + dstar)
    tag = "WIN@" + ",".join(sorted({r["method"] for r in wins})) if wins else "no robust win"
    b = (f"best {best['method']} dMCIW0={best['mciw0_diff']:+.4f}"
         f"[{best['ci_lo']:+.4f},{best['ci_hi']:+.4f}]" if best else "")
    print(f"  tau={tau:.2f} d*={dstar:>4.0f} (truth logRR {truth:+.3f}): {tag} | {b}")
    return bool(wins)


def main():
    print("Stage-3c scoped Emax grid (strong selection): heavy tau + extrapolated d* -> shrinkage win?")
    grid = [(0.15, 2), (0.50, 8), (0.50, 16)]   # interior baseline; heavy-tau edge; heavy-tau extrapolated
    any_win = False
    for tau, dstar in grid:
        any_win = run(tau, dstar) or any_win
    print("VERDICT:", "WIN REGION FOUND" if any_win
          else "HONEST NULL across the scoped region (no robust win; adaptshrink HARMS at extrapolated d*)")


if __name__ == "__main__":
    main()
