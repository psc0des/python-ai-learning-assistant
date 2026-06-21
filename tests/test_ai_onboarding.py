"""Beginner-proof AI onboarding: actionable errors + first-run guidance.

A first-time learner has the default local provider (Ollama) selected but no
local model installed. Every "not configured" path must point them to the
no-install hosted route instead of a dead-end message.
"""

from pathlib import Path

import ai_coach

ROOT = Path(__file__).resolve().parents[1]


def test_no_local_model_hint_points_to_hosted_path():
    msg = ai_coach.NO_LOCAL_MODEL_HINT.format(label="Ollama")
    assert "Ollama" in msg
    assert "AI Settings" in msg
    assert "API key" in msg
    # Names at least one hosted provider so a beginner knows the alternative.
    assert any(p in msg for p in ("OpenAI", "Anthropic", "Google", "Groq"))


def test_unreachable_local_provider_error_offers_hosted_alternative():
    exc = OSError("[WinError 10061] No connection could be made (connection refused)")
    msg = ai_coach.friendly_provider_error("ollama", "http://127.0.0.1:11434", exc)
    assert "Could not reach Ollama" in msg
    assert "AI Settings" in msg
    assert "API key" in msg


def test_hosted_unreachable_error_is_unchanged_for_endpoint_advice():
    exc = OSError("connection refused")
    msg = ai_coach.friendly_provider_error("openai", "https://api.openai.com/v1/chat/completions", exc)
    assert "Check that the endpoint is correct" in msg


def test_ask_ai_coach_with_no_local_model_returns_actionable_error():
    result = ai_coach.ask_ai_coach(
        {"provider": "ollama", "model": "", "topic_id": "", "question": "hi"},
        topics=[],
        exercises=[],
    )
    assert result["ok"] is False
    assert "AI Settings" in result["error"]
    assert "API key" in result["error"]


def test_stream_ai_coach_with_no_local_model_returns_actionable_error():
    events = list(
        ai_coach.stream_ai_coach(
            {"provider": "ollama", "model": "", "topic_id": "", "question": "hi"},
            topics=[],
            exercises=[],
        )
    )
    done = [e for e in events if e.get("type") == "done"]
    assert done, "stream must end with a done event"
    assert done[-1]["ok"] is False
    assert "AI Settings" in done[-1]["error"]


def test_frontend_has_first_run_ai_onboarding():
    app_js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert "function isAiConfigured" in app_js
    assert "function maybeShowAiOnboarding" in app_js
    # One-time flag so the banner does not nag on every boot.
    assert "pySkillLabAiOnboarded" in app_js
    # Wired into AI settings init so it runs after saved settings are loaded.
    assert "maybeShowAiOnboarding();" in app_js
    assert "ai-onboard-nudge" in app_js


def test_frontend_boot_degrades_gracefully_on_load_failure():
    app_js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    boot_start = app_js.index("async function boot()")
    boot_end = app_js.index("function showBootError", boot_start)
    boot_body = app_js[boot_start:boot_end]
    assert "try {" in boot_body
    assert "showBootError(error)" in boot_body
    assert "function showBootError" in app_js
    assert "boot-error" in app_js
