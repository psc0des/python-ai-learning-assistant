"""AI coach integration for Python Skill Lab.

Handles prompt construction and calls to multiple AI providers:
- Ollama (local)
- LM Studio (local, OpenAI-compatible)
- OpenAI (hosted)
- Anthropic (hosted)
- Google AI Studio (hosted)
- Grok (xAI, hosted)
- Groq Cloud (hosted, OpenAI-compatible)
- Azure AI Foundry (hosted, OpenAI-compatible)

API keys can be provided via environment variables (preferred) or client-side.
"""

from __future__ import annotations

import json
import logging
import os
import textwrap
import time
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

AI_TIMEOUT_SECONDS = int(os.environ.get("PY_SKILL_LAB_AI_TIMEOUT_SECONDS", "45"))
AI_MODEL_LIST_TIMEOUT_SECONDS = int(os.environ.get("PY_SKILL_LAB_AI_MODELS_TIMEOUT_SECONDS", "8"))

# Environment variable names for server-side API keys (preferred over client-sent)
ENV_OPENAI_API_KEY = "PY_SKILL_LAB_OPENAI_KEY"
ENV_ANTHROPIC_API_KEY = "PY_SKILL_LAB_ANTHROPIC_KEY"
ENV_GOOGLE_API_KEY = "PY_SKILL_LAB_GOOGLE_KEY"
ENV_GROK_API_KEY = "PY_SKILL_LAB_GROK_KEY"
ENV_GROQ_API_KEY = "PY_SKILL_LAB_GROQ_KEY"
ENV_AZURE_FOUNDRY_API_KEY = "PY_SKILL_LAB_AZURE_FOUNDRY_KEY"

# Default/fallback model IDs age quickly. Used when a request omits a model
# and when a provider's live model list can't be fetched; the UI's live
# refresh result is always the source of truth.
FALLBACK_MODELS: dict[str, list[str]] = {
    "openai": ["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini"],
    "anthropic": ["claude-3-5-haiku-latest", "claude-3-5-sonnet-latest"],
    "google": ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash"],
    "grok": ["grok-3-mini", "grok-3", "grok-2-1212"],
    "groq": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"],
}


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
    except TimeoutError as exc:
        raise RuntimeError(f"timed out after {AI_TIMEOUT_SECONDS}s") from exc
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"AI provider returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", "")
        if isinstance(reason, TimeoutError):
            raise RuntimeError(f"timed out after {AI_TIMEOUT_SECONDS}s") from exc
        raise


def _post_stream_lines(url: str, headers: dict[str, str], payload: dict[str, Any]):
    """POST JSON and yield provider streaming response lines."""
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=AI_TIMEOUT_SECONDS) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if line:
                    yield line
    except TimeoutError as exc:
        raise RuntimeError(f"timed out after {AI_TIMEOUT_SECONDS}s") from exc
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"AI provider returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", "")
        if isinstance(reason, TimeoutError):
            raise RuntimeError(f"timed out after {AI_TIMEOUT_SECONDS}s") from exc
        raise


def get_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    """GET JSON from a URL and parse the response."""
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=AI_MODEL_LIST_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except TimeoutError as exc:
        raise RuntimeError(
            f"timed out after {AI_MODEL_LIST_TIMEOUT_SECONDS}s"
        ) from exc
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"AI provider returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", "")
        if isinstance(reason, TimeoutError):
            raise RuntimeError(
                f"timed out after {AI_MODEL_LIST_TIMEOUT_SECONDS}s"
            ) from exc
        raise


def friendly_provider_error(provider: str, endpoint: str, exc: Exception) -> str:
    """Convert low-level network errors into learner-readable setup guidance."""
    provider_label = {
        "ollama": "Ollama",
        "lmstudio": "LM Studio",
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "google": "Google AI Studio",
        "grok": "Grok",
        "groq": "Groq Cloud",
        "azure-foundry": "Azure AI Foundry",
    }.get(provider, provider or "AI provider")
    default_endpoint = {
        "ollama": "http://127.0.0.1:11434",
        "lmstudio": "http://127.0.0.1:1234",
    }.get(provider, endpoint)
    endpoint_text = endpoint or default_endpoint
    text = str(exc)
    lower = text.lower()

    if "timed out" in lower:
        warmup = ""
        if provider in {"ollama", "lmstudio"}:
            warmup = " Local models may need one warm-up request after launch; try once more after the model finishes loading."
        return f"{provider_label} did not respond before the timeout. Check that the provider is running and the endpoint is correct.{warmup}"
    if "connection refused" in lower or "winerror 10061" in lower:
        if provider in {"ollama", "lmstudio"}:
            return f"Could not reach {provider_label} at {endpoint_text}. Is it running?"
        return f"Could not reach {provider_label} at {endpoint_text}. Check that the endpoint is correct."
    return text


# ---------------------------------------------------------------------------
# API key resolution
# ---------------------------------------------------------------------------

_ENV_KEY_MAP = {
    "openai": ENV_OPENAI_API_KEY,
    "anthropic": ENV_ANTHROPIC_API_KEY,
    "google": ENV_GOOGLE_API_KEY,
    "grok": ENV_GROK_API_KEY,
    "groq": ENV_GROQ_API_KEY,
    "azure-foundry": ENV_AZURE_FOUNDRY_API_KEY,
}


def resolve_api_key(provider: str, client_key: str) -> str:
    """Resolve the API key: prefer server-side env var, fall back to client-sent."""
    env_var = _ENV_KEY_MAP.get(provider)
    if env_var:
        server_key = os.environ.get(env_var, "")
        if server_key:
            logger.debug("Using server-side API key for %s", provider)
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
    mode: str = "lab",
) -> str:
    """Build a structured prompt for the AI coach.

    mode='chat'  — learner typed a freeform question; answer only that, no exercise injection.
    mode='lab'   — triggered by a preset button; include exercise, code, and test context.
    """
    topic_title = topic["title"] if topic else "Python learning practice"

    lesson_sections = (topic or {}).get("lesson_sections", [])
    section_lines: list[str] = []
    for idx, section in enumerate(lesson_sections[:6], start=1):
        section_title = str(section.get("title", f"Section {idx}")).strip()
        section_body = str(section.get("body", "")).strip().replace("\n", " ")
        if len(section_body) > 180:
            section_body = section_body[:180] + "... (truncated)"
        section_lines.append(f"- {section_title}: {section_body}")

    recent_history = (chat_history or [])[-6:]
    history_lines = []
    for message in recent_history:
        role = message.get("role", "user")
        text = message.get("text", "")
        if len(text) > 500:
            text = text[:500] + "... (truncated)"
        history_lines.append(f"{role}: {text}")
    history = "\n".join(history_lines)

    if mode == "chat":
        return textwrap.dedent(
            f"""
            You are a patient Python learning coach helping a complete beginner.
            Answer the learner's question directly and concisely.
            If they show a code snippet, explain exactly what's right or wrong with it and show the correct version.
            Keep it plain, practical, and encouraging. Do NOT discuss the current exercise or lab unless they ask.

            === TOPIC CONTEXT ===
            Topic: {topic_title}

            === LESSON SNAPSHOT ===
            {chr(10).join(section_lines) if section_lines else "- No lesson sections available."}

            === RECENT CONVERSATION ===
            {history or "- No previous conversation."}

            === LEARNER'S QUESTION ===
            {question}
            """
        ).strip()

    # lab mode — full context with exercise, code, and test results
    exercise_title = exercise["title"] if exercise else "free practice"
    exercise_prompt = exercise["prompt"] if exercise else "Review the learner's code."
    real_world = "\n".join(f"- {item}" for item in (topic or {}).get("real_world", []))

    source_lines: list[str] = []
    for idx, section in enumerate(lesson_sections[:6], start=1):
        section_title = str(section.get("title", f"Section {idx}")).strip()
        source_label = str(section.get("source_label", "")).strip()
        source_url = str(section.get("source_url", "")).strip()
        if source_url:
            source_lines.append(f"- {source_label or section_title}: {source_url}")

    for doc in (topic or {}).get("docs", [])[:6]:
        doc_label = str(doc.get("label", "Official docs")).strip()
        doc_url = str(doc.get("url", "")).strip()
        if doc_url:
            source_lines.append(f"- {doc_label}: {doc_url}")

    run_result_str = json.dumps(run_result, indent=2)
    if len(run_result_str) > 2000:
        run_result_str = run_result_str[:2000] + "\n... (truncated)"

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


def _make_result(text: str, tokens_in: int, tokens_out: int,
                 elapsed_sec: float, gen_sec: float | None = None) -> dict[str, Any]:
    """Build a standardised call-result dict with usage stats."""
    divisor = gen_sec if (gen_sec and gen_sec > 0) else elapsed_sec
    tok_per_sec = round(tokens_out / divisor, 1) if divisor > 0 and tokens_out > 0 else 0.0
    return {
        "text": text,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "elapsed_sec": round(elapsed_sec, 1),
        "tok_per_sec": tok_per_sec,
    }


def call_ollama(base_url: str, model: str, prompt: str,
                temperature: float = 0.2, top_p: float = 0.9, top_k: int = 40) -> dict[str, Any]:
    """Call the Ollama local API."""
    url = base_url.rstrip("/") + "/api/chat"
    t0 = time.time()
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
    elapsed = time.time() - t0
    text = data.get("message", {}).get("content", "").strip() or "No response text returned."
    tokens_out = int(data.get("eval_count") or 0)
    tokens_in = int(data.get("prompt_eval_count") or 0)
    eval_ns = data.get("eval_duration") or 0
    gen_sec = eval_ns / 1e9 if eval_ns and tokens_out else None
    return _make_result(text, tokens_in, tokens_out, elapsed, gen_sec)


def stream_ollama(
    base_url: str,
    model: str,
    prompt: str,
    temperature: float = 0.2,
    top_p: float = 0.9,
    top_k: int = 40,
):
    """Yield standard stream events from the Ollama chat API."""
    url = base_url.rstrip("/") + "/api/chat"
    t0 = time.time()
    text_parts: list[str] = []
    tokens_in = 0
    tokens_out = 0
    gen_sec: float | None = None

    for line in _post_stream_lines(
        url,
        {"Content-Type": "application/json"},
        {
            "model": model,
            "stream": True,
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
    ):
        data = json.loads(line)
        chunk = data.get("message", {}).get("content", "")
        if chunk:
            text_parts.append(chunk)
            yield {"type": "chunk", "text": chunk}
        if data.get("done"):
            tokens_out = int(data.get("eval_count") or 0)
            tokens_in = int(data.get("prompt_eval_count") or 0)
            eval_ns = data.get("eval_duration") or 0
            gen_sec = eval_ns / 1e9 if eval_ns and tokens_out else None

    elapsed = time.time() - t0
    result = _make_result("".join(text_parts).strip(), tokens_in, tokens_out, elapsed, gen_sec)
    yield {"type": "done", "ok": True, **result}


def call_openai_compatible(url: str, api_key: str, model: str, prompt: str,
                           temperature: float = 0.2, top_p: float = 0.9) -> dict[str, Any]:
    """Call an OpenAI-compatible API (OpenAI, LM Studio, Grok, Groq, etc.)."""
    t0 = time.time()
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
    elapsed = time.time() - t0
    text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip() or "No response text returned."
    usage = data.get("usage") or {}
    tokens_in = int(usage.get("prompt_tokens") or 0)
    tokens_out = int(usage.get("completion_tokens") or 0)
    # Groq returns usage.completion_time (seconds) — more accurate than wall time
    groq_gen_sec = usage.get("completion_time")
    gen_sec = float(groq_gen_sec) if groq_gen_sec else None
    return _make_result(text, tokens_in, tokens_out, elapsed, gen_sec)


def stream_openai_compatible(
    url: str,
    api_key: str,
    model: str,
    prompt: str,
    temperature: float = 0.2,
    top_p: float = 0.9,
):
    """Yield standard stream events from an OpenAI-compatible chat endpoint."""
    t0 = time.time()
    text_parts: list[str] = []
    tokens_in = 0
    tokens_out = 0

    for line in _post_stream_lines(
        url,
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        {
            "model": model,
            "stream": True,
            "messages": [
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "top_p": top_p,
        },
    ):
        if not line.startswith("data:"):
            continue
        data_text = line[len("data:"):].strip()
        if data_text == "[DONE]":
            break
        data = json.loads(data_text)
        usage = data.get("usage") or {}
        if usage:
            tokens_in = int(usage.get("prompt_tokens") or tokens_in or 0)
            tokens_out = int(usage.get("completion_tokens") or tokens_out or 0)
        choices = data.get("choices") or []
        if choices:
            delta = choices[0].get("delta") or {}
            chunk = delta.get("content") or ""
            if chunk:
                text_parts.append(chunk)
                yield {"type": "chunk", "text": chunk}

    elapsed = time.time() - t0
    result = _make_result("".join(text_parts).strip(), tokens_in, tokens_out, elapsed)
    yield {"type": "done", "ok": True, **result}


def openai_compatible_chat_url(endpoint: str, default_base: str) -> str:
    """Normalize an OpenAI-compatible base URL to its chat completions URL."""
    base = (endpoint or default_base).rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return base + "/chat/completions"
    return base + "/v1/chat/completions"


def openai_compatible_models_url(endpoint: str, default_base: str) -> str:
    """Normalize an OpenAI-compatible base/chat URL to its model-list URL."""
    base = (endpoint or default_base).rstrip("/")
    if base.endswith("/models"):
        return base
    return model_list_url(openai_compatible_chat_url(endpoint, default_base))


def call_anthropic(url: str, api_key: str, model: str, prompt: str,
                   temperature: float = 0.2, top_p: float = 0.9) -> dict[str, Any]:
    """Call the Anthropic Messages API."""
    t0 = time.time()
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
    elapsed = time.time() - t0
    chunks = data.get("content", [])
    text = "\n".join(
        chunk.get("text", "") for chunk in chunks if chunk.get("type") == "text"
    ).strip() or "No response text returned."
    usage = data.get("usage") or {}
    tokens_in = int(usage.get("input_tokens") or 0)
    tokens_out = int(usage.get("output_tokens") or 0)
    return _make_result(text, tokens_in, tokens_out, elapsed)


def call_google(endpoint: str, api_key: str, model: str, prompt: str,
                temperature: float = 0.2, top_p: float = 0.9, top_k: int = 40) -> dict[str, Any]:
    """Call the Google AI Studio (Gemini) API."""
    base = (endpoint or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
    model_id = model.replace("models/", "")
    url = f"{base}/models/{model_id}:generateContent?key={api_key}"
    t0 = time.time()
    data = post_json(
        url,
        {"Content-Type": "application/json"},
        {
            "system_instruction": {"parts": [{"text": SYSTEM_MESSAGE}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "topP": top_p,
                "topK": top_k,
                "maxOutputTokens": 2048,
            },
        },
    )
    elapsed = time.time() - t0
    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts).strip() or "No response text returned."
    usage = data.get("usageMetadata") or {}
    tokens_in = int(usage.get("promptTokenCount") or 0)
    tokens_out = int(usage.get("candidatesTokenCount") or 0)
    return _make_result(text, tokens_in, tokens_out, elapsed)


# ---------------------------------------------------------------------------
# Main AI coach entry point
# ---------------------------------------------------------------------------

def _prepare_ai_request(
    payload: dict[str, Any],
    topics: list[dict[str, Any]],
    exercises: list[dict[str, Any]],
) -> dict[str, Any]:
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
    mode = str(payload.get("mode", "lab"))
    try:
        temperature = max(0.0, min(1.0, float(payload.get("temperature", 0.2))))
        top_p = max(0.0, min(1.0, float(payload.get("top_p", 0.9))))
        top_k = max(1, min(200, int(payload.get("top_k", 40))))
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Check your AI settings: temperature and top_p must be numbers between 0 and 1; "
            "top_k must be an integer."
        ) from exc

    topic = next((item for item in topics if item["id"] == topic_id), None)
    exercise = next((item for item in exercises if item["id"] == exercise_id), None)
    prompt = build_ai_prompt(topic, exercise, code, run_result, question, chat_history, mode)

    return {
        "provider": provider,
        "api_key": api_key,
        "model": model,
        "endpoint": endpoint,
        "code": code,
        "run_result": run_result,
        "exercise": exercise,
        "prompt": prompt,
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
    }


def _fallback_ai_result(request: dict[str, Any], exc: Exception) -> dict[str, Any]:
    from runner import coach_feedback

    fallback = coach_feedback(
        request["code"],
        str(request["run_result"].get("stdout", "")),
        str(request["run_result"].get("stderr", "")),
        request["run_result"].get("tests", []),
        request["exercise"],
    )
    return {
        "ok": False,
        "answer": "\n".join(f"- {item}" for item in fallback),
        "error": friendly_provider_error(request["provider"], request["endpoint"], exc),
    }


def ask_ai_coach(
    payload: dict[str, Any],
    topics: list[dict[str, Any]],
    exercises: list[dict[str, Any]],
) -> dict[str, Any]:
    """Process an AI coach request and return the response."""
    try:
        request = _prepare_ai_request(payload, topics, exercises)
    except Exception as exc:
        provider = str(payload.get("provider", "ollama")).lower()
        return {
            "ok": False,
            "answer": "- Check your AI settings and try again.",
            "error": friendly_provider_error(provider, str(payload.get("endpoint", "")), exc),
        }

    provider = request["provider"]
    api_key = request["api_key"]
    model = request["model"]
    endpoint = request["endpoint"]
    prompt = request["prompt"]
    temperature = request["temperature"]
    top_p = request["top_p"]
    top_k = request["top_k"]

    try:
        if provider == "ollama":
            if not model:
                raise ValueError("Choose an installed Ollama model from the live model dropdown.")
            call_result = call_ollama(endpoint or "http://127.0.0.1:11434", model, prompt,
                                      temperature, top_p, top_k)
        elif provider == "lmstudio":
            if not model:
                raise ValueError("Choose a loaded LM Studio model from the live model dropdown.")
            call_result = call_openai_compatible(
                openai_compatible_chat_url(endpoint, "http://127.0.0.1:1234"),
                api_key or "lm-studio",
                model,
                prompt, temperature, top_p,
            )
        elif provider == "openai":
            if not api_key:
                raise ValueError("OpenAI API key is required. Set it in the UI or as PY_SKILL_LAB_OPENAI_KEY env var.")
            call_result = call_openai_compatible(
                endpoint or "https://api.openai.com/v1/chat/completions",
                api_key,
                model or FALLBACK_MODELS["openai"][0],
                prompt, temperature, top_p,
            )
        elif provider == "anthropic":
            if not api_key:
                raise ValueError("Anthropic API key is required. Set it in the UI or as PY_SKILL_LAB_ANTHROPIC_KEY env var.")
            call_result = call_anthropic(
                endpoint or "https://api.anthropic.com/v1/messages",
                api_key,
                model or FALLBACK_MODELS["anthropic"][0],
                prompt, temperature, top_p,
            )
        elif provider == "google":
            if not api_key:
                raise ValueError("Google API key is required. Get one free at aistudio.google.com or set PY_SKILL_LAB_GOOGLE_KEY env var.")
            call_result = call_google(
                endpoint or "https://generativelanguage.googleapis.com/v1beta",
                api_key,
                model or FALLBACK_MODELS["google"][0],
                prompt, temperature, top_p, top_k,
            )
        elif provider == "grok":
            if not api_key:
                raise ValueError("Grok API key is required. Get one at console.x.ai or set PY_SKILL_LAB_GROK_KEY env var.")
            call_result = call_openai_compatible(
                endpoint or "https://api.x.ai/v1/chat/completions",
                api_key,
                model or FALLBACK_MODELS["grok"][0],
                prompt, temperature, top_p,
            )
        elif provider == "groq":
            if not api_key:
                raise ValueError("Groq API key is required. Get one free at console.groq.com or set PY_SKILL_LAB_GROQ_KEY env var.")
            call_result = call_openai_compatible(
                endpoint or "https://api.groq.com/openai/v1/chat/completions",
                api_key,
                model or FALLBACK_MODELS["groq"][0],
                prompt, temperature, top_p,
            )
        elif provider == "azure-foundry":
            if not api_key:
                raise ValueError("Azure AI Foundry API key is required. Enter it in AI Settings or set PY_SKILL_LAB_AZURE_FOUNDRY_KEY env var.")
            if not endpoint:
                raise ValueError("Azure AI Foundry endpoint is required. Enter your project URL in AI Settings.")
            call_result = call_openai_compatible(
                openai_compatible_chat_url(endpoint, endpoint),
                api_key,
                model or "",
                prompt, temperature, top_p,
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")

        logger.info("AI coach responded via %s/%s (%.1fs, %d out tokens)",
                    provider, model, call_result["elapsed_sec"], call_result["tokens_out"])
        return {
            "ok": True,
            "answer": call_result["text"],
            "tokens_in": call_result["tokens_in"],
            "tokens_out": call_result["tokens_out"],
            "elapsed_sec": call_result["elapsed_sec"],
            "tok_per_sec": call_result["tok_per_sec"],
        }

    except Exception as exc:
        logger.warning("AI coach failed (%s): %s", provider, exc)
        return _fallback_ai_result(request, exc)


def stream_ai_coach(
    payload: dict[str, Any],
    topics: list[dict[str, Any]],
    exercises: list[dict[str, Any]],
):
    """Yield standard NDJSON events for an AI coach request."""
    try:
        request = _prepare_ai_request(payload, topics, exercises)
    except Exception as exc:
        provider = str(payload.get("provider", "ollama")).lower()
        yield {
            "type": "done",
            "ok": False,
            "answer": "- Check your AI settings and try again.",
            "error": friendly_provider_error(provider, str(payload.get("endpoint", "")), exc),
        }
        return

    provider = request["provider"]
    api_key = request["api_key"]
    model = request["model"]
    endpoint = request["endpoint"]
    prompt = request["prompt"]
    temperature = request["temperature"]
    top_p = request["top_p"]
    top_k = request["top_k"]

    try:
        if provider == "ollama":
            if not model:
                raise ValueError("Choose an installed Ollama model from the live model dropdown.")
            yield from stream_ollama(endpoint or "http://127.0.0.1:11434", model, prompt,
                                     temperature, top_p, top_k)
        elif provider == "lmstudio":
            if not model:
                raise ValueError("Choose a loaded LM Studio model from the live model dropdown.")
            yield from stream_openai_compatible(
                openai_compatible_chat_url(endpoint, "http://127.0.0.1:1234"),
                api_key or "lm-studio",
                model,
                prompt, temperature, top_p,
            )
        elif provider in {"openai", "grok", "groq", "azure-foundry"}:
            if provider == "openai":
                if not api_key:
                    raise ValueError("OpenAI API key is required. Set it in the UI or as PY_SKILL_LAB_OPENAI_KEY env var.")
                url = endpoint or "https://api.openai.com/v1/chat/completions"
                selected_model = model or FALLBACK_MODELS["openai"][0]
            elif provider == "grok":
                if not api_key:
                    raise ValueError("Grok API key is required. Get one at console.x.ai or set PY_SKILL_LAB_GROK_KEY env var.")
                url = endpoint or "https://api.x.ai/v1/chat/completions"
                selected_model = model or FALLBACK_MODELS["grok"][0]
            elif provider == "groq":
                if not api_key:
                    raise ValueError("Groq API key is required. Get one free at console.groq.com or set PY_SKILL_LAB_GROQ_KEY env var.")
                url = endpoint or "https://api.groq.com/openai/v1/chat/completions"
                selected_model = model or FALLBACK_MODELS["groq"][0]
            else:
                if not api_key:
                    raise ValueError("Azure AI Foundry API key is required. Enter it in AI Settings or set PY_SKILL_LAB_AZURE_FOUNDRY_KEY env var.")
                if not endpoint:
                    raise ValueError("Azure AI Foundry endpoint is required. Enter your project URL in AI Settings.")
                url = openai_compatible_chat_url(endpoint, endpoint)
                selected_model = model or ""
            yield from stream_openai_compatible(url, api_key, selected_model, prompt, temperature, top_p)
        else:
            result = ask_ai_coach(payload, topics, exercises)
            if result.get("answer"):
                yield {"type": "chunk", "text": result["answer"]}
            yield {
                "type": "done",
                "ok": result.get("ok", False),
                "text": result.get("answer", ""),
                "tokens_in": result.get("tokens_in", 0),
                "tokens_out": result.get("tokens_out", 0),
                "elapsed_sec": result.get("elapsed_sec", 0),
                "tok_per_sec": result.get("tok_per_sec", 0),
                "error": result.get("error", ""),
            }
        logger.info("AI coach streamed via %s/%s", provider, model)
    except Exception as exc:
        logger.warning("AI coach stream failed (%s): %s", provider, exc)
        yield {"type": "done", **_fallback_ai_result(request, exc)}


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

    if provider in {"openai", "anthropic", "google", "grok", "groq", "azure-foundry"} and not api_key:
        return {
            "ok": False,
            "models": FALLBACK_MODELS.get(provider, []),
            "suggestions_only": True,
            "error": "No API key configured — showing suggested models only.",
        }

    try:
        if provider == "ollama":
            url = (endpoint or "http://127.0.0.1:11434").rstrip("/") + "/api/tags"
            data = get_json(url, {})
            models = [item["name"] for item in data.get("models", []) if item.get("name")]
        elif provider == "lmstudio":
            url = openai_compatible_models_url(endpoint, "http://127.0.0.1:1234")
            data = get_json(url, {"Authorization": f"Bearer {api_key or 'lm-studio'}"})
            models = [item["id"] for item in data.get("data", []) if item.get("id")]
        elif provider == "openai":
            url = model_list_url(endpoint or "https://api.openai.com/v1/chat/completions")
            data = get_json(url, {"Authorization": f"Bearer {api_key}"})
            models = sorted(item["id"] for item in data.get("data", []) if item.get("id"))
        elif provider == "anthropic":
            url = model_list_url(endpoint or "https://api.anthropic.com/v1/messages")
            data = get_json(url, {"x-api-key": api_key, "anthropic-version": "2023-06-01"})
            models = [item["id"] for item in data.get("data", []) if item.get("id")]
        elif provider in ("grok", "groq"):
            default_endpoint = (
                "https://api.x.ai/v1/chat/completions" if provider == "grok"
                else "https://api.groq.com/openai/v1/chat/completions"
            )
            url = model_list_url(endpoint or default_endpoint)
            data = get_json(url, {"Authorization": f"Bearer {api_key}"})
            models = sorted(item["id"] for item in data.get("data", []) if item.get("id"))
        elif provider == "google":
            base = (endpoint or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
            data = get_json(f"{base}/models?key={api_key}", {})
            models = [
                item["name"].replace("models/", "")
                for item in data.get("models", [])
                if item.get("name", "").startswith("models/gemini")
                and "generateContent" in item.get("supportedGenerationMethods", [])
            ]
        elif provider == "azure-foundry":
            if not endpoint:
                raise ValueError("Azure AI Foundry endpoint is required (e.g. https://….services.ai.azure.com/…/v1)")
            url = openai_compatible_models_url(endpoint, endpoint)
            data = get_json(url, {"Authorization": f"Bearer {api_key}"})
            models = [item["id"] for item in data.get("data", []) if item.get("id")]
        else:
            raise ValueError(f"Unknown provider: {provider}")

        return {"ok": True, "models": models or FALLBACK_MODELS.get(provider, [])}
    except Exception as exc:
        logger.warning("Model listing failed (%s): %s", provider, exc)
        return {
            "ok": False,
            "models": FALLBACK_MODELS.get(provider, []),
            "error": friendly_provider_error(provider, endpoint, exc),
        }
