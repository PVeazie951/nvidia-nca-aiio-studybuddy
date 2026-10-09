#!/usr/bin/env bash
# Stop the Study Buddy processes.
set -uo pipefail
cd "$(dirname "$0")"

for svc in backend frontend; do
  if [ -f "logs/$svc.pid" ]; then
    pid=$(cat "logs/$svc.pid")
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" && echo "stopped $svc (pid $pid)"
    else
      echo "$svc not running"
    fi
    rm -f "logs/$svc.pid"
  fi
done
