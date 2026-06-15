"""Static checks for frontend learner-state contracts."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_practice_hash_uses_full_question_payload():
    app_js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert "questions.slice(0, 3)" not in app_js
    assert "question: q.question" in app_js
    assert "options: (q.options || [])" in app_js
    assert "answer: q.answer" in app_js
    assert "explanation: q.explanation" in app_js


def test_latest_attempt_readiness_contract_is_documented():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert "latest submitted practice-test score" in readme
    assert "Readiness uses the latest submitted attempt" in claude


def test_readiness_progress_bar_is_not_rendered():
    index_html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    app_js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    styles = (ROOT / "static" / "styles.css").read_text(encoding="utf-8")

    assert "readinessBar" not in app_js
    assert "renderReadinessBar" not in app_js
    assert "id=\"readinessBar\"" not in index_html
    assert ".readiness-bar" not in styles


def test_ai_help_uses_embedded_lab_coach_and_separate_ask_ai():
    index_html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    app_js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    styles = (ROOT / "static" / "styles.css").read_text(encoding="utf-8")

    assert "class=\"coach-card lab-coach-card\"" in index_html
    assert "id=\"aiOutput\"" in index_html
    assert "id=\"coachInput\"" in index_html
    assert "id=\"coachStatus\"" in index_html
    assert "id=\"aiBtn\"" in index_html
    assert "id=\"explainBtn\"" in index_html

    assert "id=\"askAiDock\"" in index_html
    assert "id=\"askAiPanel\"" in index_html
    assert "id=\"askAiLauncher\"" in index_html
    assert "id=\"askAiOutput\"" in index_html
    assert "id=\"askAiInput\"" in index_html
    assert "id=\"askAiStatus\"" in index_html
    assert "id=\"askAiSendBtn\"" in index_html
    assert "id=\"askAiNewChat\"" in index_html
    assert "class=\"ask-ai-chat-icon\"" in index_html
    assert ">AI</span>" not in index_html
    assert "Quick help while you read, try examples, or step through code." in index_html
    assert "Ask what this means, why it works, or for a small example" in index_html
    assert "id=\"coachDock\"" not in index_html
    assert "id=\"coachLauncher\"" not in index_html
    assert "id=\"coachPanel\"" not in index_html
    assert "id=\"codePopupAiPanel\"" not in index_html
    assert "id=\"codePopupAiBody\"" not in index_html
    assert "id=\"codePopupAiClose\"" not in index_html

    assert "async function askLabCoach" in app_js
    assert "async function askFloatingAi" in app_js
    assert "await askFloatingAi(full, { includeTopicContext: true });" in app_js
    assert "await askFloatingAi(question + ctx, { includeTopicContext: true });" in app_js
    assert "askAiMessages" in app_js
    assert "coachMessages" in app_js
    assert "Need a quick explanation?" in app_js
    assert "MESSAGE_TYPE_INTERVAL_MS" in app_js
    assert "function _animateAssistantMessage" in app_js
    assert "async function postAiStreamWithTimeout" in app_js
    assert "\"/api/ai-coach-stream\"" in app_js
    assert "response.body.getReader()" in app_js
    assert "event.type === \"chunk\"" in app_js
    assert "setCoachStatus(\"Coach is typing...\")" in app_js
    assert "setAskAiStatus(\"Ask AI is typing...\")" in app_js
    assert "await postJsonWithTimeout(\"/api/ai-coach\", payload, timeoutMs)" in app_js
    assert "_beginStreamingAssistantMessage" in app_js
    assert "_updateStreamingAssistantMessage" in app_js
    assert "typing: cursor < text.length" in app_js
    assert "coachTypingTimer" in app_js
    assert "askAiTypingTimer" in app_js
    assert "function startNewAskAiChat" in app_js
    assert "askAiMessages = [{ role: \"assistant\", text: ASK_AI_WELCOME_MESSAGE }]" in app_js
    assert "els.askAiNewChat.addEventListener(\"click\", startNewAskAiChat)" in app_js
    assert "I stay separate from the lab coach" not in app_js
    assert "async function askGlobalCoach" not in app_js
    assert "function _callInlineAi" not in app_js

    assert ".ask-ai-dock" in styles
    assert ".lab-coach-card" in styles
    assert "grid-template-columns: minmax(360px, 1fr) minmax(360px, 1fr);" in styles
    assert "right: 22px;" in styles
    assert "z-index: 1100;" in styles
    assert ".coach-message.is-typing .message-content::after" in styles
    assert "@media (prefers-reduced-motion: reduce)" in styles
    assert "#coachInput,\n#askAiInput" in styles
    assert "#coachInput:focus,\n#askAiInput:focus" in styles
    assert "body {\n    padding-bottom: 84px;" in styles
    assert "[hidden]" in styles
    assert "display: none !important;" in styles


def test_ai_settings_separates_model_inventory_from_connection_testing():
    index_html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    app_js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    setup = (ROOT / "SETUP.md").read_text(encoding="utf-8")
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")

    assert "Show local models" in index_html
    assert "id=\"modelSelect\"" in index_html
    assert "id=\"modelHelpText\"" in index_html
    assert "id=\"apiKeyHelpText\"" in index_html

    assert "const LOCAL_AI_PROVIDERS = new Set" in app_js
    assert "function updateAiSettingsMode" in app_js
    assert "els.model.hidden = local" in app_js
    assert "els.modelSelect.hidden = !local" in app_js
    assert "Test selected model" in app_js
    assert "Verify provider" in app_js
    assert "Sending a short prompt to the selected local model." in app_js
    assert "Choose the model you want to use, then run Test selected model." in app_js
    assert "This local model is ready for AI Coach and Ask AI." in app_js
    assert "is selected. Use Test selected model" not in app_js
    assert "Connected —" not in app_js
    assert "models available" not in app_js

    assert "Show local models" in readme
    assert "Test selected model" in setup
    assert "Verify provider" in setup
    assert "Do not show model counts as a generic \"Connected\" state" in claude


def test_floating_ask_ai_freeform_chat_does_not_inject_topic_context():
    app_js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")

    assert "async function askFloatingAi(questionOverride = \"\", { includeTopicContext = false, includeHistory = !includeTopicContext } = {})" in app_js
    assert "topic_id: includeTopicContext ? selectedTopicId : \"\"" in app_js
    assert "const askAiHistory = includeHistory" in app_js
    assert ".filter((message) => message.text !== \"thinking\" && message.contextKind !== \"contextual\")" in app_js
    assert "appendAskAiMessage(\"user\", question, { contextKind });" in app_js
    assert "appendAskAiMessage(\"assistant\", \"thinking\", { contextKind });" in app_js
    assert "chat_history: askAiHistory" in app_js
    assert "askFloatingAi();" in app_js
    assert "els.askAiSendBtn.addEventListener(\"click\", () => askFloatingAi())" in app_js
    assert "await askFloatingAi(full, { includeTopicContext: true });" in app_js
    assert "await askFloatingAi(question + ctx, { includeTopicContext: true });" in app_js
    assert "askFloatingAi(question, { includeTopicContext: true });" in app_js


def test_ai_settings_provider_test_does_not_inject_topic_context():
    app_js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")

    provider_test_start = app_js.index("async function testAiProviderConnection")
    provider_test_end = app_js.index(
        "\n\ndocument.querySelector(\"#aiSettingsTestBtn\")",
        provider_test_start,
    )
    provider_test = app_js[provider_test_start:provider_test_end]

    assert "topic_id: \"\"" in provider_test
    assert "topic_id: selectedTopicId" not in provider_test


def test_ai_settings_are_draft_until_save_or_successful_provider_test():
    app_js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")

    assert "const persistOnSuccess = options.persistOnSuccess === true;" in app_js
    assert "if (persistOnSuccess && result.ok && models.length && !result.suggestions_only)" in app_js

    model_change_start = app_js.index("els.model.addEventListener(\"change\"")
    model_change_end = app_js.index("if (els.modelSelect)", model_change_start)
    model_change = app_js[model_change_start:model_change_end]
    assert "saveAiSettings()" not in model_change

    model_select_start = app_js.index("els.modelSelect.addEventListener(\"change\"")
    model_select_end = app_js.index("els.endpoint.addEventListener", model_select_start)
    model_select_change = app_js[model_select_start:model_select_end]
    assert "saveAiSettings()" not in model_select_change

    assert "saveAiSettings();" in app_js[app_js.index("async function testAiProviderConnection"):]


def test_practice_and_selection_routing_contracts():
    app_js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")

    assert "function setPracticeCheckButtonsEnabled" in app_js
    assert "setPracticeCheckButtonsEnabled(false);" in app_js
    assert "setPracticeCheckButtonsEnabled(true);" in app_js

    selection_start = app_js.index("_selectionPopover.addEventListener(\"click\"")
    selection_end = app_js.index("return _selectionPopover;", selection_start)
    selection_handler = app_js[selection_start:selection_end]
    assert selection_handler.index("if (!els.vizOverlay.hidden)") < selection_handler.index("if (!els.codePopup.hidden)")


def test_set_model_options_clears_stale_model_when_none_selected():
    app_js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")

    start = app_js.index("function setModelOptions")
    end = app_js.index("\n  preferredModel = els.model.value;", start)
    body = app_js[start:end]

    assert "} else if (selectedModel != null) {" in body
    assert "} else {" in body
    assert "No models and no preferred model" in body
    assert "els.model.value = \"\";" in body
    assert "if (els.modelSelect) els.modelSelect.innerHTML = \"\";" in body


def test_ai_stream_generation_guards_prevent_cross_conversation_leaks():
    app_js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")

    assert "let coachStreamGen = 0;" in app_js
    assert "let askAiStreamGen = 0;" in app_js

    # selectExercise() and startNewAskAiChat() invalidate any in-flight stream
    # for the conversation they are resetting.
    assert (
        "coachStreamGen++;\n  _stopTypingTimer(\"coach\");\n  coachMessages = ["
        in app_js
    )
    assert (
        "askAiStreamGen++;\n  _stopTypingTimer(\"askAi\");\n"
        "  askAiMessages = [{ role: \"assistant\", text: ASK_AI_WELCOME_MESSAGE }];"
        in app_js
    )

    coach_start = app_js.index("async function askLabCoach")
    coach_end = app_js.index("\n\nasync function askFloatingAi")
    coach_body = app_js[coach_start:coach_end]

    floating_start = app_js.index("async function askFloatingAi")
    floating_end = app_js.index(
        "\n\n// ---------------------------------------------------------------------------\n// AI settings",
        floating_start,
    )
    floating_body = app_js[floating_start:floating_end]

    assert "const generation = ++coachStreamGen;" in coach_body
    assert coach_body.count("if (generation !== coachStreamGen) return;") == 3

    assert "const generation = ++askAiStreamGen;" in floating_body
    assert floating_body.count("if (generation !== askAiStreamGen) return;") == 3
