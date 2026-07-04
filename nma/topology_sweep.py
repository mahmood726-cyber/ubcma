"""B x topology REGION MAP for AdaptShrink-NMA: at which selection strengths does the matched-coverage
win hold, per network topology? Deepens topology_stress.py (single strong B) into a small region map,
the topology analogue of the Phase-3 network-size sweep. Reuses topology_stress.run (same harness).
"""
import sys, io, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import topology_stress as ts  # noqa: E402
# NB: topology_stress already re-wraps sys.stdout on import; do NOT re-wrap (closes the buffer).

BS = [0.0, 0.25, 0.5, 1.0]
TOPOS = ["dense", "ladder", "star"]


def main():
    print("=" * 78)
    print("AdaptShrink-NMA: selection-strength x topology region map (dMCIW0 auto - common-DL)")
    print("  negative + CI<0 = robust matched-coverage win; reps=300/cell")
    print("=" * 78)
    header = "  {:10}".format("topology") + "".join(f"{'B='+str(b):>16}" for b in BS)
    print(header)
    grid = {}
    for topo in TOPOS:
        cells = []
        line = f"  {topo:10}"
        for B in BS:
            r = ts.run(topology=topo, B=B, reps=300, seed=3, boot=2000)
            tag = "WIN" if r["verdict"] == "WINS" else ("HARM" if r["verdict"] == "HARMS" else "tie")
            line += f"{r['dmciw0']:>+9.3f}[{tag:>4}]"
            cells.append({"B": B, **{k: r[k] for k in ("dmciw0", "ci", "verdict")}})
        print(line)
        grid[topo] = cells
    json.dump(grid, open(Path(__file__).resolve().parent / "topology_sweep_result.json", "w"), indent=1)
    print("\n  reading: expect ~tie at B=0 (inertia/safety) strengthening to robust WIN as selection grows,")
    print("  in every topology if topology is not a boundary of the win.")
    print("wrote topology_sweep_result.json")


if __name__ == "__main__":
    main()
