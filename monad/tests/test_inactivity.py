"""Tests for RunPod auto sleep/wake."""

from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

MONAD_ROOT = Path(__file__).resolve().parents[1]
if str(MONAD_ROOT) not in sys.path:
    sys.path.insert(0, str(MONAD_ROOT))

import inactivity
from engine.ollama import OllamaEngine


class TestInactivity(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.activity_file = Path(self._tmpdir.name) / "activity"
        self.pid_file = Path(self._tmpdir.name) / "reply-loop.pid"
        os.environ["MONAD_ACTIVITY_FILE"] = str(self.activity_file)
        os.environ["MONAD_REPLY_LOOP_PID_FILE"] = str(self.pid_file)
        inactivity._shutdown_initiated = False
        inactivity._inactivity_monitor_thread = None
        with inactivity._in_flight_lock:
            inactivity._in_flight_count = 0
        inactivity._process_start = time.time()
        inactivity.INACTIVITY_TIMEOUT_SECONDS = 3600
        inactivity.INACTIVITY_CHECK_INTERVAL_SECONDS = 60
        inactivity.OLLAMA_READY_TIMEOUT_SECONDS = 300

    def tearDown(self) -> None:
        inactivity.stop_inactivity_monitor()
        self._tmpdir.cleanup()

    @mock.patch("inactivity.requests.get")
    def test_is_ollama_ready_true_false(self, mock_get: mock.Mock) -> None:
        mock_get.return_value = mock.Mock(status_code=200)
        self.assertTrue(inactivity.is_ollama_ready("https://example.test"))

        mock_get.side_effect = ConnectionError("down")
        self.assertFalse(inactivity.is_ollama_ready("https://example.test"))

    @mock.patch("inactivity.start_inactivity_monitor")
    @mock.patch("pod_manager.start_pod")
    @mock.patch("inactivity.is_ollama_ready", return_value=True)
    def test_ensure_skips_start_when_ready(
        self,
        _ready: mock.Mock,
        mock_start: mock.Mock,
        mock_monitor: mock.Mock,
    ) -> None:
        inactivity.ensure_ollama_ready("https://example.test")
        mock_start.assert_not_called()
        mock_monitor.assert_called_once()

    @mock.patch("inactivity.start_inactivity_monitor")
    @mock.patch("pod_manager.start_pod", return_value=True)
    @mock.patch("pod_manager.find_pod", return_value={"id": "pod1"})
    @mock.patch("inactivity.is_ollama_ready")
    def test_ensure_starts_pod_when_down(
        self,
        mock_ready: mock.Mock,
        _find: mock.Mock,
        mock_start: mock.Mock,
        mock_monitor: mock.Mock,
    ) -> None:
        mock_ready.side_effect = [False, False, True]
        inactivity.ensure_ollama_ready("https://example.test")
        mock_start.assert_called_once()
        mock_monitor.assert_called_once()

    @mock.patch("pod_manager.start_pod", return_value=False)
    @mock.patch("pod_manager.find_pod", return_value={"id": "pod1"})
    @mock.patch("inactivity.is_ollama_ready", return_value=False)
    def test_ensure_raises_when_start_fails(
        self,
        _ready: mock.Mock,
        _find: mock.Mock,
        _start: mock.Mock,
    ) -> None:
        with self.assertRaises(RuntimeError):
            inactivity.ensure_ollama_ready("https://example.test")

    @mock.patch("inactivity.start_inactivity_monitor")
    @mock.patch("pod_manager.start_pod", return_value=True)
    @mock.patch("pod_manager.find_pod", return_value={"id": "pod1"})
    @mock.patch("inactivity.is_ollama_ready", return_value=False)
    def test_ensure_raises_when_never_ready(
        self,
        _ready: mock.Mock,
        _find: mock.Mock,
        _start: mock.Mock,
        _monitor: mock.Mock,
    ) -> None:
        inactivity.OLLAMA_READY_TIMEOUT_SECONDS = 0
        with self.assertRaises(RuntimeError):
            inactivity.ensure_ollama_ready("https://example.test")

    @mock.patch("pod_manager.stop_pod")
    def test_monitor_stops_after_timeout(self, mock_stop: mock.Mock) -> None:
        inactivity.INACTIVITY_TIMEOUT_SECONDS = 0.05
        inactivity.INACTIVITY_CHECK_INTERVAL_SECONDS = 0.02
        inactivity._shutdown_initiated = False
        old = time.time() - 1.0
        self.activity_file.write_text(str(old), encoding="utf-8")

        thread = threading.Thread(target=inactivity.monitor_inactivity, daemon=True)
        thread.start()
        time.sleep(0.15)
        inactivity.stop_inactivity_monitor()
        thread.join(timeout=1.0)
        mock_stop.assert_called()

    @mock.patch("pod_manager.stop_pod")
    def test_monitor_disabled_when_timeout_zero(self, mock_stop: mock.Mock) -> None:
        inactivity.INACTIVITY_TIMEOUT_SECONDS = 0
        inactivity.INACTIVITY_CHECK_INTERVAL_SECONDS = 0.02
        inactivity._shutdown_initiated = False
        self.activity_file.write_text(str(time.time() - 999), encoding="utf-8")

        thread = threading.Thread(target=inactivity.monitor_inactivity, daemon=True)
        thread.start()
        time.sleep(0.08)
        inactivity.stop_inactivity_monitor()
        thread.join(timeout=1.0)
        mock_stop.assert_not_called()

    @mock.patch("pod_manager.stop_pod")
    def test_in_flight_prevents_stop(self, mock_stop: mock.Mock) -> None:
        inactivity.INACTIVITY_TIMEOUT_SECONDS = 0.05
        inactivity.INACTIVITY_CHECK_INTERVAL_SECONDS = 0.02
        inactivity._shutdown_initiated = False
        self.activity_file.write_text(str(time.time() - 1.0), encoding="utf-8")

        with inactivity.ollama_in_flight():
            thread = threading.Thread(target=inactivity.monitor_inactivity, daemon=True)
            thread.start()
            time.sleep(0.15)
            inactivity.stop_inactivity_monitor()
            thread.join(timeout=1.0)

        mock_stop.assert_not_called()

    def test_tick_does_not_update_activity(self) -> None:
        from reply_loop import tick

        class NeverEngine:
            def complete_text(self, prompt: str) -> str:
                raise AssertionError("tick should not call the engine when no reply needed")

        backend = mock.Mock()
        backend.principal = "monad-principal"
        backend.list_threads.return_value = [{"id": "thread-1"}]
        backend.read_thread.return_value = {
            "messages": [{"author": "monad-principal", "body": "already replied"}],
        }

        with mock.patch("inactivity.update_activity") as mock_update:
            tick(backend, NeverEngine(), set())
        mock_update.assert_not_called()

    @mock.patch("pod_manager.stop_pod")
    def test_stop_pod_after_oneshot_skips_when_reply_loop_alive(
        self,
        mock_stop: mock.Mock,
    ) -> None:
        inactivity.INACTIVITY_TIMEOUT_SECONDS = 60
        inactivity.mark_reply_loop_running()
        inactivity.stop_pod_after_oneshot()
        mock_stop.assert_not_called()

    @mock.patch("pod_manager.stop_pod")
    def test_stop_pod_after_oneshot_stops_when_no_reply_loop(
        self,
        mock_stop: mock.Mock,
    ) -> None:
        inactivity.INACTIVITY_TIMEOUT_SECONDS = 60
        inactivity.stop_pod_after_oneshot()
        mock_stop.assert_called_once()

    @mock.patch("inactivity.ollama_session", new_callable=mock.MagicMock)
    @mock.patch("engine.ollama.requests.post")
    def test_ollama_engine_generate_uses_session(
        self,
        mock_post: mock.Mock,
        mock_session: mock.Mock,
    ) -> None:
        mock_post.return_value = mock.Mock(
            raise_for_status=mock.Mock(),
            json=mock.Mock(return_value={"response": "ok"}),
        )

        engine = OllamaEngine(base_url="https://example.test")
        result = engine.complete("hello")
        self.assertEqual(result, "ok")
        mock_session.assert_called_once_with("https://example.test")


if __name__ == "__main__":
    unittest.main()
