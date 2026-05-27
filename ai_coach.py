"""AI coach integration for Python Skill Lab.

Handles prompt construction and calls to multiple AI providers:
- Ollama (local)
- LM Studio (local, OpenAI-compatible)
- OpenAI (hosted)
- Anthropic (hosted)

API keys can be provided via environment variables (preferred) or client-side.
"""

from __future__ import annotations

import json
import logging
import os
import textwrap
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

AI_TIMEOUT_SECONDS = 90

# Environment variable names for server-side API keys (preferred over client-sent)
ENV_OPENAI_API_KEY = "PY_SKILL_LAB_OPENAI_KEY"
ENV_ANTHROPIC_API_KEY = "PY_SKILL_LAB_ANTHROPIC_KEY"


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def post_json(url: str, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    """POST JSON to a URL and parse the JSON response."""
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=AI_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"AI provider returned HTTP {exc.code}: {detail}") from exc


def get_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    """GET JSON from a URL and parse the response."""
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"AI provider returned HTTP {exc.code}: {detail}") from exc


# ---------------------------------------------------------------------------
# API key resolution
# ---------------------------------------------------------------------------

def resolve_api_key(provider: str, client_key: str) -> str:
    """Resolve the API key: prefer server-side env var, fall back to client-sent.

    This allows secure deployment where keys are set on the server,
    while still supporting the local single-user workflow where the
    learner enters their own key.
    """
    if provider == "openai":
        server_key = os.environ.get(ENV_OPENAI_API_KEY, "")
        if server_key:
            logger.debug("Using server-side OpenAI API key")
            return server_key
    elif provider == "anthropic":
        server_key = os.environ.get(ENV_ANTHROPIC_API_KEY, "")
        if server_key:
            logger.debug("Using server-side Anthropic API key")
            return server_key
    return client_key


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def build_ai_prompt(
    topic: dict[str, Any] | None,
    exercise: dict[str, Any] | None,
    code: str,
    run_result: dict[str, Any],
    question: str = "",
    chat_history: list[dict[str, Any]] | None = None,
) -> str:
    """Build a structured prompt for the AI coach.

    Organizes context into clear sections so the model can reason about
    the learner's specific situation.
    """
    topic_title = topic["title"] if topic else "Python learning practice"
    exercise_title = exercise["title"] if exercise else "free practice"
    exercise_prompt = exercise["prompt"] if exercise else "Review the learner's code."
    real_world = "\n".join(f"- {item}" for item in (topic or {}).get("real_world", []))

    lesson_sections = (topic or {}).get("lesson_sections", [])
    section_lines: list[str] = []
    source_lines: list[str] = []
    for idx, section in enumerate(lesson_sections[:6], start=1):
        section_title = str(section.get("title", f"Section {idx}")).strip()
        section_body = str(section.get("body", "")).strip().replace("\n", " ")
        if len(section_body) > 180:
            section_body = section_body[:180] + "... (truncated)"
        section_lines.append(f"- {section_title}: {section_body}")

        source_label = str(section.get("source_label", "")).strip()
        source_url = str(section.get("source_url", "")).strip()
        if source_url:
            source_lines.append(f"- {source_label or section_title}: {source_url}")

    for doc in (topic or {}).get("docs", [])[:6]:
        doc_label = str(doc.get("label", "Official docs")).strip()
        doc_url = str(doc.get("url", "")).strip()
        if doc_url:
            source_lines.append(f"- {doc_label}: {doc_url}")

    # Limit chat history to recent messages and truncate very long ones
    recent_history = (chat_history or [])[-6:]
    history_lines = []
    for message in recent_history:
        role = message.get("role", "user")
        text = message.get("text", "")
        # Truncate individual messages to prevent context overflow
        if len(text) > 500:
            text = text[:500] + "... (truncated)"
        history_lines.append(f"{role}: {text}")
    history = "\n".join(history_lines)

    # Truncate test result to prevent huge payloads
    run_result_str = json.dumps(run_result, indent=2)
    if len(run_result_str) > 2000:
        run_result_str = run_result_str[:2000] + "\n... (truncated)"

    # Truncate learner code if very long
    code_display = code
    if len(code_display) > 3000:
        code_display = code_display[:3000] + "\n# ... (truncated)"

    return textwrap.dedent(
        f"""
        You are a patient Python learning coach helping a beginner.
        Your role is to guide, not to give away answers.
        Keep responses practical, concise, and encouraging.
        Use simple language. Avoid jargon unless you explain it.

        === CONTEXT ===
        Topic: {topic_title}
        Exercise: {exercise_title}
        Task: {exercise_prompt}

        === LEARNER'S QUESTION ===
        {question or "Review the learner's current work."}

        === REAL-WORLD CONTEXT ===
        {real_world or "- No extra real-world context."}

        === LESSON SNAPSHOT (GROUND YOUR ANSWER HERE) ===
        {chr(10).join(section_lines) if section_lines else "- No lesson sections available."}

        === OFFICIAL SOURCES ===
        {chr(10).join(source_lines) if source_lines else "- No official sources listed."}

        === RECENT CONVERSATION ===
        {history or "- No previous conversation."}

        === TEST RESULTS ===
        {run_result_str}

        === LEARNER'S CODE ===
        ```python
        {code_display}
        ```

        === YOUR RESPONSE FORMAT ===
        1. Direct answer to the learner's question
        2. What their code currently gets right (be specific)
        3. What to fix or learn next (one thing at a time)
        4. A small hint or nudge - not the full answer unless code already passes
        5. If relevant, connect to a real-world scenario
        6. If you go beyond the lesson snapshot, say that explicitly
        """
    ).strip()

# ---------------------------------------------------------------------------
# Provider-specific callers
# ---------------------------------------------------------------------------

SYSTEM_MESSAGE = "You are a friendly Python learning coach. Help beginners build practical coding skills step by step."


def call_ollama(base_url: str, model: str, prompt: str,
                temperature: float = 0.2, top_p: float = 0.9, top_k: int = 40) -> str:
    """Call the Ollama local API."""
    url = base_url.rstrip("/") + "/api/chat"
    data = post_json(
        url,
        {"Content-Type": "application/json"},
        {
            "model": model,
            "stream": False,
            "messages": [
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": prompt},
            ],
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
            },
        },
    )
    return data.get("message", {}).get("content", "").strip() or "No response text returned."


def call_openai_compatible(url: str, api_key: str, model: str, prompt: str,
                           temperature: float = 0.2, top_p: float = 0.9) -> str:
    """Call an OpenAI-compatible API (OpenAI, LM Studio, etc.)."""
    data = post_json(
        url,
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "top_p": top_p,
        },
    )
    return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip() or "No response text returned."


def call_anthropic(url: str, api_key: str, model: str, prompt: str,
                   temperature: float = 0.2, top_p: float = 0.9) -> str:
    """Call the Anthropic Messages API."""
    data = post_json(
        url,
        {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        {
            "model": model,
            "max_tokens": 1500,
            "temperature": temperature,
            "top_p": top_p,
            "system": SYSTEM_MESSAGE,
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    chunks = data.get("content", [])
    return "\n".join(
        chunk.get("text", "") for chunk in chunks if chunk.get("type") == "text"
    ).strip() or "No response text returned."


# ---------------------------------------------------------------------------
# Main AI coach entry point
# ---------------------------------------------------------------------------

def ask_ai_coach(
    payload: dict[str, Any],
    topics: list[dict[str, Any]],
    exercises: list[dict[str, Any]],
) -> dict[str, Any]:
    """Process an AI coach request and return the response."""
    provider = str(payload.get("provider", "ollama")).lower()
    client_key = str(payload.get("api_key", ""))
    api_key = resolve_api_key(provider, client_key)
    model = str(payload.get("model", "")).strip()
    endpoint = str(payload.get("endpoint", "")).strip()
    code = str(payload.get("code", ""))
    topic_id = str(payload.get("topic_id", ""))
    exercise_id = str(payload.get("exercise_id", ""))
    run_result = payload.get("run_result", {})
    question = str(payload.get("question", "")).strip()
    chat_history = payload.get("chat_history", [])
    temperature = max(0.0, min(1.0, float(payload.get("temperature", 0.2))))
    top_p = max(0.0, min(1.0, float(payload.get("top_p", 0.9))))
    top_k = max(1, min(200, int(payload.get("top_k", 40))))

    topic = next((item for item in topics if item["id"] == topic_id), None)
    exercise = next((item for item in exercises if item["id"] == exercise_id), None)
    prompt = build_ai_prompt(topic, exercise, code, run_result, question, chat_history)

    try:
        if provider == "ollama":
            answer = call_ollama(endpoint or "http://127.0.0.1:11434", model or "qwen3.5:latest", prompt,
                                 temperature, top_p, top_k)
        elif provider == "lmstudio":
            answer = call_openai_compatible(
                endpoint or "http://127.0.0.1:1234/v1/chat/completions",
                api_key or "lm-studio",
                model or "local-model",
                prompt, temperature, top_p,
            )
        elif provider == "openai":
            if not api_key:
                raise ValueError("OpenAI API key is required. Set it in the UI or as PY_SKILL_LAB_OPENAI_KEY env var.")
            answer = call_openai_compatible(
                endpoint or "https://api.openai.com/v1/chat/completions",
                api_key,
                model or "gpt-4.1-mini",
                prompt, temperature, top_p,
            )
        elif provider == "anthropic":
            if not api_key:
                raise ValueError("Anthropic API key is required. Set it in the UI or as PY_SKILL_LAB_ANTHROPIC_KEY env var.")
            answer = call_anthropic(
                endpoint or "https://api.anthropic.com/v1/messages",
                api_key,
                model or "claude-3-5-haiku-latest",
                prompt, temperature, top_p,
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")

        logger.info("AI coach responded via %s/%s", provider, model)
        return {"ok": True, "answer": answer}

    except Exception as exc:
        logger.warning("AI coach failed (%s): %s", provider, exc)
        from runner import coach_feedback

        fallback = coach_feedback(
            code,
            str(run_result.get("stdout", "")),
            str(run_result.get("stderr", "")),
            run_result.get("tests", []),
            exercise,
        )
        return {
            "ok": False,
            "answer": "\n".join(f"- {item}" for item in fallback),
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# Model listing
# ---------------------------------------------------------------------------

def model_list_url(chat_endpoint: str) -> str:
    """Derive the models list URL from a chat completions endpoint."""
    if chat_endpoint.endswith("/chat/completions"):
        return chat_endpoint[: -len("/chat/completions")] + "/models"
    if chat_endpoint.endswith("/messages"):
        return chat_endpoint[: -len("/messages")] + "/models"
    return chat_endpoint.rstrip("/") + "/models"


def list_ai_models(payload: dict[str, Any]) -> dict[str, Any]:
    """List available models for a given AI provider."""
    provider = str(payload.get("provider", "ollama")).lower()
    endpoint = str(payload.get("endpoint", "")).strip()
    client_key = str(payload.get("api_key", ""))
    api_key = resolve_api_key(provider, client_key)

    fallback: dict[str, list[str]] = {
        "ollama": ["qwen3.5:latest", "nemotron-3-nano:4b"],
        "lmstudio": ["local-model"],
        "openai": ["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini"],
        "anthropic": ["claude-3-5-haiku-latest", "claude-3-5-sonnet-latest"],
    }

    try:
        if provider == "ollama":
            url = (endpoint or "http://127.0.0.1:11434").rstrip("/") + "/api/tags"
            data = get_json(url, {})
            models = [item["name"] for item in data.get("models", []) if item.get("name")]
        elif provider == "lmstudio":
            url = endpoint or "http://127.0.0.1:1234/v1/models"
            data = get_json(url, {"Authorization": f"Bearer {api_key or 'lm-studio'}"})
            models = [item["id"] for item in data.get("data", []) if item.get("id")]
        elif provider == "openai":
            if not api_key:
                models = fallback[provider]
            else:
                url = model_list_url(endpoint or "https://api.openai.com/v1/chat/completions")
                data = get_json(url, {"Authorization": f"Bearer {api_key}"})
                models = sorted(item["id"] for item in data.get("data", []) if item.get("id"))
        elif provider == "anthropic":
            if not api_key:
                models = fallback[provider]
            else:
                url = model_list_url(endpoint or "https://api.anthropic.com/v1/messages")
                data = get_json(
                    url,
                    {
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                    },
                )
                models = [item["id"] for item in data.get("data", []) if item.get("id")]
        else:
            raise ValueError(f"Unknown provider: {provider}")

        return {"ok": True, "models": models or fallback.get(provider, [])}
    except Exception as exc:
        logger.warning("Model listing failed (%s): %s", provider, exc)
        return {"ok": False, "models": fallback.get(provider, []), "error": str(exc)}

