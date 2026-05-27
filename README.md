# Python Skill Lab

A local beginner-friendly learning app for Python, backend APIs, DevOps automation, and AI engineering topics. It is learning-first, with career readiness built into each topic.

## Run

```powershell
python app.py
```

Then open:

```text
http://127.0.0.1:8765
```

## What It Covers

- Python basics, functions, data structures, OOP, errors, testing, async
- FastAPI, Pydantic, HTTP, SQL, Git, terminal basics, Python for DevOps
- LangChain, LangGraph, MCP, RAG, embeddings, vector databases
- Topic flow: overview, lesson, labs, and practice test
- Practice exercises with local tests and optional AI coaching

## Content System

Curriculum content now lives in `content/` as structured files (per-topic `topic.json`, `lesson.md`, `labs.json`, `practice.json`) plus `content/sources.json`.

The app loads this through `content_loader.py` and keeps the same `/api/curriculum` response shape used by the current UI.

## Notes

The code runner executes snippets locally with a short timeout. Treat it as a practice tool, not a security sandbox for untrusted code.

UI theme note: dark mode has been removed for now. The app uses a single warm light theme to avoid inconsistent contrast and readability issues.

For full setup, deployment, and AI provider notes, see `SETUP.md`.
