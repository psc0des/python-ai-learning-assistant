# Python Skill Lab

A local-first, beginner-focused learning app for Python, backend APIs, DevOps automation, and AI engineering. Runs entirely on `127.0.0.1` with no cloud dependencies required — fonts, editor, and all curriculum ship with the repo.

## Stack

- **Language:** Python 3.10+ (backend, runner, tests)
- **Frontend:** Vanilla JS + CSS (no framework, no build step for the app itself)
- **Code editor:** CodeMirror 6 — vendored as a pre-built ESM bundle at `static/vendor/codemirror-bundle.js` (rebuilt via `scripts/build.js` using esbuild + npm)
- **Fonts:** Inter + JetBrains Mono — vendored as woff2 files at `static/vendor/fonts/` (downloaded via `scripts/vendor_fonts.py`)
- **HTTP server:** `http.server.ThreadingHTTPServer` (stdlib only — no Flask, no FastAPI)
- **AI Coach:** OpenAI-compatible endpoints — Ollama, LM Studio, OpenAI, Anthropic, Google AI Studio, Grok (xAI), Groq Cloud, Azure AI Foundry
- **Testing:** pytest (no third-party packages required to run the app)
- **Vendor tooling (build-time only):** Node.js 18+, esbuild, npm — only needed to rebuild the CodeMirror bundle

## Key Commands

```powershell
# Run the app
python app.py

# Run full test suite (always do this before reporting changes complete)
python -B -m pytest tests -q -p no:cacheprovider

# Run lint
python -m ruff check --no-cache .

# Run just the security and content tests (fast check)
python -B -m pytest tests/test_origin_validation.py tests/test_content_drift.py -v

# Rebuild the CodeMirror vendor bundle (only after upgrading CodeMirror versions)
cd scripts
npm install
node build.js

# Refresh local fonts (only after font version changes)
python scripts/vendor_fonts.py

# Run with strict content validation (fails startup on any content warning)
$env:PY_SKILL_LAB_STRICT_CONTENT="1"; python app.py

# Run on a different port
$env:PY_SKILL_LAB_PORT="9000"; python app.py
```

## Architecture

```
Python_Learning_Assistant/
  app.py                  HTTP server, API routes, origin validation (_is_allowed_origin)
  content_loader.py       Structured curriculum loader from content/
  runner.py               Lab runner + execution tracer (sys.settrace, AST safety scan)
  ai_coach.py             AI provider integration (8 providers, fallback-safe)
  models.py               Request/response validation and startup content checks
  content/
    manifest.json         Topic order and schema metadata (21 topics)
    sources.json          Official source registry with checked_at dates
    topics/               One directory per topic:
      <topic-id>/
        topic.json        Structured topic data (intro, mental_model, lesson_sections, etc.)
        lesson.md         Full markdown lesson — MUST stay in sync with lesson_sections
        labs.json         List of coding lab objects
        practice.json     Practice test questions
  static/
    index.html            App shell — loads from /vendor/fonts.css and /codemirror-init.js
    app.js                All UI logic — topic rendering, labs, AI coach, visualizer
    styles.css            Warm notebook visual design
    codemirror-init.js    CodeMirror 6 setup — imports from /vendor/codemirror-bundle.js only
    favicon.svg
    vendor/
      codemirror-bundle.js  Pre-built ESM bundle (committed — rebuilt via scripts/build.js)
      fonts.css             @font-face declarations pointing to local woff2 files (committed)
      fonts/                Inter + JetBrains Mono woff2 files (committed)
  scripts/
    build.js              esbuild script → static/vendor/codemirror-bundle.js
    codemirror-entry.js   Re-exports all CodeMirror symbols used by codemirror-init.js
    package.json          npm manifest (esbuild + CodeMirror packages)
    vendor_fonts.py       Downloads font CSS + woff2 from Google Fonts into static/vendor/
  pyproject.toml          Ruff lint configuration
  .pre-commit-config.yaml Optional pre-commit hook configuration
  tests/
    test_runner.py              Lab runner and _safe()/_norm() normalization tests
    test_trace.py               Execution tracer tests
    test_content_loader.py      Content structure and loader tests
    test_content_quality.py     Quality gate (≥5 labs, ≥8 questions per reference topic, sources present)
    test_content_drift.py       Parity guard: lesson.md headings must match topic.json lesson_sections
    test_api_contract.py        API payload shape tests
    test_origin_validation.py   HTTP origin header security tests
    test_ai_prompt.py           AI coach prompt tests
    test_content_integrity.py   Topic metadata, practice test quality, and content validation tests
    test_lab_content.py         Lab/exercise field and solution-execution tests
    test_runtime_api.py         Live server smoke tests
    test_ai_models.py           AI model listing and local provider contract tests
  CLAUDE.md               This file — project rules for Claude
  AGENTS.md               Short agent orientation; CLAUDE.md remains authoritative
  README.md               Short project overview
  SETUP.md                Full setup, deployment, and AI provider notes
  .gitignore              Excludes __pycache__, scripts/node_modules, .env, etc.
```

## Security Rules

### Origin validation (P0 — do not weaken)

Every POST in `app.py` is protected by `_is_allowed_origin(origin, HOST, PORT)`. This function uses `urllib.parse.urlparse` and requires an **exact match** of scheme (`http`), hostname (`127.0.0.1` **or** `localhost`), and port (`8765` or configured port). An empty `Origin` header is allowed (same-origin browser request). Every other origin is rejected with 403.

**Never replace this with `startswith()`** — that was the previous security bug. A prefix match allows `http://127.0.0.1.evil.com` through.

Tests in `tests/test_origin_validation.py` cover: exact match, empty origin, localhost same port, localhost wrong port, hostile prefix domain, wrong port, default port 80, external domain, https scheme, null origin string, malformed input. All 11 must pass.

### Code runner

`runner.py` runs learner code in a subprocess with a short timeout. It applies two layers of blocking:
1. **AST scan** — rejects dangerous imports (`os`, `subprocess`, `socket`, etc.), dangerous builtins (`exec`, `eval`, `__import__`, etc.), `open()`, `input()`, and direct `__builtins__` name access (e.g. `__builtins__['__import__']('os')`).
2. **Runtime restriction** — injects a stripped `__builtins__` dict into `USER_GLOBALS` for both run and trace paths, removing `eval`, `exec`, `compile`, `breakpoint`, `open`, `input`, `globals`, `locals`, `vars`, `getattr`, `setattr`, and `delattr` so the restricted set is enforced even if the AST scan is bypassed.

Learner code cannot read or write files or prompt for keyboard input. This is a learning sandbox, not a production security boundary. **Do not expose this app to a network or multi-user environment.**

`input()` is blocked before execution because the subprocess is non-interactive — a blocked `input()` call would silently wait until the run timeout, which looks like an infinite loop to a beginner. The runner returns a clear targeted message instead. Labs should use function parameters and sample variables, not `input()`.

HTTP request bodies are capped at 100 KB (`MAX_REQUEST_BODY_BYTES` in `app.py`) before JSON parsing, so an oversized POST cannot consume memory before the runner's code-size check applies.

Two normalizations in the runner are intentional and must not be removed:
- `_safe(value)` — converts non-JSON-serializable values to `repr` strings rather than crashing
- `_norm(value)` — recursively converts tuples to lists so beginner code returning `(1, 2)` matches `expected=[1, 2]`

## Content Rules

### practice.json schema

Each question object uses `"answer"` (not `"correct_index"`) for the zero-based correct option index:

```json
{"question": "...", "options": ["A", "B", "C", "D"], "answer": 0, "explanation": "..."}
```

`tests/test_content_integrity.py` and `tests/test_content_quality.py` both read `q["answer"]`. Never use `correct_index`.

### Source of truth

`content/topics/` is the authoritative source for all curriculum. There is no
runtime fallback to legacy Python content modules; broken structured content
must fail fast and be fixed in `content/`.

### List fields must be JSON arrays

`real_world`, `must_know`, `common_traps`, `interview`, and `docs` in `topic.json`
**must be JSON arrays**, never a single string — the UI renders them through
`renderList()`/`.map()`, and a string crashes the entire topic render. `len()`
checks pass on strings, so type is enforced explicitly by
`tests/test_content_integrity.py::TestTopicFields::test_list_fields_are_lists`.
`renderList()` also coerces non-arrays defensively, but content must still be
correct. `must_know` and `interview` need ≥3 items (see quality bar).

### Section sync (enforced by test)

`topic.json` `lesson_sections` titles and `lesson.md` `##` headings **must match exactly** — same count, same order, same title text. `tests/test_content_drift.py` enforces this and will fail the suite if they drift. Whenever you edit one, update the other.

### Quality bar for reference topics

Every topic marked `quality_status: reference` must have:
- at least 5 labs (capstone labs count toward this)
- at least 8 practice questions
- `source_url` on every `lesson_sections` entry

`tests/test_content_quality.py` enforces this. Do not mark a topic `reference` until it passes.

### Capstone labs

Each topic has one capstone lab (`difficulty: "Advanced"`, `difficulty_order: 6`) that integrates multiple concepts into a class-based multi-method challenge. Capstone labs are added to `labs.json` only — no changes to `topic.json` or `lesson.md`. All code must be pure Python (no imports from `BLOCKED_MODULES`). Every capstone must use a class with `__init__` and instance methods — not bare functions — so it genuinely exercises the OOP and encapsulation patterns the curriculum teaches.

Topics with capstones: `oop` (TaskManager), `fastapi` (Request Router), `rag-vectors` (Mini RAG Pipeline), `python-devops` (Deployment Checker), `errors-testing` (Debug Report Builder), `pydantic` (Schema Validator), `async` (Task Scheduler), `langchain` (Prompt Pipeline), `langgraph` (State Graph Runner), `mcp` (Tool Registry), `sql-http-git` (HTTP Log Analyzer), `llm-api-basics` (ChatSession), `structured-llm-outputs` (OutputValidator), `simple-rag-project` (MiniRAG), `simple-tool-calling` (ToolRegistry), `ai-evaluation` (EvalHarness), `ai-app-architecture` (SimpleAIApp).

### Try-it buttons in lesson sections

A "▶ Try it" button appears in the UI only for code fences tagged ` ```python run `. Blocks without the `run` tag render as static code.

**Important:** The live app renders lessons from `topic.json` `lesson_sections[].body`, not from `lesson.md`. The `run` tag must be present in **both** the `lesson.md` fence AND the matching `topic.json` body string so the tag is visible to the renderer and to the test suite. When you add or remove a `run` tag, update both files.

Add `run` only when ALL of the following are true:
- All names called are defined within the block itself (no external object refs like `app`, `chain`, `graph`, `client`, `router`, `llm`)
- No third-party imports (fastapi, pydantic, langchain, langgraph, etc.)
- No `input()` or `open()` calls
- Not a traceback, bash, shell, sql, or diff block
- Top-level `async def` is only used if followed by `asyncio.run()`

Two tests enforce this:
- `test_lesson_run_blocks_execute_cleanly` — runs every `run`-tagged block in `lesson.md` through the runner and asserts zero stderr.
- `test_topic_json_run_blocks_execute_cleanly` — same check for `topic.json` body fields (the source the app actually renders).

If a block fails either test, remove the `run` tag from both files rather than patching the snippet.

### Content writing style

- Cite official docs (`source_label` / `source_url` on each section, `docs` list on the topic).
- One-sentence analogy opener → technical explanation → beginner code example → production code example. No inline `# Layman example:` labels — they were removed because they read awkwardly.
- Explain what happens when code runs. Avoid generic "this helps you understand X" motivation copy.
- Cover common beginner mistakes directly in `common_traps`.
- Keep interview language out of lesson sections unless the section is explicitly about interview readiness.

### SVG diagrams

Eight topics have an inline `diagram_svg` + `diagram_caption` in one `lesson_sections` entry: `getting-started`, `fastapi`, `rag-vectors`, `mcp`, `langgraph`, `langchain`, `ai-evaluation`, and `ai-app-architecture`. The SVG is trusted authored content and is **not** passed through `escapeHtml`. Locked palette: `#1e293b` charcoal (focal), `#059669` green (result), `#94a3b8` slate (borders), `#4a5568` gray (arrows), `#b45309` amber (data stores).

## UI Rules

Preserve the warm notebook/study-lab visual style. The plain white SaaS look was explicitly rejected.

Keep:
- warm paper background
- subtle grid texture
- restrained green accents
- dark active tab/button state
- compact learning workspace
- readable long-form lesson text

**Do not introduce:** generic dashboard chrome, purple gradients, oversized hero sections, marketing-page layouts, or dark mode (removed — caused inconsistent contrast).

Critical CSS invariants:
- `[hidden] { display: none }` overrides are required for both overlays — do not remove them
- `.code-popup` / `.code-popup-modal` sit at `z-index: 800`; `#vizOverlay` stays at `z-index: 1000`
- Both modals (`.viz-modal` and `.code-popup-modal`) use `position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%)` to self-center — do **not** add `display: flex` centering back to `.viz-overlay` or `.code-popup` (that fights the drag logic)
- `.viz-overlay` and `.code-popup` are plain backdrops with no flex — each modal positions itself and is draggable via JS mousedown on its header (`.viz-modal-head` / `.code-popup-header`)
- Escape key priority: viz overlay handles Escape first; code popup Escape is skipped while viz is open — do not break this ordering
- `.ai-settings-panel` is `position: fixed; z-index: 800; max-height: calc(100vh - 24px); overflow-y: auto`. JS opens it to the right of the sidebar (`rect.right + 8`) on wide viewports, reads `offsetHeight` after render, then clamps `top` so Save & Apply is never off-screen. On narrow viewports it opens above the button when there is room, otherwise below, and clamps both `top` and `left` so the panel stays within the viewport on all screen sizes. Do not revert to `width: rect.width` (the button width) — that was the original bug that caused the panel to overlap the sidebar topic list. Do not revert to `bottom`-based positioning for the narrow fallback — that caused the panel to go above the viewport on mobile.
- Topic search in `renderTopicList` scores matches: title/track hits rank above intro-only hits. Do not flatten this back to a single `haystack` string — that caused unrelated topics to appear ahead of direct title matches.
- The Show Solution gate requires 2 failed attempts before revealing the solution. When blocked, the gate message is shown on the button itself (temporary text change + `disabled` for 2.5 s) — do not move the message to the AI Coach panel, which is too far from the blocked action to be useful.
- Practice tests can be retaken. Readiness uses the latest submitted attempt, not the first attempt. `practiceHash` must represent the full current question set (question text, options, answer, explanation), so score state is invalidated when content changes.
- Do not reintroduce the old top-level readiness/progress bar without a fresh UX design pass. Learner progress should stay lightweight in sidebar badges unless the progress model is made clearer.
- Keep AI help split into two surfaces: embedded Labs `AI Coach` (`#aiOutput`, `#coachInput`, `#coachStatus`) for exercise/test coaching, and floating bottom-right `Ask AI` (`#askAiDock`) for selected text, lesson Ask AI, Try It Ask AI, Visualizer Ask AI, and independent chat. Do not merge these surfaces or reuse the lab coach IDs in the floating messenger. The floating Ask AI sits above popups and the visualizer (`z-index: 1100`), so Escape closes Ask AI before closing the underlying surface when both are open.
- Freeform floating Ask AI chat must stay independent: do not send `selectedTopicId` unless the learner used a contextual action such as lesson Ask AI, selected text, Try It Ask AI, or Visualizer Ask AI.
- Floating Ask AI freeform history must not include previous contextual snippets, Try It code/output, or Visualizer state. Compute chat history before appending the current user message so the current question is not duplicated in both `chat_history` and `question`.
- Floating Ask AI close only hides the messenger; `New chat` resets `askAiMessages` so learners can intentionally start fresh after changing models or context.
- Keep AI Settings split by learner intent: Ollama/LM Studio expose **Show local models** for installed-model inventory and **Test selected model** for an actual reply check; hosted/API providers expose **Verify provider** for the configured key/model. Do not show model counts as a generic "Connected" state.
- Treat AI Settings as draft until the learner clicks **Save & Apply** or a provider/model test succeeds. Do not persist provider/model changes from boot, provider switching, model listing, or ordinary AI chat.
- `.env` is auto-loaded before `ai_coach` is imported so server-side provider keys, selected provider/model/endpoint, and timeout constants survive app restarts. Shell environment variables still take priority. AI Settings uses `/api/ai-settings` to save non-secret provider state plus an optional newly typed key; `/api/ai-settings` GET may return `key_present` but must never return the key itself. Verify provider must save a newly typed key before making the verification request so a stale `.env` key cannot override it. Never log, echo, or commit secret values.
- Verify provider is a health check, not a normal coaching request: send `purpose: "provider_test"` with a tiny answer cap (`max_tokens: 64`) and the short hosted timeout from `PY_SKILL_LAB_AI_PROVIDER_TEST_TIMEOUT_SECONDS` so hosted preview models do not burn the full learner-chat budget just to confirm connectivity.
- AI chat should feel live: route AI Coach and floating Ask AI messages through `/api/ai-coach-stream` so supported providers stream chunks into the transcript. Keep `/api/ai-coach` as the fallback JSON route, not as the default frontend chat path.
- AI Coach and Ask AI streams use generation counters (`coachStreamGen`, `askAiStreamGen`) to prevent a late chunk from a previous request landing in a new conversation. `selectExercise()` and `startNewAskAiChat()` increment the counter for the surface they reset; `askLabCoach()`/`askFloatingAi()` capture the counter at call start (`const generation = ++coachStreamGen` / `++askAiStreamGen`) and bail out of `onChunk`, the post-stream success path, and the `catch` block if the counter has since changed. Do not remove these guards or write streamed text into `coachMessages`/`askAiMessages` without checking `generation` first — `coachMessages`/`askAiMessages` are reassigned on reset, and an unguarded async callback can append a stray message into the new array.
- AI is optional and not configured out of the box (the default provider is local Ollama, which a first-time learner usually has not installed). The unconfigured paths must stay actionable, not dead ends: `ai_coach.NO_LOCAL_MODEL_HINT` and the local "connection refused" branch of `friendly_provider_error` both point the learner to ⚙ AI Settings and the no-install hosted route (paste an API key). `maybeShowAiOnboarding()` shows one dismissible first-run banner (`.ai-onboard-nudge`, reusing `.review-nudge` styling) when `isAiConfigured()` is false, gated by the `pySkillLabAiOnboarded` localStorage flag so it never nags. Tests: `tests/test_ai_onboarding.py`.
- `boot()` is wrapped in try/catch: a curriculum load failure calls `showBootError()` to render a plain-language `.boot-error` panel instead of leaving a blank workspace. Do not remove this guard.
- Chat responses (Coach + Ask AI) render through `renderMarkdown()`, a block-level parser: code fences, ATX headings (`#`–`######` → `.md-h`), unordered/ordered lists, and paragraphs that **join soft-wrapped lines with a space** (`_renderTextBlock` / `_inlineMarkdown`). Do not revert to the old `\n`→`<br>` substitution — small local models emit many newlines and that produced the "disoriented" one-fragment-per-line transcript. `stripThinkTags()` runs first as defense-in-depth so reasoning-model `<think>…</think>` (closed or unclosed) can never reach the transcript. Server-side, `_ThinkFilter` must be applied on **every** reasoning-capable path, not just LM Studio: hosted streaming (`stream_openai_compatible` is called with `filter_thinking=True` for openai/grok/groq/azure-foundry) and the non-streaming `call_openai_compatible` both strip `<think>` — needed because hosted reasoning models like Groq `qwen3-32b` emit it inline in content. Tests: `tests/test_chat_rendering.py`, `tests/test_ai_models.py`.
- Lesson bodies render through `renderLessonMarkdown()` (separate from chat — it adds Try-it buttons on runnable code fences). It also parses bullet/numbered lists into `<ul>/<ol>` (`.lesson-list`); without that, `- item` lines collapse into one run-on paragraph. Lesson bodies use list markers but not ATX headings (sections carry their own titles).
- The floating Ask AI panel has minimize/maximize/close window controls (`#askAiMinimize`, `#askAiMaximize`, `#askAiClose`). Minimize and close both collapse to the launcher bubble keeping the conversation; `toggleAskAiMaximize()` toggles `.ask-ai-panel.maximized` (wider/taller for long answers). `startNewAskAiChat()` resets to the welcome message and signals a clear fresh start ("New chat started", scroll to top) — keep the `askAiMessages = [{ role: "assistant", text: ASK_AI_WELCOME_MESSAGE }]` reset line intact for the stream-generation guard.

## Vendor Bundle Rules

The pre-built vendor files (`static/vendor/`) are committed to the repo so the app works offline without Node.js. Rebuild them only when upgrading CodeMirror or font versions, then commit the rebuilt files.

`codemirror-init.js` imports all CodeMirror symbols from `/vendor/codemirror-bundle.js` only — never from `esm.sh` or any other CDN. If the bundle is unavailable the plain `<textarea>` gracefully degrades.

`scripts/node_modules/` is gitignored. `scripts/package-lock.json` is gitignored.

## Doc Sync Rule (mandatory)

Every code or content change must be accompanied by doc updates in the same commit. Never commit code first and sync docs afterward.

### Always check when making changes

- `CLAUDE.md` — when project rules, architecture, or security decisions change
- `AGENTS.md` — only when the short orientation or CLAUDE.md handoff changes
- `SETUP.md` — when project structure, requirements, or setup steps change
- `README.md` — when major features or the offline/local-first story changes

### Update when relevant (the specific thing changed)

- `tests/` — when adding features, always add or update tests to cover the new behavior
- `content/topics/<id>/lesson.md` — whenever `lesson_sections` in `topic.json` changes
- `static/vendor/` — whenever CodeMirror or font versions are bumped (commit rebuilt files)

## Commit Message Format

- **One line only** — no multi-line body, no bullet points
- Format: `type: short description (under 72 chars)`
- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `security`
- Examples:
  - `security: fix origin validation — parse URL instead of startswith`
  - `feat: add execution visualizer with per-step stdout`
  - `test: add HTTP origin validation and content drift tests`
  - `chore: vendor CodeMirror 6 and fonts for offline use`
  - `docs: update SETUP and AGENTS for vendor bundle setup`

## Git Identity

- GitHub username: **psc0des**
- Git author name: `psc0des`
- Git author email: `sarathy.vass6@gmail.com`
- Before the first commit in any session, verify:
  ```bash
  git config user.name   # must be psc0des
  git config user.email  # must be sarathy.vass6@gmail.com
  ```
- If either is wrong, set before committing:
  ```bash
  git config --global user.name "psc0des"
  git config --global user.email "sarathy.vass6@gmail.com"
  ```

## Workflow Principles

### 1. Tests before done

Run `python -B -m pytest tests -q -p no:cacheprovider` before reporting any task complete. Do not ship a regression.

Run `python -m ruff check --no-cache .` before reporting Python code or CI/tooling changes complete.

### 2. No CDN drift

The app must work offline after cloning. Every external resource (fonts, JS libraries) must be vendored in `static/vendor/`. No new `<link href="https://...">` or `import ... from "https://..."` lines in committed code.

### 3. Content and code together

When a content change also affects tests (new sections, new topics, structural changes), update the tests in the same PR/commit. Do not leave tests in a failing state as a follow-up.

### 4. Scope discipline

Do not add features, refactor, or introduce abstractions beyond what the task requires. A bug fix does not need surrounding cleanup. No half-finished implementations.

### 5. Security is load-bearing

The origin validation check, the AST safety scan, and the rate limiter are not optional. Do not weaken them as a shortcut or side effect of other changes. The rate limiter covers three independent buckets: code-execution (`/api/run`, `/api/trace` — 15 req/60s per IP), AI coach (`/api/ai-coach` — 10 req/60s per IP), and model-list (`/api/ai-models` — 30 req/60s per IP).

### 6. Verify before reporting

For UI changes: start the dev server (`python app.py`) and test the golden path in a browser. Type-checking and tests verify code correctness — they do not verify feature correctness.

## Core Principles

- **Beginner-first**: the primary user has never written code. Every content and UX decision should serve that person first.
- **Local-first**: the app works fully offline after setup. No cloud services required to learn or practice.
- **Simplicity**: stdlib over frameworks. Minimal impact per change. No premature abstractions.
- **Honest quality**: tests passing does not mean content is good. Teaching quality requires human review.

## AGENTS.md Relationship

`CLAUDE.md` is the authoritative project instruction file. `AGENTS.md` is a
short compatibility/orientation file that points back here. Do not duplicate
large architecture, content, UI, or security sections into `AGENTS.md`; update
this file first, then adjust the short pointer only if needed.
