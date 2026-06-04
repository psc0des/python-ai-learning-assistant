# Codex Fix Notes

Date: 2026-06-04
Project: Python Skill Lab / Python Learning Assistant

## Context

The user reported seven real end-to-end issues after the audit:

1. When a local AI provider/container was down, the application showed incorrect local model values.
2. Beginner code using `input()` in the code editor timed out instead of explaining the actual problem.
3. LM Studio base endpoints were treated as final API endpoints, causing incorrect `GET /` and `GET /v1/chat/completions` requests.
4. The Execution Visualizer used AI for deterministic runner-block errors, causing long and inconsistent explanations.
5. The Execution Visualizer auto-called AI narration even when the deterministic trace was already available, adding timeout noise.
6. Beginner lab test results showed expected/got values without showing the actual function call, making the output hard to understand.
7. The first beginner function-parameter lab did not explicitly explain where `a` and `b` values come from.

These were valid audit misses. The earlier audit over-weighted existing tests and happy-path browser behavior and did not sufficiently test local-provider failure states, stale settings, or beginner console-style scripts.

## Finding 1 - Local AI Model Dropdown Showed Wrong Models

### User-Observed Behavior

When a Docker/local AI endpoint was down, the app could still show model names that were not actually installed or available.

Example:

- UI showed a local model such as `phi3.5` or stale provider/model state.
- User did not have that model installed.
- Actual `ollama list` showed:

```text
granite4.1:3b
qwen3.5:latest
nemotron-3-nano:4b
```

### Root Cause

Local model listing had hardcoded fallback model lists for Ollama and LM Studio.

Affected files:

- `ai_coach.py`
- `static/app.js`

The fallback behavior is acceptable for hosted APIs where model names are known defaults, but it is wrong for local providers. Local providers must reflect the live endpoint only.

### Fix Applied

Removed local fallback model lists for:

- Ollama
- LM Studio

Changed frontend behavior so:

- a failed local model refresh no longer invents model options;
- stale selected model values are no longer injected into the dropdown;
- local provider status can show `no live model selected`;
- the app tells the user that no local fallback models were shown because local providers must reflect installed models.

### Verification

Direct backend probe with dead Ollama endpoint:

```text
{'ok': False, 'models': [], 'error': '<urlopen error connection refused>'}
```

Browser verification with:

```text
http://127.0.0.1:11999
```

Result:

```text
models: []
selected: ""
status: ollama / no live model selected
```

## Finding 2 - `input()` Timed Out In Code Editor

### User-Observed Behavior

Running this style of beginner script:

```python
def is_palindrome(string):
    clean_string = string.replace(" ", "").lower()
    return clean_string == clean_string[::-1]

word = input("Enter a word or phrase: ")

if is_palindrome(word):
    print(f"'{word}' is a palindrome!")
else:
    print(f"'{word}' is not a palindrome.")
```

showed:

```text
Execution timed out. Check for infinite loops or very slow code.
```

That message is misleading. The code was waiting for interactive input, not looping.

### Root Cause

The runner is non-interactive, but `input()` was not blocked before subprocess execution. The child process waited for stdin and eventually hit the timeout path.

Affected file:

- `runner.py`

### Fix Applied

Added AST detection for `input()` before execution.

Now the runner returns a targeted learner-facing error:

```text
Line N: input() is not available in this practice runner. Use a function parameter or a sample variable instead.
```

Built-in feedback also adds:

```text
If you used input(), rewrite the code as a function and pass sample values directly.
```

### Verification

Direct runner probe:

```text
False
Line 1: input() is not available in this practice runner. Use a function parameter or a sample variable instead.
If you used input(), rewrite the code as a function and pass sample values directly.
```

Browser verification with the palindrome script:

```text
Error:
Line 5: input() is not available in this practice runner. Use a function parameter or a sample variable instead.

Coach:
  Your code uses constructs that are blocked in this practice sandbox.
  If you used input(), rewrite the code as a function and pass sample values directly.
  This sandbox is designed for learning exercises - system access is restricted for safety.
  Focus on the exercise logic using Python's built-in data types and standard operations.
```

## Finding 3 - LM Studio Endpoint Normalization Was Broken

### User-Observed Behavior

When LM Studio was configured with:

```text
http://127.0.0.1:1234
```

LM Studio logged unexpected requests:

```text
Unexpected endpoint or method. (GET /). Returning 200 anyway
Unexpected endpoint or method. (GET /v1/chat/completions). Returning 200 anyway
```

The UI showed:

```text
Provider: LM Studio (local)
Model: local-model
Endpoint: http://127.0.0.1:1234
```

### Root Cause

The app allowed users to enter a base URL, but the backend reused that raw endpoint for different operations.

Wrong behavior:

- model refresh could call `GET /`;
- model refresh could call `GET /v1/chat/completions`;
- chat could fail if the endpoint was only a base URL.

Correct behavior:

- model refresh must call `GET /v1/models`;
- chat must call `POST /v1/chat/completions`.

### Fix Applied

Added endpoint normalization helpers in `ai_coach.py`:

```text
openai_compatible_chat_url()
openai_compatible_models_url()
```

LM Studio now accepts either:

```text
http://127.0.0.1:1234
```

or:

```text
http://127.0.0.1:1234/v1/chat/completions
```

and derives the correct target:

```text
model list: http://127.0.0.1:1234/v1/models
chat:       http://127.0.0.1:1234/v1/chat/completions
```

The frontend LM Studio default endpoint was changed to:

```text
http://127.0.0.1:1234
```

### Verification

Direct normalization probe:

```text
http://127.0.0.1:1234/v1/models
http://127.0.0.1:1234/v1/models
http://127.0.0.1:1234/v1/chat/completions
```

Regression coverage in `tests/test_ai_models.py` verifies:

- LM Studio base endpoint lists from `/v1/models`;
- LM Studio chat endpoint also maps model listing to `/v1/models`;
- LM Studio chat uses `/v1/chat/completions` when the configured endpoint is only the base URL.

## Finding 4 - Visualizer Over-Used AI For Known Runner Blocks

### User-Observed Behavior

When visualizing code that used `input()`, the Visualizer correctly stopped before execution, but the explanation area could show a long AI-generated answer with Markdown headings and a full rewritten code block.

This was confusing inside the modal because the reason was already deterministic:

```text
input() is not available in this practice runner.
```

### Root Cause

The Visualizer treated all zero-step errors as candidates for AI narration. For known runner-block cases, this is unnecessary and risky because local models may ignore formatting constraints and produce overly long answers.

This is not mainly a security issue for `input()`. It is a non-interactive-runner limitation: the subprocess cannot pause and wait for keyboard input. Other blocked constructs, such as `open()` or system imports, are security/safety boundaries.

Affected file:

- `static/app.js`

### Fix Applied

Added deterministic built-in Visualizer notes for known runner-block cases:

- `input()`;
- `open()`;
- blocked sandbox/system-access constructs.

Changed both Visualizer paths:

- automatic zero-step explanation;
- manual Visualizer `Ask AI` button.

Known runner-block errors now skip AI narration and display a short built-in explanation instead.

Current `input()` Visualizer message:

```text
input() is blocked here because this runner cannot pause and wait for keyboard input. Use a sample variable or pass a value into your function instead.
```

### Verification

Browser verification with the palindrome script:

```text
overlayVisible: true
variablesText: Python stopped before running any code.
beforeAsk: input() is blocked here because this runner cannot pause and wait for keyboard input. Use a sample variable or pass a value into your function instead.
afterAsk: Runner input() is blocked here because this runner cannot pause and wait for keyboard input. Use a sample variable or pass a value into your function instead.
hasLongMarkdown: false
```

Regression coverage:

- `tests/test_trace.py`
  - verifies `input()` is rejected before trace execution;
  - verifies the error does not surface as a timeout;
  - verifies no trace steps are returned.

## Finding 5 - Visualizer Auto-Narration Added Unnecessary AI Timeout Noise

### User-Observed Behavior

The Visualizer could show:

```text
AI explanation unavailable: Error: timed out after 18s
```

even though the actual execution trace and variables were already available.

### Root Cause

The Visualizer had two layers:

1. deterministic trace from `/api/trace`;
2. optional AI narration from `/api/narrate`.

The second layer was auto-triggered in the background, so a slow local model could make the Visualizer look broken even when the trace itself worked.

### Fix Applied

Removed automatic AI narration from the Visualizer open path.

Now:

- opening the Visualizer calls `/api/trace` only;
- steps, variables, stdout, and errors remain deterministic;
- AI runs only when the learner explicitly clicks `Ask AI`;
- known runner-block errors still use built-in deterministic notes.

### Verification

Browser/network verification for a normal trace:

```text
note: About to run line 1.
count: Step 1 of 4
variables: No variables yet.
```

Network requests observed:

```text
POST /api/trace
```

No `/api/narrate` request was made.

## Finding 6 - Lab Test Results Hid The Actual Function Call

### User-Observed Behavior

The `Add Two Numbers` lab showed:

```text
Tests: 3/3 passed
  PASS two positives | expected 5, got 5
  PASS with zero | expected 10, got 10
  PASS negatives | expected -3, got -3
```

For a beginner, that does not explain where `5`, `10`, or `-3` came from.

### Root Cause

The runner already returned each test's `call` field, such as:

```text
add(2, 3)
```

but `static/app.js` did not display it in the test result line.

The lab prompt also assumed the learner already understood "passed to it" without a concrete example.

### Fix Applied

Updated `static/app.js` so test results include the actual function call:

```text
PASS add(2, 3) -> expected 5, got 5
```

For tests where the label is different from the call, the UI preserves both:

```text
PASS descriptive label | function_call(...) -> expected X, got Y
```

Updated `content/topics/getting-started/labs.json` for `Add Two Numbers`:

- prompt now includes `add(2, 3)` as a concrete example;
- test labels now match the tested function calls.

### Verification

Browser verification:

```text
Tests: 3/3 passed
  PASS add(2, 3) -> expected 5, got 5
  PASS add(10, 0) -> expected 10, got 10
  PASS add(-4, 1) -> expected -3, got -3
```

## Finding 7 - Beginner Lab Did Not Explain Function Parameters Clearly Enough

### User-Observed Behavior

The learner saw:

```text
def add(a, b):
    return a + b
```

and passed tests, but still had a reasonable beginner question:

```text
Where do values for a and b come from?
```

### Root Cause

The lab used the phrase "numbers passed to it", which is normal developer language but not enough for a zero-beginner lesson. The UI also showed test results without explicitly saying that the tests are the caller.

### Fix Applied

Updated `content/topics/getting-started/labs.json` for `Add Two Numbers`:

- prompt now says the learner does not need `input()`;
- prompt explains the tests call `add(...)` with sample values;
- hint explains `a` and `b` receive values from calls like `add(2, 3)`;
- explanation says Python puts `2` into `a` and `3` into `b`.

Updated `static/app.js` test output:

```text
The tests called your code with these sample values:
  PASS add(2, 3) returned 5 (expected 5)
  PASS add(10, 0) returned 10 (expected 10)
  PASS add(-4, 1) returned -3 (expected -3)
```

### Verification

Browser verification confirmed the prompt now says:

```text
You do not need to ask the user for a or b with input(); the tests will call your function with sample values.
```

## Files Changed

Application files:

```text
ai_coach.py
runner.py
static/app.js
```

Tests:

```text
tests/test_runner.py
tests/test_ai_models.py
tests/test_trace.py
```

Audit/report artifact:

```text
ai_audit_v3.md
```

This handoff file:

```text
codexfix.md
```

## Tests Added

### `tests/test_ai_models.py`

Added coverage that:

- Ollama model listing returns `models: []` when the endpoint is down.
- Ollama model listing returns only models reported by `/api/tags`.
- LM Studio model listing uses `/v1/models` for base and chat endpoints.
- LM Studio chat uses `/v1/chat/completions` when configured with only the base endpoint.

### `tests/test_runner.py`

Added coverage that:

- `input()` is detected by the AST scanner.
- code containing `input()` is blocked before execution;
- the error does not surface as a timeout.

## Verification Run

Command:

```powershell
python -B -m pytest tests -q -p no:cacheprovider
```

Result:

```text
754 passed in 15.42s
```

## Notes For Dev

The fixes above are intentionally narrow.

Recommended next review points:

1. Confirm localStorage cannot preserve stale local model values after endpoint changes.
2. Consider disabling Send/Ask AI when local provider has no live selected model.
3. Add a small learner tip near the editor explaining that the runner is non-interactive and labs should use functions/parameters instead of `input()`.
4. Include Docker-down/local-provider-down cases in future E2E QA.
5. Include beginner pasted scripts, not only lab-shaped functions, in runner QA.

## Important Process Note

The original audit request was report-only. Code was edited during follow-up investigation. Keep or revert those changes according to the project owner's preference.

---

# Post-Audit Non-Capstone Fixes - 2026-06-04

The owner asked to fix every `ai_audit_v4.md` finding except the OOP capstone. The capstone was left untouched because another dev is already working on it.

## Fixed

1. Mobile/narrow layout overflow
   - Added late responsive CSS overrides in `static/styles.css`.
   - Verified at `390x844`: `scrollWidth` equals `clientWidth`, and there are no non-code layout overflow offenders.

2. Stacked Try-it + Visualizer Escape behavior
   - Updated the Visualizer Escape handler in `static/app.js` to stop propagation after closing the top modal.
   - Verified one Escape closes Visualizer only and leaves Try-it open.

3. AI settings false success on bad local endpoint
   - `static/app.js` now shows `Checking...` first and only shows `Saved` after model refresh succeeds.
   - Failed local refresh keeps the settings panel open, shows `Save failed`, clears fake/stale local models, and does not close silently.
   - Endpoint/API key edits no longer silently save before Save & Apply.

4. Local AI fake-model fallback hardening
   - `ai_coach.py` no longer silently uses `llama3.2` or `local-model` when Ollama/LM Studio chat is called with no selected live model.
   - Added tests requiring explicit live model selection for local chat.

5. Removed stale visualizer auto-narration path
   - Removed `/api/narrate` route from `app.py`.
   - Removed unused `narrate_trace()` from `ai_coach.py`.
   - Removed `_loadNarrations()` and narration loading/error state from `static/app.js`.
   - Visualizer remains deterministic by default; manual Ask AI still works through `/api/ai-coach`.

6. Updated docs and project instructions
   - `SETUP.md` now recommends LM Studio base endpoint `http://127.0.0.1:1234`.
   - Removed static Ollama model recommendations that could imply unavailable models.
   - `docs/ai_provider_qa.md` now tests local model lists as live-only and visualizer Ask AI as optional.
   - `AGENTS.md` now documents deterministic visualizer behavior.

7. Beginner lab wording
   - Updated early Getting Started, Python Basics, and Functions lab prompts to explain that tests call functions with sample values.
   - Added explicit "do not use input()" wording where appropriate.

8. Thin lab tests
   - All 80 labs now have at least 3 tests.
   - Added edge/variant tests across FastAPI, LangChain, MCP, OOP non-capstone, Python DevOps, RAG/Vectors, SQL/HTTP/Git, and Getting Started.
   - The OOP capstone was not changed.

9. Runner feedback
   - `runner.py` docstring now documents both `input()` and `open()` blocking.
   - Blocked-code feedback is now conditional so `open()`/imports do not receive misleading `input()` advice.

## Browser Verification

Local server:

```text
http://127.0.0.1:9886
```

Verified:

- Console: 0 errors, 0 warnings.
- Ollama dropdown showed only real installed models:
  - `granite4.1:3b`
  - `qwen3.5:latest`
  - `nemotron-3-nano:4b`
- Bad endpoint `http://127.0.0.1:11999`:
  - button: `Save failed`
  - panel stayed open
  - model list empty
  - no stale model in settings label
- Mobile `390x844`:
  - `scrollWidth: 375`
  - `clientWidth: 375`
  - no non-code overflow offenders
- Try-it + Visualizer:
  - Visualizer opened above Try-it
  - network calls did not include `/api/narrate`
  - one Escape closed only Visualizer, not Try-it
- Add Two Numbers lab output still shows sample function calls:
  - `PASS add(2, 3) returned 5 (expected 5)`
  - `PASS add(10, 0) returned 10 (expected 10)`
  - `PASS add(-4, 1) returned -3 (expected -3)`

## Verification Run

Commands:

```powershell
node --check static\app.js
python -B -m pytest tests -q -p no:cacheprovider
$env:PY_SKILL_LAB_STRICT_CONTENT='1'; python -B -c "import app; app.validate_on_startup(); print('strict validation ok')"
```

Results:

```text
JavaScript syntax check passed
756 passed in 14.35s
strict validation ok
Content validation passed: 15 topics, 80 exercises, 15 practice tests
```
