# Contributing to Python Skill Lab

Thanks for helping improve Python Skill Lab. This is a local-first learning app,
so contributions should preserve the beginner-friendly tone, offline-first setup,
and honest local-only security model.

## Local Setup

```powershell
git clone https://github.com/psc0des/python-ai-learning-assistant.git
cd python-ai-learning-assistant
pip install -r requirements-dev.txt
python app.py
```

Open `http://127.0.0.1:8765`.

The app itself uses only the Python standard library. `pytest` is only needed
for development and CI.

## Tests

Run the full suite before opening a pull request:

```powershell
python -B -m pytest tests -q -p no:cacheprovider
```

Run lint before opening a pull request:

```powershell
python -m ruff check --no-cache .
```

For content-only edits, this faster check is useful while iterating:

```powershell
python -B -m pytest tests/test_curriculum.py tests/test_exercises.py tests/test_content_drift.py -q -p no:cacheprovider
```

Before release-oriented changes, also run strict startup validation:

```powershell
$env:PY_SKILL_LAB_STRICT_CONTENT="1"
python -B -c "import app; app.validate_on_startup(); print('strict validation ok')"
```

## Adding or Editing Curriculum

Authoritative curriculum lives in `content/`.

- Use `content/manifest.json` for topic order.
- Each topic lives under `content/topics/<topic-id>/`.
- Keep `topic.json`, `lesson.md`, `labs.json`, and `practice.json` consistent.
- If you update `lesson_sections` in `topic.json`, update `lesson.md` headings
  to match. `tests/test_content_drift.py` enforces this.
- Cite official docs in each topic's source metadata or section-level
  `source_url`.
- Keep lessons instructional and practical; interview readiness is a secondary
  benefit, not the main lesson voice.
- Labs should include starter code, deterministic tests, hints, solutions, and
  explanations.

There is no runtime fallback to legacy Python content modules. If structured
content fails to load, fix the files under `content/` instead of adding a
parallel source of truth.

## Security and Runtime Rules

Python Skill Lab runs learner code locally on the user's own machine. It is not
a hardened sandbox for shared or public hosting.

- Do not weaken `_is_allowed_origin` in `app.py`.
- Do not remove the AST scan or stripped `__builtins__` runtime restrictions in
  `runner.py`.
- Do not route user, AI, or external HTML/SVG into trusted authored-content
  rendering paths.
- Do not persist API keys to files, localStorage, or committed examples.
- Do not add runtime CDN dependencies; fonts and CodeMirror are vendored for
  offline use.

## Pull Request Checklist

- The change is scoped to the issue or request.
- Full tests pass locally.
- Ruff passes locally.
- Relevant docs are updated in the same PR.
- New content includes official-source citations.
- No secrets, `.env` files, caches, or local logs are committed.
- UI changes preserve the warm notebook/study-lab direction.
