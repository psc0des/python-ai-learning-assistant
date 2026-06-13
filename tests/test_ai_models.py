"""Tests for AI model listing behavior."""

import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError

import ai_coach
import app


def test_ollama_model_listing_does_not_invent_fallbacks_when_down(monkeypatch):
    def raise_down(url, headers):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(ai_coach, "get_json", raise_down)

    result = ai_coach.list_ai_models({
        "provider": "ollama",
        "endpoint": "http://127.0.0.1:11435",
    })

    assert result["ok"] is False
    assert result["models"] == []
    assert "Could not reach Ollama" in result["error"]
    assert "Is it running?" in result["error"]


def test_ollama_model_listing_returns_only_installed_models(monkeypatch):
    def fake_tags(url, headers):
        return {
            "models": [
                {"name": "granite4.1:3b"},
                {"name": "qwen3.5:latest"},
            ]
        }

    monkeypatch.setattr(ai_coach, "get_json", fake_tags)

    result = ai_coach.list_ai_models({
        "provider": "ollama",
        "endpoint": "http://127.0.0.1:11434",
    })

    assert result == {
        "ok": True,
        "models": ["granite4.1:3b", "qwen3.5:latest"],
    }


def test_lmstudio_base_endpoint_lists_models_from_v1_models(monkeypatch):
    requested = {}

    def fake_models(url, headers):
        requested["url"] = url
        return {"data": [{"id": "local-model-a"}, {"id": "local-model-b"}]}

    monkeypatch.setattr(ai_coach, "get_json", fake_models)

    result = ai_coach.list_ai_models({
        "provider": "lmstudio",
        "endpoint": "http://127.0.0.1:1234",
    })

    assert requested["url"] == "http://127.0.0.1:1234/v1/models"
    assert result == {"ok": True, "models": ["local-model-a", "local-model-b"]}


def test_lmstudio_chat_endpoint_lists_models_from_v1_models(monkeypatch):
    requested = {}

    def fake_models(url, headers):
        requested["url"] = url
        return {"data": [{"id": "loaded-model"}]}

    monkeypatch.setattr(ai_coach, "get_json", fake_models)

    result = ai_coach.list_ai_models({
        "provider": "lmstudio",
        "endpoint": "http://127.0.0.1:1234/v1/chat/completions",
    })

    assert requested["url"] == "http://127.0.0.1:1234/v1/models"
    assert result == {"ok": True, "models": ["loaded-model"]}


def test_lmstudio_chat_uses_chat_completions_when_base_endpoint_is_configured(monkeypatch):
    requested = {}

    def fake_post(url, headers, payload):
        requested["url"] = url
        return {"choices": [{"message": {"content": "ok"}}], "usage": {}}

    monkeypatch.setattr(ai_coach, "post_json", fake_post)

    result = ai_coach.call_openai_compatible(
        ai_coach.openai_compatible_chat_url("http://127.0.0.1:1234", "http://127.0.0.1:1234"),
        "lm-studio",
        "loaded-model",
        "hello",
    )

    assert requested["url"] == "http://127.0.0.1:1234/v1/chat/completions"
    assert result["text"] == "ok"


def test_ollama_chat_requires_live_selected_model():
    result = ai_coach.ask_ai_coach(
        {
            "provider": "ollama",
            "model": "",
            "question": "hi",
            "mode": "chat",
        },
        topics=[],
        exercises=[],
    )

    assert result["ok"] is False
    assert "Choose an installed Ollama model" in result["error"]


def test_hosted_provider_no_key_returns_suggestions_only():
    for provider in ("openai", "anthropic", "google", "grok", "groq"):
        result = ai_coach.list_ai_models({"provider": provider, "api_key": ""})
        assert result["ok"] is False, f"{provider}: expected ok=False when no key"
        assert result.get("suggestions_only") is True, f"{provider}: expected suggestions_only=True"
        assert len(result["models"]) > 0, f"{provider}: expected non-empty fallback model list"
        assert "API key" in result["error"], f"{provider}: expected key-related error message"


def test_azure_foundry_no_key_returns_suggestions_only():
    result = ai_coach.list_ai_models({
        "provider": "azure-foundry",
        "api_key": "",
        "endpoint": "https://example.services.ai.azure.com/api/projects/proj/v1",
    })
    assert result["ok"] is False
    assert result.get("suggestions_only") is True
    assert result["models"] == []
    assert "API key" in result["error"]


def test_azure_foundry_model_listing_calls_v1_models(monkeypatch):
    requested = {}

    def fake_get(url, headers):
        requested["url"] = url
        requested["auth"] = headers.get("Authorization", "")
        return {"data": [{"id": "gpt-4o"}, {"id": "gpt-4o-mini"}]}

    monkeypatch.setattr(ai_coach, "get_json", fake_get)

    result = ai_coach.list_ai_models({
        "provider": "azure-foundry",
        "endpoint": "https://example.services.ai.azure.com/api/projects/proj/v1",
        "api_key": "test-key",
    })

    assert requested["url"] == "https://example.services.ai.azure.com/api/projects/proj/v1/models"
    assert requested["auth"] == "Bearer test-key"
    assert result == {"ok": True, "models": ["gpt-4o", "gpt-4o-mini"]}


def test_azure_foundry_model_listing_trailing_slash_endpoint(monkeypatch):
    requested = {}

    def fake_get(url, headers):
        requested["url"] = url
        return {"data": [{"id": "gpt-4o"}]}

    monkeypatch.setattr(ai_coach, "get_json", fake_get)

    ai_coach.list_ai_models({
        "provider": "azure-foundry",
        "endpoint": "https://example.services.ai.azure.com/api/projects/proj/v1/",
        "api_key": "test-key",
    })

    assert requested["url"] == "https://example.services.ai.azure.com/api/projects/proj/v1/models"


def test_azure_foundry_chat_uses_openai_compatible_path(monkeypatch):
    requested = {}

    def fake_post(url, headers, payload):
        requested["url"] = url
        return {"choices": [{"message": {"content": "hello"}}], "usage": {}}

    monkeypatch.setattr(ai_coach, "post_json", fake_post)

    result = ai_coach.ask_ai_coach(
        {
            "provider": "azure-foundry",
            "endpoint": "https://example.services.ai.azure.com/api/projects/proj/v1",
            "api_key": "test-key",
            "model": "gpt-4o",
            "question": "hi",
            "mode": "chat",
        },
        topics=[],
        exercises=[],
    )

    assert requested["url"] == "https://example.services.ai.azure.com/api/projects/proj/v1/chat/completions"
    assert result["ok"] is True
    assert result["answer"] == "hello"


def test_lmstudio_chat_requires_live_selected_model():
    result = ai_coach.ask_ai_coach(
        {
            "provider": "lmstudio",
            "model": "",
            "question": "hi",
            "mode": "chat",
        },
        topics=[],
        exercises=[],
    )

    assert result["ok"] is False
    assert "Choose a loaded LM Studio model" in result["error"]


def test_ai_models_endpoint_rate_limit_returns_429(monkeypatch):
    monkeypatch.setattr(app, "check_rate_limit", lambda _ip, **kw: False)
    server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        req = urllib.request.Request(
            f"http://{host}:{port}/api/ai-models",
            data=json.dumps({"provider": "ollama"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                payload = json.load(response)
                status = response.status
        except HTTPError as exc:
            status = exc.code
            payload = json.loads(exc.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert status == 429
    assert payload["ok"] is False
    assert payload["models"] == []
    assert "Rate limit exceeded" in payload["error"]
