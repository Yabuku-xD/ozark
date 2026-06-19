#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

export OZARK_PROJECT_ROOT="$(pwd)"

# ─── Color helpers ────────────────────────────────────
CREAM='\033[38;2;255;237;215m'
SIENNA='\033[38;2;220;80;0m'
GREY='\033[38;2;108;95;81m'
RESET='\033[0m'

echo ""
echo -e "${CREAM}  OZARK${RESET}${GREY}  ·  Agent Simulation Lab${RESET}"
echo -e "${GREY}  ─────────────────────────────────${RESET}"
echo ""

# ─── Dependencies ─────────────────────────────────────
if [[ ! -d node_modules ]]; then
    echo -e "${GREY}  Installing Node dependencies...${RESET}"
    npm install
fi

if ! python3 - <<'PY' >/dev/null 2>&1
import yaml
PY
then
    echo -e "${GREY}  Installing Python dependencies...${RESET}"
    python3 -m pip install -r requirements.txt
fi

# ─── Build dashboard ──────────────────────────────────
echo -e "${GREY}  Building dashboard...${RESET}"
(cd frontend && npm run build) 2>&1 | tail -1
echo ""

# ─── Port check ───────────────────────────────────────
PORT="${PORT:-8787}"
if lsof -i :"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo -e "${SIENNA}  ⚠${RESET}${GREY}  Port $PORT is already in use.${RESET}"
    echo -e "${GREY}  Kill the process or set a different PORT, then re-run.${RESET}"
    echo ""
    exit 1
fi

# ─── Start server ─────────────────────────────────────
echo -e "${GREY}  Starting server on port $PORT...${RESET}"
python3 -c "from backend.server import main; main()" &
SERVER_PID=$!

# Cleanup on exit (Ctrl+C, kill, etc.)
trap "kill $SERVER_PID 2>/dev/null; exit 0" INT TERM EXIT

# Wait for the server to come up.
for i in $(seq 1 30); do
    if ! kill -0 $SERVER_PID 2>/dev/null; then
        echo -e "${SIENNA}  ⚠${RESET}${GREY}  Server exited unexpectedly.${RESET}"
        exit 1
    fi
    if curl -sf "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

# ─── Open dashboard ───────────────────────────────────
if command -v python3 >/dev/null; then
    python3 -c "import webbrowser; webbrowser.open('http://127.0.0.1:$PORT/')" || true
fi
echo -e "${SIENNA}  ▶${RESET}${CREAM}  Dashboard ready at http://127.0.0.1:$PORT/${RESET}"
echo -e "${GREY}  Press Ctrl+C to stop.${RESET}"
echo ""

wait $SERVER_PID
