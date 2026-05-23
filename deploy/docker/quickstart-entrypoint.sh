#!/bin/bash
set -euo pipefail

PROJECT_ROOT="/app/prism-insight"
CONFIG_DIR="${PROJECT_ROOT}/quickstart-config"
CONFIG_PATH="${CONFIG_DIR}/mcp_agent.config.yaml"
BUNDLED_CONFIG="${PROJECT_ROOT}/src/config/mcp_agent.config.yaml"

echo "========================================"
echo "  PRISM-INSIGHT Quick Start"
echo "========================================"

mkdir -p "${CONFIG_DIR}" \
         "${PROJECT_ROOT}/src/var/reports" \
         "${PROJECT_ROOT}/src/var/pdf_reports" \
         "${PROJECT_ROOT}/src/var/logs"

if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "[ERROR] OPENAI_API_KEY is required for quickstart."
    echo "[ERROR] Export OPENAI_API_KEY before running docker compose."
    exit 1
fi

if [ ! -f "${BUNDLED_CONFIG}" ]; then
    echo "[ERROR] Missing bundled ${BUNDLED_CONFIG} in image build."
    exit 1
fi

if [ ! -f "${CONFIG_PATH}" ]; then
    echo "[INIT] Seeding MCP config from repository defaults..."
    cp "${BUNDLED_CONFIG}" "${CONFIG_PATH}"
fi

# Legacy images / volumes may have shipped mcp_agent.secrets.yaml — keys now live only in `.env`/env.
rm -f "${PROJECT_ROOT}/mcp_agent.secrets.yaml"

echo "[INIT] Applying quickstart MCP config to repo root..."
cp "${CONFIG_PATH}" "${PROJECT_ROOT}/src/config/mcp_agent.config.yaml"

echo "[INIT] Quickstart config ready (LLM/API keys via OPENAI_* in compose environment and/or .env)"
echo "[INIT] Reports will be written to ./quickstart-output/"
echo "[INIT] Run a demo with:"
echo "       docker exec -it prism-quickstart python3 demo.py NVDA"
echo ""

exec "${PROJECT_ROOT}/deploy/docker/entrypoint.sh" "$@"
