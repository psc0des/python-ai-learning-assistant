# Python Skill Lab Setup

## Code Location

This project is saved at:

```text
E:\AI\Python_Learning_Assistant
```

## Project Structure

```text
Python_Learning_Assistant/
  app.py              Local HTTP server, API routes (including /api/trace)
  content_loader.py   Structured content loader with legacy fallback
  runner.py           Lab test runner and execution tracer (sys.settrace in subprocess)
  ai_coach.py         AI provider integration
  curriculum.py       Legacy topic metadata (fallback only)
  exercises.py        Legacy coding labs (fallback only)
  practice_tests.py   Legacy practice tests (fallback only)
  content/
    manifest.json     Topic order and schema metadata (15 topics)
    sources.json      Official source registry
    topics/           Per-topic authored content (topic.json, lesson.md, labs.json, practice.json)
  static/
    index.html        App shell — includes scratchpad, try-it popup, viz overlay modal
    app.js            UI behavior, topic rendering, labs, AI coach, execution visualizer
    styles.css        Warm notebook visual design
    codemirror-init.js  CodeMirror 6 editor setup — imports from /vendor/codemirror-bundle.js
    vendor/
      codemirror-bundle.js  Bundled CodeMirror 6 (built by scripts/build.js — committed)
      fonts.css             Local @font-face declarations (built by scripts/vendor_fonts.py — committed)
      fonts/                Inter and JetBrains Mono woff2 files (committed)
  scripts/
    build.js          esbuild script — bundles CodeMirror into static/vendor/codemirror-bundle.js
    codemirror-entry.js  Entry point that re-exports all required CodeMirror symbols
    package.json      npm manifest for esbuild + CodeMirror packages
    vendor_fonts.py   Downloads Inter and JetBrains Mono from Google Fonts into static/vendor/fonts/
  tests/
    test_content_loader.py       Content structure and loader tests
    test_content_quality.py      Quality gate (≥5 labs, ≥8 questions, sources present)
    test_runner.py               Lab runner tests incl. _safe() and _norm() edge cases
    test_trace.py                Execution tracer tests
    test_origin_validation.py    HTTP origin header security tests (exact match, hostile prefix, wrong port)
    test_content_drift.py        Parity guard: lesson.md headings must match topic.json lesson_sections
  AGENTS.md           Contributor instructions and project quality rules
  README.md           Short project overview
  SETUP.md            Setup and deployment notes
```

## Requirements

- Python 3.10 or newer
- No required third-party Python packages for the current version
- Node.js 18 or newer (only needed to rebuild the CodeMirror vendor bundle — pre-built bundle is committed)
- Optional local AI:
  - Ollama running at `http://127.0.0.1:11434`
  - LM Studio running at `http://127.0.0.1:1234`
- Optional hosted AI:
  - OpenAI API key
  - Anthropic API key

## First-Time Vendor Setup

The pre-built vendor files (`static/vendor/`) are committed to the repo — you do **not** need to rebuild them to run the app. Rebuild only when upgrading CodeMirror or font versions.

To rebuild the CodeMirror bundle:

```powershell
cd scripts
npm install
node build.js
```

To refresh the local font files:

```powershell
python scripts/vendor_fonts.py
```

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

Recommended models (pull if not installed):

```text
llama3.2
qwen2.5
phi3.5
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

### Google AI Studio (free tier available)

Get a free API key at `https://aistudio.google.com`. Use:

```text
Provider: Google AI Studio
Endpoint: https://generativelanguage.googleapis.com/v1beta
API key: your Google AI Studio API key
```

Recommended free models: `gemini-2.0-flash`, `gemini-2.0-flash-lite`.

### Grok (xAI)

Get an API key at `https://console.x.ai`. Use:

```text
Provider: Grok (xAI)
Endpoint: https://api.x.ai/v1/chat/completions
API key: your xAI API key
```

Recommended model: `grok-3-mini` (has a free tier).

### Groq Cloud (free tier available)

Get a free API key at `https://console.groq.com`. Groq runs open models (Llama, Gemma, Mistral) on custom inference hardware — very fast responses. Use:

```text
Provider: Groq Cloud
Endpoint: https://api.groq.com/openai/v1/chat/completions
API key: your Groq API key
```

Recommended free models: `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`.

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

The app is learning-focused, not interview-only. 15 topics across Python Core, Engineering Habits, Backend, AI Apps, and DevOps.

Each topic is organized as:

- Overview
- Lesson (with inline concept diagrams for structural topics)
- Labs
- Practice Test

### Concept Diagrams

Six topics have an inline SVG concept diagram embedded in one lesson section (`diagram_svg` + `diagram_caption` fields in `topic.json`): `getting-started` (function input/output), `fastapi` (request lifecycle), `rag-vectors` (pipeline), `mcp` (host/client/server), `langgraph` (state graph), `langchain` (agent loop). Diagrams use the locked palette: charcoal `#1e293b` (focal), green `#059669` (result), slate `#94a3b8` (borders), gray `#4a5568` (arrows).

### Execution Visualizer

Every code editor — the scratchpad, the lab editor, and the lesson try-it popup — has a **Visualize** button. It calls `/api/trace`, which runs the code under `sys.settrace` in a subprocess and returns a list of `{line, vars}` steps (max 300). The shared `#vizOverlay` modal steps through the execution line by line with a variables panel.

### AI Coach

The AI Coach is conversational and can review the current topic, code, and latest local test result. Selecting any text on the page shows a floating Ask AI button — clicking it switches to the Labs tab and sends the selection as a question to the coach.

Each AI reply shows a small stats line below the response: model name, output tokens, input tokens, tok/s, and elapsed time. This is useful for comparing local Ollama speed against cloud providers.

## Theme Behavior

Dark mode is currently disabled/removed. The UI runs in a single warm light theme so visual contrast and readability stay consistent across pages.
