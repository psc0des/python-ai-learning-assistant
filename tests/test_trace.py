"""Tests for the execution visualizer trace backend and /api/trace endpoint."""

from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen

import app
from runner import trace_user_code, MAX_TRACE_STEPS


class TestTraceBackend:
    def test_loop_accumulator_progression(self):
        code = (
            "def total(items):\n"
            "    s = 0\n"
            "    for x in items:\n"
            "        s = s + x\n"
            "    return s\n"
            "result = total([10, 20])\n"
        )
        out = trace_user_code({"code": code})
        assert out["ok"] is True
        assert not out["error"]
        # the running total should pass through 0, 10, 30 across the steps
        s_values = [step["vars"]["s"] for step in out["steps"] if "s" in step["vars"]]
        assert 0 in s_values and 10 in s_values and 30 in s_values
        # final snapshot exposes the module-level result
        assert out["steps"][-1].get("final") is True
        assert out["steps"][-1]["vars"].get("result") == 30

    def test_runtime_error_is_captured_not_raised(self):
        out = trace_user_code({"code": "x = 1\ny = x + missing\n"})
        assert out["ok"] is False
        assert "NameError" in out["error"]
        assert out["steps"]  # partial trace still returned

    def test_blocked_import_is_rejected(self):
        out = trace_user_code({"code": "import os\nos.getcwd()\n"})
        assert out["ok"] is False
        assert "not allowed" in out["error"]
        assert out["steps"] == []

    def test_non_serializable_value_does_not_crash(self):
        # a set is not JSON-serializable; it must degrade to a safe repr string
        out = trace_user_code({"code": "s = {1, 2, 3}\nd = {'a': 1}\n"})
        assert out["ok"] is True
        final = out["steps"][-1]["vars"]
        assert isinstance(final["s"], str) and "1" in final["s"]
        assert final["d"] == {"a": 1}

    def test_step_cap_truncates_infinite_loop(self):
        out = trace_user_code({"code": "i = 0\nwhile True:\n    i = i + 1\n"})
        assert out["truncated"] is True
        # capped recorded line-steps plus one final snapshot
        assert len(out["steps"]) <= MAX_TRACE_STEPS + 1

    def test_stdout_is_captured(self):
        out = trace_user_code({"code": "print('hello')\nx = 5\n"})
        assert out["stdout"] == "hello\n"

    def test_oversized_code_rejected(self):
        out = trace_user_code({"code": "x = 1\n" * 10000})
        assert out["ok"] is False
        assert "too large" in out["error"].lower()


class TestTraceEndpoint:
    def _post(self, path, body):
        server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        host, port = server.server_address
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            req = Request(
                f"http://{host}:{port}{path}",
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(req, timeout=5) as response:
                return json.load(response)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_trace_endpoint_returns_steps(self):
        payload = self._post("/api/trace", {"code": "a = 1\nb = a + 2\n"})
        assert payload["ok"] is True
        assert payload["steps"]
        assert payload["steps"][-1]["vars"].get("b") == 3
