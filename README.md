# Python Skill Lab

A local beginner-friendly learning app for Python, backend APIs, DevOps automation, and AI engineering topics. It is learning-first, with career readiness built into each topic.

> **⚠️ Run this on your own machine only.** Python Skill Lab executes the code you write in a local subprocess on `127.0.0.1`. The code runner uses lightweight checks to block obvious mistakes, but it is **not a security sandbox** and those checks can be bypassed. **Do not host this on a shared, public, or multi-user server**, and do not expose the port to a network. On your own desktop, the runner has no more power than your own terminal — which is exactly what it is meant for.

## Who This Is For

This app is built for **complete beginners** — people who want to get into Python and AI programming and may have never written a line of code before.

- **Never coded before?** Start with the **Getting Started: Coding From Zero** topic. It assumes no prior programming knowledge and explains what code is, how to run it, variables, types, your first function, and how to read errors without panicking.
- **Know another language, or returning to coding?** You can jump straight to **Python Basics** and move quickly through the Python Core track.
- **Heading toward AI engineering?** Python is the foundation for AI work. Once you are comfortable with the Python Core track, the FastAPI, Pydantic, LangChain, LangGraph, MCP, and RAG topics take you into modern AI application development.

Every topic follows the same flow: overview → lesson → hands-on labs → practice test, with an optional AI coach that guides you without giving away the answer.

## Run

```powershell
python app.py
```

Then open:

```text
http://127.0.0.1:8765
```

The app runs fully offline — fonts and the code editor are served from `static/vendor/` with no CDN calls required.

## What It Covers

- 15 topics: Python basics, functions, data structures, OOP, errors/testing, async, FastAPI, Pydantic, SQL/HTTP/Git, Python for DevOps, LangChain, LangGraph, MCP, RAG/embeddings/vector databases — plus a zero-knowledge Getting Started on-ramp
- Topic flow: overview → lesson (with inline concept diagrams) → hands-on labs → practice test
- **Execution Visualizer** — step through your own code line by line, watching variables change, available in every editor (scratchpad, lab, and lesson try-it popup)
- Practice exercises with local test runner and optional AI coaching across 7 providers (Ollama, LM Studio, OpenAI, Anthropic, Google AI Studio, Grok, Groq)

## Content System

Curriculum content now lives in `content/` as structured files (per-topic `topic.json`, `lesson.md`, `labs.json`, `practice.json`) plus `content/sources.json`.

The app loads this through `content_loader.py` and keeps the same `/api/curriculum` response shape used by the current UI.

## Notes

The code runner executes snippets locally with a short timeout. Treat it as a practice tool, not a security sandbox for untrusted code.

UI theme note: dark mode has been removed for now. The app uses a single warm light theme to avoid inconsistent contrast and readability issues.

For full setup, deployment, and AI provider notes, see `SETUP.md`.
