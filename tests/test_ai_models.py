"""Tests for AI model listing behavior."""

import urllib.error

import ai_coach


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
    assert "connection refused" in result["error"]


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
