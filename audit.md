# Python Skill Lab Audit

Audit date: 2026-05-26  
Auditor stance: solution architecture, curriculum quality, and learning-platform readiness  
Scope reviewed: `app.py`, `curriculum.py`, `exercises.py`, `practice_tests.py`, `models.py`, `runner.py`, `ai_coach.py`, `static/index.html`, `static/app.js`, and tests.

## Executive Verdict

The app shell is useful, but the curriculum is not yet good enough for a serious learning platform. It is closer to a prototype with one strong reference topic than a reliable official-doc-driven course.

The key problem is not that the curriculum is stored in Python. For a small prototype, Python dictionaries can work. The real problem is that the current content system has no durable content model, no source mapping, no objective coverage model, and weak validation. Tests pass, but they mostly prove that the data has fields and exercise solutions pass their own tests. They do not prove that the lessons teach the official concepts correctly or completely.

Python Basics is the only topic that currently resembles the desired standard. Most other topics are short summaries. They are not deep lessons.

## Verification Snapshot

Commands run:

```powershell
python -B -m pytest tests -q -p no:cacheprovider
```

Result:

```text
376 passed in 8.04s
```

Content coverage measured from the current tree:

| Topic | Labs | Questions | Lesson sections | Sourced sections | Lesson-section words |
|---|---:|---:|---:|---:|---:|
| python-basics | 5 | 8 | 6 | 6 | 359 |
| data-structures | 2 | 5 | 4 | 0 | 118 |
| functions | 2 | 5 | 4 | 0 | 111 |
| oop | 2 | 5 | 4 | 0 | 113 |
| errors-testing | 2 | 5 | 4 | 0 | 104 |
| fastapi | 2 | 5 | 4 | 0 | 91 |
| pydantic | 2 | 5 | 4 | 0 | 88 |
| async | 2 | 5 | 4 | 0 | 83 |
| langchain | 2 | 5 | 4 | 0 | 93 |
| langgraph | 2 | 5 | 4 | 0 | 82 |
| mcp | 2 | 5 | 4 | 0 | 80 |
| rag-vectors | 2 | 5 | 4 | 0 | 79 |
| python-devops | 2 | 5 | 4 | 0 | 80 |
| sql-http-git | 2 | 5 | 4 | 0 | 82 |

This confirms the product instruction problem directly: only Python Basics has 5 labs. Every other topic currently violates the stated "at least 5 labs per topic" direction.

## Official Source Review

Official docs sampled during this audit:

- Python Tutorial: https://docs.python.org/3/tutorial/index.html
- FastAPI Tutorial: https://fastapi.tiangolo.com/tutorial/
- Pydantic Models: https://docs.pydantic.dev/latest/concepts/models/
- LangChain Overview: https://docs.langchain.com/oss/python/langchain/overview
- LangGraph Overview: https://docs.langchain.com/oss/python/langgraph/overview
- MCP Architecture: https://modelcontextprotocol.io/docs/learn/architecture
- OpenAI Embeddings: https://platform.openai.com/docs/guides/embeddings

Important observations:

- Python official docs explicitly say the tutorial is for programmers new to Python, not beginners new to programming. This app must translate official docs into beginner teaching, not copy or lightly paraphrase them.
- Pydantic docs emphasize that "validation" guarantees the resulting model output conforms to types and constraints, not that raw input was already correct. The current Pydantic lesson does not teach this nuance.
- LangChain docs have shifted. `https://docs.langchain.com/oss/python` currently redirects to Deep Agents, not the LangChain overview. The app should use canonical links such as `https://docs.langchain.com/oss/python/langchain/overview`.
- LangGraph docs frame LangGraph as low-level orchestration for long-running, stateful agents with durable execution, streaming, human-in-the-loop, and persistence. The current topic mentions these ideas but does not teach how they fit together.
- MCP docs describe a host-client-server architecture: a host creates one MCP client per MCP server. The current MCP lesson compresses this too much and misses the host/client distinction.
- OpenAI embeddings docs have moved behind the current docs shell and redirect from `platform.openai.com` to `developers.openai.com`. Existing links may still work, but the content system needs link checking and canonical URL updates.

## Major Findings

### P0 - Curriculum Depth Is Not Production-Ready

Evidence:

- `curriculum.py` has a rich `python-basics` override with 6 sourced lesson sections.
- Every other topic has only 4 short lesson sections and zero `source_url` fields.
- Most non-Python-Basics lesson section totals are under 120 words for the whole lesson section set.

Impact:

Learners will get shallow definitions instead of instruction. This is especially risky for FastAPI, Pydantic, LangChain, LangGraph, MCP, RAG, and DevOps topics where wrong simplifications create bad engineering habits.

Required fix:

Treat Python Basics as the exemplar. Each topic needs:

- 6 to 10 lesson sections.
- Section-level official source references.
- Practical examples.
- Beginner mistakes.
- At least 5 labs.
- Practice questions mapped to lesson objectives.

### P0 - The Content Model Is Too Weak

Current state:

- `TOPICS`, `EXERCISES`, and `PRACTICE_TESTS` are plain Python lists.
- `DIRECTIONAL_OVERVIEWS` later mutates topics by ID in `_enrich_topics()`.
- The base topic and the override can disagree, and the override silently wins.

Impact:

This is hard to review, hard to author, and easy to break quietly. Junior devs will keep adding content where it is convenient instead of where it belongs.

Required fix:

Move authored curriculum out of hand-edited Python modules into a structured content directory, then load and validate it.

Recommended structure:

```text
content/
  manifest.json
  sources.json
  topics/
    python-basics/
      topic.json
      lesson.md
      labs.json
      practice.json
    fastapi/
      topic.json
      lesson.md
      labs.json
      practice.json
```

Python files should load, validate, and serve content. They should not be the authoring format.

### P0 - Tests Give False Confidence

Evidence:

- `tests/test_curriculum.py` only requires one docs link, one real-world note, at least 3 practice questions, and required fields.
- `tests/test_exercises.py` only requires at least 2 test cases per exercise.
- `models.py` startup validation warns only when practice tests have fewer than 3 questions, despite the app direction requiring broad concept coverage.

Impact:

The app can pass all tests while most topics remain shallow and under-labbed. This is exactly what is happening.

Required fix:

Add content quality gates:

- Minimum 5 labs per topic.
- Minimum 8 practice questions per topic, or one per learning objective, whichever is greater.
- Every lesson section must have at least one `source_ref`.
- Every practice question must map to one learning objective.
- Every lab must map to one or more learning objectives.
- Every source URL must be official or explicitly marked as non-official supplemental.
- CI should fail, not warn, when content violates the baseline.

### P1 - Official Sources Are Listed, Not Integrated

The UI supports section-level source links in `static/app.js`, but only Python Basics uses them. The rest of the curriculum mostly has a topic-level docs list.

Impact:

A learner cannot tell which official page supports a lesson section. A reviewer cannot verify whether a section is complete or accurate.

Required fix:

Create a source registry:

```json
{
  "python.tutorial.control_flow": {
    "title": "Python Tutorial: More Control Flow Tools",
    "url": "https://docs.python.org/3/tutorial/controlflow.html",
    "official": true,
    "checked_at": "2026-05-26"
  }
}
```

Then each lesson section should reference source IDs:

```json
{
  "id": "functions-default-arguments",
  "title": "Default Arguments and Shared State",
  "source_refs": ["python.tutorial.control_flow.defining_functions"],
  "objectives": ["functions.defaults", "functions.mutable_default_trap"]
}
```

### P1 - Topic Scope Is Uneven

Some topics are focused enough:

- Python Basics
- Functions
- OOP
- FastAPI
- Pydantic

Some topics are too broad for one beginner lesson:

- `sql-http-git` combines SQL, HTTP, Git, and Linux basics. That is four separate learning tracks.
- `rag-vectors` combines RAG, embeddings, vector databases, evaluation, citations, chunking, and retrieval debugging.
- `python-devops` teaches subprocess, pathlib, Docker, Ansible, config, logging, dry runs, idempotency, and operational safety.

Impact:

Broad topics produce shallow content and weak labs.

Required fix:

Split large topics or create submodules:

- HTTP Fundamentals
- SQL Basics
- Git Workflow
- Linux and Terminal Basics
- Embeddings
- Retrieval and RAG
- RAG Evaluation
- DevOps Scripting with Files and Config
- DevOps Command Execution Safety

### P1 - Labs Do Not Match the Claimed Platform Ambition

Current labs are mostly small function-return exercises. That is fine for Python basics, but insufficient for backend, DevOps, and AI engineering foundations.

Impact:

Learners will pass toy exercises without learning real workflows.

Required fix:

Introduce lab types:

- `function_lab`: current style, deterministic function tests.
- `debug_lab`: learner fixes broken code.
- `trace_lab`: learner predicts behavior or explains an error.
- `api_design_lab`: route/model/status-code exercises without needing a live FastAPI dependency.
- `simulation_lab`: DevOps or AI workflow using mocked files, command outputs, API responses, or document chunks.
- `capstone_lab`: multi-step lab at the end of a track.

Also fix the runner/content mismatch: the DevOps topic teaches `pathlib` and `subprocess`, but the runner blocks those modules. That is reasonable for safe function labs, but the curriculum needs non-runner simulations for those concepts.

### P1 - AI Coach Is Not Grounded in the Official Lesson Content

Current `build_ai_prompt()` includes topic title, exercise prompt, real-world notes, test results, and code. It does not include:

- Lesson sections.
- Official citations.
- Learning objectives.
- Source URLs.
- Current topic misconceptions.

Impact:

The AI Coach can answer in a way that drifts from the official-doc-based curriculum. This undermines the user's main requirement.

Required fix:

Build the AI prompt from the same content model:

- Include topic objectives.
- Include the active lesson section summary.
- Include source titles and URLs.
- Instruct the model to say when an answer is outside the local lesson.
- For hosted providers, never send full source documents by default; send curated section summaries and citations.

### P1 - Model Defaults and External Docs Need Freshness Checks

Hardcoded model defaults exist in both `ai_coach.py` and `static/app.js`.

Impact:

Models and official docs change. Hardcoded defaults will become stale, and stale model IDs create avoidable support issues.

Required fix:

Move provider defaults into one server-served config object. Add a test that backend and frontend defaults come from the same source. For official docs, add a `checked_at` field and a simple link-check command.

### P2 - Current UI Is Directionally Good, But It Hides Content Weakness

The warm notebook/study-lab UI direction is appropriate and should be preserved. The issue is not the visual shell; the issue is that the lesson content rendered inside it is too thin.

Recommended UI improvements after content migration:

- Show lesson objectives at the top of the topic.
- Show "Source" links per section consistently.
- Show lab difficulty and mapped objective.
- Show practice-test review by objective, not only score.
- Add progress states: not started, reading, lab passed, test passed, revisit.

## Recommended Content Architecture

### 1. Define a Real Schema

Minimum topic schema:

```json
{
  "id": "fastapi",
  "track": "Backend",
  "title": "FastAPI",
  "level": "Intermediate",
  "prerequisites": ["python-basics", "functions", "pydantic"],
  "outcomes": [],
  "objectives": [],
  "official_sources": [],
  "sections": [],
  "common_mistakes": [],
  "real_world": []
}
```

Minimum section schema:

```json
{
  "id": "request-lifecycle",
  "title": "Request Lifecycle",
  "body_md": "...",
  "source_refs": ["fastapi.tutorial.first_steps", "fastapi.tutorial.body"],
  "objectives": ["fastapi.request_lifecycle"],
  "examples": []
}
```

Minimum lab schema:

```json
{
  "id": "validate-ticket-payload",
  "topic_id": "pydantic",
  "type": "function_lab",
  "objectives": ["pydantic.model_validate", "pydantic.field_constraints"],
  "difficulty": "Beginner",
  "starter": "...",
  "tests": [],
  "hint": "...",
  "solution": "...",
  "explanation": "..."
}
```

Minimum practice question schema:

```json
{
  "id": "pydantic-validation-output",
  "objective": "pydantic.validation_output",
  "source_refs": ["pydantic.models.validation"],
  "question": "...",
  "options": [],
  "answer": 0,
  "explanation": "..."
}
```

### 2. Keep Runtime Dependency-Light

This project can stay dependency-light:

- Use JSON for metadata and labs.
- Use Markdown files for lesson bodies.
- Use Python dataclasses for loaded models.
- Add a strict `content_loader.py`.
- Add `tests/test_content_quality.py`.

Do not add a database yet. It is unnecessary for a local-first learning app.

### 3. Avoid Copying Official Docs Verbatim

The right approach is:

- Read official docs.
- Extract concepts and required facts.
- Write beginner-friendly original explanations.
- Link the exact official source.
- Include examples suited to this app's learning path.

This avoids copyright issues and gives learners a better explanation than raw docs.

## Topic-by-Topic Remediation Priorities

| Priority | Topic | Required work |
|---|---|---|
| P0 | data-structures | Expand from container summaries to official tutorial coverage: list methods, comprehensions, `del`, tuples/sequences, sets, dicts, looping techniques, comparison behavior. Add 3+ labs. |
| P0 | functions | Expand default args, keyword args, special parameters, docstrings, annotations, scope basics, return vs print. Add 3+ labs. |
| P0 | errors-testing | Expand exceptions, handling, raising, cleanup, assertions, unittest/pytest style, debugging tracebacks. Add 3+ labs. |
| P0 | fastapi | Teach path/query/body params, Pydantic request bodies, response models, dependencies, error handling, status codes, OpenAPI docs. Add API-design labs. |
| P0 | pydantic | Teach BaseModel, validation output guarantee, coercion, strictness, Field constraints, defaults vs optional, errors, serialization. Add validation labs. |
| P1 | langchain | Update canonical docs link. Teach models, messages, tools, agents, structured output, retrieval, tracing/evaluation, and when not to use an agent. |
| P1 | langgraph | Expand state, nodes, edges, conditional edges, checkpoints, durable execution, streaming, interrupts/human review, persistence. |
| P1 | mcp | Teach host vs client vs server, tools/resources/prompts, transports, discovery methods, permissions, and safe server design. |
| P1 | rag-vectors | Split or deepen: chunking, embeddings, vector search, metadata, reranking, citations, evaluation, failure analysis. |
| P1 | python-devops | Add simulation labs because runner blocks actual subprocess/pathlib usage. Teach safe command execution separately from toy functions. |
| P2 | sql-http-git | Split into separate topics or subtopics. Current combined scope is too large for one beginner module. |

## Recommended Implementation Plan

### Phase 1 - Stabilize Content Infrastructure

Deliverables:

- `content/` directory.
- `content_loader.py`.
- `content/sources.json`.
- JSON/Markdown schema.
- Migration of current content into the new structure without rewriting substance.
- Tests proving the API output remains compatible with the current UI.

Acceptance criteria:

- App still starts.
- `/api/curriculum` returns the same top-level shape expected by `static/app.js`.
- Existing 376 tests still pass.
- New content quality tests fail for known shallow topics until they are upgraded.

### Phase 2 - Add Real Quality Gates

Deliverables:

- `tests/test_content_quality.py`.
- Link/source validation.
- Objective coverage validation.
- Lab and question minimums.
- Section-source validation.

Acceptance criteria:

- Python Basics passes the new standard.
- Other topics are explicitly marked `quality_status: draft` until upgraded.
- Draft topics can exist, but production-ready claims cannot pass.

### Phase 3 - Upgrade Python Core

Upgrade in this order:

1. Data Structures
2. Functions
3. Errors, Debugging, and Testing
4. OOP
5. Async Python

Acceptance criteria per topic:

- 6+ lesson sections.
- 5+ labs.
- 8+ questions.
- Every objective has at least one lesson section and one assessment item.
- Official Python docs cited per section.

### Phase 4 - Upgrade Backend and AI Topics

Upgrade:

1. Pydantic
2. FastAPI
3. LangChain
4. LangGraph
5. MCP
6. RAG and embeddings

Acceptance criteria:

- Canonical official docs links.
- Practical workflow examples.
- Labs reflect real developer use, not only vocabulary.
- AI Coach prompt uses lesson objectives and citations.

### Phase 5 - Split Oversized Topics

Split `sql-http-git` and possibly `rag-vectors` into smaller modules.

Acceptance criteria:

- Each topic teaches one coherent skill area.
- Learners can complete each module in a focused session.
- Labs and practice tests map cleanly to objectives.

## Suggested Definition of Done for Any Topic

A topic is not done unless all of this is true:

- Has a clear beginner-friendly overview.
- Has 6 to 10 lesson sections.
- Every section has official source references.
- Has at least 5 labs.
- Has at least 8 practice questions.
- Labs include edge cases and beginner mistakes.
- Practice questions cover every major lesson concept.
- Explanations teach why the answer is right, not only what is right.
- AI Coach receives topic objectives and citation context.
- Tests pass.
- Source links were checked within the last 90 days.

## Bottom Line

Your juniors have built a useful local learning shell, but they have not built a strong curriculum system yet. The current app passes tests because the tests are too forgiving. The next fix should not be "add more text to `curriculum.py`." The next fix should be to create a proper content architecture with source mapping, objective coverage, and quality gates, then upgrade topics one by one using Python Basics as the reference standard.

---

## Follow-Up: Content Enrichment Pass (2026-05-27)

The P0 curriculum depth finding (shallow lesson sections) was addressed in a full content rewrite pass.

**What changed:**

- All 14 `content/topics/*/topic.json` files rewritten. Each topic now has 6 lesson sections following a consistent pattern: layman analogy → technical explanation → beginner code example → professional/production code example → key rules or traps.
- All 14 `content/topics/*/lesson.md` files rewritten to match the enriched `topic.json` content with full markdown formatting.
- `static/app.js` — added `renderLessonMarkdown()` function supporting code fences, inline code, bold, and paragraph breaks. `renderLessonSections()` now uses this renderer via `<div class="section-body">`.
- `static/styles.css` — added `.section-body`, `.lesson-code` styles for multi-paragraph lesson cards.
- `AGENTS.md` — updated "Current Content Status" to reflect all 14 topics at reference quality.

**Findings still open (not addressed in this pass):**

- Labs: most topics still have 2 labs (below the stated 5-lab minimum). Python Basics is the only topic at 5 labs.
- Practice questions: most topics still have 5 questions (below the stated 8-question minimum). Python Basics has 8.
- Content quality gates (test_content_quality.py) not yet implemented.
- AI Coach is still not grounded in lesson section content or objectives.
- Topic scope issues (sql-http-git, rag-vectors, python-devops being overly broad) are not resolved.
- Source registry (sources.json) exists but section-level `source_refs` with objective mapping not yet implemented.

**Next priority:** expand labs to 5+ per topic and practice questions to 8+ per topic, starting with the Python Core track.

---

## Follow-Up: Scratchpad, Popup, and Tone Pass (2026-05-28)

**What changed:**

**UI — Python Scratchpad:**
- `static/index.html` — added `#scratchpad` collapsible panel inside `#lessonSection` (after the study-grid). Dark editor with traffic-light header bar; starts collapsed; toggle by clicking the header.
- `static/app.js` — added `loadInScratchpad()`, `runScratchpad()` functions; scratchpad toggle/run/clear/Ctrl+Enter/Tab event handlers wired up.
- `static/styles.css` — added `.scratchpad`, `.scratchpad-header`, `.scratchpad-editor`, `.scratchpad-toolbar`, `.scratchpad-output` styles plus notebook theme overrides.
- Uses the existing `/api/run` endpoint with no `exercise_id` — zero new backend infrastructure.

**UI — "▶ Try it" code popup:**
- Every lesson code block now shows a `▶ Try it` button on hover (top-right corner of the block).
- Clicking opens a fixed-position overlay in the bottom-right of the viewport — page position is fully preserved, no scroll.
- `static/index.html` — added `#codePopup` element before `</body>`.
- `static/app.js` — added `openCodePopup()`, `closeCodePopup()`, `runCodePopup()` functions; Escape to close; Tab/Ctrl+Enter keyboard shortcuts.
- `static/styles.css` — added `.code-popup` and child styles plus notebook theme overrides.
- `renderLessonMarkdown()` updated to wrap code blocks in `.lesson-code-wrap` with the try-it button embedded as `data-code` attribute.

**Content — label removal:**
- Stripped `# Layman example:` and `# Professional example:` comment lines from all 14 `topic.json` lesson_sections and `lesson.md` files. Only one stray label existed (in `functions`); the rest were already clean.

**Content — tone refinement:**
- `python-basics/topic.json` intro rewritten: was a generic "most popular... reads like plain English" opener. Now opens with a concrete automation scenario, names the dynamic-typing tradeoff explicitly, previews exactly what the topic covers.
- `oop/topic.json` intro rewritten: was a soft "bundle the data and functions" framing. Now opens with a concrete failure scenario (disconnected functions as a codebase grows), explains what a class mechanically solves, and preserves the "when NOT to use it" nuance.
- 12 other topic intros reviewed and kept unchanged (already at the right register).

**Findings still open:**
- Labs and practice question counts unchanged (still below 5-lab / 8-question minimum for most topics).
- AI Coach grounding still not implemented.

