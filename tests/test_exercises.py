"""Tests for exercise solutions and content integrity.

Verifies that:
- All exercise solutions pass their own tests
- All exercises have required fields
- All exercises reference valid topics
"""

import pytest
from runner import run_user_code
from content_loader import load_content

LOADED = load_content()
EXERCISES = LOADED.exercises
TOPICS = LOADED.topics


TOPIC_IDS = {topic["id"] for topic in TOPICS}


class TestExerciseSolutions:
    """Verify that every exercise's solution passes its own tests."""

    @pytest.fixture(params=[ex for ex in EXERCISES if ex.get("solution")], ids=lambda ex: ex["id"])
    def exercise(self, request):
        return request.param

    def test_solution_passes(self, exercise):
        result = run_user_code(
            {"code": exercise["solution"], "exercise_id": exercise["id"]},
            EXERCISES,
        )
        assert result["ok"], (
            f"Exercise '{exercise['id']}' solution failed:\n"
            f"  stderr: {result.get('stderr', '')}\n"
            f"  tests: {result.get('tests', [])}"
        )
        for test in result.get("tests", []):
            assert test["passed"], (
                f"Exercise '{exercise['id']}' test '{test['label']}' failed:\n"
                f"  expected: {test['expected']}\n"
                f"  actual: {test['actual']}"
            )


class TestExerciseFields:
    """Verify all exercises have required fields."""

    REQUIRED = {"id", "topic_id", "title", "difficulty", "prompt", "starter", "tests"}

    @pytest.fixture(params=EXERCISES, ids=lambda ex: ex["id"])
    def exercise(self, request):
        return request.param

    def test_has_required_fields(self, exercise):
        missing = self.REQUIRED - set(exercise.keys())
        assert not missing, f"Exercise '{exercise['id']}' missing fields: {missing}"

    def test_has_solution(self, exercise):
        assert exercise.get("solution"), f"Exercise '{exercise['id']}' is missing a solution"

    def test_has_hint(self, exercise):
        assert exercise.get("hint"), f"Exercise '{exercise['id']}' is missing a hint"

    def test_has_at_least_two_tests(self, exercise):
        assert len(exercise.get("tests", [])) >= 2, (
            f"Exercise '{exercise['id']}' should have at least 2 test cases"
        )

    def test_references_valid_topic(self, exercise):
        assert exercise["topic_id"] in TOPIC_IDS, (
            f"Exercise '{exercise['id']}' references unknown topic '{exercise['topic_id']}'"
        )
