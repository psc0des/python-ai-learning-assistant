"""Runtime API smoke tests against a live in-process HTTP server."""

from __future__ import annotations

import json
import threading
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
