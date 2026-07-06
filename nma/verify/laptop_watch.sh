#!/usr/bin/env bash
# laptop_watch.sh -- wait (up to MAXMIN) for the flaky laptop node to surface, then
# run BOTH codex seats (A=.codex mahmood726, B=.codex-noreen) on the grid CSVs.
# Burns both laptop seats per Mahmood's directive; survives the node's flapping by
# polling. Logs everything; writes result_codex_laptop_{A,B}_grid.json on success.
set -u
# Portable default: honor a caller-supplied KEY, else resolve the ssh key under
# the invoking user's home (no hardcoded C:/Users/<name>/ path).
KEY="${KEY:-${HOME:-$USERPROFILE}/.ssh/node2_ed25519}"
HOST="100.80.183.43"; USER="mahmo"; WORKDIR="C:\\Users\\mahmo\\nma_verify"
MAXMIN="${MAXMIN:-45}"
PROBE="ssh -n -o ConnectTimeout=12 -o BatchMode=yes -o ServerAliveInterval=5 -i $KEY $USER@$HOST"
t_end=$(( $(date +%s) + MAXMIN*60 ))
n=0
while [ "$(date +%s)" -lt "$t_end" ]; do
  n=$((n+1))
  if $PROBE "echo UP" 2>/dev/null | grep -qi UP; then
    echo "[$(date +%H:%M:%S)] laptop UP on probe $n -- launching both seats"
    KEY="$KEY" MODEL="gpt-5.5" \
      SEATS="A:C:\\Users\\mahmo\\.codex B:C:\\Users\\mahmo\\.codex-noreen" \
      bash F:/ubcma/nma/verify/launch_codex_remote.sh "$HOST" "$USER" "$WORKDIR" laptop sync
    echo "[$(date +%H:%M:%S)] laptop run finished (rc=$?)"
    exit 0
  fi
  sleep 25
done
echo "[$(date +%H:%M:%S)] laptop never reachable within ${MAXMIN}m over $n probes -- giving up"
exit 3
