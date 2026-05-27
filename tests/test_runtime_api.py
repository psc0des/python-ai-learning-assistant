"""Runtime API smoke tests against a live in-process HTTP server."""

from __future__ import annotations

import json
import threading
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
