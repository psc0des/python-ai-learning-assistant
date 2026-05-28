# Implementation Plan v2

**Date:** 2026-05-28
**Companion to:** `ai_audit_v2.md` (the audit that found these items)
**Owner decisions captured:** ship to GitHub for local download; audience = complete beginners; add a beginner on-ramp; build concept diagrams for the topics where flow matters.

This document tracks the concrete follow-up work after the v2 audit. It has three parts:
1. **Done in this pass** — what was implemented and verified.
2. **P1 runner fixes** — the two latent bugs, with exact change locations and acceptance tests.
3. **Concept-diagram plan** — what to draw, where, and how to ship it dependency-free.

---

## Part 1 — Done in this pass (implemented + verified)

### 1.1 README safety + audience framing
**File:** `README.md`
- Added a bold **"Run this on your own machine only"** warning explaining the runner is not a security sandbox and must never be hosted multi-user/public. This is the cheap insurance that keeps the bypassable-denylist finding (audit P2) safe.
- Added a **"Who This Is For"** section that routes complete beginners to the new on-ramp, language-switchers to Python Basics, and AI-track learners through the backend/AI topics.

### 1.2 Beginner on-ramp topic
**New files:** `content/topics/getting-started/{topic.json, lesson.md, labs.json, practice.json}`
**Edited:** `content/manifest.json` (added `getting-started` as the **first** topic).

A true-zero-knowledge topic, **Getting Started: Coding From Zero**, built to the same `reference` quality bar as every other topic:
- 6 lesson sections, **every section sourced** to official `docs.python.org` tutorial pages.
- 5 labs (gentle, function-based so the runner can test return values): `say_hello`, `add`, `greet`, `is_even`, `describe_number`.
- 8 practice questions with explanations.

Sections cover, for someone who has never coded: what code is and how to run it → `print()` → variables → the three first types (text / numbers / True-False) → `if`/`else` → a first function + **how to read an error message without panicking**.

**Verified:**
- Content loads in `structured` mode; topic count 14 → **15**, on-ramp is first.
- All 5 lab solutions pass their own tests; **no** starter passes without work.
- All 8 questions have valid answer indices and explanations.

### 1.3 Relaxed obsolete legacy-parity tests
**File:** `tests/test_content_loader.py`
The two tests that forced structured content to be an **exact mirror** of the deprecated `curriculum.py` snapshot were blocking any new topic. They were rewritten to assert structured content is a **superset** of the legacy baseline (`>=` and subset checks) instead of exact equality. This is correct now that `mode` is always `structured` and the legacy modules are a fallback only. No application code changed; no new content was forced into the deprecated modules.

> **Note on the legacy modules:** `curriculum.py`, `exercises.py`, `practice_tests.py` are now dead weight (only used if `content/manifest.json` disappears). A future cleanup could delete them and the fallback path entirely. Left in place for now to keep the change small.

---

## Part 2 — P1 runner fixes (next sprint, not yet implemented)

Both bugs live in `runner.py` and are **latent** — no current lab triggers them (all 75 lab solutions pass). They matter because a *learner's own* code can trigger them, producing a confusing internal error instead of a clean result. Keep them off the critical path for launch, but fix them early.

### 2.1 Non-serializable return value crashes the test harness — FIXED (2026-05-28)
**Status: closed.** `build_test_code()` now wraps `actual` through a `_safe()` helper (keeps JSON-serializable values, otherwise a truncated `repr`) and computes `passed` defensively. A `set`/object return now yields a clean failed test instead of crashing the harness. Regression test: `tests/test_runner.py::TestNonSerializableReturn`.

<details><summary>Original finding (for history)</summary>

**Where:** `runner.py`, `build_test_code()` — the per-test result dict stores the raw `actual` value, then the whole list is `json.dumps(...)`-ed at the end. If `actual` is a `set`, a custom object, or anything non-JSON-serializable, `json.dumps` throws **inside the subprocess**, the result marker never prints, `parse_test_results()` returns `[]`, and the learner sees zero tests plus a leaked `"<string>", line N` traceback.

**Fix direction:** make the value safe to serialize before it goes into the results list. In the subprocess template, replace the raw `actual` capture with a serialization-safe form, e.g.:

```python
def _safe(value):
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return repr(value)
```

Use `_safe(actual)` (and `_safe(expected)` for symmetry) when building each result dict. Result: an exotic return value degrades to a **failed test with a readable `repr`**, never a crash.

**Acceptance test (add to `tests/test_runner.py`):**
- A function returning `{1, 2, 3}` against `expected=[1,2,3]` yields one test result with `passed=False` and a non-empty `actual`, and `tests` is **not** empty.
- No traceback text leaks into `stderr` for that case.

</details>

### 2.2 Tuple return can never equal a JSON list
**Where:** `runner.py`, `build_test_code()` — comparison is `actual == expected`. `expected` is loaded from JSON, which has no tuple type, so a tuple-returning solution compares unequal to its list `expected` (`(1,2) == [1,2]` is `False`).

**Fix direction (pick one):**
- **(a) Normalize before compare** in the subprocess: recursively convert tuples↔lists on both sides before `==`. Lowest friction for authors; slight risk of hiding a genuine list-vs-tuple distinction (acceptable for a beginner platform).
- **(b) Document + lint:** state "labs must return JSON-expressible types (no tuples/sets)" and add a content test that flags tuple/set literals in `expected`. Keeps comparisons strict.

**Recommendation:** (a) for learner-friendliness, since beginners routinely return tuples without realizing the distinction.

**Acceptance test:** a function returning `(1, 2)` against `expected=[1, 2]` reports `passed=True`.

### 2.3 (Optional, P3) De-risk the "sandbox" wording
Either rename `scan_for_dangerous_code` messaging away from "sandbox" or keep the README localhost-only rule as the primary control (done in 1.1). No code change required for launch.

---

## Part 3 — Concept-diagram plan

> **Status update (2026-05-28): hybrid approach agreed + all phases shipped.**
> Decision matrix: **structural** concepts ("how parts connect") use static SVG; **execution** concepts ("how code runs / values change") use a Python-Tutor-style execution visualizer.
> - **Phase A (DONE):** static SVG diagrams shipped for `getting-started` (function), `fastapi` (request lifecycle), `rag-vectors` (pipeline), `mcp` (host/client/server), `langgraph` (state graph), `langchain` (agent loop). **Richer versions applied 2026-05-28** — example data at each stage, annotated notes below each diagram. Mechanism: optional `diagram_svg` + `diagram_caption` fields on a lesson section, rendered as a trusted inline `<figure>` (`renderLessonSections` in `static/app.js`; `.section-diagram` in `styles.css`, transparent container). **Locked palette:** charcoal `#1e293b` = focal/your-code box; green `#059669` = result/output; white boxes with slate `#94a3b8` borders; gray `#4a5568` arrows; muted `#718096` sublabels; amber `#b45309` = data stores. No cool/indigo fills (they clash with the warm notebook theme).
> - **Phase B (DONE):** execution visualizer shipped — see 3.5 below.


**Principle:** diagrams earn their place only where **flow** is the hard part. For true beginners, a picture of "variables" adds nothing over a sticky-note sentence + a code example. For a request lifecycle or a retrieval pipeline, a picture beats three paragraphs. So we draw selectively, not for all 15 topics.

### 3.1 Where diagrams add real value (build these)
| Topic | Diagram | Why it helps |
|---|---|---|
| fastapi | Request → routing → validation → handler → response | The lifecycle is the mental model learners miss |
| rag-vectors | Document → chunk → embed → store → retrieve → generate | The pipeline is inherently a flow |
| mcp | Host ↔ Client ↔ Server (one client per server) | The 3-role separation is spatial |
| langgraph | State machine: nodes, edges, conditional edges, checkpoint | It literally *is* a graph |
| langchain | Prompt → model → tool-call loop → structured output | The agent loop is a cycle |
| getting-started | One simple "input → process → return" picture for a function | The single visual a beginner benefits from |

### 3.2 Where to skip
data-structures, functions, oop, errors-testing, async, pydantic, python-basics, python-devops, sql-http-git — text + code examples are clearer than a diagram for these. (Async could get one later if learners struggle with the event-loop concept.)

### 3.3 How to ship them dependency-free
The app is intentionally dependency-light and renders lesson bodies through a small markdown renderer (`renderLessonMarkdown` in `static/app.js`). Recommended approach, in order of preference:

1. **Inline SVG** stored per section. Add an optional `diagram_svg` (or `diagram_path`) field to a lesson section; render it inside `.section-body`. SVG is text, versionable, scales crisply, needs no library, and `escapeHtml` does not apply (it is trusted authored content — sanitize at author time, never from user/AI input).
2. **Fallback: a labeled ASCII/box diagram** inside a code fence — zero new rendering code, works today. Good for a first cut.

**Authoring note:** these diagrams can be produced with the `excalidraw-diagram` skill (hand-drawn style, exports SVG) and dropped into the topic. Keep each diagram to one idea; a busy diagram is worse than none for a beginner.

### 3.4 Suggested order
1. `getting-started` function picture (smallest, validates the rendering approach).
2. `fastapi` request lifecycle.
3. `rag-vectors` pipeline.
4. `mcp` roles, `langgraph` graph, `langchain` loop.

(All of the above shipped in Phase A.)

### 3.5 Phase B — Execution visualizer (SHIPPED 2026-05-28)
Step through the learner's **own** code and show variables changing line by line (Python-Tutor style), available in the scratchpad.

**What was built:**
- `runner.py`: `build_trace_code()` + `trace_user_code()` run the snippet under `sys.settrace` **in a subprocess** (same isolation as the lab runner). Records one step per executed line — `{line, vars}` — plus a final-state snapshot that captures the last assignments.
- **Guardrails:** step cap `MAX_TRACE_STEPS = 300`; reuses the AST security scan to block dangerous code; **safe value serialization** (non-JSON values degrade to a truncated `repr`, never crash); callables/modules/classes filtered out of the variables panel; stdout captured; timeout via the existing 6s subprocess limit.
- `app.py`: new `/api/trace` endpoint, added to the rate-limited code-execution set + origin check + concurrency cap.
- Frontend: a **Visualize** button in the scratchpad opens an inline stepper — active-line highlight, a Variables panel, Prev/Next, step counter (shows "(capped)" when truncated). (`static/app.js` `visualizeScratchpad`/`renderViz`/`stepViz`; styles `.viz-*` in `styles.css`.)

**Verified:** 8 new tests in `tests/test_trace.py` (loop accumulator progression, runtime error captured-not-raised, blocked import, non-serializable set, step cap on infinite loop, stdout capture, oversized code, live `/api/trace` endpoint). Full suite 683 passing. Live endpoint returns correct steps. **Not visually verified in a browser** (browser access was unavailable) — the stepper UI should be eyeballed once.

**Update (2026-05-28):**
- The visualizer is now a **shared modal overlay** (`#vizOverlay`), opened by `openVisualizer(code, btn)` from **both** the scratchpad **and** the lab editor (Visualize button next to Run Tests). Esc / backdrop / arrow keys control it. Errors render inside the overlay (no blocking `alert`).
- **P1.1 is now closed** (see §2.1) — the lab runner serializes return values safely too.

**Still open / next:**
- Roll the visualizer into the Python-core lessons (link lab snippets straight into the stepper).
- P1.2 (tuple vs JSON-list comparison) remains open by choice — not requested yet.

---

## Backlog (from the audit)

**Closed 2026-05-28:**
- ~~P1.2: tuple vs JSON-list comparison~~ — `_norm()` in `build_test_code()` normalizes tuples/lists (and nested) before comparing; genuine mismatches still fail. Tests in `tests/test_runner.py::TestTupleListComparison`.
- ~~P3: bogus default Ollama model~~ — `qwen3.5:latest`/`nemotron-3-nano:4b` replaced with real tags (`llama3.2`, `qwen2.5`, `phi3.5`) in both `ai_coach.py` and `static/app.js`.
- ~~P3: committed dev artifacts~~ — `.playwright-mcp/`, `qa-home-full.png`, `srv.*` added to `.gitignore` and untracked via `git rm --cached` (local files kept; staged for the next commit).

**Still open:**
- P3: centralize provider defaults in one server-served config consumed by both `ai_coach.py` and `static/app.js` (the two lists are still maintained separately).
- Roadmap: per-question objective IDs for progress analytics; decide whether to split the broad topics (`sql-http-git`, `rag-vectors`, `python-devops`).
- Cleanup: delete the dead legacy content modules and the fallback path once confident.
- Product: roll the execution visualizer directly into the Python-core lessons.
