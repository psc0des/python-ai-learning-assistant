"""Tests for .env-backed AI provider persistence."""

import json
import os
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import app


ROOT = Path(__file__).resolve().parents[1]


def _temp_env_path(name: str) -> Path:
    temp_root = ROOT / ".runner_tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    # This environment can write but not delete files. Use deterministic,
    # gitignored paths and overwrite them on each run.
    return temp_root / name


def test_dotenv_loads_before_ai_coach_import():
    app_py = (ROOT / "app.py").read_text(encoding="utf-8")

    assert app_py.index("_load_dotenv(_ENV_PATH)") < app_py.index("from ai_coach import")


def test_load_dotenv_preserves_existing_shell_values(monkeypatch):
    env_file = _temp_env_path("env-load-test.env")
    env_file.write_text(
        "\n".join([
            "PY_SKILL_LAB_TEST_ONLY=file-value",
            "PY_SKILL_LAB_SHELL_WINS=file-value",
            "PY_SKILL_LAB_QUOTED='quoted value'",
        ]),
        encoding="utf-8",
    )
    monkeypatch.delenv("PY_SKILL_LAB_TEST_ONLY", raising=False)
    monkeypatch.setenv("PY_SKILL_LAB_SHELL_WINS", "shell-value")
    monkeypatch.delenv("PY_SKILL_LAB_QUOTED", raising=False)

    app._load_dotenv(env_file)

    assert os.environ["PY_SKILL_LAB_TEST_ONLY"] == "file-value"
    assert os.environ["PY_SKILL_LAB_SHELL_WINS"] == "shell-value"
    assert os.environ["PY_SKILL_LAB_QUOTED"] == "quoted value"


def test_update_dotenv_writes_key_and_updates_process_env(monkeypatch):
    env_file = _temp_env_path("env-update-test.env")
    env_file.write_text("# local config\nPY_SKILL_LAB_GROQ_KEY=old\n", encoding="utf-8")
    monkeypatch.setenv("PY_SKILL_LAB_GROQ_KEY", "old")

    app._update_dotenv(env_file, {"PY_SKILL_LAB_GROQ_KEY": "dummy-groq-key"})

    assert "PY_SKILL_LAB_GROQ_KEY=dummy-groq-key" in env_file.read_text(encoding="utf-8")
    assert os.environ["PY_SKILL_LAB_GROQ_KEY"] == "dummy-groq-key"


def test_save_ai_key_endpoint_writes_provider_env_key(monkeypatch):
    env_file = _temp_env_path("env-save-key-test.env")
    env_file.write_text("# local config\n", encoding="utf-8")
    monkeypatch.setattr(app, "_ENV_PATH", env_file)
    monkeypatch.setenv("PY_SKILL_LAB_GROQ_KEY", "")

    server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        req = urllib.request.Request(
            f"http://{host}:{port}/api/save-ai-key",
            data=json.dumps({"provider": "groq", "api_key": "dummy-groq-key"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            payload = json.load(response)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert payload == {"ok": True, "env_key": "PY_SKILL_LAB_GROQ_KEY"}
    assert "PY_SKILL_LAB_GROQ_KEY=dummy-groq-key" in env_file.read_text(encoding="utf-8")
    assert os.environ["PY_SKILL_LAB_GROQ_KEY"] == "dummy-groq-key"


def test_current_ai_settings_reports_saved_key_without_secret(monkeypatch):
    monkeypatch.setenv("PY_SKILL_LAB_AI_PROVIDER", "google")
    monkeypatch.setenv("PY_SKILL_LAB_AI_MODEL", "gemini-2.0-flash")
    monkeypatch.setenv("PY_SKILL_LAB_AI_ENDPOINT", "https://generativelanguage.googleapis.com/v1beta")
    monkeypatch.setenv("PY_SKILL_LAB_GOOGLE_KEY", "secret-google-key")

    settings = app._current_ai_settings()

    assert settings == {
        "ok": True,
        "provider": "google",
        "model": "gemini-2.0-flash",
        "endpoint": "https://generativelanguage.googleapis.com/v1beta",
        "key_present": True,
    }
    assert "secret-google-key" not in json.dumps(settings)


def test_ai_settings_endpoint_persists_provider_model_endpoint_and_key(monkeypatch):
    env_file = _temp_env_path("env-ai-settings-test.env")
    env_file.write_text("# local config\n", encoding="utf-8")
    monkeypatch.setattr(app, "_ENV_PATH", env_file)
    for key in (
        "PY_SKILL_LAB_AI_PROVIDER",
        "PY_SKILL_LAB_AI_MODEL",
        "PY_SKILL_LAB_AI_ENDPOINT",
        "PY_SKILL_LAB_GOOGLE_KEY",
    ):
        monkeypatch.delenv(key, raising=False)

    server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        body = {
            "provider": "google",
            "model": "gemini-2.0-flash",
            "endpoint": "https://generativelanguage.googleapis.com/v1beta",
            "api_key": "secret-google-key",
        }
        req = urllib.request.Request(
            f"http://{host}:{port}/api/ai-settings",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            saved = json.load(response)
        with urllib.request.urlopen(f"http://{host}:{port}/api/ai-settings", timeout=5) as response:
            loaded = json.load(response)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    env_text = env_file.read_text(encoding="utf-8")
    assert saved == {"ok": True, "env_key": "PY_SKILL_LAB_GOOGLE_KEY", "key_present": True}
    assert "PY_SKILL_LAB_AI_PROVIDER=google" in env_text
    assert "PY_SKILL_LAB_AI_MODEL=gemini-2.0-flash" in env_text
    assert "PY_SKILL_LAB_AI_ENDPOINT=https://generativelanguage.googleapis.com/v1beta" in env_text
    assert "PY_SKILL_LAB_GOOGLE_KEY=secret-google-key" in env_text
    assert loaded == {
        "ok": True,
        "provider": "google",
        "model": "gemini-2.0-flash",
        "endpoint": "https://generativelanguage.googleapis.com/v1beta",
        "key_present": True,
    }
    assert "secret-google-key" not in json.dumps(loaded)
