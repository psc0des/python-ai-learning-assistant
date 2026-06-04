# AI Provider QA Checklist

Manual sign-off checklist for each of the 7 supported providers. Run this before every release that touches `ai_coach.py`, `static/app.js` AI settings, or provider model lists.

Tester initials and date go in the Sign-off column. A blank cell means untested.

---

## Test Steps (same for every provider)

| # | Step | Expected outcome |
|---|------|-----------------|
| 1 | Enter provider credentials in AI Settings and click Save & Apply | Button shows ✓ Saved only after model refresh succeeds; failed local refresh keeps the panel open and shows an explicit error |
| 2 | Click the model dropdown refresh button (↻) | Model list populates within the AI models timeout (default 8 s); local providers show only live installed/loaded models; no JS error in console |
| 3 | Open any topic → Labs → type a question in the AI Coach box and click Send | Response arrives within the AI timeout (default 25 s); response is coherent and references the topic |
| 4 | Open Execution Visualizer → run a short snippet → optionally click Ask AI | Deterministic step explanation appears without AI; optional Ask AI explains the current step when provider is healthy |
| 5 | Clear the API key field, save, and send a message | App shows explicit key error (not a blank response or crash); built-in feedback still appears |

---

## Provider Sign-off Table

### 1. Ollama (local)

**Prerequisites:** Ollama installed and running (`ollama serve`). At least one local model pulled.

**Settings:**
- Provider: Ollama (local)
- Endpoint: `http://127.0.0.1:11434`
- Model: choose from the live dropdown after refresh
- API key: leave blank

| Test | Pass | Fail | Notes | Sign-off |
|------|------|------|-------|---------|
| 1 Settings save | | | | |
| 2 Model list loads | | | | |
| 3 Coach responds | | | | |
| 4 Visualizer deterministic note / optional Ask AI | | | | |
| 5 Missing key fallback | | | N/A — no key required | |

---

### 2. LM Studio (local)

**Prerequisites:** LM Studio running with local server enabled. A model loaded.

**Settings:**
- Provider: LM Studio (local)
- Endpoint: `http://127.0.0.1:1234`
- Model: choose from the live dropdown after LM Studio reports loaded models
- API key: leave blank

| Test | Pass | Fail | Notes | Sign-off |
|------|------|------|-------|---------|
| 1 Settings save | | | | |
| 2 Model list loads | | | App calls `/v1/models` derived from the base endpoint | |
| 3 Coach responds | | | | |
| 4 Visualizer deterministic note / optional Ask AI | | | | |
| 5 Missing key fallback | | | N/A — no key required | |

---

### 3. OpenAI

**Prerequisites:** Valid OpenAI API key with access to `gpt-4.1-mini` or equivalent.

**Settings:**
- Provider: OpenAI
- Endpoint: `https://api.openai.com/v1/chat/completions`
- Model: `gpt-4.1-mini`
- API key: your key

| Test | Pass | Fail | Notes | Sign-off |
|------|------|------|-------|---------|
| 1 Settings save | | | | |
| 2 Model list loads | | | | |
| 3 Coach responds | | | | |
| 4 Visualizer deterministic note / optional Ask AI | | | | |
| 5 Missing key fallback | | | Expect "AI Coach unavailable" + key error message | |

---

### 4. Anthropic

**Prerequisites:** Valid Anthropic API key with access to `claude-3-5-haiku-latest`.

**Settings:**
- Provider: Anthropic
- Endpoint: `https://api.anthropic.com/v1/messages`
- Model: `claude-3-5-haiku-latest`
- API key: your key

| Test | Pass | Fail | Notes | Sign-off |
|------|------|------|-------|---------|
| 1 Settings save | | | | |
| 2 Model list loads | | | Anthropic does not expose a model-list endpoint; list may be static | |
| 3 Coach responds | | | | |
| 4 Visualizer deterministic note / optional Ask AI | | | | |
| 5 Missing key fallback | | | Expect "AI Coach unavailable" + key error message | |

---

### 5. Google AI Studio

**Prerequisites:** Valid Google AI Studio API key with access to `gemini-2.0-flash`.

**Settings:**
- Provider: Google AI Studio
- Endpoint: `https://generativelanguage.googleapis.com/v1beta`
- Model: `gemini-2.0-flash`
- API key: your key

| Test | Pass | Fail | Notes | Sign-off |
|------|------|------|-------|---------|
| 1 Settings save | | | | |
| 2 Model list loads | | | | |
| 3 Coach responds | | | | |
| 4 Visualizer deterministic note / optional Ask AI | | | | |
| 5 Missing key fallback | | | Expect "AI Coach unavailable" + key error message | |

---

### 6. Grok (xAI)

**Prerequisites:** Valid xAI API key with access to `grok-3-mini`.

**Settings:**
- Provider: Grok (xAI)
- Endpoint: `https://api.x.ai/v1/chat/completions`
- Model: `grok-3-mini`
- API key: your key

| Test | Pass | Fail | Notes | Sign-off |
|------|------|------|-------|---------|
| 1 Settings save | | | | |
| 2 Model list loads | | | | |
| 3 Coach responds | | | | |
| 4 Visualizer deterministic note / optional Ask AI | | | | |
| 5 Missing key fallback | | | Expect "AI Coach unavailable" + key error message | |

---

### 7. Groq Cloud

**Prerequisites:** Valid Groq API key with access to `llama-3.3-70b-versatile`.

**Settings:**
- Provider: Groq Cloud
- Endpoint: `https://api.groq.com/openai/v1/chat/completions`
- Model: `llama-3.3-70b-versatile`
- API key: your key

| Test | Pass | Fail | Notes | Sign-off |
|------|------|------|-------|---------|
| 1 Settings save | | | | |
| 2 Model list loads | | | | |
| 3 Coach responds | | | | |
| 4 Visualizer deterministic note / optional Ask AI | | | | |
| 5 Missing key fallback | | | Expect "AI Coach unavailable" + key error message | |

---

## Release Gate

Do not ship a release that changes AI provider code unless at minimum:

- Ollama (local) passes all 4 applicable steps
- At least one hosted provider (OpenAI, Anthropic, Google, Grok, or Groq) passes all 5 steps
- No JS console errors during any test step

Full certification (all 7 providers) is preferred before a major version bump.
