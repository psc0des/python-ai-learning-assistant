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
import time
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

AI_TIMEOUT_SECONDS = 90

# Environment variable names for server-side API keys (preferred over client-sent)
ENV_OPENAI_API_KEY = "PY_SKILL_LAB_OPENAI_KEY"
ENV_ANTHROPIC_API_KEY = "PY_SKILL_LAB_ANTHROPIC_KEY"
ENV_GOOGLE_API_KEY = "PY_SKILL_LAB_GOOGLE_KEY"
ENV_GROK_API_KEY = "PY_SKILL_LAB_GROK_KEY"
ENV_GROQ_API_KEY = "PY_SKILL_LAB_GROQ_KEY"


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

_ENV_KEY_MAP = {
    "openai": ENV_OPENAI_API_KEY,
    "anthropic": ENV_ANTHROPIC_API_KEY,
    "google": ENV_GOOGLE_API_KEY,
    "grok": ENV_GROK_API_KEY,
    "groq": ENV_GROQ_API_KEY,
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
            call_result = call_ollama(endpoint or "http://127.0.0.1:11434", model or "llama3.2", prompt,
                                      temperature, top_p, top_k)
        elif provider == "lmstudio":
            call_result = call_openai_compatible(
                endpoint or "http://127.0.0.1:1234/v1/chat/completions",
                api_key or "lm-studio",
                model or "local-model",
                prompt, temperature, top_p,
            )
        elif provider == "openai":
            if not api_key:
                raise ValueError("OpenAI API key is required. Set it in the UI or as PY_SKILL_LAB_OPENAI_KEY env var.")
            call_result = call_openai_compatible(
                endpoint or "https://api.openai.com/v1/chat/completions",
                api_key,
                model or "gpt-4.1-mini",
                prompt, temperature, top_p,
            )
        elif provider == "anthropic":
            if not api_key:
                raise ValueError("Anthropic API key is required. Set it in the UI or as PY_SKILL_LAB_ANTHROPIC_KEY env var.")
            call_result = call_anthropic(
                endpoint or "https://api.anthropic.com/v1/messages",
                api_key,
                model or "claude-3-5-haiku-latest",
                prompt, temperature, top_p,
            )
        elif provider == "google":
            if not api_key:
                raise ValueError("Google API key is required. Get one free at aistudio.google.com or set PY_SKILL_LAB_GOOGLE_KEY env var.")
            call_result = call_google(
                endpoint or "https://generativelanguage.googleapis.com/v1beta",
                api_key,
                model or "gemini-2.0-flash",
                prompt, temperature, top_p, top_k,
            )
        elif provider == "grok":
            if not api_key:
                raise ValueError("Grok API key is required. Get one at console.x.ai or set PY_SKILL_LAB_GROK_KEY env var.")
            call_result = call_openai_compatible(
                endpoint or "https://api.x.ai/v1/chat/completions",
                api_key,
                model or "grok-3-mini",
                prompt, temperature, top_p,
            )
        elif provider == "groq":
            if not api_key:
                raise ValueError("Groq API key is required. Get one free at console.groq.com or set PY_SKILL_LAB_GROQ_KEY env var.")
            call_result = call_openai_compatible(
                endpoint or "https://api.groq.com/openai/v1/chat/completions",
                api_key,
                model or "llama-3.3-70b-versatile",
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


def narrate_trace(payload: dict[str, Any]) -> dict[str, Any]:
    """Generate beginner-friendly per-step narrations for the execution visualizer."""
    provider = str(payload.get("provider", "ollama")).lower()
    client_key = str(payload.get("api_key", ""))
    api_key = resolve_api_key(provider, client_key)
    model = str(payload.get("model", "")).strip()
    endpoint = str(payload.get("endpoint", "")).strip()
    code = str(payload.get("code", "")).strip()
    steps = payload.get("steps", [])
    run_error = str(payload.get("error", "")).strip()

    if not code or not steps:
        return {"ok": False, "narrations": {}, "error": "No code or steps"}

    lines = code.splitlines()
    def _get_line(n: int) -> str:
        idx = n - 1
        return lines[idx].strip() if 0 <= idx < len(lines) else "?"

    step_descriptions = []
    for i, step in enumerate(steps, start=1):
        line_num = step.get("line", 0)
        line_code = _get_line(line_num)
        vars_items = list(step.get("vars", {}).items())[:6]
        vars_str = ", ".join(f"{k}={repr(v)}" for k, v in vars_items) or "none"
        if step.get("final") and run_error:
            step_descriptions.append(
                f"Step {i} (ERROR — Python stopped here): line `{line_code}` caused {run_error} | vars before crash: {{{vars_str}}}"
            )
        elif step.get("final"):
            step_descriptions.append(f"Step {i} (FINAL — done): vars={{{vars_str}}}")
        else:
            step_descriptions.append(f"Step {i}: about to run `{line_code}` | vars so far: {{{vars_str}}}")

    error_rule = (
        "- For the ERROR step: explain what went wrong in plain words AND give a one-sentence fix hint a beginner can act on. "
        "Start with 'Error:' — e.g. 'Error: sarathay has no quotes so Python treated it as a variable name; write lastname = \"sarathay\" instead.'\n"
    ) if run_error else ""

    prompt = (
        "TASK: Explain each step of this Python code to a complete beginner.\n"
        "Rules:\n"
        "- ONE sentence per step, max 20 words\n"
        "- Use the actual variable values shown\n"
        "- Start with 'Python stores', 'Python checks', 'Python prints', 'Python adds', etc.\n"
        + error_rule
        + "- Return ONLY valid JSON: {\"1\": \"...\", \"2\": \"...\", ...} — no markdown, no extra text\n\n"
        f"CODE:\n```python\n{code}\n```\n\n"
        "STEPS:\n" + "\n".join(step_descriptions)
    )

    try:
        if provider == "ollama":
            result = call_ollama(endpoint or "http://127.0.0.1:11434", model or "llama3.2", prompt, 0.3, 0.9, 40)
        elif provider == "lmstudio":
            result = call_openai_compatible(endpoint or "http://127.0.0.1:1234/v1/chat/completions", api_key or "lm-studio", model or "local-model", prompt, 0.3, 0.9)
        elif provider == "openai":
            if not api_key:
                raise ValueError("OpenAI API key required")
            result = call_openai_compatible(endpoint or "https://api.openai.com/v1/chat/completions", api_key, model or "gpt-4.1-mini", prompt, 0.3, 0.9)
        elif provider == "anthropic":
            if not api_key:
                raise ValueError("Anthropic API key required")
            result = call_anthropic(endpoint or "https://api.anthropic.com/v1/messages", api_key, model or "claude-3-5-haiku-latest", prompt, 0.3, 0.9)
        elif provider == "google":
            if not api_key:
                raise ValueError("Google API key required")
            result = call_google(endpoint or "https://generativelanguage.googleapis.com/v1beta", api_key, model or "gemini-2.0-flash", prompt, 0.3, 0.9, 40)
        elif provider == "grok":
            if not api_key:
                raise ValueError("Grok API key required")
            result = call_openai_compatible(endpoint or "https://api.x.ai/v1/chat/completions", api_key, model or "grok-3-mini", prompt, 0.3, 0.9)
        elif provider == "groq":
            if not api_key:
                raise ValueError("Groq API key required")
            result = call_openai_compatible(endpoint or "https://api.groq.com/openai/v1/chat/completions", api_key, model or "llama-3.3-70b-versatile", prompt, 0.3, 0.9)
        else:
            raise ValueError(f"Unknown provider: {provider}")

        text = result.get("text", "").strip()
        # Strip any markdown code fences the model may have added
        if "```" in text:
            parts = text.split("```")
            for part in parts:
                part = part.lstrip("json").strip()
                if part.startswith("{"):
                    text = part
                    break
        narrations = json.loads(text)
        return {"ok": True, "narrations": {str(k): str(v) for k, v in narrations.items()}}

    except json.JSONDecodeError:
        return {"ok": False, "narrations": {}, "error": "AI returned non-JSON"}
    except Exception as exc:
        return {"ok": False, "narrations": {}, "error": str(exc)}


def list_ai_models(payload: dict[str, Any]) -> dict[str, Any]:
    """List available models for a given AI provider."""
    provider = str(payload.get("provider", "ollama")).lower()
    endpoint = str(payload.get("endpoint", "")).strip()
    client_key = str(payload.get("api_key", ""))
    api_key = resolve_api_key(provider, client_key)

    fallback: dict[str, list[str]] = {
        "ollama": ["llama3.2", "qwen2.5", "phi3.5"],
        "lmstudio": ["local-model"],
        "openai": ["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini"],
        "anthropic": ["claude-3-5-haiku-latest", "claude-3-5-sonnet-latest"],
        "google": ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash"],
        "grok": ["grok-3-mini", "grok-3", "grok-2-1212"],
        "groq": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"],
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
        elif provider in ("grok", "groq"):
            if not api_key:
                models = fallback[provider]
            else:
                default_endpoint = (
                    "https://api.x.ai/v1/chat/completions" if provider == "grok"
                    else "https://api.groq.com/openai/v1/chat/completions"
                )
                url = model_list_url(endpoint or default_endpoint)
                data = get_json(url, {"Authorization": f"Bearer {api_key}"})
                models = sorted(item["id"] for item in data.get("data", []) if item.get("id"))
        elif provider == "google":
            if not api_key:
                models = fallback[provider]
            else:
                base = (endpoint or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
                data = get_json(f"{base}/models?key={api_key}", {})
                models = [
                    item["name"].replace("models/", "")
                    for item in data.get("models", [])
                    if item.get("name", "").startswith("models/gemini")
                    and "generateContent" in item.get("supportedGenerationMethods", [])
                ]
        else:
            raise ValueError(f"Unknown provider: {provider}")

        return {"ok": True, "models": models or fallback.get(provider, [])}
    except Exception as exc:
        logger.warning("Model listing failed (%s): %s", provider, exc)
        return {"ok": False, "models": fallback.get(provider, []), "error": str(exc)}

