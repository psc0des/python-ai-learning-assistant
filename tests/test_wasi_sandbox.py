"""Tests for the WASI/wasmtime sandbox — the real security boundary that
replaced the subprocess-only defense-in-depth model (see runner.py's module
docstring for the full security-model explanation).

These tests deliberately bypass scan_for_dangerous_code() and call
_run_via_wasi() directly with raw escape payloads that the original security
audit proved would break out of the old subprocess sandbox (gc/inspect
module-graph walks, frame-walking, direct os module access). The point is to
prove the WASM/WASI boundary itself holds structurally — independent of
whatever the AST allowlist catches — not just that the AST layer catches them
(that's covered by tests/test_security.py).
"""

from __future__ import annotations

import threading

import pytest

import runner
from runner import (
    _imports_asyncio,
    _run_via_wasi,
    _WasiTimeout,
    build_test_code,
    run_user_code,
    trace_user_code,
)


def _run_raw(code: str) -> tuple[str, str]:
    """Run `code` through the real test-harness wrapper, but via _run_via_wasi
    directly — bypassing scan_for_dangerous_code entirely."""
    test_code = build_test_code(code, [])
    return _run_via_wasi(test_code, runner.RUN_TIMEOUT_SECONDS)


class TestWasiIsRealBoundaryNotJustAstScan:
    """Every one of these payloads passes an empty scan_for_dangerous_code()
    result in principle (we don't even call the scanner) — proving the WASI
    sandbox itself, not pattern-matching, is what stops them."""

    def test_gc_walk_to_os_cannot_spawn_shell(self):
        code = (
            "import gc\n"
            "osmod = [o for o in gc.get_objects() if type(o).__name__=='module' and o.__name__=='os'][0]\n"
            "try:\n"
            "    osmod.system('echo pwned')\n"
            "    print('ESCAPED')\n"
            "except AttributeError as e:\n"
            "    print('BLOCKED:', e)\n"
        )
        stdout, stderr = _run_raw(code)
        assert "ESCAPED" not in stdout
        assert "BLOCKED" in stdout
        assert not stderr

    def test_os_module_has_no_filesystem_access(self):
        code = (
            "import gc\n"
            "osmod = [o for o in gc.get_objects() if type(o).__name__=='module' and o.__name__=='os'][0]\n"
            "try:\n"
            "    print(osmod.listdir('/'))\n"
            "    print('ESCAPED')\n"
            "except Exception as e:\n"
            "    print('BLOCKED:', repr(e))\n"
        )
        stdout, stderr = _run_raw(code)
        assert "ESCAPED" not in stdout
        assert "BLOCKED" in stdout

    def test_direct_open_has_no_accessible_filesystem(self):
        code = (
            "try:\n"
            "    open('C:/anywhere.txt', 'w').write('x')\n"
            "    print('WROTE FILE')\n"
            "except Exception as e:\n"
            "    print('BLOCKED:', repr(e))\n"
        )
        stdout, stderr = _run_raw(code)
        assert "WROTE FILE" not in stdout
        assert "BLOCKED" in stdout

    def test_socket_network_not_supported(self):
        code = (
            "import gc\n"
            "socketmods = [o for o in gc.get_objects() if type(o).__name__=='module' and o.__name__=='socket']\n"
            "print('socket module present:', bool(socketmods))\n"
        )
        stdout, stderr = _run_raw(code)
        assert "socket module present: False" in stdout

    def test_infinite_loop_is_interrupted_via_wasi_timeout(self):
        with pytest.raises(_WasiTimeout):
            _run_via_wasi(build_test_code("while True:\n    pass\n", []), timeout=1.0)


class TestAsyncioHybridRouting:
    """asyncio's event loop needs socket.socketpair(), which WASI doesn't
    support, so code that imports asyncio must be routed to the subprocess
    fallback instead of the WASI sandbox."""

    def test_imports_asyncio_detects_import_statement(self):
        assert _imports_asyncio("import asyncio\n") is True

    def test_imports_asyncio_detects_from_import(self):
        assert _imports_asyncio("from asyncio import sleep\n") is True

    def test_imports_asyncio_false_for_unrelated_code(self):
        assert _imports_asyncio("import json\ndef f():\n    return 1\n") is False

    def test_imports_asyncio_false_on_syntax_error(self):
        assert _imports_asyncio("def f(\n") is False

    def test_asyncio_lab_code_runs_via_subprocess_fallback(self):
        code = (
            "import asyncio\n"
            "async def main():\n"
            "    await asyncio.sleep(0.01)\n"
            "    return 42\n"
            "print(asyncio.run(main()))\n"
        )
        result = run_user_code({"code": code, "exercise_id": ""}, [])
        assert result["stdout"] == "42"
        assert result["stderr"] == ""

    def test_non_asyncio_code_runs_via_wasi(self):
        # No direct way to assert "which path ran" from the public API, but
        # this at minimum proves plain code still works end to end.
        result = run_user_code({"code": "print(2 + 2)", "exercise_id": ""}, [])
        assert result["stdout"] == "4"
        assert result["stderr"] == ""


class TestWasiConcurrency:
    """The compiled WASI Engine/Module are shared across requests; only the
    Store is per-execution. Confirms concurrent requests don't cross-
    contaminate or crash, matching ThreadingHTTPServer's concurrency model."""

    def test_concurrent_runs_do_not_interfere(self):
        results = {}
        lock = threading.Lock()

        def worker(n):
            r = run_user_code({"code": f"print({n} * 2)", "exercise_id": ""}, [])
            with lock:
                results[n] = r["stdout"]

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for n in range(8):
            assert results[n] == str(n * 2)


class TestWasiTraceVisualizer:
    """sys.settrace (the visualizer's mechanism) must work identically under
    WASI — this is the trace_user_code path, not run_user_code."""

    def test_trace_works_via_wasi(self):
        result = trace_user_code({"code": "x = 1\ny = 2\nz = x + y\n"})
        assert result["ok"] is True
        assert result["error"] == ""
        assert len(result["steps"]) >= 3

    def test_asyncio_trace_routes_to_subprocess_fallback(self):
        code = (
            "import asyncio\n"
            "async def main():\n"
            "    return 1\n"
            "asyncio.run(main())\n"
        )
        result = trace_user_code({"code": code})
        assert result["ok"] is True
