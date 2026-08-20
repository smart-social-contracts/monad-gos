#!/bin/bash
# Monad RunPod entrypoint: Ollama only (mirrors geister/run_ollama_only.sh)
set -euo pipefail
set -x

mkdir -p logs

OLLAMA_DATA="${OLLAMA_DATA:-/root/.ollama}"
export OLLAMA_HOST=0.0.0.0
export OLLAMA_MODELS="${OLLAMA_DATA}/models"
: "${OLLAMA_MODEL_LIST:=${MONAD_OLLAMA_MODEL:-llama3.2}}"

echo "OLLAMA_HOST=$OLLAMA_HOST"
echo "OLLAMA_MODELS=$OLLAMA_MODELS"
echo "OLLAMA_MODEL_LIST=$OLLAMA_MODEL_LIST"

# Optional Cloudflare tunnel (credentials injected at runtime)
if [[ -n "${CLOUDFLARED_CREDS_B64:-}" ]]; then
    mkdir -p /root/.cloudflared
    printf '%s' "$CLOUDFLARED_CREDS_B64" | base64 -d > /root/.cloudflared/credentials.json
    chmod 600 /root/.cloudflared/credentials.json
    if [[ -n "${CLOUDFLARED_PEM_B64:-}" ]]; then
        printf '%s' "$CLOUDFLARED_PEM_B64" | base64 -d > /root/.cloudflared/cert.pem
        chmod 600 /root/.cloudflared/cert.pem
    fi
    if [[ -f /app/cloudflared/config.yml ]]; then
        cloudflared tunnel --config /app/cloudflared/config.yml run "${CLOUDFLARED_TUNNEL_NAME:-realms-runpod}" \
            >> logs/cloudflared.log 2>&1 &
        echo "Cloudflare tunnel started (PID: $!)"
    else
        echo "WARNING: /app/cloudflared/config.yml missing; skipping tunnel"
    fi
fi

ollama serve 2>&1 | tee -a logs/ollama.log &

echo "Waiting for Ollama on port 11434..."
for i in $(seq 1 120); do
    if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
        break
    fi
    sleep 2
done

echo "Pulling models: $OLLAMA_MODEL_LIST"
for model in $OLLAMA_MODEL_LIST; do
    ollama pull "$model"
done

echo "=== Monad Ollama pod ready ==="
echo "RunPod proxy: https://${RUNPOD_POD_ID:-unknown}-11434.proxy.runpod.net"
sleep infinity
