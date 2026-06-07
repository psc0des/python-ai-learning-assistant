# Python Skill Lab

**A local desktop learning app for Python, backend APIs, DevOps automation, and AI engineering.** Runs entirely on your own machine — no account, no internet required, no server to manage.

> **⚠️ Personal use only — do not host for other people.**
> Python Skill Lab runs the code you write in a local subprocess on `127.0.0.1`. The code runner is designed for personal learning, not as a hardened security sandbox. **Do not deploy this on a shared, public, or multi-user server and do not expose the port to a network.** On your own desktop it is no more powerful than your own terminal, which is exactly the point.

## Who This Is For

This app is built for **complete beginners** — people who want to get into Python and AI programming and may have never written a line of code before.

- **Never coded before?** Start with the **Getting Started: Coding From Zero** topic. It assumes no prior programming knowledge and explains what code is, how to run it, variables, types, your first function, and how to read errors without panicking.
- **Know another language, or returning to coding?** You can jump straight to **Python Basics** and move quickly through the Python Core track.
- **Heading toward AI engineering?** Python is the foundation for AI work. Once you are comfortable with the Python Core track, the FastAPI, Pydantic, LangChain, LangGraph, MCP, and RAG topics take you into modern AI application development.

Every topic follows the same flow: overview → lesson → hands-on labs → practice test, with an optional AI coach that guides you without giving away the answer.

## Requirements

- Python 3.10 or newer
- No `pip install` needed — the app uses only the Python standard library
- Optional: an AI provider key or a local Ollama/LM Studio instance for the AI coach feature (the app works fine without one)

## Run

```powershell
python app.py
```

Then open `http://127.0.0.1:8765` in your browser.

The app runs fully offline — fonts and the code editor are bundled in `static/vendor/` with no CDN calls at runtime.

## Tests

```powershell
pip install -r requirements-dev.txt
python -B -m pytest tests -q -p no:cacheprovider
```

`pytest` is the only dev dependency. The app itself needs no `pip install`. All 1080 tests should pass on a clean clone.

## What It Covers

- 21 topics: Python basics, functions, data structures, OOP, errors/testing, async, LLM API calls, structured LLM outputs, basic AI evaluation, basic AI app architecture, FastAPI, Pydantic, SQL/HTTP/Git, Python for DevOps, LangChain, LangGraph, MCP, RAG/embeddings, simple RAG project, tool calling — plus a zero-knowledge Getting Started on-ramp; 122 labs total including one Advanced capstone per topic
- Topic flow: overview → lesson (with inline concept diagrams) → hands-on labs → practice test
- **Capstone labs** — one advanced multi-function project per major track (Python Core, Backend, AI Apps, DevOps, Engineering Habits) that integrates concepts from across the track
- **Learner readiness signals** — sidebar badges show lab progress and test scores; a readiness bar shows "Core labs done" when all non-capstone labs and the practice test (≥80%) are complete, and "Topic complete" once the capstone is also passed, with a direct link to the next topic
- **Execution Visualizer** — step through your own code line by line, watching variables change; draggable overlay, available in every editor; beginner-friendly error explanations for both runtime and syntax errors
- Practice exercises with local test runner and context-aware AI coaching — inline inside the Try It popup and Visualizer, or via the full AI Coach chat; supports 7 providers (Ollama, LM Studio, OpenAI, Anthropic, Google AI Studio, Grok, Groq)

## Content System

Curriculum content now lives in `content/` as structured files (per-topic `topic.json`, `lesson.md`, `labs.json`, `practice.json`) plus `content/sources.json`.

The app loads this through `content_loader.py` and keeps the same `/api/curriculum` response shape used by the current UI.

## Notes

The code runner executes snippets locally with a short timeout. Treat it as a practice tool, not a security sandbox for untrusted code.

AI request timeout defaults are intentionally short so the learning UI does not appear frozen if a provider is down:

- `PY_SKILL_LAB_AI_TIMEOUT_SECONDS` (default `25`) for AI coach calls
- `PY_SKILL_LAB_AI_MODELS_TIMEOUT_SECONDS` (default `8`) for model list refresh

UI theme note: dark mode has been removed for now. The app uses a single warm light theme to avoid inconsistent contrast and readability issues.

For full setup, deployment, and AI provider notes, see `SETUP.md`.
