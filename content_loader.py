"""Structured curriculum loader for Python Skill Lab.

This module loads curriculum content from `content/` and keeps the API shape
compatible with the current frontend.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger("skill_lab.content_loader")

ROOT = Path(__file__).parent.resolve()
CONTENT_DIR = ROOT / "content"
MANIFEST_PATH = CONTENT_DIR / "manifest.json"


@dataclass
class LoadedContent:
    topics: list[dict[str, Any]]
    exercises: list[dict[str, Any]]
    practice_tests: list[dict[str, Any]]
    sources: dict[str, Any]
    manifest: dict[str, Any]
    mode: str


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _normalize_topic(topic: dict[str, Any]) -> dict[str, Any]:
    """Ensure topic shape expected by the existing UI and tests."""
    normalized = dict(topic)
    normalized.setdefault("must_know", [])
    normalized.setdefault("common_traps", [])
    normalized.setdefault("interview", [])
    normalized.setdefault("docs", [])
    normalized.setdefault("real_world", [])
    normalized.setdefault("lesson_sections", [])
    normalized.setdefault("outcome", "")
    normalized.setdefault("quality_status", "draft")
    return normalized


def _load_structured_content() -> LoadedContent:
    manifest = _load_json(MANIFEST_PATH)
    topic_ids: list[str] = manifest.get("topic_order", [])
    topics: list[dict[str, Any]] = []
    exercises: list[dict[str, Any]] = []
    practice_tests: list[dict[str, Any]] = []

    for topic_id in topic_ids:
        topic_dir = CONTENT_DIR / "topics" / topic_id
        topic_path = topic_dir / "topic.json"
        labs_path = topic_dir / "labs.json"
        practice_path = topic_dir / "practice.json"

        if not topic_path.exists():
            raise FileNotFoundError(f"Missing topic file: {topic_path}")
        if not labs_path.exists():
            raise FileNotFoundError(f"Missing labs file: {labs_path}")
        if not practice_path.exists():
            raise FileNotFoundError(f"Missing practice file: {practice_path}")

        topic = _normalize_topic(_load_json(topic_path))
        topics.append(topic)

        topic_labs = _load_json(labs_path)
        if not isinstance(topic_labs, list):
            raise ValueError(f"labs.json must be a list: {labs_path}")
        exercises.extend(topic_labs)

        topic_practice = _load_json(practice_path)
        if isinstance(topic_practice, dict) and "questions" in topic_practice:
            practice_tests.append(topic_practice)
        elif isinstance(topic_practice, list):
            practice_tests.extend(topic_practice)
        else:
            raise ValueError(
                f"practice.json must be a practice-test object or list: {practice_path}"
            )

    sources = {}
    sources_path = CONTENT_DIR / "sources.json"
    if sources_path.exists():
        sources = _load_json(sources_path)

    return LoadedContent(
        topics=topics,
        exercises=exercises,
        practice_tests=practice_tests,
        sources=sources,
        manifest=manifest,
        mode="structured",
    )


def load_content() -> LoadedContent:
    """Load content from structured files.

    Structured content is the only runtime source of truth. A load failure is
    fatal so a broken release cannot silently serve stale generated data.
    """
    try:
        loaded = _load_structured_content()
    except Exception as exc:
        raise RuntimeError(f"Structured content failed to load. Fix content/. Error: {exc}") from exc

    logger.info(
        "Loaded structured content: %d topics, %d labs, %d practice tests",
        len(loaded.topics),
        len(loaded.exercises),
        len(loaded.practice_tests),
    )
    return loaded
