"""Tests for structured content loading compatibility."""

from content_loader import load_content
from curriculum import TOPICS as LEGACY_TOPICS
from exercises import EXERCISES as LEGACY_EXERCISES
from practice_tests import PRACTICE_TESTS as LEGACY_PRACTICE_TESTS


def test_uses_structured_content_mode():
    loaded = load_content()
    assert loaded.mode == "structured"


def test_structured_counts_match_legacy_snapshot():
    loaded = load_content()
    assert len(loaded.topics) == len(LEGACY_TOPICS)
    assert len(loaded.exercises) >= len(LEGACY_EXERCISES)
    assert len(loaded.practice_tests) == len(LEGACY_PRACTICE_TESTS)


def test_topic_ids_match_legacy_snapshot():
    loaded = load_content()
    loaded_ids = {topic["id"] for topic in loaded.topics}
    legacy_ids = {topic["id"] for topic in LEGACY_TOPICS}
    assert loaded_ids == legacy_ids


def test_topics_have_quality_status():
    loaded = load_content()
    for topic in loaded.topics:
        assert topic.get("quality_status") in {"reference", "draft"}
