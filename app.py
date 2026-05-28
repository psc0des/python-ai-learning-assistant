"""Python Skill Lab — HTTP server.

A slim server that routes requests to the runner and AI coach modules.
All business logic lives in runner.py, ai_coach.py, and models.py.
"""

from __future__ import annotations

import collections
from datetime import datetime, timezone
import json
import logging
import os
import time
import threading
import webbrowser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ai_coach import ask_ai_coach, list_ai_models, narrate_trace
from content_loader import load_content
from models import validate_content_at_startup
from runner import run_user_code, trace_user_code

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent.resolve()
STATIC_DIR = ROOT / "static"
HOST = "127.0.0.1"
PORT = int(os.environ.get("PY_SKILL_LAB_PORT", os.environ.get("PY_INTERVIEW_PORT", "8765")))
STRICT_CONTENT_MODE = os.environ.get("PY_SKILL_LAB_STRICT_CONTENT", "0") == "1"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("skill_lab")


# ---------------------------------------------------------------------------
# Content loading
# ---------------------------------------------------------------------------

CONTENT = load_content()
TOPICS = CONTENT.topics
EXERCISES = CONTENT.exercises
PRACTICE_TESTS = CONTENT.practice_tests
CONTENT_LOADED_AT = datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Rate limiting (per-IP, for /api/run only)
# ---------------------------------------------------------------------------

RATE_LIMIT_WINDOW = 60   # seconds
RATE_LIMIT_MAX = 15      # max code-run requests per IP per window

_rate_lock = threading.Lock()
_rate_buckets: collections.defaultdict[str, list[float]] = collections.defaultdict(list)


def check_rate_limit(ip: str) -> bool:
    """Return True if the IP is within its rate limit, False if throttled."""
    now = time.monotonic()
    with _rate_lock:
        _rate_buckets[ip] = [
            t for t in _rate_buckets[ip] if now - t < RATE_LIMIT_WINDOW
        ]
        if len(_rate_buckets[ip]) >= RATE_LIMIT_MAX:
            return False
        _rate_buckets[ip].append(now)
        return True


# ---------------------------------------------------------------------------
# Concurrent request cap
# ---------------------------------------------------------------------------

MAX_CONCURRENT_REQUESTS = 20
_request_semaphore = threading.Semaphore(MAX_CONCURRENT_REQUESTS)


# ---------------------------------------------------------------------------
# Startup validation
# ---------------------------------------------------------------------------

def validate_on_startup() -> None:
    """Check content integrity at startup and log any warnings."""
    logger.info("Content mode: %s", CONTENT.mode)
    warnings = validate_content_at_startup(TOPICS, EXERCISES, PRACTICE_TESTS)
    for warning in warnings:
        logger.warning("Content: %s", warning)
    if warnings:
        logger.info("Found %d content warning(s). The app will still start.", len(warnings))
        if STRICT_CONTENT_MODE:
            raise RuntimeError(
                "Strict content mode is enabled and validation warnings were found. "
                "Fix content issues or disable PY_SKILL_LAB_STRICT_CONTENT."
            )
    else:
        logger.info("Content validation passed: %d topics, %d exercises, %d practice tests",
                     len(TOPICS), len(EXERCISES), len(PRACTICE_TESTS))


# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------


def _is_allowed_origin(origin: str, host: str, port: int) -> bool:
    """Return True only when origin exactly matches scheme+host+port."""
    if not origin:
        return True
    try:
        parsed = urlparse(origin)
        origin_port = parsed.port if parsed.port is not None else (80 if parsed.scheme == "http" else 443)
        return parsed.scheme == "http" and parsed.hostname == host and origin_port == port
    except Exception:
        return False


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def guess_type(self, path: Any) -> str:
        mtype = super().guess_type(path)
        # Ensure UTF-8 is declared for text-based assets so browsers never
        # fall back to a platform default (e.g. Windows-1252) and mangle
        # Unicode characters such as ✓ and ▶ in JS/CSS files.
        if isinstance(mtype, str) and mtype in (
            "application/javascript", "text/javascript", "text/css"
        ) and "charset" not in mtype:
            return mtype + "; charset=utf-8"
        return mtype

    def do_GET(self) -> None:
        if self.path == "/api/curriculum":
            self.send_json({
                "topics": TOPICS,
                "exercises": EXERCISES,
                "practice_tests": PRACTICE_TESTS,
                "content_mode": CONTENT.mode,
                "loaded_at": CONTENT_LOADED_AT,
            })
            return
        # Serve index.html explicitly with no-cache so JS/HTML never go out of sync
        if self.path in ("/", "/index.html") or self.path.startswith("/?"):
            content = (STATIC_DIR / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.end_headers()
            self.wfile.write(content)
            return
        super().do_GET()

    def do_POST(self) -> None:
        allowed_endpoints = {"/api/run", "/api/trace", "/api/narrate", "/api/ai-coach", "/api/ai-models"}
        if self.path not in allowed_endpoints:
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")
            return

        # Exact origin check — scheme, host, and port must all match
        origin = self.headers.get("Origin", "")
        if not _is_allowed_origin(origin, HOST, PORT):
            logger.warning("Blocked cross-origin POST from: %s", origin)
            self.send_json(
                {"ok": False, "error": "Cross-origin requests are not allowed."},
                status=403,
            )
            return

        # Rate limiting on the code-execution endpoints
        if self.path in ("/api/run", "/api/trace"):
            client_ip = self.client_address[0]
            if not check_rate_limit(client_ip):
                logger.warning("Rate limit exceeded for IP: %s", client_ip)
                self.send_json(
                    {
                        "ok": False,
                        "stdout": "",
                        "stderr": f"Rate limit exceeded: max {RATE_LIMIT_MAX} code runs per {RATE_LIMIT_WINDOW}s. Wait a moment.",
                        "tests": [],
                        "feedback": ["You're running code very fast. Take a moment to read your results before the next run."],
                    },
                    status=429,
                )
                return

        # Concurrent request cap
        if not _request_semaphore.acquire(blocking=False):
            logger.warning("Too many concurrent requests — rejecting.")
            self.send_json(
                {"ok": False, "error": "Server is busy. Please try again in a moment."},
                status=503,
            )
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")

            if self.path == "/api/run":
                result = run_user_code(payload, EXERCISES)
            elif self.path == "/api/trace":
                result = trace_user_code(payload)
            elif self.path == "/api/narrate":
                result = narrate_trace(payload)
            elif self.path == "/api/ai-models":
                result = list_ai_models(payload)
            else:
                result = ask_ai_coach(payload, TOPICS, EXERCISES)

            self.send_json(result)

        except json.JSONDecodeError:
            self.send_json(
                {"ok": False, "error": "Invalid JSON in request body."},
                status=400,
            )
        except Exception as exc:
            logger.exception("Request handler error on %s", self.path)
            self.send_json(
                {
                    "ok": False,
                    "stdout": "",
                    "stderr": repr(exc),
                    "tests": [],
                    "feedback": ["The app hit an internal error. Check the server console and try again."],
                },
                status=500,
            )
        finally:
            _request_semaphore.release()

    def send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        logger.debug("%s %s", self.address_string(), format % args)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    validate_on_startup()

    server = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}"
    logger.info("Python Skill Lab running at %s", url)
    logger.info("Press Ctrl+C to stop.")

    if os.environ.get("PY_SKILL_LAB_OPEN_BROWSER", os.environ.get("PY_INTERVIEW_OPEN_BROWSER", "1")) == "1":
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
