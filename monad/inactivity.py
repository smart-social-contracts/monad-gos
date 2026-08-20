"""RunPod GPU auto sleep/wake for Monad Ollama."""

from __future__ import annotations

import atexit
import logging
import os
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import requests

logger = logging.getLogger(__name__)

INACTIVITY_TIMEOUT_SECONDS = int(os.getenv("INACTIVITY_TIMEOUT_SECONDS", "3600"))
INACTIVITY_CHECK_INTERVAL_SECONDS = int(os.getenv("INACTIVITY_CHECK_INTERVAL_SECONDS", "60"))
OLLAMA_READY_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_READY_TIMEOUT_SECONDS", "300"))

DEFAULT_ACTIVITY_FILE = Path("/tmp/chora-monad-last-activity")
DEFAULT_REPLY_LOOP_PID_FILE = Path("/tmp/chora-monad-reply-loop.pid")

_process_start = time.time()
_ensure_ollama_lock = threading.Lock()
_in_flight_lock = threading.Lock()
_in_flight_count = 0
_inactivity_monitor_thread: threading.Thread | None = None
_shutdown_initiated = False


def _activity_file() -> Path:
    override = os.getenv("MONAD_ACTIVITY_FILE")
    return Path(override) if override else DEFAULT_ACTIVITY_FILE


def _reply_loop_pid_file() -> Path:
    override = os.getenv("MONAD_REPLY_LOOP_PID_FILE")
    return Path(override) if override else DEFAULT_REPLY_LOOP_PID_FILE


def update_activity() -> None:
    """Record user/LLM activity (not polling)."""
    now = time.time()
    path = _activity_file()
    path.write_text(str(now), encoding="utf-8")
    logger.debug("Activity updated at %s", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)))


def last_activity_time() -> float:
    path = _activity_file()
    if path.is_file():
        try:
            return float(path.read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            pass
    return _process_start


def is_ollama_ready(url: str) -> bool:
    try:
        resp = requests.get(f"{url.rstrip('/')}/api/tags", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def _in_flight_llm_count() -> int:
    with _in_flight_lock:
        return _in_flight_count


@contextmanager
def ollama_in_flight() -> Iterator[None]:
    global _in_flight_count
    with _in_flight_lock:
        _in_flight_count += 1
    try:
        yield
    finally:
        with _in_flight_lock:
            _in_flight_count -= 1


def ensure_ollama_ready(url: str) -> None:
    """Wake the RunPod GPU pod and wait until Ollama responds."""
    if is_ollama_ready(url):
        update_activity()
        start_inactivity_monitor()
        return

    from pod_manager import find_pod, start_pod

    with _ensure_ollama_lock:
        if is_ollama_ready(url):
            update_activity()
            start_inactivity_monitor()
            return

        logger.info("Ollama unreachable at %s; starting RunPod pod", url)
        if find_pod() is None:
            raise RuntimeError(
                "No monad-ollama RunPod pod found. Create one with: runpod/setup.sh create"
            )
        if not start_pod():
            raise RuntimeError(
                "Could not resume the monad-ollama RunPod pod; the original GPU host may be busy"
            )

        deadline = time.time() + OLLAMA_READY_TIMEOUT_SECONDS
        while time.time() < deadline:
            if is_ollama_ready(url):
                logger.info("Ollama is ready after pod start")
                update_activity()
                start_inactivity_monitor()
                return
            time.sleep(5)

        raise RuntimeError(
            "Ollama did not become ready within "
            f"{OLLAMA_READY_TIMEOUT_SECONDS}s after starting the RunPod pod"
        )


@contextmanager
def ollama_session(url: str) -> Iterator[None]:
    ensure_ollama_ready(url)
    with ollama_in_flight():
        yield
    update_activity()


def monitor_inactivity() -> None:
    while not _shutdown_initiated:
        try:
            time.sleep(INACTIVITY_CHECK_INTERVAL_SECONDS)
            if _shutdown_initiated:
                break

            inactive_duration = time.time() - last_activity_time()
            logger.debug(
                "Inactivity check: %.0fs since last activity (timeout: %ss)",
                inactive_duration,
                INACTIVITY_TIMEOUT_SECONDS,
            )

            if (
                INACTIVITY_TIMEOUT_SECONDS > 0
                and inactive_duration >= INACTIVITY_TIMEOUT_SECONDS
                and _in_flight_llm_count() == 0
            ):
                logger.info(
                    "Inactivity timeout reached (%.0fs); stopping RunPod pod",
                    inactive_duration,
                )
                try:
                    from pod_manager import stop_pod

                    if stop_pod():
                        logger.info("RunPod pod stopped due to inactivity")
                    else:
                        logger.warning("RunPod pod stop failed")
                except Exception:
                    logger.exception("Error stopping RunPod pod")

                update_activity()
        except Exception:
            logger.exception("Error in inactivity monitor")
            time.sleep(INACTIVITY_CHECK_INTERVAL_SECONDS)


def start_inactivity_monitor() -> None:
    global _inactivity_monitor_thread
    if INACTIVITY_TIMEOUT_SECONDS <= 0:
        logger.info("Inactivity timeout disabled (INACTIVITY_TIMEOUT_SECONDS=0)")
        return
    if _inactivity_monitor_thread is None or not _inactivity_monitor_thread.is_alive():
        logger.info(
            "Starting inactivity monitor (timeout: %ss)",
            INACTIVITY_TIMEOUT_SECONDS,
        )
        _inactivity_monitor_thread = threading.Thread(
            target=monitor_inactivity,
            daemon=True,
            name="monad-inactivity-monitor",
        )
        _inactivity_monitor_thread.start()
        atexit.register(_set_shutdown)


def _set_shutdown() -> None:
    global _shutdown_initiated
    _shutdown_initiated = True


def stop_inactivity_monitor() -> None:
    _set_shutdown()
    logger.info("Inactivity monitor stopped")


def mark_reply_loop_running() -> None:
    _reply_loop_pid_file().write_text(str(os.getpid()), encoding="utf-8")


def clear_reply_loop_running() -> None:
    path = _reply_loop_pid_file()
    if path.is_file():
        path.unlink(missing_ok=True)


def reply_loop_is_running() -> bool:
    path = _reply_loop_pid_file()
    if not path.is_file():
        return False
    try:
        pid = int(path.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def stop_pod_after_oneshot() -> None:
    if INACTIVITY_TIMEOUT_SECONDS <= 0:
        return
    if reply_loop_is_running():
        logger.info("Reply loop is running; leaving RunPod pod up")
        return
    logger.info("Stopping RunPod pod after one-shot deliberation")
    from pod_manager import stop_pod

    stop_pod()
