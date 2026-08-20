"""RunPod lifecycle for the Monad Ollama GPU pod."""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import runpod

logger = logging.getLogger(__name__)

POD_PREFIX = "monad-ollama-"
OLLAMA_PORT = 11434
RESUME_MAX_ATTEMPTS = int(os.getenv("POD_RESUME_MAX_ATTEMPTS", "6"))
RESUME_RETRY_DELAY_SECONDS = int(os.getenv("POD_RESUME_RETRY_DELAY_SECONDS", "30"))
ORIGINAL_HOST_GPU_UNAVAILABLE = "not enough free gpus on the host machine"

DEFAULT_MODEL = os.environ.get("MONAD_OLLAMA_MODEL", "llama3.2")
MIN_PRICE = float(os.environ.get("MIN_GPU_PRICE", "0.05"))
MAX_PRICE = float(os.environ.get("MAX_GPU_PRICE", "0.25"))
IMAGE = os.environ.get("MONAD_RUNPOD_IMAGE", "ollama/ollama:latest")
VOLUME_ID = os.environ.get("MONAD_NETWORK_VOLUME_ID") or os.environ.get("NETWORK_VOLUME_ID")
CONTAINER_DISK = int(os.environ.get("MONAD_CONTAINER_DISK_GB", "30"))


def _secrets_path() -> Path:
    override = os.environ.get("MONAD_RUNPOD_SECRETS")
    if override:
        return Path(override)
    return Path(__file__).resolve().parent / "runpod" / "monad-runpod.secrets.env"


def _load_env_file(path: Path, keys: set[str] | None = None) -> None:
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if keys is not None and key not in keys:
                continue
            os.environ.setdefault(key, value.strip())


def load_secrets() -> None:
    """Load RunPod secrets from env files without logging values."""
    _load_env_file(_secrets_path())
    if not os.environ.get("RUNPOD_API_KEY"):
        geister = Path("/srv/dev/geister/vm/geister-api.secrets.env")
        _load_env_file(geister, keys={"RUNPOD_API_KEY"})
    api_key = os.environ.get("RUNPOD_API_KEY")
    if not api_key:
        raise ValueError(
            "RUNPOD_API_KEY is not set. Export it or create "
            f"{_secrets_path()}"
        )
    runpod.api_key = api_key


def proxy_url(pod_id: str) -> str:
    return f"https://{pod_id}-{OLLAMA_PORT}.proxy.runpod.net"


def find_pod() -> dict[str, Any] | None:
    load_secrets()
    for pod in runpod.get_pods():
        name = pod.get("name", "")
        if name.startswith(POD_PREFIX):
            return pod
    return None


def _wait_status(pod_id: str, targets: set[str], timeout: int = 600) -> str:
    start = time.time()
    while time.time() - start < timeout:
        for pod in runpod.get_pods():
            if pod["id"] == pod_id:
                status = pod.get("desiredStatus", "UNKNOWN")
                if status in targets:
                    return status
                if status in {"Error", "FAILED"}:
                    return status
        time.sleep(5)
    return "TIMEOUT"


def _is_original_host_gpu_unavailable(error: Exception) -> bool:
    return ORIGINAL_HOST_GPU_UNAVAILABLE in str(error).lower()


def _pick_gpu() -> list[dict[str, Any]]:
    affordable: list[dict[str, Any]] = []
    for gpu in runpod.get_gpus():
        try:
            detail = runpod.get_gpu(gpu["id"])
        except Exception:
            continue
        community = detail.get("communitySpotPrice")
        secure = detail.get("secureSpotPrice")
        price = community if community is not None else secure
        if price is None or price < MIN_PRICE or price > MAX_PRICE:
            continue
        affordable.append(
            {
                "id": gpu["id"],
                "name": detail.get("displayName", gpu["id"]),
                "price": price,
            }
        )
    affordable.sort(key=lambda item: item["price"])
    return affordable


def create_pod() -> None:
    existing = find_pod()
    if existing:
        print(json.dumps({"action": "exists", "pod": existing, "url": proxy_url(existing["id"])}))
        return

    gpus = _pick_gpu()
    if not gpus:
        raise SystemExit(
            f"No GPUs found between ${MIN_PRICE}/hr and ${MAX_PRICE}/hr. "
            "Raise MAX_GPU_PRICE or wait for capacity."
        )

    cheapest = gpus[0]
    print(
        f"Selected GPU: {cheapest['name']} at ${cheapest['price']:.3f}/hr "
        f"(max allowed ${MAX_PRICE}/hr)"
    )

    pod_name = f"{POD_PREFIX}{int(time.time())}"
    env = {
        "OLLAMA_HOST": "0.0.0.0",
        "MONAD_OLLAMA_MODEL": DEFAULT_MODEL,
        "RUNPOD_POD_ID": "pending",
    }
    for key in ("CLOUDFLARED_CREDS_B64", "CLOUDFLARED_PEM_B64", "CLOUDFLARED_TUNNEL_NAME"):
        if os.environ.get(key):
            env[key] = os.environ[key]

    kwargs: dict[str, Any] = {
        "name": pod_name,
        "image_name": IMAGE,
        "gpu_type_id": cheapest["id"],
        "gpu_count": 1,
        "container_disk_in_gb": CONTAINER_DISK,
        "support_public_ip": True,
        "start_ssh": True,
        "ports": f"{OLLAMA_PORT}/http",
        "env": env,
    }
    if VOLUME_ID:
        kwargs["network_volume_id"] = VOLUME_ID
        kwargs["volume_mount_path"] = "/root/.ollama"

    result = None
    for attempt, gpu in enumerate(gpus[:8], start=1):
        kwargs["gpu_type_id"] = gpu["id"]
        try:
            print(f"Creating pod on {gpu['name']} (${gpu['price']:.3f}/hr), attempt {attempt}...")
            result = runpod.create_pod(**kwargs)
            cheapest = gpu
            break
        except Exception as exc:
            msg = str(exc).lower()
            print(f"GPU {gpu['name']} failed: {exc}")
            if "no longer any instances" in msg or "insufficient" in msg:
                continue
            raise
    if not result:
        raise SystemExit("All candidate GPUs failed. No pod created.")

    pod_id = result.get("id") if isinstance(result, dict) else str(result)
    status = _wait_status(pod_id, {"RUNNING"})
    print(
        json.dumps(
            {
                "action": "created",
                "pod_id": pod_id,
                "pod_name": pod_name,
                "gpu": cheapest,
                "status": status,
                "url": proxy_url(pod_id),
                "model": DEFAULT_MODEL,
                "hourly_cost_usd": cheapest["price"],
            }
        )
    )


def _resume_pod(pod_id: str) -> bool:
    for attempt in range(1, RESUME_MAX_ATTEMPTS + 1):
        logger.info("Resuming pod %s (attempt %s/%s)", pod_id, attempt, RESUME_MAX_ATTEMPTS)
        try:
            runpod.resume_pod(pod_id=pod_id, gpu_count=1)
            status = _wait_status(pod_id, {"RUNNING"})
            if status == "RUNNING":
                return True
            logger.warning("Pod %s did not reach RUNNING (status=%s)", pod_id, status)
        except Exception as exc:
            logger.warning("Resume failed for pod %s: %s", pod_id, exc)
            if _is_original_host_gpu_unavailable(exc):
                logger.warning("Original GPU host has no free GPUs")
                return False
        if attempt < RESUME_MAX_ATTEMPTS:
            logger.info("Retrying resume in %ss", RESUME_RETRY_DELAY_SECONDS)
            time.sleep(RESUME_RETRY_DELAY_SECONDS)
    return False


def start_pod() -> bool:
    """Resume an existing pod. Does not create a new pod."""
    load_secrets()
    pod = find_pod()
    if not pod:
        logger.warning("No monad-ollama pod found")
        return False
    pod_id = pod["id"]
    status = pod.get("desiredStatus", "UNKNOWN")
    if status == "RUNNING":
        return True
    return _resume_pod(pod_id)


def stop_pod() -> bool:
    """Stop the pod if running; no pod or already stopped counts as success."""
    load_secrets()
    pod = find_pod()
    if not pod:
        return True
    pod_id = pod["id"]
    status = pod.get("desiredStatus", "UNKNOWN")
    if status in {"EXITED", "STOPPED"}:
        return True
    try:
        runpod.stop_pod(pod_id)
    except Exception as exc:
        logger.error("Failed to stop pod %s: %s", pod_id, exc)
        return False
    final = _wait_status(pod_id, {"EXITED", "STOPPED"}, timeout=180)
    return final in {"EXITED", "STOPPED"}


def pod_status() -> dict[str, Any]:
    pod = find_pod()
    if not pod:
        return {"found": False}
    pod_id = pod["id"]
    return {
        "found": True,
        "pod_id": pod_id,
        "name": pod.get("name"),
        "status": pod.get("desiredStatus"),
        "gpu": pod.get("machine", {}).get("gpuDisplayName"),
        "url": proxy_url(pod_id),
        "monad_env": f"MONAD_OLLAMA_URL={proxy_url(pod_id)}",
        "model": DEFAULT_MODEL,
    }


def cli_start_pod() -> None:
    pod = find_pod()
    if not pod:
        raise SystemExit("No monad-ollama pod found. Run: setup.sh create")
    pod_id = pod["id"]
    status = pod.get("desiredStatus", "UNKNOWN")
    if status == "RUNNING":
        print(json.dumps({"action": "already_running", "pod_id": pod_id, "url": proxy_url(pod_id)}))
        return
    if not _resume_pod(pod_id):
        raise SystemExit(f"Failed to resume pod {pod_id}")
    status = _wait_status(pod_id, {"RUNNING"})
    print(json.dumps({"action": "started", "pod_id": pod_id, "status": status, "url": proxy_url(pod_id)}))


def cli_stop_pod() -> None:
    pod = find_pod()
    if not pod:
        print(json.dumps({"action": "none"}))
        return
    pod_id = pod["id"]
    stop_pod()
    status = _wait_status(pod_id, {"EXITED", "STOPPED"}, timeout=180)
    print(json.dumps({"action": "stopped", "pod_id": pod_id, "status": status}))


def cli_status_pod() -> None:
    print(json.dumps(pod_status()))


def destroy_pod() -> None:
    pod = find_pod()
    if not pod:
        print(json.dumps({"action": "none"}))
        return
    pod_id = pod["id"]
    runpod.terminate_pod(pod_id)
    print(json.dumps({"action": "terminated", "pod_id": pod_id}))


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1 or args[0] not in {"create", "start", "stop", "status", "destroy"}:
        print(
            "Usage: pod_manager.py {create|start|stop|status|destroy}",
            file=sys.stderr,
        )
        return 1
    try:
        load_secrets()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    action = args[0]
    try:
        if action == "create":
            create_pod()
        elif action == "start":
            cli_start_pod()
        elif action == "stop":
            cli_stop_pod()
        elif action == "status":
            cli_status_pod()
        elif action == "destroy":
            destroy_pod()
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
