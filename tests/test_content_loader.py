"""Tests for structured content loading compatibility."""

import pytest

from content_loader import load_content


def test_uses_structured_content_mode():
    loaded = load_content()
    assert loaded.mode == "structured"


def test_structured_content_has_expected_current_baseline():
    loaded = load_content()
    assert len(loaded.topics) == 25
    assert len(loaded.exercises) == 146
    assert len(loaded.practice_tests) == 25


def test_structured_topic_order_matches_manifest():
    loaded = load_content()
    loaded_ids = [topic["id"] for topic in loaded.topics]
    assert loaded_ids == loaded.manifest["topic_order"]


def test_topics_have_quality_status():
    loaded = load_content()
    for topic in loaded.topics:
        assert topic.get("quality_status") in {"reference", "draft"}


def test_structured_failure_is_fatal_by_default(monkeypatch):
    import content_loader

    def broken_loader():
        raise ValueError("Simulated broken content")

    monkeypatch.setattr(content_loader, "_load_structured_content", broken_loader)

    with pytest.raises(RuntimeError, match="Structured content failed to load"):
        content_loader.load_content()
