"""Static accessibility contracts.

Guards the fixes from the a11y pass (axe-core found these as serious WCAG issues):
- scrollable code blocks must be keyboard-focusable (tabindex)
- the CodeMirror editor must have an accessible name
- modals must return focus to their trigger on close
- the "Illustration only" note must not use a near-invisible dark-on-dark color
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _app_js() -> str:
    return (ROOT / "static" / "app.js").read_text(encoding="utf-8")


def test_scrollable_code_blocks_are_keyboard_focusable():
    app_js = _app_js()
    index_html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    # Generated lesson + chat code blocks.
    assert '<pre class="lesson-code" tabindex="0">' in app_js
    assert '<pre class="coach-code" tabindex="0">' in app_js
    # Static overview code blocks.
    assert '<pre tabindex="0"><code id="syntax">' in index_html
    assert '<pre tabindex="0"><code id="example">' in index_html


def test_codemirror_editor_has_accessible_name():
    cm = (ROOT / "static" / "codemirror-init.js").read_text(encoding="utf-8")
    assert 'EditorView.contentAttributes.of({ "aria-label": "Code editor" })' in cm


def test_modals_return_focus_to_trigger_on_close():
    app_js = _app_js()
    # Visualizer captures and restores focus.
    assert "_vizReturnFocus = sourceBtn || document.activeElement;" in app_js
    assert "if (els.vizClose) requestAnimationFrame(() => els.vizClose.focus());" in app_js
    assert "_vizReturnFocus && typeof _vizReturnFocus.focus === \"function\"" in app_js
    # Code popup captures and restores focus.
    assert "_codePopupReturnFocus = document.activeElement;" in app_js
    assert "_codePopupReturnFocus && typeof _codePopupReturnFocus.focus === \"function\"" in app_js


def test_illustration_note_uses_readable_contrast_color():
    styles = (ROOT / "static" / "styles.css").read_text(encoding="utf-8")
    note_block = styles[styles.index(".lesson-code-note {"):styles.index(".lesson-code-note {") + 300]
    # Light slate over the dark code block, and the near-invisible opacity is gone.
    assert "color: #94a3b8;" in note_block
    assert "opacity: 0.6;" not in note_block
