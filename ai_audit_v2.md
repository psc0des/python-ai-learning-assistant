# Python Skill Lab — Independent Audit v2

**Audit date:** 2026-05-28
**Auditor stance:** Skeptical, fact-first. I trusted no claim — every statement below is backed by something I ran or read in the current tree.
**Scope:** `app.py`, `runner.py`, `ai_coach.py`, `content_loader.py`, `models.py`, all 14 topics under `content/`, the `static/` frontend, and the test suite.
**Constraint honored:** I did **not** edit any application code. This report is the only file I created.

---

## Executive Verdict

**Your engineers are mostly telling you the truth. The product is in materially better shape than the previous `audit.md` (v1, dated 2026-05-26) describes.**

I went in expecting to catch a thin prototype dressed up as a finished product. That is not what I found. The big-ticket problems the v1 audit raised as **P0/P1 blockers** — shallow lessons, missing source links, too few labs, no quality gates, an un-grounded curriculum — have been **fixed and verified**, not papered over.

What I *did* find are **a handful of genuine edge-case bugs and polish gaps**. None of them block a launch for the stated goal (a free, local, open-source tool to learn Python and Python-for-AI). They should go on a backlog, not a panic list.

**Bottom line:** This is a legitimately shippable MVP. It is not a scam, and it is not vaporware. I would let it reach users — with the caveat that two runner edge cases (below) get fixed in the next pass because a learner *can* trip them.

---

## How I Verified (so you can re-run it yourself)

Everything here is reproducible. The important checks:

| Check | Command | Result |
|---|---|---|
| Full test suite | `python -m pytest -q` | **635 passed** in ~11s |
| Server actually boots & serves | started `app.py`, hit `/api/curriculum` + `/` | HTTP 200, 14 topics, `mode=structured` |
| **Every lab solution passes its own tests** | ran all 70 solutions through the real runner | **70/70 pass, 0 failures, 0 missing solutions** |
| Practice answers are valid | checked all 112 questions | **0 invalid answer indices, all have explanations** |
| Labs aren't trivial | ran all 70 *starter* templates | **0 starters pass without work** (every lab requires real effort) |
| Source links are official | parsed all 85 section source URLs | **100% official docs, 100% https** |

That combination — solutions pass, starters don't, answers are valid — is the single strongest signal that the content is *real* and not filler. A faked course fails exactly these checks.

---

## What the Engineers Got Right (verified, not taken on faith)

### 1. Content depth is real and consistent
Every one of the 14 topics now has:

| Metric | Every topic | v1 audit found (most topics) |
|---|---|---|
| Labs | **5** | 2 |
| Practice questions | **8** | 5 |
| Lesson sections | **6** | 4 |
| Sourced sections | **all of them** | 0 (only Python Basics) |
| Lesson words | **~1,000–1,420** | 79–120 |

The v1 audit's headline finding ("only Python Basics meets the standard") is **no longer true**. The gap was closed across the board.

### 2. The curriculum is genuinely sourced to official docs
All 85 section-level source URLs point to canonical, first-party documentation: `docs.python.org` (42), `docs.langchain.com` (17), `fastapi.tiangolo.com`, `docs.pydantic.dev`, `modelcontextprotocol.io`, `developer.mozilla.org`, `git-scm.com`, `postgresql.org`, etc. All https. The specific LangChain canonical-link fix the v1 audit asked for is in place and resolves (HTTP 200).

### 3. The previously-flagged "wrong simplifications" were corrected
I sampled the AI topics the v1 audit called riskiest. The **MCP** lesson now teaches the Host / Client / Server distinction and the Tools / Resources / Prompts capability split correctly — the exact gap v1 said was missing. This is accurate, current material, not hand-waving.

### 4. There is a real quality gate, and the labels are honest
`tests/test_content_quality.py` enforces, for any topic claiming `quality_status: "reference"`: ≥5 labs, ≥8 questions, and a source URL on *every* lesson section. All 14 topics are marked `reference`, and **all 14 actually meet the bar** — so the claim is backed by an enforced test, not a sticker. A topic that fell below the bar would fail CI.

### 5. Security posture is appropriate for what this is
- Server binds to `127.0.0.1` only.
- POST endpoints are allow-listed; cross-origin POSTs are rejected.
- Per-IP rate limiting on `/api/run` and a concurrent-request cap.
- The frontend escapes HTML everywhere it matters — lesson markdown, coach messages, and **even AI-model output** are passed through `escapeHtml()` before rendering. No obvious XSS path.
- API keys can be supplied via environment variables instead of the browser.

### 6. The runner is honest about its limits
The README explicitly states it is "a practice tool, not a security sandbox for untrusted code." That disclaimer is correct and important (see the denylist note below). Honesty here is a point in the engineers' favor, not against them.

---

## Genuine Findings (real, but none are launch-blockers)

### P1 — Runner crashes on non-JSON-serializable return values
**Evidence:** I ran a function returning a `set` (`{1,2,3}`) against a test. Inside the subprocess, `json.dumps(results)` throws because a set isn't JSON-serializable. The result marker never prints, so the app shows **zero tests** and leaks an internal traceback referencing `"<string>", line 43` to the learner.

**Why it matters:** A beginner who returns a set (or any custom object) where a list was expected gets a confusing internal error instead of a clean "expected `[1,2,3]`, got `{1,2,3}`". It looks like the app is broken, not their code.

**Scope:** Latent. **None of the 70 current labs trigger it** (I verified all 70 pass cleanly). It only surfaces when a learner's own answer returns an exotic type. The scratchpad is unaffected (no test serialization there).

**Fix direction:** In `build_test_code`, coerce `actual` to a serializable form (e.g. `repr()` fallback) before `json.dumps`, so a bad return degrades to a failed test, not a crash.

### P1 — Tuple returns can never compare equal to expected values
**Evidence:** A function returning `(1, 2)` against an `expected` of `[1, 2]` reports **FAIL** — because JSON has no tuple type, every `expected` loaded from content is a list, and `(1,2) == [1,2]` is `False` in Python.

**Why it matters:** A future lab author who writes a tuple-returning exercise will mark correct learner answers as wrong, and won't understand why. It's a trap baked into the test harness.

**Scope:** Latent. No current lab expects a tuple, so nothing is broken today. This is a content-authoring landmine, not a live defect.

**Fix direction:** Normalize tuples/lists on both sides before comparison, or document "labs must return JSON-expressible types."

### P2 — The sandbox denylist is bypassable
**Evidence:** `import os` is blocked, but `import gc`, `import inspect`, `import platform`, and `__builtins__['__import__']('os')` all pass the scanner. A denylist of module names can always be walked around.

**Why it matters / why it's only P2:** The README already says this is *not* a security sandbox, the server is localhost-only, and the threat model is "a single user on their own desktop" — i.e. a user could only attack their own machine, which they can already do by opening a terminal. The real risk is the word "sandbox" in the code creating a *false sense of safety* if anyone ever exposes this on a network. **Do not deploy this multi-user or on a shared host without a real sandbox** (subprocess + OS-level isolation / container / seccomp).

### P3 — Stale/odd default model names
**Evidence:** The default Ollama model is `qwen3.5:latest`, which is not a real Ollama tag (the real families are `qwen2.5` / `qwen3`); the model-list fallback also includes `nemotron-3-nano:4b`. Hosted-provider defaults are hardcoded in both `ai_coach.py` and `static/app.js`.

**Why it matters:** A first-time Ollama user who hasn't pulled that exact tag gets a failed call. It degrades gracefully to built-in coach feedback (good), but the default is misleading. Model IDs also drift over time. Low impact, easy fix.

### P3 — Dev artifacts committed to the repo
`audit.md`, `qa-home-full.png`, and a folder of `.playwright-mcp/*.log` / `*.yml` capture files are tracked in git. Harmless, but clutter for an OSS project. Add them to `.gitignore` and remove from history at the next convenient point.

### P3 — No objective mapping / stable IDs on practice questions
Practice questions have no `id` or learning-objective tag (the frontend keys off array index, which works). The v1 audit's "map every question to an objective" recommendation is still open. This is a *nice-to-have for analytics and review*, not a correctness issue.

---

## Findings From v1 That Are Now CLOSED

For your records — these were the v1 audit's blockers, and where they stand now:

| v1 Finding | Status |
|---|---|
| P0 — Curriculum depth not production-ready | **Closed.** All 14 topics at 5 labs / 8 Qs / ~1,000+ words. |
| P0 — Content model too weak (hand-edited Python) | **Closed.** Structured `content/` dir with JSON + markdown, loaded & validated. |
| P0 — Tests give false confidence | **Closed.** `test_content_quality.py` enforces the baseline; 635 tests total. |
| P1 — Sources listed, not integrated | **Closed.** Every section has an official `source_url`. |
| P1 — MCP / LangChain wrong simplifications | **Closed (sampled).** MCP host/client/server now correct; LangChain link fixed. |
| P1 — AI coach not grounded in lesson content | **Mostly closed.** `build_ai_prompt()` now injects lesson-section summaries + source URLs. |

The one v1 item only *partially* addressed is **topic-scope breadth** (`sql-http-git`, `rag-vectors`, `python-devops` are still broad single topics). That's a curriculum-design opinion, not a bug — those topics now have full depth, they just cover a lot of ground. Splitting them is a roadmap call, not a defect.

---

## Were You Being Deceived?

**No — not on the evidence.** The claim "the project is done" holds up for an MVP of the stated scope. The work is real: solutions execute and pass, starters require effort, answers are valid, sources are official and live, the server runs, and 635 tests pass. The previous audit's serious findings were genuinely remediated, and the team even left an honest paper trail of what was *still open* in `audit.md` rather than hiding it.

The remaining issues are the kind every shipped product has: two latent edge-case bugs in the test runner, a knowingly-disclaimed non-sandbox, and cosmetic cleanup. That is a normal backlog, not a cover-up.

**My recommendation:** Approve it for release as a v1. Put the two **P1 runner fixes** at the top of the next sprint (they're small and they protect the learner experience), schedule the topic-split discussion as a roadmap item, and sweep the P3 polish whenever convenient.

---

## Suggested Next-Sprint Punch List (priority order)

1. **P1** — Make the test harness tolerant of non-serializable return values (no internal traceback leaks to learners).
2. **P1** — Normalize tuple/list comparison in the runner (or document the restriction for lab authors).
3. **P2** — Either replace the denylist with real OS-level isolation **or** rename it away from "sandbox" and keep the localhost-only deployment rule explicit in SETUP.md.
4. **P3** — Fix the default Ollama model id; centralize provider defaults in one server-served config consumed by both backend and frontend.
5. **P3** — `.gitignore` the dev artifacts (`.playwright-mcp/`, `qa-home-full.png`).
6. **Roadmap** — Decide whether to split `sql-http-git` / `rag-vectors` / `python-devops`; add per-question objective IDs for progress analytics.
