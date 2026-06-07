# AGENTS.md

## Project Purpose

Python Skill Lab is a local-first learning app for Python, backend APIs, DevOps automation, and AI engineering foundations.

The app is learning-focused, not interview-only. Interview readiness should be a secondary benefit of strong lessons, realistic labs, and practice questions.

## Code Location

```text
E:\AI\Python_Learning_Assistant
```

## Run Locally

```powershell
cd "E:\AI\Python_Learning_Assistant"
python app.py
```

Open:

```text
http://127.0.0.1:8765
```

If port `8765` is busy, set another port:

```powershell
$env:PY_SKILL_LAB_PORT="9000"
python app.py
```

## Test

Run the full test suite before handing changes back:

```powershell
python -B -m pytest tests -q -p no:cacheprovider
```

For a faster content-only check:

```powershell
python -B -m pytest tests/test_curriculum.py tests/test_exercises.py -q -p no:cacheprovider
```

## Main Files

- `app.py`: local HTTP server and API routes. Serves `index.html` with `Cache-Control: no-cache` so browsers never serve a stale HTML with mismatched JS.
- `content_loader.py`: loads structured curriculum from `content/`.
- `ai_coach.py`: AI provider integration for Ollama, LM Studio, OpenAI, Anthropic, Google AI Studio, Grok (xAI), and Groq Cloud.
- `runner.py`: local Python exercise runner.
- `models.py`: request/response validation and startup content checks.
- `curriculum.py`: topic metadata, overview copy, lesson content, citations, real-world notes.
- `exercises.py`: coding labs, starter code, tests, hints, solutions.
- `practice_tests.py`: multiple-choice practice tests.
- `content/manifest.json`: topic ordering and schema metadata.
- `content/sources.json`: official source registry with `checked_at`.
- `content/topics/*`: per-topic authored content (`topic.json`, `lesson.md`, `labs.json`, `practice.json`).
- `static/index.html`: app shell. Includes the collapsible Python Scratchpad panel (Lesson tab), the `#codePopup` Try-it centered modal overlay (maximize ⤢/restore ⤡ button, "🤖 Ask AI" toolbar button, inline `#codePopupAiPanel` response area, backdrop click to close), and the shared `#vizOverlay` execution visualizer modal (with "🤖 Ask AI" button in the controls row). Fonts load from `/vendor/fonts.css` (local — no Google Fonts CDN call).
- `static/app.js`: UI behavior, topic rendering, labs, tests, AI coach interactions, selection-triggered Ask AI popover, scratchpad toggle/run/clear/visualize, Try-it modal open/maximize/run/visualize/close, lesson code block "▶ Try it" delegation (only for fences tagged ` ```python run ` — opt-in, not heuristic), `openVisualizer` / `renderViz` / `stepViz` for the deterministic execution visualizer. Runtime and compile-time errors show deterministic runner explanations; AI is called only when the learner explicitly clicks Ask AI. Both modals are draggable by their headers — `vizDrag` for the viz overlay (`.viz-modal-head`), `codePopupDrag` for the Try It popup (`.code-popup-header`, skips button clicks); `closeViz` / `closeCodePopup` reset positions. AI coach sends `mode: "chat"` when the user types a question and `mode: "lab"` when a preset button triggers it; auto-run only fires in lab mode (`questionOverride` must be set). **Escape key priority**: viz overlay handles its own Escape first; code popup Escape is skipped while viz is open — do not break this ordering. **AI settings panel**: `_aiSettingsBtn` click opens `#aiSettingsPanel` to the right of the sidebar (`rect.right + 8`) on wide viewports; JS reads `offsetHeight` after render and clamps `top` so Save & Apply is never pushed below the viewport. Falls back to above-the-button on narrow viewports.
- `static/styles.css`: warm notebook visual design. Includes `.section-diagram` (transparent, blends into lesson card), `.viz-*` (execution visualizer modal — `.viz-modal` is `position: fixed; transform: translate(-50%, -50%)` for self-centering and drag; `.viz-overlay` is a plain backdrop with no flex; `.viz-ln-error` highlights the error line in red for SyntaxErrors), `.code-popup` / `.code-popup-modal` (Try-it modal — same draggable `position: fixed` pattern as viz; `.code-popup` is a plain backdrop; `.code-popup-header` has `cursor: grab`; `z-index: 800`; viz overlay stays at `z-index: 1000` on top). Both overlays require `[hidden] { display: none }` overrides — do not remove them.
- `static/codemirror-init.js`: CodeMirror 6 editor initializer. Imports all symbols from `/vendor/codemirror-bundle.js` (local — no esm.sh CDN calls). If the bundle is unavailable the plain `<textarea>` still works.
- `static/vendor/codemirror-bundle.js`: pre-built ESM bundle of all CodeMirror 6 packages. Rebuilt via `cd scripts && npm install && node build.js`. Committed to the repo so the app works offline without Node.js.
- `static/vendor/fonts.css` + `static/vendor/fonts/`: Inter and JetBrains Mono woff2 files and @font-face declarations served locally. Rebuilt via `python scripts/vendor_fonts.py`. Committed to the repo.
- `scripts/build.js`, `scripts/codemirror-entry.js`, `scripts/package.json`: esbuild tooling for the CodeMirror bundle. `node_modules/` is gitignored.
- `scripts/vendor_fonts.py`: downloads font CSS and woff2 files from Google Fonts into `static/vendor/`.
- `SETUP.md`: setup, local deployment, and AI provider notes.

## Product Direction

Keep the app beginner-friendly and practical.

Each topic should have:

- `Overview`: clear explanation of why the topic matters and how it works.
- `Lesson`: structured teaching content with official-source citations.
- `Labs`: at least 5 labs per topic, covering the major lesson concepts.
- `Practice Test`: enough questions to cover every major lesson concept.

Avoid shallow wording such as "this topic helps you understand X" without actually teaching X. The content should read like a patient instructor walking the learner through the idea.

## Content Quality Bar

Use official documentation as the source of truth for topic explanations.

Examples:

- Python: `https://docs.python.org/3/`
- FastAPI: `https://fastapi.tiangolo.com/`
- Pydantic: `https://docs.pydantic.dev/`
- LangChain: `https://docs.langchain.com/`
- LangGraph: `https://langchain-ai.github.io/langgraph/`
- MCP: `https://modelcontextprotocol.io/`
- OpenAI API topics: `https://platform.openai.com/docs/`
- Anthropic API topics: `https://docs.anthropic.com/`

When adding or rewriting lesson content:

- cite the official docs in the topic `docs` list or section-level `source_url`;
- explain concepts in learner-friendly language;
- include practical examples and real-world usage;
- keep interview wording out of the main lesson unless the section is explicitly about interview readiness;
- prefer "what happens when code runs" explanations over generic motivation;
- cover common beginner mistakes directly.

## Current Content Status

All 21 topics have been rewritten to reference quality:

- richer `intro` and `mental_model` fields; `python-basics` and `oop` intros further refined for tone (direct, confident engineering-handbook register — see Async Python intro as the target standard);
- official source citations at the section level (`source_label` / `source_url`);
- 6 lesson sections per topic;
- each section: one-sentence analogy opener → technical explanation → beginner code example → production/professional code example (no inline `# Layman example:` or `# Professional example:` labels — labels were removed as they read awkwardly in-context);
- `lesson.md` files updated to match the rich content in each `topic.json`.

Topics at this level: `getting-started`, `python-basics`, `functions`, `data-structures`, `oop`, `errors-testing`, `fastapi`, `pydantic`, `async`, `llm-api-basics`, `structured-llm-outputs`, `ai-evaluation`, `langchain`, `langgraph`, `mcp`, `rag-vectors`, `simple-rag-project`, `simple-tool-calling`, `ai-app-architecture`, `python-devops`, `sql-http-git`.

### Concept Diagrams

Six topics have an inline SVG diagram in one lesson section (`diagram_svg` + `diagram_caption` on the section object in `topic.json`). These are rendered as a `<figure>` inside `.section-diagram`. The SVG is trusted authored content — it is NOT passed through `escapeHtml`. Locked palette: charcoal `#1e293b` (focal/your-code), green `#059669` (result/output), white with slate `#94a3b8` borders (plain boxes), gray `#4a5568` (arrows), amber `#b45309` (store/data).

Topics with diagrams: `getting-started` (function), `fastapi` (request lifecycle), `rag-vectors` (pipeline with Vector DB), `mcp` (host/client/server), `langgraph` (state graph), `langchain` (ReAct agent loop), `ai-evaluation` (eval loop), `ai-app-architecture` (three-layer structure).

Do not assume the curriculum is complete just because tests pass. Tests validate structure and exercise correctness, not full teaching quality.

## UI Direction

Preserve the warm notebook/study-lab style.

The user disliked the plain white SaaS-style version. Keep the current visual direction:

- warm paper background;
- subtle grid texture;
- restrained green accents;
- dark active tab/button state;
- compact learning workspace;
- readable long-form lesson text.

Avoid replacing the UI with generic dashboard styling, purple gradients, oversized hero sections, or marketing-page layouts.

## Labs And Runner Notes

The exercise runner executes learner code locally with a timeout. It is for personal learning, not a hardened multi-user sandbox.

When adding labs:

- include `starter`, `tests`, `hint`, `solution`, and `explanation`;
- keep tests clear and deterministic;
- include edge cases such as empty input, invalid input, boundaries, duplicates, and casing where relevant;
- verify every solution passes its own tests;
- prefer small functions that return values over print-only exercises.

**Capstone labs** (one per topic, `difficulty_order: 6`, `difficulty: "Advanced"`) integrate concepts from the topic into a class-based multi-method challenge. Capstone labs live in `labs.json` alongside regular labs — no `topic.json` or `lesson.md` changes needed. All code must be pure Python (no blocked imports). Every capstone must use a class with `__init__` and instance methods. All 17 capstone topics: `oop`, `fastapi`, `rag-vectors`, `python-devops`, `errors-testing`, `pydantic`, `async`, `langchain`, `langgraph`, `mcp`, `sql-http-git`, `llm-api-basics` (ChatSession), `structured-llm-outputs` (OutputValidator), `simple-rag-project` (MiniRAG), `simple-tool-calling` (ToolRegistry), `ai-evaluation` (EvalHarness), `ai-app-architecture` (SimpleAIApp).

### Runner Safety

`runner.py` applies two normalizations before comparing or serializing test results:

- `_safe(value)` — converts non-JSON-serializable values (sets, objects) to a truncated `repr` string instead of crashing `json.dumps` inside the subprocess.
- `_norm(value)` — recursively converts tuples to lists (and nested) so a function returning `(1, 2)` compares equal to `expected=[1, 2]`. This is intentional for a beginner platform; beginners routinely return tuples when lists are expected.

### Execution Tracer

`runner.py` also exposes `trace_user_code(code)` which runs the snippet under `sys.settrace` in a subprocess and returns a list of `{line, vars}` steps (max `MAX_TRACE_STEPS = 300`). Non-serializable values degrade to `repr`. Dangerous imports are blocked by the same AST scan used by the lab runner. The `/api/trace` endpoint in `app.py` is rate-limited and concurrency-capped identically to `/api/run`. The `/api/ai-coach` and `/api/ai-models` endpoints share an AI rate-limit bucket (10 requests per 60s per IP, separate from the 15/60s code-run limit). `/api/ai-models` returns `{"ok": false, "models": [], "error": "..."}` on 429; `/api/ai-coach` returns `{"ok": false, "reply": "..."}` on 429.

## AI Coach

The AI Coach supports:

- Ollama (local);
- LM Studio (local);
- OpenAI;
- Anthropic;
- Google AI Studio (free tier: `gemini-2.0-flash`, `gemini-2.0-flash-lite`);
- Grok (xAI) (free tier: `grok-3-mini`);
- Groq Cloud (free tier: `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`).

Google AI Studio uses a non-OpenAI API format (`system_instruction` / `contents` / `generationConfig`). Grok and Groq are OpenAI-compatible.

Each AI reply shows a stats line below the message content: model name, output token count, input token count, tok/s, and elapsed seconds. Ollama uses native `eval_duration` for accurate tok/s on CPU. Groq uses `usage.completion_time`. All others use server wall time.

Selecting any text on the page (except inside the code editor or input fields) shows a floating Ask AI button. The destination depends on context:
- **Inside the Try It popup**: answered inline in `#codePopupAiPanel` — code and current output are automatically included. No tab switch.
- **Inside the Visualizer**: answered inline in `#vizNote` — current step line, variables, and any error are automatically included.
- **Everywhere else**: navigates to the Labs tab and pre-fills the coach input.

The Try It popup has a dedicated "🤖 Ask AI" toolbar button that auto-sends a code-review question with the editor contents and output. The Visualizer has a "🤖 Ask AI" button in the controls row that auto-sends a step-explanation or error-explanation question. Both use `_callInlineAi()` → `askInlinePopup()` / `askInlineViz()` in `app.js`. The coach works without a loaded exercise in this mode — no code context is sent, just the topic and the question.

The AI coach has two prompt modes controlled by the `mode` field in the `/api/ai-coach` payload:
- `"chat"` — sent when the learner types their own question in the coach input box. The prompt contains only topic/lesson context and the question; exercise code and test results are omitted so the AI answers only what was asked.
- `"lab"` — sent when a preset button (e.g. "Explain my code") triggers the coach. The full prompt is used: exercise prompt, learner code, test results, and the 6-point structured response format.

The app should work without AI configured. Local tests and built-in feedback should remain useful even when no provider is connected.

API keys must stay in the browser session and should not be committed to files.

## Security Notes

The app currently binds to localhost. Keep it local by default.

### Origin validation

`app.py` validates the `Origin` header on every POST using `_is_allowed_origin(origin, HOST, PORT)`. This function parses the origin as a URL and requires an exact match of scheme (`http`), hostname (`127.0.0.1`), and port (`8765` or whatever `PY_SKILL_LAB_PORT` is set to). A missing `Origin` header is allowed (same-origin or non-browser client). Any other origin — including prefix-matching domains like `http://127.0.0.1.evil.com` — is rejected with 403.

Do not replace this check with a `startswith()` string comparison. That pattern was the previous bug.

Tests: `tests/test_origin_validation.py` covers exact match, empty origin, hostile prefix domain, wrong port, default port 80, external domain, https, null origin string, and malformed input.

### Code execution

The runner applies two layers of blocking:
1. **AST scan** — rejects dangerous imports (`os`, `subprocess`, `socket`, etc.), dangerous builtins (`exec`, `eval`, `__import__`, etc.), `open()`, `input()`, and direct `__builtins__` name access (the subscript bypass `__builtins__['__import__']('os')` and attribute variants).
2. **Runtime restriction** — injects a stripped `__builtins__` dict into `USER_GLOBALS` for both run and trace subprocess harnesses, removing `eval`, `exec`, `compile`, `breakpoint`, `open`, `input`, `globals`, `locals`, `vars`, `getattr`, `setattr`, and `delattr`. This closes bypass paths that might survive the AST scan.

`input()` is blocked before execution because the subprocess is non-interactive; a waiting `input()` call would silently time out, which looks like an infinite loop. HTTP request bodies are capped at 100 KB before JSON parsing (`MAX_REQUEST_BODY_BYTES` in `app.py`).

Do not expose this app to a network or multiple users without reviewing:

- code execution isolation;
- file I/O restrictions;
- process limits;
- network restrictions;
- authentication;
- API key handling;
- logging and audit behavior.

## Contributor Rules

- Keep changes scoped to the user's request.
- Treat `content/` as the authored source of truth for curriculum work.
- Keep legacy `curriculum.py`, `exercises.py`, and `practice_tests.py` aligned only until full migration cleanup is complete.
- Use `PY_SKILL_LAB_STRICT_CONTENT=1` during release checks to fail startup when validation warnings exist.
- Do not replace the current UI language casually.
- Do not remove official citations when editing lessons.
- Do not weaken local AI plus API-provider support.
- Do not commit API keys, local secrets, generated caches, or `.pytest_cache`.
- Restart the local server after changing Python content modules if browser verification is needed.
- Run tests before reporting that code/content changes are complete.
- When editing lesson content: if you update `lesson_sections` in `topic.json`, update `lesson.md` to match — section count and titles must stay in sync. The test `tests/test_content_drift.py` enforces this and will fail if they drift.
- The vendor bundle and fonts are committed so the app works offline without Node.js. Rebuild only when upgrading CodeMirror or fonts, then commit the rebuilt files.
