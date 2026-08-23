#!/bin/bash
# Reproducible RunPod + Ollama setup for Monad GOS Monad (mirrors geister/pod_manager.py pattern).
#
# Usage:
#   ./runpod/setup.sh create    # create pod, pull model, print MONAD_OLLAMA_URL
#   ./runpod/setup.sh start     # resume existing pod
#   ./runpod/setup.sh stop      # stop pod (billing pauses on community spot)
#   ./runpod/setup.sh status    # show pod + URL
#   ./runpod/setup.sh verify    # curl /api/tags
#   ./runpod/setup.sh destroy   # terminate pod
#
# The Monad process auto-stops the pod after INACTIVITY_TIMEOUT_SECONDS of idle
# LLM use (default 3600s / 1h). Set INACTIVITY_TIMEOUT_SECONDS=0 to disable
# auto-stop while still allowing wake-on-demand.
#
# Environment (optional secrets file: runpod/monad-runpod.secrets.env):
#   RUNPOD_API_KEY              RunPod API key (required)
#   MONAD_NETWORK_VOLUME_ID     persistent volume for models (optional)
#   MONAD_OLLAMA_MODEL          default model to pull (default: llama3.2)
#   MIN_GPU_PRICE               min spot $/hr (default: 0.05)
#   MAX_GPU_PRICE               max spot $/hr (default: 0.25)
#   MONAD_RUNPOD_IMAGE          docker image (default: ollama/ollama:latest)
#
# Cloudflare tunnel (optional — do NOT auto-provision DNS):
#   Set CLOUDFLARED_CREDS_B64 + CLOUDFLARED_PEM_B64 on the pod env to enable tunnel.
#   See runpod/cloudflared/config.yml for suggested hostname monad-ollama.realmsgos.dev.
#   Then use MONAD_OLLAMA_URL=https://monad-ollama.realmsgos.dev instead of RunPod proxy.
#
# Cost notes:
#   Cheapest capable GPUs (community spot, Mar 2026): RTX A2000 ~$0.12/hr, RTX 3070 ~$0.13/hr.
#   llama3.2 (~3B) fits both; 8B-class models need ~8GB VRAM (3070/A4000 tier).
#   Script stops before create if estimated hourly rate exceeds MAX_GPU_PRICE.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONAD_DIR="$(dirname "$SCRIPT_DIR")"
SECRETS_FILE="${MONAD_RUNPOD_SECRETS:-$SCRIPT_DIR/monad-runpod.secrets.env}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'
log() { echo -e "${GREEN}[monad-runpod]${NC} $*"; }
warn() { echo -e "${YELLOW}[monad-runpod]${NC} $*"; }
err() { echo -e "${RED}[monad-runpod]${NC} $*" >&2; }

load_secrets() {
    if [[ -f "$SECRETS_FILE" ]]; then
        set -a
        # shellcheck disable=SC1090
        source "$SECRETS_FILE"
        set +a
        log "Loaded secrets from $SECRETS_FILE"
    fi
    if [[ -z "${RUNPOD_API_KEY:-}" ]]; then
        # Fallback: geister secrets on this VM (same RunPod account)
        local geister_secrets="/srv/dev/geister/vm/geister-api.secrets.env"
        if [[ -f "$geister_secrets" ]]; then
            set -a
            # shellcheck disable=SC1090
            source "$geister_secrets"
            set +a
            warn "Using RUNPOD_API_KEY from $geister_secrets"
        fi
    fi
    if [[ -z "${RUNPOD_API_KEY:-}" ]]; then
        err "RUNPOD_API_KEY is not set. Export it or create $SECRETS_FILE"
        exit 1
    fi
    export RUNPOD_API_KEY
}

fix_runpod_cli_config() {
  local cfg="${HOME}/.runpod/config.toml"
  if [[ ! -f "$cfg" ]] || grep -q 'api_key = "get"' "$cfg" 2>/dev/null; then
    mkdir -p "${HOME}/.runpod"
    cat > "$cfg" <<EOF
[default]
api_key = "${RUNPOD_API_KEY}"
EOF
    log "Updated RunPod CLI config at $cfg"
  fi
}

pod_python() {
    python3 "$MONAD_DIR/pod_manager.py" "$@"
}

verify_ollama() {
    local url="${1:-}"
    if [[ -z "$url" ]]; then
        local status_json
        status_json="$(pod_python status)"
        url="$(python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('url',''))" <<<"$status_json")"
    fi
    if [[ -z "$url" ]]; then
        err "No pod URL to verify"
        return 1
    fi
    log "Verifying Ollama at $url/api/tags ..."
    curl -sfS --max-time 30 "${url}/api/tags" | python3 -m json.tool
}

pull_model() {
    local url="$1"
    local model="${MONAD_OLLAMA_MODEL:-llama3.2}"
    log "Pulling model $model via $url ..."
    curl -sfS --max-time 600 -X POST "${url}/api/pull" \
        -d "{\"name\":\"${model}\"}" \
        -H 'Content-Type: application/json'
    echo
}

print_summary() {
    local json="$1"
    python3 - "$json" <<'PY'
import json, sys
d = json.loads(sys.argv[1])
url = d.get("url")
if not url and d.get("monad_env"):
    url = d["monad_env"].split("=", 1)[1]
print()
print("=" * 60)
print("Monad RunPod Ollama")
print("=" * 60)
if d.get("pod_id"):
    print(f"Pod ID:     {d.get('pod_id')}")
if d.get("name"):
    print(f"Pod name:   {d.get('name')}")
if d.get("status"):
    print(f"Status:     {d.get('status')}")
if d.get("gpu"):
    g = d["gpu"]
    if isinstance(g, dict):
        print(f"GPU:        {g.get('name')} (${g.get('price', '?')}/hr)")
    else:
        print(f"GPU:        {g}")
if d.get("model"):
    print(f"Model:      {d.get('model')}")
if d.get("hourly_cost_usd"):
    print(f"Est. cost:  ${d['hourly_cost_usd']:.3f}/hr while running")
if url:
    print(f"MONAD_OLLAMA_URL={url}")
    print(f"curl {url}/api/tags")
print("=" * 60)
print("Cloudflare (optional): see runpod/cloudflared/config.yml")
print("  Hostname: monad-ollama.realmsgos.dev → localhost:11434")
print("  Set CLOUDFLARED_CREDS_B64 on pod; then MONAD_OLLAMA_URL=https://monad-ollama.realmsgos.dev")
print("=" * 60)
PY
}

usage() {
    cat <<EOF
Usage: $0 {create|start|stop|status|verify|destroy|estimate}

  create   - Create pod (cheapest GPU in price band), wait for RUNNING
  start    - Resume stopped pod
  stop     - Stop pod to pause billing
  status   - Show pod status and MONAD_OLLAMA_URL
  verify   - curl /api/tags on running pod
  destroy  - Terminate pod
  estimate - Show cheapest GPUs in configured price band (no spend)

Environment: RUNPOD_API_KEY, MONAD_OLLAMA_MODEL (default llama3.2),
  MIN_GPU_PRICE (0.05), MAX_GPU_PRICE (0.25), MONAD_NETWORK_VOLUME_ID

Auto-stop: Monad stops the pod after INACTIVITY_TIMEOUT_SECONDS idle (default 3600).
  Set INACTIVITY_TIMEOUT_SECONDS=0 to disable auto-stop.
EOF
}

estimate_cost() {
    export RUNPOD_API_KEY
    python3 <<'PY'
import os, runpod
runpod.api_key = os.environ["RUNPOD_API_KEY"]
MIN_PRICE = float(os.environ.get("MIN_GPU_PRICE", "0.05"))
MAX_PRICE = float(os.environ.get("MAX_GPU_PRICE", "0.25"))
rows = []
for gpu in runpod.get_gpus():
    try:
        d = runpod.get_gpu(gpu["id"])
        p = d.get("communitySpotPrice") or d.get("secureSpotPrice")
        if p is not None and MIN_PRICE <= p <= MAX_PRICE:
            rows.append((p, d.get("displayName"), gpu["id"]))
    except Exception:
        pass
rows.sort(key=lambda r: r[0])
print(f"GPUs in ${MIN_PRICE}-${MAX_PRICE}/hr band ({len(rows)} found):")
for p, name, gid in rows[:15]:
    print(f"  ${p:.3f}/hr  {name}")
if rows:
    print(f"Cheapest: {rows[0][1]} at ${rows[0][0]:.3f}/hr")
PY
}

main() {
    local cmd="${1:-status}"
    load_secrets
    fix_runpod_cli_config

    case "$cmd" in
        create)
            log "Creating Monad Ollama pod (max ${MAX_GPU_PRICE:-0.25}/hr)..."
            local out
            out="$(pod_python create)"
            echo "$out"
            local result
            result="$(echo "$out" | tail -1)"
            print_summary "$result"
            local url status
            url="$(python3 -c "import json,sys; d=json.loads(sys.argv[1]); print(d.get('url',''))" "$result")"
            status="$(python3 -c "import json,sys; d=json.loads(sys.argv[1]); print(d.get('status', d.get('pod',{}).get('desiredStatus','')))" "$result")"
            if [[ -n "$url" ]] && [[ "$status" == "RUNNING" || "$(python3 -c "import json,sys; print(json.loads(sys.argv[1]).get('action',''))" "$result")" == "exists" ]]; then
                log "Waiting for Ollama HTTP..."
                for i in $(seq 1 60); do
                    if curl -sf --max-time 5 "${url}/api/tags" >/dev/null 2>&1; then
                        break
                    fi
                    sleep 5
                done
                local models
                models="$(curl -sf --max-time 10 "${url}/api/tags" | python3 -c "import json,sys; print(len(json.load(sys.stdin).get('models',[])))" 2>/dev/null || echo 0)"
                if [[ "${models:-0}" -eq 0 ]]; then
                    pull_model "$url" || warn "Model pull may still be in progress; check pod logs"
                fi
                verify_ollama "$url"
            else
                warn "Pod not RUNNING yet; run: $0 verify"
            fi
            ;;
        start)
            out="$(pod_python start)"
            echo "$out"
            print_summary "$(echo "$out" | tail -1)"
            ;;
        stop)
            pod_python stop
            ;;
        status)
            out="$(pod_python status)"
            echo "$out"
            print_summary "$out"
            ;;
        verify)
            verify_ollama
            ;;
        destroy)
            warn "Terminating Monad Ollama pod..."
            pod_python destroy
            ;;
        estimate)
            estimate_cost
            ;;
        help|-h|--help)
            usage
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

main "${1:-status}"
