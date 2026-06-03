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


class FakeManifestPath:
    def exists(self):
        return True


def test_structured_failure_is_fatal_by_default(monkeypatch):
    import content_loader

    def broken_loader():
        raise ValueError("Simulated broken content")

    monkeypatch.setattr(content_loader, "_ALLOW_LEGACY_FALLBACK", False)
    monkeypatch.setattr(content_loader, "_load_structured_content", broken_loader)
    monkeypatch.setattr(content_loader, "MANIFEST_PATH", FakeManifestPath())

    import pytest
    with pytest.raises(RuntimeError, match="Structured content failed to load"):
        content_loader.load_content()


def test_structured_failure_falls_back_with_env_var(monkeypatch):
    import content_loader

    def broken_loader():
        raise ValueError("Simulated broken content")

    monkeypatch.setattr(content_loader, "_ALLOW_LEGACY_FALLBACK", True)
    monkeypatch.setattr(content_loader, "_load_structured_content", broken_loader)
    monkeypatch.setattr(content_loader, "MANIFEST_PATH", FakeManifestPath())

    result = content_loader.load_content()
    assert result.mode == "legacy"
