"""API contract checks for /api/curriculum payload shape."""

from content_loader import load_content


TOPIC_KEYS_USED_BY_UI = {
    "id",
    "track",
    "title",
    "level",
    "intro",
    "mental_model",
    "outcome",
    "lesson_sections",
    "syntax",
    "example",
    "real_world",
    "must_know",
    "common_traps",
    "interview",
    "docs",
}


def test_topics_include_keys_used_by_ui():
    loaded = load_content()
    for topic in loaded.topics:
        missing = [key for key in TOPIC_KEYS_USED_BY_UI if key not in topic]
        assert not missing, f"Topic '{topic.get('id')}' missing API-contract keys: {missing}"


def test_exercise_contract_fields_exist():
    loaded = load_content()
    required = {"id", "topic_id", "title", "prompt", "starter", "tests"}
    for exercise in loaded.exercises:
        missing = [key for key in required if key not in exercise]
        assert not missing, f"Exercise '{exercise.get('id')}' missing API-contract keys: {missing}"


def test_practice_test_contract_fields_exist():
    loaded = load_content()
    for practice_test in loaded.practice_tests:
        assert "topic_id" in practice_test
        assert "questions" in practice_test

