"""Content drift guard: lesson.md sections must stay in sync with topic.json.

Fails if lesson_sections in topic.json and ## headings in lesson.md disagree
in count or title, preventing silent drift between the two sources.
"""

from __future__ import annotations

import re
from pathlib import Path

from content_loader import load_content, CONTENT_DIR


def _lesson_md_headings(topic_id: str) -> list[str]:
    lesson_path = CONTENT_DIR / "topics" / topic_id / "lesson.md"
    if not lesson_path.exists():
        return []
    text = lesson_path.read_text(encoding="utf-8")
    return re.findall(r"^## (.+)$", text, re.MULTILINE)


class TestContentDrift:
    def test_lesson_md_exists_for_every_topic_with_sections(self):
        loaded = load_content()
        missing = []
        for topic in loaded.topics:
            tid = topic["id"]
            if topic.get("lesson_sections"):
                lesson_path = CONTENT_DIR / "topics" / tid / "lesson.md"
                if not lesson_path.exists():
                    missing.append(tid)
        assert not missing, f"Topics have lesson_sections in JSON but no lesson.md: {missing}"

    def test_section_count_matches_lesson_md(self):
        loaded = load_content()
        mismatches = []
        for topic in loaded.topics:
            tid = topic["id"]
            json_sections = topic.get("lesson_sections", [])
            md_headings = _lesson_md_headings(tid)
            if json_sections and md_headings and len(json_sections) != len(md_headings):
                mismatches.append(
                    f"{tid}: JSON has {len(json_sections)} sections, "
                    f"lesson.md has {len(md_headings)} headings"
                )
        assert not mismatches, "Section count drift between topic.json and lesson.md:\n" + "\n".join(mismatches)

    def test_section_titles_match_lesson_md_headings(self):
        loaded = load_content()
        mismatches = []
        for topic in loaded.topics:
            tid = topic["id"]
            json_titles = [s.get("title", "") for s in topic.get("lesson_sections", [])]
            md_headings = _lesson_md_headings(tid)
            if not json_titles or not md_headings:
                continue
            for i, (jt, mh) in enumerate(zip(json_titles, md_headings)):
                if jt != mh:
                    mismatches.append(f"{tid} section {i+1}: JSON='{jt}' | MD='{mh}'")
        assert not mismatches, "Title drift between topic.json and lesson.md:\n" + "\n".join(mismatches)
