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
$env:PY_INTERVIEW_PORT="9000"
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

- `app.py`: local HTTP server and API routes.
- `content_loader.py`: loads structured curriculum from `content/`.
- `ai_coach.py`: AI provider integration for Ollama, LM Studio, OpenAI, and Anthropic.
- `runner.py`: local Python exercise runner.
- `models.py`: request/response validation and startup content checks.
- `curriculum.py`: topic metadata, overview copy, lesson content, citations, real-world notes.
- `exercises.py`: coding labs, starter code, tests, hints, solutions.
- `practice_tests.py`: multiple-choice practice tests.
- `content/manifest.json`: topic ordering and schema metadata.
- `content/sources.json`: official source registry with `checked_at`.
- `content/topics/*`: per-topic authored content (`topic.json`, `lesson.md`, `labs.json`, `practice.json`).
- `static/index.html`: app shell.
- `static/app.js`: UI behavior, topic rendering, labs, tests, AI coach interactions.
- `static/styles.css`: warm notebook visual design.
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

Python Basics has been rewritten as the first reference-quality topic:

- richer overview wording;
- official Python Tutorial citations;
- 6 lesson sections;
- 5 labs;
- 8 practice questions.

Most other topics still need the same depth pass. Do not assume the curriculum is complete just because tests pass. Tests currently validate structure and exercise correctness, not full teaching quality.

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

## AI Coach

The AI Coach supports:

- Ollama;
- LM Studio;
- OpenAI;
- Anthropic.

The app should work without AI configured. Local tests and built-in feedback should remain useful even when no provider is connected.

API keys must stay in the browser session and should not be committed to files.

## Security Notes

The app currently binds to localhost. Keep it local by default.

Do not expose this app to a network or multiple users without reviewing:

- code execution isolation;
- filesystem access;
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
