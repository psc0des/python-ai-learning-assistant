"""Static contracts for chat markdown rendering and Ask AI window controls.

These guard the fixes for the real user-reported issues:
- chat responses rendered as disoriented one-fragment-per-line stacks
- reasoning-model <think> blocks leaking into the transcript
- missing minimize/maximize/close window controls
- "New chat" not clearly starting fresh
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _app_js() -> str:
    return (ROOT / "static" / "app.js").read_text(encoding="utf-8")


def _index_html() -> str:
    return (ROOT / "static" / "index.html").read_text(encoding="utf-8")


def _styles() -> str:
    return (ROOT / "static" / "styles.css").read_text(encoding="utf-8")


def test_chat_markdown_renderer_handles_blocks_not_raw_br():
    app_js = _app_js()
    # The old crude renderer turned every newline into <br>; that bug is gone.
    assert "html.replace(/\\n/g, '<br>')" not in app_js
    # Proper block-level rendering helpers exist.
    assert "function _renderTextBlock" in app_js
    assert "function _inlineMarkdown" in app_js
    # Headings, unordered lists, ordered lists are handled.
    assert 'md-h md-h${level}' in app_js
    assert "<ul>" in app_js and "<ol>" in app_js
    # Soft-wrapped lines are joined with a space (the disorientation fix).
    assert 'paraLines.join(" ")' in app_js


def test_chat_strips_reasoning_think_tags():
    app_js = _app_js()
    assert "function stripThinkTags" in app_js
    # Strips both closed and unclosed <think> blocks.
    assert "<think>[\\s\\S]*?<\\/think>" in app_js
    assert "<think>[\\s\\S]*$" in app_js
    # renderMarkdown runs the strip before rendering.
    assert "const cleaned = stripThinkTags(text);" in app_js


def test_ask_ai_has_min_max_close_window_controls():
    index_html = _index_html()
    assert 'id="askAiMinimize"' in index_html
    assert 'id="askAiMaximize"' in index_html
    assert 'id="askAiClose"' in index_html

    app_js = _app_js()
    assert "function toggleAskAiMaximize" in app_js
    assert 'els.askAiMaximize.addEventListener("click", toggleAskAiMaximize)' in app_js
    # Minimize collapses back to the bubble (same as close), keeping the chat.
    assert 'els.askAiMinimize.addEventListener("click", closeAskAiPanel)' in app_js

    styles = _styles()
    assert ".ask-ai-win-btn" in styles
    assert ".ask-ai-panel.maximized" in styles


def test_new_chat_starts_fresh_clearly():
    app_js = _app_js()
    new_chat_start = app_js.index("function startNewAskAiChat")
    new_chat_end = app_js.index("\n}", new_chat_start)
    body = app_js[new_chat_start:new_chat_end]
    # Still resets the active transcript to the welcome message.
    assert "askAiMessages = [{ role: \"assistant\", text: ASK_AI_WELCOME_MESSAGE }]" in body
    # Makes the reset obvious to the learner.
    assert "New chat started" in body
    assert "scrollTop = 0" in body
    # The previous conversation is archived as its own session, not discarded.
    assert "_archiveActiveAskAiSession()" in body
    assert "askAiSessions.push(" in body


def test_new_chat_creates_parallel_session_not_overwrite():
    # The real user-reported bug: "New chat" used to wipe the only transcript.
    # Ask AI must instead behave like separate messenger threads — starting a
    # new chat must not erase a previous one, and learners must be able to
    # switch back to it.
    app_js = _app_js()
    assert "let askAiSessions = [{ id: askAiSessionSeq, title: \"New chat\", messages: askAiMessages }];" in app_js
    assert "function switchAskAiSession(id)" in app_js
    assert "function closeAskAiSession(id)" in app_js
    # Switching sessions invalidates any in-flight stream for the chat being left,
    # the same generation guard already used for New Chat.
    switch_start = app_js.index("function switchAskAiSession")
    switch_end = app_js.index("\n}", switch_start)
    switch_body = app_js[switch_start:switch_end]
    assert "askAiStreamGen++;" in switch_body
    assert "askAiMessages = session.messages;" in switch_body
    # Closing a session never drops the last remaining chat.
    close_start = app_js.index("function closeAskAiSession")
    close_end = app_js.index("\n}", close_start)
    close_body = app_js[close_start:close_end]
    assert "if (askAiSessions.length <= 1) return;" in close_body


def test_ask_ai_session_tabs_render_only_when_multiple_chats_exist():
    index_html = _index_html()
    assert 'id="askAiSessionTabs"' in index_html
    assert 'role="tablist"' in index_html

    app_js = _app_js()
    render_start = app_js.index("function renderAskAiSessionTabs")
    render_end = app_js.index("\n}", render_start)
    body = app_js[render_start:render_end]
    # A single chat does not clutter the panel with a tab strip.
    assert "if (askAiSessions.length < 2) {" in body
    assert "els.askAiSessionTabs.hidden = true;" in body


def test_lab_and_practice_text_renders_inline_code_not_literal_backticks():
    # Lab prompts, hints, and practice questions/options/explanations contain
    # backticked code references. They must render through _inlineMarkdown (which
    # escapes HTML and renders `code`), not textContent which shows raw backticks.
    app_js = _app_js()
    assert "els.exercisePrompt.innerHTML = _inlineMarkdown(selectedExercise.prompt" in app_js
    assert "els.exercisePrompt.textContent = selectedExercise.prompt" not in app_js
    assert "els.testOutput.innerHTML = `💡 Hint: ${_inlineMarkdown(selectedExercise.hint" in app_js
    # Practice explanations render inline code (innerHTML + _inlineMarkdown).
    assert "explanationEl.innerHTML = `✓ Correct. ${_inlineMarkdown(question.explanation" in app_js
    assert "explanationEl.textContent" not in app_js
    # Practice question text and options use the inline renderer.
    assert "${_inlineMarkdown(question.question)}" in app_js
    assert "<span>${_inlineMarkdown(option)}</span>" in app_js
