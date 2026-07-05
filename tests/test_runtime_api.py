"""Runtime API smoke tests against a live in-process HTTP server."""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from urllib.request import urlopen

import app


def test_curriculum_endpoint_matches_runtime_content():
    server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        with urlopen(f"http://{host}:{port}/api/curriculum", timeout=5) as response:
            payload = json.load(response)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert payload["content_mode"] == app.CONTENT.mode
    assert payload["content_mode"] == "structured"
    assert payload.get("loaded_at")

    topic_ids_api = {topic["id"] for topic in payload["topics"]}
    topic_ids_runtime = {topic["id"] for topic in app.TOPICS}
    assert topic_ids_api == topic_ids_runtime
    assert len(payload["exercises"]) == len(app.EXERCISES)
    assert len(payload["practice_tests"]) == len(app.PRACTICE_TESTS)


def test_oversized_post_body_returns_413():
    server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        body = b"x" * (app.MAX_REQUEST_BODY_BYTES + 1)
        req = urllib.request.Request(
            f"http://{host}:{port}/api/run",
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(body)),
            },
        )
        try:
            urllib.request.urlopen(req, timeout=5)
            assert False, "Expected HTTPError 413"
        except urllib.error.HTTPError as exc:
            assert exc.code == 413
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_deeply_nested_json_returns_400_not_500():
    """Regression test for the LOW-MEDIUM finding: a ~40 KB body (well under
    the 100 KB cap) with ~20,000-deep array nesting raises RecursionError
    inside json.loads, which is not a json.JSONDecodeError/ValueError and
    used to fall through to the generic 500 handler, leaking an exception
    repr for trivially malformed input."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        # Build raw nested-array JSON syntax directly — wrapping it through
        # json.dumps() as a string value would just escape the brackets as
        # text and never trigger the parser's recursion at all.
        nested_array = "[" * 20000 + "]" * 20000
        body = ('{"code": "x", "exercise_id": ' + nested_array + '}').encode("utf-8")
        req = urllib.request.Request(
            f"http://{host}:{port}/api/run",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            urlopen(req, timeout=5)
            assert False, "Expected HTTPError 400"
        except urllib.error.HTTPError as exc:
            assert exc.code == 400
            payload = json.loads(exc.read())
            assert payload["ok"] is False
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_rate_limit_bucket_evicted_after_window_expires():
    """Regression test for the LOW finding: check_rate_limit pruned expired
    timestamps within a bucket but never removed the (now-empty) bucket key
    itself, so every distinct source IP left permanent dict entries for the
    life of the process."""
    ip = "203.0.113.99"  # TEST-NET-3, won't collide with a real caller
    bucket = "code"
    key = f"{bucket}:{ip}"
    app._rate_buckets.pop(key, None)

    assert app.check_rate_limit(ip, bucket=bucket, max_requests=5) is True
    assert key in app._rate_buckets

    # Simulate the window elapsing by back-dating the stored timestamp
    # instead of a real 60s sleep.
    with app._rate_lock:
        app._rate_buckets[key] = [time.monotonic() - app.RATE_LIMIT_WINDOW - 1]

    assert app.check_rate_limit(ip, bucket=bucket, max_requests=5) is True
    # The stale timestamp should have been pruned and a fresh one recorded —
    # exactly one entry, not an ever-growing list, and the key must not have
    # been left behind empty at any point.
    assert len(app._rate_buckets[key]) == 1

    app._rate_buckets.pop(key, None)
