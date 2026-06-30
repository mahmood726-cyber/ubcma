#!/usr/bin/env bash
# launch_codex_remote.sh -- stage grid CSVs + spec to a remote Windows node and run
# codex exec (seat A and/or B) to independently re-derive the grid MCIW0 + bootstrap.
#
# Usage: launch_codex_remote.sh <host> <user> <remote_workdir> <node_tag> <mode>
#   mode = sync   : run codex synchronously over SSH, capture stdout + result file
#          detach : launch codex detached (survives SSH drop), retrieve result later
# Seats are read from SEATS env (space-separated "tag:CODEX_HOME" pairs), e.g.
#   SEATS="A:C:\\Users\\mahmo\\.codex B:C:\\Users\\mahmo\\.codex-noreen"
#
# Requires: KEY env = path to ssh key; the gridcell_*_perrep.csv + grid_verify_spec.md
# present in nma/verify/grid (CSVs) and nma/verify (spec).
set -u
HOST="$1"; USER="$2"; WORKDIR="$3"; NODE="$4"; MODE="${5:-sync}"
KEY="${KEY:-C:/Users/mahmo/.ssh/node2_ed25519}"
SEATS="${SEATS:-A:C:\\Users\\mahmo\\.codex}"
MODEL="${MODEL:-gpt-5.5}"
GRID="F:/ubcma/nma/verify/grid"
SPEC="F:/ubcma/nma/verify/grid_verify_spec.md"
SSH="ssh -n -o ConnectTimeout=20 -o BatchMode=yes -o ServerAliveInterval=10 -o ServerAliveCountMax=6 -i $KEY"
SCP="scp -o ConnectTimeout=20 -o BatchMode=yes -i $KEY"
clean() { grep -ivE "WARNING|post-quantum|store now|may need|openssh.com|^\*\*"; }

echo "### node=$NODE host=$USER@$HOST workdir=$WORKDIR mode=$MODE seats=[$SEATS]"

# 1. ensure workdir (mkdir is harmless if it already exists; echo always runs)
$SSH "$USER@$HOST" "mkdir \"$WORKDIR\" 2>nul & echo MKDIR_OK" 2>&1 | clean | grep -i MKDIR_OK || { echo "UNREACHABLE"; exit 2; }

# 2. stage CSVs + spec
$SCP "$GRID"/gridcell_*_perrep.csv "$USER@$HOST:$WORKDIR/" 2>&1 | clean
$SCP "$SPEC" "$USER@$HOST:$WORKDIR/grid_verify_spec.md" 2>&1 | clean

# 3. per-seat prompt + launch
for pair in $SEATS; do
  TAG="${pair%%:*}"; HOME_C="${pair#*:}"
  PROMPT_LOCAL="/tmp/codex_grid_prompt_${NODE}_${TAG}.txt"
  sed "s/NODE = pc2/NODE = ${NODE}_${TAG}/" F:/ubcma/nma/verify/codex_grid_prompt.txt > "$PROMPT_LOCAL"
  $SCP "$PROMPT_LOCAL" "$USER@$HOST:$WORKDIR/prompt_${TAG}.txt" 2>&1 | clean
  RUN="cd /d \"$WORKDIR\" && set CODEX_HOME=$HOME_C && codex exec -m $MODEL --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox < prompt_${TAG}.txt"
  if [ "$MODE" = detach ]; then
    # detached: schtasks one-shot so it survives SSH drop; writes log + result file
    BAT="$WORKDIR\\run_${TAG}.bat"
    $SSH "$USER@$HOST" "(echo $RUN ^> codex_${NODE}_${TAG}.log 2^>^&1) > \"$BAT\" & echo BAT_OK" 2>&1 | clean | grep -i BAT_OK
    $SSH "$USER@$HOST" "schtasks /create /tn codex_${NODE}_${TAG} /tr \"$BAT\" /sc once /st 00:00 /f & schtasks /run /tn codex_${NODE}_${TAG} & echo LAUNCHED_${TAG}" 2>&1 | clean | grep -iE "LAUNCHED|ERROR"
  else
    echo "=== seat $TAG (sync) ==="
    $SSH "$USER@$HOST" "$RUN 2>&1" 2>&1 | clean | tail -25
    $SCP "$USER@$HOST:$WORKDIR/result_codex_${NODE}_${TAG}_grid.json" "F:/ubcma/nma/verify/result_codex_${NODE}_${TAG}_grid.json" 2>&1 | clean
  fi
done
echo "### done node=$NODE"
