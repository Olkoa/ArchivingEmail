#!/usr/bin/env bash
set -uo pipefail

STREAMLIT_PORT="${STREAMLIT_SERVER_PORT:-8501}"
STREAMLIT_ADDR="${STREAMLIT_SERVER_ADDRESS:-0.0.0.0}"
RESTART_DELAY="${APP_RESTART_DELAY:-2}"

trap 'echo "Termination signal received. Shutting down."; exit 0' SIGTERM SIGINT

while true; do
    echo "Starting Streamlit on ${STREAMLIT_ADDR}:${STREAMLIT_PORT}..."
    streamlit run app/app.py \
        --server.port "${STREAMLIT_PORT}" \
        --server.address "${STREAMLIT_ADDR}"

    exit_code=$?
    if [[ ${exit_code} -eq 0 ]]; then
        echo "Streamlit exited cleanly. Stopping restart loop."
        break
    fi

    echo "Streamlit crashed with exit code ${exit_code}. Restarting in ${RESTART_DELAY}s..." >&2
    sleep "${RESTART_DELAY}"

done
