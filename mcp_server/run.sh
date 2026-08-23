#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/mcp_server/.venv"
PIDFILE="${MONAD_MCP_PIDFILE:-/tmp/monad-mcp.pid}"
LOG="${MONAD_MCP_LOG:-/tmp/monad-mcp.log}"
PYTHONPATH="$ROOT:$ROOT/mcp_tools"
export PYTHONPATH

usage() {
  cat <<EOF
Usage: $(basename "$0") {start|stop|status|logs|fg}

Environment:
  MONAD_MCP_PORT       (default 5002)
  MONAD_MCP_HOST       (default 127.0.0.1)
  MONAD_MCP_LOG        (default /tmp/monad-mcp.log)
  MONAD_MCP_PIDFILE    (default /tmp/monad-mcp.pid)
EOF
}

ensure_venv() {
  if [[ ! -x "$VENV/bin/python3" ]]; then
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install -q -r "$ROOT/mcp_server/requirements.txt"
  fi
}

is_running() {
  [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null
}

cmd="${1:-}"
case "$cmd" in
  start)
    ensure_venv
    if is_running; then
      echo "monad-mcp already running (pid $(cat "$PIDFILE"))"
      exit 0
    fi
    nohup "$VENV/bin/python3" -m mcp_server.server >>"$LOG" 2>&1 &
    echo $! >"$PIDFILE"
    echo "started monad-mcp pid $(cat "$PIDFILE") (log: $LOG)"
    ;;
  stop)
    if is_running; then
      kill "$(cat "$PIDFILE")" && rm -f "$PIDFILE"
      echo "stopped monad-mcp"
    else
      echo "monad-mcp is not running"
      rm -f "$PIDFILE"
    fi
    ;;
  status)
    if is_running; then
      echo "running pid $(cat "$PIDFILE")"
    else
      echo "not running"
      exit 1
    fi
    ;;
  logs)
    tail -f "$LOG"
    ;;
  fg)
    ensure_venv
    exec "$VENV/bin/python3" -m mcp_server.server
    ;;
  *)
    usage
    exit 1
    ;;
esac
