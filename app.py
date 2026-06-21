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

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent.resolve()
STATIC_DIR = ROOT / "static"
_ENV_PATH = ROOT / ".env"
HOST = "127.0.0.1"

# ---------------------------------------------------------------------------
# .env loader / updater (stdlib only, no python-dotenv needed)
# ---------------------------------------------------------------------------

def _load_dotenv(path: Path) -> None:
    """Load .env into os.environ at startup, skipping keys already set by the shell."""
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val


def _ensure_dotenv(path: Path) -> None:
    """Create .env from .env.example on first run so the file always exists for auto-writing."""
    if path.exists():
        return
    example = path.parent / ".env.example"
    if example.exists():
        path.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
        logger.info("Created .env from .env.example (first run)")
    else:
        path.write_text("# Python Skill Lab local configuration\n", encoding="utf-8")
        logger.info("Created empty .env (first run)")


def _update_dotenv(path: Path, updates: dict[str, str]) -> None:
    """Write or update key=value pairs in .env, then sync immediately into os.environ."""
    lines: list[str] = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    written: set[str] = set()
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.partition("=")[0].strip()
            if key in updates:
                out.append(f"{key}={updates[key]}")
                written.add(key)
                continue
        out.append(line)
    for key, val in updates.items():
        if key not in written:
            out.append(f"{key}={val}")
    text = "\n".join(out)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")
    for key, val in updates.items():
        if val:
            os.environ[key] = val
        elif key in os.environ:
            del os.environ[key]


_PROVIDER_ENV_KEY: dict[str, str] = {
    "openai":        "PY_SKILL_LAB_OPENAI_KEY",
    "anthropic":     "PY_SKILL_LAB_ANTHROPIC_KEY",
    "google":        "PY_SKILL_LAB_GOOGLE_KEY",
    "grok":          "PY_SKILL_LAB_GROK_KEY",
    "groq":          "PY_SKILL_LAB_GROQ_KEY",
    "azure-foundry": "PY_SKILL_LAB_AZURE_FOUNDRY_KEY",
}

_AI_SETTING_ENV_KEYS = {
    "provider": "PY_SKILL_LAB_AI_PROVIDER",
    "model": "PY_SKILL_LAB_AI_MODEL",
    "endpoint": "PY_SKILL_LAB_AI_ENDPOINT",
}


def _current_ai_settings() -> dict[str, Any]:
    """Return non-secret AI settings loaded from the process environment."""
    provider = os.environ.get(_AI_SETTING_ENV_KEYS["provider"], "").strip().lower()
    env_key = _PROVIDER_ENV_KEY.get(provider, "")
    return {
        "ok": True,
        "provider": provider,
        "model": os.environ.get(_AI_SETTING_ENV_KEYS["model"], "").strip(),
        "endpoint": os.environ.get(_AI_SETTING_ENV_KEYS["endpoint"], "").strip(),
        "key_present": bool(env_key and os.environ.get(env_key, "").strip()),
    }


def _save_ai_settings(payload: dict[str, Any], include_blank_key: bool = False) -> dict[str, Any]:
    """Persist non-secret provider settings and optionally the hosted provider key."""
    provider = str(payload.get("provider", "")).strip().lower()
    model = str(payload.get("model", "")).strip()
    endpoint = str(payload.get("endpoint", "")).strip()
    updates = {
        _AI_SETTING_ENV_KEYS["provider"]: provider,
        _AI_SETTING_ENV_KEYS["model"]: model,
        _AI_SETTING_ENV_KEYS["endpoint"]: endpoint,
    }

    env_key = _PROVIDER_ENV_KEY.get(provider)
    api_key = str(payload.get("api_key", "")).strip()
    if env_key and (api_key or include_blank_key):
        updates[env_key] = api_key

    _update_dotenv(_ENV_PATH, updates)
    logger.info("Saved AI settings for provider=%s model=%s endpoint=%s", provider, model, endpoint)
    return {
        "ok": True,
        "env_key": env_key or "",
        "key_present": bool(env_key and os.environ.get(env_key, "").strip()),
    }


_load_dotenv(_ENV_PATH)

from ai_coach import ask_ai_coach, list_ai_models, stream_ai_coach
from content_loader import load_content
from models import validate_content_at_startup
from runner import run_user_code, trace_user_code

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
# Rate limiting (per-IP, per-bucket)
# ---------------------------------------------------------------------------

RATE_LIMIT_WINDOW = 60        # seconds
RATE_LIMIT_MAX = 15           # max code-run requests per IP per window
AI_RATE_LIMIT_MAX = 10        # max AI coach requests per IP per window
AI_MODELS_RATE_LIMIT_MAX = 30 # max model-list requests per IP per window

_rate_lock = threading.Lock()
_rate_buckets: collections.defaultdict[str, list[float]] = collections.defaultdict(list)


def check_rate_limit(ip: str, bucket: str = "code", max_requests: int = RATE_LIMIT_MAX) -> bool:
    """Return True if the IP is within its rate limit for the given bucket, False if throttled."""
    key = f"{bucket}:{ip}"
    now = time.monotonic()
    with _rate_lock:
        _rate_buckets[key] = [
            t for t in _rate_buckets[key] if now - t < RATE_LIMIT_WINDOW
        ]
        if len(_rate_buckets[key]) >= max_requests:
            return False
        _rate_buckets[key].append(now)
        return True


# ---------------------------------------------------------------------------
# Concurrent request cap
# ---------------------------------------------------------------------------

MAX_CONCURRENT_REQUESTS = 20
_request_semaphore = threading.Semaphore(MAX_CONCURRENT_REQUESTS)

MAX_REQUEST_BODY_BYTES = 100_000  # 100 KB hard cap applied before JSON parsing


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
        return parsed.scheme == "http" and parsed.hostname in (host, "localhost") and origin_port == port
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
        request_path = urlparse(self.path).path
        if request_path == "/api/curriculum":
            self.send_json({
                "topics": TOPICS,
                "exercises": EXERCISES,
                "practice_tests": PRACTICE_TESTS,
                "content_mode": CONTENT.mode,
                "loaded_at": CONTENT_LOADED_AT,
            })
            return
        if request_path == "/api/ai-settings":
            self.send_json(_current_ai_settings())
            return
        # Serve index.html explicitly with no-cache so JS/HTML never go out of sync
        if request_path in ("/", "/index.html"):
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
        request_path = urlparse(self.path).path
        allowed_endpoints = {
            "/api/run",
            "/api/trace",
            "/api/ai-coach",
            "/api/ai-coach-stream",
            "/api/ai-models",
            "/api/save-ai-key",
            "/api/ai-settings",
        }
        if request_path not in allowed_endpoints:
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

        # Rate limiting on AI coach endpoint
        if request_path in {"/api/ai-coach", "/api/ai-coach-stream"}:
            client_ip = self.client_address[0]
            if not check_rate_limit(client_ip, bucket="ai", max_requests=AI_RATE_LIMIT_MAX):
                logger.warning("AI rate limit exceeded for IP: %s", client_ip)
                msg = f"Rate limit exceeded: max {AI_RATE_LIMIT_MAX} AI requests per {RATE_LIMIT_WINDOW}s. Wait a moment."
                self.send_json(
                    {"ok": False, "answer": msg, "error": msg, "reply": msg},
                    status=429,
                )
                return

        # Rate limiting on model-list endpoint (separate bucket — listing is cheaper than inference)
        if request_path == "/api/ai-models":
            client_ip = self.client_address[0]
            if not check_rate_limit(client_ip, bucket="models", max_requests=AI_MODELS_RATE_LIMIT_MAX):
                logger.warning("Model-list rate limit exceeded for IP: %s", client_ip)
                msg = f"Rate limit exceeded: max {AI_MODELS_RATE_LIMIT_MAX} model-list requests per {RATE_LIMIT_WINDOW}s. Wait a moment."
                self.send_json({"ok": False, "models": [], "error": msg}, status=429)
                return

        # Rate limiting on the code-execution endpoints
        if request_path in ("/api/run", "/api/trace"):
            client_ip = self.client_address[0]
            if not check_rate_limit(client_ip, bucket="code", max_requests=RATE_LIMIT_MAX):
                logger.warning("Rate limit exceeded for IP: %s", client_ip)
                message = (
                    f"Rate limit exceeded: max {RATE_LIMIT_MAX} code runs per "
                    f"{RATE_LIMIT_WINDOW}s. Wait a moment."
                )
                if request_path == "/api/trace":
                    self.send_json(
                        {
                            "ok": False,
                            "steps": [],
                            "stdout": "",
                            "truncated": False,
                            "error": message,
                            "error_line": 0,
                        },
                        status=429,
                    )
                else:
                    self.send_json(
                        {
                            "ok": False,
                            "stdout": "",
                            "stderr": message,
                            "tests": [],
                            "feedback": [
                                "You're running code very fast. Take a moment to read your results before the next run."
                            ],
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
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self.send_json({"ok": False, "error": "Invalid request."}, status=400)
                return
            if length > MAX_REQUEST_BODY_BYTES:
                self.send_json(
                    {"ok": False, "error": "Request body too large."},
                    status=413,
                )
                return
            payload = json.loads(self.rfile.read(length) or b"{}")

            if request_path == "/api/run":
                result = run_user_code(payload, EXERCISES)
            elif request_path == "/api/trace":
                result = trace_user_code(payload)
            elif request_path == "/api/ai-models":
                result = list_ai_models(payload)
            elif request_path == "/api/ai-coach-stream":
                self.send_ndjson_stream(stream_ai_coach(payload, TOPICS, EXERCISES))
                return
            elif request_path == "/api/ai-settings":
                result = _save_ai_settings(payload)
            elif request_path == "/api/save-ai-key":
                provider = str(payload.get("provider", "")).lower()
                api_key = str(payload.get("api_key", "")).strip()
                env_key = _PROVIDER_ENV_KEY.get(provider)
                if not env_key:
                    result = {"ok": False, "error": f"No env key mapping for provider '{provider}'."}
                else:
                    _update_dotenv(_ENV_PATH, {env_key: api_key})
                    logger.info("Saved %s to .env", env_key)
                    result = {"ok": True, "env_key": env_key}
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

    def send_ndjson_stream(self, events: Any, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        for event in events:
            line = json.dumps(event).encode("utf-8") + b"\n"
            try:
                self.wfile.write(line)
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                logger.info("Client disconnected from AI stream.")
                break

    def log_message(self, format: str, *args: Any) -> None:
        logger.debug("%s %s", self.address_string(), format % args)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    _ensure_dotenv(_ENV_PATH)
    _load_dotenv(_ENV_PATH)
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
