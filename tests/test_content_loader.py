"""Tests for structured content loading compatibility."""

from content_loader import load_content
from curriculum import TOPICS as LEGACY_TOPICS
from exercises import EXERCISES as LEGACY_EXERCISES
from practice_tests import PRACTICE_TESTS as LEGACY_PRACTICE_TESTS


def test_uses_structured_content_mode():
    loaded = load_content()
    assert loaded.mode == "structured"


def test_structured_content_covers_legacy_baseline():
    # Structured content is the source of truth. The legacy modules are a
    # deprecated fallback snapshot, so structured content must include at
    # least everything legacy had, but is allowed to add new topics/labs.
    loaded = load_content()
    assert len(loaded.topics) >= len(LEGACY_TOPICS)
    assert len(loaded.exercises) >= len(LEGACY_EXERCISES)
    assert len(loaded.practice_tests) >= len(LEGACY_PRACTICE_TESTS)


def test_structured_content_is_superset_of_legacy_topics():
    loaded = load_content()
    loaded_ids = {topic["id"] for topic in loaded.topics}
    legacy_ids = {topic["id"] for topic in LEGACY_TOPICS}
    missing = legacy_ids - loaded_ids
    assert not missing, f"Structured content is missing legacy topics: {missing}"


def test_topics_have_quality_status():
    loaded = load_content()
    for topic in loaded.topics:
        assert topic.get("quality_status") in {"reference", "draft"}
