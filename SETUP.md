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
  content_loader.py   Structured content loader from content/
  runner.py           Lab test runner and execution tracer (sys.settrace in subprocess)
  ai_coach.py         AI provider integration
  content/
    manifest.json     Topic order and schema metadata (22 topics)
    sources.json      Official source registry
    topics/           Per-topic authored content (topic.json, lesson.md, labs.json, practice.json)
  static/
    index.html        App shell — includes scratchpad, try-it popup, viz overlay modal
    app.js            UI behavior, topic rendering, labs, AI coach, execution visualizer
    styles.css        Warm notebook visual design
    codemirror-init.js  CodeMirror 6 editor setup — imports from /vendor/codemirror-bundle.js
    vendor/
      codemirror-bundle.js  Bundled CodeMirror 6 (built by scripts/build.js — committed)
  scripts/
    build.js          esbuild script — bundles CodeMirror into static/vendor/codemirror-bundle.js
    codemirror-entry.js  Entry point that re-exports all required CodeMirror symbols
    package.json      npm manifest for esbuild + CodeMirror packages
  pyproject.toml      Ruff lint configuration
  .pre-commit-config.yaml Optional pre-commit hook configuration
  tests/
    test_content_loader.py       Content structure and loader tests
    test_content_quality.py      Quality gate (≥5 labs, ≥8 questions, sources present)
    test_runner.py               Lab runner tests incl. _safe() and _norm() edge cases
    test_trace.py                Execution tracer tests
    test_origin_validation.py    HTTP origin header security tests (exact match, hostile prefix, wrong port)
    test_content_drift.py        Parity guard: lesson.md headings must match topic.json lesson_sections
  docs/
    ai_provider_qa.md   Manual QA checklist for all 8 AI providers (sign-off before release changes to ai_coach.py)
  .env.example        Documented environment variables
  CONTRIBUTING.md     Human contributor setup and PR guide
  SECURITY.md         Vulnerability reporting and local-only security model
  AGENTS.md           Contributor instructions and project quality rules
  README.md           Short project overview
  SETUP.md            Setup and deployment notes
```

## Requirements

- Python 3.10 or newer
- No required third-party Python packages for the current version
- Development tools from `requirements-dev.txt` for tests, lint, and pre-commit
- Node.js 18 or newer (only needed to rebuild the CodeMirror vendor bundle — pre-built bundle is committed)
- Optional local AI:
  - Ollama running at `http://127.0.0.1:11434`
  - LM Studio running at `http://127.0.0.1:1234`
- Optional hosted AI:
  - OpenAI API key
  - Anthropic API key
  - Google AI Studio API key
  - Grok (xAI) API key
  - Groq Cloud API key
  - Azure AI Foundry API key and endpoint

The AI Coach is **optional** — every lesson, lab, practice test, and the
execution visualizer work without it. It is not configured out of the box (the
default provider is local Ollama). On first run the app shows a one-time,
dismissible "Set up AI" banner; the quickest path for most learners is a hosted
provider (OpenAI, Anthropic, Google, or Groq) with an API key, which needs no
local install. If you try the coach before setting it up, the app explains what
to do instead of failing silently.

## First-Time Vendor Setup

The pre-built vendor files (`static/vendor/`) are committed to the repo — you do **not** need to rebuild them to run the app. Rebuild only when upgrading CodeMirror.

To rebuild the CodeMirror bundle:

```powershell
cd scripts
npm install
node build.js
```

The UI uses system fonts (no web fonts), so there is nothing to download or vendor for typography.

## Development Checks

Install development tools:

```powershell
pip install -r requirements-dev.txt
```

Run lint:

```powershell
python -m ruff check --no-cache .
```

Optional local pre-commit setup:

```powershell
pre-commit install
pre-commit run --all-files
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

Structured content is the only runtime source of truth. If `content/` fails to
load, startup raises a fatal error so a broken release cannot silently serve
stale generated data.

Optional AI timeout tuning (useful for slower/faster local models):

```powershell
$env:PY_SKILL_LAB_AI_TIMEOUT_SECONDS="45"
$env:PY_SKILL_LAB_AI_PROVIDER_TEST_TIMEOUT_SECONDS="20"
$env:PY_SKILL_LAB_AI_MODELS_TIMEOUT_SECONDS="8"
python app.py
```

Defaults are intentionally short so the UI fails fast with clear fallback feedback instead of appearing stuck.

To use another port:

```powershell
$env:PY_SKILL_LAB_PORT="9000"
python app.py
```

Then open:

```text
http://127.0.0.1:9000
```

`PY_SKILL_LAB_PORT` is the primary env var. The legacy alias `PY_INTERVIEW_PORT` also works but is not recommended for new setups.

## Configuration

All supported environment variables are listed in `.env.example`. The app
auto-loads `.env` at startup, and values already set in your shell take
priority over the file. The AI Settings panel writes the selected provider,
model, endpoint, and hosted provider API keys to `.env` when you click
**Save & Apply** or **Verify provider**. Saved keys are used server-side after
restart, but the browser never receives the secret value back.

| Variable | Default | Purpose |
|---|---:|---|
| `PY_SKILL_LAB_PORT` | `8765` | Local server port. |
| `PY_SKILL_LAB_OPEN_BROWSER` | `1` | Opens the browser automatically when the server starts. |
| `PY_SKILL_LAB_STRICT_CONTENT` | `0` | Fails startup when content validation has warnings. |
| `PY_SKILL_LAB_AI_TIMEOUT_SECONDS` | `45` | Timeout for AI coach calls. Local models may need one warm-up request after launch. |
| `PY_SKILL_LAB_AI_LOCAL_TIMEOUT_SECONDS` | `120` | Longer timeout for local streaming model calls. |
| `PY_SKILL_LAB_AI_PROVIDER_TEST_TIMEOUT_SECONDS` | `20` | Short timeout for hosted Verify Provider health checks. |
| `PY_SKILL_LAB_AI_MODELS_TIMEOUT_SECONDS` | `8` | Timeout for model-list refresh calls. |
| `PY_SKILL_LAB_AI_PROVIDER` | blank | Last selected AI provider. |
| `PY_SKILL_LAB_AI_MODEL` | blank | Last selected AI model. |
| `PY_SKILL_LAB_AI_ENDPOINT` | blank | Last selected AI endpoint. |
| `PY_SKILL_LAB_OPENAI_KEY` | blank | Optional server-side OpenAI key. |
| `PY_SKILL_LAB_ANTHROPIC_KEY` | blank | Optional server-side Anthropic key. |
| `PY_SKILL_LAB_GOOGLE_KEY` | blank | Optional server-side Google AI Studio key. |
| `PY_SKILL_LAB_GROK_KEY` | blank | Optional server-side Grok (xAI) key. |
| `PY_SKILL_LAB_GROQ_KEY` | blank | Optional server-side Groq Cloud key. |
| `PY_SKILL_LAB_AZURE_FOUNDRY_KEY` | blank | Optional server-side Azure AI Foundry key. |

Deprecated compatibility aliases: `PY_INTERVIEW_PORT` and
`PY_INTERVIEW_OPEN_BROWSER`. Prefer the `PY_SKILL_LAB_*` names for new setup.

## AI Coach Setup

The app works without AI. Local tests and built-in feedback still run.

### Ollama

1. Start Ollama.
2. Make sure at least one model is installed.
3. In the app, open **AI Settings** in the left sidebar.
4. Select:

```text
Provider: Ollama
Endpoint: http://127.0.0.1:11434
Model: choose from the dropdown
```

Model names are read from your local Ollama installation. Click **Show local models**, choose one of the installed models from the Model dropdown, then click **Test selected model** to confirm that the selected model can answer. The app should not show local models that are not actually installed.

### LM Studio

1. Start LM Studio.
2. Enable the local OpenAI-compatible server.
3. In the app, open **AI Settings** in the left sidebar and select:

```text
Provider: LM Studio
Endpoint: http://127.0.0.1:1234
```

The app derives LM Studio's `/v1/models` and `/v1/chat/completions` routes from that base URL. Click **Show local models**, choose a loaded model from the Model dropdown, then click **Test selected model**. If LM Studio is reachable but no models appear, load a model in LM Studio first.

### OpenAI

In the app, open **AI Settings** in the left sidebar and enter:

```text
Provider: OpenAI
Endpoint: https://api.openai.com/v1/chat/completions
API key: your OpenAI API key
```

### Anthropic

In the app, open **AI Settings** in the left sidebar and enter:

```text
Provider: Anthropic
Endpoint: https://api.anthropic.com/v1/messages
API key: your Anthropic API key
```

### Google AI Studio (free tier available)

Get a free API key at `https://aistudio.google.com`. In the app, open **AI Settings** and enter:

```text
Provider: Google AI Studio
Endpoint: https://generativelanguage.googleapis.com/v1beta
API key: your Google AI Studio API key
```

Recommended free models: `gemini-2.0-flash`, `gemini-2.0-flash-lite`.

### Grok (xAI)

Get an API key at `https://console.x.ai`. In the app, open **AI Settings** and enter:

```text
Provider: Grok (xAI)
Endpoint: https://api.x.ai/v1/chat/completions
API key: your xAI API key
```

Recommended model: `grok-3-mini` (has a free tier).

### Groq Cloud (free tier available)

Get a free API key at `https://console.groq.com`. Groq runs open models (Llama, Gemma, Mistral) on custom inference hardware — very fast responses. In the app, open **AI Settings** and enter:

```text
Provider: Groq Cloud
Endpoint: https://api.groq.com/openai/v1/chat/completions
API key: your Groq API key
```

Recommended free models: `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`.

### Azure AI Foundry

Get your endpoint and API key from the Azure AI Foundry portal. In the app, open **AI Settings** and enter:

```text
Provider: Azure AI Foundry
Endpoint: https://<your-project>.services.ai.azure.com/api/projects/<project-name>/v1/
API key: your Azure AI Foundry API key
Model: type the deployed model name (e.g. gpt-4o, Phi-4-mini-instruct)
```

The model field is a free-text input. Type the exact deployed model name if the UI does not list it.

When a hosted provider key is configured, click **Verify provider** to send a tiny capped test prompt to the configured model. If you type a key in the UI, Verify first saves the provider/model/endpoint and key to `.env` so a stale saved key cannot override the new one. Then click **Save & Apply** to keep the provider/model selection. After restart, the API key field stays blank for safety; the helper text says when a saved server-side key is available.

### Server-side API key environment variables

Instead of entering keys in the UI, you can set them as environment variables before starting the server. The app reads these on startup and they take priority over any UI-entered key.

| Provider | Environment variable |
|---|---|
| OpenAI | `PY_SKILL_LAB_OPENAI_KEY` |
| Anthropic | `PY_SKILL_LAB_ANTHROPIC_KEY` |
| Google AI Studio | `PY_SKILL_LAB_GOOGLE_KEY` |
| Grok (xAI) | `PY_SKILL_LAB_GROK_KEY` |
| Groq Cloud | `PY_SKILL_LAB_GROQ_KEY` |
| Azure AI Foundry | `PY_SKILL_LAB_AZURE_FOUNDRY_KEY` |

When a server-side key is set, **Verify provider** can connect to the provider directly. Hosted provider model names are treated as configured API choices; local Ollama/LM Studio model discovery stays separate under **Show local models**.

Custom endpoints are trusted destinations. If you change a hosted provider endpoint, Python Skill Lab sends the configured API key to that endpoint. Only use provider URLs or local servers you control, and do not expose this app as a shared/public service.

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

The app is learning-focused, not interview-only. 22 topics across Python Core, Engineering Habits, Intermediate Python, Must-Know Extras, DevOps, Backend, AI Foundations, AI Apps, and AI Projects.

Each topic is organized as:

- Overview
- Lesson (with inline concept diagrams for structural topics)
- Labs
- Practice Test

### Concept Diagrams

Eight topics have an inline SVG concept diagram embedded in one lesson section (`diagram_svg` + `diagram_caption` fields in `topic.json`): `getting-started` (function input/output), `fastapi` (request lifecycle), `rag-vectors` (pipeline), `mcp` (host/client/server), `langgraph` (state graph), `langchain` (agent loop), `ai-evaluation` (eval loop), and `ai-app-architecture` (three-layer structure). Diagrams use the locked palette: charcoal `#1e293b` (focal), green `#059669` (result), slate `#94a3b8` (borders), gray `#4a5568` (arrows).

### Execution Visualizer

Every code editor — the scratchpad, the lab editor, and the lesson try-it popup — has a **Visualize** button. It calls `/api/trace`, which runs the code under `sys.settrace` in a subprocess and returns a list of `{line, vars}` steps (max 300). The shared `#vizOverlay` modal steps through the execution line by line with a variables panel. The modal is draggable — grab the header and move it anywhere on screen.

Three cases are handled deterministically without AI:
- **Runtime error** (e.g. `NameError`): some steps ran before the crash. The final step is highlighted with a plain-English note.
- **Compile-time error** (e.g. `SyntaxError`): no lines ran. The trace returns 0 steps and an `error_line` field. The offending line is highlighted in red with a built-in explanation.
- **Blocked construct** (e.g. `input()`, `open()`): caught by the AST scanner before the trace runs. A short deterministic note explains the block and what to do instead.

AI narration is **not** automatic. The learner clicks "Ask AI" in the visualizer controls to request an AI explanation of the current step or error. This keeps the visualizer deterministic and avoids AI timeout noise.

### AI Coach

AI help has two separate surfaces so the learner always knows what kind of help they are asking for:

- **AI Coach in Labs**: embedded beside the code editor. Send is freeform lab chat; Explain Code includes the current exercise code and latest test result.
- **Ask AI messenger**: floating quick-help chat for selected text, lesson Ask AI, Try It code/output, Visualizer step/error context, and independent questions.
- **Try It popup open**: Ask AI opens the messenger with popup code and output automatically attached.
- **Visualizer open**: Ask AI opens the messenger with the current step line, variables, and any error automatically attached; the visualizer note stays deterministic.

The lab coach operates in two modes. When the learner types a freeform question in the lab coach (`mode: "chat"`), only topic and lesson context is sent — exercise code and test results are excluded so the AI focuses on the question asked. Tests are also **not** auto-run in this mode. When a preset button such as "Explain Code" is clicked (`mode: "lab"`), the full context is sent, tests are auto-run if no prior result exists, and the AI gives a structured review of the exercise and test results. The floating Ask AI messenger always uses chat mode and never auto-runs tests. Freeform Ask AI chat does not inject the current topic; lesson, selection, Try It, and Visualizer actions opt into topic/page context explicitly.

Closing the floating Ask AI messenger only hides it. Use **New chat** in the Ask AI header to clear that messenger's conversation history, especially after changing models or switching from a contextual question to a general one.

AI responses stream into both the Labs coach and floating Ask AI when the selected provider supports streaming. Ollama, LM Studio, OpenAI-compatible providers, Grok, Groq, and Azure AI Foundry use the streaming route. Providers without a streaming adapter still fall back to a messenger-style reveal so learners never get a sudden full-answer dump.

Each AI reply shows a small stats line below the response: model name, output tokens, input tokens, tok/s, and elapsed time. This is useful for comparing local Ollama speed against cloud providers.

If a provider is unavailable or slow, the app surfaces explicit fallback states:

- Lab Explain Code: `AI Coach unavailable (...)` + built-in feedback in the embedded lab coach
- Freeform, selected-text, Try It, and Visualizer Ask AI: transport/timeout messages appear in the floating Ask AI messenger
- Local Ollama/LM Studio timeouts include a warm-up hint because the first request after launch can be slower than later requests
- Hosted-provider timeouts ask the learner to check API key, model name, endpoint, network access, and provider status. Preview models can be slower than stable fast models, so provider verification uses a small `max_tokens` cap and a shorter health-check timeout.

## Theme Behavior

Dark mode is currently disabled/removed. The UI runs in a single warm light theme so visual contrast and readability stay consistent across pages.
