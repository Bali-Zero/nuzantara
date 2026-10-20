#!/usr/bin/env bash
# Local Qdrant for the showroom (no Docker). Usage: scripts/qdrant_local.sh start|stop|status
# Official release binary, bound to 127.0.0.1 only, data under .showroom-data/ (git-ignored).
# Measured 14 Oct 2026: v1.19.2 x86_64-apple-darwin runs on an Ivy Bridge Mac (AVX, no AVX2).
set -euo pipefail
VERSION="1.19.2"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/.showroom-data"
BIN_DIR="$DATA/qdrant-$VERSION"
PIDFILE="$DATA/qdrant.pid"
PORT="${QDRANT_PORT:-6333}"

asset() {
  case "$(uname -s)-$(uname -m)" in
    Darwin-x86_64) echo "qdrant-x86_64-apple-darwin.tar.gz" ;;
    Darwin-arm64) echo "qdrant-aarch64-apple-darwin.tar.gz" ;;
    Linux-x86_64) echo "qdrant-x86_64-unknown-linux-gnu.tar.gz" ;;
    *) echo "unsupported platform $(uname -s)-$(uname -m)" >&2; return 1 ;;
  esac
}

running() { [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; }

case "${1:-}" in
  start)
    if running; then echo "qdrant already running (pid $(cat "$PIDFILE"))"; exit 0; fi
    mkdir -p "$BIN_DIR" "$DATA/qdrant-storage"
    if [ ! -x "$BIN_DIR/qdrant" ]; then
      A="$(asset)"
      curl -fsSL -o "$BIN_DIR/$A" "https://github.com/qdrant/qdrant/releases/download/v$VERSION/$A"
      tar -xzf "$BIN_DIR/$A" -C "$BIN_DIR"
    fi
    cd "$DATA"  # qdrant writes .qdrant-initialized into the working directory
    QDRANT__SERVICE__HOST=127.0.0.1 QDRANT__SERVICE__HTTP_PORT="$PORT" QDRANT__SERVICE__GRPC_PORT=$((PORT + 1)) \
    QDRANT__STORAGE__STORAGE_PATH="$DATA/qdrant-storage/storage" \
    QDRANT__STORAGE__SNAPSHOTS_PATH="$DATA/qdrant-storage/snapshots" \
    QDRANT__TELEMETRY_DISABLED=true \
      nohup "$BIN_DIR/qdrant" > "$DATA/qdrant.log" 2>&1 &
    echo $! > "$PIDFILE"
    for _ in $(seq 1 30); do
      curl -fs -m 1 "http://127.0.0.1:$PORT/readyz" >/dev/null 2>&1 && break
      sleep 1
    done
    running || { echo "qdrant exited; see $DATA/qdrant.log" >&2; exit 1; }
    [ -d "$DATA/qdrant-storage/storage/collections" ] || { echo "storage path not applied" >&2; exit 1; }
    echo "qdrant $(curl -fs "http://127.0.0.1:$PORT/" | sed -E 's/.*"version":"([^"]+)".*/\1/') on 127.0.0.1:$PORT (pid $(cat "$PIDFILE"))"
    ;;
  stop)
    if running; then kill "$(cat "$PIDFILE")"; rm -f "$PIDFILE"; echo "qdrant stopped"; else echo "qdrant not running"; fi
    ;;
  status)
    if running; then echo "running (pid $(cat "$PIDFILE"))"; else echo "not running"; exit 1; fi
    ;;
  *) echo "usage: $0 start|stop|status" >&2; exit 2 ;;
esac
