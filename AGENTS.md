# AGENTS.md

`CLAUDE.md` is the primary source of truth for this project. Use this file as a
short orientation layer only; when rules overlap, follow `CLAUDE.md`.

## Project

Python Skill Lab is the app/product title. The repository slug is
`python-ai-learning-assistant`.

The app is a local-first learning tool for Python, backend APIs, DevOps
automation, and AI engineering foundations. It is learning-focused, not
interview-only.

## Run

```powershell
cd "E:\AI\Python_Learning_Assistant"
python app.py
```

Open `http://127.0.0.1:8765`.

If port `8765` is busy:

```powershell
$env:PY_SKILL_LAB_PORT="9000"
python app.py
```

## Verify

Run the full suite before handing work back:

```powershell
python -B -m pytest tests -q -p no:cacheprovider
```

Run lint:

```powershell
python -m ruff check --no-cache .
```

Run strict content validation for release checks:

```powershell
$env:PY_SKILL_LAB_STRICT_CONTENT="1"
python -B -c "import app; app.validate_on_startup(); print('strict validation ok')"
```

For UI changes, restart the local app and verify the browser-visible flow with
Playwright or a real browser.

## Non-Negotiables

- Keep the app local by default; do not expose it as a shared/public service.
- Do not weaken `_is_allowed_origin`, runner AST checks, stripped builtins,
  request body caps, rate limits, or API-key handling.
- Treat `content/` as the authored curriculum source of truth.
- If `topic.json` `lesson_sections` changes, update matching `lesson.md`
  headings in the same change.
- Use official docs as the source of truth for lesson content.
- Preserve the warm notebook/study-lab UI direction.
- Do not commit secrets, `.env`, caches, generated QA logs, or local audit notes.
- Keep docs in sync with behavior in the same commit.

See `CLAUDE.md` for full architecture notes, content rules, UI invariants,
security details, commit conventions, and workflow principles.
