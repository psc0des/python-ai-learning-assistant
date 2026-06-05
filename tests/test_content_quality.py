"""Baseline quality-gate tests for curriculum maturity."""

import json
import re
from collections import Counter
from pathlib import Path

from content_loader import load_content


def test_reference_topics_meet_baseline():
    loaded = load_content()
    labs_per_topic = Counter(ex["topic_id"] for ex in loaded.exercises)
    questions_per_topic = {
        test["topic_id"]: len(test.get("questions", []))
        for test in loaded.practice_tests
    }

    reference_topics = [topic for topic in loaded.topics if topic.get("quality_status") == "reference"]
    assert reference_topics, "At least one topic should be marked as reference quality."

    for topic in reference_topics:
        tid = topic["id"]
        assert labs_per_topic.get(tid, 0) >= 5, f"Reference topic '{tid}' should have at least 5 labs."
        assert questions_per_topic.get(tid, 0) >= 8, (
            f"Reference topic '{tid}' should have at least 8 practice questions."
        )
        lesson_sections = topic.get("lesson_sections", [])
        sourced_sections = [section for section in lesson_sections if section.get("source_url")]
        assert len(sourced_sections) == len(lesson_sections), (
            f"Reference topic '{tid}' should have source_url for all lesson sections."
        )


def test_non_reference_topics_are_explicitly_draft():
    loaded = load_content()
    for topic in loaded.topics:
        if topic.get("quality_status") != "reference":
            assert topic.get("quality_status") == "draft", (
                f"Topic '{topic['id']}' should be marked as draft until fully upgraded."
            )


def test_practice_answer_diversity():
    """No topic should use the predictable [0,1,2,3,0,1,2,3] answer pattern."""
    uniform_pattern = [0, 1, 2, 3, 0, 1, 2, 3]
    loaded = load_content()
    violations = []
    for pt in loaded.practice_tests:
        questions = pt.get("questions", [])
        if len(questions) == 8:
            indices = [q["answer"] for q in questions]
            if indices == uniform_pattern:
                violations.append(pt["topic_id"])
    assert not violations, (
        f"Topics with predictable [0,1,2,3,0,1,2,3] answer pattern (easy to game): "
        f"{violations}"
    )


def test_lesson_run_blocks_execute_cleanly():
    """All 'python run' code fences in lesson.md files must execute without error."""
    from runner import run_user_code

    content_dir = Path(__file__).parent.parent / "content" / "topics"
    code_block_re = re.compile(r"```python run\n([\s\S]*?)```", re.MULTILINE)
    failures = []
    for lesson_file in sorted(content_dir.glob("*/lesson.md")):
        topic = lesson_file.parent.name
        text = lesson_file.read_text(encoding="utf-8")
        for match in code_block_re.finditer(text):
            snippet = match.group(1).rstrip("\n")
            result = run_user_code({"code": snippet, "exercise_id": ""}, [])
            if result.get("stderr"):
                failures.append(
                    f"{topic}: {result['stderr'][:200]!r}\n  code: {snippet[:120]!r}"
                )
    assert not failures, (
        f"{len(failures)} 'python run' lesson block(s) failed in runner:\n"
        + "\n---\n".join(failures)
    )


def test_topic_json_run_blocks_execute_cleanly():
    """All 'python run' code fences in topic.json body fields must execute without error."""
    from runner import run_user_code

    content_dir = Path(__file__).parent.parent / "content" / "topics"
    code_block_re = re.compile(r"```python run\n([\s\S]*?)```", re.MULTILINE)
    failures = []
    for topic_file in sorted(content_dir.glob("*/topic.json")):
        topic_id = topic_file.parent.name
        topic = json.loads(topic_file.read_text(encoding="utf-8"))
        for section in topic.get("lesson_sections", []):
            body = section.get("body", "")
            for match in code_block_re.finditer(body):
                snippet = match.group(1).rstrip("\n")
                result = run_user_code({"code": snippet, "exercise_id": ""}, [])
                if result.get("stderr"):
                    failures.append(
                        f"{topic_id}/{section.get('title','?')}: {result['stderr'][:200]!r}\n  code: {snippet[:120]!r}"
                    )
    assert not failures, (
        f"{len(failures)} 'python run' topic.json block(s) failed in runner:\n"
        + "\n---\n".join(failures)
    )


def test_code_fence_regex_does_not_eat_code():
    """The renderLessonMarkdown regex must stop info-string at first newline."""
    code_block_re = re.compile(r"```([^\n`]*)\n([\s\S]*?)```")
    sample = "```python\nimport asyncio\n\nasync def main(): pass\n```"
    m = code_block_re.search(sample)
    assert m is not None
    assert m.group(1).strip() == "python", (
        f"Info string should be 'python', got {m.group(1)!r}"
    )
    assert m.group(2).startswith("import asyncio"), (
        f"Code content should start with 'import asyncio', got {m.group(2)[:40]!r}"
    )

    sample_run = "```python run\nimport asyncio\n\nasync def main(): pass\n```"
    m2 = code_block_re.search(sample_run)
    assert m2 is not None
    assert m2.group(1).strip() == "python run"
    assert m2.group(2).startswith("import asyncio")

