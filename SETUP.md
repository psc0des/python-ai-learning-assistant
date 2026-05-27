# Python Skill Lab Setup

## Code Location

This project is saved at:

```text
E:\AI\Python_Learning_Assistant
```

## Project Structure

```text
Python_Learning_Assistant/
  app.py              Local HTTP server, code runner, AI provider integration
  content_loader.py   Structured content loader with legacy fallback
  curriculum.py       Learning topics, lesson content, citations, real-world notes
  exercises.py        Coding labs and test cases
  practice_tests.py   Topic practice-test questions
  content/
    manifest.json     Topic order and schema metadata
    sources.json      Official source registry
    topics/           Per-topic authored content (topic, lesson, labs, practice)
  static/
    index.html        Browser UI
    app.js            UI behavior, labs, tests, AI chat
    styles.css        App styling
  AGENTS.md           Contributor instructions and project quality rules
  README.md           Short project overview
  SETUP.md            Setup and deployment notes
```

## Requirements

- Python 3.10 or newer
- No required third-party Python packages for the current version
- Optional local AI:
  - Ollama running at `http://127.0.0.1:11434`
  - LM Studio running at `http://127.0.0.1:1234`
- Optional hosted AI:
  - OpenAI API key
  - Anthropic API key

## Run Locally

Open PowerShell in the project folder:

```powershell
cd "E:\AI\Python_Learning_Assistant"
python app.py
```

Then open:

```text
http://127.0.0.1:8765
```

### Recommended QA Restart (avoids stale content)

Because curriculum content is loaded once at process start, long-running servers can become stale after content edits.

Before audit/QA runs on port `8765`, restart with:

```powershell
cd "E:\AI\Python_Learning_Assistant"
powershell -ExecutionPolicy Bypass -File .\scripts\restart_8765.ps1
```

This script:
- stops any process listening on `8765`
- starts a fresh app process from current workspace content
- checks `/api/curriculum` and prints loaded mode/counts

Optional strict content validation mode:

```powershell
$env:PY_SKILL_LAB_STRICT_CONTENT="1"
python app.py
```

When strict mode is on, startup fails if content validation warnings exist.

To use another port:

```powershell
$env:PY_INTERVIEW_PORT="9000"
python app.py
```

Then open:

```text
http://127.0.0.1:9000
```

## AI Coach Setup

The app works without AI. Local tests and built-in feedback still run.

### Ollama

1. Start Ollama.
2. Make sure at least one model is installed.
3. In the app, go to `Labs` -> `AI provider settings`.
4. Select:

```text
Provider: Ollama
Endpoint: http://127.0.0.1:11434
Model: choose from the dropdown
```

Current detected local Ollama models on this machine:

```text
qwen3.5:latest
nemotron-3-nano:4b
```

### LM Studio

1. Start LM Studio.
2. Enable the local OpenAI-compatible server.
3. In the app, use:

```text
Provider: LM Studio
Endpoint: http://127.0.0.1:1234/v1/chat/completions
```

### OpenAI

Use:

```text
Provider: OpenAI
Endpoint: https://api.openai.com/v1/chat/completions
API key: your OpenAI API key
```

### Anthropic

Use:

```text
Provider: Anthropic
Endpoint: https://api.anthropic.com/v1/messages
API key: your Anthropic API key
```

## Local Deployment

For personal/local use, running `python app.py` is enough.

For a more persistent local setup on Windows, a senior developer can wrap it with:

- a PowerShell startup script
- Windows Task Scheduler
- NSSM or another Windows service wrapper
- a local reverse proxy if needed

Recommended local-only binding:

```text
127.0.0.1
```

The current app intentionally binds to localhost so it is not exposed to the network by default.

## Important Security Note

The coding lab executes Python snippets locally with a timeout. This is fine for personal learning, but it is not a secure sandbox for untrusted users.

Before deploying for multiple users, a senior developer should review and harden:

- code execution isolation
- filesystem restrictions
- process limits
- network restrictions
- authentication
- API key handling
- logging and audit behavior

## Current Product Shape

The app is now learning-focused, not interview-only.

Each topic is organized as:

- Overview
- Lesson
- Labs
- Practice Test

The AI Coach is conversational and can review the current topic, code, and latest local test result.

## Theme Behavior

Dark mode is currently disabled/removed. The UI runs in a single warm light theme so visual contrast and readability stay consistent across pages.
