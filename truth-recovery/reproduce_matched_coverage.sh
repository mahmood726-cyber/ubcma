#!/usr/bin/env bash
# Reproduce the matched-coverage bake-off (AdaptShrink / UBCMA vs Henmi-Copas).
#
# Truth-first: every number below is produced from seeded simulation by
# matched_coverage_bakeoff.py and re-checked by its built-in truth-gate
# (finite-estimate guard + paired-bootstrap robustness of the MCIW0 advantage).
# No number is hand-entered.
#
# Runtime: ~3 s per replicate (dominated by the UBCMA multi-start fit and the
# Copas grid). 300 reps x 3 mechanisms ~= 45 min per strength on one core.
#
# Usage:
#   bash truth-recovery/reproduce_matched_coverage.sh            # both strengths, 300 reps
#   REPS=120 bash truth-recovery/reproduce_matched_coverage.sh   # quicker
set -euo pipefail
cd "$(dirname "$0")/.."

REPS="${REPS:-300}"
export PYTHONPATH=src

for strength in strong moderate; do
  echo "=== matched-coverage bake-off: ${strength}, ${REPS} reps ==="
  python truth-recovery/matched_coverage_bakeoff.py \
    --reps "${REPS}" --strength "${strength}" --target 0.95 \
    --out-prefix truth-recovery/mc | tee "truth-recovery/run_mc_${strength}.log"
done

echo
echo "Regression tests (fast, no re-sim):"
python -m pytest tests/test_adaptshrink.py truth-recovery/test_matched_coverage.py -q

echo
echo "Artifacts:"
echo "  truth-recovery/mc_<strength>_perrep.csv      (per-replicate mu_hat + CI)"
echo "  truth-recovery/mc_<strength>_table.csv       (MCIW0 / MCIW summary)"
echo "  truth-recovery/mc_<strength>_truthgate.json  (verified + bootstrap-robust wins)"
