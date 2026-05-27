"""Tests for curriculum and practice test content integrity.

Verifies that:
- All topics have required fields
- All topics have exercises
- All practice tests have sufficient questions
- Content validation catches issues
"""

from collections import Counter

import pytest
from content_loader import load_content
from models import validate_content_at_startup

LOADED = load_content()
TOPICS = LOADED.topics
EXERCISES = LOADED.exercises
PRACTICE_TESTS = LOADED.practice_tests


class TestTopicFields:
    """Verify all topics have required content."""

    REQUIRED = {"id", "track", "title", "level", "intro", "mental_model", "syntax", "example"}

    @pytest.fixture(params=TOPICS, ids=lambda t: t["id"])
    def topic(self, request):
        return request.param

    def test_has_required_fields(self, topic):
        missing = self.REQUIRED - set(topic.keys())
        assert not missing, f"Topic '{topic['id']}' missing fields: {missing}"

    def test_has_must_know(self, topic):
        assert len(topic.get("must_know", [])) >= 3, (
            f"Topic '{topic['id']}' should have at least 3 must_know items"
        )

    def test_has_interview_tips(self, topic):
        assert len(topic.get("interview", [])) >= 3, (
            f"Topic '{topic['id']}' should have at least 3 interview/career tips"
        )

    def test_has_docs(self, topic):
        assert len(topic.get("docs", [])) >= 1, (
            f"Topic '{topic['id']}' should have at least 1 documentation link"
        )

    def test_has_real_world(self, topic):
        assert len(topic.get("real_world", [])) >= 1, (
            f"Topic '{topic['id']}' should have at least 1 real-world implementation note"
        )


class TestPracticeTests:
    """Verify practice test content quality."""

    @pytest.fixture(params=PRACTICE_TESTS, ids=lambda t: t["topic_id"])
    def test_entry(self, request):
        return request.param

    def test_has_enough_questions(self, test_entry):
        questions = test_entry.get("questions", [])
        assert len(questions) >= 3, (
            f"Practice test for '{test_entry['topic_id']}' has only {len(questions)} questions — need 3+"
        )

    def test_questions_have_explanations(self, test_entry):
        for i, q in enumerate(test_entry.get("questions", [])):
            assert q.get("explanation"), (
                f"Practice test '{test_entry['topic_id']}' question {i} has no explanation"
            )

    def test_questions_have_four_options(self, test_entry):
        for i, q in enumerate(test_entry.get("questions", [])):
            assert len(q.get("options", [])) == 4, (
                f"Practice test '{test_entry['topic_id']}' question {i} should have exactly 4 options"
            )

    def test_answer_index_valid(self, test_entry):
        for i, q in enumerate(test_entry.get("questions", [])):
            answer = q.get("answer")
            options = q.get("options", [])
            assert 0 <= answer < len(options), (
                f"Practice test '{test_entry['topic_id']}' question {i} has invalid answer index {answer}"
            )

    def test_answer_distribution_not_overly_skewed(self, test_entry):
        questions = test_entry.get("questions", [])
        if len(questions) < 4:
            return
        answers = [q.get("answer") for q in questions if isinstance(q.get("answer"), int)]
        counts = Counter(answers)
        assert len(counts) >= 2, (
            f"Practice test '{test_entry['topic_id']}' uses only one answer index. "
            "Rebalance option ordering."
        )
        dominant_ratio = max(counts.values()) / len(answers)
        assert dominant_ratio <= 0.75, (
            f"Practice test '{test_entry['topic_id']}' is overly skewed "
            f"(dominant answer ratio={dominant_ratio:.2f})."
        )


class TestContentValidation:
    """Test the content validation utility."""

    def test_validates_current_content(self):
        warnings = validate_content_at_startup(TOPICS, EXERCISES, PRACTICE_TESTS)
        # Filter out expected warnings (like topics with <5 questions)
        errors = [w for w in warnings if "missing fields" in w or "unknown topic" in w]
        assert not errors, f"Content has structural errors:\n" + "\n".join(errors)


class TestTopicCoverage:
    """Verify all topics have exercises and practice tests."""

    def test_all_topics_have_exercises(self):
        topic_ids = {t["id"] for t in TOPICS}
        exercise_topic_ids = {e["topic_id"] for e in EXERCISES}
        missing = topic_ids - exercise_topic_ids
        assert not missing, f"Topics without exercises: {missing}"

    def test_all_topics_have_practice_tests(self):
        topic_ids = {t["id"] for t in TOPICS}
        test_topic_ids = {t["topic_id"] for t in PRACTICE_TESTS}
        missing = topic_ids - test_topic_ids
        assert not missing, f"Topics without practice tests: {missing}"
