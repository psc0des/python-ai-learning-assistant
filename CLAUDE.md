# Python Skill Lab

A local-first, beginner-focused learning app for Python, backend APIs, DevOps automation, and AI engineering. Runs entirely on `127.0.0.1` with no cloud dependencies required — fonts, editor, and all curriculum ship with the repo.

## Stack

- **Language:** Python 3.10+ (backend, runner, tests)
- **Frontend:** Vanilla JS + CSS (no framework, no build step for the app itself)
- **Code editor:** CodeMirror 6 — vendored as a pre-built ESM bundle at `static/vendor/codemirror-bundle.js` (rebuilt via `scripts/build.js` using esbuild + npm)
- **Fonts:** Inter + JetBrains Mono — vendored as woff2 files at `static/vendor/fonts/` (downloaded via `scripts/vendor_fonts.py`)
- **HTTP server:** `http.server.ThreadingHTTPServer` (stdlib only — no Flask, no FastAPI)
- **AI Coach:** OpenAI-compatible endpoints — Ollama, LM Studio, OpenAI, Anthropic, Google AI Studio, Grok (xAI), Groq Cloud
- **Testing:** pytest (no third-party packages required to run the app)
- **Vendor tooling (build-time only):** Node.js 18+, esbuild, npm — only needed to rebuild the CodeMirror bundle

## Key Commands

```powershell
# Run the app
python app.py

# Run full test suite (always do this before reporting changes complete)
python -B -m pytest tests -q -p no:cacheprovider

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
  ai_coach.py             AI provider integration (7 providers, fallback-safe)
  models.py               Request/response validation and startup content checks
  curriculum.py           Legacy topic metadata (fallback only — do not add to)
  exercises.py            Legacy coding labs (fallback only — do not add to)
  practice_tests.py       Legacy practice tests (fallback only — do not add to)
  content/
    manifest.json         Topic order and schema metadata (15 topics)
    sources.json          Official source registry with checked_at dates
    topics/               One directory per topic:
      <topic-id>/
        topic.json        Structured topic data (intro, mental_model, lesson_sections, etc.)
        lesson.md         Full markdown lesson — MUST stay in sync with lesson_sections
        labs.json         List of coding lab objects
        practice.json     Practice test questions
  static/
    index.html            App shell — loads from /vendor/fonts.css and /codemirror-init.js
    app.js                All UI logic (~1429 lines) — topic rendering, labs, AI coach, visualizer
    styles.css            Warm notebook visual design (~2137 lines)
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
  tests/
    test_runner.py              Lab runner and _safe()/_norm() normalization tests
    test_trace.py               Execution tracer tests
    test_content_loader.py      Content structure and loader tests
    test_content_quality.py     Quality gate (≥5 labs, ≥8 questions per reference topic, sources present)
    test_content_drift.py       Parity guard: lesson.md headings must match topic.json lesson_sections
    test_api_contract.py        API payload shape tests
    test_origin_validation.py   HTTP origin header security tests
    test_ai_prompt.py           AI coach prompt tests
    test_curriculum.py          Curriculum metadata tests
    test_exercises.py           Exercise structure tests
    test_runtime_api.py         Live server smoke tests
    test_ai_models.py           AI model listing and local provider contract tests
  CLAUDE.md               This file — project rules for Claude
  AGENTS.md               Contributor instructions and architectural notes
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

`runner.py` runs learner code in a subprocess with a short timeout. It uses an AST scan to block dangerous imports (`os`, `subprocess`, `socket`, etc.), dangerous builtins (`exec`, `eval`, `__import__`, etc.), `open()` entirely, and `input()` — learner code cannot read or write files or prompt for keyboard input. This is a learning sandbox, not a production security boundary. **Do not expose this app to a network or multi-user environment.**

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

`tests/test_curriculum.py` and `tests/test_content_quality.py` both read `q["answer"]`. Never use `correct_index`.

### Source of truth

`content/topics/` is the authoritative source for all curriculum. The legacy `curriculum.py`, `exercises.py`, `practice_tests.py` files exist only as fallback — do not add content to them.

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

Topics with capstones: `oop` (TaskManager), `fastapi` (Request Router), `rag-vectors` (Mini RAG Pipeline), `python-devops` (Deployment Checker), `errors-testing` (Debug Report Builder), `pydantic` (Schema Validator), `async` (Task Scheduler), `langchain` (Prompt Pipeline), `langgraph` (State Graph Runner), `mcp` (Tool Registry), `sql-http-git` (HTTP Log Analyzer).

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

Six topics have an inline `diagram_svg` + `diagram_caption` in one `lesson_sections` entry. The SVG is trusted authored content and is **not** passed through `escapeHtml`. Locked palette: `#1e293b` charcoal (focal), `#059669` green (result), `#94a3b8` slate (borders), `#4a5568` gray (arrows), `#b45309` amber (data stores).

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

## Vendor Bundle Rules

The pre-built vendor files (`static/vendor/`) are committed to the repo so the app works offline without Node.js. Rebuild them only when upgrading CodeMirror or font versions, then commit the rebuilt files.

`codemirror-init.js` imports all CodeMirror symbols from `/vendor/codemirror-bundle.js` only — never from `esm.sh` or any other CDN. If the bundle is unavailable the plain `<textarea>` gracefully degrades.

`scripts/node_modules/` is gitignored. `scripts/package-lock.json` is gitignored.

## Doc Sync Rule (mandatory)

Every code or content change must be accompanied by doc updates in the same commit. Never commit code first and sync docs afterward.

### Always check when making changes

- `CLAUDE.md` — when project rules, architecture, or security decisions change
- `AGENTS.md` — when main files, security model, or contributor rules change
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

Run `python -B -m pytest tests -q -p no:cacheprovider` before reporting any task complete. The current baseline is 795 tests passing. Do not ship a regression.

### 2. No CDN drift

The app must work offline after cloning. Every external resource (fonts, JS libraries) must be vendored in `static/vendor/`. No new `<link href="https://...">` or `import ... from "https://..."` lines in committed code.

### 3. Content and code together

When a content change also affects tests (new sections, new topics, structural changes), update the tests in the same PR/commit. Do not leave tests in a failing state as a follow-up.

### 4. Scope discipline

Do not add features, refactor, or introduce abstractions beyond what the task requires. A bug fix does not need surrounding cleanup. No half-finished implementations.

### 5. Security is load-bearing

The origin validation check, the AST safety scan, and the rate limiter are not optional. Do not weaken them as a shortcut or side effect of other changes. The rate limiter covers two independent buckets: code-execution (`/api/run`, `/api/trace` — 15 req/60s per IP) and AI coach (`/api/ai-coach` — 10 req/60s per IP).

### 6. Verify before reporting

For UI changes: start the dev server (`python app.py`) and test the golden path in a browser. Type-checking and tests verify code correctness — they do not verify feature correctness.

## Core Principles

- **Beginner-first**: the primary user has never written code. Every content and UX decision should serve that person first.
- **Local-first**: the app works fully offline after setup. No cloud services required to learn or practice.
- **Simplicity**: stdlib over frameworks. Minimal impact per change. No premature abstractions.
- **Honest quality**: tests passing does not mean content is good. Teaching quality requires human review.
