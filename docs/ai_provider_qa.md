# AI Provider QA Checklist

Manual sign-off checklist for each of the 8 supported providers. Run this before every release that touches `ai_coach.py`, `static/app.js` AI settings, or provider model lists.

Tester initials and date go in the Sign-off column. A blank cell means untested.

An API-level smoke test is not a substitute for this checklist. Calling
`/api/ai-coach-stream` directly and confirming a valid NDJSON `chunk`/`done`
stream verifies the backend route and provider adapter, but does not exercise
AI Settings, the Model dropdown, the AI Coach/Ask AI UI, or the typing/stream
rendering. Record API-only checks in the Notes column and leave Pass/Fail/
Sign-off blank until the full UI walkthrough is done.

---

## Test Steps

| # | Step | Expected outcome |
|---|------|-----------------|
| 1 | Configure AI Settings and click Save & Apply | Button shows "Saved" only after validation succeeds; failed local model discovery keeps the panel open and shows an explicit error |
| 2 | Local providers: click Show local models, choose a Model dropdown option, then click Test selected model | Model list populates within the AI models timeout (default 8 s); local providers show only live installed/loaded models; selected model replies or shows a warm-up/provider error; no JS console error |
| 3 | Hosted providers: enter key/model and click Verify provider | The configured model replies or a clear key/provider error appears; suggested models are not treated as a verified connection |
| 4 | Open any topic -> Labs -> type a question in the AI Coach box and click Send | Response starts streaming before the full answer is complete when the provider supports streaming; non-streaming providers use the fallback reveal; answer is coherent for the lab context |
| 5 | Open floating Ask AI -> send a freeform message -> use New chat | Freeform chat does not inherit the current topic unless a contextual action is used; New chat clears the Ask AI history |
| 6 | Open Execution Visualizer -> run a short snippet -> optionally click Ask AI | Deterministic step explanation appears without AI; optional Ask AI opens the floating messenger with current step context when provider is healthy |
| 7 | Clear the API key field for a hosted provider, save, and send a message | App shows explicit key error, not a blank response or crash; built-in feedback still appears where applicable |

---

## Provider Sign-Off Table

### 1. Ollama (local)

**Prerequisites:** Ollama installed and running (`ollama serve`). At least one local model pulled.

**Settings:**
- Provider: Ollama (local)
- Endpoint: `http://127.0.0.1:11434`
- Model: choose from the Model dropdown after Show local models
- API key: leave blank

| Test | Pass | Fail | Notes | Sign-off |
|------|------|------|-------|---------|
| 1 Settings save | | | | |
| 2 Local model list + selected model test | | | | |
| 3 Hosted verify | | | N/A - local provider | |
| 4 Coach responds | | | API-level only: `POST /api/ai-coach-stream` with `model: granite4.1:3b` returned valid `chunk`/`done` NDJSON events (audit, 2026-06-15). Full UI walkthrough not yet performed. | |
| 5 Freeform Ask AI / New chat | | | | |
| 6 Visualizer deterministic note / optional Ask AI | | | | |
| 7 Missing key fallback | | | N/A - no key required | |

---

### 2. LM Studio (local)

**Prerequisites:** LM Studio running with local server enabled. A model loaded.

**Settings:**
- Provider: LM Studio (local)
- Endpoint: `http://127.0.0.1:1234`
- Model: choose from the Model dropdown after Show local models
- API key: leave blank

| Test | Pass | Fail | Notes | Sign-off |
|------|------|------|-------|---------|
| 1 Settings save | | | | |
| 2 Local model list + selected model test | | | App calls `/v1/models` derived from the base endpoint | |
| 3 Hosted verify | | | N/A - local provider | |
| 4 Coach responds | | | | |
| 5 Freeform Ask AI / New chat | | | | |
| 6 Visualizer deterministic note / optional Ask AI | | | | |
| 7 Missing key fallback | | | N/A - no key required | |

---

### 3. OpenAI

**Prerequisites:** Valid OpenAI API key with access to the configured model.

**Settings:**
- Provider: OpenAI
- Endpoint: `https://api.openai.com/v1/chat/completions`
- Model: `gpt-4.1-mini` or another model your account can use
- API key: your key

| Test | Pass | Fail | Notes | Sign-off |
|------|------|------|-------|---------|
| 1 Settings save | | | | |
| 2 Local model list + selected model test | | | N/A - hosted provider | |
| 3 Hosted verify | | | | |
| 4 Coach responds | | | | |
| 5 Freeform Ask AI / New chat | | | | |
| 6 Visualizer deterministic note / optional Ask AI | | | | |
| 7 Missing key fallback | | | Expect "AI Coach unavailable" + key error message | |

---

### 4. Anthropic

**Prerequisites:** Valid Anthropic API key with access to the configured model.

**Settings:**
- Provider: Anthropic
- Endpoint: `https://api.anthropic.com/v1/messages`
- Model: `claude-3-5-haiku-latest` or another model your account can use
- API key: your key

| Test | Pass | Fail | Notes | Sign-off |
|------|------|------|-------|---------|
| 1 Settings save | | | | |
| 2 Local model list + selected model test | | | N/A - hosted provider | |
| 3 Hosted verify | | | | |
| 4 Coach responds | | | | |
| 5 Freeform Ask AI / New chat | | | | |
| 6 Visualizer deterministic note / optional Ask AI | | | | |
| 7 Missing key fallback | | | Expect "AI Coach unavailable" + key error message | |

---

### 5. Google AI Studio

**Prerequisites:** Valid Google AI Studio API key with access to the configured model.

**Settings:**
- Provider: Google AI Studio
- Endpoint: `https://generativelanguage.googleapis.com/v1beta`
- Model: `gemini-2.0-flash` or another model your account can use
- API key: your key

| Test | Pass | Fail | Notes | Sign-off |
|------|------|------|-------|---------|
| 1 Settings save | | | | |
| 2 Local model list + selected model test | | | N/A - hosted provider | |
| 3 Hosted verify | | | | |
| 4 Coach responds | | | | |
| 5 Freeform Ask AI / New chat | | | | |
| 6 Visualizer deterministic note / optional Ask AI | | | | |
| 7 Missing key fallback | | | Expect "AI Coach unavailable" + key error message | |

---

### 6. Grok (xAI)

**Prerequisites:** Valid xAI API key with access to the configured model.

**Settings:**
- Provider: Grok (xAI)
- Endpoint: `https://api.x.ai/v1/chat/completions`
- Model: `grok-3-mini` or another model your account can use
- API key: your key

| Test | Pass | Fail | Notes | Sign-off |
|------|------|------|-------|---------|
| 1 Settings save | | | | |
| 2 Local model list + selected model test | | | N/A - hosted provider | |
| 3 Hosted verify | | | | |
| 4 Coach responds | | | | |
| 5 Freeform Ask AI / New chat | | | | |
| 6 Visualizer deterministic note / optional Ask AI | | | | |
| 7 Missing key fallback | | | Expect "AI Coach unavailable" + key error message | |

---

### 7. Groq Cloud

**Prerequisites:** Valid Groq API key with access to the configured model.

**Settings:**
- Provider: Groq Cloud
- Endpoint: `https://api.groq.com/openai/v1/chat/completions`
- Model: `llama-3.3-70b-versatile` or another model your account can use
- API key: your key

| Test | Pass | Fail | Notes | Sign-off |
|------|------|------|-------|---------|
| 1 Settings save | | | | |
| 2 Local model list + selected model test | | | N/A - hosted provider | |
| 3 Hosted verify | | | | |
| 4 Coach responds | | | | |
| 5 Freeform Ask AI / New chat | | | | |
| 6 Visualizer deterministic note / optional Ask AI | | | | |
| 7 Missing key fallback | | | Expect "AI Coach unavailable" + key error message | |

---

### 8. Azure AI Foundry

**Prerequisites:** Azure AI Foundry project with at least one model deployed. Project endpoint URL and API key.

**Settings:**
- Provider: Azure AI Foundry
- Endpoint: `https://<project>.services.ai.azure.com/api/projects/<name>/v1/`
- Model: type the deployed model name, such as `gpt-4o`
- API key: your Azure AI Foundry key

| Test | Pass | Fail | Notes | Sign-off |
|------|------|------|-------|---------|
| 1 Settings save | | | Model field is text input; type the deployed model name | |
| 2 Local model list + selected model test | | | N/A - hosted provider | |
| 3 Hosted verify | | | App calls the configured project endpoint with bearer auth | |
| 4 Coach responds | | | | |
| 5 Freeform Ask AI / New chat | | | | |
| 6 Visualizer deterministic note / optional Ask AI | | | | |
| 7 Missing key fallback | | | Expect "AI Coach unavailable" + key error message | |

---

## Release Gate

Do not ship a release that changes AI provider code unless at minimum:

- Ollama or LM Studio passes all applicable local-provider steps.
- At least one hosted provider passes Settings save, Hosted verify, Coach responds, Freeform Ask AI / New chat, Visualizer Ask AI, and Missing key fallback.
- No JavaScript console errors occur during any test step.

Full certification across all 8 providers is preferred before a major version bump.
