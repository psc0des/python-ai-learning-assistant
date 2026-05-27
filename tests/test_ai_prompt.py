"""Tests for the AI coach prompt builder.

Verifies that:
- Prompts are produced for valid and missing topic/exercise combinations
- Output is bounded to prevent context overflow
- Required sections are always present
- Chat history is properly truncated
"""

import pytest
from ai_coach import build_ai_prompt


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MOCK_TOPIC = {
    "id": "python-basics",
    "title": "Python Basics",
    "real_world": ["Used in scripts", "Used in tests"],
    "lesson_sections": [
        {
            "title": "Variables and Assignment",
            "body": "Assignment binds names to objects.",
            "source_label": "Python Tutorial: Informal Introduction",
            "source_url": "https://docs.python.org/3/tutorial/introduction.html",
        }
    ],
    "docs": [
        {
            "label": "Python Tutorial",
            "url": "https://docs.python.org/3/tutorial/index.html",
        }
    ],
}

MOCK_EXERCISE = {
    "id": "reverse-words",
    "title": "Reverse Words",
    "prompt": "Write a function that reverses words.",
}

LONG_CODE = "x = 1\n" * 500   # 3 000+ chars — should be truncated
LONG_QUESTION = "Why? " * 200  # very long question


# ---------------------------------------------------------------------------
# Structure tests
# ---------------------------------------------------------------------------

class TestPromptStructure:
    def test_contains_context_section(self):
        prompt = build_ai_prompt(MOCK_TOPIC, MOCK_EXERCISE, "def f(): pass", {})
        assert "=== CONTEXT ===" in prompt

    def test_contains_learner_code_section(self):
        prompt = build_ai_prompt(MOCK_TOPIC, MOCK_EXERCISE, "def f(): pass", {})
        assert "=== LEARNER'S CODE ===" in prompt

    def test_contains_response_format(self):
        prompt = build_ai_prompt(MOCK_TOPIC, MOCK_EXERCISE, "def f(): pass", {})
        assert "=== YOUR RESPONSE FORMAT ===" in prompt

    def test_contains_topic_title(self):
        prompt = build_ai_prompt(MOCK_TOPIC, MOCK_EXERCISE, "", {})
        assert "Python Basics" in prompt

    def test_contains_exercise_title(self):
        prompt = build_ai_prompt(MOCK_TOPIC, MOCK_EXERCISE, "", {})
        assert "Reverse Words" in prompt

    def test_contains_real_world_context(self):
        prompt = build_ai_prompt(MOCK_TOPIC, MOCK_EXERCISE, "", {})
        assert "Used in scripts" in prompt

    def test_contains_lesson_snapshot_and_sources(self):
        prompt = build_ai_prompt(MOCK_TOPIC, MOCK_EXERCISE, "", {})
        assert "=== LESSON SNAPSHOT (GROUND YOUR ANSWER HERE) ===" in prompt
        assert "Variables and Assignment" in prompt
        assert "=== OFFICIAL SOURCES ===" in prompt
        assert "https://docs.python.org/3/tutorial/introduction.html" in prompt


# ---------------------------------------------------------------------------
# Missing-data fallbacks
# ---------------------------------------------------------------------------

class TestPromptFallbacks:
    def test_none_topic_does_not_crash(self):
        prompt = build_ai_prompt(None, MOCK_EXERCISE, "pass", {})
        assert len(prompt) > 0

    def test_none_exercise_does_not_crash(self):
        prompt = build_ai_prompt(MOCK_TOPIC, None, "pass", {})
        assert len(prompt) > 0

    def test_both_none_does_not_crash(self):
        prompt = build_ai_prompt(None, None, "", {})
        assert len(prompt) > 0

    def test_empty_code_does_not_crash(self):
        prompt = build_ai_prompt(MOCK_TOPIC, MOCK_EXERCISE, "", {})
        assert len(prompt) > 0


# ---------------------------------------------------------------------------
# Truncation / bounds
# ---------------------------------------------------------------------------

class TestPromptBounds:
    def test_long_code_is_truncated(self):
        # LONG_CODE is "x = 1\n" * 500 = 3000 chars, which is right at the 3000-char cap.
        # Use even more code to guarantee truncation fires.
        very_long_code = "x = 1\n" * 1000  # 6 000 chars — well past the 3 000-char limit
        prompt = build_ai_prompt(MOCK_TOPIC, MOCK_EXERCISE, very_long_code, {})
        # Should see "truncated" indicator and not all 1000 occurrences
        assert "truncated" in prompt
        assert prompt.count("x = 1") < 1000

    def test_long_run_result_is_truncated(self):
        big_result = {"stdout": "x\n" * 2000, "stderr": "", "tests": [], "feedback": []}
        prompt = build_ai_prompt(MOCK_TOPIC, MOCK_EXERCISE, "pass", big_result)
        # Result snippet in prompt must be bounded
        assert len(prompt) < 20_000

    def test_chat_history_is_limited_to_six(self):
        history = [{"role": "user", "text": f"msg {i}"} for i in range(20)]
        prompt = build_ai_prompt(MOCK_TOPIC, MOCK_EXERCISE, "pass", {}, chat_history=history)
        # Only the last 6 messages should appear
        assert "msg 19" in prompt
        assert "msg 0" not in prompt

    def test_long_individual_history_message_is_truncated(self):
        long_msg = "a" * 2000
        history = [{"role": "user", "text": long_msg}]
        prompt = build_ai_prompt(MOCK_TOPIC, MOCK_EXERCISE, "pass", {}, chat_history=history)
        # Each history message is capped at 500 chars
        assert "a" * 2000 not in prompt
        assert "truncated" in prompt


# ---------------------------------------------------------------------------
# Question inclusion
# ---------------------------------------------------------------------------

class TestPromptQuestion:
    def test_question_included_when_provided(self):
        prompt = build_ai_prompt(
            MOCK_TOPIC, MOCK_EXERCISE, "pass", {}, question="Why does my loop fail?"
        )
        assert "Why does my loop fail?" in prompt

    def test_default_review_text_when_no_question(self):
        prompt = build_ai_prompt(MOCK_TOPIC, MOCK_EXERCISE, "pass", {}, question="")
        assert "Review" in prompt or "review" in prompt
