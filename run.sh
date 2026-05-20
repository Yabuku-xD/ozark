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

# ─── macOS SwiftUI runner ─────────────────────────────
if [[ "$(uname)" == "Darwin" ]] && command -v swift &>/dev/null; then
    SWIFT_VERSION=$(swift --version 2>&1 | head -1)
    echo -e "${GREY}  Swift detected: ${CREAM}${SWIFT_VERSION}${RESET}"
    echo -e "${GREY}  Building native runner...${RESET}"
    echo ""

    cd runner

    if swift build -c release 2>&1 | while IFS= read -r line; do
        echo -e "${GREY}  │ ${line}${RESET}"
    done; then
        echo ""
        echo -e "${SIENNA}  ▶${RESET}${CREAM}  Launching Ozark Runner${RESET}"
        echo ""

        # Launch the compiled SwiftUI app
        .build/release/OzarkRunner &
        RUNNER_PID=$!

        # Wait for the runner to exit
        wait $RUNNER_PID 2>/dev/null || true
    else
        echo ""
        echo -e "${SIENNA}  ⚠${RESET}${GREY}  Swift build failed. Falling back to terminal mode...${RESET}"
        echo ""
        cd "$OZARK_PROJECT_ROOT"
        python3 -c "from backend.server import main; main()"
    fi

# ─── Fallback: terminal mode ─────────────────────────
else
    if [[ "$(uname)" == "Darwin" ]]; then
        echo -e "${GREY}  Swift not found. Install Xcode or Command Line Tools for the native UI.${RESET}"
    else
        echo -e "${GREY}  Non-macOS detected. Running in terminal mode.${RESET}"
    fi
    echo -e "${GREY}  Starting server...${RESET}"
    echo ""

    python3 -c "from backend.server import main; main()"
fi
